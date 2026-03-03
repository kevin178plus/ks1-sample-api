package proxy

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/kevin178plus/api-proxy-go/upstream"
)

// FailoverHandler 失效转移处理器
type FailoverHandler struct {
	manager  *upstream.Manager
	selector *upstream.Selector
	maxTries int
}

// NewFailoverHandler 创建失效转移处理器
func NewFailoverHandler(manager *upstream.Manager, selector *upstream.Selector, maxTries int) *FailoverHandler {
	return &FailoverHandler{
		manager:  manager,
		selector: selector,
		maxTries: maxTries,
	}
}

// Execute 执行请求（带失效转移）
func (fh *FailoverHandler) Execute(ctx context.Context, reqData map[string]interface{}, apiKey string, executeFunc func(string) (map[string]interface{}, error)) (map[string]interface{}, string, error) {
	var lastErr error
	var triedUpstreams []string

	for attempt := 0; attempt < fh.maxTries; attempt++ {
		// 选择上游
		upstreamName, err := fh.selector.Select()
		if err != nil {
			return nil, "", fmt.Errorf("no available upstream: %w", err)
		}

		// 检查是否已经尝试过
		alreadyTried := false
		for _, tried := range triedUpstreams {
			if tried == upstreamName {
				alreadyTried = true
				break
			}
		}
		if alreadyTried {
			continue
		}

		triedUpstreams = append(triedUpstreams, upstreamName)

		// 执行请求
		result, err := executeFunc(upstreamName)
		if err != nil {
			lastErr = err

			// 标记失败
			fh.manager.MarkFailure(upstreamName)

			// 检查是否超时
			if isTimeoutError(err) {
				fh.manager.MarkTimeout(upstreamName)
			}

			// 记录日志
			log.Printf("[失效转移] %s 失败: %v (尝试 %d/%d, 已尝试: %v)",
				upstreamName, err, attempt+1, fh.maxTries, triedUpstreams)

			// 等待后重试
			if attempt < fh.maxTries-1 {
				waitTime := time.Duration(1<<attempt) * time.Second
				log.Printf("[失效转移] %v 后重试...", waitTime)
				time.Sleep(waitTime)
			}

			continue
		}

		// 标记成功
		fh.manager.MarkSuccess(upstreamName)

		// 如果有连续失败历史，记录恢复
		stat := fh.manager.GetStat(upstreamName)
		if stat != nil {
			_, _, _, consecutive := stat.GetStats()
			if consecutive > 0 {
				log.Printf("[失效转移] %s 已恢复 (之前连续失败 %d 次)", upstreamName, consecutive)
			}
		}

		return result, upstreamName, nil
	}

	// 所有尝试都失败
	return nil, "", fmt.Errorf("all retries failed (tried: %v): %w", triedUpstreams, lastErr)
}

// GetFailoverStats 获取失效转移统计
func (fh *FailoverHandler) GetFailoverStats() map[string]interface{} {
	upstreams := fh.manager.GetAll()

	stats := make(map[string]interface{})
	for name, _ := range upstreams {
		stat := fh.manager.GetStat(name)
		if stat != nil {
			_, _, _, consecutive := stat.GetStats()
			success, failure, timeout := stat.GetHistoryStats()
			stats[name] = map[string]interface{}{
				"consecutive_failures": consecutive,
				"success_count":        success,
				"failure_count":        failure,
				"timeout_count":        timeout,
			}
		}
	}

	return stats
}