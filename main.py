"""CLI entry point.

Examples:
    python main.py --topic "Intro to RAG" --audience "executives"
    python main.py --topic "Q3 findings" --source report.pdf --slides 8
"""
import argparse
import json

from slide_agent import SlideAgent, get_llm
from slide_agent.sources import load_source


def main():
    ap = argparse.ArgumentParser(description="AI slide generator agent")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--audience", default="general audience")
    ap.add_argument("--source", help="Optional .txt/.md/.pdf source document")
    ap.add_argument("--slides", type=int, default=10)
    ap.add_argument("--out", default="deck.pptx")
    ap.add_argument("--model", default=None, help="Ollama model (default gemma4:latest)")
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--trace", help="Optional path to write the JSON step trace")
    a = ap.parse_args()

    source_text = load_source(a.source) if a.source else ""
    agent = SlideAgent(get_llm("ollama", model=a.model), max_steps=a.max_steps)
    state = agent.run(a.topic, a.audience, source_text, a.slides, a.out)

    if a.trace:
        with open(a.trace, "w", encoding="utf-8") as f:
            json.dump(agent.trace, f, indent=2)
    print(f"\nDone. {len(state.slides)} slides -> {state.saved_path}")


if __name__ == "__main__":
    main()
