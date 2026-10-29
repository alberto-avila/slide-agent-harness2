"""Run Harness2's recursion on the slide agent, then judge chosen vs base harness.

    python -m h2.run --k 1 --mode parallel --domain business --max-tasks 1
"""
import argparse
import json
import os
from pathlib import Path

from harness2.core.schedule import mode_token, run_domain

from .adapter import SlideBenchAdapter
from slide_agent.llm import load_dotenv

from .chat_proposer import ChatProposer


def judge_runs(adapter: SlideBenchAdapter, root: Path) -> list[dict]:
    rows = []
    for sel_path in sorted(root.rglob("selection/*/selection.json")):
        sel = json.loads(sel_path.read_text(encoding="utf-8"))
        if not sel.get("ok") or not sel.get("chosen_run_dir"):
            rows.append({"task_id": sel.get("task_id"), "mode": sel.get("mode"), "error": sel.get("error")})
            continue
        chosen = Path(sel["chosen_run_dir"])
        row = {"task_id": sel["task_id"], "mode": sel["mode"], "k": sel["k"],
               "chosen_label": sel["chosen_label"], "why": sel.get("why", "")[:300],
               "chosen": adapter.score(chosen, sel["task_id"]),
               # Every base rollout, so the baseline is an average rather than one sample.
               "base": [adapter.score(d, sel["task_id"]) for d in sorted(chosen.parent.glob("base*"))
                        if (d / "done.json").is_file()]}
        rows.append(row)
    return rows


def _mean(scores: list[dict], key: str) -> float:
    return sum(s[key] for s in scores) / len(scores) if scores else float("nan")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, default=Path("runs/slides"))
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--mode", choices=("parallel", "sequential"), default="parallel")
    ap.add_argument("--domain", help="Only run this domain (business | technical)")
    ap.add_argument("--max-tasks", type=int, help="Cap tasks per domain")
    ap.add_argument("--model", default=None, help="Executor + judge model (default gemma4:latest)")
    ap.add_argument("--improver-provider", choices=("ollama", "openai"), default=None,
                    help="Where the improver runs (default: IMPROVER_PROVIDER in .env, else ollama)")
    ap.add_argument("--improver-model", default=None,
                    help="Improver model (default: IMPROVER_MODEL in .env; gemma4 for ollama, gpt-6-luna for openai)")
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true", help="List the selected tasks and exit")
    args = ap.parse_args(argv)

    root = args.output.expanduser().resolve()
    adapter = SlideBenchAdapter(root, model=args.model, max_steps=args.max_steps)

    by_domain: dict[str, list[str]] = {}
    for t in adapter.tasks():
        by_domain.setdefault(adapter.domain_of(t), []).append(t)
    if args.domain:
        by_domain = {args.domain: by_domain[args.domain]}
    if args.max_tasks:
        by_domain = {d: ts[: args.max_tasks] for d, ts in by_domain.items()}
    print("Tasks:", json.dumps(by_domain, indent=2))
    if args.dry_run:
        return 0

    load_dotenv()
    provider = args.improver_provider or os.getenv("IMPROVER_PROVIDER") or "ollama"
    improver_model = args.improver_model or (os.getenv("IMPROVER_MODEL") if provider != "ollama" else None)         or (args.model if provider == "ollama" else None)
    prop = ChatProposer(adapter.spec.channels["proposer"], provider=provider, model=improver_model,
                        workdir=root / "proposer")
    print(f"Improver: {prop.model_id}")
    results = {}
    for domain, task_ids in by_domain.items():
        results[domain] = run_domain(
            domain, task_ids, args.k, adapter=adapter, prop=prop,
            runs_root=adapter.spec.runs_root, library_root=root / "library" / f"k{args.k}",
            modes=(mode_token(args.mode),),
        )

    rows = judge_runs(adapter, root)
    report = {"runs": results, "judged": rows, "executions": adapter.execution_count,
              "improver": prop.model_id, "improver_calls": len(prop._calls),
              "improver_tokens": prop.tokens, "improver_usd": round(prop.usd, 4)}
    (root / "report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"\n{'task':32} {'mode':5} {'chosen':7} {'base rules':>10} {'base rubric':>11} "
          f"{'chosen rules':>12} {'chosen rubric':>13}")
    for r in rows:
        if "chosen" not in r:
            print(f"{r['task_id']:32} {r.get('mode') or '':5} ERROR {r.get('error')}")
            continue
        b, c = r["base"], r["chosen"]
        print(f"{r['task_id']:32} {r['mode']:5} {r['chosen_label']:7} "
              f"{_mean(b, 'rules_passed'):>7.1f}/8 {_mean(b, 'rubric_points'):>8.1f}/25 "
              f"{c['rules_passed']:>10}/8 {c['rubric_points']:>10}/25")
    if rows and rows[0].get("chosen"):
        print(f"Judge: {rows[0]['chosen']['judge_model']} (base = mean of {len(rows[0]['base'])} rollouts)")
    print(f"Improver: {prop.model_id}, {prop.tokens['input']:,} input + {prop.tokens['output']:,} output tokens "
          f"this session (${prop.usd:.2f})")
    print(f"\nReport: {root / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
