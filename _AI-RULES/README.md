# AI 助手规则目录

本目录包含 **ks1-simple-api 项目** 的 AI 助手开发规范。

## 快速开始

根据 AI 助手能力选择使用方式：

### 方式一：文件引用（推荐）
复制以下内容到 AI 对话框：

```
请在本次对话中遵守 _AI-RULES/ 中的所有规则
```

### 方式二：纯文本（不支持文件引用时使用）
复制 [QUICK.md](QUICK.md) 的全部内容到 AI 对话框。

---

## 规则文件

| 文件 | 说明 |
|------|------|
| **[base.md](base.md)** | **核心基础规则（必读）** |
| **[QUICK.md](QUICK.md)** | **快速参考（纯文本版）** |
| [time_rules.md](time_rules.md) | 时间处理规则 |
| [operate_log.md](operate_log.md) | 操作日志规则 |
| [python.md](python.md) | Python 开发规范 |
| [bat.md](bat.md) | BAT 脚本规范 |
| [karpathy.md](karpathy.md) | Karpathy 4 原则（通用行为准则） |
| [karpathy-guidelines.md](karpathy-guidelines.md) | Karpathy 行为准则（英文版） |
| [karpathy-examples.md](karpathy-examples.md) | Karpathy 正反面对比示例 |
| [OPERATELOG_APPEND_ONLY.md](OPERATELOG_APPEND_ONLY.md) | 操作日志追加写入强制规则 |
| [operateLog-processing-rules.md](operateLog-processing-rules.md) | 操作日志拆分自动化规则 |

### 工具脚本
| 文件 | 说明 |
|------|------|
| [get_local_time.py](get_local_time.py) | 本地时间获取脚本（MCP 备选方案） |

---

## 核心速览

- **中文回复**：所有回答用中文，代码注释用中文
- **时间获取**：优先 MCP 工具(自动获取)，备选本地脚本
- **操作日志**：所有操作追加到 `operateLog.md`
- **AI 行为准则**：Karpathy 4 原则（编码前思考、简洁优先、精准修改、目标驱动）
- **Python 规范**：遵循 PEP 8，使用类型提示
- **BAT 规范**：禁止中文，使用标准模板

---

## 适用范围

本规则适用于 **ks1-simple-api 项目** 的所有 AI 助手操作，包括但不限于：

- 代码开发与优化
- 文档编写与更新
- 配置文件修改
- 测试与验证
- 问题诊断与修复

---

## 版本信息

- **文档版本**：2.0
- **创建日期**：2026-05-29
- **适用项目**：ks1-simple-api
