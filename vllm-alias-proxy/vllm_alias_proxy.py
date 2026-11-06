# VERSION: v1.0 build 4
"""vLLM 别名透传反代。

把 WorkBuddy 发来的不同模型别名统一改写为上游 vLLM 真实注册的模型名，
并按 URL 第一段路径把请求转发到「直连」或「SSH 隧道」两条链路。

除请求体里的 model 字段外，其余字段、请求头、SSE 流、响应头全部原样透传，
因此 tools / stream / stop / response_format 等 Agent 必需能力不受影响。

路由：
    /direct/v1/chat/completions -> 直连上游
    /ssh/v1/chat/completions    -> SSH 隧道上游
    /<route>/v1/models          -> 上游模型列表，id 改写为该路由的别名
    /health                     -> 健康检查
"""

from __future__ import annotations

import atexit
import ctypes
import http.client
import json
import logging
import os
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "proxy_config.json"
PID_FILE = BASE_DIR / "server.pid"
PORT_FILE = BASE_DIR / "server.port"
LOG_FILE = BASE_DIR / "server.log"

# 后台启动时控制台不可见，因此同时写一份 UTF-8 日志文件
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
LOGGER = logging.getLogger("vllm-alias-proxy")

MAX_BODY_BYTES = 64 * 1024 * 1024  # 请求体上限，防御异常大包
CHUNK_SIZE = 8192                   # 流式转发单次读取上限
PORT_RETRY_COUNT = 10               # 首选端口被占用时向后探测的端口数
SKIP_REQ_HEADERS = {
    "host", "content-length", "connection", "accept-encoding", "transfer-encoding",
}
SKIP_RESP_HEADERS = {
    "content-length", "connection", "transfer-encoding", "content-encoding",
}

CONFIG: dict[str, Any] = {}


def load_config() -> dict[str, Any]:
    """读取同目录下的 JSON 配置。"""
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_pid_alive(pid: int) -> bool:
    """检测进程是否存活。

    Windows 上不能用 os.kill(pid, 0)：CPython 在 Windows 会把它当作
    TerminateProcess(handle, 0)，反而杀掉目标进程。改用 OpenProcess 只读探测。
    """
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    kernel32.CloseHandle(handle)
    return True


def is_port_listening(host: str, port: int) -> bool:
    """探测服务端口是否已有实例在监听。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def check_existing() -> int | None:
    """返回已有存活实例的 PID；记录过期或无效时返回 None。

    Windows 上进程被强杀后内核对象可能短暂残留，或 PID 被系统复用，
    单靠 OpenProcess 会误判为"仍在运行"，因此需要再用端口监听确认。
    """
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        port = int(PORT_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None
    if not is_pid_alive(pid):
        return None
    host = str(CONFIG.get("listen_host", "127.0.0.1"))
    return pid if is_port_listening(host, port) else None


def write_service_info(port: int) -> None:
    """端口绑定成功后记录 PID 与实际端口，供精确停止使用。"""
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    PORT_FILE.write_text(str(port), encoding="utf-8")


def remove_service_info() -> None:
    """退出时清理 PID / 端口记录。"""
    for path in (PID_FILE, PORT_FILE):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            LOGGER.warning("failed to remove %s", path.name)


class ProxyHTTPServer(ThreadingHTTPServer):
    """多线程 HTTP 服务，退出时不等子线程。"""

    daemon_threads = True
    allow_reuse_address = True


class ProxyHandler(BaseHTTPRequestHandler):
    """OpenAI 兼容接口的透传处理器。"""

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s %s", self.address_string(), fmt % args)

    def handle_one_request(self) -> None:
        """捕获客户端断开导致的连接错误，避免 traceback 刷屏。"""
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            LOGGER.debug("client disconnected before request completed")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._dispatch()

    def do_PUT(self) -> None:
        self._dispatch()

    def do_OPTIONS(self) -> None:
        self._dispatch()

    @staticmethod
    def _parse_route(path_only: str) -> tuple[str, str] | None:
        """把 /direct/v1/chat/completions 拆成 (direct, /v1/chat/completions)。"""
        parts = path_only.split("/", 2)
        if len(parts) < 2 or not parts[1]:
            return None
        rest = "/" + parts[2] if len(parts) > 2 else "/"
        return parts[1], rest

    def _dispatch(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/health":
            self._send_json(200, {
                "status": "ok",
                "upstream_model": CONFIG["upstream_model"],
                "routes": list(CONFIG["routes"].keys()),
            })
            return

        route = self._parse_route(parsed.path)
        if route is None or route[0] not in CONFIG["routes"]:
            # 根路径 /v1/... 默认转发到 direct 路由，兼容无前缀客户端
            if parsed.path.startswith("/v1/"):
                route = ("direct", parsed.path)
            else:
                self._send_json(404, {"error": "unknown route", "path": parsed.path})
                return

        route_name, upstream_path = route
        route_cfg = CONFIG["routes"][route_name]
        query = ("?" + parsed.query) if parsed.query else ""
        upstream_path += query

        try:
            body = self._read_and_rewrite_body()
        except ValueError as exc:
            self._send_json(400, {"error": "invalid request body", "detail": str(exc)})
            return

        if body is None:
            self._send_json(413, {"error": "request body too large"})
            return

        self._proxy(route_name, route_cfg, upstream_path, body)

    def _read_and_rewrite_body(self) -> bytes | None:
        """读取请求体，并把其中的 model 字段改写为上游真实模型名。"""
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > MAX_BODY_BYTES:
            return None
        raw = self.rfile.read(length) if length else b""
        if not raw or self.command not in ("POST", "PUT", "PATCH"):
            return raw
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return raw  # 非 JSON 请求原样透传
        if not isinstance(payload, dict):
            return raw
        payload["model"] = CONFIG["upstream_model"]
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def _proxy(
        self,
        route_name: str,
        route_cfg: dict[str, Any],
        upstream_path: str,
        body: bytes,
    ) -> None:
        """连接上游并转发请求与响应。"""
        upstream = urlparse(route_cfg["upstream"])
        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            if key.lower() not in SKIP_REQ_HEADERS:
                headers[key] = value
        headers["Host"] = upstream.netloc
        headers["Accept-Encoding"] = "identity"
        headers["Content-Length"] = str(len(body))

        timeout = float(CONFIG.get("timeout_seconds", 300))
        connection = http.client.HTTPConnection(
            upstream.hostname, upstream.port or 80, timeout=timeout
        )
        response_started = False
        try:
            connection.request(
                self.command, upstream_path, body=body or None, headers=headers
            )
            response = connection.getresponse()
            content_type = (response.getheader("Content-Type") or "").lower()
            no_length = response.getheader("Content-Length") is None
            is_stream = "event-stream" in content_type or no_length

            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in SKIP_RESP_HEADERS:
                    self.send_header(key, value)
            response_started = True

            if is_stream:
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                self._stream_response(response)
            else:
                payload = response.read()
                if upstream_path.split("?")[0].rstrip("/").endswith("/v1/models"):
                    payload = self._rewrite_models(payload, route_cfg["alias"])
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except (OSError, http.client.HTTPException) as exc:
            LOGGER.error("route=%s upstream error: %s", route_name, exc)
            if not response_started:
                self._send_json(502, {
                    "error": "upstream unavailable",
                    "route": route_name,
                    "detail": str(exc),
                })
        finally:
            connection.close()

    def _stream_response(self, response: http.client.HTTPResponse) -> None:
        """逐块转发 SSE，不缓冲、不等待凑满缓冲区。"""
        read_one = getattr(response, "read1", None) or response.read
        try:
            while True:
                chunk = read_one(CHUNK_SIZE)
                if not chunk:
                    break
                self.wfile.write(("%x\r\n" % len(chunk)).encode("ascii") + chunk + b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            LOGGER.warning("client disconnected during streaming")

    @staticmethod
    def _rewrite_models(payload: bytes, alias: str) -> bytes:
        """把 /v1/models 返回的真实模型 id 替换成该路由的别名。"""
        try:
            data = json.loads(payload)
        except (ValueError, UnicodeDecodeError):
            return payload
        if not isinstance(data, dict):
            return payload
        for item in data.get("data", []):
            if isinstance(item, dict) and item.get("id") == CONFIG["upstream_model"]:
                item["id"] = alias
        return json.dumps(data, ensure_ascii=False).encode("utf-8")


def create_server(host: str, preferred_port: int) -> tuple[ProxyHTTPServer, int]:
    """绑定端口；被占用时向后探测，禁止强占。"""
    last_error: OSError | None = None
    for port in range(preferred_port, preferred_port + PORT_RETRY_COUNT):
        try:
            return ProxyHTTPServer((host, port), ProxyHandler), port
        except OSError as exc:
            last_error = exc
    raise RuntimeError(
        f"no free port in [{preferred_port}, {preferred_port + PORT_RETRY_COUNT}): {last_error}"
    )


def main() -> int:
    global CONFIG
    CONFIG = load_config()

    existing = check_existing()
    if existing:
        LOGGER.error("another instance is already running, pid=%s", existing)
        return 1

    host = str(CONFIG.get("listen_host", "127.0.0.1"))
    preferred_port = int(CONFIG.get("listen_port", 18010))
    server, port = create_server(host, preferred_port)
    write_service_info(port)
    atexit.register(remove_service_info)

    LOGGER.info("listening on http://%s:%s", host, port)
    if port != preferred_port:
        LOGGER.warning("port %s was busy; using %s - UPDATE models.json urls", preferred_port, port)
    LOGGER.info("upstream model: %s", CONFIG["upstream_model"])
    for name, cfg in CONFIG["routes"].items():
        LOGGER.info("route /%s -> %s alias=%s", name, cfg["upstream"], cfg["alias"])

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        LOGGER.info("shutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        LOGGER.exception("unhandled exception, service stopped")
        sys.exit(1)
