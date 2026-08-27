"""Phase 3: 用火山方舟对话模型把当天素材整理成双人播客对话稿"""
from __future__ import annotations

import json

import requests

import config

ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

SYSTEM_PROMPT = """你在为一位字节跳动火山方舟的 AI 产品经理写一期每日播客文字稿。
这位听众需要跟踪三类信息：①AI Agent 竞品产品动态（如 Codex、Claude 等主流产品的功能更新）；
②模型发布与能力（如 GPT、Fable、Opus、Kimi 等新模型评测）；③Agent 方法论新概念
（如 Loop Engineering、Harness Engineering、Graph Engineering、Agent Benchmark、Agent Evolving 等）。

请把下面这批当天素材，写成两位主播（甲、乙）的对话稿：
- 甲负责提问/引导话题，乙负责展开解读，穿插甲的追问和评论，语气自然口语化，像真人播客，不要照读原文。
- 按素材类型自然归类展开，不用生硬地喊出"第一类""第二类"这种标题。
- 每条素材都要点出"这对一个 AI PM 的工作意味着什么"这个角度，不要只是复述新闻。
- **诚实原则**：素材里如果标注了 degraded/仅有标题或摘要，就如实说"这条我们只看到标题，具体细节还没展开"，
  绝不能编造原文没有的具体数据、功能细节或结论。
- 开头简短报一句"这是 XX月XX日的 AI 资讯播报"，结尾自然收尾，不要机械总结。
- 整体时长控制在口语 5-8 分钟（约 1200-1800 字）。

输出分两部分，用下面的固定结构（Markdown），不要输出任何额外的解释性前后缀：

## 摘要

用 3-6 条要点列出今天播报的核心信息，每条一句话、能一眼抓住重点（TL;DR 风格，参考播客 App 的"本期节目"简介），
不要展开论述，只列结论性的事实和判断。

## 对话稿

正文，每句前标注"甲："或"乙："。
"""


def build_user_prompt(materials: list[dict]) -> str:
    payload = [
        {
            "source": m["source"],
            "title": m.get("title", ""),
            "text": m["text"][:3000],  # 单条素材截断，避免超长文章占满上下文
            "degraded": m.get("degraded", False),
        }
        for m in materials
    ]
    return "今天的素材列表（JSON）：\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def _split_summary_and_script(raw: str) -> tuple[str, str]:
    marker = "## 对话稿"
    idx = raw.find(marker)
    if idx == -1:
        return "", raw
    summary = raw[:idx].replace("## 摘要", "").strip()
    script = raw[idx + len(marker):].strip()
    return summary, script


def generate(materials: list[dict] | None = None) -> str:
    if materials is None:
        materials = json.loads(config.MATERIALS_PATH.read_text(encoding="utf-8"))

    api_key = config.require(config.ARK_API_KEY, "ARK_API_KEY", "在 .env 里填入方舟 API Key")
    model = config.require(config.ARK_CHAT_MODEL, "ARK_CHAT_MODEL", "在 .env 填入火山方舟对话模型 ID")

    resp = requests.post(
        ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(materials)},
            ],
        },
        timeout=240,
    )
    resp.raise_for_status()
    data = resp.json()

    raw = data["choices"][0]["message"]["content"].strip()
    summary, script = _split_summary_and_script(raw)
    config.SUMMARY_PATH.write_text(summary, encoding="utf-8")
    config.SCRIPT_PATH.write_text(script, encoding="utf-8")
    print(f"摘要已生成：{config.SUMMARY_PATH}")
    print(f"脚本已生成，请先人工过一遍：{config.SCRIPT_PATH}")
    return script


if __name__ == "__main__":
    generate()
