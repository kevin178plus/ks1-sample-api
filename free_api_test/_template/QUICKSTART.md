# 🚀 快速开始 - 创建新的 Free API

## 5 分钟快速配置

### 1️⃣ 复制模板
```powershell
cd free_api_test
Copy-Item -Path "_template" -Destination "free{编号}" -Recurse
```

### 2️⃣ 修改 config.py
```python
TITLE_NAME = "你的 API 名称"
BASE_URL = "https://api.example.com"
MODEL_NAME = "gpt-3.5-turbo"
API_KEY = os.getenv("FREE{编号}_API_KEY")  # 确保编号匹配
DEFAULT_WEIGHT = 50  # 10-200
```

### 3️⃣ 配置 .env
在根目录的 `.env` 文件中添加:
```bash
FREE{编号}_API_KEY=你的实际_API_KEY
```

### 4️⃣ 测试
```bash
cd free{编号}
python test_api.py
```

### 5️⃣ 完成! 🎉
启动 `multi_free_api_proxy` 后会自动检测并使用新 API。

---

## ✅ 检查清单

- [ ] 目录名：`free{数字}`
- [ ] config.py 已更新
- [ ] .env 已配置 API Key
- [ ] test_api.py 测试通过
- [ ] README.md 已更新（可选）

---

## 📋 核心配置速查

| 参数 | 说明 | 示例 |
|------|------|------|
| TITLE_NAME | 显示名称 | "OpenAI" |
| BASE_URL | API地址 | "https://api.openai.com" |
| MODEL_NAME | 默认模型 | "gpt-3.5-turbo" |
| USE_PROXY | 代理开关 | False |
| DEFAULT_WEIGHT | 权重 | 50 |

---

## 🔧 常用命令

```bash
# 测试单个 API
cd free1 && python test_api.py

# 启动代理服务
cd multi_free_api_proxy
python multi_free_api_proxy_v3_optimized.py

# 查看日志
tail -f logs/*.log
```

---

**详细文档**: 查看 [`TEMPLATE_USAGE.md`](./TEMPLATE_USAGE.md)
