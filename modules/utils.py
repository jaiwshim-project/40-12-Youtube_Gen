"""공통 유틸리티"""
import os
import yaml
from pathlib import Path

def load_settings() -> dict:
    settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if not settings_path.exists():
        return {
            "api_keys": {
                "anthropic":  {"api_key": ""},
                "gemini":     {"api_key": ""},
                "elevenlabs": {"api_key": "", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
            },
            "models": {"anthropic": "claude-sonnet-4-6"},
            "style":  {"tone": "따뜻하고 감성적인", "target_audience": "30-60대 감성 콘텐츠 시청자"},
        }
    with open(settings_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_anthropic_key(settings: dict) -> str:
    key = settings["api_keys"]["anthropic"]["api_key"]
    if not key or key == "YOUR_ANTHROPIC_API_KEY":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    return key
