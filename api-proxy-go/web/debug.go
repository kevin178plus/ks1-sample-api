package web

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

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
	healthStatus string // 健康检查状态: "checking", "disabled", "enabled"
}

// NewDebugHandler 创建调试页面处理器
func NewDebugHandler(cfg *config.Config, manager *upstream.Manager, statsMgr *stats.StatsManager, keyStatsMgr *stats.KeyStatsManager) *DebugHandler {
	h := &DebugHandler{
		config:      cfg,
		manager:     manager,
		statsMgr:    statsMgr,
		keyStatsMgr: keyStatsMgr,
		logger:      logger.NewLogger(),
		healthStatus: "disabled",
	}
	
	// 设置健康检查状态
	if cfg.HealthCheck.Enabled {
		h.healthStatus = "enabled"
	}
	
	return h
}

// RegisterRoutes 注册路由
func (dh *DebugHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/debug", dh.handleDebugPage)
	mux.HandleFunc("/debug/stats", dh.handleStats)
	mux.HandleFunc("/debug/apis", dh.handleAPIs)
	mux.HandleFunc("/debug/concurrency", dh.handleConcurrency)
	mux.HandleFunc("/debug/api/test/", dh.handleTestSingle)
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

	// 获取健康检查配置信息（用于前端显示）
	healthEnabled := dh.config.HealthCheck.Enabled
	healthInterval := dh.config.HealthCheck.Interval.String()
	healthTimeout := dh.config.HealthCheck.Timeout.String()

	// 简单的 HTML 页面，使用 JavaScript 异步加载数据
	html := `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>API 代理调试面板</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: Arial, sans-serif; max-width: 1400px; margin: 20px auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1, h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .stats { background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stat-item { margin: 10px 0; font-size: 16px; }
        .stat-label { font-weight: bold; color: #333; }
        .stat-value { color: #007bff; font-size: 24px; font-weight: bold; }
        .refresh-btn { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .refresh-btn:hover { background-color: #0056b3; }
        .refresh-btn:disabled { background-color: #ccc; cursor: not-allowed; }
        .timestamp { color: #666; font-size: 12px; margin-top: 10px; }
        .health-status { padding: 10px 15px; border-radius: 5px; margin: 10px 0; font-size: 14px; }
        .health-status.enabled { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .health-status.disabled { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
        .tabs { display: flex; border-bottom: 2px solid #e7f3ff; margin-bottom: 20px; flex-wrap: wrap; gap: 5px; }
        .tab { padding: 10px 20px; cursor: pointer; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; }
        .tab.active { color: #007bff; border-bottom-color: #007bff; font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .api-grid { display: flex; flex-wrap: wrap; gap: 15px; }
        .api-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            min-width: 300px;
            max-width: 400px;
            max-height: 586px;
            overflow-y: auto;
            flex: 1;
        }
        .api-card.available { border-left-color: #28a745; }
        .api-card.unavailable { border-left-color: #dc3545; }
        .api-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .api-card-title { font-size: 16px; font-weight: bold; }
        .api-card-status { font-size: 14px; font-weight: bold; }
        .api-card-status.available { color: #28a745; }
        .api-card-status.unavailable { color: #dc3545; }
        .api-card-info { font-size: 13px; color: #555; line-height: 1.6; }
        .api-card-info div { margin: 4px 0; }
        .api-card-actions { margin-top: 12px; padding-top: 10px; border-top: 1px solid #ddd; display: flex; gap: 8px; }
        .test-btn { background-color: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 13px; }
        .test-btn:hover { background-color: #218838; }
        .test-btn:disabled { background-color: #ccc; cursor: not-allowed; }
        .test-btn.testing { background-color: #ffc107; }
        .sub-tabs { display: flex; gap: 10px; margin-bottom: 15px; }
        .sub-tab { padding: 8px 16px; cursor: pointer; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa; }
        .sub-tab.active { background: #007bff; color: white; border-color: #007bff; }
        .sub-tab-count { margin-left: 5px; padding: 2px 6px; border-radius: 10px; font-size: 12px; }
        .sub-tab.active .sub-tab-count { background: rgba(255,255,255,0.3); }
        .sub-tab:not(.active) .sub-tab-count { background: #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <h1>API 代理调试面板</h1>
        <p>最后更新: <span id="timestamp">加载中...</span></p>
        <div id="healthStatus" class="health-status disabled">健康检查配置: 加载中...</div>
        <button class="refresh-btn" onclick="location.reload()">刷新</button>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="showTab('stats')">统计信息</div>
        <div class="tab" onclick="showTab('apis')">API 状态</div>
    </div>

    <div id="tab-stats" class="tab-content active">
        <div id="content-stats"><div class="loading"><p>加载数据中，请稍候...</p></div></div>
    </div>

    <div id="tab-apis" class="tab-content">
        <div class="sub-tabs">
            <div class="sub-tab active" id="subTabAvailable" onclick="showSubTab('available')">
                可用 <span class="sub-tab-count" id="availableCount">0</span>
            </div>
            <div class="sub-tab" id="subTabUnavailable" onclick="showSubTab('unavailable')">
                不可用 <span class="sub-tab-count" id="unavailableCount">0</span>
            </div>
        </div>
        <div id="content-apis-available"></div>
        <div id="content-apis-unavailable" style="display:none;"></div>
    </div>
    
    <script>
        // 健康检查配置
        const healthEnabled = ` + strconv.FormatBool(healthEnabled) + `;
        const healthInterval = "` + healthInterval + `";
        const healthTimeout = "` + healthTimeout + `";
        
        // 更新健康检查状态显示
        function updateHealthStatus() {
            const healthEl = document.getElementById('healthStatus');
            if (healthEnabled) {
                healthEl.className = 'health-status enabled';
                healthEl.innerHTML = '<strong>健康检查已启用</strong> | 检查间隔: ' + healthInterval + ' | 超时: ' + healthTimeout;
            } else {
                healthEl.className = 'health-status disabled';
                healthEl.innerHTML = '<strong>健康检查已禁用</strong> | API 可用性将在首次请求时自动检测';
            }
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector('.tab[onclick*="' + tabName + '"]').classList.add('active');
            document.getElementById('tab-' + tabName).classList.add('active');
        }

        let currentApiData = [];
        let currentSubTab = 'available';

        function showSubTab(tabName) {
            currentSubTab = tabName;
            document.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
            document.getElementById('subTab' + tabName.charAt(0).toUpperCase() + tabName.slice(1)).classList.add('active');

            if (tabName === 'available') {
                document.getElementById('content-apis-available').style.display = 'flex';
                document.getElementById('content-apis-unavailable').style.display = 'none';
            } else {
                document.getElementById('content-apis-available').style.display = 'none';
                document.getElementById('content-apis-unavailable').style.display = 'flex';
            }
        }

        function testApi(apiName, btn) {
            btn.disabled = true;
            btn.textContent = '测试中...';
            btn.classList.add('testing');

            // 发送测试请求
            fetch('/debug/api/test/' + apiName, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    // 重新加载 API 列表
                    loadAPIs();
                })
                .catch(err => {
                    alert('测试失败: ' + err);
                    btn.disabled = false;
                    btn.textContent = '重新测试';
                    btn.classList.remove('testing');
                });
        }

        function createApiCard(api) {
            const statusClass = api.available ? 'available' : 'unavailable';
            const statusText = api.available ? '● 可用' : '● 不可用';
            return '<div class="api-card ' + statusClass + '">' +
                '<div class="api-card-header">' +
                '<span class="api-card-title">' + api.name + '</span>' +
                '<span class="api-card-status ' + statusClass + '">' + statusText + '</span>' +
                '</div>' +
                '<div class="api-card-info">' +
                '<div><strong>模型:</strong> ' + (api.model || 'N/A') + '</div>' +
                '<div><strong>权重:</strong> ' + (api.weight || 0) + '</div>' +
                '<div><strong>连续失败:</strong> ' + (api.consecutive_failures || 0) + '</div>' +
                '<div><strong>最后测试:</strong> ' + (api.last_test_time || '未测试') + '</div>' +
                '<div><strong>测试结果:</strong> ' + (api.last_test_result || 'N/A') + '</div>' +
                '</div>' +
                '<div class="api-card-actions">' +
                '<button class="test-btn" onclick="testApi(\'' + api.name + '\', this)">重新测试</button>' +
                '</div>' +
                '</div>';
        }
        
        async function loadStats() {
            try {
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
                document.getElementById('content-stats').innerHTML = statsHtml;
            } catch (error) {
                document.getElementById('content-stats').innerHTML = '<div class="container"><p style="color: red;">加载统计失败: ' + error.message + '</p></div>';
            }
        }
        
        async function loadAPIs() {
            try {
                // 显示加载中状态
                document.getElementById('content-apis-available').innerHTML = '<p class="loading">加载 API 状态中，请稍候...</p>';
                document.getElementById('content-apis-unavailable').innerHTML = '<p class="loading">加载 API 状态中，请稍候...</p>';

                // 缩短超时时间到 10 秒，避免长时间等待
                const apisResponse = await Promise.race([
                    fetch('/debug/apis'),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout (10s)')), 10000))
                ]);
                if (apisResponse.ok) {
                    const apisData = await apisResponse.json();
                    currentApiData = apisData;

                    if (apisData.length === 0) {
                        document.getElementById('content-apis-available').innerHTML = '<p>暂无 API 配置</p>';
                        return;
                    }

                    // 分离可用和不可用 API，并排序
                    const availableApis = apisData
                        .filter(api => api.available)
                        .sort((a, b) => (b.weight || 0) - (a.weight || 0)); // 按权重降序
                    const unavailableApis = apisData
                        .filter(api => !api.available)
                        .sort((a, b) => a.name.localeCompare(b.name)); // 按名称升序

                    // 更新计数
                    document.getElementById('availableCount').textContent = availableApis.length;
                    document.getElementById('unavailableCount').textContent = unavailableApis.length;

                    // 渲染可用 API
                    document.getElementById('content-apis-available').innerHTML =
                        '<div class="api-grid">' + availableApis.map(createApiCard).join('') + '</div>';

                    // 渲染不可用 API
                    document.getElementById('content-apis-unavailable').innerHTML =
                        '<div class="api-grid">' + unavailableApis.map(createApiCard).join('') + '</div>';

                    // 确保当前子标签显示正确
                    showSubTab(currentSubTab);
                }
            } catch (e) {
                document.getElementById('content-apis-available').innerHTML = '<p style="color: red;">API 列表加载超时 (' + e.message + ')，请稍后刷新</p>';
                document.getElementById('content-apis-unavailable').innerHTML = '<p style="color: red;">API 列表加载超时 (' + e.message + ')，请稍后刷新</p>';
            }
        }
        
        // 初始化
        document.getElementById('timestamp').textContent = new Date().toLocaleString('zh-CN');
        updateHealthStatus();
        loadStats();
        loadAPIs();
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

// handleTestSingle 测试单个 API
func (dh *DebugHandler) handleTestSingle(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !dh.config.Debug.Enabled {
		http.Error(w, "Debug mode not enabled", http.StatusForbidden)
		return
	}

	// 从 URL 路径提取 API 名称：/debug/api/test/free1
	path := r.URL.Path
	apiName := strings.TrimPrefix(path, "/debug/api/test/")
	if apiName == "" {
		http.Error(w, "API name required", http.StatusBadRequest)
		return
	}

	// 调用上游管理器的测试方法
	result := dh.manager.Test(apiName)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": result,
		"name":    apiName,
	})
}