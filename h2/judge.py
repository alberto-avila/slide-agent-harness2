"""Deck judge: deterministic best-practice checks plus an LLM rubric, as pass/fail criteria.

Harness2 only calls this after selection, so these criteria never reach the improver.
"""
import json
import os

from slide_agent.best_practices import MAX_BULLETS, MAX_TITLE_WORDS, MAX_WORDS_PER_BULLET
from slide_agent.llm import get_llm, load_dotenv

# Each criterion has anchors so the judge can't hand out 5s by default.
RUBRIC = {
    "story": ("The deck follows a clear arc: problem, why it matters, insight, evidence, call to action.",
              "1 = a list of unrelated topics; 3 = a recognisable order but weak links or a missing step; "
              "5 = every slide builds on the previous one and the ending follows from the evidence"),
    "assertion_titles": ("Slide titles state takeaways (assertions) rather than bare topics.",
                         "1 = titles are nouns like 'Overview' or 'Benefits'; 3 = about half are assertions; "
                         "5 = every content title is a specific claim the slide proves"),
    "audience_fit": ("Vocabulary and depth suit the stated audience.",
                     "1 = jargon or depth clearly wrong for the audience; 3 = mostly fits with some lapses; "
                     "5 = every slide is pitched exactly for this audience"),
    "accuracy": ("Content is factually sound, specific, and faithful to the source if one was given.",
                 "1 = errors or invented facts; 3 = correct but vague or generic; "
                 "5 = correct, concrete, and every claim traceable to the source when there is one"),
    "notes_quality": ("Speaker notes add useful detail beyond the bullets.",
                      "1 = missing or repeating the bullets; 3 = some added detail; "
                      "5 = notes on every content slide give the presenter talking points, data or examples"),
}

JUDGE_SYSTEM = (
    "You are a strict presentation coach. Grade harshly and consistently: 3 is a competent "
    "deck, 4 is clearly strong, and 5 is rare and reserved for work you could not improve. "
    "Do not reward length or polish that lacks substance."
)


def judge_llm():
    """The judge model is configured separately from the agent (see .env)."""
    load_dotenv()
    provider = os.getenv("JUDGE_PROVIDER", "openai")
    model = os.getenv("JUDGE_MODEL") or None
    kwargs = {"temperature": 0.0} if provider == "ollama" else {}
    return get_llm(provider, model=model, **kwargs)


def render_deck(slides: list[dict]) -> str:
    out = []
    for n, s in enumerate(slides, 1):
        out.append(f"## Slide {n} [{s.get('layout')}]: {s.get('title')}")
        out += [f"- {b}" for b in s.get("bullets", [])]
        if s.get("notes"):
            out.append(f"Notes: {s['notes']}")
    return "\n".join(out)


def rule_checks(slides: list[dict], task: dict) -> dict[str, bool]:
    content = [s for s in slides if s.get("layout") == "content"]
    bullets = [b for s in content for b in s.get("bullets", [])]
    tail = " ".join(s.get("title", "").lower() for s in slides[-2:])
    return {
        "has_slides": len(slides) >= 3,
        "slide_count_near_target": abs(len(slides) - task["slides"]) <= 2,
        "title_slide_first": bool(slides) and slides[0].get("layout") == "title",
        "closing_slide": any(k in tail for k in ("summary", "takeaway", "next step", "question", "conclusion", "q&a")),
        "short_titles": all(len(s.get("title", "").split()) <= MAX_TITLE_WORDS for s in slides),
        "max_bullets": all(len(s.get("bullets", [])) <= MAX_BULLETS for s in content),
        "short_bullets": bool(bullets) and all(len(b.split()) <= MAX_WORDS_PER_BULLET for b in bullets),
        "speaker_notes": bool(content) and all(s.get("notes", "").strip() for s in content),
    }


def llm_rubric(slides: list[dict], task: dict, source_text: str = "") -> dict:
    prompt = (
        f"Topic: {task['topic']}\nAudience: {task['audience']}\n"
        f"Requested slide count: about {task['slides']}\n\n"
        + (f"Source document the deck must be faithful to:\n{source_text}\n\n" if source_text else "")
        + f"Deck:\n{render_deck(slides)}\n\n"
        "Rate each criterion from 1 to 5 using its anchors:\n"
        + "\n".join(f"- {k}: {desc} Anchors: {anchors}." for k, (desc, anchors) in RUBRIC.items())
        + "\n\nReply with only a JSON object of the form "
        '{"<criterion>": {"reason": "<one sentence citing specific slides>", "rating": <1-5>}, ...} '
        "covering every criterion. Write the reason before deciding the rating."
    )
    llm = judge_llm()
    raw = llm.chat([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": prompt}])
    data = json.loads(raw)
    return {
        "model": f"{type(llm).__name__}:{llm.model}",
        "ratings": {k: int(data[k]["rating"]) for k in RUBRIC},
        "reasons": {k: str(data[k].get("reason", "")) for k in RUBRIC},
    }


def score_deck(slides: list[dict], task: dict, source_text: str = "") -> dict:
    rules = rule_checks(slides, task)
    if slides:
        rubric = llm_rubric(slides, task, source_text)
    else:
        rubric = {"model": "none", "ratings": {k: 1 for k in RUBRIC}, "reasons": {k: "no deck" for k in RUBRIC}}
    # Points, not pass/fail: a 4/5 threshold hid every difference once the judge got strict.
    rules_passed = sum(rules.values())
    rubric_points = sum(rubric["ratings"].values())
    return {
        "rules_passed": rules_passed,
        "rules_total": len(rules),
        "rubric_points": rubric_points,
        "rubric_max": 5 * len(RUBRIC),
        # Harness2's core.judge reads these two: one point per rule plus 1-5 per rubric item.
        "n_passed": rules_passed + rubric_points,
        "n_criteria": len(rules) + 5 * len(RUBRIC),
        "rules": rules,
        "ratings": rubric["ratings"],
        "reasons": rubric["reasons"],
        "judge_model": rubric["model"],
    }
