package upstream

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"
)

// HealthChecker 健康检查器
type HealthChecker struct {
	manager *Manager
	ticker  *time.Ticker
	ctx     context.Context
	cancel  context.CancelFunc
	wg      sync.WaitGroup
}

// NewHealthChecker 创建健康检查器
func NewHealthChecker(manager *Manager) *HealthChecker {
	ctx, cancel := context.WithCancel(context.Background())
	return &HealthChecker{
		manager: manager,
		ctx:     ctx,
		cancel:  cancel,
	}
}

// Start 启动健康检查
func (h *HealthChecker) Start() {
	if !h.manager.config.HealthCheck.Enabled {
		return
	}

	h.ticker = time.NewTicker(h.manager.config.HealthCheck.Interval)

	h.wg.Add(1)
	go h.run()
}

// Stop 停止健康检查
func (h *HealthChecker) Stop() {
	if h.ticker != nil {
		h.ticker.Stop()
	}
	h.cancel()
	h.wg.Wait()
}

// run 运行健康检查
func (h *HealthChecker) run() {
	defer h.wg.Done()

	// 启动时立即检查一次
	h.checkAll()

	for {
		select {
		case <-h.ctx.Done():
			return
		case <-h.ticker.C:
			h.checkAll()
		}
	}
}

// checkAll 检查所有上游
func (h *HealthChecker) checkAll() {
	// 获取所有上游
	upstreams := h.manager.GetAll()

	// 并发检查
	var wg sync.WaitGroup
	for name := range upstreams {
		wg.Add(1)
		go func(n string) {
			defer wg.Done()
			h.checkUpstream(n)
		}(name)
	}
	wg.Wait()
}

// checkUpstream 检查单个上游
func (h *HealthChecker) checkUpstream(name string) {
	upstream, exists := h.manager.Get(name)
	if !exists {
		return
	}

	// SDK 模式，跳过 HTTP 检查
	if upstream.Config.UseSDK {
		upstream.mu.Lock()
		upstream.Available = true
		upstream.LastTestTime = time.Now()
		upstream.LastTestResult = "success (SDK mode)"
		upstream.mu.Unlock()
		return
	}

	// HTTP 模式，发送测试请求
	url := strings.TrimSuffix(upstream.Config.Address, "/") + "/v1/chat/completions"

	reqBody := `{
		"model": "test",
		"messages": [{"role": "user", "content": "ping"}],
		"max_tokens": 5
	}`

	ctx, cancel := context.WithTimeout(h.ctx, h.manager.config.HealthCheck.Timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "POST", url, strings.NewReader(reqBody))
	if err != nil {
		h.markUnavailable(upstream, fmt.Sprintf("create request failed: %v", err))
		return
	}

	req.Header.Set("Authorization", "Bearer "+upstream.Config.APIKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := h.manager.httpClient.Do(req)
	if err != nil {
		h.markUnavailable(upstream, fmt.Sprintf("request failed: %v", err))
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		h.markAvailable(upstream, "success")
	} else {
		h.markUnavailable(upstream, fmt.Sprintf("failed: status %d", resp.StatusCode))
	}
}

// markAvailable 标记为可用
func (h *HealthChecker) markAvailable(upstream *Upstream, result string) {
	upstream.mu.Lock()
	defer upstream.mu.Unlock()

	wasUnavailable := !upstream.Available
	upstream.Available = true
	upstream.LastTestTime = time.Now()
	upstream.LastTestResult = result

	if wasUnavailable {
		log.Printf("[健康检查] %s 已恢复", upstream.Name)
		h.manager.updateAvailableList()
	}
}

// markUnavailable 标记为不可用
func (h *HealthChecker) markUnavailable(upstream *Upstream, result string) {
	upstream.mu.Lock()
	defer upstream.mu.Unlock()

	wasAvailable := upstream.Available
	upstream.Available = false
	upstream.LastTestTime = time.Now()
	upstream.LastTestResult = result

	if wasAvailable {
		log.Printf("[健康检查] %s 已失效: %s", upstream.Name, result)
		h.manager.updateAvailableList()
	}
}