"""YouTube 올인원 자동화 웹 플랫폼"""
from flask import Flask, request, jsonify, send_from_directory
import subprocess, sys, os, json, threading, yaml
from pathlib import Path
from datetime import datetime

app = Flask(__name__, static_folder="web/static", template_folder="web")
ROOT = Path(__file__).parent
logs = {}

# ── 유틸 ──────────────────────────────────────────────────────
def read_file(path):
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_settings():
    p = ROOT / "config" / "settings.yaml"
    if not p.exists():
        return {"api_keys": {"anthropic": {"api_key": ""}, "gemini": {"api_key": ""}, "elevenlabs": {"api_key": "", "voice_id": ""}}, "models": {"anthropic": "claude-sonnet-4-6"}, "style": {"tone": "", "target_audience": ""}}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_settings(data):
    p = ROOT / "config" / "settings.yaml"
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

def run_task(task_id, cmd):
    logs[task_id] = {"status": "running", "output": ""}
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", cwd=str(ROOT)
        )
        for line in proc.stdout:
            logs[task_id]["output"] += line
        proc.wait()
        logs[task_id]["status"] = "done" if proc.returncode == 0 else "error"
    except Exception as e:
        logs[task_id]["output"] += f"\n오류: {e}"
        logs[task_id]["status"] = "error"

# ── 정적 파일 ──────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("web/static", path)

# ── 설정 API ──────────────────────────────────────────────────
@app.route("/api/settings", methods=["GET"])
def get_settings():
    s = load_settings()
    return jsonify({
        "anthropic": s["api_keys"]["anthropic"]["api_key"],
        "gemini":    s["api_keys"]["gemini"]["api_key"],
        "elevenlabs": s["api_keys"]["elevenlabs"]["api_key"],
        "elevenlabs_voice": s["api_keys"]["elevenlabs"].get("voice_id",""),
        "model": s["models"]["anthropic"],
        "tone": s["style"]["tone"],
        "audience": s["style"]["target_audience"],
    })

@app.route("/api/settings", methods=["POST"])
def post_settings():
    d = request.json
    s = load_settings()
    s["api_keys"]["anthropic"]["api_key"]  = d.get("anthropic", "")
    s["api_keys"]["gemini"]["api_key"]     = d.get("gemini", "")
    s["api_keys"]["elevenlabs"]["api_key"] = d.get("elevenlabs", "")
    s["api_keys"]["elevenlabs"]["voice_id"]= d.get("elevenlabs_voice", "21m00Tcm4TlvDq8ikWAM")
    s["models"]["anthropic"]               = d.get("model", "claude-sonnet-4-6")
    s["style"]["tone"]                     = d.get("tone", "따뜻하고 감성적인")
    s["style"]["target_audience"]          = d.get("audience", "30-60대 감성 콘텐츠 시청자")
    save_settings(s)
    return jsonify({"ok": True})

# ── 데이터 API ─────────────────────────────────────────────────
@app.route("/api/outputs")
def list_outputs():
    out_dir = ROOT / "output"
    if not out_dir.exists():
        return jsonify([])
    folders = sorted([f.name for f in out_dir.iterdir() if f.is_dir()
                      and not f.name.startswith("research")], reverse=True)
    result = []
    for f in folders:
        video_path = ROOT / "output" / f / "07_video" / "final_video.mp4"
        result.append({
            "ts": f,
            "title":       read_file(f"output/{f}/00_script/title.txt"),
            "thumbnail":   read_file(f"output/{f}/00_script/thumbnail.txt"),
            "script":      read_file(f"output/{f}/00_script/script.txt"),
            "prompts":     read_file(f"output/{f}/03_prompts/image_prompts.txt"),
            "guide":       read_file(f"output/{f}/04_guide/vrew_guide.md"),
            "timeline":    read_file(f"output/{f}/04_guide/timeline.md"),
            "meta_title":  read_file(f"output/{f}/05_metadata/title.txt"),
            "description": read_file(f"output/{f}/05_metadata/description.txt"),
            "tags":        read_file(f"output/{f}/05_metadata/tags.txt"),
            "blog":        read_file(f"output/{f}/06_blog/blog_post.txt"),
            "youtube_url": read_file(f"output/{f}/07_video/youtube_url.txt"),
            "has_video":   video_path.exists(),
            "image_count": len(list((ROOT / "output" / f / "02_images").glob("*.png")))
                           if (ROOT / "output" / f / "02_images").exists() else 0,
        })
    return jsonify(result)

@app.route("/api/inputs")
def list_inputs():
    inp = ROOT / "input"
    if not inp.exists():
        return jsonify([])
    return jsonify([f.name for f in inp.iterdir() if f.is_file()])

@app.route("/api/save", methods=["POST"])
def save_file_api():
    d = request.json
    path = (ROOT / d.get("path", "")).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        return jsonify({"ok": False, "error": "invalid path"}), 400
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(d.get("content", ""), encoding="utf-8")
    return jsonify({"ok": True})

@app.route("/api/file", methods=["POST"])
def read_file_api():
    d = request.json
    path = (ROOT / d.get("path", "")).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        return jsonify({"ok": False, "error": "invalid path"}), 400
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    return jsonify({"content": content})

# ── 실행 API ──────────────────────────────────────────────────
@app.route("/api/run/research", methods=["POST"])
def run_research():
    d = request.json
    source = d.get("source", "")
    if not source:
        return jsonify({"error": "source required"}), 400
    tid = f"research_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--research", source]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/write", methods=["POST"])
def run_write():
    d = request.json
    source = d.get("source", "")
    if not source:
        return jsonify({"error": "source required"}), 400
    tid = f"write_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--write", source]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/generate", methods=["POST"])
def run_generate():
    d = request.json
    ts    = d.get("ts")
    source = d.get("source", "")
    short  = d.get("short", False)
    if not ts or not source:
        return jsonify({"error": "ts and source required"}), 400
    tid = f"gen_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py",
           f"output/{ts}/00_script/script.txt", "--source", source]
    if short:
        cmd.append("--short")
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/images", methods=["POST"])
def run_images():
    d = request.json
    ts = d.get("ts")
    if not ts:
        return jsonify({"error": "ts required"}), 400
    tid = f"images_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--images", f"output/{ts}"]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/video", methods=["POST"])
def run_video():
    d = request.json
    ts = d.get("ts")
    if not ts:
        return jsonify({"error": "ts required"}), 400
    tid = f"video_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--video", f"output/{ts}"]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/upload", methods=["POST"])
def run_upload():
    d = request.json
    ts      = d.get("ts")
    privacy = d.get("privacy", "private")
    if not ts:
        return jsonify({"error": "ts required"}), 400
    tid = f"upload_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--upload", f"output/{ts}",
           "--privacy", privacy]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/run/blog", methods=["POST"])
def run_blog():
    d = request.json
    url = d.get("url")
    ts  = d.get("ts")
    if not url or not ts:
        return jsonify({"error": "url and ts required"}), 400
    tid = f"blog_{datetime.now().strftime('%H%M%S')}"
    cmd = [sys.executable, "orchestrator.py", "--blog", url, f"output/{ts}"]
    threading.Thread(target=run_task, args=(tid, cmd), daemon=True).start()
    return jsonify({"task_id": tid})

@app.route("/api/log/<task_id>")
def get_log(task_id):
    return jsonify(logs.get(task_id, {"status": "not_found", "output": ""}))

# ── 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  YouTube 자동화 플랫폼")
    print("  http://localhost:5000")
    print("  종료: Ctrl+C")
    print("="*50 + "\n")
    app.run(debug=False, port=5000)
