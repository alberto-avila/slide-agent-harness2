"""Re-judge every finished rollout in a run folder with the current judge (no agent reruns).

    python -m h2.rescore --output runs/slides
    python -m h2.rescore --output RUN_B --out rescore_openai.json --reuse-run RUN_A

`--reuse-run` copies scores from another run's rescore file for rollouts whose deck.json is
byte-identical there (e.g. shared base rollouts), so two runs compare against the exact same
baseline instead of two noisy re-judgings of it.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .adapter import SlideBenchAdapter


def _deck_sha(run_dir: Path) -> str | None:
    p = run_dir / "deck.json"
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def _rollouts(root: Path):
    for done in sorted((root / "executions").rglob("done.json")):
        run_dir = done.parent
        rel = run_dir.relative_to(root / "executions").parts  # (tag, *task_id parts, label)
        yield run_dir, "/".join(rel[1:-1]), rel[-1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, default=Path("runs/slides"))
    ap.add_argument("--out", default="rescore.json", help="File name inside the run folder")
    ap.add_argument("--reuse-run", type=Path, help="Run folder whose scores to reuse for identical decks")
    args = ap.parse_args(argv)
    root = args.output.expanduser().resolve()
    adapter = SlideBenchAdapter(root)

    reuse = {}
    if args.reuse_run:
        ref = args.reuse_run.expanduser().resolve()
        scored = {(r["task_id"], r["label"]): r
                  for r in json.loads((ref / args.out).read_text(encoding="utf-8"))}
        for run_dir, task_id, label in _rollouts(ref):
            sha, row = _deck_sha(run_dir), scored.get((task_id, label))
            if sha and row:
                reuse[sha] = row

    rows = []
    for run_dir, task_id, label in _rollouts(root):
        prev = reuse.get(_deck_sha(run_dir))
        if prev and prev["task_id"] == task_id:
            got = {k: v for k, v in prev.items() if k not in ("task_id", "label")}
            got["reused_from"] = f"{args.reuse_run.name}/{prev['label']}"
        else:
            got = adapter.score(run_dir, task_id)
        rows.append({"task_id": task_id, "label": label, **got})
        print(f"{task_id:35} {label:6} rules {got['rules_passed']}/{got['rules_total']}  "
              f"rubric {got['rubric_points']:>2}/{got['rubric_max']}  {got['ratings']}"
              + ("  (reused)" if "reused_from" in got else ""), flush=True)

    out = root / args.out
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nJudge: {rows[0]['judge_model'] if rows else 'n/a'}\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
