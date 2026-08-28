# AI 资讯自动播客化

把每天转发到飞书"AI资讯"会话里的 AI 竞品动态、模型发布、Agent 方法论素材，自动整理成一期双人对话播客 +
TL;DR 文字摘要。打包成 Claude Code / Codex 通用的 Skill（`SKILL.md`），拿到这个仓库配好 `.env` 就能用。

## 为什么做这个

作为火山方舟的 AI 产品经理，日常需要追踪三类信息：AI Agent 竞品动态（Codex、Claude 等主流产品的功能更新）、
模型发布与能力评测、Agent 方法论新概念（Loop/Harness/Graph Engineering 等）。这些内容大多刷小红书和公众号
时随手转发到微信群，"以后有空看"，结果长期堆积没时间看；试过公众号自带的机器朗读，语音生硬听不下去。

于是把"刷到但没空看"的碎片信息，变成通勤/运动时能听的双人对话播客——工具本身也是"用 AI Agent 独立构建端到端产品"
这件事的一次实践。

## 效果预览（真实生成，未编辑）

以下是某次真实运行的输出片段（完整素材是当天转发的几篇公众号文章）：

**TL;DR 摘要**（`output/summary.md`）：

> 1. Anthropic 披露内部 80% 合入代码已由 Claude 生成，工程师人均产出较 2021 年提升约 8 倍，同步公开 AI 原生
>    SDLC 实践手册，将传统线性研发流改为 6 阶段闭环，重构 AI 编码提速后的人-AI 分工与全链路追溯机制。
> 2. Anthropic 最新多智能体研究证实"思维病毒"风险：恶意/无意义理念可通过智能体交互、持久记忆跨上下文传播，
>    不同模型抗感染能力差异显著（Claude Sonnet 4.6 表现最优）。

**双人对话稿**（`output/script.md`）节选：

> 甲：这是10月16日的AI资讯播报。今天最值得咱们AI产品经理深挖的，应该是Anthropic刚放出来的内部AI原生研发
> 流程玩法吧？
>
> 乙：对，首先数据确实挺有冲击力：他们现在内部80%的合入代码都是Claude写的...但这次最有价值的不是晒效率，
> 是他们直接点破了现在很多公司踩的坑：代码生成速度提上来了，但是需求、评审、测试、安全治理这些环节还是
> 按老节奏跑，原来围绕"写代码最慢"设计的线性流水线反而成了新瓶颈。

最终产出一期 `episode.mp3`（双人音色朗读全文）。

## 系统设计与关键判断

```
飞书"AI资讯"会话 → 消息采集 → 正文抽取 → 双人对话脚本生成(LLM) → 语音合成(TTS) → episode.mp3
                fetch_lark_messages.py   extract_content.py   generate_script.py   synthesize_audio.py
```

几个做的过程中做过评估、有意选择的地方：

- **信息源逐一判断合规边界，而不是一刀切**：公众号、YouTube 字幕、Twitter/X 都有可合规调用的公开接口
  （官方 oEmbed / 字幕轨道），直接完整抓取；小红书没有公开 API，抓取需要绕过反爬机制、有账号风险，主动放弃
  自动化抓取，只用转发时自带的标题/摘要文本，并在生成脚本时明确要求模型对"仅有标题"的素材如实说明局限，
  绝不编造原文没有的细节。
- **成本判断**：最初评估过火山引擎的"语音播客大模型"（一步生成双人播客），但它只支持预购买 token 包
  （最低 ¥70,000），对个人项目完全不划算；改用按字符量计费的经典语音合成 2.0，逐句合成后用 ffmpeg 拼接，
  效果接近、成本可控。
- **网络不可达时的容错**：云端 TTS 连不上时，自动降级为 macOS 自带的 `say` 命令做本地双音色合成，保证在
  网络受限的环境（比如沙盒、CI）里也能跑完整条流水线。

## 快速开始

```bash
git clone git@github.com:chloe050918/ai-agent-digest.git
cd ai-agent-digest
pip3 install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入四项凭证：

| 变量 | 获取方式 |
|---|---|
| `LARK_CHAT_ID` | 飞书里新建一个用于转发资讯的会话，用 `lark-cli im +chat-search --query <会话名>` 查到 chat_id |
| `VOLC_SPEECH_API_KEY` | [火山引擎语音技术控制台](https://console.volcengine.com/speech) 开通"语音合成 2.0"后，在"API Key"页面获取 |
| `ARK_API_KEY` | [火山方舟控制台](https://console.volcengine.com/ark) → API Key 管理 → 新建 |
| `ARK_CHAT_MODEL` | 火山方舟模型市场里选一个对话模型的 ID，例如 `doubao-seed-2-1-pro-260628` |

跑起来：

```bash
python3 run_daily.py
```

会依次拉取消息、抽取正文、生成脚本（此处会暂停，建议先看一眼 `output/script.md` 再继续）、合成音频，
最终产出 `output/episode.mp3`。也可以单独跑某一阶段，参考 `SKILL.md` 里的说明。

## 目录结构

- `fetch_lark_messages.py` — Phase 1，拉取飞书会话最近 N 小时消息（`--hours` 可调，默认 24）
- `extract_content.py` — Phase 2，公众号文章抓正文；YouTube 视频拉官方字幕轨道；Twitter/X 用官方 oEmbed
  接口取推文正文；小红书链接不抓取，只用分享自带的标题/摘要文本
- `generate_script.py` — Phase 3，调用火山方舟对话模型生成 TL;DR 摘要 + "甲/乙"双人对话稿
- `synthesize_audio.py` — Phase 4，逐句调用语音合成 2.0，云端不可达时自动降级本机 TTS，ffmpeg 拼接成一期音频
- `run_daily.py` — 手动触发全链路
- `SKILL.md` — Claude Code / Codex 通用的 Skill 定义，说明何时触发、怎么用
- `config.py` — 环境变量加载与统一路径管理
- `output/` — 每次运行的中间产物和最终音频（不进 git）

## 技术栈

Python 3.9+ · 飞书开放平台 API（`lark-cli`）· 火山方舟 LLM API（OpenAI 兼容）· 火山引擎语音合成 API ·
YouTube Data 字幕接口 · X/Twitter oEmbed · ffmpeg

## 已知限制

- 没有 RSS 订阅源和公网托管，暂时只能本地播放 mp3，还不能用小宇宙/Apple Podcasts 订阅
- 没有每日定时自动触发，需要手动运行
- 小红书内容因合规原因不做正文抓取（见上文"系统设计与关键判断"）
