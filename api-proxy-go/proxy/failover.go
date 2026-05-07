package proxy

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/kevin178plus/api-proxy-go/upstream"
)

// FailoverHandler 失效转移处理器
//
// 职责：在多个上游之间做带退避的轮换尝试，自动跳过已尝试过的上游，
// 命中错误时调用 Manager 标记失败 / 超时；命中成功时记录恢复。
//
// P1-1 重构：原来 `proxy.go` 内联失败转移逻辑与本文件存在重复实现，
// 现统一收敛到本类型；`Proxy.executeWithFailover` 改为 thin wrapper。
type FailoverHandler struct {
	manager     *upstream.Manager
	selector    *upstream.Selector
	maxTries    int
	backoffBase time.Duration
}

// NewFailoverHandler 创建失效转移处理器
//
// maxTries：最多尝试次数（含首次）。
// backoffBase：首次重试基础等待时长，后续按 2^attempt * base 退避。
func NewFailoverHandler(manager *upstream.Manager, selector *upstream.Selector, maxTries int, backoffBase time.Duration) *FailoverHandler {
	if maxTries <= 0 {
		maxTries = 3
	}
	if backoffBase <= 0 {
		backoffBase = time.Second
	}
	return &FailoverHandler{
		manager:     manager,
		selector:    selector,
		maxTries:    maxTries,
		backoffBase: backoffBase,
	}
}

// Execute 执行请求（带失效转移）
//
// executeFunc 接收选中的上游名，返回业务结果或错误。
// 返回 (result, 命中上游名, error)。
func (fh *FailoverHandler) Execute(
	ctx context.Context,
	executeFunc func(string) (map[string]interface{}, error),
) (map[string]interface{}, string, error) {
	var lastErr error
	tried := make(map[string]struct{}, fh.maxTries)
	triedOrder := make([]string, 0, fh.maxTries)

	for attempt := 0; attempt < fh.maxTries; attempt++ {
		// 选择上游
		upstreamName, err := fh.selector.Select()
		if err != nil {
			if lastErr != nil {
				return nil, "", fmt.Errorf("no available upstream after %d tries: %w (last err: %v)", attempt, err, lastErr)
			}
			return nil, "", fmt.Errorf("no available upstream: %w", err)
		}

		// 已尝试过 → 跳过本次，但仍占用一次 attempt 名额，避免无限循环
		if _, dup := tried[upstreamName]; dup {
			// 等待短暂后再选，让 Selector 有机会随机到不同节点
			select {
			case <-ctx.Done():
				return nil, "", ctx.Err()
			case <-time.After(50 * time.Millisecond):
			}
			continue
		}
		tried[upstreamName] = struct{}{}
		triedOrder = append(triedOrder, upstreamName)

		// 执行请求
		result, err := executeFunc(upstreamName)
		if err != nil {
			lastErr = err
			fh.manager.MarkFailure(upstreamName)
			if isTimeoutError(err) {
				fh.manager.MarkTimeout(upstreamName)
			}
			log.Printf("[失效转移] %s 失败: %v (尝试 %d/%d, 已尝试: %v)",
				upstreamName, err, attempt+1, fh.maxTries, triedOrder)

			// 等待后重试（最后一次不再 sleep）
			if attempt < fh.maxTries-1 {
				wait := time.Duration(1<<attempt) * fh.backoffBase
				log.Printf("[失效转移] %v 后重试...", wait)
				select {
				case <-ctx.Done():
					return nil, "", ctx.Err()
				case <-time.After(wait):
				}
			}
			continue
		}

		// 成功
		fh.manager.MarkSuccess(upstreamName)
		if stat := fh.manager.GetStat(upstreamName); stat != nil {
			_, _, _, consecutive := stat.GetStats()
			if consecutive > 0 {
				log.Printf("[失效转移] %s 已恢复 (之前连续失败 %d 次)", upstreamName, consecutive)
			}
		}
		return result, upstreamName, nil
	}

	return nil, "", fmt.Errorf("all retries failed (tried: %v): %w", triedOrder, lastErr)
}

// GetFailoverStats 获取失效转移统计
func (fh *FailoverHandler) GetFailoverStats() map[string]interface{} {
	upstreams := fh.manager.GetAll()
	stats := make(map[string]interface{}, len(upstreams))
	for name := range upstreams {
		stat := fh.manager.GetStat(name)
		if stat == nil {
			continue
		}
		_, _, _, consecutive := stat.GetStats()
		success, failure, timeout := stat.GetHistoryStats()
		stats[name] = map[string]interface{}{
			"consecutive_failures": consecutive,
			"success_count":        success,
			"failure_count":        failure,
			"timeout_count":        timeout,
		}
	}
	return stats
}
