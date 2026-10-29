import re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent          # ax8pptx/ package dir
REPO = ROOT.parent                                       # repo root
SKIP = {"__pycache__", ".git", "out", "art", ".venv", "venv", "dist", "build"}
PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"gh[opsu]_[A-Za-z0-9]{20,}",
    r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"api[_-]?key\s*[=:]\s*['\"][A-Za-z0-9]{16,}",
]

files = []
for base in (ROOT, REPO):
    for p in base.iterdir():
        if p.is_dir():
            if p.name in SKIP:
                continue
            if base is REPO and p.name != ROOT.name:
                continue
            files.extend(q for q in p.rglob("*") if q.is_file() and not (SKIP & set(q.parts)))
        elif p.is_file() and p.suffix in (".py", ".md", ".txt", ".example", "") or p.name == ".gitignore":
            files.append(p)

hits, scanned = [], 0
for p in set(files):
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    scanned += 1
    for pat in PATTERNS:
        for m in re.finditer(pat, t):
            hits.append(f"{p.relative_to(REPO)}: {m.group(0)[:14]}...")

print(f"scanned {scanned} files")
print("SECRET HITS:", hits if hits else "none")
sys.exit(1 if hits else 0)
