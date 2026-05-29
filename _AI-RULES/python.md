# Python 开发规范

适用于本项目的所有 Python 代码。

---

## 1. 代码风格

### 基本要求
- 遵循 **PEP 8** 规范
- 使用 **4 空格缩进**
- 行长不超过 **88 字符**（black 默认）
- 使用 **UTF-8** 编码

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | snake_case | `user_name`, `get_config()` |
| 类名 | PascalCase | `ConfigManager`, `TaskExecutor` |
| 常量 | UPPER_CASE | `MAX_RETRIES`, `DEFAULT_PORT` |
| 私有成员 | _leading_underscore | `_internal_var`, `__private_method()` |

---

## 2. 类型提示

### 必须使用类型提示
```python
from typing import Optional, List, Dict, Any

def process_message(
    message: str,
    user_id: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """处理消息并返回结果"""
    # 实现代码
    pass
```

### 复杂类型使用 TypeAlias
```python
from typing import TypedDict

class TaskResult(TypedDict):
    success: bool
    message: str
    data: Optional[Dict[str, Any]]

def execute_task(task_id: str) -> TaskResult:
    """执行任务并返回结果"""
    pass
```

---

## 3. 注释规范

### 中文注释
- 所有注释使用中文
- 解释"为什么"，而非"是什么"
- 函数必须添加 docstring

### Docstring 格式
```python
def send_notification(
    user_id: str,
    message: str,
    priority: str = "normal"
) -> bool:
    """
    发送通知给指定用户

    Args:
        user_id: 用户 ID
        message: 通知消息内容
        priority: 优先级（normal/high/urgent）

    Returns:
        发送成功返回 True，失败返回 False

    Raises:
        ValueError: 当 user_id 为空时
    """
    if not user_id:
        raise ValueError("user_id 不能为空")

    # 实现代码
    return True
```

---

## 4. 错误处理

### 使用特定异常
```python
# ✅ 正确
raise ValueError("配置参数无效")
raise FileNotFoundError("配置文件不存在")

# ❌ 错误
raise Exception("出错了")
```

### 捕获特定异常
```python
# ✅ 正确
try:
    config = load_config()
except FileNotFoundError:
    logger.warning("配置文件不存在，使用默认配置")
    config = default_config()
except ValueError as e:
    logger.error(f"配置文件格式错误: {e}")
    raise

# ❌ 错误
try:
    config = load_config()
except Exception as e:
    print(e)  # 不应该捕获所有异常
```

---

## 5. 日志规范

### 使用 logging 模块
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: Dict[str, Any]) -> bool:
    logger.info(f"开始处理数据: {data['id']}")
    try:
        # 处理逻辑
        logger.debug("数据处理成功")
        return True
    except Exception as e:
        logger.error(f"数据处理失败: {e}", exc_info=True)
        return False
```

### 日志级别使用
- **DEBUG**: 详细调试信息
- **INFO**: 一般信息（启动、完成等）
- **WARNING**: 警告信息（可恢复的问题）
- **ERROR**: 错误信息（功能受影响）
- **CRITICAL**: 严重错误（系统崩溃）

---

## 6. 文件结构

### 标准结构
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块简短描述

详细描述（可选）
"""

# 标准库导入
import os
import sys
from typing import Optional, Dict, Any

# 第三方库导入
import requests
from flask import Flask

# 本地模块导入
from app.config import Config
from app.logger import setup_logger

# 常量定义
MAX_RETRIES = 3
TIMEOUT = 30

# 全局变量
logger = setup_logger(__name__)

# 类定义
class MyClass:
    pass

# 函数定义
def my_function():
    pass

# 主程序
if __name__ == "__main__":
    pass
```

---

## 7. 安全规范

### 路径操作
```python
from pathlib import Path

# ✅ 正确 - 使用 Path
def safe_path_join(base: str, relative: str) -> Path:
    """安全地拼接路径，防止目录遍历攻击"""
    base_path = Path(base).resolve()
    target_path = (base_path / relative).resolve()

    # 确保目标路径在基础路径内
    if not str(target_path).startswith(str(base_path)):
        raise ValueError(f"非法路径: {relative}")

    return target_path

# ❌ 错误 - 直接拼接
def unsafe_path_join(base: str, relative: str) -> str:
    return os.path.join(base, relative)  # 可能被 "../" 攻击
```

### 用户输入验证
```python
def validate_user_input(user_id: str, command: str) -> bool:
    """验证用户输入"""
    # 检查是否为空
    if not user_id or not command:
        return False

    # 检查长度
    if len(command) > 1000:
        return False

    # 检查危险字符
    dangerous_chars = [';', '|', '&', '`', '$', '(', ')']
    if any(char in command for char in dangerous_chars):
        return False

    return True
```

---

## 8. 性能优化

### 避免重复计算
```python
# ❌ 错误
for item in items:
    result = complex_calculation(item)  # 重复计算
    process(result)

# ✅ 正确
cache = {}
for item in items:
    if item not in cache:
        cache[item] = complex_calculation(item)
    process(cache[item])
```

### 使用生成器
```python
# ✅ 正确 - 处理大数据时使用生成器
def process_large_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:  # 逐行读取，内存友好
            yield process_line(line)

# ❌ 错误 - 一次性读取所有数据
def process_large_file_bad(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()  # 内存占用大
    return [process_line(line) for line in lines]
```

---

## 9. 测试规范

### 编写可测试代码
```python
# ✅ 正确 - 依赖注入
class TaskExecutor:
    def __init__(self, notifier):
        self.notifier = notifier

    def execute(self, task) -> bool:
        result = self._run_task(task)
        if result:
            self.notifier.send("任务完成")
        return result

# ❌ 错误 - 硬编码依赖
class TaskExecutor:
    def __init__(self):
        self.notifier = Notifier()  # 难以测试

    def execute(self, task) -> bool:
        result = self._run_task(task)
        if result:
            Notifier().send("任务完成")  # 无法 mock
        return result
```

---

## 10. 常用工具

### 格式化工具
```bash
# Black - 代码格式化
black .

# isort - import 排序
isort .

# autoflake - 删除未使用的 import
autoflake --remove-all-unused-imports --in-place .
```

### 代码检查
```bash
# pylint - 代码质量检查
pylint .

# flake8 - 风格检查
flake8 .

# mypy - 类型检查
mypy .
```

---

## 11. 最佳实践

### 使用 with 语句管理资源
```python
# ✅ 正确
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# ❌ 错误
f = open('config.yaml', 'r', encoding='utf-8')
config = yaml.safe_load(f)
f.close()  # 可能被异常跳过
```

### 使用上下文管理器
```python
from contextlib import contextmanager

@contextmanager
def temp_directory():
    """临时目录上下文管理器"""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)

# 使用
with temp_directory() as temp_dir:
    process_files(temp_dir)
```

---

## 版本信息

- **文档版本**：1.0
- **创建日期**：2026-02-28
- **适用项目**：ks1-simple-api
