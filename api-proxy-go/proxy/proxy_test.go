package proxy

import (
	"net/http"
	"testing"

	"github.com/kevin178plus/api-proxy-go/config"
)

func newTestProxy(trusted []string) *Proxy {
	cfg := config.DefaultConfig()
	cfg.Proxy.TrustedProxies = trusted
	return &Proxy{config: cfg}
}

func makeReq(remote, xff, xri string) *http.Request {
	r, _ := http.NewRequest("GET", "/v1/models", nil)
	r.RemoteAddr = remote
	if xff != "" {
		r.Header.Set("X-Forwarded-For", xff)
	}
	if xri != "" {
		r.Header.Set("X-Real-IP", xri)
	}
	return r
}

func TestIsClientLocalhost_DirectLoopback(t *testing.T) {
	p := newTestProxy(nil)
	cases := []string{"127.0.0.1:1234", "[::1]:5678", "[::1]:0"}
	for _, addr := range cases {
		if !p.isClientLocalhost(makeReq(addr, "", "")) {
			t.Errorf("addr=%s 应被允许", addr)
		}
	}
}

func TestIsClientLocalhost_NonLoopback_NoTrustedProxies(t *testing.T) {
	p := newTestProxy(nil)
	if p.isClientLocalhost(makeReq("8.8.8.8:80", "127.0.0.1", "")) {
		t.Error("无可信代理时不应信任 XFF")
	}
}

func TestIsClientLocalhost_TrustedProxyWithLoopbackXFF(t *testing.T) {
	p := newTestProxy([]string{"10.0.0.5"})
	r := makeReq("10.0.0.5:443", "127.0.0.1", "")
	if !p.isClientLocalhost(r) {
		t.Error("可信代理 + XFF=loopback 应被允许")
	}
}

func TestIsClientLocalhost_TrustedProxyWithRemoteXFF(t *testing.T) {
	p := newTestProxy([]string{"10.0.0.5"})
	r := makeReq("10.0.0.5:443", "8.8.8.8", "")
	if p.isClientLocalhost(r) {
		t.Error("可信代理但 XFF=远端 IP，不应被允许")
	}
}

func TestIsClientLocalhost_TrustedProxyCIDR(t *testing.T) {
	p := newTestProxy([]string{"10.0.0.0/24"})
	r := makeReq("10.0.0.42:443", "127.0.0.1", "")
	if !p.isClientLocalhost(r) {
		t.Error("CIDR 命中代理 + 本地 XFF 应允许")
	}
	r2 := makeReq("10.0.1.1:443", "127.0.0.1", "") // 不在 CIDR 范围
	if p.isClientLocalhost(r2) {
		t.Error("不在 CIDR 范围内的代理不应被信任")
	}
}

func TestIsClientLocalhost_XForwardedForChain(t *testing.T) {
	p := newTestProxy([]string{"10.0.0.5"})
	// 链式 XFF：原始客户端在最左
	r := makeReq("10.0.0.5:443", "127.0.0.1, 10.0.0.5", "")
	if !p.isClientLocalhost(r) {
		t.Error("XFF 链最左为 loopback 应被允许")
	}
}

func TestIsClientLocalhost_XRealIPFallback(t *testing.T) {
	p := newTestProxy([]string{"10.0.0.5"})
	r := makeReq("10.0.0.5:443", "", "127.0.0.1")
	if !p.isClientLocalhost(r) {
		t.Error("X-Real-IP=loopback 应被允许")
	}
}

func TestMinInt(t *testing.T) {
	if minInt(3, 5) != 3 || minInt(5, 3) != 3 || minInt(4, 4) != 4 {
		t.Fatal("minInt 行为异常")
	}
}
