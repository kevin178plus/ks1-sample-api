# 操作日志

## 历史记录说明
历史操作记录已按日期拆分到 logs/operateLog-by-ymd 目录下的对应文件中：
- logs/operateLog-by-ymd/2026-02-14.md：2026年2月14日操作记录
- logs/operateLog-by-ymd/2026-02-15.md：2026年2月15日操作记录
- logs/operateLog-by-ymd/2026-02-17.md：2026年2月17日操作记录
- logs/operateLog-by-ymd/2026-02-18.md：2026年2月18日操作记录

---

## 2026-02-23 - Free API 默认参数配置统一管理
**更新时间：** 2026-02-23 19:29:43

### 需求背景
用户要求将各个 free 的 max_tokens 和 multi_free_api_proxy_v3.py 的默认参数统一放到各自的 config.py 中管理。

### 实施的改进

#### 1. 为各个 free 的 config.py 添加 MAX_TOKENS 配置
**修改文件：**
- [free_api_test/free1/config.py](free_api_test/free1/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free2/config.py](free_api_test/free2/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free3/config.py](free_api_test/free3/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free4/config.py](free_api_test/free4/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free5/config.py](free_api_test/free5/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free6/config.py](free_api_test/free6/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free7/config.py](free_api_test/free7/config.py) - 添加 `MAX_TOKENS = 2000`
- [free_api_test/free8/config.py](free_api_test/free8/config.py) - 添加 `MAX_TOKENS = 2000`

#### 2. 创建 multi_free_api_proxy/config.py
**新增文件：** [multi_free_api_proxy/config.py](multi_free_api_proxy/config.py)

**包含的配置项：**
- `DEFAULT_MAX_TOKENS = 2000` - 最大生成token数
- `DEFAULT_TEMPERATURE = 0.7` - 生成随机性
- `DEFAULT_TOP_P = 1.0` - 核采样概率
- `TIMEOUT_BASE = 45` - 基础超时时间（秒）
- `TIMEOUT_RETRY = 60` - 重试超时时间（秒）
- `MAX_RETRIES = 3` - 最大重试次数
- `MAX_CONCURRENT_REQUESTS = 5` - 最大并发请求数

#### 3. 修改 multi_free_api_proxy_v3.py
**修改内容：**
- 导入 config 模块（使用直接读取文件方式，避免模块名冲突）
- 从各 free 的 config.py 读取 MAX_TOKENS 配置
- 使用 config.py 中的默认值（temperature, max_tokens, top_p 等）
- 调试页面也使用统一的默认值配置

#### 4. 创建 __init__.py
**新增文件：** [multi_free_api_proxy/__init__.py](multi_free_api_proxy/__init__.py)

### 技术实现细节

1. **导入方式改进**
   由于 multi_free_api_proxy 目录中存在 multi_free_api_proxy.py 文件，直接导入会冲突，改用直接读取文件方式：
   ```python
   config_file = script_dir / "config.py"
   spec = importlib.util.spec_from_file_location("proxy_config", str(config_file))
   proxy_config = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(proxy_config)
   ```

2. **默认值优先级**
   - 客户端请求参数 > 各 free 的 MAX_TOKENS > DEFAULT_MAX_TOKENS

### 优势总结

1. **统一管理** - 所有默认参数集中在一个文件中
2. **灵活配置** - 各 free 可以有自己的 MAX_TOKENS 配置
3. **易于维护** - 修改配置只需修改 config.py
4. **向后兼容** - 未配置时使用默认值

### 文件变更清单

**新增文件：**
- [multi_free_api_proxy/config.py](multi_free_api_proxy/config.py) - 默认参数配置
- [multi_free_api_proxy/__init__.py](multi_free_api_proxy/__init__.py) - 包初始化文件

**修改的文件：**
- [free_api_test/free1/config.py](free_api_test/free1/config.py) - 添加 MAX_TOKENS
- [free_api_test/free2/config.py](free_api_test/free2/config.py) - 添加 MAX_TOKENS
- [free_api_test/free3/config.py](free_api_test/free3/config.py) - 添加 MAX_TOKENS
- [free_api_test/free4/config.py](free_api_test/free4/config.py) - 添加 MAX_TOKENS
- [free_api_test/free5/config.py](free_api_test/free5/config.py) - 添加 MAX_TOKENS
- [free_api_test/free6/config.py](free_api_test/free6/config.py) - 添加 MAX_TOKENS
- [free_api_test/free7/config.py](free_api_test/free7/config.py) - 添加 MAX_TOKENS
- [free_api_test/free8/config.py](free_api_test/free8/config.py) - 添加 MAX_TOKENS
- [multi_free_api_proxy/multi_free_api_proxy_v3.py](multi_free_api_proxy/multi_free_api_proxy_v3.py) - 使用 config.py 的默认值

**更新完成时间：** 2026-02-23 19:29:43

---

## 2026-02-28 - 修复 Python 3.13 兼容性问题
**更新时间：** 2026-02-28

### 问题描述
启动 `multi_free_api_proxy_v3.py` 时出现以下错误：
```
TypeError: 'handle' must be a _ThreadHandle
```

### 根本原因
Python 3.13 修改了 threading 模块的 API，导致旧版本的 watchdog 库 (4.0.0) 不兼容，无法启动文件监控线程。

### 解决方案
升级 watchdog 到 6.0.0 版本（支持 Python 3.13）：
```bash
pip install --upgrade watchdog
```

**变更记录：**
- watchdog 从 4.0.0 升级到 6.0.0
- 程序成功启动，服务运行在 http://127.0.0.1:5000

### 验证结果
程序已成功启动并正常运行。

---

*最后更新：2026-02-28*
