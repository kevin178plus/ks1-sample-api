"""
生成 ks1-simple-api 系列信息图 - 图3: 上游API状态地图（修复版，减少中文乱码）
"""
import os, requests

API_KEY = os.getenv("FREE22_API_KEY", "sk-8izJi2KDDGYDqTZ6IEvMTYXjRwds19at")

PROMPT = """这是一张专业、现代的技术信息图，主题为「ks1-simple-api Upstream Status」。深色科技风背景（深蓝到紫黑渐变），信息卡片网格布局，2026年5月检测数据。

【顶部标题区】
大标题：「Upstream Status」
副标题：「22 Upstreams · 2026-05-27 Auto Check」
右上角标签：「test_upstreams_proxy_swap.py」

【核心数据横幅 — 5个横向小卡片】
卡片1（绿色）：「13 OK」✅
卡片2（橙色）：「1 Fixed」🔧
卡片3（红色）：「6 Down」⛔
卡片4（黄色）：「1 Timeout」⚠️
卡片5（青色）：「12 Proxy」🔒

【主体 — 22个上游卡片网格（4列×6行，最后行4个）】
每个卡片包含：编号、服务商名、状态圆点、代理锁图标

第一行（全部绿色✅可用）：
free1 OpenRouter ●🔒 | free2 ChatAnywhere ● | free3 Free.v36 ● | free4 Mistral ●🔧
第二行（绿色）：
free8 Friendli ● | free12 OpenCode ● | free13 atomgit ● | free15 Groq ●🔒
第三行（绿色）：
free16 Sambanova ● | free17 Cerebras ●🔒 | free19 Cohere ●🔒 | free20 LongCat ●
第四行（绿色+已关停）：
free21 FreeModel ●🔒 | free22 SenseNova ● | free5 iFlow ●❌ | free9 Volcano ●❌
第五行（红色失效）：
free6 CSDN ⛔400 | free7 NVIDIA ⛔410 | free10 Cloud ⛔403 | free11 BaiShan ⛔403
第六行（红色+黄色）：
free14 CGC ⛔DNS | free18 Gemini ⚠️Timeout | free18 Retry ⚠️Still Fail | free4 Fix 🔧

【卡片颜色规则】
- 绿色卡片：可用上游，边框绿色
- 橙色卡片：已修复上游，边框橙色，标注"Proxy Fixed"
- 红色卡片：失效上游，边框红色，标注HTTP错误码
- 黄色卡片：超时上游，边框黄色

【底部 — 智能修复说明】
淡紫色背景框：
「🔧 free4 (Mistral AI) Timeout → use_proxy=true → OK」
「⚙️ Auto detect + Smart fix with test_upstreams_proxy_swap.py」

设计要点：
- 卡片大小一致，网格整齐
- 状态圆点用大色块突出（绿/橙/红/黄）
- 数字和错误码用醒目颜色
- 🔒锁图标清晰表示需要代理
- 文字精简，每卡片不超过3行
- 文字以英文为主，避免中文乱码
- 留白充足，不拥挤
- 适合 2752x1536 横屏展示"""

url = "https://token.sensenova.cn/v1/images/generations"
payload = {"model": "sensenova-u1-fast", "prompt": PROMPT, "size": "2752x1536", "n": 1}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("🖼️ 生成图3（修复版）: 上游状态全景...")
resp = requests.post(url, headers=headers, json=payload, timeout=120)
if resp.status_code == 200:
    img_url = resp.json()["data"][0]["url"]
    img_resp = requests.get(img_url, timeout=60)
    with open("ks1-simple-api-03-上游状态全景-v2.png", "wb") as f:
        f.write(img_resp.content)
    print(f"✅ 已保存: ks1-simple-api-03-上游状态全景-v2.png")
else:
    print(f"❌ 失败: HTTP {resp.status_code} - {resp.text[:300]}")
