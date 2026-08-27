"""Phase 2: 把消息里的链接展开成正文素材。

公众号文章（mp.weixin.qq.com）：直接抓取网页正文。
YouTube 视频（youtube.com / youtu.be）：拉取官方字幕轨道（公开接口，无需登录，不涉及反爬问题）。
Twitter/X（twitter.com / x.com）：用官方 oEmbed 接口（publish.x.com，专为"内嵌推文"设计，免密钥）取推文正文。
小红书链接（xiaohongshu.com / xhslink.com）：不做自动抓取（无公开 API，抓取需要
模拟登录+设备指纹绕过反爬，有账号风险），只使用转发消息里自带的标题/摘要文本。
"""
from __future__ import annotations

import json
import re

import requests
from bs4 import BeautifulSoup
from readability import Document
from youtube_transcript_api import YouTubeTranscriptApi

import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

WEIXIN_RE = re.compile(r"mp\.weixin\.qq\.com")
XHS_RE = re.compile(r"xiaohongshu\.com|xhslink\.com")
YOUTUBE_RE = re.compile(r"(?:youtube\.com|youtu\.be)")
YOUTUBE_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([\w-]{11})"
)
TWITTER_RE = re.compile(r"(?:twitter\.com|x\.com)/\w+/status/\d+")
TWEET_TEXT_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL)


def fetch_weixin_article(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    doc = Document(resp.text)
    soup = BeautifulSoup(doc.summary(), "html.parser")
    body_text = soup.get_text("\n", strip=True)
    return {"source": "weixin", "title": doc.title(), "text": body_text, "url": url, "degraded": False}


def fetch_youtube_transcript(url: str) -> dict:
    m = YOUTUBE_ID_RE.search(url)
    if not m:
        raise ValueError(f"无法从链接解析出视频 ID: {url}")
    video_id = m.group(1)
    transcript = YouTubeTranscriptApi().fetch(video_id, languages=["zh-Hans", "zh-Hant", "zh", "en"])
    body_text = " ".join(snippet.text for snippet in transcript)
    return {"source": "youtube", "title": "", "text": body_text, "url": url, "degraded": False}


def fetch_tweet_text(url: str) -> dict:
    resp = requests.get("https://publish.x.com/oembed", params={"url": url}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    m = TWEET_TEXT_RE.search(data.get("html", ""))
    body_text = BeautifulSoup(m.group(1), "html.parser").get_text(" ", strip=True) if m else ""
    if not body_text:
        raise ValueError("oEmbed 返回内容里没有解析到推文正文")
    return {"source": "twitter", "title": data.get("author_name", ""), "text": body_text, "url": url, "degraded": False}


def build_material(message: dict) -> dict:
    urls = message.get("urls", [])
    text = message["text"]

    if not urls:
        return {"source": "text", "title": "", "text": text, "url": "", "degraded": False}

    url = urls[0]  # 一条转发消息一般只有一个主链接
    caption = text.replace(url, "").strip()

    if WEIXIN_RE.search(url):
        try:
            article = fetch_weixin_article(url)
            if caption:
                article["text"] = f"{caption}\n\n{article['text']}"
            return article
        except Exception as exc:  # noqa: BLE001
            return {
                "source": "weixin", "title": "", "text": caption or "(抓取失败，仅有链接)",
                "url": url, "degraded": True, "error": str(exc),
            }

    if YOUTUBE_RE.search(url):
        try:
            video = fetch_youtube_transcript(url)
            if caption:
                video["text"] = f"{caption}\n\n{video['text']}"
            return video
        except Exception as exc:  # noqa: BLE001
            return {
                "source": "youtube", "title": "", "text": caption or "(字幕获取失败，仅有链接，可能该视频未提供字幕)",
                "url": url, "degraded": True, "error": str(exc),
            }

    if TWITTER_RE.search(url):
        try:
            tweet = fetch_tweet_text(url)
            if caption:
                tweet["text"] = f"{caption}\n\n{tweet['text']}"
            return tweet
        except Exception as exc:  # noqa: BLE001
            return {
                "source": "twitter", "title": "", "text": caption or "(oEmbed 获取失败，仅有链接，可能该推文已禁止内嵌)",
                "url": url, "degraded": True, "error": str(exc),
            }

    if XHS_RE.search(url):
        # 不抓取，如实标注仅有分享文本
        return {
            "source": "xiaohongshu", "title": "", "text": caption or "(仅有链接，无分享文本)",
            "url": url, "degraded": True,
        }

    # 未知来源：不做特殊处理，只保留原文文本，不强行抓取
    return {"source": "other", "title": "", "text": caption or text, "url": url, "degraded": True}


def extract(messages: list[dict] | None = None) -> list[dict]:
    if messages is None:
        messages = json.loads(config.RAW_MESSAGES_PATH.read_text(encoding="utf-8"))

    materials = [build_material(m) for m in messages]
    config.MATERIALS_PATH.write_text(
        json.dumps(materials, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    weixin_ok = sum(1 for m in materials if m["source"] == "weixin" and not m["degraded"])
    degraded = sum(1 for m in materials if m["degraded"])
    print(f"处理 {len(materials)} 条素材：{weixin_ok} 条公众号正文抓取成功，{degraded} 条降级为仅标题/摘要")
    return materials


if __name__ == "__main__":
    extract()
