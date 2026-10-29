"""Text fit - the difference between "AI slop" and "designed".

Estimates rendered text height from character counts and advances, then
either shrinks the type or splits the slide. No hardcoded guesses about
what "looks fine".
"""

from dataclasses import dataclass
from typing import List, Tuple

# Rough advance widths (em) for a typical sans face at body weight.
EM_WIDE = 0.545
LINE_HEIGHT = 1.22


@dataclass
class Box:
    width_in: float
    height_in: float


def est_lines(text: str, width_in: float, size_pt: float) -> int:
    """Estimated wrapped line count for a single paragraph."""
    if not text:
        return 0
    # usable glyph width in points, minus the bullet gutter allowance
    usable_pt = (width_in * 72) - (size_pt * 1.2)
    if usable_pt <= 0:
        return 99
    chars_per_line = max(1, int(usable_pt / (size_pt * EM_WIDE)))
    return max(1, -(-len(text) // chars_per_line))


def est_height(texts: List[str], box: Box, size_pt: float) -> float:
    """Total rendered height in inches for a bullet stack."""
    spacing_pt = size_pt * 0.62
    total_pt = 0.0
    for t in texts:
        lines = est_lines(t, box.width_in, size_pt)
        total_pt += lines * size_pt * LINE_HEIGHT + spacing_pt
    return total_pt / 72.0


def fit_size(texts: List[str], box: Box, start_pt: int, min_pt: int = 12) -> int:
    """Largest size (pt) at which the stack fits. Returns min_pt if nothing fits."""
    size = start_pt
    while size > min_pt:
        if est_height(texts, box, size) <= box.height_in:
            return size
        size -= 1
    return min_pt


def needs_split(texts: List[str], box: Box, min_pt: int = 13) -> bool:
    return est_height(texts, box, min_pt) > box.height_in


def balance_split(texts: List[str]) -> Tuple[List[str], List[str]]:
    """Split a bullet list near the middle by character weight, on item bounds."""
    total = sum(len(t) for t in texts)
    acc, cut = 0, 0
    for i, t in enumerate(texts):
        acc += len(t)
        cut = i + 1
        if acc >= total / 2:
            break
    return texts[:cut], texts[cut:]
