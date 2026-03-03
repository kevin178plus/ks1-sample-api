package config

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"gopkg.in/yaml.v3"
)

var (
	globalConfig atomicConfig
	configMutex  sync.RWMutex
)

// atomicConfig 原子配置（用于安全读取）
type atomicConfig struct {
	value *Config
}

// Load 加载配置文件
func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	cfg := DefaultConfig()
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %w", err)
	}

	// 验证配置
	if err := validateConfig(cfg); err != nil {
		return nil, fmt.Errorf("配置验证失败: %w", err)
	}

	return cfg, nil
}

// validateConfig 验证配置
func validateConfig(cfg *Config) error {
	// 验证权重配置
	if cfg.Weight.SpecialThreshold < 1 {
		return fmt.Errorf("special_threshold 必须 >= 1")
	}
	if cfg.Weight.MinAutoDecrease < 0 || cfg.Weight.MinAutoDecrease > cfg.Weight.SpecialThreshold {
		return fmt.Errorf("min_auto_decrease 必须在 0 和 special_threshold 之间")
	}

	// 验证健康检查配置
	if cfg.HealthCheck.Interval <= 0 {
		return fmt.Errorf("health_check.interval 必须 > 0")
	}

	// 验证限流配置
	if cfg.RateLimit.Enabled && cfg.RateLimit.RequestsPerSecond <= 0 {
		return fmt.Errorf("rate_limit.requests_per_second 必须 > 0")
	}

	return nil
}

// SetGlobal 设置全局配置（原子操作）
func SetGlobal(cfg *Config) {
	configMutex.Lock()
	defer configMutex.Unlock()
	globalConfig.value = cfg
}

// GetGlobal 获取全局配置（原子操作）
func GetGlobal() *Config {
	configMutex.RLock()
	defer configMutex.RUnlock()
	return globalConfig.value
}

// LoadUpstreamConfig 加载单个上游配置文件
func LoadUpstreamConfig(path string) (*UpstreamConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取上游配置失败: %w", err)
	}

	cfg := &UpstreamConfig{}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("解析上游配置失败: %w", err)
	}

	// 设置默认值
	if cfg.DefaultWeight == 0 {
		cfg.DefaultWeight = 10
	}
	if cfg.MaxTokens == 0 {
		cfg.MaxTokens = 2000
	}
	if cfg.Thresholds.Warning == 0 {
		cfg.Thresholds.Warning = 80
	}
	if cfg.Thresholds.Critical == 0 {
		cfg.Thresholds.Critical = 95
	}

	return cfg, nil
}

// DiscoverUpstreams 扫描上游配置目录
func DiscoverUpstreams(rootDir string) (map[string]*UpstreamConfig, error) {
	upstreams := make(map[string]*UpstreamConfig)

	entries, err := os.ReadDir(rootDir)
	if err != nil {
		if os.IsNotExist(err) {
			// 目录不存在，返回空 map
			return upstreams, nil
		}
		return nil, fmt.Errorf("读取上游目录失败: %w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		name := entry.Name()
		configPath := filepath.Join(rootDir, name, "config.yaml")

		// 尝试加载 config.yaml
		cfg, err := LoadUpstreamConfig(configPath)
		if err != nil {
			// 跳过没有 config.yaml 的目录
			continue
		}

		cfg.Name = name
		upstreams[name] = cfg
	}

	return upstreams, nil
}

// SaveConfig 保存配置到文件
func SaveConfig(cfg *Config, path string) error {
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("序列化配置失败: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}

	return nil
}