"""
生成 ks1-simple-api 系列信息图 - 图2: 双引擎架构对比（修复版，减少中文乱码）
"""
import os, requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代的技术信息图，主题为「ks1-simple-api 双引擎架构对比」。深色科技风背景（深蓝到紫黑渐变），左右分栏设计，左侧Python主题色（浅蓝#64B5F6），右侧Go主题色（青绿#26A69A），中间用渐变分隔线。

【顶部标题区】
居中大标题：「Dual Engine」
副标题：「Python Flask vs Go」

【左侧 — Python引擎区（浅蓝色调）】
顶部图标：Python蛇形logo + Flask杯子图标
标题：「Python Flask」
端口标签：「Port 5000」

核心特性（4个标签，带小图标）：
🔧 Auto Reload — config changes take effect automatically
📡 File Watch — watchdog monitors file changes
🌐 Debug Panel — web UI shows real-time status
🛡️ Daemon — auto restart on crash

优势标签（绿色底）：
「Flexible · Easy Debug · Rich Ecosystem」

【右侧 — Go引擎区（青绿色调）】
顶部图标：Go语言gopher形象
标题：「Go Engine」
端口标签：「Port 8080 / 5060」

核心特性（4个标签，带小图标）：
⚡ Graceful Restart — config change < 3 seconds
🏥 Health Check — auto check every 5 minutes
📊 Stats — track by upstream + API Key
🔐 Access Control — whitelist API Key validation

优势标签（绿色底）：
「High Perf · Low Memory · Strong Concurrency」

【中间 — 差异对比区（白色小卡片）】
一个小卡片，标题「Key Differences」，3行对比：
Health Check → Python: at startup only | Go: every 5 min
Config Load  → Python: full restart | Go: graceful < 3s
Auth         → Python: none | Go: whitelist support

【底部 — 推荐建议】
左侧（浅蓝底）：「Dev / Test → Python」
右侧（青绿底）：「Production / High Load → Go」
中间箭头：「Both can run together, no conflict」

设计要点：
- 左右对称布局，视觉平衡
- 数字和标签用大字号突出
- 图标简洁扁平化
- 中间对比区用白色卡片突出差异
- 底部推荐用色块区分
- 文字以英文为主，避免中文乱码
- 整体适合 2752x1536 横屏展示"""

url = "https://token.sensenova.cn/v1/images/generations"
payload = {"model": "sensenova-u1-fast", "prompt": PROMPT, "size": "2752x1536", "n": 1}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("🖼️ 生成图2（修复版）: 双引擎架构对比...")
resp = requests.post(url, headers=headers, json=payload, timeout=120)
if resp.status_code == 200:
    img_url = resp.json()["data"][0]["url"]
    img_resp = requests.get(img_url, timeout=60)
    with open("ks1-simple-api-02-双引擎架构-v2.png", "wb") as f:
        f.write(img_resp.content)
    print(f"✅ 已保存: ks1-simple-api-02-双引擎架构-v2.png")
else:
    print(f"❌ 失败: HTTP {resp.status_code} - {resp.text[:300]}")
