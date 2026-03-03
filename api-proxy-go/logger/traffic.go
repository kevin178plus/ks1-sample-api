package logger

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/google/uuid"
	stdlog "log"
)

// TrafficLogEntry 流量日志条目
type TrafficLogEntry struct {
	Timestamp   time.Time              `json:"timestamp"`
	RequestID   string                 `json:"request_id"`
	Type        string                 `json:"type"` // REQUEST, RESPONSE, ERROR
	Upstream    string                 `json:"upstream,omitempty"`
	StatusCode  int                    `json:"status_code,omitempty"`
	Duration    int64                  `json:"duration_ms,omitempty"`
	Data        map[string]interface{} `json:"data,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// TrafficLogger 流量日志器
type TrafficLogger struct {
	enabled      bool
	path         string
	bufferSize   int
	recordBody   bool
	maxBodyBytes int
	buffer       chan *TrafficLogEntry
	wg           sync.WaitGroup
	mu           sync.Mutex
	file         *os.File
}

// NewTrafficLogger 创建流量日志器
func NewTrafficLogger(enabled bool, path string, bufferSize int, recordBody bool, maxBodyBytes int) *TrafficLogger {
	if !enabled {
		return &TrafficLogger{enabled: false}
	}

	// 确保目录存在
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		stdlog.Printf("[错误] 创建流量日志目录失败: %v", err)
		return &TrafficLogger{enabled: false}
	}

	tl := &TrafficLogger{
		enabled:      true,
		path:         path,
		bufferSize:   bufferSize,
		recordBody:   recordBody,
		maxBodyBytes: maxBodyBytes,
		buffer:       make(chan *TrafficLogEntry, bufferSize),
	}

	// 启动写入协程
	tl.wg.Add(1)
	go tl.writeLoop()

	return tl
}

// LogRequest 记录请求
func (tl *TrafficLogger) LogRequest(requestID string, method, path string, headers map[string]string, body []byte, upstream string) {
	if !tl.enabled {
		return
	}

	entry := &TrafficLogEntry{
		Timestamp: time.Now(),
		RequestID: requestID,
		Type:      "REQUEST",
		Upstream:  upstream,
		Data: map[string]interface{}{
			"method":  method,
			"path":    path,
			"headers": headers,
		},
	}

	// 如果需要记录 Body
	if tl.recordBody && len(body) > 0 {
		if len(body) > tl.maxBodyBytes {
			body = body[:tl.maxBodyBytes]
		}
		entry.Data["body"] = string(body)
	}

	tl.sendEntry(entry)
}

// LogResponse 记录响应
func (tl *TrafficLogger) LogResponse(requestID string, statusCode int, headers map[string]string, body []byte, duration time.Duration, upstream string) {
	if !tl.enabled {
		return
	}

	entry := &TrafficLogEntry{
		Timestamp:  time.Now(),
		RequestID:  requestID,
		Type:       "RESPONSE",
		StatusCode: statusCode,
		Duration:   duration.Milliseconds(),
		Upstream:   upstream,
		Data: map[string]interface{}{
			"headers": headers,
		},
	}

	// 如果需要记录 Body
	if tl.recordBody && len(body) > 0 {
		if len(body) > tl.maxBodyBytes {
			body = body[:tl.maxBodyBytes]
		}
		entry.Data["body"] = string(body)
	}

	tl.sendEntry(entry)
}

// LogError 记录错误
func (tl *TrafficLogger) LogError(requestID string, err error, upstream string) {
	if !tl.enabled {
		return
	}

	entry := &TrafficLogEntry{
		Timestamp: time.Now(),
		RequestID: requestID,
		Type:      "ERROR",
		Upstream:  upstream,
		Error:     err.Error(),
	}

	tl.sendEntry(entry)
}

// sendEntry 发送日志条目
func (tl *TrafficLogger) sendEntry(entry *TrafficLogEntry) {
	select {
	case tl.buffer <- entry:
		// 成功发送
	default:
		// 缓冲区满，丢弃日志
		stdlog.Printf("[警告] 流量日志缓冲区满，丢弃日志")
	}
}

// writeLoop 写入循环
func (tl *TrafficLogger) writeLoop() {
	defer tl.wg.Done()

	for entry := range tl.buffer {
		tl.writeEntry(entry)
	}
}

// writeEntry 写入单个条目
func (tl *TrafficLogger) writeEntry(entry *TrafficLogEntry) {
	tl.mu.Lock()
	defer tl.mu.Unlock()

	// 打开文件（追加模式）
	file, err := os.OpenFile(tl.path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		stdlog.Printf("[错误] 打开流量日志文件失败: %v", err)
		return
	}
	defer file.Close()

	// 序列化
	data, err := json.Marshal(entry)
	if err != nil {
		stdlog.Printf("[错误] 序列化流量日志失败: %v", err)
		return
	}

	// 写入
	if _, err := file.Write(append(data, '\n')); err != nil {
		stdlog.Printf("[错误] 写入流量日志失败: %v", err)
	}
}

// Close 关闭流量日志器
func (tl *TrafficLogger) Close() {
	if !tl.enabled {
		return
	}

	// 关闭缓冲区
	close(tl.buffer)

	// 等待写入完成
	tl.wg.Wait()
}

// GenerateRequestID 生成请求 ID
func GenerateRequestID() string {
	return uuid.New().String()[:8]
}

// log 日志器（用于输出错误）
var logger = &Logger{}