"""
生成 ks1-simple-api 系列信息图 - 图1: 项目全景图
"""
import os, requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代的技术信息图，主题为「ks1-simple-api 项目全景图」。深色科技风背景（深蓝到紫黑渐变），亮色点缀（青色#00E5FF、橙色#FF9100、绿色#00E676），风格类似科技产品发布会信息图。

整体布局：顶部大标题区 + 中部核心数据区 + 底部价值主张区

【顶部标题区】
大标题（醒目大字）：「ks1-simple-api」
副标题（稍小）：「多免费API代理服务 — 全景图」
右上角小标签：「2026.05」

【中部核心数据区 — 3个大卡片横向排列】
卡片1（青色边框）：
  数字：「22」
  文字：「个上游API」
  小字：「覆盖全球主流免费模型」
  图标：8个圆点组成的API节点网络

卡片2（橙色边框）：
  数字：「2」
  文字：「种引擎」
  小字：「Python Flask + Go」
  图标：左右两个引擎齿轮咬合

卡片3（绿色边框）：
  数字：「4」
  文字：「种部署场景」
  小字：「开发/生产/简单/旧服务器」
  图标：4个小方块代表不同场景

【中部下方 — 核心架构图】
一个居中的中心节点（圆形，写着"API Proxy"），向外辐射连接：
- 左上箭头 → 「Free API 1~22」
- 右上箭头 → 「OpenAI兼容格式」
- 左下箭头 → 「自动轮换」
- 右下箭头 → 「故障转移」
中心节点下方小字：「本机一键启动 · 无需One API」

【底部价值主张区 — 3行文字】
第一行（绿色）：「✅ 兼容 OpenAI API — 直接替换端点，零代码修改」
第二行（橙色）：「🔄 智能故障转移 — 自动检测失效，3次重试后切换」
第三行（青色）：「📊 实时统计面板 — 网页查看调用次数，流量日志可追溯」

【右下角 — 一句话定位】
淡紫色背景框，白色文字：
「让免费AI触手可及」

设计要点：
- 信息密度适中，留白充足
- 数字用超大字号突出
- 图标简洁扁平化
- 颜色编码统一：青色=技术，橙色=智能，绿色=可靠
- 整体比例适合 2752x1536 横屏展示
- 所有文字清晰可读，无拥挤感"""

url = "https://token.sensenova.cn/v1/images/generations"
payload = {"model": "sensenova-u1-fast", "prompt": PROMPT, "size": "2752x1536", "n": 1}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("🖼️ 生成图1: 项目全景图...")
resp = requests.post(url, headers=headers, json=payload, timeout=120)
if resp.status_code == 200:
    img_url = resp.json()["data"][0]["url"]
    img_resp = requests.get(img_url, timeout=60)
    with open("ks1-simple-api-01-全景图.png", "wb") as f:
        f.write(img_resp.content)
    print(f"✅ 已保存: ks1-simple-api-01-全景图.png")
else:
    print(f"❌ 失败: HTTP {resp.status_code} - {resp.text[:300]}")
