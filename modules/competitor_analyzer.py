"""경쟁 영상 리서치 모듈 (Gemini API)"""
import os
from pathlib import Path
from datetime import datetime
from modules.utils import load_settings

def research(source_text: str, output_dir: Path) -> str:
    settings = load_settings()
    api_key = settings["api_keys"]["gemini"]["api_key"]
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "Gemini API 키가 없습니다. config/settings.yaml을 확인하세요."

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "google-genai 패키지가 없습니다.\npip install google-genai 실행 후 재시도하세요."

    client = genai.Client(api_key=api_key)

    prompt = f"""당신은 유튜브 콘텐츠 전략 전문가입니다.
아래 소재와 관련된 유튜브 경쟁 영상을 분석해주세요.

## 소재
{source_text[:2000]}

## 분석 요청사항

### 1. 추천 검색 키워드
이 소재로 유튜브에서 검색할 만한 키워드 10개를 제안해주세요.

### 2. 예상 경쟁 영상 유형 분석
이 주제로 인기 있을 영상 유형을 5가지 분석해주세요:
- 제목 패턴
- 영상 길이
- 썸네일 스타일
- 주요 내용 구성

### 3. 차별화 전략
기존 콘텐츠와 차별화할 수 있는 포인트 3가지를 제안해주세요.

### 4. 추천 영상 구성
이 소재로 만들 영상의 최적 구성을 제안해주세요:
- 인트로 후킹 전략
- 핵심 섹션 구성
- 아웃트로 전략

### 5. SEO 전략
- 추천 제목 패턴 3가지
- 핵심 태그 15개
- 설명란 전략

분석 결과를 구체적이고 실용적으로 작성해주세요.
"""

    print("  Gemini AI로 리서치 중...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    result = response.text

    # 저장
    research_dir = output_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = research_dir / f"analysis_{ts}.txt"
    out_file.write_text(result, encoding="utf-8")

    print(f"  저장 완료: {out_file}")
    return result
