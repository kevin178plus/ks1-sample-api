package middleware

import (
	"net/http"
	"strings"
	"sync"
	"time"
)

// 默认清理参数：
//   - cleanupInterval：每 5 分钟扫一次
//   - idleTTL：限流器在 10 分钟无访问后被回收
const (
	defaultCleanupInterval = 5 * time.Minute
	defaultIdleTTL         = 10 * time.Minute
)

// RateLimiter 限流器（简单令牌桶实现）
//
// P0-4 修复：
//   - 增加 lastSeen 字段记录最后访问时间。
//   - 构造时启动后台清理 goroutine，按 idleTTL 回收空闲 limiter，
//     避免大量动态 IP 场景下 map 无界增长。
//   - 提供 Stop() 用于优雅关闭清理 goroutine。
type RateLimiter struct {
	limiters        map[string]*tokenBucket
	mu              sync.Mutex
	rps             int
	cleanupInterval time.Duration
	idleTTL         time.Duration
	stopCh          chan struct{}
	stopOnce        sync.Once
}

// tokenBucket 令牌桶
type tokenBucket struct {
	tokens     int
	lastRefill time.Time
	lastSeen   time.Time
	mu         sync.Mutex
}

// NewRateLimiter 创建限流器并启动后台清理协程
func NewRateLimiter(rps int) *RateLimiter {
	return NewRateLimiterWithTTL(rps, defaultCleanupInterval, defaultIdleTTL)
}

// NewRateLimiterWithTTL 自定义清理参数（主要用于测试）
func NewRateLimiterWithTTL(rps int, cleanupInterval, idleTTL time.Duration) *RateLimiter {
	rl := &RateLimiter{
		limiters:        make(map[string]*tokenBucket),
		rps:             rps,
		cleanupInterval: cleanupInterval,
		idleTTL:         idleTTL,
		stopCh:          make(chan struct{}),
	}
	go rl.cleanupLoop()
	return rl
}

// getLimiter 获取指定 IP 的限流器
func (rl *RateLimiter) getLimiter(ip string) *tokenBucket {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[ip]
	if !exists {
		limiter = &tokenBucket{
			tokens:     rl.rps,
			lastRefill: time.Now(),
			lastSeen:   time.Now(),
		}
		rl.limiters[ip] = limiter
	} else {
		// 更新最后访问时间，防止活跃 IP 被错误回收
		limiter.lastSeen = time.Now()
	}
	return limiter
}

// allow 检查是否允许请求
func (tb *tokenBucket) allow(rps int) bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill)

	// 补充令牌
	if elapsed >= time.Second {
		tb.tokens = rps
		tb.lastRefill = now
	}

	// 检查是否有可用令牌
	if tb.tokens > 0 {
		tb.tokens--
		return true
	}

	return false
}

// Handler 返回限流处理器
func (rl *RateLimiter) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := getClientIP(r)
		limiter := rl.getLimiter(ip)
		if !limiter.allow(rl.rps) {
			http.Error(w, "Too many requests", http.StatusTooManyRequests)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// Stop 停止后台清理协程，幂等。
func (rl *RateLimiter) Stop() {
	rl.stopOnce.Do(func() {
		close(rl.stopCh)
	})
}

// Size 当前 limiter 数量（测试与 /debug 暴露用）。
func (rl *RateLimiter) Size() int {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	return len(rl.limiters)
}

// cleanupLoop 周期性回收空闲 limiter
func (rl *RateLimiter) cleanupLoop() {
	ticker := time.NewTicker(rl.cleanupInterval)
	defer ticker.Stop()
	for {
		select {
		case <-rl.stopCh:
			return
		case now := <-ticker.C:
			rl.purgeIdle(now)
		}
	}
}

// purgeIdle 清理 lastSeen 超过 idleTTL 的 limiter
func (rl *RateLimiter) purgeIdle(now time.Time) {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	for ip, lim := range rl.limiters {
		lim.mu.Lock()
		expired := now.Sub(lim.lastSeen) > rl.idleTTL
		lim.mu.Unlock()
		if expired {
			delete(rl.limiters, ip)
		}
	}
}

// getClientIP 获取客户端 IP
func getClientIP(r *http.Request) string {
	// 优先从 X-Forwarded-For 获取
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// 取第一个 IP
		if idx := strings.Index(xff, ","); idx != -1 {
			return strings.TrimSpace(xff[:idx])
		}
		return strings.TrimSpace(xff)
	}

	// 从 X-Real-IP 获取
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return strings.TrimSpace(xri)
	}

	// 从 RemoteAddr 获取
	if r.RemoteAddr != "" {
		if idx := strings.LastIndex(r.RemoteAddr, ":"); idx != -1 {
			return r.RemoteAddr[:idx]
		}
		return r.RemoteAddr
	}

	return "unknown"
}
