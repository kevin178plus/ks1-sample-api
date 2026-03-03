package models

import (
	"sync"
	"time"
)

// UpstreamStat 上游统计信息
type UpstreamStat struct {
	// 当前周期统计
	HourlyCount  int `json:"hourly_count"`  // 当前小时调用次数
	DailyCount   int `json:"daily_count"`   // 当前天调用次数
	MonthlyCount int `json:"monthly_count"` // 当前月调用次数

	// 周期信息
	HourlyStart  time.Time `json:"hourly_start"`  // 当前小时开始时间
	DailyStart   time.Time `json:"daily_start"`   // 当前天开始时间
	MonthlyStart time.Time `json:"monthly_start"` // 当前月开始时间

	// 历史统计
	SuccessCount int `json:"success_count"` // 总成功次数
	FailureCount int `json:"failure_count"` // 总失败次数
	TimeoutCount int `json:"timeout_count"` // 总超时次数

	// 连续失败
	ConsecutiveFailures int `json:"consecutive_failures"` // 连续失败次数

	mu sync.RWMutex
}

// RecordRequest 记录一次请求
func (s *UpstreamStat) RecordRequest(success bool, isTimeout bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()

	// 检查周期是否过期，如果过期则重置
	s.checkAndResetCycles(now)

	// 更新当前周期统计
	s.HourlyCount++
	s.DailyCount++
	s.MonthlyCount++

	// 更新历史统计
	if success {
		s.SuccessCount++
		s.ConsecutiveFailures = 0
	} else {
		s.FailureCount++
		s.ConsecutiveFailures++
		if isTimeout {
			s.TimeoutCount++
		}
	}
}

// checkAndResetCycles 检查并重置周期
func (s *UpstreamStat) checkAndResetCycles(now time.Time) {
	// 检查小时周期
	if now.Sub(s.HourlyStart) >= time.Hour {
		s.HourlyCount = 0
		s.HourlyStart = time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, now.Location())
	}

	// 检查天周期
	if now.Sub(s.DailyStart) >= 24*time.Hour {
		s.DailyCount = 0
		s.DailyStart = time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
	}

	// 检查月周期
	if now.Month() != s.MonthlyStart.Month() || now.Year() != s.MonthlyStart.Year() {
		s.MonthlyCount = 0
		s.MonthlyStart = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
	}
}

// GetStats 获取统计快照
func (s *UpstreamStat) GetStats() (hourly, daily, monthly int, consecutive int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.HourlyCount, s.DailyCount, s.MonthlyCount, s.ConsecutiveFailures
}

// GetHistoryStats 获取历史统计
func (s *UpstreamStat) GetHistoryStats() (success, failure, timeout int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.SuccessCount, s.FailureCount, s.TimeoutCount
}

// KeyStat API Key 统计信息
type KeyStat struct {
	Key          string    `json:"key"`           // API Key
	TotalCount   int       `json:"total_count"`   // 总调用次数
	SuccessCount int       `json:"success_count"` // 成功次数
	FailureCount int       `json:"failure_count"` // 失败次数
	Limit        int       `json:"limit"`         // 限额（调用次数）
	LastUsed     time.Time `json:"last_used"`     // 最后使用时间

	mu sync.RWMutex
}

// RecordRequest 记录一次请求
func (s *KeyStat) RecordRequest(success bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.TotalCount++
	s.LastUsed = time.Now()
	if success {
		s.SuccessCount++
	} else {
		s.FailureCount++
	}
}

// IsExceeded 检查是否超过限额
func (s *KeyStat) IsExceeded() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.Limit > 0 && s.TotalCount >= s.Limit
}

// GetUsage 获取使用情况
func (s *KeyStat) GetUsage() (total, success, failure int, limit int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.TotalCount, s.SuccessCount, s.FailureCount, s.Limit
}

// Reset 重置统计
func (s *KeyStat) Reset() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.TotalCount = 0
	s.SuccessCount = 0
	s.FailureCount = 0
}

// NewUpstreamStat 创建上游统计
func NewUpstreamStat() *UpstreamStat {
	now := time.Now()
	return &UpstreamStat{
		HourlyStart:  time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 0, 0, 0, now.Location()),
		DailyStart:   time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location()),
		MonthlyStart: time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location()),
	}
}

// NewKeyStat 创建 API Key 统计
func NewKeyStat(key string, limit int) *KeyStat {
	return &KeyStat{
		Key:   key,
		Limit: limit,
	}
}