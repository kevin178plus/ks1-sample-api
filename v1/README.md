# KUAE Cloud Coding Plan - Local API Proxy

OpenAI Compatible Local API Proxy for KUAE Cloud Coding Plan

## Requirements

- PHP 7.4 or higher
- PHP extensions: curl, json

## Installation

1. Clone this repository
2. Copy `.env.example` to `.env` and configure your API key
3. Ensure PHP is installed and accessible from command line

## Configuration

### Environment Variables (.env)

Create a `.env` file in the project root with the following variables:

```properties
# Database Configuration (for future use)
DB_HOST=localhost
DB_PORT=3306
DB_USER=ai01adm
DB_PASSWORD=ai01pw
DB_NAME=ks1api
DB_CHARSET=utf8mb4

# KUAE Cloud API Key
kuaecloud_coding_plan=your_api_key_here
```

### Alternative Configuration (api-key.ini)

For backward compatibility, you can also use `api-key.ini`:

```ini
[key]
kuaecloud-coding_plan=your_api_key_here
```

Note: The `.env` file takes priority over `api-key.ini`.

## Usage

### Starting the Server

**Windows:**
```batch
php -S localhost:12680 kuaecloud-api.php
```

Or use the provided batch file:
```batch
一键启动.bat
```

**Linux/Mac:**
```bash
php -S localhost:12680 kuaecloud-api.php
```

### API Endpoint

Base URL: `http://localhost:12680/v1`

### Example Request

```bash
curl -X POST http://localhost:12680/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "model": "GLM-4.7",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Python Example

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_api_key",
    base_url="http://localhost:12680/v1"
)

response = client.chat.completions.create(
    model="GLM-4.7",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

## Supported Tools

This API proxy is compatible with the following AI coding tools:

### Claude Code (Anthropic Protocol)
- Base URL: `https://coding-plan-endpoint.kuaecloud.net`
- Model: `GLM-4.7`

### Cline, Cursor, Kilo Code, Roo Code, OpenCode (OpenAI Protocol)
- Base URL: `https://coding-plan-endpoint.kuaecloud.net/v1`
- Model: `GLM-4.7`

### Local Proxy Configuration
For local development, use:
- Base URL: `http://localhost:12680/v1`
- API Key: Your configured key from `.env`

## Testing

Open `index.html` or `test-api.html` in your browser to test the API.

### index.html Features
- Server startup instructions
- Quick test interface
- Configuration guide for various tools
- Example commands for curl and Python

### test-api.html Features
- Simplified test interface
- Direct API testing

## Debug Mode

Enable debug logging by setting the `DEBUG` environment variable:

```bash
# Linux/Mac
export DEBUG=true

# Windows CMD
set DEBUG=true

# Windows PowerShell
$env:DEBUG="true"
```

Debug logs will be written to `api.log`.

## API Reference

### Chat Completions

**Endpoint:** `POST /v1/chat/completions`

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {api_key}`

**Request Body:**
```json
{
  "model": "GLM-4.7",
  "messages": [
    {
      "role": "user",
      "content": "Your message here"
    }
  ],
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Response content"
      }
    }
  ]
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid JSON, missing fields)
- `401` - Unauthorized (invalid API key)
- `405` - Method Not Allowed (non-POST requests)
- `500` - Internal Server Error (API request failed)

Error response format:
```json
{
  "error": {
    "message": "Error description",
    "type": "error_code",
    "param": null
  }
}
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Ensure PHP is installed and in your PATH
   - Check that port 12680 is not already in use

2. **API key errors**
   - Verify your API key in `.env` or `api-key.ini`
   - Check file permissions

3. **Connection errors**
   - Ensure the server is running
   - Check firewall settings
   - Verify the base URL in your client configuration

## License

This project is provided as-is for use with KUAE Cloud Coding Plan.

## Support

For issues related to KUAE Cloud services, please refer to the official documentation at:
https://docs.mthreads.com/kuaecloud/kuaecloud-doc-online/coding_plan/tools_config
