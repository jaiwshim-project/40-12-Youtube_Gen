"""Vrew 편집 가이드 + 타임라인 생성 모듈"""
import anthropic
from modules.utils import load_settings, get_anthropic_key

def generate_guide(script_text: str, short: bool = False) -> dict:
    settings = load_settings()
    api_key = get_anthropic_key(settings)

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = settings["models"]["anthropic"]

    format_type = "숏폼 (60초 이내)" if short else "롱폼 (5-10분)"

    prompt = f"""아래 대본으로 Vrew 영상 편집 가이드와 타임라인을 작성해주세요.

## 대본
{script_text}

## 형식: {format_type}

## Vrew 편집 가이드 작성 요령
1. 단계별 편집 순서 명시
2. 자막 스타일 지침
3. 이미지 배치 시점
4. BGM 추천 (분위기)
5. 전환 효과

## 타임라인 형식
| 시간 | 내용 | 이미지 | 자막 |
|------|------|--------|------|

아래 형식으로 출력:

=== VREW 편집 가이드 ===
(편집 가이드 내용)

=== 타임라인 ===
(타임라인 표)
"""

    message = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = message.content[0].text
    result = {"guide": full_text, "timeline": ""}

    if "=== VREW 편집 가이드 ===" in full_text and "=== 타임라인 ===" in full_text:
        guide_part = full_text.split("=== VREW 편집 가이드 ===")[1].split("=== 타임라인 ===")[0].strip()
        timeline_part = full_text.split("=== 타임라인 ===")[1].strip()
        result["guide"] = guide_part
        result["timeline"] = timeline_part

    return result
