(() => {
  const $ = (id) => document.getElementById(id);
  const msg = $("msg");
  const checkBtn = $("check");
  const ruler = $("ruler");
  const history = [];

  const pct = (p) => (p * 100).toFixed(1) + "%";
  const isSpam = (label) => label === "SPAM";
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };

  /* ---------- status chips ---------- */
  function setStatus(id, state, text) {
    const e = $(id);
    e.dataset.state = state;
    e.querySelector(".st-text").textContent = text;
  }

  async function pollStatus() {
    try {
      const s = await (await fetch("/api/status")).json();
      setStatus("st-nb", s.nb.status, s.nb.status === "ready" ? "ready" : "model file missing");
      setStatus("st-hf", s.hf.status, { ready: "ready", loading: "loading", error: "unavailable" }[s.hf.status]);
      if (s.hf.model) $("hf-name").textContent = s.hf.model + " from Hugging Face";
      if (s.hf.status === "error") $("st-hf").title = s.hf.error || "";
      if (s.hf.status === "loading") setTimeout(pollStatus, 2000);
    } catch {
      setStatus("st-nb", "error", "server not reachable");
      setStatus("st-hf", "error", "server not reachable");
      setTimeout(pollStatus, 3000);
    }
  }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) pollStatus(); });

  /* ---------- composer ---------- */
  function updateCount() { $("count").textContent = msg.value.length + " / 5000"; }
  msg.addEventListener("input", () => { updateCount(); $("msg-error").textContent = ""; });
  msg.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") check(); });

  document.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      msg.value = btn.dataset.text;
      updateCount();
      $("msg-error").textContent = "";
      msg.focus();
    });
  });
  $("clear").addEventListener("click", () => { msg.value = ""; updateCount(); msg.focus(); });
  checkBtn.addEventListener("click", check);

  /* ---------- ruler ---------- */
  function moveMarker(key, prob) {
    const marker = $("mk-" + key);
    $("mk-" + key + "-v").textContent = pct(prob);
    marker.style.left = Math.min(Math.max(prob, 0), 1) * 100 + "%";
    marker.style.setProperty("--shift", prob < 0.15 ? "38%" : prob > 0.85 ? "-38%" : "0");
  }

  function showRuler(nb, hf) {
    if (!((nb && !nb.error) || (hf && !hf.error))) return;
    if (ruler.classList.contains("idle")) {
      ruler.classList.remove("idle");
      ["nb", "hf"].forEach((k) => { $("mk-" + k).style.left = "50%"; });
      void ruler.offsetWidth;
    }
    ["nb", "hf"].forEach((k) => {
      const r = k === "nb" ? nb : hf;
      const m = $("mk-" + k);
      if (r && !r.error) { m.style.display = ""; moveMarker(k, r.prob); }
      else m.style.display = "none";
    });
  }

  /* ---------- result pieces ---------- */
  function renderModel(outId, r) {
    const out = $(outId);
    out.textContent = "";
    if (r.error) {
      out.appendChild(el("span", "note", "Not available: " + r.error));
      return;
    }
    const pill = el("span", "pill " + (isSpam(r.label) ? "spam" : "safe"), r.label);
    const big = el("span", "pct", pct(r.prob));
    big.appendChild(el("small", "", "chance of spam"));
    out.append(pill, big);
  }

  function renderDecision(t) {
    const box = $("decision");
    box.hidden = false;
    box.className = "decision " + t.level;
    $("decision-title").textContent = t.decision;
    $("decision-reason").textContent = t.reason;
  }

  function renderWarnings(list) {
    const ul = $("warnings");
    ul.textContent = "";
    ul.hidden = !list || list.length === 0;
    (list || []).forEach((w) => ul.appendChild(el("li", "", w)));
  }

  function renderWords(ulId, words, emptyText) {
    const ul = $(ulId);
    ul.textContent = "";
    if (!words || words.length === 0) ul.appendChild(el("li", "none", emptyText));
    else words.forEach((w) => ul.appendChild(el("li", "", w.word)));
  }

  function renderExplain(ex) {
    const box = $("explain");
    if (!ex) { box.hidden = true; return; }
    box.hidden = false;
    renderWords("ex-spam", ex.spam_words, "None found");
    renderWords("ex-safe", ex.safe_words, "None found");
  }

  function clearResults() {
    $("decision").hidden = true;
    $("explain").hidden = true;
    renderWarnings([]);
  }

  /* ---------- history ---------- */
  function cell(r) {
    const td = document.createElement("td");
    if (r.error) { td.textContent = "n/a"; return td; }
    const wrap = el("span", "cell");
    wrap.append(el("span", "tag " + (isSpam(r.label) ? "spam" : "safe"), r.label), el("span", "num", pct(r.prob)));
    td.appendChild(wrap);
    return td;
  }

  function renderHistory() {
    const body = $("hist-body");
    body.textContent = "";
    history.forEach((h) => {
      const tr = document.createElement("tr");
      const tdMsg = el("td", "msg");
      const b = el("button", "", h.text);
      b.type = "button";
      b.title = "Load this message again";
      b.addEventListener("click", () => {
        msg.value = h.text;
        updateCount();
        msg.focus();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      tdMsg.appendChild(b);
      const tdRes = el("td", "result-" + h.triage.level, h.triage.decision);
      tr.append(tdMsg, cell(h.nb), cell(h.hf), tdRes);
      body.appendChild(tr);
    });
    $("hist-empty").hidden = history.length > 0;
    $("hist-clear").hidden = history.length === 0;
  }
  $("hist-clear").addEventListener("click", () => { history.length = 0; renderHistory(); });

  /* ---------- check ---------- */
  async function check() {
    const text = msg.value.trim();
    if (!text) {
      $("msg-error").textContent = "Enter a message first.";
      msg.focus();
      return;
    }
    checkBtn.disabled = true;
    checkBtn.textContent = $("st-hf").dataset.state === "loading" ? "Waiting for the pretrained model to load..." : "Checking...";
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      let data = {};
      try { data = await res.json(); } catch { /* not JSON */ }
      if (!res.ok) {
        $("msg-error").textContent = data.error || "Something went wrong. Try again.";
        return;
      }
      const { nb, hf } = data;
      showRuler(nb, hf);
      renderModel("out-nb", nb);
      renderModel("out-hf", hf);
      renderWarnings(data.warnings);
      renderDecision(data.triage);
      renderExplain(data.explanation);
      pollStatus();
      history.unshift({ text, nb, hf, triage: data.triage });
      if (history.length > 10) history.pop();
      renderHistory();
    } catch {
      $("msg-error").textContent = "Cannot reach the app server. Check that python server.py is still running.";
    } finally {
      checkBtn.disabled = false;
      checkBtn.textContent = "Check message";
    }
  }

  /* ---------- task 1 metrics ---------- */
  async function loadMetrics() {
    try {
      const m = await (await fetch("/api/metrics")).json();
      if (!m.accuracy) return;
      ["accuracy", "precision", "recall", "f1"].forEach((k) => {
        if (m[k] !== undefined) $("m-" + k).textContent = (m[k] * 100).toFixed(1) + "%";
      });
      $("metrics").hidden = false;
    } catch { /* optional */ }
  }

  /* ---------- evaluation + failure cases ---------- */
  const MODEL_NAMES = { naive_bayes: "Naive Bayes (ours)", pretrained: "Pretrained model" };
  const SETS = [
    ["test_set", "Held-out SMS messages", "Messages neither model was trained on (same split as Task 1)."],
    ["stress_set", "Hand-written tricky messages", "Phishing, scams and real bank alerts or one-time codes that look suspicious but are fine."],
  ];

  function renderFailures(modelKey, m) {
    const d = el("details", "fails");
    d.appendChild(el("summary", "", "Failure cases: " + MODEL_NAMES[modelKey] + " (" + m.failure_count + ")"));
    if (!m.failures.length) { d.appendChild(el("p", "fail-none", "No mistakes on this set.")); return d; }
    const ul = el("ul", "fail-list");
    m.failures.forEach((f) => {
      const li = document.createElement("li");
      const kind = el("span", "fail-kind " + (f.kind === "missed spam" ? "missed" : "alarm"), f.kind === "missed spam" ? "Missed spam" : "False alarm");
      const text = el("span", "", f.text + (f.category ? "  (" + f.category + ")" : ""));
      li.append(kind, text, el("span", "fail-prob", pct(f.spam_prob)));
      ul.appendChild(li);
    });
    d.appendChild(ul);
    return d;
  }

  function renderEvaluation(ev) {
    const body = $("eval-body");
    body.textContent = "";
    const present = SETS.filter(([k]) => ev[k]);
    if (!present.length) {
      $("eval-lead").textContent = "No evaluation results yet. Run python evaluate.py, then reload this page.";
      return;
    }
    $("eval-lead").textContent = "Missed spam means a spam message was let through. A false alarm means a real message was flagged.";
    present.forEach(([key, title, sub]) => {
      const set = ev[key];
      const wrap = el("div", "eval-set");
      wrap.appendChild(el("h3", "", title));
      wrap.appendChild(el("p", "sub", set.size + " messages, " + set.spam + " spam. " + sub));
      const tw = el("div", "table-wrap");
      const table = el("table", "eval-table");
      const head = document.createElement("tr");
      ["Model", "Accuracy", "Precision", "Recall", "F1", "Missed spam", "False alarms"].forEach((h) => {
        const th = el("th", "", h); th.scope = "col"; head.appendChild(th);
      });
      const thead = document.createElement("thead"); thead.appendChild(head);
      const tbody = document.createElement("tbody");
      Object.entries(set.models).forEach(([mk, m]) => {
        const tr = document.createElement("tr");
        tr.appendChild(el("td", "name", MODEL_NAMES[mk]));
        [m.accuracy, m.precision, m.recall, m.f1].forEach((v) => tr.appendChild(el("td", "num", (v * 100).toFixed(1) + "%")));
        tr.appendChild(el("td", "num", String(m.fn)));
        tr.appendChild(el("td", "num", String(m.fp)));
        tbody.appendChild(tr);
      });
      table.append(thead, tbody);
      tw.appendChild(table);
      wrap.appendChild(tw);
      Object.entries(set.models).forEach(([mk, m]) => wrap.appendChild(renderFailures(mk, m)));
      body.appendChild(wrap);
    });
  }

  async function loadEvaluation() {
    try {
      const res = await fetch("/api/evaluation");
      renderEvaluation(await res.json());
    } catch {
      $("eval-lead").textContent = "Could not load the evaluation results.";
    }
  }

  updateCount();
  clearResults();
  renderHistory();
  pollStatus();
  loadMetrics();
  loadEvaluation();
})();
