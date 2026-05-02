# API Key 泄露记录

> 本文件记录可能在 Git 历史中泄露的 API Key，请逐一检查并禁用

## 已泄露的 API Key（按文件分组）

### 1. api-proxy-go/upstreams/free3/config.yaml
- **Key**: `REVOKED_KEY`
- **操作**: 前往对应平台禁用此 Key

### 2. api-proxy-go/upstreams/free2/config.yaml
- **Key**: `REVOKED_KEY`
- **操作**: 前往对应平台禁用此 Key

### 3. v1/index.html
- **Key**: `REVOKED_KEY`
- **操作**: 前往对应平台禁用此 Key

### 4. v1/test-api.html
- **Key**: `REVOKED_KEY`
- **操作**: 同上（可能是同一个Key）

### 5. free_api_test/free10/贵阳基地二区glm-5API文档.md
- **Key**: `REVOKED_KEY`
- **操作**: 前往对应平台禁用此 Key

---

## 已清理的文件

以下文件的泄露 Key 已在工作区中清理（替换为 xxxx）：

| 文件 | 状态 |
|------|------|
| README.md | ✅ 已替换为 `sk-xxx` |
| MULTI_FREE_API_UPDATE.md | ⚠️ 仍含泄露Key，需提交后禁用 |

---

## 建议操作步骤

1. **立即登录各平台** - 前往 API 提供商后台禁用以上 Key
2. **更新 .env 文件** - 使用新的 Key 替换
3. **重新部署** - 确保服务使用新 Key
4. **验证服务** - 测试 API 调用是否正常

---

## 预防措施

- 始终使用环境变量存储 API Key
- 提交前运行 `git diff` 检查
- 使用 `.gitignore` 排除 `.env` 文件
- 定期检查敏感信息泄露
