# 时间处理规则

适用于本项目的所有时间相关操作。

---

## 核心原则

根据不同场景使用不同的方式获取日期/时间，**优先使用 MCP 工具**：

| 场景 | 优先级 | 获取方式 | 示例 |
|------|--------|----------|------|
| **问题分析** | 1. MCP 工具<br>2. 本地脚本 | 调用 MCP 时间工具 | 在 AI 对话中自动获取 |
| **记录日志** | 1. MCP 工具<br>2. 本地脚本 | 调用 MCP 时间工具 | 记录时间戳时自动获取 |
| **编写代码** | 内置函数 | 使用语言内置函数 | `datetime.now()` 等 |

**注意**：MCP 工具不可用时，使用本地脚本 `python get_local_time.py` 作为备选方案。

---

## 🚨 绝对禁止硬编码日期！🚨

**每次需要当前时间时，必须使用动态获取的方式，绝对禁止使用硬编码日期！**

### 为什么这很重要？
1. **准确性**：确保所有时间记录的准确性
2. **一致性**：保持项目中时间格式的统一
3. **可追溯性**：正确的时间戳有助于问题追踪
4. **专业性**：体现开发过程的严谨性

### 错误示例（绝对禁止）
❌ `2025-01-08` （硬编码错误日期）
❌ `2025-01-01` （硬编码日期）
❌ 任何不是通过命令获取的当前日期

### 正确示例
✅ 使用 `python get_local_time.py --iso` 获取准确的当前时间
✅ 使用 MCP 工具自动获取

### 检查清单
在每次操作前，请确认：
- [ ] 是否需要记录时间？
- [ ] 是否已经获取了当前准确时间？
- [ ] 时间格式是否正确？
- [ ] 是否避免了硬编码日期？

---

## 1. 问题分析或日志记录场景

当你在**分析问题**或**记录本地日志文件**时，如果需要获取当前日期或时间：

### 优先使用 MCP 工具
- **工具类型**: MCP 时间工具
- **时区**: 本地时间（上海时区 UTC+8）
- **格式**: ISO 8601 格式

### 备选方案（MCP 不可用时）
- **脚本位置**: `get_local_time.py`
- **时区**: 本地时间（上海时区 UTC+8）
- **格式**: ISO 8601 格式

#### 使用示例
```bash
# 获取完整时间信息
python get_local_time.py

# 获取 ISO 格式时间
python get_local_time.py --iso

# 获取日期
python get_local_time.py --date

# 获取时间
python get_local_time.py --time
```

#### 输出示例
```
当前时间: 2026-02-28 15:30:45
ISO格式: 2026-02-28T15:30:45
日期: 2026-02-28
时间: 15:30:45
时间戳: 1740737445
```

---

## 2. 编写代码场景

当你在**编写应用程序代码**时，应该使用编程语言的内置日期/时间函数：

### Python 代码
```python
from datetime import datetime, timezone, timedelta

# ✅ 正确 - 使用 Python 内置函数
current_time = datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))

# 获取 UTC 时间
utc_time = datetime.now(timezone.utc)
print(utc_time.isoformat())

# 转换为本地时间（上海时区）
from zoneinfo import ZoneInfo
local_time = datetime.now(ZoneInfo("Asia/Shanghai"))
print(local_time.strftime("%Y-%m-%d %H:%M:%S"))
```

### 其他语言
| 语言 | 内置函数 |
|------|----------|
| JavaScript | `new Date()` |
| Java | `LocalDateTime.now()` |
| Go | `time.Now()` |

---

## 3. 日志记录格式

### 标准格式
在日志文件中记录时间时，使用以下格式：

```python
# ISO 8601 格式（推荐）
from datetime import datetime
timestamp = datetime.now().isoformat()
print(f"[{timestamp}] Task completed")

# 或自定义格式
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"[{timestamp}] Task completed")
```

### 操作日志格式
在 `operateLog.md` 中记录时：
```markdown
## 2026-02-28 15:30:45 完成功能开发

实现用户认证功能

---
```

---

## 4. 时间比较和计算

### Python 示例
```python
from datetime import datetime, timedelta

# 时间比较
start_time = datetime(2026, 2, 28, 10, 0, 0)
end_time = datetime.now()

if end_time > start_time:
    duration = end_time - start_time
    print(f"耗时: {duration.total_seconds()} 秒")

# 时间计算
future_time = datetime.now() + timedelta(hours=2)
past_time = datetime.now() - timedelta(days=1)
```

---

## 5. 时区处理

### Python 时区处理
```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# UTC 时间
utc_time = datetime.now(timezone.utc)

# 上海时区
shanghai_time = datetime.now(ZoneInfo("Asia/Shanghai"))

# 时区转换
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

utc_time = datetime.now(timezone.utc)
shanghai_time = utc_time.astimezone(ZoneInfo("Asia/Shanghai"))
```

---

## 6. 时间格式化

### 常用格式
```python
from datetime import datetime

now = datetime.now()

# ISO 8601
iso_format = now.isoformat()  # 2026-02-28T15:30:45.123456

# 简短格式
short_format = now.strftime("%Y-%m-%d %H:%M:%S")  # 2026-02-28 15:30:45

# 仅日期
date_only = now.strftime("%Y-%m-%d")  # 2026-02-28

# 仅时间
time_only = now.strftime("%H:%M:%S")  # 15:30:45

# 文件名友好格式
filename_format = now.strftime("%Y%m%d_%H%M%S")  # 20260228_153045
```

---

## 7. 脚本说明

### get_local_time.py

位于 `get_local_time.py`

#### 支持的参数
- 无参数：输出完整时间信息
- `--iso`：输出 ISO 8601 格式
- `--date`：仅输出日期
- `--time`：仅输出时间
- `--timestamp`：输出 Unix 时间戳

#### 使用示例
```bash
# 完整信息
python get_local_time.py

# ISO 格式（用于日志）
python get_local_time.py --iso

# 仅日期（用于文件名）
python get_local_time.py --date
```

---

## 8. 注意事项

1. **优先使用 MCP 工具**：分析问题时优先使用 MCP 时间工具
2. **备选本地脚本**：MCP 工具不可用时，使用 `get_local_time.py`
3. **时区一致**：使用本地时间（上海时区 UTC+8）
4. **格式统一**：日志记录使用 ISO 8601 格式，代码中根据业务需求格式化
5. **脚本位置**：本地时间脚本统一放在 `_AI-RULES/` 目录下
6. **避免硬编码**：不要在代码中硬编码时区，使用配置或环境变量

---

## 9. 常见错误

### ❌ 错误做法
```python
# 错误 1 - 使用网络 API
import requests
time = requests.get("http://worldtimeapi.org/api/ip").json()

# 错误 2 - 硬编码时区
from datetime import datetime
# 假设当前时区是 UTC+8，没有显式指定
now = datetime.now()
```

### ✅ 正确做法
```python
# 正确 1 - 使用 Python 内置函数
from datetime import datetime
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Asia/Shanghai"))

# 正确 2 - 分析问题时使用 MCP 工具
# （在 AI 对话中自动获取）
```

---

## 版本信息

- **文档版本**：1.1
- **创建日期**：2026-02-28
- **更新日期**：2026-05-29
- **适用项目**：ks1-simple-api
