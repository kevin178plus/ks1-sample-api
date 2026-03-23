# 多Free API代理服务更新说明

## 更新内容

### 1. 修改了.env文件
添加了以下Free API Keys:
```
FREE1_API_KEY=sk-or-v1-e38xxxxxxxxxxxxxx2
FREE2_API_KEY=sk-RJexxxxxxxxxxx
FREE3_API_KEY=sk-t76Oxxxxxxxxxxxxxxxxxx
```

### 2. 修改了free*/test_api.py文件
修改了free1、free2、free3目录下的test_api.py文件，使其从.env读取API Key:
```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取API Key
API_KEY = os.getenv("FREE1_API_KEY")  # 或 FREE2_API_KEY, FREE3_API_KEY
if not API_KEY:
    raise ValueError("FREE1_API_KEY not found in .env file")
```

### 3. 修改了multi_free_api_proxy.py
主要修改:
1. 从.env加载Free API Keys
2. 为每个API指定特定的模型:
   - free1: openrouter/free
   - free2: gpt-3.5-turbo
   - free3: gpt-3.5-turbo
3. 忽略原始请求中的model参数，只使用API配置的模型

## 使用方法

1. 确保已安装python-dotenv:
```bash
pip install python-dotenv
```

2. 启动服务:
```bash
python multi_free_api_proxy_v2.py
```

3. 服务会自动:
   - 检测free1、free2、free3三个API
   - 测试这些API是否可用
   - 轮换使用这些可用的API
   - 每个API使用其配置的特定模型

## API模型配置

| API | 模型 | 说明 |
|-----|------|------|
| free1 | openrouter/free | OpenRouter免费模型 |
| free2 | gpt-3.5-turbo | ChatAnywhere API |
| free3 | gpt-3.5-turbo | Free ChatGPT API |

## 注意事项

1. 所有API Key都存储在.env文件中，便于管理和保护
2. 每个API使用其特定的模型，忽略客户端请求的model参数
3. 服务会轮换使用这三个API，实现负载均衡
4. 定期(每5分钟)重新测试所有API的可用性

---

## 新增功能（2026-03-13）

### 智能API切换和黑名单机制

#### 1. 失败API临时黑名单
- **功能**：当API返回格式错误时，自动加入临时黑名单
- **持续时间**：60秒
- **自动清理**：黑名单记录自动过期和清理
- **效果**：在选择API时自动跳过黑名单中的API

#### 2. 智能切换机制
- **触发条件**：JSON解析失败、格式错误
- **切换方式**：立即切换到下一个API（不等待重试延迟）
- **权重调整**：大幅降低出错API的权重（-50）
- **适用场景**：
  - 上游返回非JSON格式
  - 上游返回空响应
  - 上游返回HTML错误页面

#### 3. 详细的诊断日志
- **上游响应诊断**：
  - 状态码
  - Content-Type
  - 响应长度
  - 响应内容预览
- **错误详情**：
  - JSON解析错误信息
  - 原始响应内容（前500字符）
- **切换过程**：
  - 黑名单添加/移除
  - 权重调整
  - API选择

#### 4. 新增错误类型
- **FormatError**：专门用于格式错误
- **快速处理**：格式错误立即切换，不等待

#### 5. 改进的权重管理
- **自适应调整**：
  - 成功时权重逐渐降低
  - 格式错误时大幅降低（-50）
  - 支持自定义减少量
- **特别权重**：
  - 权重>100时优先使用
  - 使用后自动递减（到50为止）

### 日志示例

```
[诊断] free5 上游响应状态码: 200
[诊断] free5 上游响应Content-Type: text/html
[错误] free5 JSON解析失败: Expecting value: line 1 column 1 (char 0)
[黑名单] free5 已加入临时黑名单 (60秒)
[权重] free5 权重自动减少: 100 -> 50 (减少: 50)
[请求] 格式错误 - 快速切换到下一个 API
[重试] 立即尝试下一个 API...
[选择] 可用 API 数量: 9/10
[请求] 发送到 free1 (尝试 2/3)
[请求] free1 独立服务成功
```

### 优势

1. **快速恢复**：遇到格式错误立即切换，最小化用户等待时间
2. **智能规避**：临时屏蔽不稳定的API，减少重复错误
3. **自适应优化**：根据API表现自动调整权重
4. **易于监控**：详细的日志输出，清晰的切换过程

### 相关文档

- 详细诊断指南：[DEBUG_GUIDE.md](DEBUG_GUIDE.md)
- 快速开始指南：[QUICK_START.md](QUICK_START.md)
- 主文档：[MULTI_FREE_API_README.md](MULTI_FREE_API_README.md)

### 配置调整

如需修改黑名单持续时间，编辑 `app_state.py`：
```python
self.failed_api_blacklist_duration = 60  # 修改为所需的秒数
```

### API端点

新增以下API端点用于管理：
- `/debug/api/weight` - 查看和设置API权重
- `/debug/api/enable` - 启用API
- `/debug/api/disable` - 停用API
- `/debug/api/weight/reset` - 重置所有权重为默认值
