# 守护进程改进说明

## 改进时间
2026-02-17

## 改进内容

### daemon.log 和 daemon.pid 支持 CACHE_DIR

#### 改进前
```python
LOG_FILE = os.path.join(SCRIPT_DIR, "daemon.log")
PID_FILE = os.path.join(SCRIPT_DIR, "daemon.pid")
```

**问题：**
- 守护进程日志和PID文件固定放在项目根目录
- 与API代理的缓存文件不在同一目录
- 文件分散，不便于管理

#### 改进后
```python
# 读取 CACHE_DIR 环境变量，如果未设置则使用 SCRIPT_DIR
CACHE_DIR = os.getenv("CACHE_DIR", SCRIPT_DIR)
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")
PID_FILE = os.path.join(CACHE_DIR, "daemon.pid")
```

**优势：**
- ✅ 支持通过 CACHE_DIR 环境变量自定义位置
- ✅ 默认情况下与API代理缓存文件在同一目录
- ✅ 集中管理所有相关文件
- ✅ 不会污染项目根目录

## 使用方式

### 方式1：使用默认配置
**.env 文件：**
```bash
# 不设置 CACHE_DIR
```

**文件位置：**
```
项目根目录/
├── daemon.log
├── daemon.pid
├── local_api_proxy.py
└── ...
```

### 方式2：使用自定义缓存目录
**.env 文件：**
```bash
CACHE_DIR=r:\api_proxy_cache
```

**文件位置：**
```
r:\api_proxy_cache/
├── daemon.log
├── daemon.pid
├── 20260217_143709_853_REQUEST_*.json
├── 20260217_143718_998_ERROR_*.json
├── 20260217_143809_475_REQUEST_*.json
└── CALLS_20260217.json
```

## 文件说明

### daemon.log
**用途：** 守护进程运行日志

**内容示例：**
```
[2026-02-17 18:00:00] Daemon starting
[2026-02-17 18:00:00] Working directory: D:\ks_ws\git-root\ks1-simple-api
[2026-02-17 18:00:00] Main script: D:\ks_ws\git-root\ks1-simple-api\local_api_proxy.py
[2026-02-17 18:00:00] Cache directory: r:\api_proxy_cache
[2026-02-17 18:00:00] Log file: r:\api_proxy_cache\daemon.log
[2026-02-17 18:00:00] PID file: r:\api_proxy_cache\daemon.pid
[2026-02-17 18:00:00] Main program started (PID: 12345)
```

### daemon.pid
**用途：** 存储守护进程的进程ID，用于单例保护

**内容示例：**
```
12345
```

## 代码修改详情

### 修改的文件
**daemon.py**

#### 修改1：添加 CACHE_DIR 支持
**位置：** 第12-14行

**修改前：**
```python
LOG_FILE = os.path.join(SCRIPT_DIR, "daemon.log")
PID_FILE = os.path.join(SCRIPT_DIR, "daemon.pid")
```

**修改后：**
```python
# 读取 CACHE_DIR 环境变量，如果未设置则使用 SCRIPT_DIR
CACHE_DIR = os.getenv("CACHE_DIR", SCRIPT_DIR)
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")
PID_FILE = os.path.join(CACHE_DIR, "daemon.pid")
```

#### 修改2：自动创建 CACHE_DIR 目录
**位置：** 第154-159行

**新增代码：**
```python
# 确保 CACHE_DIR 目录存在
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.log(f"Created cache directory: {CACHE_DIR}")
    except Exception as e:
        self.log(f"Failed to create cache directory: {e}")
        sys.exit(1)
```

#### 修改3：增强日志输出
**位置：** 第182-186行

**修改前：**
```python
self.log(f"Working directory: {SCRIPT_DIR}")
self.log(f"Main script: {MAIN_SCRIPT}")
self.log(f"Log file: {LOG_FILE}")
```

**修改后：**
```python
self.log(f"Working directory: {SCRIPT_DIR}")
self.log(f"Main script: {MAIN_SCRIPT}")
self.log(f"Cache directory: {CACHE_DIR}")
self.log(f"Log file: {LOG_FILE}")
self.log(f"PID file: {PID_FILE}")
```

## 优势总结

### 1. 集中管理
- ✅ 所有缓存相关文件在同一目录
- ✅ 便于备份和清理
- ✅ 便于监控和维护

### 2. 灵活配置
- ✅ 支持通过环境变量自定义位置
- ✅ 默认情况下使用项目根目录
- ✅ 兼容现有配置

### 3. 自动化
- ✅ 自动创建 CACHE_DIR 目录
- ✅ 启动时检查目录存在性
- ✅ 失败时提供详细错误信息

### 4. 日志增强
- ✅ 显示所有关键路径信息
- ✅ 便于问题排查
- ✅ 提高可维护性

## 配置示例

### 示例1：使用默认配置
**.env 文件：**
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
# 不设置 CACHE_DIR
```

**结果：**
- daemon.log → 项目根目录
- daemon.pid → 项目根目录
- API缓存 → 项目根目录（如果启用调试模式）

### 示例2：使用自定义缓存目录
**.env 文件：**
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
CACHE_DIR=r:\api_proxy_cache
```

**结果：**
- daemon.log → r:\api_proxy_cache\daemon.log
- daemon.pid → r:\api_proxy_cache\daemon.pid
- API缓存 → r:\api_proxy_cache\（如果启用调试模式）

### 示例3：使用网络路径
**.env 文件：**
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
CACHE_DIR=\\server\share\api_cache
```

**结果：**
- daemon.log → \\server\share\api_cache\daemon.log
- daemon.pid → \\server\share\api_cache\daemon.pid
- API缓存 → \\server\share\api_cache\（如果启用调试模式）

## 注意事项

### 1. 权限要求
- CACHE_DIR 目录需要有写入权限
- 守护进程需要创建目录的权限
- 确保目录路径正确

### 2. 路径格式
- Windows：使用反斜杠或正斜杠
- Linux/Mac：使用正斜杠
- 支持绝对路径和相对路径

### 3. 环境变量优先级
- CACHE_DIR 环境变量优先
- 未设置时使用项目根目录
- 与 local_api_proxy.py 的行为一致

### 4. 清理建议
- 定期清理 daemon.log 避免文件过大
- 定期清理旧的缓存文件
- 停止守护进程后可以安全删除 daemon.pid

## 验证方法

### 检查文件位置
```bash
# 查看守护进程日志
type r:\api_proxy_cache\daemon.log

# 查看 PID 文件
type r:\api_proxy_cache\daemon.pid
```

### 验证目录创建
启动守护进程后，检查日志输出：
```
[2026-02-17 18:00:00] Created cache directory: r:\api_proxy_cache
```

### 验证单例保护
尝试重复启动守护进程：
```bash
python daemon.py start
python daemon.py start
```

第二次启动应该显示：
```
Daemon already running (PID: xxx)
```

## 向后兼容性

### 兼容性说明
- ✅ 完全向后兼容现有配置
- ✅ 未设置 CACHE_DIR 时行为不变
- ✅ 不影响现有功能

### 迁移建议
- 建议设置 CACHE_DIR 集中管理文件
- 可以手动移动现有文件到新位置
- 删除旧的 daemon.log 和 daemon.pid

## 总结

### 改进效果
- ✅ daemon.log 和 daemon.pid 支持 CACHE_DIR
- ✅ 自动创建 CACHE_DIR 目录
- ✅ 增强日志输出，显示所有路径
- ✅ 完全向后兼容

### 使用建议
- 生产环境：设置 CACHE_DIR 集中管理
- 开发环境：可以使用默认配置
- 定期清理：避免日志和缓存文件过大

---

**改进完成时间：** 2026-02-17
**改进版本：** v2.2
