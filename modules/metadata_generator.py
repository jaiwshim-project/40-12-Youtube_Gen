"""YouTube 메타데이터 (제목/설명/태그) 생성 모듈"""
import anthropic
from modules.utils import load_settings, get_anthropic_key

def generate_metadata(script_text: str, title_draft: str = "") -> dict:
    settings = load_settings()
    api_key = get_anthropic_key(settings)

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = settings["models"]["anthropic"]

    prompt = f"""아래 대본으로 YouTube 업로드용 메타데이터를 생성해주세요.

## 대본 (일부)
{script_text[:2000]}

## 초안 제목
{title_draft}

## 출력 형식

=== 최종 제목 ===
(SEO 최적화된 최종 업로드 제목 1개, 60자 이내)

=== 영상 설명 ===
(3-5문단, 첫 2줄은 핵심 내용 요약, 타임스탬프 섹션 포함, 채널 소개, 해시태그 3개)

=== 태그 ===
(쉼표로 구분된 15-20개 태그)
"""

    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = message.content[0].text
    result = {"title": "", "description": "", "tags": ""}

    if "=== 최종 제목 ===" in full_text:
        parts = full_text.split("=== 최종 제목 ===")
        if len(parts) > 1:
            rest = parts[1]
            if "=== 영상 설명 ===" in rest:
                result["title"] = rest.split("=== 영상 설명 ===")[0].strip()
            else:
                result["title"] = rest.strip()

    if "=== 영상 설명 ===" in full_text:
        parts = full_text.split("=== 영상 설명 ===")
        if len(parts) > 1:
            rest = parts[1]
            if "=== 태그 ===" in rest:
                result["description"] = rest.split("=== 태그 ===")[0].strip()
            else:
                result["description"] = rest.strip()

    if "=== 태그 ===" in full_text:
        result["tags"] = full_text.split("=== 태그 ===")[1].strip()

    return result
