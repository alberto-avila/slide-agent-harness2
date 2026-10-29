"""Harness2 BenchmarkAdapter for the slide agent (modelled on harness2/demo.py)."""
import json
import shutil
import traceback
from pathlib import Path

from harness2.core import tree
from harness2.core.spec import BenchPrompts, BenchSpec, ChannelSpec
from harness2.substrate.opencode import OpencodeSubstrate

from slide_agent.agent import DEFAULT_HARNESS, SlideAgent
from slide_agent.llm import get_llm
from slide_agent.sources import load_source

from . import judge

H2_DIR = Path(__file__).resolve().parent

PROMPTS = BenchPrompts(
    work=(
        "Building presentation slide decks for a stated topic and audience with a small local "
        "model that acts by emitting one JSON tool call per turn. A good deck has one idea per "
        "slide, assertion-style titles, concise parallel bullets, details in speaker notes, a "
        "clear story arc and a closing takeaway."
    ),
    deliverable_word="slide deck",
    inv_levers=(
        "- systemprompt.md: the workflow order and how to plan before adding slides\n"
        "- guardrails.md: concrete slide-writing rules (bullet length, title style, structure)\n"
        "- tool_descriptions/tool_guidance.md: how to use each tool, including fixing issues "
        "after critique_deck\n"
        "- skills/<name>/SKILL.md: reusable procedures, e.g. story-arc planning\n"
        "- scripts/ and plugin/ are NOT executed by this agent; do not edit them"
    ),
    dom_levers=(
        "- audience-specific vocabulary and depth guidance for this kind of deck\n"
        "- typical section structures for decks in this area\n"
        "- LongTermMEMORY.md: durable lessons about this kind of deck"
    ),
    yardstick=(
        "The agent plans an outline that fits the requested slide count, writes each slide once "
        "with short bullets and speaker notes, checks the deck, fixes what the check reports, "
        "then saves and finishes without wasted or malformed turns."
    ),
)


class SlideBenchAdapter:
    def __init__(self, root: Path, model: str = None, max_steps: int = 30):
        self.root = Path(root)
        self.model = model
        self.max_steps = max_steps
        self.substrate = OpencodeSubstrate()
        # Channel values are bookkeeping only: ChatProposer ignores the Vertex plumbing.
        channel = ChannelSpec("opencode", "ollama/" + (model or "gemma4:latest"))
        self.spec = BenchSpec(
            name="slides",
            runs_root=self.root / "runs",
            install_mode="workspace_config",
            prompts=PROMPTS,
            channels={"proposer": channel, "selector": channel},
        )
        self._tasks = {t["id"]: t for t in json.loads((H2_DIR / "tasks.json").read_text(encoding="utf-8"))}
        self.execution_count = 0

        # Copy the base harness into the run root so it is a stable c1..c8 tree.
        base = {rel: "" for rel in self.substrate.surface().always_on}
        base.update(tree.read_tree(self.substrate.surface(), DEFAULT_HARNESS))
        tree.write_tree(self.substrate.surface(), base, self.base_harness(), stubs=False)

    # --- task catalogue -------------------------------------------------------------
    def tasks(self, split: str = "all") -> list[str]:
        return sorted(self._tasks)

    def domain_of(self, task_id: str) -> str:
        return self._tasks[task_id]["domain"]

    def task_prompt(self, task_id: str) -> str:
        t = self._tasks[task_id]
        s = f"Create a ~{t['slides']}-slide presentation.\nTopic: {t['topic']}\nAudience: {t['audience']}"
        if t.get("source"):
            s += f"\nSource document: {Path(t['source']).name} (use it as the factual basis)"
        return s

    def task_files(self, task_id: str) -> Path | None:
        src = self._tasks[task_id].get("source")
        if not src:
            return None
        d = self.root / "sources" / task_id
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(H2_DIR / src, d / Path(src).name)
        return d

    def base_harness(self) -> Path:
        return self.root / "base"

    def validate_tree(self, harness: tree.Tree) -> None:
        problems = []
        if not harness.get("systemprompt.md", "").strip():
            problems.append("systemprompt.md must not be empty.")
        size = sum(len(v) for v in harness.values())
        if size > 20_000:
            problems.append(f"The harness is {size} chars; keep it under 20000 so a small model can follow it.")
        if problems:
            raise ValueError(" ".join(problems))

    # --- execution ------------------------------------------------------------------
    def execute(self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None) -> Path:
        run_dir = self.root / "executions" / run_id
        if (run_dir / "done.json").is_file():  # idempotent by run_id
            return run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        self.execution_count += 1

        t = self._tasks[task_id]
        source_text = load_source(str(H2_DIR / t["source"])) if t.get("source") else ""
        agent = SlideAgent(get_llm("ollama", model=self.model), max_steps=self.max_steps,
                           verbose=False, harness_dir=harness_dir or self.base_harness())
        error = ""
        state = None
        try:
            state = agent.run(t["topic"], t["audience"], source_text, t["slides"],
                              filename="deck.pptx", output_dir=str(run_dir))
        except Exception:
            error = traceback.format_exc()
        (run_dir / "trajectory.md").write_text(agent.trajectory_text(), encoding="utf-8")
        (run_dir / "trace.json").write_text(json.dumps(agent.trace, indent=2, default=str), encoding="utf-8")
        if state is not None:
            (run_dir / "deck.json").write_text(json.dumps(state.slides, indent=2), encoding="utf-8")
        (run_dir / "done.json").write_text(json.dumps({"steps": len(agent.trace), "error": error}), encoding="utf-8")
        return run_dir

    def delivered(self, run_dir: Path) -> bool:
        return (Path(run_dir) / "deck.pptx").is_file()

    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        p = Path(run_dir) / "trajectory.md"
        return p.read_text(encoding="utf-8")[:obs_trunc] if p.is_file() else ""

    def deliverable_text(self, run_dir: Path) -> str:
        p = Path(run_dir) / "deck.json"
        if not p.is_file():
            return ""
        return judge.render_deck(json.loads(p.read_text(encoding="utf-8")))

    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        text = self.deliverable_text(run_dir)
        return {"deck.pptx": text} if text else {}

    # --- grading (called only after selection) --------------------------------------
    def score(self, run_dir: Path, task_id: str) -> dict | None:
        p = Path(run_dir) / "deck.json"
        slides = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []
        t = self._tasks[task_id]
        source_text = load_source(str(H2_DIR / t["source"])) if t.get("source") else ""
        return judge.score_deck(slides, t, source_text)
