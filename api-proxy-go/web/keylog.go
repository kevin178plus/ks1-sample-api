package web

import (
	"fmt"
	"sync"
	"time"
)

// KeyLogEntry 关键日志条目
type KeyLogEntry struct {
	Timestamp string `json:"timestamp"` // HH:mm:ss 格式
	Message   string `json:"message"`
}

// KeyLogBuffer 关键日志环形缓冲区
type KeyLogBuffer struct {
	entries []KeyLogEntry
	maxSize int
	mu      sync.Mutex
}

// NewKeyLogBuffer 创建关键日志缓冲区
func NewKeyLogBuffer(maxSize int) *KeyLogBuffer {
	return &KeyLogBuffer{
		entries: make([]KeyLogEntry, 0, maxSize),
		maxSize: maxSize,
	}
}

// Append 追加日志条目
func (b *KeyLogBuffer) Append(message string) {
	b.mu.Lock()
	defer b.mu.Unlock()

	now := time.Now()
	entry := KeyLogEntry{
		Timestamp: now.Format("15:04:05"),
		Message:   message,
	}
	b.entries = append(b.entries, entry)
	if len(b.entries) > b.maxSize {
		b.entries = b.entries[len(b.entries)-b.maxSize:]
	}
}

// Appendf 格式化追加
func (b *KeyLogBuffer) Appendf(format string, args ...interface{}) {
	b.Append(fmt.Sprintf(format, args...))
}

// GetAll 获取所有日志（副本）
func (b *KeyLogBuffer) GetAll() []KeyLogEntry {
	b.mu.Lock()
	defer b.mu.Unlock()

	result := make([]KeyLogEntry, len(b.entries))
	copy(result, b.entries)
	return result
}

// Clear 清空日志
func (b *KeyLogBuffer) Clear() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.entries = b.entries[:0]
}
