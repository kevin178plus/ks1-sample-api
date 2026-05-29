"""
使用 SenseNova U1 Fast 生成项目全景信息图
"""
import os
import json
import requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代、信息密度高的技术信息图，主题为「多免费API代理服务 — ks1-simple-api 全景分析」。整体采用深色科技风背景（深蓝到紫黑渐变），搭配亮色点缀（青色、橙色、绿色），风格类似信息可视化仪表盘，专业但不失亲和力。

图像分为四个主要区块，呈2x2网格布局：

【左上区块 — 项目全景概览】
标题：「ks1-simple-api 全景图」
副标题：轻量级多免费API代理服务

内容包含：
- 一个中心枢纽图标（齿轮+API符号），向外辐射连接多个API节点
- 核心数据卡片（3个横向排列）：
  ▸ 22 个上游API | 13可用 | 1已修复 | 6失效 | 1超时
  ▸ 2 种引擎 | Python(Flask) + Go | 双版本并行
  ▸ 4 种部署场景 | 开发/生产/简单/旧服务器
- 一句话定位：「无需One API，本机一键启动，兼容OpenAI格式，自动轮换免费模型」

【右上区块 — 双引擎架构对比】
标题：「Python vs Go 双引擎架构」

左侧Python引擎（浅蓝色调）：
- Flask Web服务 | 端口5000
- 图标：Python蛇形logo + Flask杯子
- 特性标签：自动热重载 · 调试面板 · 文件监控 · 守护进程
- 优势：灵活 · 易调试 · 生态丰富

右侧Go引擎（青绿色调）：
- Go HTTP服务 | 端口8080/5060
- 图标：Go语言gopher形象
- 特性标签：优雅重启(<3s) · 健康检查(5min) · 限额统计 · 白名单认证
- 优势：高性能 · 低内存 · 并发强

中间对比箭头和差异表（小字号）：
健康检查：Python(启动时) vs Go(周期5min)
配置加载：Python(重启) vs Go(优雅重启)
API Key认证：Python(无) vs Go(有)

【左下区块 — 22个上游API状态地图】
标题：「上游API状态全景 (2026-05-27检测)」

用网格卡片形式展示22个上游，每个卡片包含：
- 编号（free1~free22）
- 服务商名称
- 状态指示灯（绿色✅/橙色🔧/红色⛔/黄色⚠️）
- 是否需要代理（🔒图标表示需要）

可用（绿色，13个）：
free1 OpenRouter ✅🔒 | free2 ChatAnywhere ✅ | free3 Free.v36 ✅
free4 Mistral ✅🔧 | free8 Friendli ✅ | free12 OpenCode ✅
free13 atomgit ✅ | free15 Groq ✅🔒 | free16 Sambanova ✅
free17 Cerebras ✅🔒 | free19 Cohere ✅🔒 | free20 LongCat ✅
free21 FreeModel ✅🔒 | free22 商汤日日新 ✅

已修复（橙色，1个）：
free4 Mistral 🔧 | 标注「use_proxy反转修复」

失效（红色，6个）：
free6 CSDN ⛔400 | free7 NVIDIA ⛔410 | free10 联通云 ⛔403
free11 白山智算 ⛔403 | free14 CGC ⛔DNS | free18 Gemini ⚠️超时

【右下区块 — 部署场景与核心工作流】
标题：「部署场景 & 核心工作流」

上半部分 — 4个场景卡片（带推荐星级）：
🚀 simple-deployment ⭐⭐⭐⭐⭐ | 5分钟快速部署
🛠️ development ⭐⭐⭐⭐⭐ | 本地开发调试
🖥️ win2012-server ⭐⭐⭐⭐ | 老旧服务器优化
🏭 production ⭐⭐⭐⭐⭐ | 企业级生产环境

下半部分 — 核心工作流（横向流程图，带箭头）：
步骤1「启动」→ 加载.env配置 + 扫描upstreams目录
步骤2「健康检查」→ 测试各上游可用性 → 权重排序
步骤3「请求路由」→ 权重轮询选择最优API → 发送请求
步骤4「故障处理」→ 失败自动重试(3次) → 转移至备用上游
步骤5「统计记录」→ 更新调用统计 → 流量日志持久化

底部一行小字：
「故障自动隔离 · 权重动态调整 · 连续失败3次标记不可用 · 反转use_proxy智能修复」

整体设计要点：
- 使用统一的颜色编码体系：绿色=可用，橙色=修复中，红色=失效，黄色=警告，青色=代理需求
- 图标风格统一，扁平化设计
- 文字精简，多用图标和符号传达信息
- 区块之间有清晰的视觉分隔线
- 整体比例协调，信息密度高但不拥挤
- 适合在2K分辨率(2752x1536)下清晰展示所有细节"""

url = "https://token.sensenova.cn/v1/images/generations"

payload = {
    "model": "sensenova-u1-fast",
    "prompt": PROMPT,
    "size": "2752x1536",
    "n": 1
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("🚀 正在调用 SenseNova U1 Fast 图像生成接口...")
print(f"📐 分辨率: 2752x1536 (16:9 2K)")
print(f"📏 Prompt长度: {len(PROMPT)} 字符")
print()

resp = requests.post(url, headers=headers, json=payload, timeout=120)

if resp.status_code == 200:
    data = resp.json()
    img_url = data["data"][0]["url"]
    print("✅ 图像生成成功！")
    print(f"🔗 图片URL: {img_url}")
    
    # 下载图片
    img_resp = requests.get(img_url, timeout=60)
    output_path = "ks1-simple-api-infographic.png"
    with open(output_path, "wb") as f:
        f.write(img_resp.content)
    print(f"💾 已保存至: {output_path}")
else:
    print(f"❌ 请求失败: HTTP {resp.status_code}")
    print(f"📄 响应内容: {resp.text[:500]}")
