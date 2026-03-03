package upstream

import (
	"math/rand"
	"sync"
	"time"
)

// Selector 选择器
type Selector struct {
	manager *Manager
	rand    *rand.Rand
	mu      sync.Mutex
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
	available := s.manager.GetAvailable()
	if len(available) == 0 {
		return "", ErrNoAvailableUpstream
	}

	// 获取所有可用上游的权重
	weights := make(map[string]int)
	totalWeight := 0

	for _, name := range available {
		weight := s.manager.GetWeight(name)
		weights[name] = weight
		totalWeight += weight
	}

	if totalWeight <= 0 {
		// 所有权重都为0，使用轮询
		return s.selectRoundRobin(available), nil
	}

	// 检查是否有特别权重的上游（> special_threshold）
	cfg := s.manager.config
	specialThreshold := cfg.Weight.SpecialThreshold

	for _, name := range available {
		if weights[name] > specialThreshold {
			// 选择权重最大的特别权重上游
			maxName := name
			maxWeight := weights[name]
			for n := range weights {
				if weights[n] > maxWeight {
					maxWeight = weights[n]
					maxName = n
				}
			}
			return maxName, nil
		}
	}

	// 正常权重选择
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

	// 理论上不会到这里
	return available[0], nil
}

// selectRoundRobin 轮询选择
func (s *Selector) selectRoundRobin(available []string) string {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 简单实现：返回第一个，调用方需要处理轮询
	// 在实际使用中，应该在 Manager 中维护轮询状态
	return available[0]
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