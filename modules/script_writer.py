"""대본 + 제목 + 썸네일 생성 모듈"""
import anthropic
from modules.utils import load_settings, get_anthropic_key

def write_script(source_text: str, ref_text: str = "") -> dict:
    settings = load_settings()
    api_key = get_anthropic_key(settings)

    # API 키를 SDK 자동감지에 맡김 (ANTHROPIC_API_KEY 환경변수 또는 Claude Code 환경)
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = settings["models"]["anthropic"]
    tone = settings["style"]["tone"]
    audience = settings["style"]["target_audience"]

    ref_section = f"\n\n## 참고 경쟁 영상 분석\n{ref_text}" if ref_text else ""

    prompt = f"""당신은 유튜브 콘텐츠 전문 작가입니다.
아래 소재를 바탕으로 유튜브 영상용 제목, 썸네일 문구, 대본을 작성해주세요.

## 소재
{source_text}{ref_section}

## 작성 지침
- 톤: {tone}
- 대상 시청자: {audience}
- 대본 길이: 5-8분 분량 (약 1200-2000자)
- 구성: 인트로(후킹) → 본론(3-4개 섹션) → 아웃트로(구독 유도)
- 자연스러운 구어체 사용
- 각 섹션 앞에 [섹션명] 태그 표시

## 출력 형식 (반드시 이 형식 준수)

=== 제목 ===
(클릭률 높은 유튜브 제목 3가지 제안, 번호 매기기)

=== 썸네일 문구 ===
(3-5단어의 임팩트 있는 썸네일 텍스트)

=== 대본 ===
(전체 대본)
"""

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = message.content[0].text

    # 파싱
    result = {"title": "", "thumbnail": "", "script": full_text}

    if "=== 제목 ===" in full_text and "=== 썸네일 문구 ===" in full_text:
        title_part = full_text.split("=== 제목 ===")[1].split("=== 썸네일 문구 ===")[0].strip()
        result["title"] = title_part

    if "=== 썸네일 문구 ===" in full_text and "=== 대본 ===" in full_text:
        thumb_part = full_text.split("=== 썸네일 문구 ===")[1].split("=== 대본 ===")[0].strip()
        result["thumbnail"] = thumb_part

    if "=== 대본 ===" in full_text:
        script_part = full_text.split("=== 대본 ===")[1].strip()
        result["script"] = script_part

    return result
