# API Key 泄漏处置与预防

> 严重级别：🔴 **CRITICAL** — 必须在生产部署前完成。

## 一、需要立即吊销的密钥（已写入 git 历史）

数据来源：仓库根 `API_KEY_LEAKAGE_REPORT.md`

| # | 文件路径 | 密钥（部分掩码） | 推断厂商 | 处置 |
|---|---|---|---|---|
| 1 | `api-proxy-go/upstreams/free3/config.yaml` | `sk-t76O…7dD8` | free3 上游（自查） | 登录后台立即吊销 |
| 2 | `api-proxy-go/upstreams/free2/config.yaml` | `sk-RJeQ…ltLt` | free2 上游（自查） | 登录后台立即吊销 |
| 3 | `v1/index.html` | `sk-evyh…yixg` | 自查（可能是 OpenAI 兼容） | 登录后台立即吊销 |
| 4 | `v1/test-api.html` | `sk-evyh…yixg` | 同 #3 | 同 #3 |
| 5 | `free_api_test/free10/贵阳基地二区glm-5API文档.md` | `sk-tQkK…1Ty` | 智谱 GLM | 登录后台立即吊销 |

> 注意：即使工作区文件已脱敏，**git 历史中仍可被任何拿到 .git 目录的人检出**。吊销密钥是唯一彻底的补救手段。

## 二、git 历史清理（吊销之后建议执行）

```bash
# 1. 安装 git-filter-repo（推荐，比 filter-branch 快且安全）
pipx install git-filter-repo   # 或 brew/scoop

# 2. 镜像备份（重要！filter-repo 默认会重写历史）
git clone --mirror <repo-url> repo-backup.git

# 3. 准备替换清单 replacements.txt（每行一个）
sk-t76OXjTTXmPRzpNj8aF6F5F0508b488fB087A51c760e7dD8==>REVOKED_KEY
sk-RJeQTUufTH2oUcdLLyOIMZbxFQNwVZdi622xyZaCEJV7ltLt==>REVOKED_KEY
sk-evyhjiwnpfbhrimwavlzsvpcfmgpuxijqrmtnobjvjnqyixg==>REVOKED_KEY
sk-tQkKZU7OWNmJTNkYOugEh8XY2HkpA1Ty==>REVOKED_KEY

# 4. 执行重写
git filter-repo --replace-text replacements.txt

# 5. 强制推送（需所有协作者重新克隆）
git push --force --all
git push --force --tags
```

## 三、预防措施（已在本次 PR 中落地）

### 3.1 加固后的 .gitignore（仓库根）

新增条目阻止再次提交明文密钥：

```
# 上游配置（含 api_key）
api-proxy-go/upstreams/*/config.yaml
!api-proxy-go/upstreams/example/config.yaml

# 任何位置的 .env
**/.env
**/.env.*
!**/.env.example

# 编辑器临时密钥文件
*.pem
*.key
secrets/
```

### 3.2 推荐的 pre-commit 钩子

```bash
# 安装 gitleaks
go install github.com/zricethezav/gitleaks/v8@latest

# 创建 .git/hooks/pre-commit（chmod +x）
#!/usr/bin/env bash
gitleaks protect --staged --redact --no-banner || {
  echo "❌ 检测到疑似密钥，提交终止"
  exit 1
}
```

或集成到 `pre-commit` 框架：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/zricethezav/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

### 3.3 上游密钥配置规范

✅ **统一从环境变量加载**（已实现于 `config/config.go:loadAPIKeyFromEnv`）：

```yaml
# upstreams/free1/config.yaml — 不要写 api_key 明文
name: free1
address: https://openrouter.ai/api
# api_key 不写，由 OPENROUTER_API_KEY 环境变量注入
```

`.env`（已在 .gitignore 中）：

```bash
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
```

## 四、提交前自查清单

- [ ] `git diff --staged | grep -Ei 'sk-[a-zA-Z0-9]{20,}|api[_-]?key\s*[:=]'` 无结果
- [ ] gitleaks pre-commit 钩子已启用
- [ ] 新增上游目录使用 `example/config.yaml` 模板，密钥走环境变量
- [ ] `.env` 不在 `git status` 中

---

附：本次 PR 已在仓库根 `.gitignore` 增加 `api-proxy-go/upstreams/*/config.yaml` 等忽略规则，但**不会影响已经追踪的文件**——仍需手动 `git rm --cached` 已经入库的明文配置文件，并迁移到环境变量。
