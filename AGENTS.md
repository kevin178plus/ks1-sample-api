# ks1-simple-api — AI 助手指引

本项目是一个轻量级本地 API 代理服务，自动使用多个免费 API 模型，兼容 OpenAI API 格式。

**Python**（Flask）+ **Go** 双引擎。

## 必读规范

每次会话开始时，**必须先读取 `_AI-RULES/` 目录下的所有规范文件**，并严格遵守。

| 文件 | 说明 |
|------|------|
| `_AI-RULES/base.md` | 核心基础规则 |
| `_AI-RULES/python.md` | Python 开发规范 |
| `_AI-RULES/bat.md` | BAT 脚本规范 |
| `_AI-RULES/time_rules.md` | 时间处理规则 |
| `_AI-RULES/operate_log.md` | 操作日志规则 |
| `_AI-RULES/karpathy.md` | AI 行为准则 |

## 快速提醒

- **中文回复**，代码注释用中文
- **所有操作**追加记录到 `operateLog.md`
- **Windows 控制台**禁止 emoji，用 `[OK]`/`[FAIL]` 替代
- **时间获取**优先 MCP 工具，不可用时用 `python _AI-RULES/get_local_time.py`
- **不熟悉的逻辑先问**，不要盲目假设
