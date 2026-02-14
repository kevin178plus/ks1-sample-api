# 🛠️ 开发调试场景

**适用场景：** 本地开发、测试环境、功能调试

## 📁 文件说明

### 🔧 原始开发文件
- **`local_api_proxy.py`** - 完整功能的本地代理服务
  - 支持文件监控和自动重载
  - 调试模式和消息缓存
  - 网页调试面板
  - 实时调用统计

- **`start_proxy.bat`** - 开发环境启动脚本
  - 自动检查和安装依赖
  - 便捷的服务启动

- **`test_local_proxy.py`** - 本地测试脚本
  - API功能测试
  - 连接性验证
  - 示例调用代码

### 🚀 优化版开发文件 (推荐)
- **`local_api_proxy_optimized.py`** - 优化版代理服务
  - ✅ 30秒超时控制，避免无限等待
  - ✅ 缓存文件数量限制，防止磁盘耗尽
  - ✅ 更好的错误处理和分类
  - ✅ 完整的中文支持
  - ✅ 线程安全的文件监控

- **`start_proxy_optimized.bat`** - 优化版启动脚本
  - ✅ UTF-8编码支持
  - ✅ 完整的Python环境检查
  - ✅ 智能的.env文件创建
  - ✅ 清晰的用户提示

- **`test_local_proxy_optimized.py`** - 优化版测试脚本
  - ✅ 30秒超时控制
  - ✅ 中英文双语测试
  - ✅ 详细的错误分类和处理
  - ✅ 测试结果统计汇总

## 🚀 开发启动

### 🌟 推荐：使用优化版

#### 1. 快速启动（优化版）
```bash
# 运行优化版启动脚本
start_proxy_optimized.bat

# 或直接启动优化版服务
python local_api_proxy_optimized.py
```

#### 2. 测试功能（优化版）
```bash
# 运行优化版测试
python test_local_proxy_optimized.py
```

### 📋 原始版本启动

#### 1. 快速启动（原始版）
```bash
# 运行原始版启动脚本
start_proxy.bat

# 或直接启动原始版服务
python local_api_proxy.py
```

#### 2. 测试功能（原始版）
```bash
# 运行原始版测试
python test_local_proxy.py
```

### 🔧 调试模式配置
```bash
# 创建调试模式文件
echo > DEBUG_MODE.txt

# 配置缓存目录（可选）
echo CACHE_DIR=./cache > .env
echo OPENROUTER_API_KEY=your-key-here >> .env
```

### 📊 访问调试界面
- **API服务**: http://localhost:5000/v1/chat/completions
- **调试面板**: http://localhost:5000/debug
- **健康检查**: http://localhost:5000/health
- **统计接口**: http://localhost:5000/debug/stats

## 🧪 测试功能

### 🌟 优化版测试（推荐）
```bash
# 运行优化版测试脚本（自动测试中英文）
python test_local_proxy_optimized.py
```

**优化版测试特点：**
- ✅ 30秒超时控制
- ✅ 中英文双语测试
- ✅ 详细错误分类
- ✅ 测试结果统计汇总
- ✅ 常见问题排查指引

### 📋 原始版测试
```bash
# 运行原始版测试脚本
python test_local_proxy.py

# 手动测试
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

### 🔍 调试功能对比

| 功能 | 原始版 | 优化版 |
|------|--------|--------|
| 文件监控 | ✅ | ✅ |
| 消息缓存 | ✅ | ✅ |
| 调用统计 | ✅ | ✅ |
| 网页面板 | ✅ | ✅ |
| 超时控制 | ❌ | ✅ 30秒 |
| 缓存限制 | ❌ | ✅ 100文件 |
| 中文支持 | ⚠️ 部分 | ✅ 完整 |
| 错误处理 | ⚠️ 基础 | ✅ 详细 |

### 🐛 常见问题排查

**使用优化版时的优势：**
- 超时错误：明确提示"请求超时"
- 连接错误：提示"连接失败，请确保服务已启动"
- API错误：区分网络错误和配置错误
- 测试结果：提供具体的修复建议

## 💡 开发特性

- **热重载** - 配置文件修改自动生效，无需重启
- **详细日志** - 完整的请求响应记录
- **错误追踪** - 详细的错误信息和堆栈
- **性能监控** - 响应时间和调用次数统计

## 📊 调试数据

### 缓存文件结构
```
cache/
├── 20240214_143022_123_REQUEST_a1b2c3d4.json
├── 20240214_143025_456_RESPONSE_a1b2c3d4.json
├── CALLS_20240214.json
└── ...
```

### 调试面板功能
- 今日调用次数实时更新
- 最后更新时间显示
- 自动刷新（5秒间隔）
- JSON格式统计数据

## 🔧 开发配置

### .env 文件示例
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
CACHE_DIR=./cache
REFERER_URL=http://localhost:5000
```

### 调试模式控制
```bash
# 启用调试模式
echo > DEBUG_MODE.txt

# 禁用调试模式
del DEBUG_MODE.txt
```

## ⚠️ 开发注意事项

1. **调试数据** - 启用调试模式会产生大量缓存文件
2. **性能影响** - 文件监控和缓存会轻微影响性能
3. **本地访问** - 默认只绑定localhost，外网无法访问
4. **API密钥** - 确保.env文件不要提交到版本控制

## 🧪 开发测试流程

1. **环境准备** - 运行start_proxy.bat安装依赖
2. **配置密钥** - 设置OPENROUTER_API_KEY
3. **启动服务** - 启动local_api_proxy.py
4. **功能测试** - 使用test_local_proxy.py测试
5. **调试分析** - 访问/debug查看详细信息
6. **修改迭代** - 修改配置文件，自动重载生效

## 📚 扩展开发

### 添加新API端点
在local_api_proxy.py中添加路由：
```python
@app.route('/custom/endpoint', methods=['POST'])
def custom_endpoint():
    # 自定义逻辑
    return jsonify({"result": "custom response"})
```

### 修改模型配置
```python
# 在chat_completions函数中修改
openrouter_payload = {
    "model": "openrouter/deepseek-r1",  # 改为其他模型
    # ...
}
```

这个场景适合日常开发、功能测试和问题调试。