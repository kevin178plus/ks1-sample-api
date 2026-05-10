package upstream

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/models"
)

// Upstream 上游服务
type Upstream struct {
	Name        string              // 上游名称
	Config      *config.UpstreamConfig // 配置
	Stat        *models.UpstreamStat  // 统计信息
	CurrentWeight int                // 当前权重
	Available   bool                // 是否可用
	LastTestTime time.Time          // 最后测试时间
	LastTestResult string           // 最后测试结果

	mu sync.RWMutex
}

// Manager 上游管理器
type Manager struct {
	upstreams    map[string]*Upstream
	available    []string // 可用上游名称列表
	config       *config.Config
	httpClient   *http.Client
	mu           sync.RWMutex

	// 健康检查
	healthCheckCtx    context.Context
	healthCheckCancel context.CancelFunc
}

// NewManager 创建上游管理器
func NewManager(cfg *config.Config) *Manager {
	ctx, cancel := context.WithCancel(context.Background())

	return &Manager{
		upstreams:         make(map[string]*Upstream),
		available:        make([]string, 0),
		config:           cfg,
		httpClient: &http.Client{
			Timeout: cfg.HealthCheck.Timeout,
			Transport: &http.Transport{
				MaxIdleConns:        10,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		healthCheckCtx:    ctx,
		healthCheckCancel: cancel,
	}
}

// Load 加载上游配置
func (m *Manager) Load() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 扫描上游配置目录
	upstreamConfigs, err := config.DiscoverUpstreams(m.config.Upstreams.RootDir)
	if err != nil {
		return fmt.Errorf("扫描上游配置失败: %w", err)
	}

	// 创建上游服务
	for name, cfg := range upstreamConfigs {
		m.upstreams[name] = &Upstream{
			Name:          name,
			Config:        cfg,
			Stat:          models.NewUpstreamStat(),
			CurrentWeight: cfg.DefaultWeight,
			Available:     false, // 初始状态为不可用，需要测试
		}
	}

	// 更新可用列表（需要在锁外调用）
	return nil
}

// TestAll 测试所有上游
func (m *Manager) TestAll() {
	m.mu.RLock()
	names := make([]string, 0, len(m.upstreams))
	for name, upstream := range m.upstreams {
		if upstream.Config.Enabled {
			names = append(names, name)
		}
	}
	m.mu.RUnlock()

	// 按名称排序，确保测试顺序一致
	sort.Strings(names)

	log.Printf("[上游] 开始测试 %d 个启用的上游服务...", len(names))

	for _, name := range names {
		m.Test(name)
	}

	log.Printf("[上游] 上游测试完成")
}

// Test 测试单个上游
func (m *Manager) Test(name string) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	// 先获取配置信息，避免在持有锁的情况下进行 HTTP 请求
	upstream.mu.RLock()
	config := upstream.Config
	useSDK := config.UseSDK
	upstream.mu.RUnlock()

	if useSDK {
		// SDK 模式，暂时标记为可用（实际测试在调用时进行）
		upstream.mu.Lock()
		upstream.Available = true
		upstream.LastTestTime = time.Now()
		upstream.LastTestResult = "success (SDK mode)"
		upstream.mu.Unlock()
		log.Printf("[上游] %s: SDK 模式，跳过测试", name)
		return
	}

	// HTTP 模式，发送测试请求
	apiURL := strings.TrimSuffix(config.Address, "/") + "/v1/chat/completions"
	log.Printf("[上游] %s: 测试 %s", name, apiURL)
	
	// 创建最小化的测试请求体，使用上游配置的模型名称
	testBody := fmt.Sprintf(`{"model":"%s","messages":[{"role":"user","content":"ping"}],"max_tokens":1}`, config.Model)
	req, err := http.NewRequestWithContext(m.healthCheckCtx, "POST", apiURL, strings.NewReader(testBody))
	if err != nil {
		log.Printf("[上游] %s: 创建请求失败: %v", name, err)
		upstream.mu.Lock()
		upstream.Available = false
		upstream.LastTestTime = time.Now()
		upstream.LastTestResult = fmt.Sprintf("create request failed: %v", err)
		upstream.mu.Unlock()
		return
	}

	req.Header.Set("Authorization", "Bearer "+config.APIKey)
	req.Header.Set("Content-Type", "application/json")

	// OpenRouter 需要 HTTP-Referer 和 X-Title 头
	if strings.Contains(config.Address, "openrouter.ai") {
		req.Header.Set("HTTP-Referer", "http://localhost:5000")
		req.Header.Set("X-Title", "API-Proxy-Go")
	}

	// 选择 HTTP 客户端（根据是否需要代理）
	httpClient := m.httpClient
	if config.UseProxy && m.config.Proxy.HTTPProxy != "" {
		proxyURL, err := url.Parse(m.config.Proxy.HTTPProxy)
		if err != nil {
			log.Printf("[上游] %s: 代理 URL 解析失败: %v", name, err)
		} else {
			transport := &http.Transport{
				Proxy:           http.ProxyURL(proxyURL),
				MaxIdleConns:    10,
				MaxConnsPerHost: 10,
				IdleConnTimeout: 90 * time.Second,
			}
			httpClient = &http.Client{
				Timeout:   m.config.HealthCheck.Timeout,
				Transport: transport,
			}
			log.Printf("[上游] %s: 使用代理 %s", name, m.config.Proxy.HTTPProxy)
		}
	}

	resp, err := httpClient.Do(req)
	if err != nil {
		log.Printf("[上游] %s: 请求失败: %v", name, err)
		upstream.mu.Lock()
		upstream.Available = false
		upstream.LastTestTime = time.Now()
		upstream.LastTestResult = fmt.Sprintf("request failed: %v", err)
		upstream.mu.Unlock()
		return
	}
	defer resp.Body.Close()

	now := time.Now()
	var success bool
	var testResult string
	if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusCreated {
		log.Printf("[上游] %s: 测试成功 (状态码 %d)", name, resp.StatusCode)
		success = true
		testResult = "success"
	} else {
		log.Printf("[上游] %s: 测试失败 - 状态码 %d", name, resp.StatusCode)
		success = false
		testResult = fmt.Sprintf("failed: status %d", resp.StatusCode)
	}

	// 更新上游状态
	upstream.mu.Lock()
	upstream.Available = success
	upstream.LastTestTime = now
	upstream.LastTestResult = testResult
	if success {
		upstream.Stat.RecordRequest(true, false)
	} else {
		upstream.Stat.RecordRequest(false, false)
	}
	upstream.mu.Unlock()

	// 注意：不调用 UpdateAvailable() 更新可用列表
	// 可用列表由健康检查 goroutine 定期更新，避免在 TestAll 遍历中产生锁竞争
}

// Get 获取上游
func (m *Manager) Get(name string) (*Upstream, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	upstream, exists := m.upstreams[name]
	return upstream, exists
}

// GetAll 获取所有上游
func (m *Manager) GetAll() map[string]*Upstream {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string]*Upstream)
	for name, upstream := range m.upstreams {
		result[name] = upstream
	}
	return result
}

// GetAvailable 获取可用上游列表
func (m *Manager) GetAvailable() []string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make([]string, len(m.available))
	copy(result, m.available)
	return result
}

// GetAvailableWithWeights 在同一把锁内原子获取「可用列表 + 各自权重」快照，
// 避免选择算法在迭代过程中读到不一致的状态（P0-3 修复）。
//
// 返回值为副本，调用方可自由修改不影响 Manager 内部状态。
func (m *Manager) GetAvailableWithWeights() ([]string, map[string]int) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	names := make([]string, len(m.available))
	copy(names, m.available)

	weights := make(map[string]int, len(names))
	for _, name := range names {
		up, ok := m.upstreams[name]
		if !ok {
			continue
		}
		up.mu.RLock()
		weights[name] = up.CurrentWeight
		up.mu.RUnlock()
	}
	return names, weights
}

// UpdateAvailable 公开方法，更新可用列表
func (m *Manager) UpdateAvailable() {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 直接实现更新逻辑，不调用updateAvailableList以避免死锁
	m.available = make([]string, 0)
	for name, upstream := range m.upstreams {
		upstream.mu.RLock()
		if upstream.Available && upstream.Config.Enabled {
			m.available = append(m.available, name)
		}
		upstream.mu.RUnlock()
	}

	if len(m.available) > 0 {
		log.Printf("[上游] 可用上游列表: %v", m.available)
	} else {
		log.Printf("[上游] 警告: 没有可用的上游服务")
	}
}

// updateAvailableList 内部方法，更新可用列表（调用者需要持有锁）
func (m *Manager) updateAvailableList() {
	m.available = make([]string, 0)
	for name, upstream := range m.upstreams {
		upstream.mu.RLock()
		if upstream.Available && upstream.Config.Enabled {
			m.available = append(m.available, name)
		}
		upstream.mu.RUnlock()
	}

	if len(m.available) > 0 {
		log.Printf("[上游] 可用上游列表: %v", m.available)
	} else {
		log.Printf("[上游] 警告: 没有可用的上游服务")
	}
}

// MarkFailure 标记失败
func (m *Manager) MarkFailure(name string) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	upstream.Stat.RecordRequest(false, false)

	// 检查是否需要标记为不可用
	_, _, _, consecutive := upstream.Stat.GetStats()
	if consecutive >= m.config.HealthCheck.MaxFailures {
		upstream.mu.Lock()
		upstream.Available = false
		upstream.mu.Unlock()
		m.updateAvailableList()
	}
}

// MarkSuccess 标记成功
func (m *Manager) MarkSuccess(name string) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	upstream.Stat.RecordRequest(true, false)

	// 如果之前不可用，尝试恢复
	upstream.mu.RLock()
	wasUnavailable := !upstream.Available
	upstream.mu.RUnlock()

	if wasUnavailable {
		m.Test(name)
	}
}

// MarkTimeout 标记超时
func (m *Manager) MarkTimeout(name string) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	upstream.Stat.RecordRequest(false, true)
}

// GetWeight 获取权重
func (m *Manager) GetWeight(name string) int {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return 0
	}

	upstream.mu.RLock()
	defer upstream.mu.RUnlock()
	return upstream.CurrentWeight
}

// SetWeight 设置权重
func (m *Manager) SetWeight(name string, weight int) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	upstream.mu.Lock()
	upstream.CurrentWeight = weight
	upstream.mu.Unlock()
}

// DecreaseWeight 减少权重
func (m *Manager) DecreaseWeight(name string) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return
	}

	upstream.mu.Lock()
	if upstream.CurrentWeight > m.config.Weight.MinAutoDecrease {
		upstream.CurrentWeight--
	}
	upstream.mu.Unlock()
}

// StartHealthCheck 启动健康检查
func (m *Manager) StartHealthCheck() {
	if !m.config.HealthCheck.Enabled {
		return
	}

	go func() {
		ticker := time.NewTicker(m.config.HealthCheck.Interval)
		defer ticker.Stop()

		for {
			select {
			case <-m.healthCheckCtx.Done():
				return
			case <-ticker.C:
				m.TestAll()
			}
		}
	}()
}

// Stop 停止管理器
func (m *Manager) Stop() {
	m.healthCheckCancel()
}

// GetStat 获取统计信息
func (m *Manager) GetStat(name string) *models.UpstreamStat {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return nil
	}

	return upstream.Stat
}

// GetUpstreamInfo 获取上游信息（用于调试页面）
func (m *Manager) GetUpstreamInfo(name string) (available bool, model string, weight int, consecutive int, lastTestTime time.Time, exists bool) {
	m.mu.RLock()
	upstream, exists := m.upstreams[name]
	m.mu.RUnlock()

	if !exists {
		return false, "", 0, 0, time.Time{}, false
	}

	upstream.mu.RLock()
	defer upstream.mu.RUnlock()

	stat := upstream.Stat
	var consecutiveFailures int
	if stat != nil {
		_, _, _, consecutiveFailures = stat.GetStats()
	}

	return upstream.Available, upstream.Config.Model, upstream.CurrentWeight, consecutiveFailures, upstream.LastTestTime, true
}

// GetAllUpstreamInfo 批量获取所有上游信息（用于调试页面优化性能）
// 使用RLock读锁获取所有上游的快照信息，允许与健康检查的读锁并发
func (m *Manager) GetAllUpstreamInfo() []map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]map[string]interface{}, 0, len(m.upstreams))

	for name, upstream := range m.upstreams {
		// 外部已持有RLock，可以安全地使用RLock读取upstream数据
		upstream.mu.RLock()
		
		stat := upstream.Stat
		var consecutiveFailures int
		if stat != nil {
			_, _, _, consecutiveFailures = stat.GetStats()
		}

		// 处理最后测试时间
		lastTestTimeStr := "未测试"
		if !upstream.LastTestTime.IsZero() {
			lastTestTimeStr = upstream.LastTestTime.Format("2006-01-02 15:04:05")
		}

		info := map[string]interface{}{
			"name":                 name,
			"available":            upstream.Available,
			"model":                upstream.Config.Model,
			"weight":               upstream.CurrentWeight,
			"consecutive_failures": consecutiveFailures,
			"last_test_time":       lastTestTimeStr,
			"last_test_result":     upstream.LastTestResult,
			"enabled":              upstream.Config.Enabled,
		}
		
		upstream.mu.RUnlock()
		result = append(result, info)
	}

	return result
}