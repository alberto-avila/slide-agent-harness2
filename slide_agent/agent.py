"""Simple ReAct-style tool loop using a JSON protocol (works with models without native tool calling).

The guidance text (system prompt, guardrails, memory, tool guidance, skills) is loaded from a
harness directory so Harness2 can edit it. The JSON protocol and tool list stay in code.
"""
import json
from pathlib import Path

from .llm import LLM
from .tools import TOOL_DOCS, TOOLS, DeckState

DEFAULT_HARNESS = Path(__file__).resolve().parent.parent / "harness_base"

HARNESS_FILES = ("systemprompt.md", "guardrails.md", "LongTermMEMORY.md",
                 "tool_descriptions/tool_guidance.md")

PROTOCOL = """Respond with ONLY one JSON object per turn, in this format:
{"thought": "short reasoning", "tool": "<tool name>", "args": {...}}
"""


def build_system_prompt(harness_dir: Path) -> str:
    parts = []
    for rel in HARNESS_FILES:
        p = harness_dir / rel
        if p.is_file() and p.read_text(encoding="utf-8").strip():
            parts.append(p.read_text(encoding="utf-8").strip())
    for skill in sorted(harness_dir.glob("skills/*/SKILL.md")):
        parts.append(f"Skill `{skill.parent.name}`:\n" + skill.read_text(encoding="utf-8").strip())
    parts.append("Available tools:\n" + TOOL_DOCS)
    parts.append(PROTOCOL)
    return "\n\n".join(parts)


class SlideAgent:
    def __init__(self, llm: LLM, max_steps: int = 40, verbose: bool = True, harness_dir=None):
        self.llm = llm
        self.max_steps = max_steps
        self.verbose = verbose
        self.harness_dir = Path(harness_dir) if harness_dir else DEFAULT_HARNESS
        self.trace: list[dict] = []  # step log, for evaluation harnesses

    def run(self, topic: str, audience: str = "general audience", source_text: str = "",
            num_slides: int = 10, filename: str = "deck.pptx", output_dir: str = "output") -> DeckState:
        state = DeckState(source_text=source_text)
        task = (f"Create a presentation.\nTopic: {topic}\nAudience: {audience}\n"
                f"Target slide count: about {num_slides}\nOutput filename: {filename}\n"
                f"Source document provided: {'yes, ' + str(len(source_text)) + ' chars' if source_text else 'no'}")
        messages = [{"role": "system", "content": build_system_prompt(self.harness_dir)},
                    {"role": "user", "content": task}]

        for step in range(1, self.max_steps + 1):
            raw = self.llm.chat(messages)
            messages.append({"role": "assistant", "content": raw})

            try:
                call = json.loads(raw)
                tool, args = call["tool"], call.get("args", {}) or {}
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                obs = f"Error: invalid response ({e}). Reply with one JSON object: {{\"thought\", \"tool\", \"args\"}}."
                tool, args = None, {}
            else:
                if tool == "finish":
                    if state.saved_path is None:
                        obs = "Error: you must call save_deck before finish."
                    else:
                        self._log(step, {"tool": tool, "args": args, "raw": raw}, "finished")
                        break
                elif tool not in TOOLS:
                    obs = f"Error: unknown tool '{tool}'."
                else:
                    if tool == "save_deck":
                        args = {**args, "output_dir": output_dir}
                    try:
                        obs = TOOLS[tool](state, **args)
                    except Exception as e:
                        obs = f"Error running {tool}: {e}"

            self._log(step, {"tool": tool, "args": args, "raw": raw}, obs)
            messages.append({"role": "user", "content": f"Observation: {obs}"})
        else:
            # Ran out of steps: save whatever we have
            if state.slides and state.saved_path is None:
                TOOLS["save_deck"](state, filename=filename, output_dir=output_dir)
                self._log(self.max_steps, {"tool": "save_deck(auto)"}, state.saved_path)

        return state

    def trajectory_text(self) -> str:
        """The trace in Harness2's shared [ACTION]/[OBSERVATION]/[ERROR] grammar."""
        out = []
        for t in self.trace:
            call = t["call"]
            out.append(f"[ACTION] {call.get('tool')} {json.dumps(call.get('args', {}), ensure_ascii=False)}")
            obs = str(t["observation"])
            out.append(("[ERROR] " if obs.startswith("Error") else "[OBSERVATION] ") + obs)
        return "\n".join(out) + "\n"

    def _log(self, step, call, obs):
        self.trace.append({"step": step, "call": call, "observation": obs})
        if self.verbose:
            print(f"[{step}] {call.get('tool')} -> {str(obs)[:200]}", flush=True)
