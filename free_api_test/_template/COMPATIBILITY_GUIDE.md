# 📋 模板配置兼容性说明

## ✅ multi_free_api_proxy 完全兼容配置

本模板已针对 `multi_free_api_proxy` 系列版本进行了优化和兼容。

---

## 🔍 自动加载机制

### multi_free_api_proxy 如何读取配置

`multi_free_api_proxy_v3_optimized.py` 通过以下步骤自动加载 API 配置：

```python
# 1. 扫描目录
api_dirs = list(free_api_dir.glob("free*"))

# 2. 读取 config.py
spec = importlib.util.spec_from_file_location(f"config_{api_name}", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# 3. 提取关键参数
api_key = getattr(config_module, "API_KEY", None)
base_url = getattr(config_module, "BASE_URL", None)
model_name = getattr(config_module, "MODEL_NAME", None)
use_proxy = getattr(config_module, "USE_PROXY", False)
use_sdk = getattr(config_module, "USE_SDK", False)
max_tokens = getattr(config_module, "MAX_TOKENS", config.DEFAULT_MAX_TOKENS)
default_weight = getattr(config_module, "DEFAULT_WEIGHT", 10)
endpoint = getattr(config_module, "ENDPOINT", "/v1/chat/completions")
response_format = getattr(config_module, "RESPONSE_FORMAT", {...})

# 4. 验证环境变量
env_key = f"{api_name.upper()}_API_KEY"
env_api_key = os.getenv(env_key)

# 5. 添加到可用列表
app_state.add_api(api_name, api_config)
```

---

## 📊 必需参数 vs 可选参数

### ✅ 必需参数（缺少则跳过）

| 参数 | 说明 | 示例 |
|------|------|------|
| `API_KEY` | API 密钥 | `os.getenv("FREE1_API_KEY")` |
| `BASE_URL` | API 基础 URL | `"https://api.openai.com"` |
| `MODEL_NAME` | 默认模型 | `"gpt-3.5-turbo"` |

### ⚙️ 推荐参数（有默认值）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `USE_PROXY` | `False` | 是否使用代理 |
| `USE_SDK` | `False` | 是否使用 SDK |
| `MAX_TOKENS` | `2000` | 最大 token 数 |
| `DEFAULT_WEIGHT` | `10` | 默认权重 |
| `ENDPOINT` | `/v1/chat/completions` | API 端点 |
| `RESPONSE_FORMAT` | 标准格式 | 响应解析配置 |

### 🎯 可选参数

| 参数 | 说明 |
|------|------|
| `AVAILABLE_MODELS` | 可用模型列表 |
| `TITLE_NAME` | 显示名称 |

---

## 🔧 特殊配置处理

### 1. 代理配置

```python
# config.py
USE_PROXY = True

# .env
HTTP_PROXY=http://127.0.0.1:7890
```

**multi_free_api_proxy 处理逻辑**：
```python
if use_proxy and config.HTTP_PROXY:
    proxies = {
        "http": config.HTTP_PROXY,
        "https": config.HTTP_PROXY
    }
```

### 2. SDK 模式

```python
# config.py
USE_SDK = True

# 需要在 multi_free_api_proxy 中添加特殊处理
if api_name == "free5":
    use_sdk = True
```

### 3. 响应格式配置

对于非标准响应格式的 API：

```python
RESPONSE_FORMAT = {
    "content_fields": ["content", "reasoning_content"],
    "merge_fields": False,
    "field_separator": "\n\n---\n\n",
    "use_reasoning_as_fallback": True
}
```

**multi_free_api_proxy 使用方式**：
```python
# 在响应处理中按优先级提取内容
for field in response_format["content_fields"]:
    content = message.get(field)
    if content:
        break
```

### 4. 权重配置

```python
# 高权重（优先使用）
DEFAULT_WEIGHT = 150

# 正常权重
DEFAULT_WEIGHT = 50

# 低权重（备用）
DEFAULT_WEIGHT = 10
```

**权重规则**：
- `> 100`: 特别权重，下次请求必然选中
- `50-100`: 正常使用
- `10-50`: 低频使用

---

## 🏷️ 环境变量命名规范

### 标准格式
```
FREE{编号}_API_KEY
```

### 示例
| 目录名 | 环境变量 |
|--------|----------|
| free1 | `FREE1_API_KEY` |
| free2 | `FREE2_API_KEY` |
| free10 | `FREE10_API_KEY` |
| free_new | `FREE_NEW_API_KEY` |

**重要**：环境变量必须在启动前设置或在 `.env` 文件中定义。

---

## 📁 文件结构要求

### 最小可行结构
```
free{编号}/
├── config.py    # 必需
└── .env         # 必需（或在全局 .env 中配置）
```

### 推荐结构
```
free{编号}/
├── config.py           # 必需
├── test_api.py         # 推荐
├── ask.txt            # 推荐（配合 test_api.py）
├── README.md          # 推荐
├── .env.example       # 推荐
├── .gitignore         # 推荐
└── .env               # 必需（不提交到 Git）
```

---

## 🧪 测试兼容性

### test_api.py 集成

模板中的 `test_api.py` 可直接被调用：

```bash
python free1/test_api.py
```

也支持在 `multi_free_api_proxy` 中作为健康检查：

```python
# multi_free_api_proxy_v3_optimized.py
def test_api_startup(api_name):
    # 使用与 test_api.py 相同的配置
    api_config = app_state.get_api(api_name)
    # ...
```

---

## 🔄 版本兼容性

### 已兼容的版本

| 版本 | 兼容性 | 说明 |
|------|--------|------|
| `multi_free_api_proxy.py` | ✅ 完全兼容 | 初代版本 |
| `multi_free_api_proxy_v3.py` | ✅ 完全兼容 | v3 版本 |
| `multi_free_api_proxy_v3_optimized.py` | ✅ 完全兼容 | 优化版本（推荐） |

### 特性对比

| 特性 | v1 | v3 | v3_optimized |
|------|----|----|--------------|
| 自动加载配置 | ✅ | ✅ | ✅ |
| 权重系统 | ❌ | ✅ | ✅ |
| 健康检查 | ✅ | ✅ | ✅ |
| 动态轮换 | ✅ | ✅ | ✅ |
| 并发控制 | ❌ | ✅ | ✅ |
| 响应格式配置 | ❌ | ✅ | ✅ |

---

## 🛠️ 配置迁移指南

### 从旧版本迁移

如果已有旧的 API 配置，需要更新以适配新版本：

#### 1. 添加缺失的参数
```python
# 旧配置
API_KEY = "xxx"
BASE_URL = "https://..."
MODEL_NAME = "gpt-3.5"

# 新配置（添加）
USE_PROXY = False
USE_SDK = False
MAX_TOKENS = 2000
DEFAULT_WEIGHT = 10
RESPONSE_FORMAT = {...}
```

#### 2. 更新环境变量
```bash
# 旧方式（硬编码）
API_KEY = "sk-xxx"

# 新方式（环境变量）
API_KEY = os.getenv("FREE1_API_KEY")
```

#### 3. 添加 .env 文件
```bash
# 创建 .env
FREE1_API_KEY=sk-xxx
```

---

## 📝 最佳实践清单

### ✅ DO（推荐）

- [x] 使用环境变量存储 API Key
- [x] 提供 `.env.example` 作为参考
- [x] 设置合理的 `DEFAULT_WEIGHT`
- [x] 配置 `RESPONSE_FORMAT` 以适配特殊 API
- [x] 使用 `test_api.py` 进行预测试
- [x] 在 README 中记录特殊配置

### ❌ DON'T（避免）

- [ ] 在代码中硬编码 API Key
- [ ] 将 `.env` 提交到 Git
- [ ] 使用不符合规范的目录名
- [ ] 忽略必需的三个参数
- [ ] 设置过高或过低的权重（超出 10-200 范围）

---

## 🔍 调试技巧

### 检查配置加载

```python
# 手动测试配置加载
from pathlib import Path
import importlib.util

config_file = Path("free1/config.py")
spec = importlib.util.spec_from_file_location("config", str(config_file))
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

print(f"API_KEY: {config_module.API_KEY}")
print(f"BASE_URL: {config_module.BASE_URL}")
print(f"MODEL_NAME: {config_module.MODEL_NAME}")
```

### 查看日志

启动 `multi_free_api_proxy` 时查看日志：

```
[调试] 脚本目录：D:\...\multi_free_api_proxy
[调试] API 目录：D:\...\free_api_test
[调试] 找到 8 个 API 目录：['free1', 'free2', ...]
[加载] free1: openrouter/free @ https://openrouter.ai
[加载] free2: gpt-3.5-turbo @ https://free.v36.cm
...
[配置] 已加载 8 个 API 配置
[权重] 默认权重已初始化：{'free1': 120, 'free2': 10, ...}
```

---

## 📖 相关文档

- [`TEMPLATE_USAGE.md`](./TEMPLATE_USAGE.md) - 详细使用指南
- [`QUICKSTART.md`](./QUICKSTART.md) - 快速开始
- [`README.md`](./README.md) - API 说明
- `multi_free_api_proxy/README.md` - 代理服务文档

---

**最后更新**: 2026-03-13  
**维护者**: Template System
