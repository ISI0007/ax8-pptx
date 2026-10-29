"""Slide spec - the contract between the LLM and the renderer.

The LLM NEVER emits XML or coordinates. It emits these dataclasses.
Every field is a content slot; geometry lives in the layout registry.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal


LayoutName = Literal[
    "cover", "section", "bullets", "two_col", "kpi_row",
    "chart", "quote", "table", "closing",
]


@dataclass
class ChartSeries:
    name: str
    values: List[float]


@dataclass
class ChartSpec:
    kind: Literal["column", "bar", "line", "pie"] = "column"
    categories: List[str] = field(default_factory=list)
    series: List[ChartSeries] = field(default_factory=list)
    y_title: str = ""


@dataclass
class Slide:
    layout: LayoutName
    title: str = ""
    subtitle: str = ""
    bullets: List[str] = field(default_factory=list)
    left_title: str = ""
    left_bullets: List[str] = field(default_factory=list)
    right_title: str = ""
    right_bullets: List[str] = field(default_factory=list)
    kpis: List[Dict[str, str]] = field(default_factory=list)   # {value,label}
    chart: Optional[ChartSpec] = None
    quote: str = ""
    attribution: str = ""
    table: List[List[str]] = field(default_factory=list)       # row 0 = header
    notes: str = ""
    sources: List[str] = field(default_factory=list)


@dataclass
class Deck:
    title: str
    subtitle: str = ""
    author: str = ""
    theme: str = "midnight"
    slides: List[Slide] = field(default_factory=list)
    art_path: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def validate_deck(deck: Deck) -> List[str]:
    """Return a list of problems. Empty list == renderable."""
    errs: List[str] = []
    if not deck.slides:
        errs.append("deck has no slides")
        return errs
    if deck.slides[0].layout != "cover":
        errs.append("first slide must be layout 'cover'")
    for i, s in enumerate(deck.slides, 1):
        tag = f"slide {i} ({s.layout})"
        if s.layout in ("cover", "section", "bullets", "closing") and not s.title:
            errs.append(f"{tag}: missing title")
        if s.layout == "bullets" and not s.bullets:
            errs.append(f"{tag}: layout 'bullets' needs bullets")
        if s.layout == "chart" and not s.chart:
            errs.append(f"{tag}: layout 'chart' needs chart spec")
        if s.layout == "table" and len(s.table) < 2:
            errs.append(f"{tag}: layout 'table' needs header + >=1 row")
        if s.layout == "kpi_row" and not s.kpis:
            errs.append(f"{tag}: layout 'kpi_row' needs kpis")
        # content budget: guards against overflow
        if len(s.bullets) > 6:
            errs.append(f"{tag}: {len(s.bullets)} bullets (max 6) - split the slide")
    return errs
