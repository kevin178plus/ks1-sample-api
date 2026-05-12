package config

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
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

	// 验证代理 / 重试配置（P1-2）
	if cfg.Proxy.MaxRetries <= 0 {
		cfg.Proxy.MaxRetries = 3
	}
	if cfg.Proxy.MaxRetries > 20 {
		return fmt.Errorf("proxy.max_retries 过大: %d (建议 <=20)", cfg.Proxy.MaxRetries)
	}
	if cfg.Proxy.RetryBackoffBaseMS <= 0 {
		cfg.Proxy.RetryBackoffBaseMS = 1000
	}

	// 从环境变量加载代理配置
	loadProxyFromEnv(cfg)

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

	// 从环境变量加载 API Key
	loadAPIKeyFromEnv(cfg)

	return cfg, nil
}

// loadProxyFromEnv 从环境变量加载代理配置
// 支持的环境变量：HTTP_PROXY, HTTPS_PROXY, PROXY_URL
func loadProxyFromEnv(cfg *Config) {
	// 优先级：HTTP_PROXY > PROXY_URL
	if proxy := os.Getenv("HTTP_PROXY"); proxy != "" {
		cfg.Proxy.HTTPProxy = proxy
		log.Printf("[配置] 从环境变量 HTTP_PROXY 加载代理: %s", proxy)
	} else if proxy := os.Getenv("PROXY_URL"); proxy != "" {
		cfg.Proxy.HTTPProxy = proxy
		log.Printf("[配置] 从环境变量 PROXY_URL 加载代理: %s", proxy)
	}
	// 打印最终使用的代理配置
	if cfg.Proxy.HTTPProxy != "" {
		log.Printf("[配置] 全局 HTTP 代理已配置: %s", cfg.Proxy.HTTPProxy)
	} else {
		log.Printf("[配置] 未配置全局 HTTP 代理")
	}
}

// loadAPIKeyFromEnv 从环境变量加载 API Key
// 支持的环境变量格式：
//   - FREE1_API_KEY, FREE2_API_KEY, ... (通用)
//   - OPENROUTER_API_KEY (free1)
//   - GROQ_API_KEY (free15)
//   - SAMBANOVA_API_KEY (free16)
//   - CEREBRAS_API_KEY (free17)
//   - GEMINI_API_KEY (free18)
//   - NVIDIA_API_KEY (free7)
func loadAPIKeyFromEnv(cfg *UpstreamConfig) {
	if cfg.APIKey != "" {
		// 如果 YAML 中已有 API Key，优先使用
		return
	}

	name := cfg.Name
	if name == "" {
		return
	}

	// 映射表：上游名称 -> 环境变量名
	envVars := map[string]string{
		"free1":  "FREE1_API_KEY", // OpenRouter
		"free2":  "FREE2_API_KEY",
		"free3":  "FREE3_API_KEY",
		"free4":  "FREE4_API_KEY",
		"free5":  "FREE5_API_KEY", // iFlow SDK (已停用)
		"free6":  "FREE6_API_KEY",
		"free7":  "NVIDIA_API_KEY", // NVIDIA
		"free8":  "FREE8_API_KEY", // Friendli
		"free9":  "FREE9_API_KEY", // 火山方舟 (已过期)
		"free10": "FREE10_API_KEY",
		"free11": "FREE11_API_KEY",
		"free12": "FREE12_API_KEY",
		"free13": "FREE13_API_KEY",
		"free14": "FREE14_API_KEY",
		"free15": "GROQ_API_KEY", // Groq
		"free16": "SAMBANOVA_API_KEY", // Sambanova
		"free17": "CEREBRAS_API_KEY", // Cerebras
		"free18": "GEMINI_API_KEY", // Google Gemini
		"free19": "COHERE_API_KEY", // Cohere
		"free20": "LONGCAT_API_KEY", // LongCat API
	}

	envKey, exists := envVars[name]
	if !exists {
		// 尝试通用格式 FREE{N}_API_KEY
		envKey = strings.ToUpper(name) + "_API_KEY"
	}

	if apiKey := os.Getenv(envKey); apiKey != "" {
		cfg.APIKey = apiKey
		log.Printf("[配置] %s: 从环境变量 %s 加载 API Key (长度: %d)", name, envKey, len(apiKey))
	} else {
		log.Printf("[配置] %s: 未找到 API Key (环境变量 %s 为空)", name, envKey)
	}
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
		return nil, fmt.Errorf("读取上游目录失败：%w", err)
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		name := entry.Name()

		// 跳过以下划线开头的目录（示例/禁用配置）
		if strings.HasPrefix(name, "_") {
			log.Printf("[配置] 跳过目录 %s (以下划线开头，视为示例/禁用)", name)
			continue
		}

		configPath := filepath.Join(rootDir, name, "config.yaml")

		// 尝试加载 config.yaml
		cfg, err := LoadUpstreamConfig(configPath)
		if err != nil {
			// 跳过没有 config.yaml 的目录
			continue
		}

		cfg.Name = name

		// P1-4：SDK 模式尚未实现，加载阶段直接拒绝并提示，避免运行时 500
		if cfg.UseSDK {
			log.Printf("[配置][警告] 上游 %s 配置 use_sdk=true，但 SDK 模式尚未实现，已自动降级为 HTTP 模式", name)
			cfg.UseSDK = false
		}

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