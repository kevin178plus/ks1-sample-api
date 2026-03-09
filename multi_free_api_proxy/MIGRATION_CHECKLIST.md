# 优化版本迁移检查清单

## ✅ 迁移前准备

- [ ] 备份原始文件
  ```bash
  cp multi_free_api_proxy_v3.py multi_free_api_proxy_v3.py.backup
  ```

- [ ] 记录当前配置
  ```bash
  cat .env > .env.backup
  ```

- [ ] 停止现有服务
  ```bash
  # 停止当前运行的服务
  ```

## ✅ 文件检查

- [ ] 确认以下文件已创建：
  - [ ] `config.py` - 配置管理
  - [ ] `app_state.py` - 状态管理
  - [ ] `errors.py` - 错误处理
  - [ ] `multi_free_api_proxy_v3_optimized.py` - 优化版本
  - [ ] `templates/debug.html` - 调试页面
  - [ ] `static/css/debug.css` - 样式文件
  - [ ] `static/js/debug.js` - 脚本文件

- [ ] 验证文件完整性
  ```bash
  ls -la multi_free_api_proxy/
  ```

## ✅ 依赖检查

- [ ] 确认已安装所有依赖
  ```bash
  pip install flask requests watchdog
  ```

- [ ] 检查 Python 版本
  ```bash
  python --version  # 需要 3.7+
  ```

## ✅ 配置检查

- [ ] 检查 `.env` 文件
  ```bash
  cat .env
  ```

- [ ] 验证必要的环境变量
  - [ ] `FREE1_API_KEY` (如果使用)
  - [ ] `FREE2_API_KEY` (如果使用)
  - [ ] `PORT` (默认 5000)
  - [ ] `MAX_CONCURRENT_REQUESTS` (默认 5)

- [ ] 检查 `free_api_test` 目录结构
  ```bash
  ls -la ../free_api_test/
  ```

## ✅ 启动测试

- [ ] 启动优化版本
  ```bash
  python multi_free_api_proxy_v3_optimized.py
  ```

- [ ] 检查启动日志
  ```
  [启动] 多Free API代理服务启动在端口 5000
  [启动] 可用API: X/Y
  ```

- [ ] 验证服务可访问
  ```bash
  curl http://localhost:5000/health
  # 应返回: {"status": "ok"}
  ```

## ✅ 功能测试

### 基础端点测试

- [ ] 健康检查
  ```bash
  curl http://localhost:5000/health
  ```

- [ ] 模型列表
  ```bash
  curl http://localhost:5000/v1/models
  ```

- [ ] 上游检查
  ```bash
  curl http://localhost:5000/health/upstream
  ```

### 调试面板测试

- [ ] 访问调试面板
  ```
  http://localhost:5000/debug
  ```

- [ ] 检查统计信息标签页
  - [ ] 显示总调用次数
  - [ ] 显示成功/失败/超时/重试统计
  - [ ] 自动刷新功能正常

- [ ] 检查 API 状态标签页
  - [ ] 显示所有 API 状态
  - [ ] 显示成功/失败计数

- [ ] 检查聊天测试标签页
  - [ ] 能发送消息
  - [ ] 能接收回复
  - [ ] 显示响应时间

- [ ] 检查 API 管理标签页
  - [ ] 显示所有 API 权重
  - [ ] 能修改权重
  - [ ] 能启用/停用 API
  - [ ] 能重置权重

### API 功能测试

- [ ] 聊天完成端点
  ```bash
  curl -X POST http://localhost:5000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "messages": [{"role": "user", "content": "Hello"}],
      "max_tokens": 100
    }'
  ```

- [ ] 验证响应格式
  ```json
  {
    "choices": [
      {
        "message": {
          "content": "..."
        }
      }
    ]
  }
  ```

## ✅ 性能测试

- [ ] 并发请求测试
  ```bash
  # 发送多个并发请求
  for i in {1..5}; do
    curl -X POST http://localhost:5000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"messages": [{"role": "user", "content": "Test"}]}' &
  done
  wait
  ```

- [ ] 检查并发限制
  - [ ] 活跃请求数不超过配置值
  - [ ] 超出限制时返回 503 错误

- [ ] 检查重试机制
  - [ ] 失败请求自动重试
  - [ ] 重试次数不超过配置值

## ✅ 错误处理测试

- [ ] 测试无效 API 密钥
  ```bash
  # 修改 .env 中的 API_KEY 为无效值
  # 重启服务
  # 验证错误处理
  ```

- [ ] 测试超时处理
  - [ ] 请求超时时返回错误
  - [ ] 自动重试

- [ ] 测试并发限制
  - [ ] 超出并发限制时返回 503

## ✅ 日志检查

- [ ] 检查启动日志
  ```bash
  tail -20 daemon.log
  ```

- [ ] 检查请求日志
  ```bash
  grep "\[请求\]" daemon.log
  ```

- [ ] 检查错误日志
  ```bash
  grep "\[错误\]" daemon.log
  ```

## ✅ 配置验证

- [ ] 验证配置加载
  ```python
  from config import get_config
  config = get_config()
  print(config.MAX_CONCURRENT_REQUESTS)
  ```

- [ ] 验证状态管理
  ```python
  from app_state import AppState
  state = AppState(config)
  print(state.get_active_requests())
  ```

- [ ] 验证错误处理
  ```python
  from errors import ErrorType, TimeoutError
  print(ErrorType.TIMEOUT.value)
  ```

## ✅ 回滚准备

- [ ] 确认备份文件存在
  ```bash
  ls -la multi_free_api_proxy_v3.py.backup
  ```

- [ ] 记录回滚步骤
  ```bash
  # 如需回滚：
  # 1. 停止优化版本
  # 2. cp multi_free_api_proxy_v3.py.backup multi_free_api_proxy_v3.py
  # 3. 重启原始版本
  ```

## ✅ 生产部署前

- [ ] 在测试环境完整测试
- [ ] 性能基准测试通过
- [ ] 所有功能测试通过
- [ ] 错误处理测试通过
- [ ] 日志输出正常
- [ ] 文档已更新
- [ ] 团队成员已培训

## ✅ 部署后监控

- [ ] 监控服务状态
  ```bash
  curl http://localhost:5000/health
  ```

- [ ] 监控 API 可用性
  ```bash
  curl http://localhost:5000/health/upstream
  ```

- [ ] 监控并发请求
  ```bash
  curl http://localhost:5000/debug/concurrency
  ```

- [ ] 监控错误日志
  ```bash
  tail -f daemon.log | grep ERROR
  ```

- [ ] 定期检查调试面板
  ```
  http://localhost:5000/debug
  ```

## 📝 迁移完成

- [ ] 所有检查项已完成
- [ ] 所有测试已通过
- [ ] 文档已更新
- [ ] 团队已通知
- [ ] 监控已启用

**迁移完成时间**: _______________

**迁移负责人**: _______________

**备注**: 
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```
