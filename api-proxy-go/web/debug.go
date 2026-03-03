package web

import (
	"encoding/json"
	"net/http"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/logger"
	"github.com/kevin178plus/api-proxy-go/stats"
	"github.com/kevin178plus/api-proxy-go/upstream"
)

// DebugHandler 调试页面处理器
type DebugHandler struct {
	config      *config.Config
	manager     *upstream.Manager
	statsMgr    *stats.StatsManager
	keyStatsMgr *stats.KeyStatsManager
	logger      *logger.Logger
}

// NewDebugHandler 创建调试页面处理器
func NewDebugHandler(cfg *config.Config, manager *upstream.Manager, statsMgr *stats.StatsManager, keyStatsMgr *stats.KeyStatsManager) *DebugHandler {
	return &DebugHandler{
		config:      cfg,
		manager:     manager,
		statsMgr:    statsMgr,
		keyStatsMgr: keyStatsMgr,
		logger:      logger.NewLogger(),
	}
}

// RegisterRoutes 注册路由
func (dh *DebugHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/debug", dh.handleDebugPage)
	mux.HandleFunc("/debug/stats", dh.handleStats)
	mux.HandleFunc("/debug/apis", dh.handleAPIs)
	mux.HandleFunc("/debug/concurrency", dh.handleConcurrency)
}

// handleDebugPage 处理调试页面
func (dh *DebugHandler) handleDebugPage(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 检查是否启用调试模式
	if !dh.config.Debug.Enabled {
		http.Error(w, "Debug mode not enabled", http.StatusForbidden)
		return
	}

	// 简单的 HTML 页面，使用 JavaScript 异步加载数据
	html := `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>API 代理调试面板</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1, h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .stats { background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stat-item { margin: 10px 0; font-size: 16px; }
        .stat-label { font-weight: bold; color: #333; }
        .stat-value { color: #007bff; font-size: 24px; font-weight: bold; }
        .api-list { list-style: none; padding: 0; }
        .api-item { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .api-item.available { border-left-color: #28a745; }
        .api-item.unavailable { border-left-color: #dc3545; }
        .refresh-btn { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .timestamp { color: #666; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>API 代理调试面板</h1>
        <p>最后更新: <span id="timestamp">加载中...</span></p>
        <button class="refresh-btn" onclick="location.reload()">刷新</button>
    </div>
    <div id="content"><div class="loading"><p>加载数据中，请稍候...</p></div></div>
    <script>
        async function loadData() {
            try {
                document.getElementById('timestamp').textContent = new Date().toLocaleString('zh-CN');
                const statsResponse = await fetch('/debug/stats');
                const statsData = await statsResponse.json();
                let totalCalls = 0, successCount = 0, failureCount = 0, timeoutCount = 0;
                for (const key in statsData) {
                    const value = statsData[key];
                    if (typeof value === 'object' && value !== null) {
                        totalCalls += (value.success_count || 0) + (value.failure_count || 0) + (value.timeout_count || 0);
                        successCount += value.success_count || 0;
                        failureCount += value.failure_count || 0;
                        timeoutCount += value.timeout_count || 0;
                    }
                }
                const statsHtml = '<div class="container"><h2>统计信息</h2><div class="stats">' +
                    '<div class="stat-item"><span class="stat-label">总调用次数:</span><span class="stat-value">' + totalCalls + '</span></div>' +
                    '<div class="stat-item"><span class="stat-label">成功次数:</span><span class="stat-value">' + successCount + '</span></div>' +
                    '<div class="stat-item"><span class="stat-label">失败次数:</span><span class="stat-value">' + failureCount + '</span></div>' +
                    '<div class="stat-item"><span class="stat-label">超时次数:</span><span class="stat-value">' + timeoutCount + '</span></div></div></div>';
                let apisHtml = '<div class="container"><h2>API 状态</h2><p><em>API 列表加载中...</em></p></div>';
                try {
                    const apisResponse = await Promise.race([fetch('/debug/apis'), new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 10000))]);
                    if (apisResponse.ok) {
                        const apisData = await apisResponse.json();
                        const apiListHtml = apisData.map(api => 
                            '<li class="api-item ' + (api.available ? 'available' : 'unavailable') + '">' +
                            '<strong>' + api.name + '</strong>' +
                            (api.available ? '<span style="color: green;">● 可用</span>' : '<span style="color: red;">● 不可用</span>') +
                            '<div>模型: ' + (api.model || 'N/A') + '</div>' +
                            '<div>权重: ' + (api.weight || 0) + '</div>' +
                            '<div>连续失败: ' + (api.consecutive_failures || 0) + '</div>' +
                            '<div class="timestamp">最后测试: ' + (api.last_test_time || 'N/A') + '</div></li>'
                        ).join('');
                        apisHtml = '<div class="container"><h2>API 状态</h2><ul class="api-list">' + apiListHtml + '</ul></div>';
                    }
                } catch (e) {
                    apisHtml = '<div class="container"><h2>API 状态</h2><p><em>API 列表加载超时，请稍后刷新</em></p></div>';
                }
                document.getElementById('content').innerHTML = statsHtml + apisHtml;
            } catch (error) {
                document.getElementById('content').innerHTML = '<div class="container"><p style="color: red;">加载数据失败: ' + error.message + '</p></div>';
            }
        }
        loadData();
    </script>
</body>
</html>`

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(html))
}

// APIInfo API 信息
type APIInfo struct {
	Name               string `json:"name"`
	Available          bool   `json:"available"`
	Model              string `json:"model"`
	Weight             int    `json:"weight"`
	ConsecutiveFailures int   `json:"consecutive_failures"`
	LastTestTime       string `json:"last_test_time"`
}

// getAPIInfoList 获取 API 信息列表
func (dh *DebugHandler) getAPIInfoList() []APIInfo {
	apis := make([]APIInfo, 0)
	upstreams := dh.manager.GetAll()
	for name := range upstreams {
		available, model, weight, consecutive, lastTestTime, exists := dh.manager.GetUpstreamInfo(name)
		if !exists {
			continue
		}
		apis = append(apis, APIInfo{
			Name:               name,
			Available:          available,
			Model:              model,
			Weight:             weight,
			ConsecutiveFailures: consecutive,
			LastTestTime:       lastTestTime.Format("2006-01-02 15:04:05"),
		})
	}
	return apis
}

// handleStats 处理统计 API
func (dh *DebugHandler) handleStats(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !dh.config.Debug.Enabled {
		http.Error(w, "Debug mode not enabled", http.StatusForbidden)
		return
	}
	stats := dh.statsMgr.GetAllStats()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// handleAPIs 处理 API 列表
func (dh *DebugHandler) handleAPIs(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !dh.config.Debug.Enabled {
		http.Error(w, "Debug mode not enabled", http.StatusForbidden)
		return
	}
	
	// 使用批量获取方法优化性能
	apis := dh.manager.GetAllUpstreamInfo()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(apis)
}

// handleConcurrency 处理并发状态
func (dh *DebugHandler) handleConcurrency(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !dh.config.Debug.Enabled {
		http.Error(w, "Debug mode not enabled", http.StatusForbidden)
		return
	}
	
	// 返回并发状态
	result := map[string]interface{}{
		"active_requests": 0,
		"available_slots": 5,
		"max_concurrent": 5,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}