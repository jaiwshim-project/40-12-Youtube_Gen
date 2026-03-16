"""
web/index.html을 템플릿으로 사용하여 완전 독립형 index.html 생성.
데이터를 직접 embed하므로 Flask 서버 없이도 결과를 조회할 수 있음.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent


def read(path):
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_outputs():
    out_dir = ROOT / "output"
    if not out_dir.exists():
        return []
    folders = sorted(
        [f for f in out_dir.iterdir()
         if f.is_dir() and not f.name.startswith("research")],
        key=lambda x: x.name, reverse=True
    )
    result = []
    for f in folders:
        ts = f.name
        video_path = f / "07_video" / "final_video.mp4"
        images_dir = f / "02_images"
        result.append({
            "ts":          ts,
            "title":       read(f"output/{ts}/00_script/title.txt"),
            "thumbnail":   read(f"output/{ts}/00_script/thumbnail.txt"),
            "script":      read(f"output/{ts}/00_script/script.txt"),
            "prompts":     read(f"output/{ts}/03_prompts/image_prompts.txt"),
            "guide":       read(f"output/{ts}/04_guide/vrew_guide.md"),
            "timeline":    read(f"output/{ts}/04_guide/timeline.md"),
            "meta_title":  read(f"output/{ts}/05_metadata/title.txt"),
            "description": read(f"output/{ts}/05_metadata/description.txt"),
            "tags":        read(f"output/{ts}/05_metadata/tags.txt"),
            "blog":        read(f"output/{ts}/06_blog/blog_post.txt"),
            "youtube_url": read(f"output/{ts}/07_video/youtube_url.txt"),
            "has_video":   video_path.exists(),
            "image_count": len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0,
        })
    return result


def load_inputs():
    inp = ROOT / "input"
    if not inp.exists():
        return []
    return [f.name for f in inp.iterdir() if f.is_file()]


def build():
    outputs = load_outputs()
    inputs  = load_inputs()

    # web/index.html을 템플릿으로 읽기
    template_path = ROOT / "web" / "index.html"
    html = template_path.read_text(encoding="utf-8")

    # 데이터 JS 생성
    data_js = (
        f"const DATA = {json.dumps(outputs, ensure_ascii=False, indent=2)};\n"
        f"const INPUTS = {json.dumps(inputs, ensure_ascii=False)};\n"
    )

    # placeholder에 데이터 inject
    html = html.replace("/* __STANDALONE_DATA__ */", data_js, 1)

    out_path = ROOT / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"index.html 생성 완료: {out_path}")
    print(f"  출력 폴더 {len(outputs)}개 포함")
    return out_path


if __name__ == "__main__":
    import os
    path = build()
    os.startfile(str(path))
