"""Replace local absolute paths in run data with neutral placeholders before sharing it.

    python -m h2.scrub_paths results reports

Run records (selection.json, traces, improver prompts) embed absolute paths, which reveal the
local username and folder layout. This rewrites, in order:
    <project root>  ->  <project>
    <home folder>   ->  <home>
in every text file under the given folders, in each form a Windows path appears in: backslashes,
JSON-escaped backslashes, forward slashes and Git Bash style (/c/Users/...), any drive-letter case.
JSON files are re-parsed afterwards to make sure they are still valid.
"""
import argparse
import json
import re
from pathlib import Path

TEXT_SUFFIXES = {".json", ".md", ".txt", ".html", ".py", ".toml", ".yaml", ".yml", ".csv", ".log"}
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def path_patterns(p: Path) -> list[re.Pattern]:
    """Regexes matching the spellings of one absolute path."""
    s = str(p)
    forms = {s, s.replace("\\", "/"), s.replace("\\", "\\\\")}
    if re.match(r"^[A-Za-z]:\\", s):  # Git Bash spelling: /c/Users/...
        forms.add("/" + s[0].lower() + s[2:].replace("\\", "/"))
    return [re.compile(re.escape(f), re.IGNORECASE) for f in sorted(forms, key=len, reverse=True)]


def scrub_text(text: str, replacements: list[tuple[list[re.Pattern], str]]) -> str:
    for patterns, placeholder in replacements:
        for pat in patterns:
            text = pat.sub(placeholder, text)
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    args = ap.parse_args(argv)
    replacements = [(path_patterns(PROJECT_ROOT), "<project>"), (path_patterns(Path.home()), "<home>")]

    changed = 0
    for folder in args.folders:
        for f in sorted(folder.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in TEXT_SUFFIXES:
                continue
            original = f.read_text(encoding="utf-8", errors="surrogateescape")
            cleaned = scrub_text(original, replacements)
            if cleaned == original:
                continue
            if f.suffix.lower() == ".json":
                json.loads(cleaned)  # raises if the rewrite broke the file
            changed += 1
            if not args.dry_run:
                f.write_text(cleaned, encoding="utf-8", errors="surrogateescape")
    print(f"{'Would rewrite' if args.dry_run else 'Rewrote'} {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
