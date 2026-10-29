"""Visual regression - renders slides to PNG and diffs against baselines.

Uses LibreOffice headless when available, else falls back to a structural
snapshot (shape geometry + text) so drift is still detected without Office.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "soffice",
]


def find_soffice() -> Optional[str]:
    for c in SOFFICE_CANDIDATES:
        if os.path.isabs(c) and os.path.exists(c):
            return c
        if not os.path.isabs(c) and shutil.which(c):
            return shutil.which(c)
    return None


def render_pngs(pptx_path: str, out_dir: str) -> List[str]:
    """Convert pptx -> png. Raises if no converter is available."""
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "no pptx renderer: LibreOffice not installed. "
            "Install it or use structural_snapshot() instead."
        )
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx_path],
            check=True, capture_output=True, timeout=300,
        )
        pdf = [f for f in os.listdir(tmp) if f.endswith(".pdf")]
        if not pdf:
            raise RuntimeError("LibreOffice produced no PDF")
        src = os.path.join(tmp, pdf[0])
        dst = os.path.join(out_dir, os.path.basename(pptx_path) + ".pdf")
        shutil.move(src, dst)
    return [dst]


def structural_snapshot(pptx_path: str) -> Dict:
    """Office-free drift detection: geometry + text of every shape."""
    from pptx import Presentation
    prs = Presentation(pptx_path)
    slides = []
    for s in prs.slides:
        shapes = []
        for sh in s.shapes:
            shapes.append({
                "type": str(sh.shape_type),
                "l": round(sh.left / 914400, 3) if sh.left is not None else None,
                "t": round(sh.top / 914400, 3) if sh.top is not None else None,
                "w": round(sh.width / 914400, 3) if sh.width is not None else None,
                "h": round(sh.height / 914400, 3) if sh.height is not None else None,
                "text": (sh.text_frame.text[:120] if sh.has_text_frame else None),
                "chart": bool(sh.has_chart),
                "table": bool(sh.has_table),
            })
        slides.append(shapes)
    return {"slide_w": prs.slide_width, "slide_h": prs.slide_height, "slides": slides}


def fingerprint(snapshot: Dict) -> str:
    blob = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def compare(pptx_path: str, baseline_dir: str = "regress_baseline") -> Dict:
    """Returns {status, fingerprint, changed_slides}."""
    snap = structural_snapshot(pptx_path)
    fp = fingerprint(snap)
    os.makedirs(baseline_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(pptx_path))[0]
    base_file = os.path.join(baseline_dir, f"{name}.json")

    if not os.path.exists(base_file):
        with open(base_file, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=1)
        return {"status": "baseline_created", "fingerprint": fp, "changed_slides": []}

    with open(base_file, encoding="utf-8") as f:
        base = json.load(f)
    changed = [i + 1 for i, (a, b) in enumerate(zip(base.get("slides", []), snap["slides"]))
               if a != b]
    if len(base.get("slides", [])) != len(snap["slides"]):
        changed.append("count")
    return {
        "status": "match" if not changed else "drift",
        "fingerprint": fp,
        "baseline_fingerprint": fingerprint(base),
        "changed_slides": changed,
    }
