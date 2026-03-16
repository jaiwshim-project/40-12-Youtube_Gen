"""MoviePy + Whisper 영상 자동 빌드 모듈"""
import re
import subprocess
from pathlib import Path


# ── 시간 포맷 ─────────────────────────────────────────────────
def _srt_time(secs: float) -> str:
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ── 자막 생성 (Whisper) ────────────────────────────────────────
def generate_srt(audio_path: str, progress_cb=None) -> str:
    """음성 파일에서 SRT 자막 생성. Whisper 미설치 시 빈 문자열 반환."""
    if progress_cb:
        progress_cb("  자막 생성 중 (Whisper)...")

    # faster-whisper 우선 (더 빠름)
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, language="ko", beam_size=5)
        lines = []
        for i, seg in enumerate(segments, 1):
            lines += [str(i), f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}",
                      seg.text.strip(), ""]
        if progress_cb:
            progress_cb(f"  ✅ 자막 생성 완료 ({len(lines)//4}개 구간)")
        return "\n".join(lines)
    except ImportError:
        pass

    # openai-whisper 폴백
    try:
        import whisper
        result = whisper.load_model("base").transcribe(audio_path, language="ko")
        lines = []
        for i, seg in enumerate(result["segments"], 1):
            lines += [str(i), f"{_srt_time(seg['start'])} --> {_srt_time(seg['end'])}",
                      seg["text"].strip(), ""]
        if progress_cb:
            progress_cb(f"  ✅ 자막 생성 완료 ({len(lines)//4}개 구간)")
        return "\n".join(lines)
    except ImportError:
        if progress_cb:
            progress_cb("  [자막 건너뜀] faster-whisper 또는 openai-whisper 미설치")
        return ""


# ── 영상 빌드 ─────────────────────────────────────────────────
def build_video(image_paths: list, audio_path: str,
                srt_path: str, output_path: str, progress_cb=None) -> bool:
    """이미지 슬라이드쇼 + 음성 + 자막 → MP4"""
    if not image_paths:
        raise ValueError("이미지 파일이 없습니다. Step 3 이미지 생성을 먼저 실행하세요.")
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"음성 파일 없음: {audio_path}\nStep 2 재료 생성을 먼저 실행하세요.")

    # MoviePy import (1.x / 2.x 호환)
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
        def make_clip(path, dur):
            return ImageClip(path).set_duration(dur).resize(height=1080)
        def set_audio(video, audio):
            return video.set_audio(audio)
    except ImportError:
        try:
            from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
            def make_clip(path, dur):
                return ImageClip(path).with_duration(dur).resized(height=1080)
            def set_audio(video, audio):
                return video.with_audio(audio)
        except ImportError:
            raise ImportError(
                "moviepy 패키지가 없습니다.\n"
                "pip install moviepy"
            )

    if progress_cb:
        progress_cb("  오디오 로드 중...")
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    per_img = duration / len(image_paths)

    if progress_cb:
        progress_cb(
            f"  이미지 {len(image_paths)}장 × {per_img:.1f}초 = 총 {duration:.1f}초"
        )

    clips = [make_clip(p, per_img) for p in image_paths]
    video = set_audio(concatenate_videoclips(clips, method="compose"), audio)

    # 자막 없는 임시 파일
    has_srt = srt_path and Path(srt_path).exists()
    temp_path = str(output_path).replace(".mp4", "_nosub.mp4")
    render_target = temp_path if has_srt else output_path

    if progress_cb:
        progress_cb("  영상 렌더링 중... (수 분 소요 가능)")
    video.write_videofile(
        render_target, fps=24, codec="libx264", audio_codec="aac", logger=None
    )

    # FFmpeg로 자막 burn-in
    if has_srt:
        if progress_cb:
            progress_cb("  자막 삽입 중 (FFmpeg)...")
        srt_abs = str(Path(srt_path).resolve()).replace("\\", "/")
        style = (
            "FontName=NanumGothic,FontSize=18,Alignment=2,"
            "MarginV=40,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1"
        )
        cmd = [
            "ffmpeg", "-y", "-i", temp_path,
            "-vf", f"subtitles='{srt_abs}':force_style='{style}'",
            "-codec:a", "copy", output_path
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            Path(temp_path).unlink(missing_ok=True)
        except Exception as e:
            if progress_cb:
                progress_cb(f"  [자막 삽입 실패, 원본 사용]: {e}")
            import shutil
            shutil.move(temp_path, output_path)

    if progress_cb:
        progress_cb(f"  ✅ 영상 완성: {output_path}")
    return True
