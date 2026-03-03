package proxy

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/stats"
	"github.com/kevin178plus/api-proxy-go/upstream"
)

// Proxy 代理
type Proxy struct {
	config      *config.Config
	manager     *upstream.Manager
	statsMgr    *stats.StatsManager
	keyStatsMgr *stats.KeyStatsManager
	selector    *upstream.Selector
	httpClient  *http.Client
	mu          sync.RWMutex
}

// NewProxy 创建代理
func NewProxy(cfg *config.Config, manager *upstream.Manager, statsMgr *stats.StatsManager, keyStatsMgr *stats.KeyStatsManager) *Proxy {
	return &Proxy{
		config:      cfg,
		manager:     manager,
		statsMgr:    statsMgr,
		keyStatsMgr: keyStatsMgr,
		selector:    upstream.NewSelector(manager),
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

// ServeHTTP 处理 HTTP 请求
func (p *Proxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// 只允许 localhost 请求
	if !p.isLocalhost(r.RemoteAddr) {
		http.Error(w, "Access denied", http.StatusForbidden)
		return
	}

	// 根据路径路由
	switch {
	case strings.HasPrefix(r.URL.Path, "/v1/chat/completions"):
		p.handleChatCompletions(w, r)
	case strings.HasPrefix(r.URL.Path, "/v1/models"):
		p.handleListModels(w, r)
	case r.URL.Path == "/health":
		p.handleHealth(w, r)
	case strings.HasPrefix(r.URL.Path, "/debug"):
		// 调试端点由 web 模块处理
		http.Error(w, "Debug endpoint not implemented", http.StatusNotImplemented)
	default:
		http.Error(w, "Not found", http.StatusNotFound)
	}
}

// isLocalhost 检查是否来自 localhost
func (p *Proxy) isLocalhost(remoteAddr string) bool {
	// 移除端口号
	host, _, err := net.SplitHostPort(remoteAddr)
	if err != nil {
		host = remoteAddr
	}

	// 检查是否为本地地址
	return host == "127.0.0.1" || host == "::1" || host == "localhost"
}

// handleChatCompletions 处理聊天完成请求
func (p *Proxy) handleChatCompletions(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 读取请求体
	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("[错误] 读取请求体失败: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// 解析请求
	var reqData map[string]interface{}
	if err := json.Unmarshal(body, &reqData); err != nil {
		log.Printf("[错误] 解析请求失败: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	// 获取 API Key（从 Header 或 Query）
	apiKey := p.extractAPIKey(r)

	// 检查授权
	if !p.keyStatsMgr.IsAuthorized(apiKey) {
		log.Printf("[认证] API Key 未授权: %s", apiKey)
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// 检查限额
	if p.keyStatsMgr.IsExceeded(apiKey) {
		log.Printf("[限额] API Key 超过限额: %s", apiKey)
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	// 选择上游并处理请求（支持失效转移）
	result, _, err := p.executeWithFailover(r.Context(), reqData, apiKey)
	if err != nil {
		log.Printf("[错误] 请求失败: %v", err)
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	// 记录 API Key 统计
	p.keyStatsMgr.RecordRequest(apiKey, true)

	// 返回响应
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(result)
}

// executeWithFailover 带失效转移的请求执行
func (p *Proxy) executeWithFailover(ctx context.Context, reqData map[string]interface{}, apiKey string) (map[string]interface{}, string, error) {
	maxRetries := 3
	var lastErr error

	for attempt := 0; attempt < maxRetries; attempt++ {
		// 选择上游
		upstreamName, err := p.selector.Select()
		if err != nil {
			return nil, "", fmt.Errorf("no available upstream: %w", err)
		}

		// 执行请求
		result, err := p.executeRequest(ctx, upstreamName, reqData)
		if err != nil {
			lastErr = err

			// 标记失败
			p.manager.MarkFailure(upstreamName)

			// 检查是否超时
			if isTimeoutError(err) {
				p.manager.MarkTimeout(upstreamName)
			}

			// 记录失败
			log.Printf("[失效转移] %s 失败: %v (尝试 %d/%d)", upstreamName, err, attempt+1, maxRetries)

			// 等待后重试
			if attempt < maxRetries-1 {
				time.Sleep(time.Duration(1<<attempt) * time.Second)
				continue
			}

			continue
		}

		// 标记成功
		p.manager.MarkSuccess(upstreamName)

		// 检查阈值
		p.statsMgr.CheckThresholds(upstreamName)

		// 如果有权重自动减少
		p.manager.DecreaseWeight(upstreamName)

		return result, upstreamName, nil
	}

	return nil, "", fmt.Errorf("all retries failed: %w", lastErr)
}

// executeRequest 执行单个请求
func (p *Proxy) executeRequest(ctx context.Context, upstreamName string, reqData map[string]interface{}) (map[string]interface{}, error) {
	// 获取上游
	upstreamService, exists := p.manager.Get(upstreamName)
	if !exists {
		return nil, fmt.Errorf("upstream not found: %s", upstreamName)
	}

	cfg := upstreamService.Config

	// SDK 模式
	if cfg.UseSDK {
		return p.executeSDKRequest(ctx, upstreamService, reqData)
	}

	// HTTP 模式
	return p.executeHTTPRequest(ctx, upstreamService, reqData)
}

// executeHTTPRequest 执行 HTTP 请求
func (p *Proxy) executeHTTPRequest(ctx context.Context, upstreamService *upstream.Upstream, reqData map[string]interface{}) (map[string]interface{}, error) {
	cfg := upstreamService.Config

	// 选择模型
	model := p.selector.SelectModel(upstreamService.Name)
	if model == "" {
		model = cfg.Model
	}

	// 构建请求 URL
	reqURL := strings.TrimSuffix(cfg.Address, "/") + "/v1/chat/completions"

	// 构建请求体
	requestBody := map[string]interface{}{
		"model":    model,
		"messages": reqData["messages"],
	}

	// 添加可选参数
	if temp, ok := reqData["temperature"].(float64); ok {
		requestBody["temperature"] = temp
	}
	if maxTokens, ok := reqData["max_tokens"].(float64); ok {
		requestBody["max_tokens"] = int(maxTokens)
	} else {
		requestBody["max_tokens"] = cfg.MaxTokens
	}
	if topP, ok := reqData["top_p"].(float64); ok {
		requestBody["top_p"] = topP
	}

	// 序列化请求体
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("marshal request failed: %w", err)
	}

	// 创建请求
	req, err := http.NewRequestWithContext(ctx, "POST", reqURL, bytes.NewReader(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("create request failed: %w", err)
	}

	// 设置请求头
	req.Header.Set("Authorization", "Bearer "+cfg.APIKey)
	req.Header.Set("Content-Type", "application/json")

	// 发送请求
	resp, err := p.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response failed: %w", err)
	}

	// 检查状态码
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("upstream returned status %d: %s", resp.StatusCode, string(respBody))
	}

	// 解析响应
	var result map[string]interface{}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("parse response failed: %w", err)
	}

	// 处理响应内容（根据响应格式配置）
	if cfg.ResponseFormat.ContentFields != nil {
		content, err := upstream.ParseResponseContent(result, &cfg.ResponseFormat)
		if err == nil && content != "" {
			// 更新 content 字段
			if choices, ok := result["choices"].([]interface{}); ok && len(choices) > 0 {
				if choice, ok := choices[0].(map[string]interface{}); ok {
					if message, ok := choice["message"].(map[string]interface{}); ok {
						message["content"] = content
					}
				}
			}
		}
	}

	return result, nil
}

// executeSDKRequest 执行 SDK 请求
func (p *Proxy) executeSDKRequest(ctx context.Context, upstream *upstream.Upstream, reqData map[string]interface{}) (map[string]interface{}, error) {
	// SDK 模式暂未实现，返回错误
	return nil, fmt.Errorf("SDK mode not implemented")
}

// extractAPIKey 提取 API Key
func (p *Proxy) extractAPIKey(r *http.Request) string {
	// 从 Header 中提取
	if auth := r.Header.Get("Authorization"); auth != "" {
		// 移除 "Bearer " 前缀
		if strings.HasPrefix(auth, "Bearer ") {
			return strings.TrimPrefix(auth, "Bearer ")
		}
		return auth
	}

	// 从 Query 参数中提取
	if key := r.URL.Query().Get("api_key"); key != "" {
		return key
	}

	return ""
}

// isTimeoutError 检查是否为超时错误
func isTimeoutError(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(strings.ToLower(err.Error()), "timeout") ||
		   strings.Contains(strings.ToLower(err.Error()), "deadline exceeded")
}

// handleListModels 处理列出模型请求
func (p *Proxy) handleListModels(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 获取模型列表
	modelSelector := upstream.NewModelSelector(p.manager)
	models := modelSelector.ListModels()

	// 构建 OpenAI 格式的响应
	choices := make([]map[string]interface{}, 0, len(models))
	for _, model := range models {
		choices = append(choices, map[string]interface{}{
			"id":      model.ID,
			"object":  "model",
			"owned_by": model.Upstream,
		})
	}

	result := map[string]interface{}{
		"object": "list",
		"data":   choices,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// handleHealth 处理健康检查请求
func (p *Proxy) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	available := p.manager.GetAvailable()
	result := map[string]interface{}{
		"status":            "ok",
		"available_count":   len(available),
		"available_upstreams": available,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}