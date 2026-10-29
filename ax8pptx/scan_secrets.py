import re, pathlib, sys
ROOT = pathlib.Path(__file__).parent / "ax8pptx"
EXTRA = [pathlib.Path(__file__).parent / n for n in
         ("README.md", "requirements.txt", ".env.example", ".gitignore", "LICENSE", "AX8.py")]
PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}", r"gh[opsu]_[A-Za-z0-9]{20,}",
    r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"api[_-]?key\s*[=:]\s*['\"][A-Za-z0-9]{16,}",
]
files = [p for p in ROOT.rglob("*") if p.is_file()
         and not any(x in p.parts for x in ("__pycache__", "out", "art"))]
files += [p for p in EXTRA if p.is_file()]
hits = []
for p in files:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat in PATTERNS:
        for m in re.finditer(pat, t):
            hits.append(f"{p.name}: {m.group(0)[:14]}...")
print(f"scanned {len(files)} files")
print("SECRET HITS:", hits if hits else "none")
