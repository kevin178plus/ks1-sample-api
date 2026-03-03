package config

import "time"

// Config 主配置结构
type Config struct {
	Listen      string             `yaml:"listen"`       // 监听地址，如 ":8080"
	Upstreams   UpstreamsConfig    `yaml:"upstreams"`    // 上游配置
	Auth        AuthConfig         `yaml:"auth"`         // 认证配置
	RateLimit   RateLimitConfig    `yaml:"rate_limit"`   // 限流配置
	Debug       DebugConfig        `yaml:"debug"`        // 调试配置
	HealthCheck HealthCheckConfig  `yaml:"health_check"` // 健康检查配置
	Weight      WeightConfig       `yaml:"weight"`       // 权重配置
}

// UpstreamsConfig 上游服务配置
type UpstreamsConfig struct {
	RootDir string `yaml:"root_dir"` // 上游配置根目录，如 "./upstreams"
}

// AuthConfig 认证配置
type AuthConfig struct {
	Enabled      bool     `yaml:"enabled"`       // 是否启用认证
	Keys         []string `yaml:"keys"`          // API Key 白名单，为空则允许所有
	KeyLimit     bool     `yaml:"key_limit"`     // 是否启用按密钥限额统计
	DefaultLimit int      `yaml:"default_limit"` // 默认限额（调用次数）
}

// RateLimitConfig 限流配置
type RateLimitConfig struct {
	Enabled           bool `yaml:"enabled"`            // 是否启用限流
	RequestsPerSecond int  `yaml:"requests_per_second"` // 每秒请求数限制
}

// DebugConfig 调试配置
type DebugConfig struct {
	Enabled      bool           `yaml:"enabled"`       // 是否启用调试模式
	TrafficLog   TrafficLogConf `yaml:"traffic_log"`   // 流量日志配置
	CacheDir     string         `yaml:"cache_dir"`     // 缓存目录
}

// TrafficLogConf 流量日志配置
type TrafficLogConf struct {
	Enabled      bool   `yaml:"enabled"`        // 是否启用流量日志
	Path         string `yaml:"path"`           // 日志文件路径
	MaxSizeMB    int    `yaml:"max_size_mb"`    // 最大文件大小（MB）
	MaxBackups   int    `yaml:"max_backups"`    // 最多保留备份文件数
	Compress     bool   `yaml:"compress"`       // 是否压缩旧日志
	BufferSize   int    `yaml:"buffer_size"`    // 缓冲区大小
	RecordBody   bool   `yaml:"record_body"`    // 是否记录 Body
	MaxBodyBytes int    `yaml:"max_body_bytes"` // Body 最大记录字节数
}

// HealthCheckConfig 健康检查配置
type HealthCheckConfig struct {
	Enabled    bool          `yaml:"enabled"`    // 是否启用健康检查
	Interval   time.Duration `yaml:"interval"`   // 检查间隔，默认 12 小时
	Timeout    time.Duration `yaml:"timeout"`    // 检查超时时间
	MaxFailures int          `yaml:"max_failures"` // 最大连续失败次数
}

// WeightConfig 权重配置
type WeightConfig struct {
	SpecialThreshold int `yaml:"special_threshold"` // 特别权重阈值，>100 次必然选中
	MinAutoDecrease  int `yaml:"min_auto_decrease"`  // 自动减少权重的下限
}

// UpstreamConfig 单个上游配置（从 YAML 文件加载）
type UpstreamConfig struct {
	Name             string            `yaml:"name"`               // 上游名称
	Address          string            `yaml:"address"`            // 服务地址
	APIKey           string            `yaml:"api_key"`            // API Key
	Enabled          bool              `yaml:"enabled"`            // 是否启用
	DefaultWeight    int               `yaml:"default_weight"`     // 默认权重
	Limit            UpstreamLimit     `yaml:"limit"`              // 限额配置
	Webhook          string            `yaml:"webhook"`            // Webhook 通知 URL
	Thresholds       ThresholdConfig   `yaml:"thresholds"`         // 阈值配置
	UseProxy         bool              `yaml:"use_proxy"`          // 是否使用代理
	UseSDK           bool              `yaml:"use_sdk"`            // 是否使用 SDK
	AvailableModels  []string          `yaml:"available_models"`   // 可用模型列表
	UseWeightedModel bool              `yaml:"use_weighted_model"` // 是否使用模型权重
	ResponseFormat   ResponseFormat    `yaml:"response_format"`    // 响应格式配置
	MaxTokens        int               `yaml:"max_tokens"`         // 最大 token 数
	Model            string            `yaml:"model"`              // 默认模型
}

// UpstreamLimit 上游限额配置
type UpstreamLimit struct {
	Hourly  int `yaml:"hourly"`  // 每小时限额
	Daily   int `yaml:"daily"`   // 每天限额
	Monthly int `yaml:"monthly"` // 每月限额
}

// ThresholdConfig 阈值配置
type ThresholdConfig struct {
	Warning  int `yaml:"warning"`  // 警告阈值（百分比）
	Critical int `yaml:"critical"` // 严重阈值（百分比）
}

// ResponseFormat 响应格式配置
type ResponseFormat struct {
	ContentFields          []string `yaml:"content_fields"`            // 内容字段优先级
	MergeFields            bool     `yaml:"merge_fields"`              // 是否合并字段
	FieldSeparator         string   `yaml:"field_separator"`           // 字段分隔符
	UseReasoningAsFallback bool     `yaml:"use_reasoning_as_fallback"` // 是否使用 reasoning 作为后备
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Listen: ":8080",
		Upstreams: UpstreamsConfig{
			RootDir: "./upstreams",
		},
		Auth: AuthConfig{
			Enabled:      false,
			Keys:         []string{},
			KeyLimit:     false,
			DefaultLimit: 1000,
		},
		RateLimit: RateLimitConfig{
			Enabled:           false,
			RequestsPerSecond: 10,
		},
		Debug: DebugConfig{
			Enabled: false,
			TrafficLog: TrafficLogConf{
				Enabled:      false,
				Path:         "./logs/traffic.json",
				MaxSizeMB:    100,
				MaxBackups:   3,
				Compress:     true,
				BufferSize:   1000,
				RecordBody:   true,
				MaxBodyBytes: 1024,
			},
			CacheDir: "./cache",
		},
		HealthCheck: HealthCheckConfig{
			Enabled:     true,
			Interval:    12 * time.Hour,
			Timeout:     30 * time.Second,
			MaxFailures: 3,
		},
		Weight: WeightConfig{
			SpecialThreshold: 100,
			MinAutoDecrease:  50,
		},
	}
}