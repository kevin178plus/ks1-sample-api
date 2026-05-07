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
	failover    *FailoverHandler
	httpClient  *http.Client
	mu          sync.RWMutex
}

// NewProxy 创建代理
func NewProxy(cfg *config.Config, manager *upstream.Manager, statsMgr *stats.StatsManager, keyStatsMgr *stats.KeyStatsManager) *Proxy {
	selector := upstream.NewSelector(manager)
	backoff := time.Duration(cfg.Proxy.RetryBackoffBaseMS) * time.Millisecond
	return &Proxy{
		config:      cfg,
		manager:     manager,
		statsMgr:    statsMgr,
		keyStatsMgr: keyStatsMgr,
		selector:    selector,
		failover:    NewFailoverHandler(manager, selector, cfg.Proxy.MaxRetries, backoff),
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
	// 只允许来自 localhost 的客户端访问
	// 若部署在反向代理之后，可在 config.proxy.trusted_proxies 配置代理 IP/CIDR，
	// 命中后再信任 XFF/X-Real-IP 中的客户端地址（P0-5）。
	if !p.isClientLocalhost(r) {
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

// isClientLocalhost 判断客户端是否为 localhost。
//
// 规则（P0-5 修复）：
//  1. peer = SplitHostPort(RemoteAddr)。
//  2. 若 peer 本身就是 localhost → 允许。
//  3. 否则当且仅当 peer 命中 trusted_proxies 时，再解析
//     X-Forwarded-For（取最左侧，即原始客户端）/ X-Real-IP，
//     若解析出的客户端 IP 是 localhost 才允许。
//  4. 默认 trusted_proxies 为空 → 不信任任何代理头，等同旧行为。
func (p *Proxy) isClientLocalhost(r *http.Request) bool {
	peer := splitHostNoPort(r.RemoteAddr)
	if isLocalIP(peer) {
		return true
	}
	if !p.isTrustedProxy(peer) {
		return false
	}
	// peer 是可信代理，尝试从代理头解析真实客户端
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// XFF 链：client, proxy1, proxy2, ... — 最左侧是原始客户端
		first := xff
		if idx := strings.Index(xff, ","); idx != -1 {
			first = xff[:idx]
		}
		if isLocalIP(strings.TrimSpace(first)) {
			return true
		}
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		if isLocalIP(strings.TrimSpace(xri)) {
			return true
		}
	}
	return false
}

// isTrustedProxy 判断给定 IP 是否在 trusted_proxies 配置中（支持精确 IP 与 CIDR）
func (p *Proxy) isTrustedProxy(ip string) bool {
	if ip == "" || p.config == nil {
		return false
	}
	parsed := net.ParseIP(ip)
	if parsed == nil {
		return false
	}
	for _, entry := range p.config.Proxy.TrustedProxies {
		entry = strings.TrimSpace(entry)
		if entry == "" {
			continue
		}
		// CIDR 形式
		if strings.Contains(entry, "/") {
			_, cidr, err := net.ParseCIDR(entry)
			if err == nil && cidr.Contains(parsed) {
				return true
			}
			continue
		}
		// 精确 IP
		if net.ParseIP(entry).Equal(parsed) {
			return true
		}
	}
	return false
}

// splitHostNoPort 提取 host 部分（无端口），失败时返回原值
func splitHostNoPort(addr string) string {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		return addr
	}
	return host
}

// isLocalIP 判断是否为 localhost 名称或环回地址
func isLocalIP(host string) bool {
	if host == "localhost" {
		return true
	}
	ip := net.ParseIP(host)
	if ip == nil {
		return false
	}
	return ip.IsLoopback()
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

// executeWithFailover 带失效转移的请求执行（thin wrapper，逻辑下沉到 FailoverHandler）。
func (p *Proxy) executeWithFailover(ctx context.Context, reqData map[string]interface{}, apiKey string) (map[string]interface{}, string, error) {
	result, upstreamName, err := p.failover.Execute(ctx, func(name string) (map[string]interface{}, error) {
		return p.executeRequest(ctx, name, reqData)
	})
	if err != nil {
		return nil, "", err
	}

	// 成功后续动作（仅在最终成功时执行）
	p.statsMgr.CheckThresholds(upstreamName)
	p.manager.DecreaseWeight(upstreamName)
	return result, upstreamName, nil
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
		return nil, fmt.Errorf("parse response failed: %w (response: %s)", err, string(respBody[:minInt(len(respBody), 500)]))
	}

	// 检查响应是否包含错误
	if errMsg, hasError := result["error"]; hasError {
		errStr := ""
		if errMap, ok := errMsg.(map[string]interface{}); ok {
			if msg, ok := errMap["message"].(string); ok {
				errStr = msg
			}
		}
		return nil, fmt.Errorf("upstream returned error: %s", errStr)
	}

	// 验证响应格式（与Python版本的validate_response类似）
	content, err := upstream.ParseResponseContent(result, &cfg.ResponseFormat)
	if err != nil {
		return nil, fmt.Errorf("invalid response format: %w (result: %s)", err, string(respBody[:minInt(len(respBody), 500)]))
	}

	// 如果解析后content为空，说明响应没有有效内容
	if content == "" || content == "{}" {
		return nil, fmt.Errorf("empty response content")
	}

	// 处理响应内容（根据响应格式配置）
	if cfg.ResponseFormat.ContentFields != nil && content != "" {
		// 更新 content 字段
		if choices, ok := result["choices"].([]interface{}); ok && len(choices) > 0 {
			if choice, ok := choices[0].(map[string]interface{}); ok {
				if message, ok := choice["message"].(map[string]interface{}); ok {
					message["content"] = content
				}
			}
		}
	}

	return result, nil
}

// executeSDKRequest 执行 SDK 请求
//
// 注：SDK 模式尚未实现。配置加载阶段已将 use_sdk 强制降级为 HTTP（见
// config.DiscoverUpstreams），正常情况下此函数不应被调用；保留作为
// 防御性兜底。
func (p *Proxy) executeSDKRequest(ctx context.Context, upstream *upstream.Upstream, reqData map[string]interface{}) (map[string]interface{}, error) {
	return nil, fmt.Errorf("SDK mode not implemented (upstream=%s)", upstream.Name)
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

// minInt 返回两个 int 中较小者。
// 显式实现，避免与 Go 1.21+ 内置 min 在不同工具链下行为差异，
// 也防止包内引入同名变量时被遮蔽。
func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
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