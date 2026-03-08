@echo off
chcp 65001 >nul
echo ========================================
echo 测试 Free8 服务 (端口 5008)
echo ========================================
echo.

echo [1/4] 测试健康检查...
curl -s http://localhost:5008/health
echo.
echo.

echo [2/4] 测试模型列表...
curl -s http://localhost:5008/v1/models
echo.
echo.

echo [3/4] 测试统计信息...
curl -s http://localhost:5008/v1/stats
echo.
echo.

echo [4/4] 测试聊天完成...
curl -X POST http://localhost:5008/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}"
echo.
echo.

echo ========================================
echo 测试完成
echo ========================================
pause