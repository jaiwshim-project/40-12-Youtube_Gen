"""이미지 프롬프트 생성 모듈"""
import anthropic
from modules.utils import load_settings, get_anthropic_key

def generate_prompts(script_text: str, short: bool = False) -> str:
    settings = load_settings()
    api_key = get_anthropic_key(settings)

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = settings["models"]["anthropic"]

    count = 8 if short else 15

    prompt = f"""아래 유튜브 대본을 분석하여 영상에 사용할 이미지 프롬프트를 {count}개 생성해주세요.

## 대본
{script_text}

## 지침
- 각 프롬프트는 영어로 작성 (Whisk/이미지 생성 AI용)
- 따뜻하고 감성적인 수채화 스타일
- 장면 설명이 구체적이고 시각적
- 각 프롬프트는 "---"로 구분

## 형식
[장면 {1}]
한글 설명: (어떤 장면인지)
영어 프롬프트: (이미지 생성용 영어 프롬프트)

---
"""

    message = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
