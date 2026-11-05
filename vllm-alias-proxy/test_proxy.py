# VERSION: v1.0 build 3
"""vllm_alias_proxy 的单元测试与冒烟测试。

单元测试不依赖网络；冒烟测试需网关已启动，用 PROXY_SMOKE=1 开启。
"""

from __future__ import annotations

import io
import json
import os
import unittest
import urllib.request
from typing import Any

import vllm_alias_proxy as proxy

BASE_URL = "http://127.0.0.1:18010"

# 本机存在 HTTP_PROXY 环境变量，urllib 默认会把 127.0.0.1 也交给代理，
# 代理无法回连本机端口会返回 502。这里构造不使用任何代理的 opener。
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class UnitTests(unittest.TestCase):
    """纯函数测试，不需要上游服务。"""

    def setUp(self) -> None:
        proxy.CONFIG = {
            "upstream_model": "DeepSeek-V4-Flash",
            "routes": {"direct": {"alias": "A"}, "ssh": {"alias": "B"}},
        }

    def test_parse_route(self) -> None:
        self.assertEqual(
            proxy.ProxyHandler._parse_route("/direct/v1/chat/completions"),
            ("direct", "/v1/chat/completions"),
        )
        self.assertEqual(
            proxy.ProxyHandler._parse_route("/ssh/v1/models"),
            ("ssh", "/v1/models"),
        )
        # 单段路径会被拆成普通路由名，/health 由 _dispatch 优先处理
        self.assertEqual(proxy.ProxyHandler._parse_route("/health"), ("health", "/"))
        self.assertIsNone(proxy.ProxyHandler._parse_route("/"))

    def test_rewrite_models(self) -> None:
        payload = json.dumps({
            "object": "list",
            "data": [{"id": "DeepSeek-V4-Flash", "object": "model"}],
        }).encode("utf-8")
        rewritten = json.loads(proxy.ProxyHandler._rewrite_models(payload, "ALIAS"))
        self.assertEqual(rewritten["data"][0]["id"], "ALIAS")

    def test_rewrite_models_keeps_unrelated_ids(self) -> None:
        payload = json.dumps({"data": [{"id": "other-model"}]}).encode("utf-8")
        rewritten = json.loads(proxy.ProxyHandler._rewrite_models(payload, "ALIAS"))
        self.assertEqual(rewritten["data"][0]["id"], "other-model")

    def test_body_model_rewrite(self) -> None:
        raw = json.dumps({
            "model": "DeepSeek-V4-Flash-SSH",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
            "tools": [{"type": "function", "function": {"name": "demo"}}],
        }).encode("utf-8")

        class Dummy:
            command = "POST"
            headers = {"Content-Length": str(len(raw))}
            rfile = io.BytesIO(raw)

        result = json.loads(proxy.ProxyHandler._read_and_rewrite_body(Dummy()))
        self.assertEqual(result["model"], "DeepSeek-V4-Flash")
        self.assertTrue(result["stream"])
        self.assertEqual(len(result["tools"]), 1)
        self.assertEqual(result["messages"][0]["content"], "hi")

    def test_non_json_body_passthrough(self) -> None:
        raw = b"plain-text-body"

        class Dummy:
            command = "POST"
            headers = {"Content-Length": str(len(raw))}
            rfile = io.BytesIO(raw)

        self.assertEqual(proxy.ProxyHandler._read_and_rewrite_body(Dummy()), raw)

    def test_oversized_body_rejected(self) -> None:
        class Dummy:
            command = "POST"
            headers = {"Content-Length": str(proxy.MAX_BODY_BYTES + 1)}
            rfile = io.BytesIO(b"")

        self.assertIsNone(proxy.ProxyHandler._read_and_rewrite_body(Dummy()))


def request_json(path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any], str]:
    """向网关发一个请求，返回状态码、解析后的 JSON、原始文本。"""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with OPENER.open(req, timeout=90) as resp:
        text = resp.read().decode("utf-8", "replace")
        try:
            return resp.status, json.loads(text), text
        except ValueError:
            return resp.status, {}, text


@unittest.skipUnless(os.environ.get("PROXY_SMOKE") == "1", "set PROXY_SMOKE=1 to run live tests")
class SmokeTests(unittest.TestCase):
    """真实链路测试：别名改写、两条路由、流式透传、tools 透传。"""

    def test_health(self) -> None:
        status, data, _ = request_json("/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")

    def test_models_aliases(self) -> None:
        _, direct, _ = request_json("/direct/v1/models")
        _, ssh, _ = request_json("/ssh/v1/models")
        self.assertEqual(direct["data"][0]["id"], "DeepSeek-V4-Flash")
        self.assertEqual(ssh["data"][0]["id"], "DeepSeek-V4-Flash-SSH")

    def test_chat_both_routes(self) -> None:
        for route, alias in (("direct", "DeepSeek-V4-Flash"), ("ssh", "DeepSeek-V4-Flash-SSH")):
            with self.subTest(route=route):
                status, _, text = request_json(
                    f"/{route}/v1/chat/completions",
                    {
                        "model": alias,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                        "stream": False,
                    },
                )
                self.assertEqual(status, 200, text[:300])
                self.assertIn("choices", text)

    def test_stream_passthrough(self) -> None:
        status, _, text = request_json(
            "/direct/v1/chat/completions",
            {
                "model": "DeepSeek-V4-Flash",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 8,
                "stream": True,
            },
        )
        self.assertEqual(status, 200)
        self.assertIn("data:", text)
        self.assertIn("[DONE]", text)

    def test_tools_passthrough(self) -> None:
        status, _, text = request_json(
            "/ssh/v1/chat/completions",
            {
                "model": "DeepSeek-V4-Flash-SSH",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "stream": False,
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "get_time",
                        "description": "get current time",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }],
            },
        )
        self.assertEqual(status, 200, text[:300])
        self.assertNotIn("does not exist", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
