package stats

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/upstream"
)

// StatsManager 统计管理器
type StatsManager struct {
	manager *upstream.Manager
	config  *config.Config
	client  *http.Client
	mu      sync.RWMutex
}

// NewStatsManager 创建统计管理器
func NewStatsManager(manager *upstream.Manager, cfg *config.Config) *StatsManager {
	return &StatsManager{
		manager: manager,
		config:  cfg,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// CheckThresholds 检查阈值并触发警告
func (sm *StatsManager) CheckThresholds(upstreamName string) {
	sm.mu.RLock()
	upstream, exists := sm.manager.Get(upstreamName)
	sm.mu.RUnlock()

	if !exists {
		return
	}

	cfg := upstream.Config
	stat := sm.manager.GetStat(upstreamName)
	if stat == nil {
		return
	}

	hourly, daily, monthly, _ := stat.GetStats()

	// 检查小时限额
	if cfg.Limit.Hourly > 0 {
		ratio := float64(hourly) / float64(cfg.Limit.Hourly) * 100
		sm.checkLimit(upstreamName, "hourly", hourly, cfg.Limit.Hourly, ratio, cfg.Thresholds)
	}

	// 检查日限额
	if cfg.Limit.Daily > 0 {
		ratio := float64(daily) / float64(cfg.Limit.Daily) * 100
		sm.checkLimit(upstreamName, "daily", daily, cfg.Limit.Daily, ratio, cfg.Thresholds)
	}

	// 检查月限额
	if cfg.Limit.Monthly > 0 {
		ratio := float64(monthly) / float64(cfg.Limit.Monthly) * 100
		sm.checkLimit(upstreamName, "monthly", monthly, cfg.Limit.Monthly, ratio, cfg.Thresholds)
	}
}

// checkLimit 检查单个限额
func (sm *StatsManager) checkLimit(upstreamName, limitType string, current, limit int, ratio float64, thresholds config.ThresholdConfig) {
	if ratio >= float64(thresholds.Critical) {
		// 严重阈值：降低权重
		log.Printf("[统计] %s %s 限额严重警告: %d/%d (%.1f%%)", upstreamName, limitType, current, limit, ratio)
		sm.manager.DecreaseWeight(upstreamName)
		sm.sendWebhook(upstreamName, limitType, current, limit, ratio, "critical")
	} else if ratio >= float64(thresholds.Warning) {
		// 警告阈值：发送通知
		log.Printf("[统计] %s %s 限额警告: %d/%d (%.1f%%)", upstreamName, limitType, current, limit, ratio)
		sm.sendWebhook(upstreamName, limitType, current, limit, ratio, "warning")
	}
}

// sendWebhook 发送 Webhook 通知
func (sm *StatsManager) sendWebhook(upstreamName, limitType string, current, limit int, ratio float64, level string) {
	sm.mu.RLock()
	upstream, exists := sm.manager.Get(upstreamName)
	sm.mu.RUnlock()

	if !exists || upstream.Config.Webhook == "" {
		return
	}

	// 构建 Webhook 负载
	payload := map[string]interface{}{
		"timestamp":    time.Now().Format(time.RFC3339),
		"upstream":     upstreamName,
		"limit_type":   limitType,
		"current":      current,
		"limit":        limit,
		"ratio":        ratio,
		"level":        level,
		"message":      fmt.Sprintf("%s %s 限额 %s: %d/%d (%.1f%%)", upstreamName, limitType, level, current, limit, ratio),
	}

	// 发送 Webhook（异步）
	go func() {
		jsonData, err := json.Marshal(payload)
		if err != nil {
			log.Printf("[Webhook] 序列化失败: %v", err)
			return
		}

		resp, err := sm.client.Post(upstream.Config.Webhook, "application/json", bytes.NewReader(jsonData))
		if err != nil {
			log.Printf("[Webhook] 发送失败: %v", err)
			return
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			log.Printf("[Webhook] 返回错误: %d", resp.StatusCode)
		}
	}()
}

// GetUpstreamStats 获取上游统计
func (sm *StatsManager) GetUpstreamStats(upstreamName string) map[string]interface{} {
	stat := sm.manager.GetStat(upstreamName)
	if stat == nil {
		return nil
	}

	hourly, daily, monthly, consecutive := stat.GetStats()
	success, failure, timeout := stat.GetHistoryStats()

	return map[string]interface{}{
		"hourly":            hourly,
		"daily":             daily,
		"monthly":           monthly,
		"consecutive_failures": consecutive,
		"success_count":     success,
		"failure_count":     failure,
		"timeout_count":     timeout,
	}
}

// GetAllStats 获取所有统计
func (sm *StatsManager) GetAllStats() map[string]interface{} {
	result := make(map[string]interface{})

	upstreams := sm.manager.GetAll()
	for name := range upstreams {
		result[name] = sm.GetUpstreamStats(name)
	}

	return result
}