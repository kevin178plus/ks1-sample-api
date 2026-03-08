@echo off
chcp 65001 >nul
echo ========================================
echo 测试主服务 (端口 5000)
echo ========================================
echo.
echo.

echo [1/4] 测试健康检查...
curl -s http://localhost:5000/health
echo.
echo.

echo [2/4] 测试模型列表...
curl -s http://localhost:5000/v1/models
echo.
echo.

echo [3/4] 测试上游状态...
curl -s http://localhost:5000/health/upstream
echo.
echo.

echo [4/4] 测试聊天完成...
curl -X POST http://localhost:5000/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}"
echo.
echo.

echo ========================================
echo 测试完成
echo ========================================
pause