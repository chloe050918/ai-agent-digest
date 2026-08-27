import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

LARK_CHAT_ID = os.environ.get("LARK_CHAT_ID", "")
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
ARK_CHAT_MODEL = os.environ.get("ARK_CHAT_MODEL", "")
VOLC_SPEECH_API_KEY = os.environ.get("VOLC_SPEECH_API_KEY", "")
VOLC_VOICE_HOST_A = os.environ.get("VOLC_VOICE_HOST_A", "")
VOLC_VOICE_HOST_B = os.environ.get("VOLC_VOICE_HOST_B", "")

OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

RAW_MESSAGES_PATH = OUTPUT_DIR / "raw_messages.json"
MATERIALS_PATH = OUTPUT_DIR / "materials.json"
SCRIPT_PATH = OUTPUT_DIR / "script.md"
SUMMARY_PATH = OUTPUT_DIR / "summary.md"
EPISODE_PATH = OUTPUT_DIR / "episode.mp3"


def require(value: str, name: str, hint: str) -> str:
    if not value:
        raise RuntimeError(f"缺少 {name}，请先完成：{hint}")
    return value
