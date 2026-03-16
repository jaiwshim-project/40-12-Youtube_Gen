#!/usr/bin/env python3
"""YouTube 영상 올인원 오케스트레이터"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_output_dir(ts=None):
    if ts is None:
        ts = get_timestamp()
    out = Path(__file__).parent / "output" / ts
    for sub in ["00_script", "01_voice", "02_images", "03_prompts",
                "04_guide", "05_metadata", "06_blog", "07_video"]:
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out

def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"[오류] 파일을 찾을 수 없습니다: {path}")
        sys.exit(1)
    return p.read_text(encoding="utf-8")


# ── Step 1: 대본 ───────────────────────────────────────────────
def cmd_write(source_path: str, ref_path: str = ""):
    print("\n" + "="*50)
    print("  Step 1: 제목 + 썸네일 + 대본 생성")
    print("="*50)

    from modules.script_writer import write_script

    source_text = read_file(source_path)
    ref_text = read_file(ref_path) if ref_path else ""

    print(f"  소재 파일: {source_path}")
    print("  Claude AI로 대본 생성 중...")

    result = write_script(source_text, ref_text)

    ts = get_timestamp()
    out = create_output_dir(ts)

    (out / "00_script" / "source.txt").write_text(source_text, encoding="utf-8")
    (out / "00_script" / "title.txt").write_text(result["title"], encoding="utf-8")
    (out / "00_script" / "thumbnail.txt").write_text(result["thumbnail"], encoding="utf-8")
    (out / "00_script" / "script.txt").write_text(result["script"], encoding="utf-8")

    print(f"\n  ✅ 저장 완료: {out / '00_script'}")
    print(f"\n  다음 단계:")
    print(f"  python orchestrator.py {out / '00_script' / 'script.txt'} --source {source_path}")

    return str(out)


# ── Step 2: 재료 생성 ──────────────────────────────────────────
def cmd_generate(script_path: str, source_path: str = "", short: bool = False):
    print("\n" + "="*50)
    print(f"  Step 2: 영상 재료 생성 ({'숏폼' if short else '롱폼'})")
    print("="*50)

    from modules.prompt_generator import generate_prompts
    from modules.guide_generator import generate_guide
    from modules.metadata_generator import generate_metadata
    from modules.voice_generator import generate_voice
    from modules.clipboard_helper import copy_to_clipboard, get_first_prompt

    script_text = read_file(script_path)

    script_p = Path(script_path)
    if "output" in str(script_p):
        out = script_p.parent.parent
    else:
        ts = get_timestamp()
        out = create_output_dir(ts)
        (out / "00_script" / "script.txt").write_text(script_text, encoding="utf-8")

    title_draft = ""
    title_file = out / "00_script" / "title.txt"
    if title_file.exists():
        title_draft = title_file.read_text(encoding="utf-8")

    print("\n  [1/4] 이미지 프롬프트 생성 중...")
    prompts = generate_prompts(script_text, short)
    (out / "03_prompts" / "image_prompts.txt").write_text(prompts, encoding="utf-8")
    print(f"  ✅ 이미지 프롬프트 저장")

    first_prompt = get_first_prompt(prompts)
    if first_prompt and copy_to_clipboard(first_prompt):
        print("  📋 첫 번째 프롬프트가 클립보드에 복사됨")

    print("\n  [2/4] 음성 생성 중...")
    voice_path = str(out / "01_voice" / "narration.mp3")
    generate_voice(script_text, voice_path)

    print("\n  [3/4] Vrew 편집 가이드 생성 중...")
    guide_result = generate_guide(script_text, short)
    (out / "04_guide" / "vrew_guide.md").write_text(guide_result["guide"], encoding="utf-8")
    (out / "04_guide" / "timeline.md").write_text(guide_result["timeline"], encoding="utf-8")
    print(f"  ✅ Vrew 가이드 저장")

    print("\n  [4/4] 메타데이터 생성 중...")
    meta = generate_metadata(script_text, title_draft)
    (out / "05_metadata" / "title.txt").write_text(meta["title"], encoding="utf-8")
    (out / "05_metadata" / "description.txt").write_text(meta["description"], encoding="utf-8")
    (out / "05_metadata" / "tags.txt").write_text(meta["tags"], encoding="utf-8")
    print(f"  ✅ 메타데이터 저장")

    print("\n" + "="*50)
    print(f"  ✅ 재료 생성 완료! 출력: {out}")
    print("="*50)
    print(f"\n  다음 자동 단계:")
    print(f"  python orchestrator.py --images {out}   ← Imagen 3 이미지 생성")
    print(f"  python orchestrator.py --video  {out}   ← 영상 빌드")
    print(f"  python orchestrator.py --upload {out}   ← YouTube 업로드")


# ── Step 3: 이미지 자동 생성 (Imagen 3) ───────────────────────
def cmd_images(output_folder: str):
    print("\n" + "="*50)
    print("  Step 3: Imagen 3 이미지 자동 생성")
    print("="*50)

    from modules.image_generator import generate_images

    out = Path(output_folder)
    prompts_file = out / "03_prompts" / "image_prompts.txt"
    if not prompts_file.exists():
        print("[오류] 이미지 프롬프트 파일이 없습니다. Step 2를 먼저 실행하세요.")
        sys.exit(1)

    prompts_text = prompts_file.read_text(encoding="utf-8")
    images_dir = out / "02_images"

    paths = generate_images(prompts_text, images_dir, progress_cb=print)

    print(f"\n  ✅ 이미지 {len(paths)}장 생성 완료: {images_dir}")
    print(f"\n  다음 단계:")
    print(f"  python orchestrator.py --video {out}")


# ── Step 6: 영상 자동 빌드 ────────────────────────────────────
def cmd_video(output_folder: str):
    print("\n" + "="*50)
    print("  Step 6: 영상 자동 빌드 (MoviePy + Whisper)")
    print("="*50)

    from modules.video_builder import generate_srt, build_video

    out = Path(output_folder)
    images_dir = out / "02_images"
    audio_path = out / "01_voice" / "narration.mp3"
    video_dir  = out / "07_video"
    video_dir.mkdir(exist_ok=True)

    # 이미지 목록
    image_paths = sorted(images_dir.glob("image_*.png"))
    if not image_paths:
        image_paths = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg"))
    if not image_paths:
        print("[오류] 이미지 파일이 없습니다. Step 3 이미지 생성을 먼저 실행하세요.")
        sys.exit(1)

    print(f"  이미지 {len(image_paths)}장 발견")

    # SRT 자막 생성
    srt_path = ""
    if audio_path.exists():
        srt_text = generate_srt(str(audio_path), progress_cb=print)
        if srt_text:
            srt_path = str(video_dir / "subtitles.srt")
            Path(srt_path).write_text(srt_text, encoding="utf-8")
    else:
        print("  [경고] 음성 파일 없음 — 음성 없이 영상 생성")

    # 영상 빌드
    output_path = str(video_dir / "final_video.mp4")
    build_video(
        image_paths=[str(p) for p in image_paths],
        audio_path=str(audio_path) if audio_path.exists() else "",
        srt_path=srt_path,
        output_path=output_path,
        progress_cb=print,
    )

    print(f"\n  ✅ 영상 완성: {output_path}")
    print(f"\n  다음 단계:")
    print(f"  python orchestrator.py --upload {out}   ← YouTube 업로드")


# ── Step 7: YouTube 업로드 ────────────────────────────────────
def cmd_upload(output_folder: str, privacy: str = "private"):
    print("\n" + "="*50)
    print("  Step 7: YouTube 자동 업로드")
    print("="*50)

    from modules.youtube_uploader import upload_video

    out = Path(output_folder)
    video_path   = out / "07_video" / "final_video.mp4"
    title_file   = out / "05_metadata" / "title.txt"
    desc_file    = out / "05_metadata" / "description.txt"
    tags_file    = out / "05_metadata" / "tags.txt"

    title       = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else "YouTube 영상"
    description = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else ""
    tags        = tags_file.read_text(encoding="utf-8").strip() if tags_file.exists() else ""

    print(f"  제목: {title[:60]}")
    print(f"  공개 설정: {privacy}")

    url = upload_video(str(video_path), title, description, tags,
                       privacy=privacy, progress_cb=print)

    # URL 저장
    url_file = out / "07_video" / "youtube_url.txt"
    url_file.write_text(url, encoding="utf-8")
    print(f"\n  YouTube URL: {url}")
    print(f"\n  블로그 글 생성:")
    print(f"  python orchestrator.py --blog {url} {out}")


# ── Step 5: 블로그 ────────────────────────────────────────────
def cmd_blog(youtube_url: str, output_folder: str):
    print("\n" + "="*50)
    print("  Step 5: 블로그 글 생성")
    print("="*50)

    from modules.blog_generator import generate_blog

    out = Path(output_folder)
    script_file = out / "00_script" / "script.txt"
    title_file  = out / "05_metadata" / "title.txt"

    script_text = script_file.read_text(encoding="utf-8") if script_file.exists() else ""
    title       = title_file.read_text(encoding="utf-8") if title_file.exists() else ""

    print("  블로그 글 생성 중...")
    blog_text = generate_blog(youtube_url, script_text, title)

    blog_dir  = out / "06_blog"
    blog_dir.mkdir(exist_ok=True)
    blog_file = blog_dir / "blog_post.txt"
    blog_file.write_text(blog_text, encoding="utf-8")

    print(f"\n  ✅ 블로그 글 저장: {blog_file}")


# ── main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="YouTube 영상 올인원 오케스트레이터")
    parser.add_argument("source", nargs="?", help="소재 파일 또는 대본 파일 경로")
    parser.add_argument("--write",    action="store_true", help="Step 1: 대본 생성")
    parser.add_argument("--ref",      help="리서치 폴더 경로")
    parser.add_argument("--source",   dest="source_file",  help="Step 2용 소재 파일")
    parser.add_argument("--short",    action="store_true", help="숏폼 형식")
    parser.add_argument("--blog",     metavar="URL",       help="Step 5: 블로그 생성")
    parser.add_argument("--research", action="store_true", help="Step 0: 경쟁 영상 리서치")
    parser.add_argument("--analyze",  metavar="URL",       help="Step 0-B: URL 분석")
    parser.add_argument("--images",   metavar="OUTPUT",    help="Step 3: Imagen 3 이미지 생성")
    parser.add_argument("--video",    metavar="OUTPUT",    help="Step 6: 영상 자동 빌드")
    parser.add_argument("--upload",   metavar="OUTPUT",    help="Step 7: YouTube 업로드")
    parser.add_argument("--privacy",  default="private",
                        choices=["private", "unlisted", "public"],
                        help="YouTube 공개 설정 (기본: private)")

    args = parser.parse_args()

    if args.research:
        from modules.competitor_analyzer import research
        if not args.source:
            print("[오류] 소재 파일 경로를 입력해주세요.")
            sys.exit(1)
        source_text = read_file(args.source)
        out_dir = Path(__file__).parent / "output"
        print("\n" + "="*50)
        print("  Step 0: 경쟁 영상 리서치 (Gemini)")
        print("="*50)
        result = research(source_text, out_dir)
        print(result)
        return

    if args.analyze:
        print(f"[Step 0-B] URL 분석: {args.analyze}")
        return

    if args.images:
        cmd_images(args.images)
        return

    if args.video:
        cmd_video(args.video)
        return

    if args.upload:
        cmd_upload(args.upload, privacy=args.privacy)
        return

    if args.blog:
        if not args.source:
            print("[오류] 출력 폴더 경로가 필요합니다.")
            print("  사용법: python orchestrator.py --blog <URL> <출력폴더>")
            sys.exit(1)
        cmd_blog(args.blog, args.source)
        return

    if args.write or (args.source and not args.source_file):
        source = args.source
        if not source:
            print("[오류] 소재 파일 경로를 입력해주세요.")
            sys.exit(1)
        ref = ""
        if args.ref:
            ref_path = Path(args.ref) / "analysis.txt"
            if ref_path.exists():
                ref = ref_path.read_text(encoding="utf-8")
        cmd_write(source, ref)
        return

    if args.source and args.source_file:
        cmd_generate(args.source, args.source_file, args.short)
        return

    print("""
YouTube 영상 올인원 오케스트레이터

── 기본 파이프라인 ──────────────────────────────
  Step 0  리서치:    python orchestrator.py --research <소재파일>
  Step 1  대본:      python orchestrator.py --write <소재파일>
  Step 2  재료:      python orchestrator.py <대본파일> --source <소재파일>
  Step 3  이미지:    python orchestrator.py --images <출력폴더>
  Step 5  블로그:    python orchestrator.py --blog <YouTube_URL> <출력폴더>

── 완전 자동화 (이미지→영상→업로드) ───────────────
  Step 3  이미지:    python orchestrator.py --images output/폴더명
  Step 6  영상빌드:  python orchestrator.py --video  output/폴더명
  Step 7  업로드:    python orchestrator.py --upload output/폴더명
                     python orchestrator.py --upload output/폴더명 --privacy public
""")


if __name__ == "__main__":
    main()
