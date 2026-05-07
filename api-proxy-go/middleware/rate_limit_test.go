package middleware

import (
	"testing"
	"time"
)

func TestRateLimiter_AllowAndExhaust(t *testing.T) {
	rl := NewRateLimiterWithTTL(2, time.Hour, time.Hour)
	defer rl.Stop()
	lim := rl.getLimiter("1.2.3.4")

	if !lim.allow(2) || !lim.allow(2) {
		t.Fatalf("前两次应放行")
	}
	if lim.allow(2) {
		t.Fatalf("第三次应被拒绝（令牌耗尽）")
	}
}

func TestRateLimiter_RefillAfterOneSecond(t *testing.T) {
	rl := NewRateLimiterWithTTL(1, time.Hour, time.Hour)
	defer rl.Stop()
	lim := rl.getLimiter("1.2.3.4")

	if !lim.allow(1) {
		t.Fatalf("首次应放行")
	}
	if lim.allow(1) {
		t.Fatalf("第二次应被拒绝")
	}
	// 等待补充窗口
	lim.lastRefill = time.Now().Add(-2 * time.Second)
	if !lim.allow(1) {
		t.Fatalf("跨秒后应重新放行")
	}
}

func TestRateLimiter_PurgeIdle(t *testing.T) {
	rl := NewRateLimiterWithTTL(10, time.Hour, 50*time.Millisecond)
	defer rl.Stop()

	// 创建几个 limiter
	rl.getLimiter("a")
	rl.getLimiter("b")
	rl.getLimiter("c")

	if rl.Size() != 3 {
		t.Fatalf("初始化时 Size 应为 3, 实际 %d", rl.Size())
	}

	// 手动触发 purge：模拟时间流逝
	future := time.Now().Add(time.Second)
	rl.purgeIdle(future)
	if rl.Size() != 0 {
		t.Fatalf("过期后 Size 应为 0, 实际 %d", rl.Size())
	}
}

func TestRateLimiter_LastSeenRefreshes(t *testing.T) {
	rl := NewRateLimiterWithTTL(10, time.Hour, 100*time.Millisecond)
	defer rl.Stop()

	lim := rl.getLimiter("hot")
	// 把 lastSeen 推到很久以前，模拟一段空闲
	lim.mu.Lock()
	lim.lastSeen = time.Now().Add(-time.Hour)
	lim.mu.Unlock()

	// 再次访问应刷新 lastSeen
	rl.getLimiter("hot")
	rl.purgeIdle(time.Now())
	if rl.Size() != 1 {
		t.Fatalf("活跃 limiter 不应被清理，Size=%d", rl.Size())
	}
}

func TestRateLimiter_StopIdempotent(t *testing.T) {
	rl := NewRateLimiterWithTTL(1, time.Hour, time.Hour)
	rl.Stop()
	rl.Stop() // 不应 panic
}
