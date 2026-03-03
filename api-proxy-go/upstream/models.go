package upstream

import (
	"encoding/json"
	"fmt"
	"github.com/kevin178plus/api-proxy-go/config"
)

// ModelInfo 模型信息
type ModelInfo struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Upstream string `json:"upstream"`
}

// ModelSelector 模型选择器
type ModelSelector struct {
	manager *Manager
}

// NewModelSelector 创建模型选择器
func NewModelSelector(manager *Manager) *ModelSelector {
	return &ModelSelector{
		manager: manager,
	}
}

// GetModel 获取模型（根据上游配置）
func (ms *ModelSelector) GetModel(upstreamName string) string {
	selector := NewSelector(ms.manager)
	return selector.SelectModel(upstreamName)
}

// ListModels 列出所有可用模型
func (ms *ModelSelector) ListModels() []ModelInfo {
	models := make([]ModelInfo, 0)

	upstreams := ms.manager.GetAll()
	for name, upstream := range upstreams {
		cfg := upstream.Config

		// 如果有多模型列表
		if len(cfg.AvailableModels) > 0 {
			for _, model := range cfg.AvailableModels {
				models = append(models, ModelInfo{
					ID:       model,
					Name:     model,
					Upstream: name,
				})
			}
		} else if cfg.Model != "" {
			// 使用默认模型
			models = append(models, ModelInfo{
				ID:       cfg.Model,
				Name:     cfg.Model,
				Upstream: name,
			})
		}
	}

	return models
}

// GetModelInfo 获取模型信息
func (ms *ModelSelector) GetModelInfo(modelID string) (*ModelInfo, error) {
	upstreams := ms.manager.GetAll()

	for name, upstream := range upstreams {
		cfg := upstream.Config

		// 检查多模型列表
		if len(cfg.AvailableModels) > 0 {
			for _, model := range cfg.AvailableModels {
				if model == modelID {
					return &ModelInfo{
						ID:       model,
						Name:     model,
						Upstream: name,
					}, nil
				}
			}
		}

		// 检查默认模型
		if cfg.Model == modelID {
			return &ModelInfo{
				ID:       cfg.Model,
				Name:     cfg.Model,
				Upstream: name,
			}, nil
		}
	}

	return nil, fmt.Errorf("model not found: %s", modelID)
}

// ParseResponseContent 解析响应内容（根据响应格式配置）
func ParseResponseContent(respData map[string]interface{}, format *config.ResponseFormat) (string, error) {
	// 提取 choices
	choices, ok := respData["choices"].([]interface{})
	if !ok || len(choices) == 0 {
		return "", fmt.Errorf("no choices in response")
	}

	choice, ok := choices[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("invalid choice format")
	}

	message, ok := choice["message"].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("invalid message format")
	}

	// 尝试从字段列表中提取内容
	var contents []string
	for _, field := range format.ContentFields {
		if value, exists := message[field]; exists {
			if str, ok := value.(string); ok && str != "" {
				contents = append(contents, str)
			}
		}
	}

	// 如果所有字段都为空，尝试使用 reasoning_content
	if len(contents) == 0 && format.UseReasoningAsFallback {
		if reasoning, exists := message["reasoning_content"]; exists {
			if str, ok := reasoning.(string); ok && str != "" {
				contents = append(contents, str)
			}
		}
	}

	// 合并或返回第一个
	if format.MergeFields && len(contents) > 0 {
		sep := format.FieldSeparator
		if sep == "" {
			sep = "\n\n---\n\n"
		}
		result := ""
		for i, c := range contents {
			if i > 0 {
				result += sep
			}
			result += c
		}
		return result, nil
	}

	if len(contents) > 0 {
		return contents[0], nil
	}

	// 返回原始 JSON
	jsonData, _ := json.Marshal(respData)
	return string(jsonData), nil
}