package middleware

import (
	"net/http"
	"strings"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/stats"
)

// Auth 认证中间件
type Auth struct {
	config   *config.Config
	keyStats *stats.KeyStatsManager
}

// NewAuth 创建认证中间件
func NewAuth(cfg *config.Config, keyStats *stats.KeyStatsManager) *Auth {
	return &Auth{
		config:   cfg,
		keyStats: keyStats,
	}
}

// Handler 返回认证处理器
func (a *Auth) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 如果未启用认证，直接放行
		if !a.config.Auth.Enabled {
			next.ServeHTTP(w, r)
			return
		}

		// 提取 API Key
		apiKey := a.extractAPIKey(r)

		// 检查授权
		if !a.keyStats.IsAuthorized(apiKey) {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// 检查限额
		if a.keyStats.IsExceeded(apiKey) {
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		// 放行
		next.ServeHTTP(w, r)
	})
}

// extractAPIKey 提取 API Key
func (a *Auth) extractAPIKey(r *http.Request) string {
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