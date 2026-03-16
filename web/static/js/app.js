/* ── 상태 ── */
let currentTs = null;
let pollTimer = null;

/* ── 초기화 ── */
document.addEventListener("DOMContentLoaded", () => {
  setupStepNav();
  setupTabNav();
  loadInputFiles();
  loadOutputList();
});

/* ── 스텝 네비게이션 ── */
function setupStepNav() {
  document.querySelectorAll(".step-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".step-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".step-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.step).classList.add("active");
    });
  });
}

/* ── 탭 네비게이션 ── */
function setupTabNav() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const parent = btn.closest(".result-box");
      parent.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      parent.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });
}

/* ── 소재 파일 목록 로드 ── */
async function loadInputFiles() {
  const res = await fetch("/api/inputs");
  const files = await res.json();
  ["s0-source","s1-source","s2-source"].forEach(id => {
    const sel = document.getElementById(id);
    sel.innerHTML = files.map(f => `<option value="input/${f}">${f}</option>`).join("");
  });
}

/* ── 출력 폴더 목록 ── */
async function loadOutputList() {
  const res = await fetch("/api/outputs");
  const outputs = await res.json();
  const listEl = document.getElementById("outputList");

  listEl.innerHTML = outputs.length === 0
    ? '<div style="font-size:0.78rem;color:#555">아직 생성된 파일이 없습니다</div>'
    : outputs.map(o => `
        <div class="output-item" onclick="selectOutput('${o.ts}')" data-ts="${o.ts}">
          📄 ${o.ts.replace(/_/g," ")}
        </div>`).join("");

  // Step 2,3,4,5 셀렉트 업데이트
  ["s2-ts","s3-ts","s4-ts","s5-ts"].forEach(id => {
    const sel = document.getElementById(id);
    sel.innerHTML = outputs.map(o => `<option value="${o.ts}">${o.ts}</option>`).join("");
  });

  if (outputs.length > 0) {
    selectOutput(outputs[0].ts, outputs[0]);
  }

  return outputs;
}

function selectOutput(ts, data) {
  currentTs = ts;
  document.querySelectorAll(".output-item").forEach(el => {
    el.classList.toggle("selected", el.dataset.ts === ts);
  });
  ["s2-ts","s3-ts","s4-ts","s5-ts"].forEach(id => {
    const sel = document.getElementById(id);
    if (sel) sel.value = ts;
  });
}

/* ── Step 0: 리서치 ── */
async function runResearch() {
  const source = document.getElementById("s0-source").value;
  const log = document.getElementById("s0-log");
  log.classList.remove("hidden");
  log.textContent = "리서치 기능은 Gemini API 연동 개발 중입니다.\n현재 config/settings.yaml에 Gemini API 키가 설정되어 있습니다.";
}

/* ── Step 1: 대본 생성 ── */
async function runWrite() {
  const source = document.getElementById("s1-source").value;
  const log = document.getElementById("s1-log");
  log.classList.remove("hidden");
  log.textContent = "⏳ 대본 생성 중...\n";

  const res = await fetch("/api/run/write", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({source})
  });
  const {task_id} = await res.json();
  pollLog(task_id, log, async () => {
    await loadOutputList();
    const outputs = await (await fetch("/api/outputs")).json();
    if (outputs.length > 0) {
      const latest = outputs[0];
      currentTs = latest.ts;
      showStep1Result(latest);
    }
  });
}

function showStep1Result(data) {
  document.getElementById("r1-title-text").textContent = data.title || "(없음)";
  document.getElementById("r1-thumb-text").textContent = data.thumbnail || "(없음)";
  document.getElementById("r1-script-text").value = data.script || "";
  document.getElementById("s1-result").classList.remove("hidden");
}

async function saveScript() {
  const ts = currentTs;
  if (!ts) return alert("출력 폴더를 먼저 선택하세요.");
  const content = document.getElementById("r1-script-text").value;
  await fetch("/api/save", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({path: `output/${ts}/00_script/script.txt`, content})
  });
  alert("💾 저장 완료!");
}

/* ── Step 2: 재료 생성 ── */
async function runGenerate() {
  const ts = document.getElementById("s2-ts").value;
  const source = document.getElementById("s2-source").value;
  const short = document.getElementById("s2-short").checked;
  const log = document.getElementById("s2-log");
  log.classList.remove("hidden");
  log.textContent = "⏳ 재료 생성 중...\n";

  const res = await fetch("/api/run/generate", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ts, source, short})
  });
  const {task_id} = await res.json();
  pollLog(task_id, log, async () => {
    const outputs = await (await fetch("/api/outputs")).json();
    const found = outputs.find(o => o.ts === ts);
    if (found) showStep2Result(found);
  });
}

function showStep2Result(data) {
  // 프롬프트 카드
  const raw = data.prompts || "";
  const cards = parsePrompts(raw);
  document.getElementById("r2-prompt-list").innerHTML = cards.map((c,i) => `
    <div class="prompt-card">
      <div class="prompt-num">${i+1}</div>
      <div class="prompt-body">
        <div class="prompt-ko">${c.ko}</div>
        <div class="prompt-en">${c.en}</div>
        <button class="btn-copy" onclick="copyText(this, \`${c.en.replace(/`/g,"'")}\`)">📋 복사</button>
      </div>
    </div>`).join("");

  // 가이드 (마크다운 간단 렌더)
  document.getElementById("r2-guide-text").innerHTML = mdToHtml(data.guide || "");

  // 메타데이터
  document.getElementById("r2-meta-title").textContent = data.meta_title || "";
  document.getElementById("r2-meta-desc").textContent = data.description || "";
  document.getElementById("r2-meta-tags").textContent = data.tags || "";

  document.getElementById("s2-result").classList.remove("hidden");
}

/* ── Step 3: 이미지 프롬프트 ── */
async function loadPrompts() {
  const ts = document.getElementById("s3-ts").value;
  const res = await fetch("/api/file", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({path: `output/${ts}/03_prompts/image_prompts.txt`})
  });
  const {content} = await res.json();
  const cards = parsePrompts(content);
  const el = document.getElementById("s3-prompts");
  el.innerHTML = cards.map((c,i) => `
    <div class="prompt-card">
      <div class="prompt-num">${i+1}</div>
      <div class="prompt-body">
        <div class="prompt-ko">${c.ko}</div>
        <div class="prompt-en">${c.en}</div>
        <button class="btn-copy" onclick="copyText(this, \`${c.en.replace(/`/g,"'")}\`)">📋 복사</button>
      </div>
    </div>`).join("");
  el.classList.remove("hidden");
}

/* ── Step 4: 가이드 ── */
async function loadGuide() {
  const ts = document.getElementById("s4-ts").value;
  const [g, t] = await Promise.all([
    fetch("/api/file", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:`output/${ts}/04_guide/vrew_guide.md`})}).then(r=>r.json()),
    fetch("/api/file", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({path:`output/${ts}/04_guide/timeline.md`})}).then(r=>r.json()),
  ]);
  const gEl = document.getElementById("s4-guide");
  const tEl = document.getElementById("s4-timeline");
  gEl.innerHTML = mdToHtml(g.content || "");
  tEl.innerHTML = mdToHtml(t.content || "");
  gEl.classList.remove("hidden");
  tEl.classList.remove("hidden");
}

/* ── Step 5: 블로그 ── */
async function runBlog() {
  const url = document.getElementById("s5-url").value;
  const ts = document.getElementById("s5-ts").value;
  if (!url) return alert("YouTube URL을 입력하세요.");
  const log = document.getElementById("s5-log");
  log.classList.remove("hidden");
  log.textContent = "⏳ 블로그 글 생성 중...\n";

  const res = await fetch("/api/run/blog", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({url, ts})
  });
  const {task_id} = await res.json();
  pollLog(task_id, log, async () => {
    const r = await fetch("/api/file", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({path: `output/${ts}/06_blog/blog_post.txt`})
    });
    const {content} = await r.json();
    document.getElementById("s5-blog-text").textContent = content;
    document.getElementById("s5-result").classList.remove("hidden");
  });
}

function copyBlog() {
  const text = document.getElementById("s5-blog-text").textContent;
  navigator.clipboard.writeText(text);
  alert("📋 복사 완료!");
}

/* ── 유틸 ── */
function pollLog(task_id, logEl, onDone) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const r = await fetch(`/api/log/${task_id}`);
    const data = await r.json();
    logEl.textContent = data.output || "실행 중...";
    logEl.scrollTop = logEl.scrollHeight;
    if (data.status === "done" || data.status === "error") {
      clearInterval(pollTimer);
      if (data.status === "done" && onDone) onDone();
    }
  }, 1000);
}

function parsePrompts(raw) {
  const blocks = raw.split("---").map(b => b.trim()).filter(Boolean);
  return blocks.map(block => {
    const koMatch = block.match(/한글 설명:\s*(.+)/);
    const enMatch = block.match(/영어 프롬프트:\s*([\s\S]+)/);
    return {
      ko: koMatch ? koMatch[1].trim() : block.split("\n")[0],
      en: enMatch ? enMatch[1].trim() : ""
    };
  });
}

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = "✅ 복사됨";
    setTimeout(() => btn.textContent = "📋 복사", 2000);
  });
}

function mdToHtml(md) {
  return md
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^\|(.+)\|$/gm, row => {
      const cells = row.split("|").slice(1,-1).map(c => c.trim());
      return "<tr>" + cells.map(c => `<td>${c}</td>`).join("") + "</tr>";
    })
    .replace(/(<tr>.*<\/tr>\n?)+/g, match => `<table>${match}</table>`)
    .replace(/\n{2,}/g, "\n\n")
    .replace(/\n/g, "<br>");
}
