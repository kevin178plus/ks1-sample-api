# AI NPC生成器 - 基础规则

## 核心要求

### 0. 语言规范
- 永远用中文回复
- 技术术语保持英文（如JSON、API、prompt等）
- 代码注释使用中文

### 0.1 Windows 控制台编码规范 ⚠️重要
- **禁止在 print() 输出中使用 emoji 字符**（如 ✅❌🔄⚡ 等）
- Windows CMD/PowerShell 默认使用 GBK 编码，无法处理 emoji
- 如需状态标识，请使用 ASCII 替代：
  - ✅ → `[OK]` 或 `✓`
  - ❌ → `[FAIL]` 或 `✗`
  - ⚠️ → `[WARN]`
  - 🔄 → `[RETRY]`
- 检查现有代码中的 emoji 并替换为 ASCII 字符

### 1. 时间和日期处理
- 按照 `__AI-RULES\TIME_RULES.md` 规范
- 所有时间戳使用ISO 8601格式
- 文件更新时记录 lastUpdated 注释

### 2. 操作日志记录
- 每次完成修改后，都要把操作内容**追加**到 operateLog.md
- 按照 `_AI-RULES\OPERATELOG_APPEND_ONLY.md` 规范
- 记录配置文件版本变更

### 3. 代码规范
- PHP文件规则按照 `_AI-RULES\php.md`
- HTML文件规范按照 `_AI-RULES\html.md`
- JavaScript代码遵循ES6+标准


## 质量保证规范

### 自动化测试要求

如果项目下有 LOCAL_TSET.md 文件，在网页类功能开发完成后，应该 自动调用 按文件说明开展本地化测试（默认要求是 调用 MCP浏览器 模拟操作 访问本地测试地址 开展基本功能的自动测试，自动修正发现的报错）


## 版本信息

- **文档版本：** 2.0
- **最后更新：** 2026-01-02
