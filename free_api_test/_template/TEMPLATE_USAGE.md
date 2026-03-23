# Free API 模板目录使用指南

## 📁 模板结构

`_template` 目录是一个完整的模板，用于创建新的 Free API 子目录。

### 目录结构
```
free{编号}/
├── config.py           # API 配置（必需）
├── test_api.py         # 测试脚本（必需）
├── ask.txt            # 测试提示词（必需）
├── README.md          # 说明文档（推荐）
├── .env.example       # 环境变量示例（可选）
└── .env               # 实际配置（不提交到 Git）
```

## 🚀 快速开始

### 步骤 1: 复制模板
```bash
# Windows PowerShell
cd free_api_test
Copy-Item -Path "_template" -Destination "free{新编号}" -Recurse

# 或使用文件资源管理器手动复制
```

### 步骤 2: 修改配置文件

#### 2.1 编辑 `config.py`
```python
# 修改以下内容：
TITLE_NAME = "你的 API 名称"
BASE_URL = "https://api.你的提供商.com"
MODEL_NAME = "默认模型名称"
USE_PROXY = False  # 是否需要代理
USE_SDK = False    # 是否使用官方 SDK
DEFAULT_WEIGHT = 10  # 权重（10-200）

# 确保环境变量名称匹配编号
API_KEY = os.getenv("FREE{编号}_API_KEY")
```

#### 2.2 编辑 `.env.example`
```bash
FREE{编号}_API_KEY=你的 API_KEY_占位符
```

#### 2.3 创建 `.env` 文件（不提交到 Git）
```bash
FREE{编号}_API_KEY=你的实际_API_KEY
```

### 步骤 3: 测试 API
```bash
cd free{新编号}
python test_api.py
```

### 步骤 4: 集成到 multi_free_api_proxy
配置完成后，`multi_free_api_proxy` 会自动检测并加载新的 API 配置。

## 🔧 配置详解

### config.py 关键参数

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| TITLE_NAME | 服务显示名称 | - | ✅ |
| API_KEY | API 密钥 | - | ✅ |
| BASE_URL | API 基础 URL | - | ✅ |
| MODEL_NAME | 默认模型 | - | ✅ |
| USE_PROXY | 是否使用代理 | False | ❌ |
| USE_SDK | 是否使用 SDK | False | ❌ |
| MAX_TOKENS | 最大 token 数 | 2000 | ❌ |
| DEFAULT_WEIGHT | 默认权重 | 10 | ❌ |
| RESPONSE_FORMAT | 响应格式配置 | 标准格式 | ❌ |
| AVAILABLE_MODELS | 可用模型列表 | [] | ❌ |
| ENDPOINT | API 端点路径 | /v1/chat/completions | ❌ |

### RESPONSE_FORMAT 配置

如果 API 返回的格式特殊，需要配置此参数：

```python
RESPONSE_FORMAT = {
    # 内容字段优先级（从高到低）
    "content_fields": ["content", "reasoning_content"],
    
    # 是否合并多个字段
    "merge_fields": False,
    
    # 字段分隔符
    "field_separator": "\n\n---\n\n",
    
    # 是否使用 reasoning_content 作为回退
    "use_reasoning_as_fallback": True
}
```

## 📝 环境变量命名规则

- free1 → `FREE1_API_KEY`
- free2 → `FREE2_API_KEY`
- free3 → `FREE3_API_KEY`
- ...
- free10 → `FREE10_API_KEY`

## 🔍 multi_free_api_proxy 集成

### 自动加载机制

`multi_free_api_proxy_v3_optimized.py` 会：

1. **扫描目录**：自动扫描 `free_api_test/free*` 目录
2. **加载配置**：读取每个目录下的 `config.py`
3. **验证环境**：检查对应的环境变量是否存在
4. **健康检查**：启动时测试 API 可用性
5. **动态轮换**：根据权重和成功率自动选择 API

### 兼容性保证

模板已确保与以下组件兼容：

- ✅ `multi_free_api_proxy_v3.py`
- ✅ `multi_free_api_proxy_v3_optimized.py`
- ✅ `local_api_proxy.py`
- ✅ 独立的 `test_api.py` 脚本

## 🛠️ 常见问题

### Q1: 如何调试配置问题？
```bash
# 查看加载日志
python -c "from multi_free_api_proxy.multi_free_api_proxy_v3_optimized import load_api_configs; load_api_configs()"
```

### Q2: API 不被识别？
检查：
1. 目录名是否符合 `free{数字}` 格式
2. `config.py` 是否存在
3. 环境变量是否正确配置
4. 必需的参数是否都有值

### Q3: 如何使用代理？
在 `.env` 中配置：
```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```
并在 `config.py` 中设置 `USE_PROXY = True`

### Q4: 权重如何工作？
- **10-50**: 低频使用（备用 API）
- **50-100**: 正常使用
- **100-200**: 高频使用（优先 API）
- **>100**: 权重大于此值时，下次请求必然选中

系统会根据 API 的成功率动态调整权重。

## 📋 检查清单

创建新 API 时的检查清单：

- [ ] 复制 `_template` 到 `free{编号}`
- [ ] 修改 `config.py` 中的基本信息
- [ ] 更新环境变量命名
- [ ] 创建 `.env` 文件并配置 API Key
- [ ] 运行 `python test_api.py` 测试
- [ ] 更新 `README.md` 文档
- [ ] 在 `multi_free_api_proxy` 中验证加载
- [ ] （可选）添加特殊响应格式配置
- [ ] （可选）配置 AVAILABLE_MODELS

## 🎯 最佳实践

1. **先测试后集成**：先用 `test_api.py` 单独测试，确认无误后再集成
2. **合理设置权重**：根据 API 的稳定性和速度设置权重
3. **详细记录**：在 README 中记录 API 特点和注意事项
4. **使用环境变量**：不要在代码中硬编码 API Key
5. **备份配置**：保留 `.env.example` 作为参考

## 📦 模板更新

如果模板有更新，现有目录不会自动更新。需要手动同步：

```bash
# 比较差异
diff -r _template free{编号}

# 选择性更新特定文件
```

## 🔗 相关文档

- `multi_free_api_proxy/README.md` - 代理服务主文档
- `free_api_test/README.md` - Free API 测试总览
- 各 API 目录下的独立文档

---

**最后更新**: 2026-03-13
**版本**: 1.0
