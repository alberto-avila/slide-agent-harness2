"""LLM provider abstraction. Add a new class here to switch providers."""
import os


class LLM:
    # Token counts of the most recent call, when the provider reports them.
    last_usage: dict | None = None

    def chat(self, messages: list[dict]) -> str:
        """Take a list of {"role", "content"} messages, return the assistant text."""
        raise NotImplementedError


class OllamaLLM(LLM):
    def __init__(self, model: str = None, host: str = None, temperature: float = 0.4,
                 json_mode: bool = True, num_ctx: int = 16384):
        import ollama

        self.model = model or os.getenv("SLIDE_AGENT_MODEL", "gemma4:latest")
        self.client = ollama.Client(host=host or os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        self.temperature = temperature
        self.json_mode = json_mode
        self.num_ctx = num_ctx

    def chat(self, messages):
        resp = self.client.chat(
            model=self.model,
            messages=messages,
            format="json" if self.json_mode else None,
            options={"temperature": self.temperature, "num_ctx": self.num_ctx},
        )
        return resp["message"]["content"]


class OpenAILLM(LLM):
    """OpenAI or any OpenAI-compatible endpoint (set OPENAI_BASE_URL to point elsewhere)."""

    def __init__(self, model: str = None, json_mode: bool = True, **_ignored):
        from openai import OpenAI

        load_dotenv()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-6-astra")
        self.client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None)  # reads OPENAI_API_KEY
        self.json_mode = json_mode

    def chat(self, messages):
        extra = {"response_format": {"type": "json_object"}} if self.json_mode else {}
        resp = self.client.chat.completions.create(model=self.model, messages=messages, **extra)
        u = resp.usage
        self.last_usage = {"input": u.prompt_tokens, "output": u.completion_tokens} if u else None
        return resp.choices[0].message.content


def load_dotenv(path: str = None) -> None:
    """Minimal .env loader: KEY=VALUE lines; existing environment variables win."""
    from pathlib import Path

    p = Path(path) if path else Path(__file__).resolve().parent.parent / ".env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            if val:  # blank entries mean "unset"; an empty OPENAI_BASE_URL breaks the SDK
                os.environ.setdefault(key.strip(), val)


def get_llm(provider: str = "ollama", **kwargs) -> LLM:
    if provider == "ollama":
        return OllamaLLM(**kwargs)
    if provider == "openai":
        return OpenAILLM(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")
