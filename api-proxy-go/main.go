package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/kevin178plus/api-proxy-go/config"
	"github.com/kevin178plus/api-proxy-go/logger"
	"github.com/kevin178plus/api-proxy-go/middleware"
	"github.com/kevin178plus/api-proxy-go/proxy"
	"github.com/kevin178plus/api-proxy-go/stats"
	"github.com/kevin178plus/api-proxy-go/upstream"
	"github.com/kevin178plus/api-proxy-go/web"
)

var (
	configPath = flag.String("config", "config.yaml", "配置文件路径")
	service    = flag.Bool("service", false, "作为 Windows 服务运行")
	version    = "1.0.0"
)

func main() {
	flag.Parse()

	log.Printf("[启动] API 代理 v%s", version)

	// 加载 .env 文件（如果存在）
	loadEnvFile()

	// 加载配置
	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("[错误] 加载配置失败: %v", err)
	}
	config.SetGlobal(cfg)

	log.Printf("[配置] 监听地址: %s", cfg.Listen)
	log.Printf("[配置] 上游目录: %s", cfg.Upstreams.RootDir)
	log.Printf("[配置] 调试模式: %v", cfg.Debug.Enabled)

	// 创建上游管理器
	manager := upstream.NewManager(cfg)
	if err := manager.Load(); err != nil {
		log.Fatalf("[错误] 加载上游配置失败: %v", err)
	}

	// 更新可用列表
	manager.UpdateAvailable()

	// 测试所有上游（异步执行，不阻塞启动）
	log.Printf("[启动] 测试上游服务...")
	go func() {
		manager.TestAll()
		// 测试完成后更新可用列表
		manager.UpdateAvailable()
		log.Printf("[启动] 上游服务测试完成")
	}()

	// 启动健康检查
	healthChecker := upstream.NewHealthChecker(manager)
	healthChecker.Start()
	defer healthChecker.Stop()

	// 创建统计管理器
	statsMgr := stats.NewStatsManager(manager, cfg)

	// 创建 API Key 统计管理器
	keyStatsMgr := stats.NewKeyStatsManager(cfg)

	// 创建代理
	pxy := proxy.NewProxy(cfg, manager, statsMgr, keyStatsMgr)

	// 创建流量日志器（P1-3：轮转参数从配置生效）
	var trafficLogger *logger.TrafficLogger
	if cfg.Debug.Enabled && cfg.Debug.TrafficLog.Enabled {
		trafficLogger = logger.NewTrafficLoggerWithRotation(
			cfg.Debug.TrafficLog.Enabled,
			cfg.Debug.TrafficLog.Path,
			cfg.Debug.TrafficLog.BufferSize,
			cfg.Debug.TrafficLog.RecordBody,
			cfg.Debug.TrafficLog.MaxBodyBytes,
			cfg.Debug.TrafficLog.MaxSizeMB,
			cfg.Debug.TrafficLog.MaxBackups,
			cfg.Debug.TrafficLog.Compress,
		)
		defer trafficLogger.Close()
	}
	_ = trafficLogger // 当前路由层尚未直接调用，保留以兼容后续引用

	// 创建中间件
	authMiddleware := middleware.NewAuth(cfg, keyStatsMgr)
	rateLimitMiddleware := middleware.NewRateLimiter(cfg.RateLimit.RequestsPerSecond)
	defer rateLimitMiddleware.Stop() // 关闭后台清理 goroutine（P0-4）
	loggerMiddleware := middleware.NewLogger()

	// 创建调试页面处理器
	debugHandler := web.NewDebugHandler(cfg, manager, statsMgr, keyStatsMgr)

	// 创建 HTTP 服务器
	mux := http.NewServeMux()

	// 注册路由
	mux.HandleFunc("/v1/chat/completions", pxy.ServeHTTP)
	mux.HandleFunc("/v1/models", pxy.ServeHTTP)
	mux.HandleFunc("/health", pxy.ServeHTTP)

	// 注册调试路由
	if cfg.Debug.Enabled {
		debugHandler.RegisterRoutes(mux)
	}

	// 应用中间件
	handler := loggerMiddleware.Handler(mux)
	if cfg.RateLimit.Enabled {
		handler = rateLimitMiddleware.Handler(handler)
	}
	if cfg.Auth.Enabled {
		handler = authMiddleware.Handler(handler)
	}

	// 创建服务器
	server := &http.Server{
		Addr:         cfg.Listen,
		Handler:      handler,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// 启动配置文件监控（用于优雅重启）
	if err := watchConfig(*configPath); err != nil {
		log.Printf("[警告] 配置文件监控失败: %v", err)
	}

	// 启动服务器
	go func() {
		log.Printf("[启动] 服务器监听 %s", cfg.Listen)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[错误] 服务器启动失败: %v", err)
		}
	}()

	// 等待信号
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	<-sigChan
	log.Printf("[停止] 收到停止信号")

	// 优雅关闭
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Printf("[错误] 服务器关闭失败: %v", err)
	}

	// 停止管理器
	manager.Stop()

	log.Printf("[停止] 服务器已停止")
}

// watchConfig 监控配置文件变化（用于触发优雅重启）
func watchConfig(configPath string) error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return fmt.Errorf("创建文件监控失败: %w", err)
	}

	configDir := filepath.Dir(configPath)
	if err := watcher.Add(configDir); err != nil {
		return fmt.Errorf("添加监控目录失败: %w", err)
	}

	go func() {
		defer watcher.Close()

		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}

				// 检查是否是配置文件
				if event.Name == configPath && (event.Op&fsnotify.Write == fsnotify.Write || event.Op&fsnotify.Create == fsnotify.Create) {
					log.Printf("[重载] 检测到配置文件变化，准备重启...")
					// 延迟重启，避免频繁重启
					time.Sleep(1 * time.Second)
					triggerGracefulRestart()
				}

			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Printf("[错误] 文件监控错误: %v", err)
			}
		}
	}()

	return nil
}

// triggerGracefulRestart 触发优雅重启
func triggerGracefulRestart() {
	log.Printf("[重载] 触发优雅重启...")

	// 发送 SIGTERM 给自己
	p, err := os.FindProcess(os.Getpid())
	if err != nil {
		log.Printf("[错误] 获取进程失败: %v", err)
		return
	}

	if err := p.Signal(syscall.SIGTERM); err != nil {
		log.Printf("[错误] 发送信号失败: %v", err)
		return
	}
}

// Windows 服务支持（简化版本）
// 完整的 Windows 服务支持需要使用 golang.org/x/sys/windows/svc
// 这里提供基本框架

// loadEnvFile 加载 .env 文件（支持项目根目录和当前目录）
func loadEnvFile() {
	// 尝试多个可能的 .env 文件位置
	envPaths := []string{
		".env",                      // 当前目录 (api-proxy-go/)
		"../.env",                   // 上级目录 (项目根目录)
		"../../.env",                // 上上级目录
		"../multi_free_api_proxy/.env",  // 兼容 Python 版本的 .env 位置
		"../../multi_free_api_proxy/.env", // 也尝试这个位置
	}

	// 如果 GOPATH 存在，添加其下的路径
	if goPath := os.Getenv("GOPATH"); goPath != "" {
		envPaths = append(envPaths, goPath+"/src/github.com/kevin178plus/api-proxy-go/.env")
	}

	// 如果 EXE 路径存在，尝试从 EXE 所在目录的上一级加载
	exePath := os.Getenv("EXE_PATH")
	if exePath != "" {
		envPaths = append(envPaths, filepath.Dir(exePath)+"/.env")
	}

	for _, envPath := range envPaths {
		if _, err := os.Stat(envPath); err == nil {
			log.Printf("[配置] 加载环境变量: %s", envPath)
			loadEnv(envPath)
			return
		}
	}

	// 如果没有 .env 文件，尝试从项目根目录加载
	projectRoot := ".env"
	if _, err := os.Stat(projectRoot); err == nil {
		loadEnv(projectRoot)
	}
}

// loadEnv 解析 .env 文件并设置环境变量
func loadEnv(path string) {
	file, err := os.Open(path)
	if err != nil {
		log.Printf("[警告] 打开环境变量文件失败: %v", err)
		return
	}
	defer file.Close()

	lineNum := 0
	skipped := 0

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// 跳过空行和注释
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// 解析 KEY=VALUE 格式
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			log.Printf("[警告] 第 %d 行格式错误: %s", lineNum, line)
			skipped++
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		// 跳过 PORT、CACHE_DIR、MAX_CONCURRENT_REQUESTS（这些在 config.yaml 中配置）
		// HTTP_PROXY 需要设置，因为 config.go 会读取它用于代理
		if key == "PORT" || key == "CACHE_DIR" || key == "MAX_CONCURRENT_REQUESTS" {
			continue
		}

		os.Setenv(key, value)
	}

	if err := scanner.Err(); err != nil {
		log.Printf("[警告] 读取环境变量文件失败: %v", err)
	}

	log.Printf("[配置] 已加载 %d 个环境变量 (跳过 %d 个)", lineNum-skipped, skipped)
}

/*
type service struct {
	wg sync.WaitGroup
}

func (s *service) Execute(args []string, r <-chan svc.ChangeRequest, changes chan<- svc.Status) (ssec bool, errno uint32) {
	const cmdsAccepted = svc.AcceptStop | svc.AcceptShutdown | svc.AcceptPauseAndContinue
	changes <- svc.Status{State: svc.StartPending}

	// TODO: 实现服务逻辑

	changes <- svc.Status{State: svc.Running, Accepts: cmdsAccepted}
loop:
	for {
		select {
		case c := <-r:
			switch c.Cmd {
			case svc.Interrogate:
				changes <- c.CurrentStatus
			case svc.Stop, svc.Shutdown:
				// 优雅关闭
				changes <- svc.Status{State: svc.StopPending}
				break loop
			case svc.Pause:
				changes <- svc.Status{State: svc.Paused, Accepts: cmdsAccepted}
			case svc.Continue:
				changes <- svc.Status{State: svc.Running, Accepts: cmdsAccepted}
			default:
				log.Printf("[服务] 未知命令: %d", c.Cmd)
			}
		}
	}
	changes <- svc.Status{State: svc.Stopped}
	return false, 0
}
*/