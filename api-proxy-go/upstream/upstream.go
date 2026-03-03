package upstream

import (
	"context"
	"fmt"
	"log"
	"net/http"
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
	url := strings.TrimSuffix(config.Address, "/") + "/v1/chat/completions"
	log.Printf("[上游] %s: 测试 %s", name, url)
	
	// 创建最小化的测试请求体，使用上游配置的模型名称
	testBody := fmt.Sprintf(`{"model":"%s","messages":[{"role":"user","content":"ping"}],"max_tokens":1}`, config.Model)
	req, err := http.NewRequestWithContext(m.healthCheckCtx, "POST", url, strings.NewReader(testBody))
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

	resp, err := m.httpClient.Do(req)
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

	// 更新可用列表
	log.Printf("[上游] %s: 调用 updateAvailableList", name)
	m.updateAvailableList()
	log.Printf("[上游] %s: updateAvailableList 完成", name)
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
func (m *Manager) GetAllUpstreamInfo() []map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]map[string]interface{}, 0, len(m.upstreams))

	for name, upstream := range m.upstreams {
		upstream.mu.RLock()
		
		stat := upstream.Stat
		var consecutiveFailures int
		if stat != nil {
			_, _, _, consecutiveFailures = stat.GetStats()
		}

		info := map[string]interface{}{
			"name":                name,
			"available":           upstream.Available,
			"model":               upstream.Config.Model,
			"weight":              upstream.CurrentWeight,
			"consecutive_failures": consecutiveFailures,
			"last_test_time":      upstream.LastTestTime.Format("2006-01-02 15:04:05"),
			"enabled":             upstream.Config.Enabled,
		}
		
		upstream.mu.RUnlock()
		result = append(result, info)
	}

	return result
}