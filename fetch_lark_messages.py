"""Phase 1: 拉取飞书采集会话最近 24 小时的消息，保存到 output/raw_messages.json"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone

import config

URL_RE = re.compile(r"https?://[^\s\"'<>]+")

TZ = timezone(timedelta(hours=8))


def run_lark_cli(chat_id: str, start: datetime, end: datetime) -> dict:
    cmd = [
        "lark-cli", "im", "+chat-messages-list",
        "--chat-id", chat_id,
        "--start", start.isoformat(),
        "--end", end.isoformat(),
        "--order", "asc",
        "--page-size", "50",
        "--no-reactions",
        "--format", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli 调用失败: {result.stderr.strip()}")
    return json.loads(result.stdout)


def extract_text(message: dict) -> str:
    """text/post 消息的 content 是 JSON 字符串，这里统一拍平成纯文本"""
    raw = message.get("content", "")
    try:
        content = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw if isinstance(raw, str) else ""

    if "text" in content:
        return content["text"]

    # post 富文本：content.<lang>.content 是二维数组，每个元素是 {tag, text/href}
    parts = []
    for lang_block in content.values():
        if not isinstance(lang_block, dict):
            continue
        for line in lang_block.get("content", []):
            for seg in line:
                if seg.get("tag") == "text":
                    parts.append(seg.get("text", ""))
                elif seg.get("tag") == "a":
                    parts.append(seg.get("href", ""))
    return " ".join(parts)


def fetch(chat_id: str | None = None) -> list[dict]:
    chat_id = chat_id or config.require(
        config.LARK_CHAT_ID, "LARK_CHAT_ID",
        "在 .env 里填入飞书采集会话的 chat_id（用 lark-cli im +chat-search --query <会话名> 查询）",
    )
    end = datetime.now(TZ)
    start = end - timedelta(hours=24)

    data = run_lark_cli(chat_id, start, end)
    items = []
    for msg in data.get("messages", []):
        if msg.get("msg_type") not in ("text", "post"):
            continue
        text = extract_text(msg).strip()
        if not text:
            continue
        urls = URL_RE.findall(text)
        items.append({
            "message_id": msg.get("message_id"),
            "create_time": msg.get("create_time"),
            "sender": (msg.get("sender") or {}).get("name", ""),
            "text": text,
            "urls": urls,
        })

    config.RAW_MESSAGES_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"抓到 {len(items)} 条消息，已保存到 {config.RAW_MESSAGES_PATH}")
    return items


if __name__ == "__main__":
    fetch()
