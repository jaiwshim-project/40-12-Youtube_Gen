"""블로그 글 생성 모듈"""
import anthropic
from modules.utils import load_settings, get_anthropic_key

def generate_blog(youtube_url: str, script_text: str, title: str = "") -> str:
    settings = load_settings()
    api_key = get_anthropic_key(settings)

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = settings["models"]["anthropic"]

    prompt = f"""아래 유튜브 영상을 기반으로 네이버/티스토리 블로그 포스팅을 작성해주세요.

## 영상 제목
{title}

## YouTube URL
{youtube_url}

## 대본 (참고용)
{script_text[:3000]}

## 블로그 글 작성 지침
- SEO 최적화된 제목 (H1)
- 도입부: 영상 핵심 내용 요약 (3-5문장)
- 본론: 3-4개 섹션 (H2 헤더 사용)
- 영상 임베드 섹션 (YouTube URL 포함)
- 마무리: 공감/댓글 유도
- 총 1200-1800자
- 해시태그 10개 (마지막에)

블로그 글만 출력해주세요.
"""

    message = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
