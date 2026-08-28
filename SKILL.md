---
name: ai-agent-digest
version: 0.1.0
description: "把用户转发到飞书'AI资讯'会话里的 AI 竞品动态/模型发布/方法论资讯，自动整理成一期双人对话播客（含 TL;DR 文字摘要）。当用户说'生成今天的资讯播客'、'把飞书里的AI资讯做成播客'、'今天的AI资讯有什么'时使用。"
metadata:
  requires:
    bins: ["python3", "ffmpeg"]
    env: ["LARK_CHAT_ID", "VOLC_SPEECH_API_KEY", "ARK_API_KEY", "ARK_CHAT_MODEL"]
  cliHelp: "python3 run_daily.py"
---

# ai-agent-digest

把"刷到但没空看"的 AI 资讯（竞品动态/模型发布/Agent 方法论），从飞书转发一键转成可以边听边吸收的双人对话播客。

## 何时使用

用户提到"生成今天的资讯播客" / "飞书里的 AI 资讯整理一下" / "今天有什么值得看的 AI 动态" 之类意图时触发。

## 前置条件

`.env` 需要四个凭证（首次使用参照 `.env.example` 填写，一次配置长期有效）：
- `LARK_CHAT_ID`：飞书采集会话的 chat_id（用户平时把小红书/公众号链接转发到这个会话）
- `VOLC_SPEECH_API_KEY`：火山引擎新版控制台"语音合成2.0"的 API Key，用于 Phase 4 TTS
- `ARK_API_KEY` / `ARK_CHAT_MODEL`：火山方舟 API Key + 模型 ID，用于 Phase 3 脚本生成

未配置时运行会明确报错提示缺哪个变量，不要瞎猜着填。

## 使用方式

```bash
cd <本 skill 所在目录>
python3 run_daily.py
```

依次执行四个阶段，中途会在生成完文字稿后暂停，请先带用户过一遍 `output/summary.md`（TL;DR 摘要）
和 `output/script.md`（完整对话稿），确认没问题（尤其是标了"仅有标题"的降级素材有没有被瞎编）再继续合成音频。

也可以单独重跑某一阶段（比如只想重新生成文案，不用重新拉取飞书消息）：

```bash
python3 fetch_lark_messages.py [--hours N]  # Phase 1 拉取飞书最近 N 小时消息（默认24）→ output/raw_messages.json
python3 extract_content.py       # Phase 2 展开正文（公众号/YouTube/Twitter抓正文，小红书降级） → output/materials.json
python3 generate_script.py       # Phase 3 生成摘要+对话稿 → output/summary.md + output/script.md
python3 synthesize_audio.py      # Phase 4 合成音频 → output/episode.mp3
```

## 素材来源与处理原则

- **公众号文章**（mp.weixin.qq.com）：直接抓正文
- **YouTube 视频**（youtube.com / youtu.be）：拉官方字幕轨道，不做画面识别
- **Twitter/X**（twitter.com / x.com）：用官方 oEmbed 接口（publish.x.com，专为"内嵌推文"设计，免密钥）取推文正文
- **小红书链接**（xiaohongshu.com / xhslink.com）：**不做自动抓取**——无公开 API，抓取需要模拟登录+
  设备指纹绕过反爬，有账号封禁风险。只使用转发消息里分享自带的标题/摘要文本，脚本生成阶段会如实说明
  "这条我们只看到标题"，绝不编造原文没有的细节
- 其他未识别来源：保留原始转发文本，不强行抓取

## 输出

- `output/summary.md` — TL;DR 摘要（3-6 条要点，播客 App show notes 风格）
- `output/script.md` — 完整双人对话稿（甲/乙）
- `output/episode.mp3` — 最终音频

## 已知限制（尚未实现）

- 没有 RSS 订阅源和公网托管，暂时只能本地播放 mp3，还不能用小宇宙/Apple Podcasts 订阅
- 没有每日定时自动触发，需要手动运行
