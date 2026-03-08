# Go 版 API 代理服务 - 文档更新说明

**更新日期**: 2026-03-05

## 📝 更新内容

### 1. 明确不支持的功能

#### SDK 模式
- Go 版本不开发 SDK 模式
- 仅支持 HTTP 代理模式
- Python 版本的 SDK 模式功能不在 Go 版本的开发范围内

#### Windows 服务支持
- Go 版本不提供原生 Windows 服务支持
- 建议使用以下方式实现后台运行：
  - 任务计划程序（Windows 自带）
  - NSSM（第三方工具）
  - 其他进程管理工具

### 2. 文档更新

#### README.md
- ✅ 移除 Windows 服务部署章节
- ✅ 更新功能对比表，移除 Windows 服务支持相关内容
- ✅ 添加"不支持的功能"章节，明确说明 SDK 模式和 Windows 服务不支持
- ✅ 移除上游配置示例中的 `use_sdk` 字段

#### QUICKSTART.md
- ✅ 移除 Windows 服务部署相关的常见问题

#### SUMMARY.md
- ✅ 更新功能对比表，明确标注 SDK 模式和 Windows 服务不支持
- ✅ 移除 free5 上游配置中的 `use_sdk` 字段
- ✅ 更新"下一步计划"章节，移除 Windows 服务支持相关内容
- ✅ 添加"不支持的功能"章节

#### BUILD_TEST_REPORT.md
- ✅ 移除集成测试中的 Windows 服务部署测试项

#### upstreams/free5/config.yaml
- ✅ 移除 `use_sdk: true` 配置项

### 3. 代码说明

现有代码中包含 SDK 模式的框架代码（`proxy/proxy.go:298`），但实际功能未实现。这些代码保留用于：
- 理解项目架构
- 未来如需开发 SDK 模式时的参考

**重要**: 这些代码不会影响核心代理功能的正常运行。

## 🎯 功能完成度

### 已完成功能 (100%)
- ✅ 多上游负载均衡
- ✅ 权重轮询和随机选择
- ✅ 失效转移（3次重试，指数退避）
- ✅ 健康检查（定期检查，默认12小时）
- ✅ 限额统计（按调用次数）
- ✅ 动态权重调整
- ✅ Webhook 通知
- ✅ API Key 白名单验证
- ✅ 按 API Key 限额统计
- ✅ 令牌桶限流算法
- ✅ 调试模式
- ✅ 流量日志
- ✅ Web 调试面板
- ✅ 优雅重启（< 3秒）

### 不支持的功能
- ❌ SDK 模式（仅支持 HTTP 代理）
- ❌ Windows 服务支持（建议使用任务计划程序或 NSSM）

## 📊 测试状态

- ✅ 编译测试通过
- ✅ 功能测试通过（8/8）
- ✅ 健康检查通过
- ✅ 代理转发测试通过
- ✅ 13份完整测试报告

## 🚀 使用建议

### 后台运行（替代 Windows 服务）

#### 方式 1：使用 NSSM（推荐）
```bash
# 下载 NSSM: https://nssm.cc/download

# 安装服务
nssm install API-Proxy "D:\path\to\api-proxy.exe" -config "D:\path\to\config.yaml"

# 启动服务
nssm start API-Proxy

# 停止服务
nssm stop API-Proxy

# 卸载服务
nssm remove API-Proxy
```

#### 方式 2：使用任务计划程序
1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：启动时
4. 操作：启动程序 `api-proxy.exe -config config.yaml`
5. 设置：不管用户是否登录都要运行

#### 方式 3：使用 PowerShell 后台作业
```powershell
Start-Process -FilePath "api-proxy.exe" -ArgumentList "-config config.yaml" -WindowStyle Hidden
```

### SDK 模式替代方案

如果需要使用 SDK 模式的上游服务，建议：
1. 确认上游服务是否提供 HTTP API 接口
2. 如果提供，配置为 HTTP 代理模式
3. 如果不提供，考虑使用 Python 版本的代理服务

## 📝 文档完整性

所有文档已更新完成，明确说明了：
- ✅ 已完成的功能
- ✅ 不支持的功能
- ✅ 使用建议和替代方案
- ✅ 测试状态和报告

---

**项目状态**: 功能开发完成，文档更新完成，可以投入生产使用。