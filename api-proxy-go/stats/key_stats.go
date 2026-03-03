package stats

import (
	"sync"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/models"
)

// KeyStatsManager API Key 统计管理器
type KeyStatsManager struct {
	stats    map[string]*models.KeyStat
	config   *config.Config
	mu       sync.RWMutex
}

// NewKeyStatsManager 创建 API Key 统计管理器
func NewKeyStatsManager(cfg *config.Config) *KeyStatsManager {
	return &KeyStatsManager{
		stats:  make(map[string]*models.KeyStat),
		config: cfg,
	}
}

// RecordRequest 记录请求
func (ksm *KeyStatsManager) RecordRequest(key string, success bool) {
	ksm.mu.Lock()
	defer ksm.mu.Unlock()

	stat, exists := ksm.stats[key]
	if !exists {
		// 创建新的统计
		limit := ksm.config.Auth.DefaultLimit
		stat = models.NewKeyStat(key, limit)
		ksm.stats[key] = stat
	}

	stat.RecordRequest(success)
}

// IsAuthorized 检查是否授权
func (ksm *KeyStatsManager) IsAuthorized(key string) bool {
	cfg := ksm.config

	// 如果未启用认证，允许所有
	if !cfg.Auth.Enabled {
		return true
	}

	// 如果启用了认证但白名单为空，允许所有
	if len(cfg.Auth.Keys) == 0 {
		return true
	}

	// 检查是否在白名单中
	for _, allowedKey := range cfg.Auth.Keys {
		if key == allowedKey {
			return true
		}
	}

	return false
}

// IsExceeded 检查是否超过限额
func (ksm *KeyStatsManager) IsExceeded(key string) bool {
	if !ksm.config.Auth.KeyLimit {
		return false
	}

	ksm.mu.RLock()
	stat, exists := ksm.stats[key]
	ksm.mu.RUnlock()

	if !exists {
		return false
	}

	return stat.IsExceeded()
}

// GetStats 获取统计信息
func (ksm *KeyStatsManager) GetStats(key string) (total, success, failure int, limit int, exists bool) {
	ksm.mu.RLock()
	defer ksm.mu.RUnlock()

	stat, exists := ksm.stats[key]
	if !exists {
		return 0, 0, 0, 0, false
	}

	total, success, failure, limit = stat.GetUsage()
	return total, success, failure, limit, true
}

// GetAllStats 获取所有统计
func (ksm *KeyStatsManager) GetAllStats() map[string]interface{} {
	ksm.mu.RLock()
	defer ksm.mu.RUnlock()

	result := make(map[string]interface{})
	for key, stat := range ksm.stats {
		total, success, failure, limit := stat.GetUsage()
		result[key] = map[string]interface{}{
			"total":   total,
			"success": success,
			"failure": failure,
			"limit":   limit,
		}
	}

	return result
}

// Reset 重置统计
func (ksm *KeyStatsManager) Reset(key string) bool {
	ksm.mu.Lock()
	defer ksm.mu.Unlock()

	stat, exists := ksm.stats[key]
	if !exists {
		return false
	}

	stat.Reset()
	return true
}

// ResetAll 重置所有统计
func (ksm *KeyStatsManager) ResetAll() {
	ksm.mu.Lock()
	defer ksm.mu.Unlock()

	for _, stat := range ksm.stats {
		stat.Reset()
	}
}