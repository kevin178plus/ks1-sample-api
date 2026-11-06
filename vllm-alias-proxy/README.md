# vllm-alias-proxy — vLLM 别名透传反代

## 为什么存在

WorkBuddy 的 `~/.workbuddy/models.json` 里 `id` 有三重身份：列表唯一键、显示用模型标识、以及发给上游的请求体 `model` 值。
两个条目若想指向同一个 vLLM 实例的不同链路（直连 / SSH 隧道），`id` 必须不同，但 vLLM 又不接受未注册的模型名（会 404）。
远端 `10.140.6.57:8006` 的 vLLM 启动参数不能改，所以在本机加一层只改写 `model` 字段的透传反代。

注意：`127.0.0.1:18006` 是 `ssh -L 18006:10.140.6.57:8006` 建立的隧道，与直连指向**同一个** vLLM，不是第二个模型。

## 结构

```
WorkBuddy  ->  127.0.0.1:18010/direct/...  ->  10.140.6.57:8006   (直连)
           ->  127.0.0.1:18010/ssh/...     ->  127.0.0.1:18006    (SSH 隧道)
```

除请求体 `model` 改写为 `DeepSeek-V4-Flash` 外，其余字段、请求头、SSE 流、响应头全部原样透传，
因此 `tools` / `stream` / `stop` / `response_format` 等 Agent 必需能力不受影响。

| 路由 | WorkBuddy 里的 id | 上游 |
|------|-------------------|------|
| `/direct` | `DeepSeek-V4-Flash` | `http://10.140.6.57:8006` |
| `/ssh` | `DeepSeek-V4-Flash-SSH` | `http://127.0.0.1:18006` |
| `/`（根路径） | `DeepSeek-V4-Flash` | 默认转发到 `/direct`，兼容无前缀客户端 |

## 使用

前置条件：`/ssh` 链路需要先建立 SSH 隧道，否则该路由返回 502；`/direct` 需要能直连局域网。

- 启动：双击 `start.bat`（或 `D:\ks_ws\kk文件夹\01-常用程序（含ai编程助手）\start-vllm-alias-proxy.bat`），后台监听 `127.0.0.1:18010`，日志写 `server.log`
- 停止：双击 `stop.bat`，按 `server.pid` 精确结束进程
- 改 IP / 端口 / 别名：编辑同级 `proxy_config.json`，改完重启网关

端口 18010 被占用时会自动向后顺延到 18011 等，此时必须同步修改 `models.json` 里的 URL，
因此启动后请看一眼 `server.log` 或 `server.port` 确认实际端口。

`models.json` 中的两条 URL（迁移目录后无需改动）：

```
http://127.0.0.1:18010/direct/v1/chat/completions
http://127.0.0.1:18010/ssh/v1/chat/completions
```

## 测试

```bash
python -m unittest -v test_proxy                       # 仅单元测试
PROXY_SMOKE=1 python -m unittest -v test_proxy        # 加真实链路冒烟测试
```

本机存在 `HTTP_PROXY=127.0.0.1:8903`，urllib 会把回环地址也交给代理并返回假 502。
测试脚本已构造无代理 opener；手写 curl 时请加 `--noproxy "*"`。

## 文件

| 文件 | 说明 |
|------|------|
| `vllm_alias_proxy.py` | 标准库 ThreadingHTTPServer，零依赖 |
| `proxy_config.json` | 端口、上游真实模型名、两条路由与别名 |
| `start.bat` / `stop.bat` | 纯 ASCII + CRLF + 无 BOM，按 PID 精确启停 |
| `test_proxy.py` | 6 个单元测试 + 5 个真实链路冒烟测试 |
