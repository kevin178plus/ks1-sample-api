package config

import (
	"testing"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Listen != ":8080" {
		t.Errorf("Expected listen :8080, got %s", cfg.Listen)
	}

	if cfg.Upstreams.RootDir != "./upstreams" {
		t.Errorf("Expected root_dir ./upstreams, got %s", cfg.Upstreams.RootDir)
	}

	if cfg.Auth.Enabled {
		t.Error("Expected auth.enabled to be false")
	}

	if cfg.Weight.SpecialThreshold != 100 {
		t.Errorf("Expected special_threshold 100, got %d", cfg.Weight.SpecialThreshold)
	}
}

func TestValidateConfig(t *testing.T) {
	cfg := DefaultConfig()

	// 测试有效配置
	if err := validateConfig(cfg); err != nil {
		t.Errorf("Expected valid config, got error: %v", err)
	}

	// 测试无效的 special_threshold
	invalidCfg := DefaultConfig()
	invalidCfg.Weight.SpecialThreshold = 0
	if err := validateConfig(invalidCfg); err == nil {
		t.Error("Expected error for invalid special_threshold")
	}

	// 测试无效的 min_auto_decrease
	invalidCfg2 := DefaultConfig()
	invalidCfg2.Weight.MinAutoDecrease = 150
	if err := validateConfig(invalidCfg2); err == nil {
		t.Error("Expected error for invalid min_auto_decrease")
	}
}

func TestLoadUpstreamConfig(t *testing.T) {
	// 这个测试需要实际的上游配置文件
	// 这里只测试函数签名是否正确
	cfg, err := LoadUpstreamConfig("nonexistent.yaml")
	if err == nil {
		t.Error("Expected error for nonexistent file")
	}
	if cfg != nil {
		t.Error("Expected nil config for error")
	}
}