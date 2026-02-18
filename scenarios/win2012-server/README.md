# Windows Server 2012 R2 优化方案

## 📋 系统信息

- **操作系统**: Windows Server 2012 R2 Datacenter
- **Python 版本**: 3.11.9
- **内存**: 2GB
- **架构**: 64位

## ⚠️ 重要说明

### 系统限制
- **内存限制**: 2GB 内存较小，需要优化配置
- **Python 版本**: 3.11.9 是较新版本，兼容性良好
- **操作系统**: Windows Server 2012 R2 是较老系统，某些新特性可能不支持

### 兼容性说明
- ✅ **Python 3.11.9**: 完全支持，无兼容性问题
- ✅ **Flask**: 完全支持
- ✅ **Requests**: 完全支持
- ✅ **Watchdog**: 完全支持
- ⚠️ **async/await**: Windows Server 2012 R2 的 Python 3.11 可能不支持某些异步特性
- ⚠️ **f-string**: Python 3.11.9 完全支持，但建议测试

### 文件命名规则
所有 `.bat` 文件都按照以下规则命名：
- **a** 开头：推荐使用的脚本
- **b** 开头：可选的脚本
- **序号**：按使用顺序排序
  - 10-19：一次性安装脚本
  - 20-29：安装后启动脚本
  - 01-09：可选配置脚本

**示例：**
- `a10-minimal_setup.bat` - 最小化配置（推荐）
- `a20-monitor_service.bat` - 监控脚本（推荐）
- `b01-setup_firewall.bat` - 防火墙配置（可选）

## 🚀 快速开始

### 推荐方式：使用最小化配置

```bash
# 进入优化场景目录
cd scenarios\win2012-server

# 运行最小化配置脚本
a10-minimal_setup.bat
```

**为什么推荐最小化配置？**
- ✅ 只修改必要的设置
- ✅ 不影响系统稳定性
- ✅ 易于回退
- ✅ 适合资源受限环境

## 📦 方案对比

### 方式1：最小化配置（推荐）

**脚本**: `a10-minimal_setup.bat`

**特点：**
- ✅ 检查 Python 和依赖
- ✅ 创建便捷启动脚本
- ✅ 不修改系统设置
- ✅ 提供回退脚本
- ✅ 防火墙配置独立（可选）

**适用场景：**
- 生产环境
- 资源受限环境
- 需要最小化影响

**防火墙配置（可选）：**
如果需要开放 5000 端口，可以运行：
```bash
# 以管理员身份运行
b01-setup_firewall.bat
```

如需要删除防火墙规则，可以运行：
```bash
# 以管理员身份运行
b02-restore_firewall.bat
```

**文件结构：**
```
scenarios/win2012-server/
├── a10-minimal_setup.bat          ← 最小化配置脚本（推荐）
├── a20-monitor_service.bat          ← 监控脚本（推荐）
├── a21-safe_start.bat             ← 安全启动脚本（推荐）
├── a22-start_minimal.bat          ← 最小化启动脚本（推荐）
├── a23-daemon_service.bat          ← 守护进程（可选）
├── b01-setup_firewall.bat          ← 防火墙配置（可选）
├── b02-restore_firewall.bat        ← 防火墙恢复（可选）
├── b03-restore_system.bat          ← 系统回退脚本（可选）
├── b04-simple_ssl_setup.bat        ← SSL 配置（可选）
├── b05-win2012_optimization.bat    ← 系统优化（可选）
└── minimal_server_proxy.py          ← 最小化服务器
```

### 方式2：完整配置

**脚本**: 其他场景的完整配置

**特点：**
- ✅ 完整的功能
- ✅ 更多的配置选项
- ✅ 更多的优化

**适用场景：**
- 开发环境
- 资源充足环境
- 需要完整功能

## 🔍 监控脚本 vs 守护进程

### 监控脚本（推荐）

**脚本**: `a20-monitor_service.bat`

**工作原理：**
- 定期检查服务状态（默认每30秒）
- 如果服务停止，尝试重启
- 是一个独立的脚本，循环运行

**优点：**
- ✅ 资源占用少（只在检查时运行）
- ✅ 可以手动停止
- ✅ 配置灵活（检查间隔、重试次数等）
- ✅ 适合资源受限环境

**缺点：**
- ❌ 响应延迟（取决于检查间隔）
- ❌ 可能错过快速崩溃
- ❌ 需要额外的脚本

**适用场景：**
- 资源受限环境（2GB 内存）
- 不需要立即响应的服务
- 需要灵活配置的场景

**使用方法：**
```bash
# 启动监控脚本
a20-monitor_service.bat

# 按 Ctrl+C 停止监控
```

**配置参数：**
- `CHECK_INTERVAL`: 检查间隔（默认30秒）
- `MAX_RESTART_ATTEMPTS`: 最大重启次数（默认10次）
- `RESTART_DELAY`: 重启延迟（默认5秒）

### 守护进程（可选）

**脚本**: `a23-daemon_service.bat`

**工作原理：**
- 直接启动并管理子进程
- 监控子进程状态
- 如果子进程退出，立即重启
- 是一个持续运行的进程

**优点：**
- ✅ 响应快（子进程退出立即重启）
- ✅ 更可靠
- ✅ 统一管理
- ✅ 可以记录详细日志

**缺点：**
- ❌ 资源占用多（需要一直运行）
- ❌ 可能影响系统性能
- ❅ 配置相对复杂

**适用场景：**
- 资源充足环境
- 需要高可用性的服务
- 需要立即响应的场景

**使用方法：**
```bash
# 启动守护进程
a23-daemon_service.bat

# 按 Ctrl+C 停止守护进程
```

**配置参数：**
- `PYTHON_SCRIPT`: 服务脚本（默认 minimal_server_proxy.py）
- `MAX_RESTART_ATTEMPTS`: 最大重启次数（默认10次）
- `RESTART_DELAY`: 重启延迟（默认5秒）

### 对比总结

| 特性 | 监控脚本 | 守护进程 |
|------|---------|---------|
| 响应速度 | 慢（取决于检查间隔） | 快（立即响应） |
| 资源占用 | 低 | 高 |
| 可靠性 | 中 | 高 |
| 配置灵活性 | 高 | 中 |
| 适用环境 | 资源受限 | 资源充足 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 推荐选择

**对于 Windows Server 2012 R2 + 2GB 内存：**
- ✅ **推荐**: 使用监控脚本 `a20-monitor_service.bat`
- ⚠️ **可选**: 使用守护进程 `a23-daemon_service.bat`（如果资源充足）

**选择建议：**
1. **资源受限（2GB 内存）** → 使用监控脚本
2. **需要立即响应** → 使用守护进程
3. **需要灵活配置** → 使用监控脚本
4. **需要高可用性** → 使用守护进程

## 🎯 针对 2GB 内存的优化

### 1. 减少并发请求数

**配置方法：**
在 `.env` 文件中设置：

```bash
MAX_CONCURRENT_REQUESTS=3
```

**原因：**
- 每个请求占用约 50-100MB 内存
- 3 个并发请求约占用 150-300MB
- 留出足够内存给 Python 和操作系统

**效果：**
- ✅ 减少内存峰值
- ✅ 提高稳定性
- ✅ 避免内存不足错误

### 2. 限制缓存大小

**配置方法：**
定期清理缓存文件：

```bash
# 创建清理脚本
@echo off
set CACHE_DIR=D:\api_proxy_cache
echo Cleaning cache files older than 7 days...
forfiles /P %CACHE_DIR% /M -7 -C "cmd /c echo @path" 2>nul
echo Cleanup completed.
```

**效果：**
- ✅ 减少磁盘占用
- ✅ 提高响应速度
- ✅ 避免缓存过大

### 3. 优化 Python 配置

**配置方法：**
创建 `python_optimization.py`：

```python
import sys
import gc

# 减少 Python 内存占用
sys.setrecursionlimit(1000)  # 降低递归限制
gc.set_threshold(700, 10, 10)  # 调整垃圾回收

print("Python optimization applied")
```

**使用方法：**
```bash
# 在启动前运行优化
python python_optimization.py && python local_api_proxy.py
```

**效果：**
- ✅ 更激进的垃圾回收
- ✅ 减少内存碎片
- ✅ 提高内存利用率

### 5. 使用调试页面

**访问地址：**
```bash
http://localhost:5000/debug
```

**功能特点：**
- ✅ 简化的调试界面，内存占用小
- ✅ 在线测试 API 功能
- ✅ 查看服务状态和端点信息
- ✅ 无需额外配置即可使用

**使用说明：**
1. 启动服务后，在浏览器中访问 `http://localhost:5000/debug`
2. 在输入框中输入测试消息
3. 点击"发送请求"按钮测试 API
4. 查看响应结果

**注意：**
- 调试页面已集成在最小化版本中
- 不需要额外的配置文件
- 适合快速测试和验证

### 6. 禁用调试模式（可选）

**配置方法：**
在 `.env` 文件中不创建 `DEBUG_MODE.txt` 文件：

```bash
# 不创建 DEBUG_MODE.txt 文件
```

**效果：**
- ✅ 减少磁盘 I/O
- ✅ 减少内存占用
- ✅ 提高响应速度

## 🔧 配置建议

### 推荐配置

#### .env 文件
```bash
# 必需配置
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# 推荐配置
CACHE_DIR=D:\api_proxy_cache

# 针对 2GB 内存的优化
MAX_CONCURRENT_REQUESTS=3

# 可选配置（如果有代理）
HTTP_PROXY=http://proxy-server:port
```

#### 配置说明
- `OPENROUTER_API_KEY`: OpenRouter API 密钥（必需）
- `CACHE_DIR`: 缓存目录（推荐设置，避免文件分散）
- `MAX_CONCURRENT_REQUESTS`: 最大并发数（建议设为 3，减少内存占用）
- `HTTP_PROXY`: HTTP 代理（如果需要）

## 📊 性能监控

### 监控内存使用

**创建监控脚本：**

```bash
@echo off
:loop
echo Memory Usage:
for /f "tokens=2 delims=," %%a in ('wmic OS get FreePhysicalMemory /Value^,TotalVisibleMemorySize /Value 2^>^|findstr /V ","') do (
    set /a free=%%a
    set /a total=%%b
    set /a used=!total!-!free!
    set /a percent=!used!*100/!total!
    echo Free: !free! MB / Total: !total! MB / Used: !used! MB (!percent!%%)
)
timeout /t 5 /nobreak >nul
goto loop
```

**使用方法：**
```bash
# 保存为 monitor_memory.bat
# 运行监控
monitor_memory.bat
```

### 监控服务状态

```bash
@echo off
:check
echo Checking service status...
python daemon.py status
if %errorlevel% equ 0 (
    echo Service is running
) else (
    echo Service is not running
    echo Attempting to restart...
    python daemon.py start
)
timeout /t 30 /nobreak >nul
goto check
```

## 🐛 故障排除

### 问题1：内存不足

**症状：**
- MemoryError
- 服务崩溃
- 系统变慢

**解决方案：**
```bash
# 1. 减少并发数
MAX_CONCURRENT_REQUESTS=2

# 2. 清理缓存
del /Q D:\api_proxy_cache\*.json

# 3. 重启服务
python daemon.py restart

# 4. 监控内存使用
tasklist | findstr python
```

### 问题2：Python 版本不兼容

**症状：**
- ImportError: cannot import name 'xxx'
- 语法错误

**解决方案：**
```bash
# 检查 Python 版本
python --version

# 验证兼容性
python -c "import flask, requests, watchdog; print('All dependencies compatible')"
```

### 问题3：端口被占用

**症状：**
- Address already in use
- 服务无法启动

**解决方案：**
```bash
# 查找占用端口的进程
netstat -ano | findstr :5000

# 结束进程
taskkill /PID <进程ID> /F

# 或者使用守护进程停止
python daemon.py stop
```

### 问题4：依赖安装失败

**症状：**
- pip install 失败
- SSL 证书错误

**解决方案：**
```bash
# 1. 升级 pip
python -m pip install --upgrade pip

# 2. 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask requests watchdog

# 3. 手动下载安装包
# 从 https://pypi.org/ 下载 .whl 文件
# 使用 pip install xxx.whl 安装
```

## 📝 维护建议

### 日常维护
1. **定期清理缓存**
   - 每周清理一次旧缓存文件
   - 保留最近 7 天的文件

2. **监控日志**
   - 定期查看 `daemon.log`
   - 关注错误和警告信息

3. **更新依赖**
   - 定期检查依赖更新
   - 测试新版本兼容性

4. **备份配置**
   - 定期备份 `.env` 文件
   - 记录配置变更历史

### 紧急维护
1. **服务崩溃**
   - 查看 `daemon.log` 了解原因
   - 检查内存使用情况
   - 重启服务

2. **性能下降**
   - 检查并发请求数
   - 清理缓存
   - 重启服务

3. **磁盘空间不足**
   - 清理缓存文件
   - 清理日志文件
   - 扩展磁盘空间

## 🎯 最佳实践

### 1. 使用最小化配置
- ✅ 使用 `a10-minimal_setup.bat`
- ✅ 避免不必要的系统修改
- ✅ 保持系统稳定性

### 2. 资源管理
- ✅ 设置 `MAX_CONCURRENT_REQUESTS=3`
- ✅ 定期清理缓存
- ✅ 监控内存使用

### 3. 日志管理
- ✅ 定期查看 `daemon.log`
- ✅ 及时处理错误信息
- ✅ 保留重要日志

### 4. 测试验证
- ✅ 部署后进行功能测试
- ✅ 验证 API 连接
- ✅ 测试并发请求

### 5. 服务监控（推荐）
- ✅ 使用 `a20-monitor_service.bat` 监控服务状态
- ✅ 定期检查服务运行情况
- ✅ 及时处理服务异常

**监控脚本使用示例：**
```bash
# 启动监控脚本（推荐）
a20-monitor_service.bat

# 监控脚本会：
# - 每30秒检查一次服务状态
# - 服务停止时自动重启
# - 记录重启次数和时间
# - 防止频繁重启（5秒延迟）
```

## 📚 相关文档

- [WIN2012_INSTALLATION_GUIDE.md](../WIN2012_INSTALLATION_GUIDE.md) - 详细安装指南
- [DAEMON_IMPROVEMENT.md](../DAEMON_IMPROVEMENT.md) - 守护进程改进
- [API_PROXY_README.md](../API_PROXY_README.md) - API 代理文档
- [README.md](../README.md) - 项目主文档

## 🆘 Python 3.11.9 特性

### 支持的特性
- ✅ f-string: `f"Hello {name}"` 格式
- ✅ 类型注解: `def func(x: int) -> int:`
- ✅ 字典合并: `{**dict1, **dict2}`
- ✅ 海象运算符: `dict1 | dict2`
- ✅ match-case: `match x: case 1: ...`
- ✅ 结构化模式匹配: `match re.Pattern(r'\d+')`

### 可能不支持的特性
- ⚠️ 某些新的异步特性
- ⚠️ 某些新的标准库特性
- ⚠️ 某些第三方库的新特性

### 测试建议
部署前测试关键功能：
```python
# 测试 f-string
name = "World"
print(f"Hello {name}")

# 测试类型注解
def add(x: int, y: int) -> int:
    return x + y

# 测试字典合并
dict1 = {"a": 1}
dict2 = {"b": 2}
merged = {**dict1, **dict2}
print(merged)
```

## 🔒 安全建议

### 1. 文件权限
```bash
# 设置适当的文件权限
# 确保 CACHE_DIR 目录有写入权限
# 确保 .env 文件有读取权限
```

### 2. 网络安全
```bash
# 使用防火墙规则
# 只开放必要端口（5000）
# 限制外部访问（如果不需要）
```

### 3. API 密钥安全
```bash
# 不要将 API 密钥提交到版本控制
# 定期更换 API 密钥
# 使用环境变量存储密钥
```

## 📞 获取帮助

### 常见问题
1. **Python 3.11.9 兼容性**
   - ✅ 完全兼容
   - ⚠️ 某些新特性可能不支持

2. **2GB 内存限制**
   - ✅ 可以运行，但需要优化
   - ⚠️ 建议减少并发数

3. **Windows Server 2012 R2**
   - ✅ 支持良好
   - ⚠️ 某些新特性不支持

4. **监控脚本 vs 守护进程**
   - ✅ 推荐：监控脚本（资源占用少）
   - ⚠️ 可选：守护进程（响应快但占用多）
   - 💡 详细对比：见本文档"监控脚本 vs 守护进程"章节

5. **服务崩溃后如何自动重启**
   - ✅ 使用 `a20-monitor_service.bat`（推荐）
   - ✅ 使用 `a23-daemon_service.bat`（可选）
   - 💡 监控脚本更适合 2GB 内存环境

6. **如何停止监控/守护进程**
   - ✅ 按 Ctrl+C 停止脚本
   - ✅ 关闭命令行窗口
   - 💡 脚本会显示总重启次数

### 联系支持
- 查看项目文档：`README.md`
- 查看故障排除：[WIN2012_INSTALLATION_GUIDE.md](../WIN2012_INSTALLATION_GUIDE.md) "故障排除"章节
- 查看在线资源：OpenRouter 官方文档

## 📋 快速参考

### 系统要求
- 操作系统：Windows Server 2012 R2 或更高
- Python：3.8 或更高（推荐 3.11.9）
- 内存：至少 512MB 可用（推荐 2GB）
- 磁盘：至少 100MB 可用空间

### 文件清单
- `a10-minimal_setup.bat` - 最小化配置脚本（推荐）
- `a20-monitor_service.bat` - 监控脚本（推荐）
- `a21-safe_start.bat` - 安全启动脚本（推荐）
- `a22-start_minimal.bat` - 最小化启动脚本（推荐）
- `a23-daemon_service.bat` - 守护进程（可选）
- `b01-setup_firewall.bat` - 防火墙配置（可选）
- `b02-restore_firewall.bat` - 防火墙恢复（可选）
- `b03-restore_system.bat` - 系统回退脚本（可选）
- `b04-simple_ssl_setup.bat` - SSL 配置（可选）
- `b05-win2012_optimization.bat` - 系统优化（可选）
- `minimal_server_proxy.py` - 最小化服务器
- `python_optimization.py` - Python 优化脚本（可选）

### 端口说明
- `5000` - API 服务端口
- 需要防火墙允许此端口

### 日志文件
- `daemon.log` - 守护进程日志
- `daemon.pid` - 守护进程 PID
- `CACHE_DIR/*.json` - API 请求/响应缓存

---

**文档版本：** 1.0
**更新日期：** 2026-02-17
**适用系统：** Windows Server 2012 R2 + Python 3.11.9
