package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
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

	// 创建流量日志器
	var trafficLogger *logger.TrafficLogger
	if cfg.Debug.Enabled && cfg.Debug.TrafficLog.Enabled {
		trafficLogger = logger.NewTrafficLogger(
			cfg.Debug.TrafficLog.Enabled,
			cfg.Debug.TrafficLog.Path,
			cfg.Debug.TrafficLog.BufferSize,
			cfg.Debug.TrafficLog.RecordBody,
			cfg.Debug.TrafficLog.MaxBodyBytes,
		)
		defer trafficLogger.Close()
	}

	// 创建中间件
	authMiddleware := middleware.NewAuth(cfg, keyStatsMgr)
	rateLimitMiddleware := middleware.NewRateLimiter(cfg.RateLimit.RequestsPerSecond)
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