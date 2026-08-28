"""Phase 4: 把双人对话脚本合成为一期音频。

放弃"豆包语音播客大模型"直连方案：该服务只支持预购买token包（最低10亿token/¥70,000），
对个人日更项目完全不划算，且账号未配置对应 grant。改用经典的"语音合成大模型2.0"同步
HTTP 接口，按甲/乙逐句合成，再用 ffmpeg 按顺序拼接成一期完整音频。

云端 TTS 网络不可达时（比如在无网络出口的沙盒里跑），自动降级为 macOS 自带的 `say`
命令做本地双音色合成，保证在受限环境下也能跑完整条流水线。
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

import requests

import config

ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
RESOURCE_ID = "seed-tts-2.0"
TURN_RE = re.compile(r"^(甲|乙)[：:]\s*(.+)$")


def parse_turns(script: str) -> list[tuple[str, str]]:
    """返回 [(speaker_voice_id, text), ...]"""
    voice_a = config.require(config.VOLC_VOICE_HOST_A, "VOLC_VOICE_HOST_A", "在 .env 里配置甲的音色 ID")
    voice_b = config.require(config.VOLC_VOICE_HOST_B, "VOLC_VOICE_HOST_B", "在 .env 里配置乙的音色 ID")
    turns = []
    for line in script.splitlines():
        m = TURN_RE.match(line.strip())
        if m:
            voice = voice_a if m.group(1) == "甲" else voice_b
            turns.append((voice, m.group(2)))
    return turns


def _tts_one(api_key: str, voice: str, text: str) -> bytes:
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    body = {
        "req_params": {
            "text": text,
            "speaker": voice,
            "audio_params": {"format": "mp3", "sample_rate": 24000},
        }
    }
    resp = requests.post(ENDPOINT, headers=headers, json=body, timeout=30)
    resp.raise_for_status()

    # 响应按 HTTP chunked 分块返回，每块是独立 JSON 对象，逐块解码拼接 base64 音频
    import base64
    audio = bytearray()
    decoder = json.JSONDecoder()
    text_buf = resp.text
    pos = 0
    while pos < len(text_buf):
        while pos < len(text_buf) and text_buf[pos] in "\r\n \t":
            pos += 1
        if pos >= len(text_buf):
            break
        obj, end = decoder.raw_decode(text_buf, pos)
        pos = end
        # code=0：单块音频正常；code=20000000：整段流结束标记；其余视为报错
        if obj.get("code") not in (0, 20000000, None):
            raise RuntimeError(f"TTS 报错: {obj.get('message')} (text={text[:20]!r})")
        if obj.get("data"):
            audio.extend(base64.b64decode(obj["data"]))
    if not audio:
        raise RuntimeError(f"没收到音频数据 (text={text[:20]!r})")
    return bytes(audio)


def _synthesize_cloud(script: str) -> Path:
    api_key = config.require(config.VOLC_SPEECH_API_KEY, "VOLC_SPEECH_API_KEY", "在 .env 里填入")
    turns = parse_turns(script)
    if not turns:
        raise RuntimeError("脚本里没有解析到 '甲：'/'乙：' 格式的对话行，检查 script.md 格式")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        concat_list = tmp_path / "concat.txt"
        lines = []
        for i, (voice, text) in enumerate(turns):
            audio = _tts_one(api_key, voice, text)
            seg_path = tmp_path / f"seg_{i:04d}.mp3"
            seg_path.write_bytes(audio)
            lines.append(f"file '{seg_path}'")
            print(f"[{i + 1}/{len(turns)}] 合成完成: {text[:20]}...")
        concat_list.write_text("\n".join(lines), encoding="utf-8")

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(config.EPISODE_PATH)],
            check=True, capture_output=True,
        )

    print(f"合成完成，共 {len(turns)} 句，输出：{config.EPISODE_PATH}")
    return config.EPISODE_PATH


def _synthesize_local(script: str) -> Path:
    turns = []
    for line in script.splitlines():
        match = TURN_RE.match(line.strip())
        if match:
            turns.append((match.group(1), match.group(2)))
    if not turns:
        raise RuntimeError("脚本里没有解析到 '甲：'/'乙：' 格式的对话行，检查 script.md 格式")

    local_voices = {"甲": "Tingting", "乙": "Reed (中文（中国大陆）)"}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        concat_list = tmp_path / "concat.txt"
        lines = []
        for i, (speaker, text) in enumerate(turns):
            seg_path = tmp_path / f"seg_{i:04d}.aiff"
            subprocess.run(
                ["say", "-v", local_voices[speaker], "-r", "190", "-o", str(seg_path), text],
                check=True,
                capture_output=True,
            )
            lines.append(f"file '{seg_path}'")
            print(f"[{i + 1}/{len(turns)}] 本地合成完成: {text[:20]}...")
        concat_list.write_text("\n".join(lines), encoding="utf-8")

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c:a", "libmp3lame", "-b:a", "96k", str(config.EPISODE_PATH)],
            check=True,
            capture_output=True,
        )

    print(f"本地降级合成完成，共 {len(turns)} 句，输出：{config.EPISODE_PATH}")
    return config.EPISODE_PATH


def synthesize(script: str | None = None) -> Path:
    if script is None:
        script = config.SCRIPT_PATH.read_text(encoding="utf-8")

    try:
        return _synthesize_cloud(script)
    except requests.ConnectionError as exc:
        print(f"云端 TTS 网络不可达，切换本机双音色合成：{exc}")
        return _synthesize_local(script)


if __name__ == "__main__":
    synthesize()
