"""A Harness2 Proposer backed by a plain chat model (local Ollama or an OpenAI-compatible API)
instead of upstream's agentic Vertex session.

Upstream, the improver is an agent (Claude Code / OpenCode) that browses `context/` and edits
`context/harness/` in place. A chat model can't browse, so we inline the context files into
the prompt and, for propose calls, ask for whole replacement files in <file> blocks.
"""
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path

from harness2.core.proposer import Proposer, ProposerError, Reply, _call_fingerprint
from harness2.core.tree import normalize_rel

from slide_agent.llm import get_llm

TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".ts", ".toml", ".yaml", ".yml", ""}

# How much evidence fits in the prompt, in characters. A 32k-token local model has to cut files;
# API models with 1M-token windows see the whole evidence folder (largest seen so far: ~91k chars).
CONTEXT_BUDGET = {
    "ollama": {"per_file": 8_000, "total": 60_000},
    "openai": {"per_file": 50_000, "total": 600_000},
}

# USD per 1M tokens (input, output), from developers.openai.com/api/docs/models on 2026-10-29.
PRICES = {
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-sol": (2.00, 10.00),
    "gpt-6-astra": (10.00, 50.00),
}

EDIT_FORMAT = """
# HOW TO REPLY (you cannot edit files directly)
Return every harness file you change as a complete replacement, one block per file:
<file path="guardrails.md">
...full new file content...
</file>
Paths are relative to context/harness/ (for example systemprompt.md, guardrails.md,
tool_descriptions/tool_guidance.md, LongTermMEMORY.md, skills/<name>/SKILL.md).
Files you omit are left unchanged. End with <notes>one paragraph explaining the change</notes>.
"""

_FILE = re.compile(r'<file path="([^"]+)">\n?(.*?)</file>', re.S)

CHOICE_REMINDER = """
The choice block must contain ONLY the bare candidate id, for example:
```choice
A
```
"""

_CHOICE_BLOCK = re.compile(r"```choice\s*(.*?)\s*```", re.S)


def normalize_choice(text: str) -> str:
    """Small models often write `context/candidates/A.md`; Harness2 expects the bare id `A`.
    They also drop the <why> tags, which leaves Harness2's recorded reason empty."""
    def fix(m):
        lines = m.group(1).strip().splitlines()
        raw = lines[0].strip().strip("`") if lines else ""
        return f"```choice\n{Path(raw).stem if ('/' in raw or '.' in raw) else raw}\n```"
    text = _CHOICE_BLOCK.sub(fix, text)
    m = _CHOICE_BLOCK.search(text)
    if m and "<why>" not in text and text[: m.start()].strip():
        text = f"<why>\n{text[: m.start()].strip()}\n</why>\n\n{text[m.start():]}"
    return text


def dump_context(context_dir: Path, per_file: int, total: int) -> str:
    """Inline the context folder: task and harness first, then everything else."""
    files = [p for p in sorted(context_dir.rglob("*")) if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES]

    def priority(p: Path) -> int:
        rel = p.relative_to(context_dir).as_posix()
        return 0 if rel.startswith("task") else 1 if rel.startswith("harness/") else 2

    out, used = [], 0
    for p in sorted(files, key=priority):
        rel = p.relative_to(context_dir).as_posix()
        body = p.read_text(encoding="utf-8", errors="replace")
        if len(body) > per_file:
            body = body[:per_file] + f"\n...[truncated, {len(body)} chars total]"
        block = f'=== context/{rel} ===\n{body}\n'
        if used + len(block) > total:
            out.append(f"=== context/{rel} === [omitted: context budget reached]\n")
            continue
        out.append(block)
        used += len(block)
    return "\n".join(out)


class ChatProposer(Proposer):
    def __init__(self, spec, provider: str = "ollama", model: str = None, workdir: Path = None, attempts: int = 2):
        super().__init__(spec=spec, attempts=attempts)
        self.provider = provider
        if provider == "ollama":
            self.llm = get_llm("ollama", model=model, temperature=0.3, json_mode=False, num_ctx=32768)
        else:
            self.llm = get_llm(provider, model=model or os.getenv("IMPROVER_MODEL") or "gpt-6-luna", json_mode=False)
        self.budget = CONTEXT_BUDGET.get(provider, CONTEXT_BUDGET["openai"])
        self.workdir = Path(workdir or "runs/proposer")
        self.tokens = {"input": 0, "output": 0}
        self.usd = 0.0

    @property
    def model_id(self) -> str:
        return f"{self.provider}:{self.llm.model}"

    def _cost(self, usage: dict | None) -> float:
        price = PRICES.get(self.llm.model)
        if not usage or not price:
            return 0.0
        return (usage["input"] * price[0] + usage["output"] * price[1]) / 1_000_000

    def call(self, mission, context_dir, label, *, system="", timeout=None, max_attempts=None, harvest=None) -> Reply:
        context_dir = Path(context_dir) if context_dir else None
        run_key = self._run_key(context_dir)
        # Same content-addressed key upstream uses, so a resumed run replays identical edits
        # instead of drawing new ones that no longer match the cached rollouts. The model is part
        # of the key, so a cached reply from one improver is never replayed for another.
        key = hashlib.sha256(f"{_call_fingerprint(label, mission, system, context_dir)}|{self.model_id}".encode()).hexdigest()
        cache_file = self.workdir / "cache" / f"{key}.json"
        if cache_file.is_file():
            text = json.loads(cache_file.read_text(encoding="utf-8"))["text"]
            return self._finish(label, text, context_dir, run_key, harvest, attempts=0, wall=0.0, cached=True)

        prompt = mission
        if context_dir and context_dir.is_dir():
            prompt += "\n\n# CONTEXT FILES\n\n" + dump_context(context_dir, **self.budget)
        if harvest:
            prompt += EDIT_FORMAT
        elif label.startswith("select."):
            prompt += CHOICE_REMINDER
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]

        tries = max(1, int(max_attempts or self.attempts))
        t0, last = time.time(), ""
        for attempt in range(1, tries + 1):
            try:
                text = self.llm.chat(messages)
            except Exception as exc:
                last = f"{type(exc).__name__}: {exc}"
                continue
            if not text or not text.strip():
                last = "empty reply"
                continue
            text = normalize_choice(text)
            usage = self.llm.last_usage
            usd = self._cost(usage)
            if usage:
                self.tokens["input"] += usage["input"]
                self.tokens["output"] += usage["output"]
                self.usd += usd
            self._save_audit(run_key, label, prompt, text, usage, usd)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps({"label": label, "model": self.model_id, "usage": usage, "text": text}),
                                  encoding="utf-8")
            return self._finish(label, text, context_dir, run_key, harvest, attempts=attempt,
                                wall=round(time.time() - t0, 1), cached=False, usd=usd)
        raise ProposerError(f"{label}: no usable reply from {self.model_id} ({last})", attempts=tries)

    def _finish(self, label, text, context_dir, run_key, harvest, *, attempts, wall, cached, usd=0.0) -> Reply:
        reply = Reply(label=label, text=text, ok=True, cost_usd=usd, wall_s=wall, attempts=attempts,
                      cached=cached, channel=self.model_id)
        if harvest:
            reply.workspace = self._apply_edits(context_dir, run_key, label, text)
        self._calls.append(reply)
        return reply

    @staticmethod
    def _run_key(context_dir: Path | None) -> str:
        """`<mode tag>/<task>`: every context dir sits at runs/<tag>/<task>/{context,selection}/<x>."""
        if not context_dir:
            return "misc"
        work_dir = context_dir.parent.parent
        return f"{work_dir.parent.name}/{work_dir.name}"

    def _apply_edits(self, context_dir: Path, run_key: str, label: str, text: str) -> Path:
        """Copy context/harness to a per-task workspace and overwrite the files the model returned."""
        ws = self.workdir / "workspaces" / run_key / label
        shutil.rmtree(ws, ignore_errors=True)
        shutil.copytree(context_dir / "harness", ws, dirs_exist_ok=True)  # OneDrive can block rmtree
        for rel, body in _FILE.findall(text):
            rel = normalize_rel(rel.removeprefix("context/").removeprefix("harness/"))
            dest = ws / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body.strip() + "\n", encoding="utf-8")
        return ws

    def _save_audit(self, run_key: str, label: str, prompt: str, text: str, usage=None, usd=0.0) -> None:
        d = self.workdir / "audit" / run_key
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{label}.prompt.md").write_text(prompt, encoding="utf-8")
        (d / f"{label}.reply.md").write_text(text, encoding="utf-8")
        (d / f"{label}.meta.json").write_text(
            json.dumps({"model": self.model_id, "usage": usage, "usd": round(usd, 6)}), encoding="utf-8")


# Old name, kept so existing imports keep working.
OllamaProposer = ChatProposer
