# API Key 泄漏处置与预防

> 严重级别：🔴 **CRITICAL** — 已在 2025-05-07 完成处置

## 一、已吊销的密钥

| # | 文件路径 | 密钥（部分掩码） | 推断厂商 | 状态 |
|---|---|---|---|---|
| 1 | `api-proxy-go/upstreams/free3/config.yaml` | `sk-t76O…7dD8` | free3 上游 | ✅ 已吊销 |
| 2 | `api-proxy-go/upstreams/free2/config.yaml` | `sk-RJeQ…ltLt` | free2 上游 | ✅ 已吊销 |
| 3 | `v1/index.html` | `sk-evyh…yixg` | OpenAI 兼容 | ✅ 已吊销 |
| 4 | `v1/test-api.html` | `sk-evyh…yixg` | 同 #3 | ✅ 已吊销 |
| 5 | `free_api_test/free10/贵阳基地二区glm-5API文档.md` | `sk-tQkK…1Ty` | 智谱 GLM | ✅ 已吊销 |

## 二、Git 历史清理（已完成）

### 操作记录

```bash
# 1. 镜像备份
git clone --mirror <repo-url> ks1-sample-api-backup.git

# 2. 安装 git-filter-repo
pip install git-filter-repo

# 3. 替换泄露密钥
replacements.txt 内容:
sk-t76OXjTTXmPRzpNj8aF6F5F0508b488fB087A51c760e7dD8==>REVOKED_KEY
sk-RJeQTUufTH2oUcdLLyOIMZbxFQNwVZdi622xyZaCEJV7ltLt==>REVOKED_KEY
sk-evyhjiwnpfbhrimwavlzsvpcfmgpuxijqrmtnobjvjnqyixg==>REVOKED_KEY
sk-tQkKZU7OWNmJTNkYOugEh8XY2HkpA1Ty==>REVOKED_KEY

# 4. 执行重写
git filter-repo --replace-text replacements.txt

# 5. 强制推送
git push --force --all
git push --force --tags
```

### 清理结果

- 历史提交中密钥已全部替换为 `REVOKED_KEY`
- 20 个含 api_key 的配置文件已从 git 移除追踪
- 提交: `e485d12 security: 移除敏感配置文件追踪并加固.gitignore`

## 三、预防措施

### 3.1 .gitignore 加固

```gitignore
# 上游配置（含 api_key）
api-proxy-go/upstreams/*/config.yaml
!api-proxy-go/upstreams/example/config.yaml

# 任何位置的 .env
**/.env
**/.env.*
!**/.env.example

# 私钥 / 凭据
*.pem
*.key
secrets/
```

### 3.2 pre-commit 钩子

已配置 gitleaks 检测：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.0
    hooks:
      - id: gitleaks
```

**启用方式：**
```bash
pip install pre-commit
pre-commit install
```

### 3.3 上游密钥配置规范

统一从环境变量加载（已实现于 `config/config.go:loadAPIKeyFromEnv`）：

```yaml
# upstreams/free1/config.yaml — 不要写 api_key 明文
name: free1
address: https://openrouter.ai/api
# api_key 不写，由环境变量注入
```

## 四、协作者注意事项

1. **重新克隆仓库**：历史已重写，所有协作者需重新克隆
2. **启用 pre-commit**：运行 `pre-commit install`
3. **配置文件**：上游配置需从 `.env` 读取，不要提交含 api_key 的 config.yaml

---

*最后更新: 2025-05-07*