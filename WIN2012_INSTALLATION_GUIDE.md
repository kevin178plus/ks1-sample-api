# Windows Server 2012 R2 安装部署手册

## 📋 系统信息

- **操作系统**: Windows Server 2012 R2 Datacenter
- **Python 版本**: 3.11.9
- **内存**: 2GB
- **架构**: 64位

## ⚠️ 重要注意事项

### 系统限制
- **内存限制**: 2GB 内存较小，需要优化配置
- **Python 版本**: 3.11.9 是较新版本，兼容性良好
- **操作系统**: Windows Server 2012 R2 是较老系统，某些新特性可能不支持

### 部署建议
- ✅ **推荐**: 使用 `scenarios/win2012-server/` 下的优化版本
- ✅ **轻量级**: 避免运行过多并发请求
- ✅ **监控**: 密切监控内存使用情况
- ❌ **不推荐**: 使用生产环境配置（需要更多资源）

## 🚀 快速开始

### 方式1：使用优化版批处理（推荐）

```bash
# 进入优化场景目录
cd scenarios\win2012-server

# 运行优化版启动脚本
minimal_setup.bat
```

### 方式2：手动安装依赖

```bash
# 1. 升级 pip（如果需要）
python -m pip install --upgrade pip

# 2. 安装依赖
pip install flask requests watchdog

# 3. 验证安装
python -c "import flask, requests, watchdog; print('All dependencies installed')"
```

## 📦 详细安装步骤

### 步骤1：系统准备

#### 1.1 检查 Python 版本
```bash
python --version
```

**预期输出：**
```
Python 3.11.9
```

**如果版本不符：**
- 低于 3.8：需要升级 Python
- 高于 3.12：可能存在兼容性问题（建议降级）

#### 1.2 检查系统资源
```bash
# 查看可用内存
systeminfo | findstr /C "Available Physical Memory"

# 查看磁盘空间
wmic logicaldisk get size,freespace,caption
```

**最低要求：**
- 可用内存：至少 512MB
- 磁盘空间：至少 100MB

#### 1.3 检查网络连接
```bash
# 测试网络连接
ping openrouter.ai -n 4

# 测试端口访问
curl -I https://openrouter.ai
```

### 步骤2：部署文件

#### 2.1 复制项目文件
```bash
# 方式1：压缩后上传
# 在本地压缩项目文件夹，然后上传到服务器

# 方式2：直接复制
# 使用远程桌面或文件共享直接复制文件
```

**推荐目录结构：**
```
D:\ks1-simple-api\
├── local_api_proxy.py
├── daemon.py
├── .env
├── requirements.txt
├── scenarios\
│   └── win2012-server\
│       ├── minimal_setup.bat
│       └── README.md
└── ...
```

#### 2.2 配置环境变量
创建 `.env` 文件：

```bash
# 必需配置
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# 可选配置（推荐）
CACHE_DIR=D:\api_proxy_cache

# 可选配置（如果有代理）
HTTP_PROXY=http://proxy-server:port

# 可选配置（优化性能）
MAX_CONCURRENT_REQUESTS=3
```

**配置说明：**
- `OPENROUTER_API_KEY`: OpenRouter API 密钥（必需）
- `CACHE_DIR`: 缓存目录（推荐设置，避免文件分散）
- `HTTP_PROXY`: HTTP 代理（如果需要）
- `MAX_CONCURRENT_REQUESTS`: 最大并发数（建议设为 3，减少内存占用）

### 步骤3：安装依赖

#### 3.1 创建虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖到虚拟环境
pip install -r requirements.txt
```

**为什么使用虚拟环境：**
- ✅ 隔离项目依赖
- ✅ 避免系统 Python 环境污染
- ✅ 便于卸载和重装

#### 3.2 直接安装到系统 Python
```bash
# 安装依赖
pip install flask requests watchdog
```

**注意事项：**
- 需要管理员权限
- 可能影响其他 Python 项目

### 步骤4：配置优化

#### 4.1 针对 2GB 内存的优化
编辑 `.env` 文件：

```bash
# 减少并发请求数（默认为 5，建议降低到 3）
MAX_CONCURRENT_REQUESTS=3

# 减少缓存保留时间（如果使用缓存功能）
# 在 local_api_proxy.py 中调整缓存策略
```

#### 4.2 禁用不必要的功能
```bash
# 在 .env 中禁用调试模式（生产环境）
# 不创建 DEBUG_MODE.txt 文件
```

**禁用调试模式的好处：**
- 减少磁盘 I/O
- 减少内存占用
- 提高响应速度

### 步骤5：启动服务

#### 5.1 使用优化版启动脚本
```bash
# 进入优化场景目录
cd scenarios\win2012-server

# 运行优化版启动脚本
minimal_setup.bat
```

**脚本功能：**
- ✅ 自动检查 Python 版本
- ✅ 自动安装依赖
- ✅ 最小化系统影响
- ✅ 零配置修改（只配置必需项）
- ✅ 安全启动（不修改系统设置）

#### 5.2 使用守护进程模式
```bash
# 启动守护进程（推荐）
python daemon.py start

# 查看状态
python daemon.py status

# 停止服务
python daemon.py stop
```

**守护进程优势：**
- ✅ 自动重启：崩溃时自动恢复
- ✅ 后台运行：不占用终端
- ✅ 日志记录：便于问题排查

## 🔧 配置优化

### 针对 2GB 内存的优化建议

#### 1. 减少并发请求数
```bash
# .env 文件配置
MAX_CONCURRENT_REQUESTS=3
```

**原因：**
- 每个请求占用约 50-100MB 内存
- 3 个并发请求约占用 150-300MB
- 留出足够内存给 Python 和操作系统

#### 2. 限制缓存大小
```bash
# 在 local_api_proxy.py 中添加缓存大小限制
# 或者定期清理缓存文件
```

**清理缓存脚本：**
```bash
# 创建清理脚本 cleanup_cache.bat
@echo off
set CACHE_DIR=D:\api_proxy_cache
echo Cleaning up cache files older than 7 days...
forfiles /P %CACHE_DIR% /M -7 -C "cmd /c echo @path" 2>nul
echo Cleanup completed.
pause
```

#### 3. 优化 Python 配置
创建 `python_optimization.py`：

```python
import sys
import gc

# 减少 Python 内存占用
sys.setrecursionlimit(1000)  # 降低递归限制
gc.set_threshold(700, 10, 10)  # 调整垃圾回收

print("Python optimization applied")
```

在启动前运行：
```bash
python python_optimization.py && python local_api_proxy.py
```

#### 4. 使用轻量级模式
```bash
# 在 .env 中设置测试模式
TEST_MODE=true
```

**测试模式优势：**
- ✅ 不调用真实 API
- ✅ 快速响应
- ✅ 零网络开销

## 🐛 故障排除

### 问题1：Python 版本不兼容

**症状：**
- ImportError: cannot import name 'xxx'
- 语法错误

**解决方案：**
```bash
# 检查 Python 版本
python --version

# 如果版本过低，升级 Python
# 下载 Python 3.11.9 安装包
# https://www.python.org/downloads/

# 如果版本过高，降级到 3.11.x
```

### 问题2：内存不足

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

### 问题5：服务无法启动

**症状：**
- 守护进程启动失败
- 服务立即退出

**解决方案：**
```bash
# 1. 查看日志
type D:\api_proxy_cache\daemon.log

# 2. 检查配置
type .env

# 3. 验证 Python 脚本
python -m py_compile local_api_proxy.py

# 4. 手动启动测试
python local_api_proxy.py
```

## 📊 性能监控

### 监控内存使用
```bash
# 创建监控脚本 monitor_memory.bat
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

### 监控服务状态
```bash
# 创建监控脚本 monitor_service.bat
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

### 1. 使用优化版本
- ✅ 使用 `scenarios/win2012-server/minimal_setup.bat`
- ✅ 避免手动配置
- ✅ 减少系统影响

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

### 联系支持
- 查看项目文档：`scenarios/win2012-server/README.md`
- 查看故障排除：本手册"故障排除"章节
- 查看在线资源：OpenRouter 官方文档

## 📚 附录

### A. 系统要求
- 操作系统：Windows Server 2012 R2 或更高
- Python：3.8 或更高（推荐 3.11.x）
- 内存：至少 512MB 可用（推荐 2GB）
- 磁盘：至少 100MB 可用空间
- 网络：稳定的互联网连接

### B. 文件清单
- `local_api_proxy.py` - 主程序
- `daemon.py` - 守护进程
- `.env` - 配置文件
- `requirements.txt` - 依赖列表
- `scenarios/win2012-server/` - 优化脚本

### C. 端口说明
- `5000` - API 服务端口
- 需要防火墙允许此端口

### D. 日志文件
- `daemon.log` - 守护进程日志
- `daemon.pid` - 守护进程 PID
- `CACHE_DIR/*.json` - API 请求/响应缓存

---

**文档版本：** 1.0
**更新日期：** 2026-02-17
**适用系统：** Windows Server 2012 R2 + Python 3.11.9
