# 夸娥云编程套餐 - 本地 API 代理

OpenAI 兼容的夸娥云编程套餐本地 API 代理

## 系统要求

- PHP 7.4 或更高版本
- PHP 扩展：curl、json

## 安装

1. 克隆本仓库
2. 复制 `.env.example` 为 `.env` 并配置你的 API 密钥
3. 确保已安装 PHP 并可从命令行访问

## 配置

### 环境变量配置 (.env)

在项目根目录创建 `.env` 文件，包含以下变量：

```properties
# 数据库配置（预留）
DB_HOST=localhost
DB_PORT=3306
DB_USER=ai01adm
DB_PASSWORD=ai01pw
DB_NAME=ks1api
DB_CHARSET=utf8mb4

# 夸娥云 API 密钥
kuaecloud_coding_plan=your_api_key_here
```

### 备选配置方式 (api-key.ini)

为保持向后兼容，你也可以使用 `api-key.ini`：

```ini
[key]
kuaecloud-coding_plan=your_api_key_here
```

注意：`.env` 文件的优先级高于 `api-key.ini`。

## 使用方法

### 启动服务器

**Windows:**
```batch
php -S localhost:12680 kuaecloud-api.php
```

或使用提供的批处理文件：
```batch
一键启动.bat
```

**Linux/Mac:**
```bash
php -S localhost:12680 kuaecloud-api.php
```

### API 端点

基础 URL: `http://localhost:12680/v1`

### 请求示例

```bash
curl -X POST http://localhost:12680/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "model": "GLM-4.7",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### Python 示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_api_key",
    base_url="http://localhost:12680/v1"
)

response = client.chat.completions.create(
    model="GLM-4.7",
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)
```

## 支持的工具

本 API 代理兼容以下 AI 编程工具：

### Claude Code (Anthropic 协议)
- 基础 URL: `https://coding-plan-endpoint.kuaecloud.net`
- 模型: `GLM-4.7`

### Cline、Cursor、Kilo Code、Roo Code、OpenCode (OpenAI 协议)
- 基础 URL: `https://coding-plan-endpoint.kuaecloud.net/v1`
- 模型: `GLM-4.7`

### 本地代理配置
本地开发环境使用：
- 基础 URL: `http://localhost:12680/v1`
- API 密钥: 从 `.env` 中配置的密钥

## 测试

在浏览器中打开 `index.html` 或 `test-api.html` 进行 API 测试。

### index.html 功能
- 服务器启动说明
- 快速测试界面
- 各工具配置指南
- curl 和 Python 示例命令

### test-api.html 功能
- 简化的测试界面
- 直接 API 测试

## 调试模式

通过设置 `DEBUG` 环境变量启用调试日志：

```bash
# Linux/Mac
export DEBUG=true

# Windows CMD
set DEBUG=true

# Windows PowerShell
$env:DEBUG="true"
```

调试日志将写入 `api.log` 文件。

## API 参考

### 聊天补全

**端点:** `POST /v1/chat/completions`

**请求头:**
- `Content-Type: application/json`
- `Authorization: Bearer {api_key}`

**请求体:**
```json
{
  "model": "GLM-4.7",
  "messages": [
    {
      "role": "user",
      "content": "你的消息"
    }
  ],
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**响应:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "响应内容"
      }
    }
  ]
}
```

## 错误处理

API 返回标准 HTTP 状态码：

- `200` - 成功
- `400` - 错误的请求（无效的 JSON、缺少字段）
- `401` - 未授权（无效的 API 密钥）
- `405` - 方法不允许（非 POST 请求）
- `500` - 服务器内部错误（API 请求失败）

错误响应格式：
```json
{
  "error": {
    "message": "错误描述",
    "type": "error_code",
    "param": null
  }
}
```

## 故障排除

### 常见问题

1. **服务器无法启动**
   - 确保已安装 PHP 并在 PATH 环境变量中
   - 检查端口 12680 是否已被占用

2. **API 密钥错误**
   - 验证 `.env` 或 `api-key.ini` 中的 API 密钥
   - 检查文件权限

3. **连接错误**
   - 确保服务器正在运行
   - 检查防火墙设置
   - 验证客户端配置中的基础 URL

## 许可证

本项目按原样提供，用于夸娥云编程套餐。

## 支持

有关夸娥云服务的问题，请参考官方文档：
https://docs.mthreads.com/kuaecloud/kuaecloud-doc-online/coding_plan/tools_config
