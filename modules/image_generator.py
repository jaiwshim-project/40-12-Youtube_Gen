"""Google Imagen 3 이미지 자동 생성 모듈"""
import os
import re
from pathlib import Path
from modules.utils import load_settings


def parse_en_prompts(prompts_text: str) -> list:
    """프롬프트 텍스트에서 영어 프롬프트 + 한글 설명 추출"""
    blocks = [b.strip() for b in prompts_text.split("---") if b.strip()]
    result = []
    for block in blocks:
        ko_m = re.search(r"한글 설명:\s*(.+)", block)
        en_m = re.search(r"영어 프롬프트:\s*([\s\S]+)", block)
        if en_m:
            result.append({
                "ko": ko_m.group(1).strip() if ko_m else block.split("\n")[0],
                "en": en_m.group(1).strip(),
            })
    return result


def generate_images(prompts_text: str, output_dir: Path, progress_cb=None) -> list:
    """Imagen 3으로 이미지 생성 후 저장, 파일 경로 목록 반환"""
    settings = load_settings()
    api_key = settings["api_keys"]["gemini"]["api_key"]
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Gemini API 키가 없습니다. config/settings.yaml에서 설정하세요.")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai 패키지가 없습니다.\npip install google-genai")

    client = genai.Client(api_key=api_key)
    prompts = parse_en_prompts(prompts_text)
    if not prompts:
        raise ValueError("프롬프트를 파싱할 수 없습니다. Step 2를 먼저 실행하세요.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []

    for i, p in enumerate(prompts):
        if progress_cb:
            progress_cb(f"  [{i+1}/{len(prompts)}] {p['ko'][:35]}...")
        try:
            response = client.models.generate_images(
                model="imagen-3.0-generate-015",
                prompt=p["en"],
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="block_some",
                ),
            )
            if response.generated_images:
                path = output_dir / f"image_{i+1:02d}.png"
                path.write_bytes(response.generated_images[0].image.image_bytes)
                image_paths.append(str(path))
                if progress_cb:
                    progress_cb(f"  ✅ 저장: {path.name}")
            else:
                if progress_cb:
                    progress_cb(f"  ⚠️ 이미지 {i+1}: 응답 없음 (안전 필터 가능성)")
        except Exception as e:
            if progress_cb:
                progress_cb(f"  ⚠️ 이미지 {i+1} 생성 실패: {e}")

    return image_paths
