package upstream

import (
	"sync"
	"testing"

	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/models"
)

// newTestManager 构造一个最小化 Manager，预填充指定上游与权重，全部标记为可用。
func newTestManager(weights map[string]int) *Manager {
	cfg := config.DefaultConfig()
	m := NewManager(cfg)
	for name, w := range weights {
		m.upstreams[name] = &Upstream{
			Name:          name,
			Config:        &config.UpstreamConfig{Name: name, Enabled: true},
			Stat:          models.NewUpstreamStat(),
			CurrentWeight: w,
			Available:     true,
		}
	}
	m.UpdateAvailable()
	return m
}

// TestSelector_WeightedDistribution 验证加权随机大致符合权重比例
func TestSelector_WeightedDistribution(t *testing.T) {
	m := newTestManager(map[string]int{
		"a": 10,
		"b": 30,
		"c": 60,
	})
	s := NewSelector(m)

	const N = 10000
	counts := map[string]int{}
	for i := 0; i < N; i++ {
		name, err := s.Select()
		if err != nil {
			t.Fatalf("Select 返回错误: %v", err)
		}
		counts[name]++
	}

	// 期望比例 1:3:6，允许 ±25% 偏差
	check := func(name string, want float64) {
		got := float64(counts[name]) / float64(N)
		lo, hi := want*0.75, want*1.25
		if got < lo || got > hi {
			t.Errorf("%s 比例=%.3f 不在 [%.3f, %.3f]", name, got, lo, hi)
		}
	}
	check("a", 0.10)
	check("b", 0.30)
	check("c", 0.60)
}

// TestSelector_SpecialThreshold 命中特别权重必然选中权重最大的那个
func TestSelector_SpecialThreshold(t *testing.T) {
	m := newTestManager(map[string]int{
		"normal":  10,
		"special": 200, // > SpecialThreshold(100)
	})
	s := NewSelector(m)

	for i := 0; i < 100; i++ {
		name, err := s.Select()
		if err != nil {
			t.Fatalf("Select 返回错误: %v", err)
		}
		if name != "special" {
			t.Fatalf("期望 special，实际 %s", name)
		}
	}
}

// TestSelector_NoAvailable 空上游 → ErrNoAvailableUpstream
func TestSelector_NoAvailable(t *testing.T) {
	m := newTestManager(nil)
	s := NewSelector(m)
	_, err := s.Select()
	if err != ErrNoAvailableUpstream {
		t.Fatalf("期望 ErrNoAvailableUpstream，实际 %v", err)
	}
}

// TestSelector_ZeroWeightRoundRobin 所有权重为 0 → 轮询
func TestSelector_ZeroWeightRoundRobin(t *testing.T) {
	m := newTestManager(map[string]int{"a": 0, "b": 0, "c": 0})
	s := NewSelector(m)

	seen := map[string]int{}
	for i := 0; i < 30; i++ {
		name, err := s.Select()
		if err != nil {
			t.Fatalf("Select 返回错误: %v", err)
		}
		seen[name]++
	}
	if len(seen) < 2 {
		t.Errorf("权重全 0 应轮询不同节点，实际 seen=%v", seen)
	}
}

// TestSelector_ConcurrentSafe 并发 Select + SetWeight 不应触发 race（需 -race 才能检测）
func TestSelector_ConcurrentSafe(t *testing.T) {
	m := newTestManager(map[string]int{"a": 50, "b": 50, "c": 50})
	s := NewSelector(m)

	stop := make(chan struct{})
	var writerWG sync.WaitGroup
	var readerWG sync.WaitGroup

	// writer：持续修改权重，直到 stop 关闭
	writerWG.Add(1)
	go func() {
		defer writerWG.Done()
		for i := 0; ; i++ {
			select {
			case <-stop:
				return
			default:
			}
			m.SetWeight("a", 10+i%80)
			m.SetWeight("b", 10+i%80)
		}
	}()

	// readers：并发选择固定次数后退出
	for r := 0; r < 4; r++ {
		readerWG.Add(1)
		go func() {
			defer readerWG.Done()
			for i := 0; i < 5000; i++ {
				if _, err := s.Select(); err != nil {
					t.Errorf("Select 错误: %v", err)
					return
				}
			}
		}()
	}

	readerWG.Wait()
	close(stop)
	writerWG.Wait()
}
