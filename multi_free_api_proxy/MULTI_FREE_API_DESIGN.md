# 多Free API代理服务设计方案

## 需求分析

1. free1走代理，free2和free3不走代理
2. 启动时调用free*下的test_api.py一次，测试API是否有效
3. 有效的API直接读其.env中的api地址和key和模型使用，后续服务时不再调用free下的代码
4. 忽略原始请求中的model参数，只使用每个API配置的特定模型

## 设计方案

### 1. 配置管理

#### .env文件
```
# Free API Keys
FREE1_API_KEY=sk-or-v1-xxxxx
FREE2_API_KEY=sk-RJxxxxxxt
FREE3_API_KEY=sk-t76xxxxxx8

# 代理配置
HTTP_PROXY=http://127.0.0.1:7897

# 其他配置
CACHE_DIR=r:\api_proxy_cache
MAX_CONCURRENT_REQUESTS=5
```

#### API配置表

| API | API Key | Base URL | 模型 | 使用代理 |
|-----|----------|-----------|------|----------|
| free1 | FREE1_API_KEY | https://openrouter.ai | openrouter/free | 是 |
| free2 | FREE2_API_KEY | https://api.chatanywhere.tech | gpt-3.5-turbo | 否 |
| free3 | FREE3_API_KEY | https://free.v36.cm | gpt-3.5-turbo | 否 |

### 2. 启动流程

```
1. 加载.env文件
2. 从.env读取API Keys和代理配置
3. 直接配置API信息（不从free*目录读取）
   - free1: API Key, Base URL, 模型, use_proxy=True
   - free2: API Key, Base URL, 模型, use_proxy=False
   - free3: API Key, Base URL, 模型, use_proxy=False
4. 测试所有API是否可用
   - 使用配置的API Key和Base URL
   - 使用配置的模型
   - free1使用代理，free2和free3不使用代理
5. 将可用的API加入服务队列
6. 启动服务
```

### 3. 运行时流程

```
收到请求
  ↓
从服务队列获取下一个可用API（轮换）
  ↓
使用该API的配置（API Key, Base URL, 模型）
  ↓
根据use_proxy决定是否使用代理
  ↓
发送请求到API
  ↓
返回响应
```

### 4. 代码结构

```
multi_free_api_proxy_v3.py
├── 配置管理
│   ├── load_env()          # 加载.env文件
│   └── load_api_configs()  # 从.env加载API配置
├── 启动测试
│   ├── test_api_startup()    # 测试单个API
│   └── test_all_apis_startup()  # 测试所有API
├── 请求处理
│   ├── get_next_available_api()  # 获取下一个可用API
│   └── execute_with_free_api()  # 使用API执行请求
└── API端点
    ├── /v1/chat/completions  # 聊天完成
    ├── /v1/models            # 列出模型
    ├── /health                # 健康检查
    ├── /health/upstream       # 上游API状态
    ├── /debug/stats           # 调试统计
    └── /debug/apis            # API状态
```

### 5. 关键特性

1. **配置集中管理**
   - 所有API配置存储在.env文件
   - 不依赖free*目录的test_api.py
   - 便于管理和保护API Keys

2. **代理控制**
   - free1: use_proxy=True（使用HTTP_PROXY）
   - free2: use_proxy=False（不使用代理）
   - free3: use_proxy=False（不使用代理）

3. **模型固定**
   - free1: openrouter/free
   - free2: gpt-3.5-turbo
   - free3: gpt-3.5-turbo
   - 忽略客户端请求的model参数

4. **启动测试**
   - 启动时测试所有API
   - 只测试配置了API Key的
   - 将可用的加入服务队列

5. **轮换使用**
   - 请求时轮换使用可用API
   - 自动处理代理配置
   - 自动使用配置的模型

## 使用方法

1. 配置.env文件
2. 启动服务：
   ```bash
   python multi_free_api_proxy_v3.py
   ```
3. 服务会自动：
   - 加载API配置
   - 测试API可用性
   - 轮换使用可用API
   - 根据配置使用代理

## 注意事项

1. 确保已安装所需依赖：
   ```bash
   pip install flask requests watchdog
   ```

2. 确保API Keys配置正确

3. 根据网络环境配置代理

4. 启动时会测试所有API，确保它们可用
