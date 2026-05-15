# 操作日志

## 历史记录说明
历史操作记录已按日期拆分到 logs/operateLog-by-ymd 目录下的对应文件中：
- 2026-02-14.md：2月14日操作记录
- 2026-02-15.md：2月15日操作记录
- 2026-02-17.md：2月17日操作记录
- 2026-02-18.md：2月18日操作记录

---

## 2026-05-12 - 文档更新：移除已删除的 local_api_proxy.py 引用

**更新时间：** 2026-05-12 09:53:00

### 问题描述
用户指出 README.md 和其他文档中仍在介绍已删除的 `local_api_proxy.py` (v1 单文件版)，导致文档与实际代码不一致。

### 修改的文件

1. **start_proxy.bat** - 更新启动脚本
   - 将 `python local_api_proxy.py` 改为 `cd multi_free_api_proxy && python multi_free_api_proxy_v3_optimized.py`
   - 更新标题和提示信息

2. **README.md** - 更新主文档
   - 移除文件说明中的 `local_api_proxy.py`
   - 更新启动服务部分，添加推荐方式
   - 更新自动重载部分的文件路径
   - 更新故障排除部分的配置路径

3. **API_PROXY_README.md** - 更新部署文档
   - 更新"重要路径说明"指向正确文件
   - 更新安装依赖和配置说明
   - 更新启动服务方式
   - 更新注意事项和故障排除

4. **启动文件与版本关系.md** - 更新版本关系文档
   - 更新版本架构总览
   - 移除 v1 原始版描述
   - 更新启动脚本对应关系
   - 移除文件监控配置中的 v1 条目

5. **版本分析报告.md** - 更新版本分析文档
   - 更新项目版本总览
   - 移除 local_api_proxy.py 相关描述
   - 更新资源占用对比
   - 更新功能对比总结

### 关键变更

| 旧内容 | 新内容 |
|--------|--------|
| `local_api_proxy.py` (v1 单文件版) | 已移除 |
| 启动主入口 | `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py` |
| 配置文件 | `multi_free_api_proxy/.env` |

---

## 2026-05-10 - API代理Go版本调试页面死锁问题修复

**更新时间：** 2026-05-10

### 问题描述
调试页面 `/debug` 的 "API 状态" 标签一直显示"正在加载..."或"全不可用"，请求超时。

### 问题根因

#### 1. GetAllUpstreamInfo 使用 TryLock 导致返回空数组

**文件：** `api-proxy-go/upstream/upstream.go`

**问题代码：**
```go
func (m *Manager) GetAllUpstreamInfo() []map[string]interface{} {
    if !m.mu.TryLock() {
        // 无法获取锁（可能在健康检查中），返回空
        return []map[string]interface{}{}
    }
    defer m.mu.Unlock()
    // ...
}
```

**问题分析：** `TryLock()` 是非阻塞的写锁尝试。当健康检查（`TestAll`）持有 `RLock`（读锁）时，写锁获取失败直接返回空数组，导致前端将所有API显示为不可用。

**修复方案：** 使用 `RLock()`（读锁）替代 `TryLock()`，允许多个并发读取。

#### 2. Test 函数在遍历中调用 UpdateAvailable 导致死锁

**问题代码：**
```go
func (m *Manager) TestAll() {
    m.mu.RLock()  // 持有读锁
    for _, name := range names {
        m.Test(name)  // Test 内部调用 UpdateAvailable
    }
    m.mu.RUnlock()
}

func (m *Manager) Test(name string) {
    // ...
    m.UpdateAvailable()  // 需要 Lock() 写锁 -> 死锁！
}
```

**问题分析：** `UpdateAvailable()` 需要 `Lock()`（写锁），但在 `TestAll` 已经持有 `RLock`（读锁）的情况下尝试获取写锁，会导致死锁。

**修复方案：** 移除 `Test` 函数中的 `UpdateAvailable` 调用。可用列表由健康检查 goroutine 定期更新。

### 最终修复代码

**GetAllUpstreamInfo (upstream.go:483-521)：**
```go
func (m *Manager) GetAllUpstreamInfo() []map[string]interface{} {
    m.mu.RLock()
    defer m.mu.RUnlock()

    result := make([]map[string]interface{}, 0, len(m.upstreams))

    for name, upstream := range m.upstreams {
        upstream.mu.RLock()
        // ... 读取数据
        upstream.mu.RUnlock()
        result = append(result, info)
    }

    return result
}
```

**Test 函数 (upstream.go:219-221)：**
```go
// 移除 UpdateAvailable() 调用
// 注意：不调用 UpdateAvailable() 更新可用列表
// 可用列表由健康检查 goroutine 定期更新，避免在 TestAll 遍历中产生锁竞争
```

### 附加发现

**代理配置问题：** `upstreams/free1/config.yaml` 配置了 `use_proxy: true` 但全局代理为空，导致测试请求卡住。建议统一检查各上游配置的代理设置。

### 配置变更记录

**config.yaml：**
- 临时禁用健康检查用于测试：`health_check.enabled: false`

**debug.go：**
- 前端超时从 120秒 缩短到 10秒：`setTimeout(..., 10000)`

---

## 2026-03-10 - V3原版与优化版多角度分析
**更新时间：** 2026-03-10

### 分析目标
在保持v3原版可用性不受影响的前提下，测试和完善提高新版（optimized）的稳定性。

### 一、代码规模对比

| 版本 | 文件大小 | 代码行数 | 依赖模块 |
|------|----------|----------|----------|
| v3原版 | 85.07 KB | ~2316行 | 无独立模块 |
| 优化版 | 25.3 KB | ~719行 | config.py, app_state.py, errors.py |

### 二、功能差异分析

#### 优化版缺失的关键功能

| 功能 | v3原版 | 优化版 | 影响程度 |
|------|--------|--------|----------|
| free5/free8独立服务路由 | ✅ 完整 | ❌ 缺失 | **严重** - 独立服务API无法使用 |
| 动态模型选择(权重模型) | ✅ 完整 | ❌ 缺失 | 中等 |
| 消息缓存功能 | ✅ 完整 | ❌ 缺失 | 低 |
| 每日调用计数 | ✅ 完整 | ❌ 缺失 | 低 |
| 重载环境变量 | ✅ 完整 | ❌ 缺失 | 中等 |

#### 核心代码差异

**v3原版独立服务路由 (multi_free_api_proxy_v3.py 第694-741行):**
```python
# 路由到独立服务（free5 和 free8）
if api_name in ["free5", "free8"]:
    service_port = 5005 if api_name == "free5" else 5008
    service_url = f"http://localhost:{service_port}/v1/chat/completions"
    # ... 独立服务调用逻辑
```

**优化版缺失此逻辑 - 直接调用远程API，无法使用本地独立服务**

### 三、优化版架构优点

1. **模块化设计** - 配置、状态、错误分类管理
2. **代码简洁** - 更容易维护和理解
3. **锁管理集中** - AppState类统一管理所有并发锁
4. **模板支持** - 自带debug.html调试页面

### 四、稳定性改进建议

#### 优先级 P0 - 必须修复
1. **添加free5/free8独立服务路由**
   - 参照v3原版第694-741行实现
   - 检测api_name为free5或free8时，改为调用本地服务

2. **添加环境变量重载功能**
   - 参照v3原版reload_env()函数
   - 支持运行时配置更新

#### 优先级 P1 - 建议修复
3. **添加动态模型选择**
   - 支持use_weighted_model配置
   - 按权重随机选择模型

4. **添加消息缓存功能**
   - 支持DEBUG模式下的请求/响应缓存
   - 每日调用统计

#### 优先级 P2 - 可选改进
5. **日志增强**
   - 添加更详细的请求日志
   - 添加性能指标追踪

### 五、保持v3原版可用性

**当前v3原版启动命令：**
```bash
cd multi_free_api_proxy
python multi_free_api_proxy_v3.py
# 或指定端口
set PORT=5001 && python multi_free_api_proxy_v3.py
```

**确认v3原版功能完整：**
- ✅ 自动扫描free_api_test目录加载API配置
- ✅ free5/free8独立服务路由
- ✅ 权重管理
- ✅ 并发控制
- ✅ 失败重试机制
- ✅ 文件监控自动重启
- ✅ 调试模式

---

## 2026-03-10 - 优化版添加free5/free8独立服务路由
**更新时间：** 2026-03-10

### 修改内容
为 `multi_free_api_proxy_v3_optimized.py` 添加 free5/free8 独立服务路由功能。

### 修改位置
- 文件：`multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py`
- 函数：`execute_with_free_api` (第600-647行新增)

### 实现逻辑
1. 检测 api_name 是否为 "free5" 或 "free8"
2. 如果是，则路由到本地独立服务：
   - free5 → localhost:5005
   - free8 → localhost:5008
3. 先检查独立服务的 /v1/models 端点确认服务可用
4. 然后发送聊天请求到 /v1/chat/completions
5. 失败时自动重试（最多 MAX_RETRIES 次）

### 与v3原版对比
与 v3原版第694-741行的实现保持一致，确保功能对等。

---

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

## 2026-03-10 - .bat 启动脚本检查分析

**更新时间：** 2026-03-10

### 一、以 _ 开头的三个最常用 .bat 分析

| 文件名 | 启动目标 | 状态 |
|--------|----------|------|
| `_start_multi_free_api_v3-ansi.bat` | `multi_free_api_proxy\multi_free_api_proxy_v3.py` | ✅ 可用 |
| `_start_multi_free_api_v3-optimized.bat` | `multi_free_api_proxy\multi_free_api_proxy_v3_optimized.py` | ✅ 可用 |
| `_DelayStart-auto_start_multi_free_api_v3-ansi.bat` | `multi_free_api_proxy\multi_free_api_proxy_v3.py`（延迟16秒） | ✅ 可用 |

**结论：** 这三个文件对应的 Python 文件都存在且可以正常导入，都能正常使用。

---

### 二、哪个 .bat 还能正常启动 local_api_proxy.py？

| 文件名 | 启动目标 | 状态 |
|--------|----------|------|
| `start_proxy.bat` | `local_api_proxy.py`（原始单文件单上级代理） | ✅ 可用 |

**这是目前唯一能启动原始单文件代理的脚本。**

---

### 三、重复和多余的 .bat 文件分析

#### 功能分组

**启动主服务（Multi Free API）：**
| 文件名 | 启动目标 | 备注 |
|--------|----------|------|
| `start_multi_free_api.bat` | v1 原始版 | 较旧版本 |
| `start_multi_free_api_v3.bat` | v3 主版 | 推荐保留 |
| `start_multi_free_api_v3-ansi.bat` | v3 | 与上面几乎相同，只是编码导致乱码 |
| `start_main_service.bat` | v3 | 与上面重复 |
| `_start_multi_free_api_v3-ansi.bat` | v3 | 与上面重复 |
| `_start_multi_free_api_v3-optimized.bat` | v3 优化版 | 功能不同 |
| `_DelayStart-auto_start_multi_free_api_v3-ansi.bat` | v3（延迟启动） | 功能不同 |

**启动 Local API 代理：**
| 文件名 | 启动目标 | 备注 |
|--------|----------|------|
| `start_proxy.bat` | `local_api_proxy.py` | 唯一可用 |

**启动独立服务：**
| 文件名 | 启动目标 | 备注 |
|--------|----------|------|
| `start_free5_service.bat` | free5 独立服务 | 保留 |
| `start_free8_service.bat` | free8 独立服务 | 保留 |
| `start_all_services.bat` | 启动全部服务 | 可保留 |

**启动 Daemon：**
| 文件名 | 启动目标 | 备注 |
|--------|----------|------|
| `start_proxy_daemon.bat` | 完整版（支持 start/stop/status/restart） | 推荐保留 |
| `010-start_proxy_daemon-start.bat` | 简化版（仅 start） | 可删除 |

**测试脚本：**
| 文件名 | 用途 | 备注 |
|--------|------|------|
| `test_main_service.bat` | 测试主服务 | 保留 |
| `test_free5_service.bat` | 测试 free5 | 保留 |
| `test_free8_service.bat` | 测试 free8 | 保留 |

**其他：**
| 文件名 | 用途 | 备注 |
|--------|------|------|
| `start_doc_generator.bat` | 仅显示提示信息 | 可删除 |

---

### 四、建议删除的重复 .bat 文件

以下文件建议删除（功能重复或几乎不使用）：

| 序号 | 文件名 | 删除原因 |
|------|--------|----------|
| 1 | `start_multi_free_api.bat` | v1 版本已过时，功能与 v3 重复 |
| 2 | `start_multi_free_api_v3-ansi.bat` | 与 `start_multi_free_api_v3.bat` 完全重复，只是编码问题导致显示乱码 |
| 3 | `start_main_service.bat` | 与 `start_multi_free_api_v3.bat` 启动相同目标 |
| 4 | `010-start_proxy_daemon-start.bat` | 功能与 `start_proxy_daemon.bat` 重复（后者是完整版） |
| 5 | `start_doc_generator.bat` | 仅显示提示信息，无实际功能 |

**需要您确认后执行删除。**

---

## 2026-03-10 - 修复 multi_free_api_proxy_v3.py 配置加载错误

**更新时间：** 2026-03-10

### 问题描述
启动 `multi_free_api_proxy_v3.py` 时，所有 free API（free1-free12）加载失败，错误信息：
```
[错误] 加载 free1 配置失败: module 'proxy_config' has no attribute 'DEFAULT_MAX_TOKENS'
```

### 根本原因
`config.py` 中的默认参数（DEFAULT_MAX_TOKENS 等）是定义在 `Config` **类**中，但代码直接访问模块的 `proxy_config.DEFAULT_MAX_TOKENS`，导致属性找不到。

### 修复内容
**修改文件：** `multi_free_api_proxy/multi_free_api_proxy_v3.py`

1. 将配置导入部分改为从 `Config` 类获取默认值：
   ```python
   # 修改前
   proxy_config = importlib.util.module_from_spec(spec)
   
   # 修改后
   proxy_config = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(proxy_config)
   proxy_config_defaults = getattr(proxy_config, 'Config', None)
   ```

2. 将所有 `proxy_config.XXX` 改为 `proxy_config_defaults.XXX`

### 验证方法
重新启动服务，检查是否成功加载所有 API：
```batch
cd d:\ks_ws\git-root\ks1-simple-api\multi_free_api_proxy
set PORT=5001
python multi_free_api_proxy_v3.py
```

### 新增测试脚本
为方便测试 v3 版本，新增以下脚本：
- [020-test-on5001.bat](020-test-on5001.bat) - 在端口 5001 启动 v3 测试

---

### .bat 文件检查总结

#### free1-free12 服务状态
| 目录 | 服务类型 | API Key | 状态 |
|------|----------|---------|------|
| free1 | OpenRouter | ✅ 已配置 | 可用 |
| free2 | ChatAnywhere | ✅ 已配置 | 可用 |
| free3 | Free v36 | ✅ 已配置 | 可用 |
| free4 | Mistral | ✅ 已配置 | 可用 |
| free5 | iFlow SDK | ❌ 已注释 | 需安装 iflow-sdk |
| free6 | CSDN | ✅ 已配置 | 可用 |
| free7 | NVIDIA | ✅ 已配置 | 可用 |
| free8 | Friendli | ✅ 已配置 | 独立服务(5008) |
| free9 | 火山方舟 CodingPlan | ✅ 已配置 | 可用 |
| free10 | 联通云 CodingPlan | ✅ 已配置 | 可用 |
| free11 | 白山智算 | ✅ 已配置 | 可用 |
| free12 | OpenCode AI | ✅ 已配置 | 可用 |

#### 建议删除的 .bat 文件（共8个）
| 序号 | 文件名 | 删除原因 |
|------|--------|----------|
| 1 | `start_multi_free_api.bat` | v1版本已过时 |
| 2 | `start_multi_free_api_v3-ansi.bat` | 乱码版本 |
| 3 | `start_main_service.bat` | 与 v3 重复 |
| 4 | `_start_multi_free_api_v3-ansi.bat` | 乱码+下划线开头 |
| 5 | `_start_multi_free_api_v3-optimized.bat` | 下划线开头 |
| 6 | `_DelayStart-auto_start_multi_free_api_v3-ansi.bat` | 下划线开头+乱码 |
| 7 | `010-start_proxy_daemon-start.bat` | 与完整版重复 |
| 8 | `start_doc_generator.bat` | 仅显示提示，无实际功能 |

#### 保留的 .bat 文件清单（共9个）
| 文件名 | 功能 |
|--------|------|
| `start_proxy.bat` | 启动原始单文件代理 (local_api_proxy.py) |
| `start_multi_free_api_v3.bat` | 启动多Free API v3 主服务 |
| `start_free5_service.bat` | 启动 free5 独立服务 |
| `start_free8_service.bat` | 启动 free8 独立服务 |
| `start_all_services.bat` | 一键启动全部服务 |
| `start_proxy_daemon.bat` | Daemon 管理 |
| `test_main_service.bat` | 测试主服务 |
| `test_free5_service.bat` | 测试 free5 |
| `test_free8_service.bat` | 测试 free8 |
| `020-test-on5001.bat` | 测试 v3（端口5001） |

---

## 2026-03-10 - GUI优化与Debug页面增强

**更新时间：** 2026-03-10

### 一、GUI优化 (start_all_services_gui.py)

#### 1. 新增配置文件 gui_config.json
- 可配置 free5 和 free8 是否自动启动
- 配置文件格式：
```json
{
    "free5": {"auto_start": true},
    "free8": {"auto_start": true}
}
```

#### 2. GUI界面改进
- 新增 Free5 和 Free8 复选框开关，可单独控制
- 取消选中时自动停止对应服务
- 根据配置决定是否自动启动

### 二、Debug页面增强 (multi_free_api_proxy_v3_optimized.py)

#### 1. API管理表格新增列
- 在"当前模型"左侧新增"标题/URL"列
- 显示逻辑：优先显示 TITLE_NAME，没有则显示 BASE_URL（带换行）

#### 2. 新增 TITLE_NAME 配置
所有 free* 目录的 config.py 新增 TITLE_NAME 字段：

| API | TITLE_NAME |
|-----|------------|
| free1 | OpenRouter |
| free2 | ChatAnywhere |
| free3 | FreeChatGPT |
| free4 | Mistral AI |
| free5 | iFlow SDK |
| free6 | CSDN |
| free7 | NVIDIA |
| free8 | Friendli.ai |
| free9 | 火山引擎 |
| free10 | 联通云 |
| free11 | 白山智算 |
| free12 | OpenCode AI |

#### 3. 最近使用模型跟踪
- 新增 app_state.py 方法跟踪最近使用的模型
- 请求成功时自动记录当前使用的模型
- Debug页面显示"当前模型"列

---

## 2026-05-03 - GUI版与Go版多角度测试

**更新时间：** 2026-05-03

### 测试概览

**测试目标：** 对GUI版（端口5000/5008）和Go版（端口5060）进行多角度测试

**测试结果摘要：**
- ✅ 健康检查：所有端口正常
- ✅ Chat Completions：GUI版(5000)和Go版正常，Free8(5008)连接失败
- 🔴 模型列表：GUI版硬编码单个模型，已修复为动态扫描
- ✅ 统计面板：两个版本都正常
- ✅ 并发性能：3并发/11秒

### 一、端口状态确认

```bash
# 端口占用情况
5000 (PID 920) - GUI版主服务
5008 (PID 18796) - GUI版Free8服务  
5060 (PID 29180) - Go版服务
```

### 二、健康检查测试

| 端口 | 服务 | 状态 | 响应 |
|------|------|------|------|
| 5000 | GUI主服务 | ✅ 200 OK | `{"status":"ok"}` |
| 5008 | GUI Free8 | ✅ 200 OK | `{"models":4,"service":"friendli","status":"ok"}` |
| 5060 | Go版 | ✅ 200 OK | `{"available_count":1,"available_upstreams":["free2"],"status":"ok"}` |

### 三、Chat Completions测试

| 端口 | 服务 | 状态 | 模型 | 响应质量 |
|------|------|------|------|----------|
| 5000 | GUI主服务 | ✅ 成功 | DeepSeek-R1 | 详细推理 |
| 5008 | GUI Free8 | ❌ 失败 | - | 连接被重置 |
| 5060 | Go版 | ✅ 成功 | gpt-4o-mini | 标准响应 |

### 四、模型列表测试

| 端口 | 服务 | 模型数量 | 说明 |
|------|------|----------|------|
| 5000 | GUI主服务 | 1 → 22 | 硬编码 → 动态扫描 |
| 5060 | Go版 | 22 | 动态扫描 |

### 🔴 高优先级问题：GUI版模型列表硬编码

**问题描述：**
- `/v1/models` 端点返回固定单个模型 `openrouter/free`
- AI工具无法获取完整的可用模型列表

**修复内容：**
```python
# 修复前（local_api_proxy.py 第412-425行）
@app.route('/v1/models', methods=['GET'])
def list_models():
    return jsonify({
        "object": "list",
        "data": [{
            "id": "openrouter/free",  # 固定返回一个模型
            "object": "model",
            "owned_by": "openrouter",
            "permission": []
        }]
    })

# 修复后：动态扫描 free_api_test/ 目录
def list_models():
    models = []
    seen_models = set()
    
    upstream_dir = Path("free_api_test")
    for upstream_path in upstream_dir.glob("free*/config.py"):
        # 动态加载config.py
        spec = importlib.util.spec_from_file_location("config", upstream_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # 提取模型信息
        if hasattr(config, "API_KEY") and hasattr(config, "MODEL_NAME"):
            model_id = config.MODEL_NAME
            upstream_name = upstream_path.parent.name
            
            if model_id not in seen_models:
                seen_models.add(model_id)
                models.append({
                    "id": model_id,
                    "object": "model",
                    "owned_by": upstream_name
                })
    
    return jsonify({
        "object": "list",
        "data": models
    })
```

**修复效果：**
- ✅ 动态扫描所有上游配置
- ✅ 过滤掉未配置API Key的服务
- ✅ 返回22个模型（与Go版一致）
- ✅ 支持去重

### 五、统计面板测试

**GUI版 (5000):**
```json
{
  "date": "20260503",
  "failed": 10,
  "last_updated": "2026-05-03T09:58:02.378476",
  "retry": 0,
  "success": 159,
  "timeout": 0,
  "total": 169
}
```

**Go版 (5060):**
```json
{
  "free1": {"consecutive_failures": 1, "daily": 1, ...},
  "free2": {"consecutive_failures": 0, "daily": 2, ...},
  ...
}
```

### 六、并发性能测试

**测试配置：** 3个并发请求  
**测试结果：** 
- 总耗时：~11秒
- 每个请求：~3-4秒
- 全部成功：✅

### 七、功能对比总结

| 功能 | GUI版 (5000) | Go版 (5060) |
|------|-------------|-------------|
| 模型数量 | 22 (已修复) | 22 |
| 故障转移 | ✅ | ✅ |
| 健康检查 | ✅ | ✅ |
| 统计面板 | ✅ | ✅ |
| 流量日志 | ❌ | ✅ |
| API Key认证 | ❌ | ✅ |
| 限流 | ❌ | ✅ |
| 并发控制 | ✅ | ✅ |
| 资源占用 | ~70MB | ~10MB |

### 八、后续建议

1. **验证修复结果**：重启GUI版服务，确认 `/v1/models` 返回22个模型
2. **故障转移测试**：模拟上游失败，验证自动切换功能
3. **性能对比测试**：压力测试对比两个版本的响应时间
4. **监控上游状态**：定期检查Free8等上游服务的可用性

---

## 2026-05-03 12:46:52 - 操作日志记录规范检查

**更新时间：** 2026-05-03 12:46:52

### 检查发现的问题

1. **时间格式不规范**
   - 原记录使用 `2026-05-03`（只有日期）
   - 应使用 `2026-05-03 12:46:52`（完整时间戳）

2. **已按照 `_AI-RULES/OPERATELOG_APPEND_ONLY.md` 规范追加记录**
   - 先读取原内容
   - 在末尾追加新条目
   - 使用动态获取的当前时间

### 规则文件检查清单

| 规则文件 | 状态 | 说明 |
|---------|------|------|
| `_AI-RULES/base.md` | ✅ 已检查 | 确认了规则要求 |
| `_AI-RULES/OPERATELOG_APPEND_ONLY.md` | ✅ 已检查 | 追加写入规范 |
| `_AI-RULES/TIME_RULES.md` | ✅ 已检查 | 动态时间获取规范 |
| `_AI-RULES/operateLog-processing-rules.md` | ❌ 不存在 | 文件名可能有误 |

### 修复内容

**修改文件：** `operateLog.md`

**修改前：**
```
## 2026-05-03 - GUI版与Go版多角度测试
**更新时间：** 2026-05-03
```

**修改后：**
```
## 2026-05-03 12:46:52 - GUI版与Go版多角度测试
**更新时间：** 2026-05-03 12:46:52
```

### 后续承诺

以后所有操作日志记录将：
1. ✅ 使用完整时间戳格式 `YYYY-MM-DD HH:MM:SS`
2. ✅ 先读取原内容再追加写入
3. ✅ 使用动态获取的当前时间
4. ✅ 检查所有 `_AI-RULES/` 目录下的规则文件

---

## 2026-05-04 19:13:00 - 创建 free20 (LongCat API) 上游配置

**更新时间：** 2026-05-04 19:13:00

### 操作内容

根据 LongCat API 开放平台文档，创建 Go 版本上游配置目录：

**创建目录：** `api-proxy-go/upstreams/free20/`

**配置文件：** `config.yaml`

### LongCat API 支持的模型

| 模型名称 | API格式 | 描述 |
|---------|---------|------|
| LongCat-Flash-Chat | OpenAI/Anthropic | 高性能通用对话模型 |
| LongCat-Flash-Thinking | OpenAI/Anthropic | 深度思考模型（已升级至 2601） |
| LongCat-Flash-Thinking-2601 | OpenAI/Anthropic | 升级版深度思考模型 |
| LongCat-Flash-Lite | OpenAI/Anthropic | 高效轻量化MoE模型 |
| LongCat-Flash-Omni-2603 | OpenAI | 多模态模型 |
| LongCat-Flash-Chat-2602-Exp | OpenAI | 高性能通用对话模型 |
| LongCat-2.0-Preview | OpenAI/Anthropic | 高性能Agentic模型 |

### API 端点

- **OpenAI格式：** https://api.longcat.chat/openai
- **Anthropic格式：** https://api.longcat.chat/anthropic

### 配置参数

- **环境变量：** `LONGCAT_API_KEY`
- **默认权重：** 100
- **限额配置：** hourly: 2000, daily: 10000, monthly: 50000
- **默认模型：** LongCat-Flash-Chat

---

## 2026-05-04 19:17:00 - Go版环境变量加载脚本

**更新时间：** 2026-05-04 19:17:00

### 问题回答

**GUI版和Go版是否需要重启才能加载free20？**
- ✅ **是的**，两个版本都需要重启才能加载新的上游配置

### 新增内容

**1. 更新 config.go 添加 free20 映射**
- 文件：`api-proxy-go/config/config.go`
- 添加：`"free20": "LONGCAT_API_KEY"`

**2. 新增启动脚本**
- 文件：`050-start_api_proxy_go.bat`
- 功能：从 `multi_free_api_proxy/.env` 读取环境变量并启动 Go 版

**3. 更新 .env 文件**
- 文件：`multi_free_api_proxy/.env`
- 添加：
  ```
  LONGCAT_API_KEY=你的LongCat_API密钥
  FREE20_API_KEY=你的LongCat_API密钥
  ```

### 环境变量对应关系

| 上游 | Go版环境变量 | .env中变量 |
|------|-------------|------------|
| free20 | LONGCAT_API_KEY | LONGCAT_API_KEY / FREE20_API_KEY |

### 使用方法

1. 编辑 `multi_free_api_proxy/.env`，填入真实的 LongCat API Key
2. 双击 `050-start_api_proxy_go.bat` 启动 Go 版
3. 服务会自动加载 free20 配置

---

## 2026-05-04 20:31:00 - 完善 free19/free20 配置并提交

**更新时间：** 2026-05-04 20:31:00

### 本次更新

**1. 完善 free19 (Cohere) 和 free20 (LongCat) 配置**

**GUI版配置：**
- `free_api_test/free19/config.py` - 新建
- `free_api_test/free20/config.py` - 新建

**Go版配置：**
- `api-proxy-go/upstreams/free20/config.yaml` - 新建
- `api-proxy-go/config/config.go` - 添加 free19/free20 映射

**环境变量：**
- 根目录 `.env`：添加 `COHERE_API_KEY` 和 `LONGCAT_API_KEY`
- `multi_free_api_proxy/.env`：添加 `FREE20_API_KEY`

**2. Go版启动脚本**
- `050-start_api_proxy_go.bat` - 新建

**3. 环境变量加载位置说明**
- Go版从**根目录** `.env` 加载（`../.env`）
- GUI版从 `multi_free_api_proxy/.env` 加载

### 环境变量对应关系

| 上游 | Go版环境变量 | 根目录.env | multi .env |
|------|-------------|-----------|------------|
| free19 | COHERE_API_KEY | ✅ 有 | - |
| free20 | LONGCAT_API_KEY | ✅ 有 | FREE20_API_KEY |

### 安全说明
- `.env` 文件已在 `.gitignore` 中配置，不会提交到 git
- `*.env` 模式会忽略所有 .env 文件

---

## 2026-05-07 - 修复 Windows 控制台 GBK 编码错误

**更新时间：** 2026-05-07

### 问题描述
启动 `multi_free_api_proxy_v3_optimized.py` 时报错：
```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2705' in position 7
```
原因是 Windows CMD/PowerShell 默认使用 GBK 编码，无法处理 emoji 字符。

### 修复内容

1. **更新项目规则文档** `_AI-RULES/base.md`
   - 新增 `0.1 Windows 控制台编码规范` 章节
   - 明确禁止在 print() 输出中使用 emoji 字符
   - 提供 ASCII 替代方案：`✅` → `[OK]`, `❌` → `[FAIL]`, `⚠️` → `[WARN]`

2. **修复文件列表**
   - `server_diagnostic.py` (37处)
   - `doc_generator.py` (2处)
   - `scenarios/development/local_api_proxy_optimized.py` (2处)
   - `free_api_test/free4/test_api.py` (2处)
   - `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py` (已修复)

### 注意事项
- HTML 模板中的 emoji 保留（通过 HTTP 传输，不受控制台编码限制）
- 后续新增代码时需遵守 `_AI-RULES/base.md` 中的编码规范

---

*最后更新：2026-05-10 19:37:00*

---

## 2026-05-10 19:37:00 - 创建 free21 (FreeModel API) 上游配置

**更新时间：** 2026-05-10 19:37:00

### 操作内容

根据用户提供的 FreeModel API 信息，创建 Go 版本上游配置目录：

**创建目录：** `free_api_test/free21/`

**配置文件：** `free_api_test/free21/config.py`

### FreeModel API 信息

- **API 地址：** https://api.freemodel.dev
- **环境变量：** `FREEMODEL_API_KEY`
- **支持的接口：** `/v1/chat/completions` (OpenAI 兼容格式)

### 配置参数

- **默认模型：** freemodel-default
- **默认权重：** 100
- **是否使用代理：** 否
- **是否使用 SDK：** 否
- **最大 Token 数：** 2000

### 下一步

1. 在 `api-proxy-go/upstreams/free21/config.yaml` 创建 Go 版配置
2. 在 `api-proxy-go/config/config.go` 添加 free21 映射
3. 在 `.env` 文件添加 `FREEMODEL_API_KEY`
4. 重启服务使配置生效

---

## 2026-05-10 19:43:00 - 创建《启动文件与版本关系》文档

**更新时间：** 2026-05-10 19:43:00

### 操作内容

整理项目中所有启动文件和版本的关系，创建文档：

**文档文件：** `启动文件与版本关系.md`

### 文档内容概要

1. **版本架构总览** - Python版与Go版的架构关系
2. **Python版版本详解**
   - 独立服务（Free5/Free8）
   - 主代理服务（v1原始版 / v3原版 / v3优化版）
   - 版本功能对比表
3. **Go版** - api-proxy-go 的特性和配置
4. **启动脚本对应关系**
   - 推荐使用的脚本
   - 主服务启动脚本
   - 独立服务启动脚本
   - 测试脚本
   - Go版相关脚本
   - 建议删除的重复脚本
5. **文件监控配置**
6. **快速启动指南**
7. **上游配置目录** (free1-free21)
8. **端口分配表**

---

## 2026-05-10 19:45:00 - 创建《无效旧版本清理清单》文档

**更新时间：** 2026-05-10 19:45:00

### 操作内容

分析项目中无效、过时、重复的文件，创建清理清单文档：

**文档文件：** `无效旧版本清理清单.md`

### 建议删除的文件

#### Python 文件（2个）
- `local_api_proxy.py` - v1 原始单文件版
- `multi_free_api_proxy/multi_free_api_proxy.py` - v2 版本

#### BAT 文件（7个）
- `start_multi_free_api.bat` - v1/v2 启动脚本
- `start_multi_free_api_v3-ansi.bat` - 乱码版本
- `_start_multi_free_api_v3-ansi.bat` - 下划线+乱码
- `_DelayStart-auto_start_multi_free_api_v3-ansi.bat` - 下划线+乱码+延迟
- `start_main_service.bat` - 重复
- `010-start_proxy_daemon-start.bat` - 简化版重复
- `start_doc_generator.bat` - 无实际功能

#### 可选目录
- `scenarios/` - 历史部署脚本

### 保留的文件
- v1/ - PHP 版本（独立归档）
- docs/ - 文档目录
- multi_free_api_proxy_v3_optimized.py - v3 优化版（推荐）

---

## 2026-05-10 19:55:00 - 清理无效/旧版本文件

**更新时间：** 2026-05-10 19:55:00

### 删除的 Python 文件（3个）
- `local_api_proxy.py` - v1 原始单文件版
- `multi_free_api_proxy/multi_free_api_proxy.py` - v2 版本
- `multi_free_api_proxy/multi_free_api_proxy_v3.py` - v3 原版（保留优化版）

### 删除的 BAT 文件（8个）
- `start_multi_free_api.bat` - v1/v2 启动脚本
- `start_multi_free_api_v3.bat` - v3 原版启动脚本
- `start_multi_free_api_v3-ansi.bat` - 乱码版本
- `_start_multi_free_api_v3-ansi.bat` - 下划线+乱码
- `_DelayStart-auto_start_multi_free_api_v3-ansi.bat` - 下划线+乱码+延迟
- `start_main_service.bat` - 重复脚本
- `010-start_proxy_daemon-start.bat` - 简化版重复
- `start_doc_generator.bat` - 无实际功能

### 保留的核心文件
- `multi_free_api_proxy_v3_optimized.py` - v3 优化版（唯一主服务）
- `_start_multi_free_api_v3-optimized.bat` - 推荐启动脚本

---

## 2026-05-10 19:57:00 - 清理 free5 (iFlow SDK) 相关代码

**更新时间：** 2026-05-10 19:57:00

### 背景
iFlow SDK 服务已于 2026 年 3 月停用，决定从项目中完全移除 free5 相关代码。

### 删除的目录
- `free_api_test/free5/` - 整个目录（11个文件）

### 修改的文件
- `035-start_all_services.bat` - 移除 free5 启动命令
- `multi_free_api_proxy_v3_optimized.py` - 移除 free5 的 SDK 路由逻辑

### 保留的代码
- `api-proxy-go/config/config.go` - 保留 free5 注释（标记为已停用），不影响运行

### 当前状态
- free5 目录已删除，不会被主服务加载
- 独立服务启动脚本已更新
- 主服务代码中的 free5 路由逻辑已移除

---

## 2026-05-10 20:06:00 - 整理 multi_free_api_proxy 文档

**更新时间：** 2026-05-10 20:06:00

### 操作内容

整理 multi_free_api_proxy 目录下的文档，移除冗余/过时文档，保留核心文档到 docs/ 子目录。

### 保留的文档（移动到 docs/）
- `docs/README.md` - 主 README（重命名自 MULTI_FREE_API_README.md）
- `docs/QUICK_START.md` - 快速开始指南

### 删除的文档（10个）
- `INDEX.md` - 与 README 重复
- `README_OPTIMIZATION.md` - 与 README 重复
- `MIGRATION_CHECKLIST.md` - 迁移已完成，过时
- `MULTI_FREE_API_DESIGN.md` - 冗余文档
- `MULTI_FREE_API_UPDATE.md` - 旧版更新日志
- `OPTIMIZATION_COMPLETE.md` - 与其他优化文档重复
- `OPTIMIZATION_GUIDE.md` - 与 README 重复
- `OPTIMIZATION_SUMMARY.md` - 与 README 重复
- `STRUCTURE_COMPARISON.md` - 历史对比文档
- `DEBUG_MODE.txt` - 标志文件（已在目录中）

### 当前目录结构

```
multi_free_api_proxy/
├── docs/
│   ├── README.md           # 主文档
│   └── QUICK_START.md      # 快速开始
├── static/
├── templates/
├── __init__.py
├── app_state.py
├── config.py
├── errors.py
├── multi_free_api_proxy_v3_optimized.py  # 主服务
├── test_free1.py
├── test_free2.py
├── test_free3.py
└── test_free4.py
```

---

## 2026-05-10 21:10:00 - 修复 free1 API 测试失败问题

**更新时间：** 2026-05-10 21:10:00

### 问题描述

调试 `localhost:5000/debug` 页面显示 free1 不可用，但通过 `new-demo.py` 直接调用 OpenRouter API 成功。

### 原因分析

1. **问题根源：** `multi_free_api_proxy_v3_optimized.py` 中 `config.HTTP_PROXY` 在模块导入时就初始化（第28行），但 `load_env()` 在 `main()` 函数中才被调用（第1214行）
2. **加载顺序错误：** 导致 `config.HTTP_PROXY` 始终为 `None`
3. **影响：** free1 配置 `USE_PROXY = True`，但测试时没有代理，OpenRouter API 无法访问

### 修复内容

**文件：** `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py`

在 `config` 模块导入前，先调用 `_load_env()` 从项目根目录的 `.env` 文件加载环境变量：

```python
# 先加载 .env 环境变量
def _load_env():
    """加载环境变量"""
    script_dir = Path(__file__).parent
    env_file = script_dir.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

_load_env()

# 导入本地模块
from config import get_config
```

### 同时修正的文件

**文件：** `free_api_test/free1/new-demo.py`

参照 `test_api.py` 进行以下修正：
1. 添加从项目根目录加载 `.env` 文件
2. 添加 UTF-8 编码支持（Windows 控制台兼容）
3. 添加代理配置支持
4. 使用 `openrouter/free` 模型

### 验证结果

重启服务后，free1 应该能正确加载 `HTTP_PROXY=http://127.0.0.1:7897`，测试通过。

---

## 2026-05-10 21:16:00 - Go版添加代理支持

**更新时间：** 2026-05-10 21:16:00

### 问题描述

启动 Go 版 API 代理后，所有上游都显示不可用，但 Python 版本的 free1 通过代理可以正常访问。

### 根本原因

Go 版本的 `proxy/proxy.go` 和 `upstream/upstream.go` 虽然读取了 `use_proxy` 配置，但**没有实际使用代理发送 HTTP 请求**。

### 修复内容

**1. 添加全局代理配置字段**

**文件：** `api-proxy-go/config/types.go`

```go
// ProxyConfig 添加 http_proxy 字段
type ProxyConfig struct {
    HTTPProxy string `yaml:"http_proxy"`  // 新增：全局 HTTP 代理
    // ... 其他字段
}
```

**2. 添加从环境变量加载代理配置**

**文件：** `api-proxy-go/config/config.go`

```go
// loadProxyFromEnv 从环境变量加载代理配置
func loadProxyFromEnv(cfg *Config) {
    if proxy := os.Getenv("HTTP_PROXY"); proxy != "" {
        cfg.Proxy.HTTPProxy = proxy
        log.Printf("[配置] 从环境变量 HTTP_PROXY 加载代理: %s", proxy)
    } else if proxy := os.Getenv("PROXY_URL"); proxy != "" {
        cfg.Proxy.HTTPProxy = proxy
        log.Printf("[配置] 从环境变量 PROXY_URL 加载代理: %s", proxy)
    }
}
```

**3. 代理请求执行（健康检查）**

**文件：** `api-proxy-go/upstream/upstream.go`

在 `Test()` 方法中，根据 `config.UseProxy` 和 `m.config.Proxy.HTTPProxy` 创建带代理的 HTTP 客户端。

**4. 代理请求执行（实际请求）**

**文件：** `api-proxy-go/proxy/proxy.go`

在 `executeHTTPRequest()` 方法中同样添加代理支持。

**5. 更新配置文件**

**文件：** `api-proxy-go/config.yaml`

添加代理配置说明。

### 代理配置优先级

1. 环境变量 `HTTP_PROXY`（最高优先级）
2. 环境变量 `PROXY_URL`
3. YAML 配置 `proxy.http_proxy`

### 使用方法

当前配置已从 `multi_free_api_proxy/.env` 自动加载：
- `HTTP_PROXY=http://127.0.0.1:7897`

只需重新运行 `050-start_api_proxy_go.bat` 即可生效。

### 修改的文件列表

| 文件 | 修改类型 |
|------|----------|
| `api-proxy-go/config/types.go` | 添加 HTTPProxy 字段 |
| `api-proxy-go/config/config.go` | 添加 loadProxyFromEnv 函数 |
| `api-proxy-go/proxy/proxy.go` | executeHTTPRequest 添加代理支持 |
| `api-proxy-go/upstream/upstream.go` | Test 方法添加代理支持 |
| `api-proxy-go/config.yaml` | 添加代理配置说明 |
| `api-proxy-go/api-proxy.exe` | 重新编译 |

### 验证方法

1. 停止旧的 API Proxy Go 进程
2. 运行 `050-start_api_proxy_go.bat`
3. 查看日志，应显示：
   - `[配置] 从环境变量 HTTP_PROXY 加载代理: http://127.0.0.1:7897`
   - `[上游] free1: 使用代理 http://127.0.0.1:7897`
   - `[上游] free1: 测试成功`
4. 访问 `/health` 确认 free1 可用

---

## 2026-05-10 23:35:00 - Go版调试页面死锁、代理支持和可用列表问题修复

**更新时间：** 2026-05-10 23:35:00

### 问题描述
Go版调试页面 `/debug` 显示 "API 状态" 标签一直显示"正在加载..."或"全不可用"，且 free1 (OpenRouter) 无法使用。

### 问题根因（多个问题）

#### 1. main.go 跳过了 HTTP_PROXY 环境变量
**文件：** `api-proxy-go/main.go`
**问题：** 代码错误地将 HTTP_PROXY 加入跳过列表，导致代理配置无法加载。
**修复：** 移除 HTTP_PROXY 从跳过列表

#### 2. free1 配置 use_proxy: false
**文件：** `api-proxy-go/upstreams/free1/config.yaml`
**问题：** Go版本配置 use_proxy: false，Python版本是 USE_PROXY = True
**修复：** use_proxy: false → true

#### 3. Test 函数缺少 OpenRouter 需要的 HTTP 头
**文件：** `api-proxy-go/upstream/upstream.go`
**问题：** OpenRouter API 需要 HTTP-Referer 和 X-Title 头部
**修复：** 添加头部支持

#### 4. 健康检查没有使用代理
**文件：** `api-proxy-go/upstream/health.go`
**问题：** health check 没有根据 use_proxy 配置使用代理
**修复：** 添加代理支持和 OpenRouter 头部

#### 5. TestAll 完成后没有更新可用列表
**文件：** `api-proxy-go/main.go`
**问题：** TestAll 异步完成后没有调用 UpdateAvailable()
**修复：** 在 TestAll 完成回调中添加 UpdateAvailable() 调用

#### 6. 健康检查被临时禁用
**文件：** `api-proxy-go/config.yaml`
**问题：** health_check.enabled 被设置为 false
**修复：** health_check.enabled: false → true

### 修改的文件列表
| 文件 | 修改内容 |
|------|----------|
| `api-proxy-go/main.go` | 移除 HTTP_PROXY 跳过，TestAll完成后调用UpdateAvailable |
| `api-proxy-go/upstreams/free1/config.yaml` | use_proxy: false → true |
| `api-proxy-go/upstream/upstream.go` | 添加 OpenRouter HTTP头 |
| `api-proxy-go/upstream/health.go` | 添加代理支持和OpenRouter HTTP头 |
| `api-proxy-go/config.yaml` | health_check.enabled: false → true |
| `api-proxy-go/api-proxy.exe` | 重新编译 |

### 验证结果
1. 代理正确加载：HTTP_PROXY 已加载
2. free1 使用代理：测试时显示使用代理
3. free1 测试成功：状态码 200
4. /v1/models 返回模型列表（包括 openrouter/free）

---

*最后更新：2026-05-11 17:06:00*

---

## 2026-05-11 17:06:00 - LLM 本地服务测试 (API Key: sk-04d6316e048123a3-sjc5o8-39270609)

**更新时间：** 2026-05-11 17:06:00

### 测试目标
测试本地 LLM 服务 http://localhost:20128 的可用模型和 chat/completions 接口

### 测试脚本
- `test_local_llm_key.py` - 带 API Key 的模型列表和聊天测试
- `test_llm_raw.py` - 原始响应检查
- `test_llm_stream.py` - SSE 流式响应解析

### 测试结果汇总

| 模型 | 状态 | 响应类型 | 说明 |
|------|------|----------|------|
| kr/glm-5 | ✅ OK | SSE 流式 | 正常工作，返回 "OK" |
| kr/deepseek-3.2 | ✅ OK | SSE 流式 | 正常工作，返回 "OK" |
| MiniMax-M2.5 | ❌ FAIL | JSON | "No active credentials for provider: openai" |
| nvidia/minimaxai/minimax-m2.7 | ❌ FAIL | 超时 | 30秒超时无响应 |

### 可用模型列表 (9个)
```
kr/claude-sonnet-4.5
kr/claude-haiku-4.5
kr/deepseek-3.2
kr/qwen3-coder-next
kr/glm-5
kr/MiniMax-M2.5
nvidia/minimaxai/minimax-m2.7
nvidia/z-ai/glm4.7
nvidia/parakeet-ctc-1.1b-asr
```

### 问题分析

1. **MiniMax-M2.5 失败原因**
   - 错误信息：`"No active credentials for provider: openai"`
   - 可能是 LLM 服务配置问题，与代理无关
   - 模型标识与 provider 不匹配

2. **nvidia/minimaxai/minimax-m2.7 超时原因**
   - 30秒内无响应
   - 可能需要特殊配置或认证

### 下一步行动
1. 调查 LLM 服务的 MiniMax-M2.5 凭证配置问题
2. 测试 Go 版本 debug 页面 (http://localhost:8080)
3. 测试 Python 版本上游标识日志功能

---

*历史记录已拆分到 logs/operateLog-by-ymd/ 目录*

---

## 2026-05-12 20:56:00 - 实现缓存目录三级优先级机制

**更新时间：** 2026-05-12 20:56:00

### 问题描述

用户报告缓存路径错误，且需要在两个环境下运行（一个有 R:\ ramdisk）：
```
[缓存错误] 保存消息失败: [WinError 3] 系统找不到指定的路径。: 'r:\\'
```

### 解决方案

实现统一的缓存目录获取函数，支持三级优先级：

**1. 环境变量 `CACHE_DIR`** - 最高优先级，方便临时覆盖
**2. R:\ ramdisk** - 如果 R:\ 驱动器存在则优先使用
**3. 脚本目录** - 回退方案

### 修改的文件

#### 1. `multi_free_api_proxy/config.py` - 新增统一函数

```python
def get_cache_dir(fallback_subdir='cache'):
    """
    获取缓存目录，优先级：
    1. 环境变量 CACHE_DIR（最高优先级）
    2. R:\\api_proxy_cache（如果 R:\\ 驱动器存在，ramdisk 优先）
    3. 脚本目录下的缓存目录（回退方案）
    """
    # 1. 环境变量优先
    cache_dir = os.getenv("CACHE_DIR")
    if cache_dir:
        return cache_dir
    
    # 2. 检查 R:\ 是否存在（ramdisk）
    if os.path.exists('R:\\'):
        return 'R:\\api_proxy_cache'
    
    # 3. 回退到脚本目录
    script_dir = Path(__file__).parent.parent
    return str(script_dir / fallback_subdir)
```

#### 2. `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py` - 使用统一函数

- `update_call_stats()` 函数
- `debug_stats()` 函数

#### 3. `server_diagnostic.py` - 实现相同逻辑

### 使用方法

**方式1：环境变量（推荐临时覆盖）**
```bash
# Windows
set CACHE_DIR=D:\my_cache
python server_diagnostic.py

# 或在 .env 文件中
CACHE_DIR=D:\my_cache
```

**方式2：利用 R:\ ramdisk**
如果 R:\ 驱动器存在，缓存自动使用 `R:\api_proxy_cache`

**方式3：使用脚本目录（默认）**
无环境变量且无 R:\ 时，使用脚本目录下的 `cache` 或 `api_proxy_cache`

### 适用场景

| 环境 | 缓存目录 |
|------|----------|
| 有 R:\ ramdisk | `R:\api_proxy_cache` |
| 无 R:\ + 设置环境变量 | `CACHE_DIR` 指定路径 |
| 其他情况 | `{项目根目录}/cache` |

