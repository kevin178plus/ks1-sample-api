"""
生成 ks1-simple-api 系列信息图 - 图2: 双引擎架构对比
"""
import os, requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代的技术信息图，主题为「ks1-simple-api 双引擎架构对比」。深色科技风背景（深蓝到紫黑渐变），左右分栏设计，左侧Python主题色（浅蓝#64B5F6），右侧Go主题色（青绿#26A69A），中间用渐变分隔线。

【顶部标题区】
居中大标题：「双引擎架构」
副标题：「Python Flask vs Go — 各有所长」

【左侧 — Python引擎区（浅蓝色调）】
顶部图标：Python蛇形logo + Flask杯子图标
标题：「Python Flask 引擎」
端口标签：「端口 5000」

核心特性（4个标签，带小图标）：
🔧 自动热重载 — 修改配置自动生效
📡 文件监控 — Watchdog实时监测
🌐 调试面板 — 网页实时查看状态
🛡️ 守护进程 — 异常自动重启

优势标签（绿色底）：
「灵活 · 易调试 · 生态丰富」

【右侧 — Go引擎区（青绿色调）】
顶部图标：Go语言gopher形象
标题：「Go 高性能引擎」
端口标签：「端口 8080 / 5060」

核心特性（4个标签，带小图标）：
⚡ 优雅重启 — 配置变更<3秒完成
🏥 健康检查 — 每5分钟自动检测
📊 限额统计 — 按上游+API Key统计
🔐 白名单认证 — API Key访问控制

优势标签（绿色底）：
「高性能 · 低内存 · 并发强」

【中间 — 差异对比区（白色小卡片）】
一个小卡片，标题「关键差异」，3行对比：
健康检查 → Python: 仅启动时 ｜ Go: 每5分钟周期
配置加载 → Python: 完全重启 ｜ Go: 优雅重启<3s
API认证  → Python: 不支持 ｜ Go: 支持白名单

【底部 — 推荐建议】
左侧（浅蓝底）：「本地开发 / 调试测试 → 推荐 Python」
右侧（青绿底）：「生产部署 / 高并发 → 推荐 Go」
中间箭头：「两者可并行运行，互不干扰」

设计要点：
- 左右对称布局，视觉平衡
- 数字和标签用大字号突出
- 图标简洁扁平化
- 中间对比区用白色卡片突出差异
- 底部推荐用色块区分
- 所有文字清晰可读，无拥挤
- 整体适合 2752x1536 横屏展示"""

url = "https://token.sensenova.cn/v1/images/generations"
payload = {"model": "sensenova-u1-fast", "prompt": PROMPT, "size": "2752x1536", "n": 1}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("🖼️ 生成图2: 双引擎架构对比...")
resp = requests.post(url, headers=headers, json=payload, timeout=120)
if resp.status_code == 200:
    img_url = resp.json()["data"][0]["url"]
    img_resp = requests.get(img_url, timeout=60)
    with open("ks1-simple-api-02-双引擎架构.png", "wb") as f:
        f.write(img_resp.content)
    print(f"✅ 已保存: ks1-simple-api-02-双引擎架构.png")
else:
    print(f"❌ 失败: HTTP {resp.status_code} - {resp.text[:300]}")
