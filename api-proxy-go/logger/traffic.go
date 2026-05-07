package logger

import (
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	stdlog "log"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

// TrafficLogEntry 流量日志条目
type TrafficLogEntry struct {
	Timestamp  time.Time              `json:"timestamp"`
	RequestID  string                 `json:"request_id"`
	Type       string                 `json:"type"` // REQUEST, RESPONSE, ERROR
	Upstream   string                 `json:"upstream,omitempty"`
	StatusCode int                    `json:"status_code,omitempty"`
	Duration   int64                  `json:"duration_ms,omitempty"`
	Data       map[string]interface{} `json:"data,omitempty"`
	Error      string                 `json:"error,omitempty"`
}

// TrafficLogger 流量日志器（异步缓冲 + 大小轮转）
//
// P1-3 修复：
//   - 增加 droppedCount 原子计数，可通过 DroppedCount() 暴露给监控。
//   - 实现 size + max_backups 的滚动归档（可选 gzip 压缩）。
//   - writeLoop 共享单一文件句柄，避免每条日志都 open/close。
type TrafficLogger struct {
	enabled      bool
	path         string
	bufferSize   int
	recordBody   bool
	maxBodyBytes int

	// 轮转参数
	maxSizeBytes int64
	maxBackups   int
	compress     bool

	buffer chan *TrafficLogEntry
	wg     sync.WaitGroup

	mu          sync.Mutex // 保护 file 与 currentSize
	file        *os.File
	currentSize int64

	droppedCount uint64 // 缓冲区满丢弃计数（atomic）
}

// NewTrafficLogger 创建流量日志器
//
// 旧签名被保留以兼容已有 main.go 调用：
//
//	NewTrafficLogger(enabled, path, bufferSize, recordBody, maxBodyBytes)
//
// 此场景下使用默认 100MB / 3 备份 / 启用 gzip。
func NewTrafficLogger(enabled bool, path string, bufferSize int, recordBody bool, maxBodyBytes int) *TrafficLogger {
	return NewTrafficLoggerWithRotation(enabled, path, bufferSize, recordBody, maxBodyBytes, 100, 3, true)
}

// NewTrafficLoggerWithRotation 显式控制轮转参数。
func NewTrafficLoggerWithRotation(
	enabled bool, path string, bufferSize int,
	recordBody bool, maxBodyBytes int,
	maxSizeMB int, maxBackups int, compress bool,
) *TrafficLogger {
	if !enabled {
		return &TrafficLogger{enabled: false}
	}

	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		stdlog.Printf("[错误] 创建流量日志目录失败: %v", err)
		return &TrafficLogger{enabled: false}
	}

	if maxSizeMB <= 0 {
		maxSizeMB = 100
	}
	if maxBackups < 0 {
		maxBackups = 0
	}
	if bufferSize <= 0 {
		bufferSize = 1000
	}

	tl := &TrafficLogger{
		enabled:      true,
		path:         path,
		bufferSize:   bufferSize,
		recordBody:   recordBody,
		maxBodyBytes: maxBodyBytes,
		maxSizeBytes: int64(maxSizeMB) * 1024 * 1024,
		maxBackups:   maxBackups,
		compress:     compress,
		buffer:       make(chan *TrafficLogEntry, bufferSize),
	}

	if err := tl.openFile(); err != nil {
		stdlog.Printf("[错误] 打开流量日志文件失败: %v", err)
		return &TrafficLogger{enabled: false}
	}

	tl.wg.Add(1)
	go tl.writeLoop()
	return tl
}

// openFile 打开（或创建）日志文件，并初始化 currentSize
func (tl *TrafficLogger) openFile() error {
	f, err := os.OpenFile(tl.path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return err
	}
	stat, err := f.Stat()
	if err != nil {
		_ = f.Close()
		return err
	}
	tl.file = f
	tl.currentSize = stat.Size()
	return nil
}

// LogRequest 记录请求
func (tl *TrafficLogger) LogRequest(requestID, method, path string, headers map[string]string, body []byte, upstream string) {
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

// DroppedCount 返回累计丢弃的日志条数（线程安全）。
func (tl *TrafficLogger) DroppedCount() uint64 {
	if !tl.enabled {
		return 0
	}
	return atomic.LoadUint64(&tl.droppedCount)
}

// sendEntry 发送日志条目
func (tl *TrafficLogger) sendEntry(entry *TrafficLogEntry) {
	select {
	case tl.buffer <- entry:
		// ok
	default:
		// 缓冲区满 → 计数 + 限频日志（每 1024 次提示一次）
		n := atomic.AddUint64(&tl.droppedCount, 1)
		if n == 1 || n%1024 == 0 {
			stdlog.Printf("[警告] 流量日志缓冲区满，已累计丢弃 %d 条", n)
		}
	}
}

// writeLoop 写入循环
func (tl *TrafficLogger) writeLoop() {
	defer tl.wg.Done()
	for entry := range tl.buffer {
		tl.writeEntry(entry)
	}
}

// writeEntry 写入单个条目并按需轮转
func (tl *TrafficLogger) writeEntry(entry *TrafficLogEntry) {
	tl.mu.Lock()
	defer tl.mu.Unlock()

	if tl.file == nil {
		if err := tl.openFile(); err != nil {
			stdlog.Printf("[错误] 重新打开流量日志失败: %v", err)
			return
		}
	}

	data, err := json.Marshal(entry)
	if err != nil {
		stdlog.Printf("[错误] 序列化流量日志失败: %v", err)
		return
	}
	data = append(data, '\n')

	n, err := tl.file.Write(data)
	if err != nil {
		stdlog.Printf("[错误] 写入流量日志失败: %v", err)
		return
	}
	tl.currentSize += int64(n)

	// 触发轮转
	if tl.maxSizeBytes > 0 && tl.currentSize >= tl.maxSizeBytes {
		if err := tl.rotateLocked(); err != nil {
			stdlog.Printf("[错误] 流量日志轮转失败: %v", err)
		}
	}
}

// rotateLocked 滚动归档当前文件（调用方需持有 tl.mu）
//
// 流程：
//  1. close 当前 file。
//  2. 移除最老备份 path.{maxBackups}（如启用压缩则为 .gz）。
//  3. 自高到低重命名 path.k -> path.{k+1}。
//  4. 重命名 path -> path.1。
//  5. 如启用 compress，将 path.1 异步 gzip 为 path.1.gz。
//  6. 重新打开新 path 写入。
func (tl *TrafficLogger) rotateLocked() error {
	if tl.file != nil {
		_ = tl.file.Close()
		tl.file = nil
	}
	tl.currentSize = 0

	if tl.maxBackups <= 0 {
		// 不保留历史 → 直接清空当前文件
		if err := os.Remove(tl.path); err != nil && !os.IsNotExist(err) {
			return err
		}
		return tl.openFile()
	}

	// 删除最老备份
	oldest := backupName(tl.path, tl.maxBackups, tl.compress)
	_ = os.Remove(oldest)

	// 移位 k -> k+1
	for i := tl.maxBackups - 1; i >= 1; i-- {
		from := backupName(tl.path, i, tl.compress)
		to := backupName(tl.path, i+1, tl.compress)
		if _, err := os.Stat(from); err == nil {
			if err := os.Rename(from, to); err != nil {
				stdlog.Printf("[警告] 流量日志移位失败 %s -> %s: %v", from, to, err)
			}
		}
	}

	// 当前文件 -> .1（先不压缩，重命名后再压缩）
	rotated := tl.path + ".1"
	if err := os.Rename(tl.path, rotated); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("rename %s -> %s: %w", tl.path, rotated, err)
	}

	// 异步 gzip
	if tl.compress {
		go compressFile(rotated)
	}

	return tl.openFile()
}

// backupName 计算第 i 份备份的文件名（i>=1）
func backupName(base string, i int, compress bool) string {
	name := fmt.Sprintf("%s.%d", base, i)
	if compress && i >= 1 {
		// 注意：移位时仍按 .gz 命名才能匹配上次压缩结果
		return name + ".gz"
	}
	return name
}

// compressFile 将给定文件 gzip 为 .gz 并删除原文件
func compressFile(path string) {
	src, err := os.Open(path)
	if err != nil {
		stdlog.Printf("[警告] 压缩流量日志失败 (open %s): %v", path, err)
		return
	}
	defer src.Close()

	dst, err := os.Create(path + ".gz")
	if err != nil {
		stdlog.Printf("[警告] 压缩流量日志失败 (create %s.gz): %v", path, err)
		return
	}
	gz := gzip.NewWriter(dst)
	if _, err := io.Copy(gz, src); err != nil {
		stdlog.Printf("[警告] 压缩流量日志失败 (copy): %v", err)
		_ = gz.Close()
		_ = dst.Close()
		_ = os.Remove(path + ".gz")
		return
	}
	_ = gz.Close()
	_ = dst.Close()
	if err := os.Remove(path); err != nil {
		stdlog.Printf("[警告] 压缩后删除原文件失败 %s: %v", path, err)
	}
}

// Close 关闭流量日志器
func (tl *TrafficLogger) Close() {
	if !tl.enabled {
		return
	}
	close(tl.buffer)
	tl.wg.Wait()

	tl.mu.Lock()
	if tl.file != nil {
		_ = tl.file.Close()
		tl.file = nil
	}
	tl.mu.Unlock()
}

// GenerateRequestID 生成请求 ID
func GenerateRequestID() string {
	return uuid.New().String()[:8]
}
