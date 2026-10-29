"""Build a self-contained HTML report of the project and one or more finished Harness2 runs.

    python -m h2.report_html --run "gemma4 (local)=~/harness2_runs/slides_k2b" \\
                             --run "gpt-6-luna (OpenAI)=~/harness2_runs/slides_k2_luna"

Each --run is LABEL=PATH (or just PATH). Runs should share their base rollouts, so the first run's
base decks are the common baseline. Reads rescore_openai.json, selections, summaries and the library
of each run, so the report can be regenerated after any run. Run `python -m h2.rescore` first.
"""
import argparse
import difflib
import html
import json
import re
from datetime import date
from pathlib import Path

CRITERIA = ["story", "assertion_titles", "audience_fit", "accuracy", "notes_quality"]
KIND_ORDER = ["base", "inv", "dom", "agg"]

# First run (k=1, rag-for-execs, 4 rollouts) scored by three judges. From runs/slides/rescore*.json.
JUDGE_COMPARISON = [
    ("base1", 25, 20, 14), ("inv1", 25, 21, 13), ("dom1", 25, 23, 13), ("agg1", 25, 22, 12),
]


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def md_inline(s: str) -> str:
    """Tiny markdown subset used in Harness2's notes: **bold**, `code`, LaTeX arrows."""
    s = s.replace("$\\rightarrow$", "→").replace("\\rightarrow", "→")
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def kind_of(label: str) -> str:
    return re.sub(r"\d", "", label)


def load(run: Path) -> dict:
    rows = json.loads((run / "rescore_openai.json").read_text(encoding="utf-8"))
    report = json.loads((run / "report.json").read_text(encoding="utf-8")) if (run / "report.json").is_file() else {}
    tasks = {}
    for r in rows:
        tasks.setdefault(r["task_id"], {"rollouts": []})["rollouts"].append(r)
    tag_dirs = sorted((run / "runs").glob("slides-oc-*"))
    for t, info in tasks.items():
        slug = t.replace("/", "__")
        for tag in tag_dirs:
            sel = next((tag / slug / "selection").glob("*/selection.json"), None)
            if sel:
                info["selection"] = json.loads(sel.read_text(encoding="utf-8"))
                if not info["selection"].get("why"):  # the selector omitted <why>; use its saved reply
                    reply = next(run.glob(f"proposer/audit/{tag.name}/{slug}/select.*.reply.md"), None)
                    if reply:
                        info["selection"]["why"] = reply.read_text(encoding="utf-8").split("```choice")[0].strip()
                summ = json.loads((tag / slug / "summary.json").read_text(encoding="utf-8"))
                mode = next(iter(summ.get("modes", {}).values()), {})
                info["fell_back"] = mode.get("fell_back", [])
                info["status"] = summ.get("status")
        lib = next(run.glob(f"library/*/*/*/harnesses/{slug}"), None)
        info["experience"] = (lib / "EXPERIENCE.md").read_text(encoding="utf-8") if lib else ""
        exp_reply = next(run.glob(f"proposer/audit/*/{slug}/experience.*.reply.md"), None)
        info["no_entry"] = not lib and bool(exp_reply) and "NO_ENTRY" in exp_reply.read_text(encoding="utf-8")
        # Without a library entry (the improver declined a lesson), the adopted tree is in the task's harnesses/.
        chosen = info.get("selection", {}).get("chosen_label")
        adopted = lib / "harness" if lib else next(run.glob(f"runs/*/{slug}/harnesses/{chosen}"), None) if chosen else None
        info["diff"] = harness_diff(run / "base", adopted) if adopted else []
    # Improver cost: sum the per-call audit records (complete even across resumed sessions).
    usd, tokens_in, tokens_out, calls = 0.0, 0, 0, 0
    for meta in run.glob("proposer/audit/**/*.meta.json"):
        m = json.loads(meta.read_text(encoding="utf-8"))
        calls += 1
        usd += m.get("usd") or 0.0
        if m.get("usage"):
            tokens_in += m["usage"]["input"]
            tokens_out += m["usage"]["output"]
    improver = report.get("improver") or "ollama:gemma4:latest"
    calls = calls or len(list(run.glob("proposer/audit/**/*.reply.md")))
    return {"rows": rows, "tasks": tasks, "improver": improver,
            "cost": {"usd": usd, "input": tokens_in, "output": tokens_out, "calls": calls}}


def harness_diff(base: Path, adopted: Path) -> list[tuple[str, str]]:
    out = []
    files = sorted({p.relative_to(base).as_posix() for p in base.rglob("*.md")}
                   | {p.relative_to(adopted).as_posix() for p in adopted.rglob("*.md")})
    for rel in files:
        if rel.endswith("README.md"):  # empty stubs Harness2 writes into skills/, scripts/, plugin/, sub_agents/
            continue
        a = (base / rel).read_text(encoding="utf-8").splitlines() if (base / rel).is_file() else []
        b = (adopted / rel).read_text(encoding="utf-8").splitlines() if (adopted / rel).is_file() else []
        if a != b:
            out.append((rel, "\n".join(difflib.unified_diff(a, b, "base/" + rel, "adopted/" + rel, lineterm=""))))
    return out


def lesson_block(exp: str) -> str:
    m = re.search(r"## Transferable lesson\s*(.*)", exp, re.S)
    if not m:
        return "<p class='muted'>No transferable lesson recorded.</p>"
    items = [f"<li>{md_inline(line.strip().lstrip('-').strip())}</li>"
             for line in m.group(1).strip().splitlines() if line.strip().lstrip("-").strip()]
    return "<ul class='lesson'>" + "".join(items) + "</ul>"


def diff_block(diffs) -> str:
    if not diffs:
        return "<p class='muted'>The adopted harness is identical to the base harness.</p>"
    parts = []
    for rel, d in diffs:
        lines = []
        for ln in d.splitlines()[2:]:
            cls = "add" if ln.startswith("+") else "del" if ln.startswith("-") else "hunk" if ln.startswith("@@") else ""
            lines.append(f"<span class='{cls}'>{esc(ln)}</span>")
        parts.append(f"<details><summary><code>{esc(rel)}</code></summary><pre class='diff'>{chr(10).join(lines)}</pre></details>")
    return "".join(parts)


def headline_of(info: dict) -> dict:
    sel = info.get("selection", {})
    base = [r["rubric_points"] for r in info["rollouts"] if kind_of(r["label"]) == "base"]
    chosen = next((r for r in info["rollouts"] if r["label"] == sel.get("chosen_label")), None)
    return {
        "base_mean": sum(base) / len(base) if base else float("nan"),
        "chosen": sel.get("chosen_label"), "chosen_pts": chosen["rubric_points"] if chosen else None,
        "finals": {r["label"]: r["rubric_points"] for r in info["rollouts"] if kind_of(r["label"]) == "agg"},
        "why": sel.get("why", ""), "fell_back": info.get("fell_back", []),
    }


def build(runs: list[tuple[str, Path]], author: str = "") -> str:
    loaded = [(label, load(path)) for label, path in runs]
    first = loaded[0][1]
    judge = first["rows"][0].get("judge_model", "?") if first["rows"] else "?"
    tasks = list(first["tasks"])
    base_rows = [r for r in first["rows"] if kind_of(r["label"]) == "base"]
    improved = {label: [r for r in d["rows"] if kind_of(r["label"]) != "base"] for label, d in loaded}
    every_deck = base_rows + [r for rs in improved.values() for r in rs]
    n_decks = len(every_deck)

    def means(rows):
        return {c: sum(r["ratings"][c] for r in rows) / len(rows) for c in CRITERIA} if rows else {}

    overall = means(every_deck)
    weakest = min(overall, key=overall.get)

    # Headline table: one row per (improver, task)
    headline_rows, select_cards, lesson_cards, cost_rows = [], [], [], []
    for label, d in loaded:
        for t in tasks:
            info = d["tasks"].get(t)
            if not info:
                continue
            h = headline_of(info)
            fb = "none" if not h["fell_back"] else esc(", ".join(h["fell_back"]))
            headline_rows.append(
                f"<tr><td>{esc(label)}</td><td><code>{esc(t.split('/')[1])}</code></td>"
                f"<td class='num'>{h['base_mean']:.1f}</td><td><code>{esc(h['chosen'])}</code></td>"
                f"<td class='num'>{h['chosen_pts']}</td><td class='num'>{h['chosen_pts'] - h['base_mean']:+.1f}</td>"
                f"<td>{', '.join(f'<code>{esc(k)}</code> {v}' for k, v in sorted(h['finals'].items()))}</td>"
                f"<td>{fb}</td></tr>")
            select_cards.append(
                f"<div class='card'><h4>{esc(label)} · <code>{esc(t.split('/')[1])}</code></h4>"
                f"<p class='muted'>The selector chose <code>{esc(h['chosen'])}</code> from the composed finals "
                f"({', '.join(f'<code>{esc(k)}</code> = {v}/25' for k, v in sorted(h['finals'].items()))} by the judge).</p>"
                f"<blockquote>{md_inline(h['why'])}</blockquote></div>")
            lesson = ("<p class='muted'><strong>No lesson recorded: the improver declined (<code>NO_ENTRY</code>).</strong> "
                      "Harness² tells it to decline when every edit's evidence is <em>confounded</em> (each candidate changed "
                      "several files, so no single contrast isolates an edit). This task's library stayed empty, so nothing "
                      "carried over to the next task.</p>") if info.get("no_entry") else lesson_block(info["experience"])
            lesson_cards.append(
                f"<div class='card'><h4>{esc(label)} · <code>{esc(t.split('/')[1])}</code></h4>{lesson}"
                f"<h5>What changed in the adopted harness</h5>{diff_block(info['diff'])}</div>")
        c = d["cost"]
        cost_rows.append(
            f"<tr><td>{esc(label)}</td><td><code>{esc(d['improver'])}</code></td><td class='num'>{c['calls']}</td>"
            + (f"<td class='num'>{c['input']:,}</td><td class='num'>{c['output']:,}</td>" if c["input"]
               else "<td class='num'>n/a</td><td class='num'>n/a</td>")
            + 
            f"<td class='num'>{'$%.3f' % c['usd'] if c['input'] else 'local (free)'}</td></tr>")

    all_rows = []
    for r in sorted(base_rows, key=lambda r: (r["task_id"], r["label"])):
        all_rows.append(("Base harness (shared)", r))
    for label, rs in improved.items():
        for r in sorted(rs, key=lambda r: (r["task_id"], KIND_ORDER.index(kind_of(r["label"])), r["label"])):
            all_rows.append((label, r))
    all_rows_html = "".join(
        f"<tr><td>{esc(lbl)}</td><td><code>{esc(r['task_id'].split('/')[1])}</code></td><td><code>{esc(r['label'])}</code></td>"
        f"<td class='num'>{r['rules_passed']}/{r['rules_total']}</td><td class='num'><strong>{r['rubric_points']}</strong>/25</td>"
        + "".join(f"<td class='num'>{r['ratings'][c]}</td>" for c in CRITERIA) + "</tr>"
        for lbl, r in all_rows)

    reasons = "".join(f"<li><code>{esc(r['task_id'].split('/')[1])}</code>: {esc(r['reasons'][weakest])}</li>"
                      for r in base_rows if r["label"] == "base1")
    judge_rows = "".join(f"<tr><td><code>{l}</code></td><td class='num'>{g}</td><td class='num'>{o}</td><td class='num'>{a}</td></tr>"
                         for l, g, o, a in JUDGE_COMPARISON)

    # Chart payload
    points = [{"task": r["task_id"].split("/")[1], "group": "Base harness", "label": r["label"], "kind": "base",
               "rubric": r["rubric_points"], "rules": r["rules_passed"], "ratings": r["ratings"], "chosen": False}
              for r in base_rows]
    for label, d in loaded:
        for t, info in d["tasks"].items():
            chosen = info.get("selection", {}).get("chosen_label")
            for r in info["rollouts"]:
                if kind_of(r["label"]) != "base":
                    points.append({"task": t.split("/")[1], "group": label, "label": r["label"], "kind": kind_of(r["label"]),
                                   "rubric": r["rubric_points"], "rules": r["rules_passed"], "ratings": r["ratings"],
                                   "chosen": r["label"] == chosen})
    series = [{"name": "Base harness", "n": len(base_rows), "values": means(base_rows)}] + \
             [{"name": f"Improved by {label}", "n": len(rs), "values": means(rs)} for label, rs in improved.items()]
    base_means = {t.split("/")[1]: headline_of(first["tasks"][t])["base_mean"] for t in tasks}
    payload = json.dumps({"points": points, "groups": [label for label, _ in loaded], "series": series,
                          "base_means": base_means, "tasks": [t.split("/")[1] for t in tasks]})

    improver_list = ", ".join(f"<code>{esc(d['improver'])}</code> ({esc(label)})" for label, d in loaded)
    findings = Path(__file__).parent / "report_findings.html"
    return TEMPLATE.format(
        today=date.today().isoformat(), byline=f" · {esc(author)}" if author else "", judge=esc(judge), headline_rows="".join(headline_rows),
        all_rows=all_rows_html, selections="".join(select_cards), lessons="".join(lesson_cards),
        cost_rows="".join(cost_rows), judge_rows=judge_rows, payload=payload, weakest=esc(weakest),
        weakest_mean=f"{overall[weakest]:.1f}", reasons=reasons,
        findings=findings.read_text(encoding="utf-8") if findings.is_file() else "",
        n_decks=n_decks, n_runs=len(loaded), improver_list=improver_list,
        min_rules=min(r["rules_passed"] for r in every_deck),
    )


VARS_LIGHT = """--page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --add: #006300; --del: #b42318; --code-bg: #f0efec; --callout-bg: #fdf3e7; --callout-edge: #eb6834;"""
VARS_DARK = """--page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  --add: #0ca30c; --del: #e66767; --code-bg: #262624; --callout-bg: #2a1f17; --callout-edge: #d95926;"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide agent + Harness² — project report</title>
<style>
.viz-root {{ color-scheme: light; """ + VARS_LIGHT.replace("{", "{{").replace("}", "}}") + """ }}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) .viz-root {{ color-scheme: dark; """ + VARS_DARK + """ }}
}}
:root[data-theme="dark"] .viz-root {{ color-scheme: dark; """ + VARS_DARK + """ }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; }}
.viz-root {{ background: var(--page); color: var(--text-primary); min-height: 100vh;
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 980px; margin: 0 auto; padding: 40px 24px 80px; }}
h1 {{ font-size: 30px; line-height: 1.2; margin: 0 0 6px; }}
h2 {{ font-size: 22px; margin: 48px 0 12px; padding-top: 8px; border-top: 1px solid var(--grid); }}
h3 {{ font-size: 17px; margin: 28px 0 8px; }}
h4 {{ margin: 0 0 6px; font-size: 15px; }} h5 {{ margin: 14px 0 6px; font-size: 14px; color: var(--text-secondary); }}
p, li {{ color: var(--text-primary); }} .muted {{ color: var(--text-secondary); }}
.sub {{ color: var(--text-secondary); margin: 0 0 24px; }}
code {{ font: 13px/1.4 ui-monospace, "Cascadia Code", Consolas, monospace; background: var(--code-bg);
  padding: 1px 5px; border-radius: 4px; }}
pre {{ font: 12.5px/1.5 ui-monospace, "Cascadia Code", Consolas, monospace; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; overflow-x: auto; white-space: pre-wrap; }}
pre .add {{ color: var(--add); }} pre .del {{ color: var(--del); }} pre .hunk {{ color: var(--muted); }}
.tldr {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; }}
.tldr li {{ margin: 6px 0; }}
.callout {{ background: var(--callout-bg); border: 1px solid var(--border); border-left: 4px solid var(--callout-edge);
  border-radius: 10px; padding: 14px 18px; margin: 18px 0; }}
.callout h3 {{ margin: 0 0 6px; font-size: 16px; }} .callout p {{ margin: 6px 0; }}
.card {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin: 12px 0; }}
blockquote {{ margin: 8px 0 0; padding: 4px 14px; border-left: 3px solid var(--axis); color: var(--text-secondary); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; }}
th {{ color: var(--text-secondary); font-weight: 600; font-size: 13px; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.scroll {{ overflow-x: auto; }}
details summary {{ cursor: pointer; margin: 6px 0; }}
.lesson li {{ margin: 4px 0; }}
.figure {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 16px 16px 8px; margin: 16px 0; }}
.figure h4 {{ margin-bottom: 2px; }} .figure .cap {{ color: var(--text-secondary); font-size: 13px; margin: 0 0 8px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--text-secondary); margin: 4px 0 8px; }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.legend i {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
svg text {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
.tip {{ position: fixed; pointer-events: none; background: var(--surface-1); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 13px;
  box-shadow: 0 4px 16px rgba(0,0,0,.12); opacity: 0; transition: opacity .1s; max-width: 260px; z-index: 10; }}
.tip strong {{ font-size: 15px; }} .tip .k {{ color: var(--text-secondary); }}
.toggle {{ float: right; font: inherit; font-size: 13px; background: var(--surface-1); color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: 6px; padding: 4px 10px; cursor: pointer; }}
.flow {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: stretch; margin: 12px 0; }}
.flow div {{ flex: 1 1 150px; background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; font-size: 14px; }}
.flow b {{ display: block; margin-bottom: 2px; }}
</style>
</head>
<body>
<div class="viz-root">
<main>
<button class="toggle" id="theme">Toggle dark mode</button>
<h1>A slide-generating agent, improved with Google's Harness²</h1>
<p class="sub">Project report · {today}{byline} · judge of record: <code>{judge}</code></p>

{findings}

<h2>1. What was built</h2>
<h3>The slide agent</h3>
<p>A deliberately simple Python agent (<code>slide_agent/</code>) that turns a topic, an audience and an optional source
document (.txt, .md, .pdf) into a PowerPoint deck. It runs on a local model, <code>gemma4:latest</code> through Ollama,
using a <strong>tool-calling loop</strong>: each turn the model replies with one JSON object, <code>{{"thought", "tool", "args"}}</code>.
The agent runs the tool and returns the result as the next message. This JSON protocol works with models that have no
native tool calling, and switching providers means adding one class to <code>slide_agent/llm.py</code>.</p>
<p>Tools: <code>read_source</code>, <code>plan_outline</code>, <code>add_slide</code>, <code>edit_slide</code>, <code>delete_slide</code>,
<code>view_deck</code>, <code>critique_deck</code> (rule-based checks against the best practices) and <code>save_deck</code> (python-pptx, with speaker notes).
It is intentionally unoptimized: no retries, no context trimming, a rule-based critique. That leaves room for a harness optimizer to find improvements.</p>

<h3>The Harness² integration</h3>
<p><a href="https://github.com/google-research/harness2">Harness²</a> (Google Research, Apache 2.0) improves the <em>harness</em> around a
fixed model (prompts, guardrails, memory, tool guidance, skills) without changing model weights. To connect our agent, the guidance
text moved out of code into editable files in <code>harness_base/</code>, and a custom benchmark was written against Harness²'s
<code>BenchmarkAdapter</code> protocol.</p>
<div class="scroll"><table>
<tr><th>Piece</th><th>File</th><th>Role</th></tr>
<tr><td>Editable harness</td><td><code>harness_base/</code></td><td><code>systemprompt.md</code>, <code>guardrails.md</code>, <code>LongTermMEMORY.md</code>, <code>tool_descriptions/tool_guidance.md</code>, <code>skills/*/SKILL.md</code>. The JSON protocol and tool signatures stay in code so edits can't break parsing.</td></tr>
<tr><td>Benchmark adapter</td><td><code>h2/adapter.py</code></td><td>Tasks, domains, and <code>execute()</code>, which runs the agent with a candidate harness and writes the trajectory in Harness²'s <code>[ACTION]/[OBSERVATION]</code> format.</td></tr>
<tr><td>Tasks</td><td><code>h2/tasks.json</code></td><td>4 decks in 2 domains (business, technical). One task uses a source document (a remote-work survey).</td></tr>
<tr><td>Improver</td><td><code>h2/chat_proposer.py</code></td><td>Replaces upstream's Vertex AI agent session with a chat model, either local Ollama or an OpenAI model. It pastes the evidence folder into the prompt (a 60k-character budget locally, the full folder for API models), applies whole-file <code>&lt;file&gt;</code> edits, caches replies per model under upstream's fingerprint, and records tokens and cost.</td></tr>
<tr><td>Judge</td><td><code>h2/judge.py</code></td><td>8 rule checks plus a 5-criterion rubric with anchored 1–5 ratings, graded by a separate, stronger model. It runs only after selection, so the improver never sees scores.</td></tr>
<tr><td>Runner and tools</td><td><code>h2/run.py</code>, <code>h2/rescore.py</code>, <code>h2/report_html.py</code></td><td>Run the recursion per domain, re-judge finished rollouts (reusing scores for identical decks), and generate this report.</td></tr>
</table></div>

<h2>2. How Harness² works</h2>
<div class="flow">
<div><b>1 · Base</b>Run the agent with the unmodified harness (twice at <code>--k 2</code>).</div>
<div><b>2 · Propose</b>The improver reads the trajectories and decks and edits the harness: <code>inv</code> candidates make general edits, <code>dom</code> candidates make domain-specific edits.</div>
<div><b>3 · Probe</b>Re-run the same task with each candidate harness.</div>
<div><b>4 · Compose</b>Merge what seemed to help into <code>agg</code> finals, run them, and let the selector (the improver model) pick one with a written reason.</div>
<div><b>5 · Remember</b>Store the adopted harness and a cue/lesson/evidence entry in a per-domain library that later tasks read.</div>
</div>
<p>No step uses a ground-truth score. The improver and the selector judge only from the evidence, and the benchmark prompts are
not allowed to mention "score", "rubric" or "grader". A separate judge scores the outcome afterwards, so we can measure whether the harness actually improved.</p>

<h2>3. Experiment setup</h2>
<ul>
<li><strong>Domain:</strong> business, 2 tasks run in order: <code>rag-for-execs</code> (a pitch to non-technical executives) and
<code>remote-work-findings</code> (a deck for HR leadership built from a survey document). The second task starts with the first task's lesson in the library.</li>
<li><strong>Budget:</strong> <code>--k 2 --mode parallel</code>, giving 8 rollouts per task (2 base, 2 inv, 2 dom, 2 agg).</li>
<li><strong>Improvers compared ({n_runs}):</strong> {improver_list}. Every run starts from the <em>same</em> 4 base rollouts, with their judge
scores reused rather than re-judged, so the improvers are compared against an identical baseline. That makes {n_decks} distinct decks in total.</li>
<li><strong>Executor:</strong> <code>gemma4:latest</code> (local) in every run. <strong>Judge:</strong> <code>{judge}</code>.</li>
<li><strong>Scoring:</strong> rules passed out of 8, plus rubric points out of 25 (story, assertion titles, audience fit, accuracy, speaker notes).
Re-judging the same deck varies by about ±1 point, so smaller differences are noise.</li>
</ul>

<h2>4. Results</h2>
<div class="scroll"><table>
<tr><th>Improver</th><th>Task</th><th class="num">Base mean</th><th>Chosen</th><th class="num">Chosen</th><th class="num">Change</th><th>Composed finals</th><th>Stages that fell back</th></tr>
{headline_rows}
</table></div>
<p class="muted">Rubric points out of 25. Every deck passed at least {min_rules} of the 8 formatting rules, so the rubric carries the comparison.</p>

<div class="figure">
<h4>Rubric points for every deck, by improver and candidate type</h4>
<p class="cap">Each dot is one deck (out of 25). The larger labelled dot is the deck Harness² adopted; the vertical line is the shared base-harness mean.</p>
<div id="strip"></div>
</div>

<div class="figure">
<h4>Mean rating per criterion: base decks vs decks from each improver's harnesses</h4>
<p class="cap">1 = poor, 5 = excellent. Improved decks are the inv, dom and agg rollouts. Values are labelled on every bar.</p>
<div class="legend" id="crit-legend"></div>
<div id="crit"></div>
</div>
<p>The weakest criterion overall is <strong>{weakest}</strong> (mean {weakest_mean} out of 5). Judge reasons on the base harness:</p>
<ul>{reasons}</ul>

<details><summary>Table view: all {n_decks} decks</summary>
<div class="scroll"><table>
<tr><th>Harness from</th><th>Task</th><th>Rollout</th><th class="num">Rules</th><th class="num">Rubric</th><th class="num">Story</th><th class="num">Titles</th><th class="num">Audience</th><th class="num">Accuracy</th><th class="num">Notes</th></tr>
{all_rows}
</table></div></details>

<h3>Improver cost</h3>
<div class="scroll"><table>
<tr><th>Run</th><th>Improver</th><th class="num">Calls</th><th class="num">Input tokens</th><th class="num">Output tokens</th><th class="num">Cost</th></tr>
{cost_rows}
</table></div>
<p class="muted">Improver calls only; judge calls are extra. API prices from OpenAI's models page on 2026-10-29.</p>

<h3>Selection decisions</h3>
{selections}

<h3>What Harness² learned and changed</h3>
{lessons}

<h3>The judge decides the conclusion</h3>
<p>On the first run (k=1, <code>rag-for-execs</code>), the same 4 decks were scored by three judges using the same rubric:</p>
<div class="scroll"><table>
<tr><th>Rollout</th><th class="num">gemma4 (self-grading)</th><th class="num">gpt-oss:20b</th><th class="num">GPT-6 Astra</th></tr>
{judge_rows}
</table></div>
<p class="muted">Gemma rated every criterion 5/5. gpt-oss ranked the decks almost in reverse of GPT-6 Astra, so with gpt-oss
Harness² "helped" and with Astra it did not. GPT-6 Astra is the judge of record because its reasons cite specific, verifiable slide-level errors.</p>

<h2>5. Engineering log</h2>
<h3>Decisions</h3>
<ul>
<li><strong>Local executor, API judge, configurable improver.</strong> Gemma writes every deck for free on the local GPU. The judge is an API model from
a different family than the executor. The improver can be local or an API model; with <code>gpt-6-luna</code> it costs fractions of a cent per call.</li>
<li><strong>JSON tool protocol instead of native tool calling,</strong> because Gemma's native support in Ollama is uneven, and the protocol keeps the agent provider-agnostic.</li>
<li><strong>Custom benchmark instead of the built-in ones.</strong> LAB, JobBench and WorkBuddy test coding agents on legal, professional and office work. Our agent needed its own adapter, modelled on the repo's <code>demo.py</code>.</li>
<li><strong>Points instead of pass/fail.</strong> A 4/5 pass mark made every deck score 8/13 once the judge became strict, which hid all differences.</li>
<li><strong>A shared, reused baseline.</strong> The base mean averages all base rollouts, and every improver is compared against the same base decks and scores.</li>
</ul>
<h3>Making Harness² run on Windows</h3>
<p>Harness² targets Linux. The core needed three small patches (in <code>vendor_harness2/</code>):</p>
<ol>
<li><code>core/schedule.py</code>: <code>fcntl</code> (POSIX file locking) falls back to <code>msvcrt</code>.</li>
<li><code>core/tree.py</code>, <code>core/runmark.py</code>, <code>core/proposer.py</code>: relative paths use <code>as_posix()</code>. Windows backslashes had made the improver's edits invisible to the probes.</li>
<li><code>core/context.py</code>: evidence folders are deleted with a handler that clears read-only flags and retries. OneDrive marks synced folders read-only, and Windows refuses to delete a read-only directory, which made every stage silently fall back to the base harness.</li>
</ol>
<h3>Bugs found and fixed in our own code</h3>
<ul>
<li>The selector wrote <code>context/candidates/A.md</code> instead of the bare ID <code>A</code>, and sometimes left out the <code>&lt;why&gt;</code> tags. Replies are now normalized, and the prompt shows the format.</li>
<li>Improver workspaces and audit files were keyed by label only, so labels like <code>inv1.a1</code> collided across tasks. They are now keyed by mode and task.</li>
<li>Without a reply cache, a resumed run would draw new edits while reusing rollouts from the old ones. The proposer now caches under upstream's <code>_call_fingerprint</code>, plus the model name.</li>
<li>Gemma's 60k-character evidence budget silently left 4–12 files out of every composition prompt and 54 files out of a lesson-writing prompt. API improvers now see the full folder.</li>
<li>A blank <code>OPENAI_BASE_URL=</code> in <code>.env</code> became an empty API address. The loader now skips blank values.</li>
<li>Runs now live outside OneDrive (for example <code>~/harness2_runs/</code>). Thousands of scratch files shouldn't sync, and synced folders turn read-only.</li>
</ul>

<h2>6. Reproduce</h2>
<pre>python -m venv .venv
.venv\\Scripts\\pip install -e "./vendor_harness2[render]" ollama pypdf openai
copy .env.example .env      # add OPENAI_API_KEY; JUDGE_MODEL pins the judge
.venv\\Scripts\\python -m h2.run --output ~/harness2_runs/slides_k2b --k 2 --mode parallel --domain business
.venv\\Scripts\\python -m h2.run --output ~/harness2_runs/slides_k2_luna --k 2 --mode parallel --domain business ^
    --improver-provider openai --improver-model gpt-6-luna     # seed with the first run's base rollouts first
.venv\\Scripts\\python -m h2.rescore --output ~/harness2_runs/slides_k2_luna --out rescore_openai.json ^
    --reuse-run ~/harness2_runs/slides_k2b
.venv\\Scripts\\python -m h2.report_html --run "gemma4 (local)=~/harness2_runs/slides_k2b" ^
    --run "gpt-6-luna (OpenAI)=~/harness2_runs/slides_k2_luna"</pre>
</main>
<div class="tip" id="tip" role="tooltip"></div>
</div>

<script>
const DATA = {payload};
const KIND_NAME = {{base: "Base harness", inv: "General edit", dom: "Domain edit", agg: "Composition"}};
const CRIT_NAME = {{story: "Story arc", assertion_titles: "Assertion titles", audience_fit: "Audience fit", accuracy: "Accuracy", notes_quality: "Speaker notes"}};
const SERIES_VAR = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];
const NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tip");

function el(tag, attrs, parent) {{
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {{}})) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}}
function txt(parent, x, y, s, attrs) {{
  const t = el("text", Object.assign({{x, y}}, attrs || {{}}), parent); t.textContent = s; return t;
}}
function showTip(ev, rows) {{
  tip.replaceChildren();
  rows.forEach(([v, k], i) => {{
    const d = document.createElement("div");
    const s = document.createElement(i === 0 ? "strong" : "span"); s.textContent = v; d.appendChild(s);
    if (k) {{ const kk = document.createElement("span"); kk.className = "k"; kk.textContent = "  " + k; d.appendChild(kk); }}
    tip.appendChild(d);
  }});
  const r = ev.target.getBoundingClientRect();
  const x = (ev.clientX || r.left + r.width / 2) + 14, y = (ev.clientY || r.top) + 14;
  tip.style.left = Math.min(x, window.innerWidth - 280) + "px"; tip.style.top = y + "px"; tip.style.opacity = 1;
}}
function hideTip() {{ tip.style.opacity = 0; }}
function bindTip(target, mark, rows) {{
  target.setAttribute("tabindex", "0");
  target.setAttribute("aria-label", rows.map(r => r.join(" ")).join(", "));
  const on = ev => {{ mark.setAttribute("stroke-width", 3); showTip(ev, rows); }};
  const off = () => {{ mark.setAttribute("stroke-width", 2); hideTip(); }};
  target.addEventListener("pointermove", on); target.addEventListener("pointerleave", off);
  target.addEventListener("focus", on); target.addEventListener("blur", off);
}}

function stripChart() {{
  const host = document.getElementById("strip");
  const rowsSpec = [{{group: "Base harness", kind: "base", name: "Base harness (shared)"}}];
  DATA.groups.forEach(g => ["inv", "dom", "agg"].forEach(k => rowsSpec.push({{group: g, kind: k, name: `${{g}} · ${{KIND_NAME[k]}}`}})));
  const W = 900, rowH = 30, top = 30, left = 230, right = 30, bottom = 34;
  const vals = DATA.points.map(p => p.rubric);
  const lo = Math.max(0, Math.min(...vals) - 1), hi = Math.min(25, Math.max(...vals) + 1);
  const X = v => left + (v - lo) / (hi - lo) * (W - left - right);
  DATA.tasks.forEach(task => {{
    const H = top + rowH * rowsSpec.length + bottom;
    const svg = el("svg", {{viewBox: `0 0 ${{W}} ${{H}}`, width: "100%", role: "img",
      "aria-label": `Rubric points per deck for ${{task}}`}}, host);
    txt(svg, 0, 16, task, {{fill: "var(--text-primary)", "font-size": 14, "font-weight": 600}});
    for (let v = Math.ceil(lo); v <= hi; v++) {{
      el("line", {{x1: X(v), x2: X(v), y1: top, y2: top + rowH * rowsSpec.length, stroke: "var(--grid)", "stroke-width": 1}}, svg);
      txt(svg, X(v), H - 12, v, {{fill: "var(--muted)", "font-size": 12, "text-anchor": "middle"}});
    }}
    txt(svg, left - 12, H - 12, "points / 25", {{fill: "var(--muted)", "font-size": 12, "text-anchor": "end"}});
    rowsSpec.forEach((r, i) => {{
      const y = top + rowH * i + rowH / 2;
      if (i === 1 || (i > 1 && rowsSpec[i - 1].group !== r.group))
        el("line", {{x1: 0, x2: W - right, y1: y - rowH / 2, y2: y - rowH / 2, stroke: "var(--axis)", "stroke-width": 1}}, svg);
      txt(svg, 0, y + 4, r.name, {{fill: "var(--text-secondary)", "font-size": 12.5}});
    }});
    const bm = DATA.base_means[task];
    el("line", {{x1: X(bm), x2: X(bm), y1: top - 6, y2: top + rowH * rowsSpec.length, stroke: "var(--text-secondary)", "stroke-width": 1.5}}, svg);
    txt(svg, X(bm) + 6, top - 8, `base mean ${{bm.toFixed(1)}}`, {{fill: "var(--text-secondary)", "font-size": 12}});
    rowsSpec.forEach((r, i) => {{
      const pts = DATA.points.filter(p => p.task === task && p.group === r.group && p.kind === r.kind)
        .sort((a, b) => a.label.localeCompare(b.label));
      pts.forEach(p => {{
        const same = pts.filter(q => q.rubric === p.rubric);
        const off = same.length > 1 ? (same.indexOf(p) - (same.length - 1) / 2) * 10 : 0;
        const cx = X(p.rubric), cy = top + rowH * i + rowH / 2 + off;
        const g = el("g", {{}}, svg);
        el("circle", {{cx, cy, r: 12, fill: "transparent"}}, g);
        const dot = el("circle", {{cx, cy, r: p.chosen ? 7 : 5, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 2}}, g);
        if (p.chosen) txt(svg, cx + 11, cy + 4, `adopted (${{p.label}})`, {{fill: "var(--text-primary)", "font-size": 12, "font-weight": 600}});
        bindTip(g, dot, [[`${{p.rubric}} / 25`, `${{p.group}} · ${{p.label}}${{p.chosen ? " · adopted" : ""}}`], [`rules ${{p.rules}}/8`, ""]]
          .concat(Object.entries(p.ratings).map(([c, v]) => [String(v), CRIT_NAME[c]])));
      }});
    }});
  }});
}}

function critChart() {{
  const host = document.getElementById("crit"), legend = document.getElementById("crit-legend");
  DATA.series.forEach((s, i) => {{
    const span = document.createElement("span"); const sw = document.createElement("i");
    sw.style.background = SERIES_VAR[i]; span.appendChild(sw);
    span.appendChild(document.createTextNode(`${{s.name}} (${{s.n}} decks)`)); legend.appendChild(span);
  }});
  const crits = Object.keys(CRIT_NAME);
  const nS = DATA.series.length, barH = 14, gap = 2, groupGap = 16, left = 150, right = 60, top = 4;
  const groupH = nS * barH + (nS - 1) * gap;
  const W = 900, H = top + crits.length * (groupH + groupGap) + 22;
  const X = v => left + v / 5 * (W - left - right);
  const svg = el("svg", {{viewBox: `0 0 ${{W}} ${{H}}`, width: "100%", role: "img", "aria-label": "Mean rating per criterion by harness source"}}, host);
  for (let v = 0; v <= 5; v++) {{
    el("line", {{x1: X(v), x2: X(v), y1: top, y2: H - 22, stroke: v === 0 ? "var(--axis)" : "var(--grid)", "stroke-width": 1}}, svg);
    txt(svg, X(v), H - 6, v, {{fill: "var(--muted)", "font-size": 12, "text-anchor": "middle"}});
  }}
  crits.forEach((c, ci) => {{
    const y0 = top + ci * (groupH + groupGap);
    txt(svg, 0, y0 + groupH / 2 + 4, CRIT_NAME[c], {{fill: "var(--text-secondary)", "font-size": 13}});
    DATA.series.forEach((s, si) => {{
      const v = s.values[c], y = y0 + si * (barH + gap), w = Math.max(X(v) - X(0), 5);
      const g = el("g", {{}}, svg);
      el("rect", {{x: X(0), y: y - 1, width: w + 50, height: barH + 2, fill: "transparent"}}, g);
      const bar = el("path", {{d: `M${{X(0)}},${{y}} h${{w - 4}} a4,4 0 0 1 4,4 v${{barH - 8}} a4,4 0 0 1 -4,4 h${{-(w - 4)}} z`,
        fill: SERIES_VAR[si], stroke: "var(--surface-1)", "stroke-width": 2}}, g);
      txt(svg, X(0) + w + 6, y + barH / 2 + 4, v.toFixed(2), {{fill: "var(--text-primary)", "font-size": 12}});
      bindTip(g, bar, [[v.toFixed(2) + " / 5", `${{CRIT_NAME[c]}} · ${{s.name}}`]]);
    }});
  }});
}}

stripChart(); critChart();
document.getElementById("theme").addEventListener("click", () => {{
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
}});
</script>
</body>
</html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", required=True,
                    help="LABEL=PATH (or PATH) of a finished run with rescore_openai.json; repeat to compare runs")
    ap.add_argument("--out", type=Path, default=Path("reports/harness2_report.html"))
    ap.add_argument("--author", default="", help="Name for the report byline (omitted by default)")
    args = ap.parse_args(argv)
    runs = []
    for spec in args.run:
        label, sep, path = spec.partition("=")
        if not sep:
            label, path = Path(spec).name, spec
        runs.append((label.strip(), Path(path.strip()).expanduser().resolve()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(runs, args.author), encoding="utf-8")
    print(f"Wrote {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
