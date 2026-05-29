"""
生成 ks1-simple-api 系列信息图 - 图4: 部署场景与工作流
"""
import os, requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代的技术信息图，主题为「ks1-simple-api 部署场景与核心工作流」。深色科技风背景（深蓝到紫黑渐变），上下两部分布局。

【顶部标题区】
大标题：「部署场景 & 核心工作流」
副标题：「从5分钟快速部署到企业级生产环境」

【上半部分 — 4个部署场景卡片（2×2网格）】
卡片1（左上，绿色渐变）：
  图标：🚀 火箭
  标题：「simple-deployment」
  星级：⭐⭐⭐⭐⭐
  描述：「5分钟快速部署」
  适用：「新手 · 内网 · 快速体验」

卡片2（右上，蓝色渐变）：
  图标：🛠️ 扳手
  标题：「development」
  星级：⭐⭐⭐⭐⭐
  描述：「本地开发调试」
  适用：「文件监控 · 热重载 · 调试面板」

卡片3（左下，橙色渐变）：
  图标：🖥️ 显示器
  标题：「win2012-server」
  星级：⭐⭐⭐⭐
  描述：「老旧服务器优化」
  适用：「2GB内存 · 零系统影响」

卡片4（右下，紫色渐变）：
  图标：🏭 工厂
  标题：「production」
  星级：⭐⭐⭐⭐⭐
  描述：「企业级生产环境」
  适用：「SSL · 服务化 · 多层防护」

【下半部分 — 核心工作流（5步横向流程图）】
标题：「核心工作流」

5个步骤用圆角矩形卡片横向排列，中间用箭头连接：

步骤1（青色）：「启动」
  小字：「加载.env · 扫描upstreams」
  图标：⚡ 闪电

步骤2（蓝色）：「健康检查」
  小字：「测试上游 · 权重排序」
  图标：🏥 医疗十字

步骤3（绿色）：「请求路由」
  小字：「权重轮询 · 选择最优」
  图标：🧭 指南针

步骤4（橙色）：「故障处理」
  小字：「3次重试 · 切换备用」
  图标：🔄 循环箭头

步骤5（紫色）：「统计记录」
  小字：「调用统计 · 流量日志」
  图标：📊 柱状图

【步骤之间 — 箭头上的小标签】
箭头1→2：「自动」
箭头2→3：「实时」
箭头3→4：「失败触发」
箭头4→5：「异步」

【底部 — 智能特性栏】
4个特性标签横向排列：
「🔒 故障自动隔离」 「⚖️ 权重动态调整」 「❌ 连续3次失败标记不可用」 「🔧 反转use_proxy智能修复」

设计要点：
- 场景卡片色彩丰富，区分明显
- 星级用黄色星星清晰展示
- 工作流箭头流畅，步骤卡片等距排列
- 图标简洁扁平化
- 底部特性栏用色块区分
- 文字精简，每卡片不超过3行
- 留白充足
- 适合 2752x1536 横屏展示"""

url = "https://token.sensenova.cn/v1/images/generations"
payload = {"model": "sensenova-u1-fast", "prompt": PROMPT, "size": "2752x1536", "n": 1}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("🖼️ 生成图4: 部署场景与工作流...")
resp = requests.post(url, headers=headers, json=payload, timeout=120)
if resp.status_code == 200:
    img_url = resp.json()["data"][0]["url"]
    img_resp = requests.get(img_url, timeout=60)
    with open("ks1-simple-api-04-部署场景与工作流.png", "wb") as f:
        f.write(img_resp.content)
    print(f"✅ 已保存: ks1-simple-api-04-部署场景与工作流.png")
else:
    print(f"❌ 失败: HTTP {resp.status_code} - {resp.text[:300]}")
