package upstream

import (
	"math/rand"
	"sync"
	"time"
)

// Selector 选择器
//
// 并发说明：
//   - s.mu 仅保护 s.rand 与 s.rrCounter（rand.Rand 与计数器都非并发安全）。
//   - 上游列表与权重通过 Manager.GetAvailableWithWeights() 原子快照获得，
//     不再在选择期间反复访问 Manager 状态（P0-3 修复）。
type Selector struct {
	manager   *Manager
	rand      *rand.Rand
	rrCounter uint64 // 轮询计数器
	mu        sync.Mutex
}

// NewSelector 创建选择器
func NewSelector(manager *Manager) *Selector {
	return &Selector{
		manager: manager,
		rand:    rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// Select 选择下一个上游（基于权重）
func (s *Selector) Select() (string, error) {
	// 1. 原子快照：在 Manager 锁内一次性拿到 available + weights
	available, weights := s.manager.GetAvailableWithWeights()
	if len(available) == 0 {
		return "", ErrNoAvailableUpstream
	}

	// 2. 计算总权重 + 是否存在特别权重上游（同一份快照下）
	totalWeight := 0
	specialThreshold := s.manager.config.Weight.SpecialThreshold
	specialMaxName := ""
	specialMaxWeight := -1
	for _, name := range available {
		w := weights[name]
		totalWeight += w
		if w > specialThreshold && w > specialMaxWeight {
			specialMaxWeight = w
			specialMaxName = name
		}
	}

	// 3. 命中特别权重 → 直接返回（必然选中策略）
	if specialMaxName != "" {
		return specialMaxName, nil
	}

	// 4. 全为 0 → 轮询
	if totalWeight <= 0 {
		return s.selectRoundRobin(available), nil
	}

	// 5. 加权随机：rand 调用与本地变量绑定，无任何外部共享状态
	s.mu.Lock()
	r := s.rand.Intn(totalWeight)
	s.mu.Unlock()

	cumulative := 0
	for _, name := range available {
		cumulative += weights[name]
		if r < cumulative {
			return name, nil
		}
	}

	// 浮点/整数累加边界兜底
	return available[len(available)-1], nil
}

// selectRoundRobin 轮询选择（在权重全为 0 时使用）
func (s *Selector) selectRoundRobin(available []string) string {
	s.mu.Lock()
	defer s.mu.Unlock()
	if len(available) == 0 {
		return ""
	}
	idx := s.rrCounter % uint64(len(available))
	s.rrCounter++
	return available[idx]
}

// SelectModel 选择模型（如果上游支持多模型）
func (s *Selector) SelectModel(upstreamName string) string {
	s.manager.mu.RLock()
	upstream, exists := s.manager.upstreams[upstreamName]
	s.manager.mu.RUnlock()

	if !exists {
		return ""
	}

	cfg := upstream.Config

	// 如果只有一个模型或没有配置多模型，返回默认模型
	if len(cfg.AvailableModels) <= 1 || !cfg.UseWeightedModel {
		return cfg.Model
	}

	// 按权重随机选择模型
	// 模型权重：第一个模型权重最高，依次递减
	weights := make([]int, len(cfg.AvailableModels))
	for i := range weights {
		weights[i] = len(cfg.AvailableModels) - i
	}

	totalWeight := 0
	for _, w := range weights {
		totalWeight += w
	}

	s.mu.Lock()
	r := s.rand.Intn(totalWeight)
	s.mu.Unlock()

	cumulative := 0
	for i, w := range weights {
		cumulative += w
		if r < cumulative {
			return cfg.AvailableModels[i]
		}
	}

	return cfg.AvailableModels[0]
}

// Errors
var (
	ErrNoAvailableUpstream = NewError("no available upstream")
)

// Error 错误类型
type Error struct {
	message string
}

func NewError(message string) *Error {
	return &Error{message: message}
}

func (e *Error) Error() string {
	return e.message
}
