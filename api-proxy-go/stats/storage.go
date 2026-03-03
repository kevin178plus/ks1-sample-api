package stats

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Storage 统计数据存储
type Storage struct {
	baseDir string
	mu      sync.RWMutex
}

// NewStorage 创建存储
func NewStorage(baseDir string) (*Storage, error) {
	// 确保目录存在
	if err := os.MkdirAll(baseDir, 0755); err != nil {
		return nil, fmt.Errorf("创建存储目录失败: %w", err)
	}

	return &Storage{
		baseDir: baseDir,
	}, nil
}

// SaveDailyStats 保存每日统计
func (s *Storage) SaveDailyStats(date string, data map[string]interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filename := filepath.Join(s.baseDir, fmt.Sprintf("STATS_%s.json", date))

	fileData := map[string]interface{}{
		"date":         date,
		"stats":        data,
		"last_updated": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.MarshalIndent(fileData, "", "  ")
	if err != nil {
		return fmt.Errorf("序列化统计失败: %w", err)
	}

	if err := os.WriteFile(filename, jsonData, 0644); err != nil {
		return fmt.Errorf("写入统计文件失败: %w", err)
	}

	return nil
}

// LoadDailyStats 加载每日统计
func (s *Storage) LoadDailyStats(date string) (map[string]interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	filename := filepath.Join(s.baseDir, fmt.Sprintf("STATS_%s.json", date))

	data, err := os.ReadFile(filename)
	if err != nil {
		if os.IsNotExist(err) {
			// 文件不存在，返回空数据
			return map[string]interface{}{
				"date":  date,
				"stats": map[string]interface{}{},
			}, nil
		}
		return nil, fmt.Errorf("读取统计文件失败: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("解析统计文件失败: %w", err)
	}

	return result, nil
}

// SaveKeyStats 保存 API Key 统计
func (s *Storage) SaveKeyStats(date string, data map[string]interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filename := filepath.Join(s.baseDir, fmt.Sprintf("KEY_STATS_%s.json", date))

	fileData := map[string]interface{}{
		"date":         date,
		"stats":        data,
		"last_updated": time.Now().Format(time.RFC3339),
	}

	jsonData, err := json.MarshalIndent(fileData, "", "  ")
	if err != nil {
		return fmt.Errorf("序列化 API Key 统计失败: %w", err)
	}

	if err := os.WriteFile(filename, jsonData, 0644); err != nil {
		return fmt.Errorf("写入 API Key 统计文件失败: %w", err)
	}

	return nil
}

// LoadKeyStats 加载 API Key 统计
func (s *Storage) LoadKeyStats(date string) (map[string]interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	filename := filepath.Join(s.baseDir, fmt.Sprintf("KEY_STATS_%s.json", date))

	data, err := os.ReadFile(filename)
	if err != nil {
		if os.IsNotExist(err) {
			// 文件不存在，返回空数据
			return map[string]interface{}{
				"date":  date,
				"stats": map[string]interface{}{},
			}, nil
		}
		return nil, fmt.Errorf("读取 API Key 统计文件失败: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("解析 API Key 统计文件失败: %w", err)
	}

	return result, nil
}

// GetTodayDate 获取今天的日期字符串
func GetTodayDate() string {
	return time.Now().Format("20060102")
}

// GetYesterdayDate 获取昨天的日期字符串
func GetYesterdayDate() string {
	return time.Now().AddDate(0, 0, -1).Format("20060102")
}