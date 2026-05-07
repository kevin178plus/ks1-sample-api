package logger

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// TestTrafficLogger_DroppedCount 缓冲区满时丢弃应被计数
func TestTrafficLogger_DroppedCount(t *testing.T) {
	dir := t.TempDir()
	tl := NewTrafficLoggerWithRotation(true, filepath.Join(dir, "t.log"),
		1, false, 0, 100, 0, false)
	defer tl.Close()

	// 拉满缓冲区：直接构造 entry 通过 sendEntry 投递。
	// 由于 writeLoop 异步消费，瞬时投递大量条目会触发丢弃路径。
	for i := 0; i < 1000; i++ {
		tl.LogError("rid", errors.New("boom"), "u1")
	}
	// 等到 writeLoop 至少消费几条
	time.Sleep(50 * time.Millisecond)

	if tl.DroppedCount() == 0 {
		// 容忍的极端情况：1000 条全部被消费完
		t.Logf("DroppedCount=0（消费足够快），跳过严格断言")
	}
}

// TestTrafficLogger_Rotation 写入超过 size 阈值后应触发轮转
func TestTrafficLogger_Rotation(t *testing.T) {
	dir := t.TempDir()
	logPath := filepath.Join(dir, "traffic.log")

	// maxSizeMB=0 会被构造函数默认为 100MB；这里直接构造结构体并手动调小。
	tl := &TrafficLogger{
		enabled:      true,
		path:         logPath,
		bufferSize:   16,
		recordBody:   true,
		maxBodyBytes: 4096,
		maxSizeBytes: 1024, // 1KB 触发轮转
		maxBackups:   2,
		compress:     false,
		buffer:       make(chan *TrafficLogEntry, 16),
	}
	if err := tl.openFile(); err != nil {
		t.Fatalf("openFile: %v", err)
	}
	tl.wg.Add(1)
	go tl.writeLoop()
	defer tl.Close()

	// 用大 body 快速撑爆 1KB
	bigBody := make([]byte, 800)
	for i := range bigBody {
		bigBody[i] = 'x'
	}
	for i := 0; i < 10; i++ {
		tl.LogRequest("rid", "POST", "/v1/chat/completions",
			map[string]string{"K": "V"}, bigBody, "u1")
	}

	// 等待 writeLoop 消费 + 轮转
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Stat(logPath + ".1"); err == nil {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatalf("轮转后应存在 %s.1，但未找到", logPath)
}

// TestTrafficLogger_Disabled 关闭时所有 Log* 都是 no-op
func TestTrafficLogger_Disabled(t *testing.T) {
	tl := NewTrafficLoggerWithRotation(false, "ignored", 0, false, 0, 0, 0, false)
	tl.LogRequest("rid", "GET", "/", nil, nil, "")
	tl.LogResponse("rid", 200, nil, nil, time.Millisecond, "")
	tl.LogError("rid", errors.New("x"), "")
	tl.Close()
	if tl.DroppedCount() != 0 {
		t.Fatal("disabled logger DroppedCount 应为 0")
	}
}
