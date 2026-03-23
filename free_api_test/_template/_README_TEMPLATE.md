# 📦 Free API 模板目录

> **用途**: 用于快速创建新的 Free API 配置目录，完全兼容 `multi_free_api_proxy` 系统

---

## 🎯 快速开始

### 5 分钟配置新 API

```powershell
# 1. 复制模板
cd free_api_test
Copy-Item -Path "_template" -Destination "free10" -Recurse

# 2. 修改 config.py
# 编辑 free10/config.py，更新 API 信息

# 3. 配置 .env
# 在根目录 .env 文件中添加：FREE10_API_KEY=你的密钥

# 4. 测试
cd free10
python test_api.py

# ✅ 完成！启动 multi_free_api_proxy 会自动检测
```

**详细步骤**: 查看 [`QUICKSTART.md`](./QUICKSTART.md)

---

## 📁 模板结构

```
_template/
├── 📄 config.py           # ⭐ API 核心配置（必需）
├── 🧪 test_api.py         # ⭐ 测试脚本（推荐）
├── 💬 ask.txt            # ⭐ 测试提示词（推荐）
├── 📖 README.md          # 📝 API 说明文档（推荐）
├── 🔧 .env.example       # 📋 环境变量示例
├── 🚫 .gitignore         # 🔒 Git 忽略文件
├── 📘 TEMPLATE_USAGE.md  # 📚 完整使用指南
└── 📊 COMPATIBILITY_GUIDE.md  # 🔗 兼容性说明
```

### 核心文件说明

| 文件 | 重要性 | 用途 | 修改频率 |
|------|--------|------|----------|
| `config.py` | ⭐⭐⭐ | API 配置（URL、模型、密钥等） | 每次必改 |
| `test_api.py` | ⭐⭐ | 测试 API 可用性 | 一般不改 |
| `ask.txt` | ⭐ | 测试用提示词 | 可选修改 |
| `README.md` | ⭐ | API 使用说明 | 建议更新 |
| `.env.example` | ⭐ | 环境变量参考 | 可选修改 |

---

## 📚 文档导航

### 🚀 新手入门
1. **[QUICKSTART.md](./QUICKSTART.md)** - 5 分钟快速配置
2. **[TEMPLATE_USAGE.md](./TEMPLATE_USAGE.md)** - 完整使用指南

### 🔧 高级配置
3. **[COMPATIBILITY_GUIDE.md](./COMPATIBILITY_GUIDE.md)** - multi_free_api_proxy 兼容性详解
4. **[README.md](./README.md)** - API 说明文档模板

### 📖 参考资源
- **配置文件详解**: `config.py` 中的注释
- **测试脚本**: `test_api.py` 中的代码注释
- **环境变量**: `.env.example` 示例

---

## ✅ 配置检查清单

创建新 API 时的完整检查清单：

### 基础配置
- [ ] 复制 `_template` 到 `free{编号}`
- [ ] 重命名目录为正确编号（如 `free10`）
- [ ] 修改 `config.py` 中的基本信息
  - [ ] `TITLE_NAME` - API 显示名称
  - [ ] `BASE_URL` - API地址
  - [ ] `MODEL_NAME` - 默认模型
  - [ ] `API_KEY` - 确保环境变量名与编号匹配
  - [ ] `USE_PROXY` - 是否需要代理
  - [ ] `DEFAULT_WEIGHT` - 设置权重（10-200）

### 环境配置
- [ ] 在根目录 `.env` 文件中添加 API Key
  ```bash
  FREE{编号}_API_KEY=你的实际密钥
  ```
- [ ] （可选）创建目录专属 `.env` 文件

### 测试验证
- [ ] 运行 `python test_api.py` 测试
- [ ] 确认测试通过
- [ ] 在 `multi_free_api_proxy` 中验证加载

### 文档完善
- [ ] 更新 `README.md` 中的 API 信息
- [ ] （可选）更新 `.env.example`
- [ ] （可选）记录特殊配置和注意事项

---

## 🔍 multi_free_api_proxy 集成

### 自动检测机制

当你启动 `multi_free_api_proxy` 时，系统会：

1. **扫描目录** → 查找所有 `free*` 目录
2. **加载配置** → 读取每个目录的 `config.py`
3. **验证环境** → 检查环境变量是否配置
4. **健康检查** → 测试 API 是否可用
5. **加入轮换** → 可用的 API 加入负载均衡池

### 配置要求

为确保被 `multi_free_api_proxy` 正确识别，必须满足：

| 要求 | 说明 | 检查项 |
|------|------|--------|
| 目录命名 | `free{数字}` | ✅ 符合规范 |
| config.py | 必须存在 | ✅ 已包含 |
| API_KEY | 不能为空 | ✅ 从环境变量读取 |
| BASE_URL | 有效 URL | ✅ 需配置 |
| MODEL_NAME | 有效模型 | ✅ 需配置 |
| 环境变量 | 格式 `FREE{编号}_API_KEY` | ✅ 按规范配置 |

---

## 🛠️ 常用命令速查

```bash
# 创建新 API 目录
Copy-Item -Path "_template" -Destination "free{编号}" -Recurse

# 测试单个 API
cd free{编号}
python test_api.py

# 启动代理服务（自动加载所有 API）
cd ..\multi_free_api_proxy
python multi_free_api_proxy_v3_optimized.py

# 查看调试信息
# 启动日志会显示：
# [加载] free{编号}: {model} @ {base_url}
# [权重] 默认权重已初始化
```

---

## 📊 配置示例对比

### 示例 1: OpenRouter (free1)
```python
# config.py
TITLE_NAME = "OpenRouter"
BASE_URL = "https://openrouter.ai"
MODEL_NAME = "openrouter/free"
USE_PROXY = True
DEFAULT_WEIGHT = 120  # 高权重优先使用

# .env
FREE1_API_KEY=sk_xxxxxxxxxxxx
```

### 示例 2: 免费 API (free3)
```python
# config.py
TITLE_NAME = "FreeChatGPT"
BASE_URL = "https://free.v36.cm"
MODEL_NAME = "gpt-3.5-turbo"
USE_PROXY = False
DEFAULT_WEIGHT = 10  # 低权重备用

# .env
FREE3_API_KEY=free_xxxxxxxxxxxx
```

### 示例 3: NVIDIA (free7)
```python
# config.py
TITLE_NAME = "NVIDIA"
BASE_URL = "https://integrate.api.nvidia.com/"
MODEL_NAME = "minimaxai/minimax-m2.5"
USE_PROXY = False
DEFAULT_WEIGHT = 50  # 正常权重
MAX_TOKENS = 8192

# 特殊响应格式配置
RESPONSE_FORMAT = {
    "content_fields": ["content", "reasoning_content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": True
}

# .env
FREE7_API_KEY=nvdk_xxxxxxxxxxxx
```

---

## 🎯 权重配置建议

| 场景 | 推荐权重 | 说明 |
|------|----------|------|
| **主力 API** | 100-200 | 稳定、快速、优先使用 |
| **正常 API** | 50-100 | 日常使用，普通优先级 |
| **备用 API** | 10-50 | 偶尔使用，备选方案 |
| **测试 API** | 10 | 仅用于测试，低频使用 |

**自动调整规则**:
- 连续失败 → 权重自动降低
- 成功率高 → 权重逐渐恢复
- 权重 > 100 → 下次请求必然选中

---

## 🔒 安全提醒

### ⚠️ 重要：保护 API Key

1. **不要提交 `.env` 到 Git**
   - `.gitignore` 已配置忽略 `.env`
   - 手动检查：`git status` 确认 `.env` 未跟踪

2. **使用 `.env.example` 作为模板**
   ```bash
   # .env.example（可提交）
   FREE1_API_KEY=your_key_here
   
   # .env（不提交）
   FREE1_API_KEY=sk-actual_secret_key
   ```

3. **定期更换 API Key**
   - 发现泄露立即更换
   - 设置使用限额

---

## 🐛 常见问题排查

### Q1: API 不被识别？
**检查步骤**:
1. 目录名是否为 `free{数字}` 格式
2. `config.py` 是否存在
3. 环境变量是否正确配置
4. 重启 `multi_free_api_proxy`

### Q2: 测试失败？
**排查方法**:
```bash
# 1. 单独测试 API
cd free{编号}
python test_api.py

# 2. 查看详细错误
# 查看终端输出的错误信息

# 3. 检查网络连接
ping api.example.com

# 4. 验证 API Key
echo $FREE{编号}_API_KEY
```

### Q3: 权重不生效？
**可能原因**:
- 权重值超出范围（应在 10-200）
- API 在黑名单中
- 配置文件未重新加载

**解决方法**:
```bash
# 重启服务
# 查看日志中的权重初始化信息
# [权重] 默认权重已初始化：{'free1': 120, ...}
```

---

## 📞 获取帮助

### 相关文档
- 📘 [完整使用指南](./TEMPLATE_USAGE.md)
- 🔗 [兼容性说明](./COMPATIBILITY_GUIDE.md)
- 🚀 [快速开始](./QUICKSTART.md)
- 📖 [API 说明模板](./README.md)

### 外部资源
- `multi_free_api_proxy/README.md` - 代理服务主文档
- `free_api_test/README.md` - Free API 测试总览
- 各 API 提供商的官方文档

---

## 📝 更新日志

### v1.0 - 2026-03-13
- ✨ 初始版本发布
- ✅ 完全兼容 multi_free_api_proxy_v3_optimized
- 📚 提供完整的中文文档
- 🔧 支持所有主流配置选项
- 🎯 优化权重系统
- 📖 新增兼容性指南

---

## 🎉 开始使用

现在你已经了解了所有必要信息，开始配置你的第一个 Free API 吧！

```bash
# 立即开始
cd free_api_test
Copy-Item -Path "_template" -Destination "free10" -Recurse
cd free10
# 编辑 config.py 和 .env
python test_api.py
```

**祝你使用愉快！** 🚀

---

<div align="center">

**模板版本**: v1.0  
**最后更新**: 2026-03-13  
**维护状态**: ✅ 活跃维护

</div>
