# Slide Agent + Harness²

A simple, local AI agent that builds PowerPoint decks following slide-design best practices, connected to
Google Research's [Harness²](https://github.com/google-research/harness2) to test whether the harness around a small model
(its prompts, guardrails, memory, tool guidance and skills) can be improved automatically.

📄 **Full write-up:** [`reports/harness2_report.html`](reports/harness2_report.html). Download it and open it in a browser for
the charts, the selection reasoning, the lessons, and the harness diffs.

## Project status

| Stage | Status |
|---|---|
| Slide agent: tool-calling loop on a local model, `.pptx` output with speaker notes | ✅ Done |
| Harness² connected through a custom benchmark adapter, running natively on Windows | ✅ Done (3 small patches to the vendored copy) |
| Independent judge: 8 rule checks plus a 5-criterion rubric graded by `gpt-6-astra` | ✅ Done |
| Experiment 1: local `gemma4` as the improver (2 business tasks, `--k 2`) | ✅ Done: no measurable gain |
| Experiment 2: `gpt-6-luna` as the improver (same tasks, same baseline decks) | ✅ Done: modest gain (+0.5 and +2.0 points) |
| Improvers from other model families (Claude, Gemini, `gpt-oss:20b`, `qwen3`) | ⏳ Next: addresses the same-provider conflict below |
| Technical-domain tasks, more samples, a fidelity-checking tool for the agent | ⏳ Planned |

### Results so far
Rubric points out of 25 (graded by `gpt-6-astra`). The baseline is the mean of 2 decks built with the unmodified harness, shared by both experiments.

| Task | Baseline | Harness chosen with `gemma4` as improver | Harness chosen with `gpt-6-luna` as improver |
|---|---|---|---|
| `rag-for-execs` (pitch to executives) | 13.5 | 14 (+0.5) | 14 (+0.5) |
| `remote-work-findings` (deck from a survey document) | 12.0 | 12 (0) | **14 (+2.0)** |

- **The improver decides what gets optimized.** Gemma pushed the harness toward persuasive "mandates" that the judge penalized as inaccurate.
  Luna made the requested slide count binding and added a source-fidelity skill ("do not turn a survey finding into a causal claim").
- **Luna was more careful about evidence.** It marked every edit "confounded" and, as Harness² instructs in that case, declined to record a lesson.
  Gemma wrote "high confidence" lessons from the same kind of evidence.
- **The gains are small.** Re-judging the same deck varies by about ±1 point, and there is one deck per harness, so +2 is suggestive, not conclusive.
- **Cost:** Luna's improver calls cost about $0.05 for the whole run. The slide-writing model (`gemma4`) runs locally for free.

> ⚠ **Known limitation: improver and judge from the same provider.** In experiment 2, `gpt-6-luna` (improver) and `gpt-6-astra` (judge)
> are both OpenAI models and may share preferences, which could inflate the measured gain. The improver never sees scores or the rubric,
> which limits this but does not remove it. Next we will test improvers from other model families and cross-check with a judge from a different family.

## How it works

```
topic + audience (+ source doc) ──► slide agent (gemma4, local) ──► deck.pptx
                                         ▲
                     harness files  ─────┘   (system prompt, guardrails, memory, tool guidance, skills)
                         ▲
Harness²:  base runs → improver proposes edits → re-run with each edit → compose → select → library
                                                                                       │
                                            judge (gpt-6-astra) scores decks afterwards ┘
```

- **Slide agent (`slide_agent/`):** each turn the model replies with one JSON object, `{"thought", "tool", "args"}`, and the agent runs the tool.
  The tools are `read_source`, `plan_outline`, `add_slide`, `edit_slide`, `delete_slide`, `view_deck`, `critique_deck` and `save_deck`.
  The agent is deliberately unoptimized, which leaves Harness² room to improve it.
- **Editable harness (`harness_base/`):** the guidance text the agent loads. Harness² edits copies of these files. The JSON protocol and tool signatures stay in code.
- **Harness² integration (`h2/`):** a `BenchmarkAdapter` for the deck tasks, a chat-based improver (local Ollama or an OpenAI model),
  the judge, and tools to run, re-score, scrub and report.

## Repository layout

| Path | What it is |
|---|---|
| `slide_agent/` | The agent: `agent.py` (loop), `tools.py`, `llm.py` (Ollama and OpenAI providers), `sources.py` (.txt/.md/.pdf input) |
| `harness_base/` | The base harness files Harness² starts from |
| `main.py` | Command-line entry point for making a single deck |
| `h2/adapter.py` | Harness² benchmark adapter: tasks, domains, `execute()`, trajectories |
| `h2/tasks.json`, `h2/sources/` | 4 deck tasks in 2 domains; one uses a (fictional) survey document |
| `h2/chat_proposer.py` | The improver: replaces upstream's Vertex AI agent session with a chat model; caches replies and records cost |
| `h2/judge.py` | Rule checks plus a rubric graded by a separate model; runs only after selection |
| `h2/run.py`, `h2/rescore.py` | Run the Harness² recursion; re-judge finished decks (`--reuse-run` shares a baseline between runs) |
| `h2/report_html.py`, `h2/report_findings.html` | Generate the HTML report from one or more runs |
| `h2/scrub_paths.py` | Replace local absolute paths in run data with placeholders before sharing |
| `results/slides_k2b/`, `results/slides_k2_luna/` | Data from the two experiments: decks, trajectories, improver prompts and replies, scores (paths scrubbed) |
| `reports/harness2_report.html` | The generated report |
| `vendor_harness2/` | Vendored Harness² (Apache 2.0) with Windows patches; see [`LOCAL_MODIFICATIONS.md`](vendor_harness2/LOCAL_MODIFICATIONS.md) |

## Quick start

Requirements: Python 3.12 or 3.13, [Ollama](https://ollama.com) with `gemma4:latest` pulled, and an OpenAI API key for the judge
(and optionally the improver). Developed on Windows 11.

```bash
python -m venv .venv
.venv/Scripts/pip install -e "./vendor_harness2[render]" -r requirements.txt
cp .env.example .env        # then put your OPENAI_API_KEY in .env (never commit it)

# One deck
.venv/Scripts/python main.py --topic "Intro to RAG" --audience "executives" --slides 8 --out rag.pptx
.venv/Scripts/python main.py --topic "Summarize this report" --source report.pdf --trace output/trace.json
```

Decks go to `output/`. Set `SLIDE_AGENT_MODEL` or pass `--model` to change the local model.

## Running Harness²

```bash
.venv/Scripts/python -m h2.run --dry-run
.venv/Scripts/python -m h2.run --output ~/harness2_runs/slides_k2b --k 2 --mode parallel --domain business
.venv/Scripts/python -m h2.rescore --output ~/harness2_runs/slides_k2b --out rescore_openai.json
.venv/Scripts/python -m h2.report_html --run "gemma4 (local)=~/harness2_runs/slides_k2b"
```

- **Keep `--output` outside OneDrive** (or any synced folder). Synced folders get marked read-only, which breaks Harness²'s delete-and-rebuild steps on Windows.
- Rerunning the same `h2.run` command resumes an interrupted run. Improver replies are cached per model, so resumes stay consistent.
- `--k 2 --mode parallel` runs 8 decks per task (2 base, 2 general edits, 2 domain edits, 2 compositions). Each deck takes a few minutes on a local GPU.

### Comparing improvers
Use the same slide-writing model and the same base decks, and change only the improver. Copy the first run's `executions/.../base*` folders into a new run folder, then:

```bash
.venv/Scripts/python -m h2.run --output ~/harness2_runs/slides_k2_luna --k 2 --mode parallel --domain business \
    --improver-provider openai --improver-model gpt-6-luna
.venv/Scripts/python -m h2.rescore --output ~/harness2_runs/slides_k2_luna --out rescore_openai.json --reuse-run ~/harness2_runs/slides_k2b
.venv/Scripts/python -m h2.report_html --run "gemma4 (local)=~/harness2_runs/slides_k2b" --run "gpt-6-luna (OpenAI)=~/harness2_runs/slides_k2_luna"
```

`--reuse-run` copies the judge's scores for byte-identical decks, so both runs share one baseline instead of two noisy re-judgings.

### Configuration (`.env`)
| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Needed for the judge and for an OpenAI improver |
| `OPENAI_BASE_URL` | Optional: any OpenAI-compatible endpoint |
| `JUDGE_PROVIDER`, `JUDGE_MODEL` | The judge (default `openai` / `gpt-6-astra`). Pin one judge for every comparison |
| `IMPROVER_PROVIDER`, `IMPROVER_MODEL` | The improver (default local `ollama` / `gemma4`) |

## Privacy and secrets
- `.env` holds your API key and is git-ignored. Only `.env.example`, with empty values, is committed.
- Run folders embed absolute local paths, which reveal your username and folder layout. Before committing new run data, run
  `python -m h2.scrub_paths results reports` to replace them with `<project>` / `<home>`.
- Local run folders (`runs/`), decks from `main.py` (`output/`), and the virtual environment are git-ignored.

## Credits and licensing
- This project's code (everything outside `vendor_harness2/`) is released under the [MIT License](LICENSE).
- Harness² is © Google LLC, licensed under Apache 2.0 (see [`vendor_harness2/LICENSE`](vendor_harness2/LICENSE)). It is not an officially supported Google product.
  The local changes are documented in [`vendor_harness2/LOCAL_MODIFICATIONS.md`](vendor_harness2/LOCAL_MODIFICATIONS.md), with the exact patch in `LOCAL_PATCHES.diff`.
- Citation: Xu et al., "Harness²: Recursive Agent Harnessing for an Open World," arXiv:2610.14224 (2026).
