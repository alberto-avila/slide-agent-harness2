"""Load source documents (.txt, .md, .pdf)."""
from pathlib import Path


def load_source(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    return p.read_text(encoding="utf-8", errors="ignore")
