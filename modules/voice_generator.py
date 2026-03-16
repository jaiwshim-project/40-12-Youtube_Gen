"""ElevenLabs 음성 생성 모듈"""
import os
import re
from modules.utils import load_settings

def generate_voice(script_text: str, output_path: str) -> bool:
    settings = load_settings()
    api_key = settings["api_keys"]["elevenlabs"]["api_key"]
    if not api_key:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")

    if not api_key:
        print("  [건너뜀] ElevenLabs API 키가 없습니다. config/settings.yaml에서 설정하세요.")
        return False

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import save

        voice_id = settings["api_keys"]["elevenlabs"]["voice_id"]
        client = ElevenLabs(api_key=api_key)

        # 대본에서 지문 제거 (대괄호 내용)
        clean_script = re.sub(r'\[.*?\]', '', script_text).strip()

        audio = client.generate(
            text=clean_script,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )

        save(audio, output_path)
        print(f"  ✅ 음성 생성 완료: {output_path}")
        return True

    except ImportError:
        print("  [건너뜀] elevenlabs 패키지가 없습니다. pip install elevenlabs")
        return False
    except Exception as e:
        print(f"  [오류] 음성 생성 실패: {e}")
        return False
