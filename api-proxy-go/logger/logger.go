package logger

import (
	"log"
	"os"
)

// Logger 结构化日志器
type Logger struct {
	infoLogger  *log.Logger
	warnLogger  *log.Logger
	errorLogger *log.Logger
	debugLogger *log.Logger
}

// NewLogger 创建日志器
func NewLogger() *Logger {
	return &Logger{
		infoLogger:  log.New(os.Stdout, "[INFO] ", log.LstdFlags),
		warnLogger:  log.New(os.Stdout, "[WARN] ", log.LstdFlags),
		errorLogger: log.New(os.Stderr, "[ERROR] ", log.LstdFlags),
		debugLogger: log.New(os.Stdout, "[DEBUG] ", log.LstdFlags),
	}
}

// Info 记录信息
func (l *Logger) Info(format string, v ...interface{}) {
	l.infoLogger.Printf(format, v...)
}

// Warn 记录警告
func (l *Logger) Warn(format string, v ...interface{}) {
	l.warnLogger.Printf(format, v...)
}

// Error 记录错误
func (l *Logger) Error(format string, v ...interface{}) {
	l.errorLogger.Printf(format, v...)
}

// Debug 记录调试信息
func (l *Logger) Debug(format string, v ...interface{}) {
	l.debugLogger.Printf(format, v...)
}

// InfoWithFields 记录带字段的信息
func (l *Logger) InfoWithFields(fields map[string]interface{}, format string, v ...interface{}) {
	l.Info(format, v...)
	// TODO: 实现结构化日志
}

// WarnWithFields 记录带字段的警告
func (l *Logger) WarnWithFields(fields map[string]interface{}, format string, v ...interface{}) {
	l.Warn(format, v...)
	// TODO: 实现结构化日志
}

// ErrorWithFields 记录带字段的错误
func (l *Logger) ErrorWithFields(fields map[string]interface{}, format string, v ...interface{}) {
	l.Error(format, v...)
	// TODO: 实现结构化日志
}

// DebugWithFields 记录带字段的调试信息
func (l *Logger) DebugWithFields(fields map[string]interface{}, format string, v ...interface{}) {
	l.Debug(format, v...)
	// TODO: 实现结构化日志
}