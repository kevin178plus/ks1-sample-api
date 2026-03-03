package middleware

import (
	"net/http"
	"strings"
	"sync"
	"time"
)

// RateLimiter 限流器（简单令牌桶实现）
type RateLimiter struct {
	limiters map[string]*tokenBucket
	mu       sync.RWMutex
	rps      int // 每秒请求数限制
}

// tokenBucket 令牌桶
type tokenBucket struct {
	tokens    int
	lastRefill time.Time
	mu        sync.Mutex
}

// NewRateLimiter 创建限流器
func NewRateLimiter(rps int) *RateLimiter {
	return &RateLimiter{
		limiters: make(map[string]*tokenBucket),
		rps:      rps,
	}
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
		}
		rl.limiters[ip] = limiter
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
		// 获取客户端 IP
		ip := getClientIP(r)

		// 获取限流器
		limiter := rl.getLimiter(ip)

		// 检查是否超过限制
		if !limiter.allow(rl.rps) {
			http.Error(w, "Too many requests", http.StatusTooManyRequests)
			return
		}

		// 放行
		next.ServeHTTP(w, r)
	})
}

// getClientIP 获取客户端 IP
func getClientIP(r *http.Request) string {
	// 优先从 X-Forwarded-For 获取
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// 取第一个 IP
		if idx := strings.Index(xff, ","); idx != -1 {
			return xff[:idx]
		}
		return xff
	}

	// 从 X-Real-IP 获取
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
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

// cleanup 定期清理未使用的限流器
func (rl *RateLimiter) cleanup(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		// 简单实现：清理所有（实际应该根据最后使用时间清理）
		rl.limiters = make(map[string]*tokenBucket)
		rl.mu.Unlock()
	}
}