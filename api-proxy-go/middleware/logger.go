package middleware

import (
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// Logger 日志中间件
type Logger struct{}

// NewLogger 创建日志中间件
func NewLogger() *Logger {
	return &Logger{}
}

// Handler 返回日志处理器
func (l *Logger) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 生成请求 ID
		requestID := uuid.New().String()[:8]

		// 添加请求 ID 到响应头
		w.Header().Set("X-Request-ID", requestID)

		// 记录请求时间
		startTime := time.Now()

		// 使用 ResponseWriter 包装器捕获状态码
		rw := &responseWriter{ResponseWriter: w}

		// 记录请求信息
		log.Printf("[请求] [%s] %s %s", requestID, r.Method, r.URL.Path)

		// 调用下一个处理器
		next.ServeHTTP(rw, r)

		// 记录响应信息
		duration := time.Since(startTime)
		log.Printf("[响应] [%s] %s %s %d (%v)", requestID, r.Method, r.URL.Path, rw.statusCode, duration)
	})
}

// responseWriter ResponseWriter 包装器
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	written    bool
}

// WriteHeader 捕获状态码
func (rw *responseWriter) WriteHeader(code int) {
	if !rw.written {
		rw.statusCode = code
		rw.written = true
		rw.ResponseWriter.WriteHeader(code)
	}
}

// Write 捕获写入
func (rw *responseWriter) Write(b []byte) (int, error) {
	if !rw.written {
		rw.WriteHeader(http.StatusOK)
	}
	return rw.ResponseWriter.Write(b)
}