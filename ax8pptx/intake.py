"""Intake (clarification card) - Skywork's anti-waste trick.

Ask the five questions that change the deck BEFORE generating anything.
Each answer maps to a render decision, not just prompt text.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Literal


@dataclass
class Brief:
    topic: str
    audience: str = "general professional"      # drives register + density
    goal: Literal["inform", "persuade", "sell", "teach", "report"] = "inform"
    slide_count: int = 10                        # must be in ALLOWED_COUNTS
    theme: str = "midnight"
    must_include: List[str] = field(default_factory=list)
    must_exclude: List[str] = field(default_factory=list)
    language: str = "en"

    def to_dict(self) -> dict:
        return asdict(self)


ALLOWED_COUNTS = (8, 10, 12, 15, 20)


def questions() -> List[dict]:
    """The card shown to the user. 5 questions, all cheap to answer."""
    return [
        {"id": "topic", "q": "What is the deck about? (one line)",
         "why": "sets the research query"},
        {"id": "audience", "q": "Who reads it? (e.g. CTO, investor, student, client)",
         "why": "sets register and how much jargon is allowed"},
        {"id": "goal", "q": "What should it achieve?",
         "choices": ["inform", "persuade", "sell", "teach", "report"],
         "why": "sets the slide arc, not just the wording"},
        {"id": "slide_count", "q": "How many slides?", "choices": list(ALLOWED_COUNTS),
         "why": "sets the outline budget so we never pad or truncate"},
        {"id": "must_include", "q": "Anything that must appear? (comma separated)",
         "why": "reserved slots in the outline"},
    ]


def brief_from_answers(answers: dict) -> Brief:
    b = Brief(
        topic=answers.get("topic", "").strip(),
        audience=answers.get("audience", "general professional"),
        goal=answers.get("goal", "inform"),
        slide_count=int(answers.get("slide_count", 10)),
        theme=answers.get("theme", "midnight"),
        language=answers.get("language", "en"),
    )
    inc = answers.get("must_include") or ""
    b.must_include = [x.strip() for x in inc.split(",") if x.strip()]
    exc = answers.get("must_exclude") or ""
    b.must_exclude = [x.strip() for x in exc.split(",") if x.strip()]
    return b


def validate_brief(b: Brief) -> List[str]:
    errs = []
    if not b.topic:
        errs.append("brief.topic is required")
    if b.slide_count not in ALLOWED_COUNTS:
        errs.append(f"slide_count must be one of {ALLOWED_COUNTS}")
    if len(b.must_include) > b.slide_count - 4:
        errs.append("too many must_include items for this slide budget")
    return errs


# --- Outline contract -----------------------------------------------------

@dataclass
class OutlineItem:
    title: str
    intent: str                 # one sentence: what this slide must land
    layout_hint: str = "bullets"
    needs_data: bool = False    # requires research/chart/table


@dataclass
class Outline:
    title: str
    subtitle: str
    items: List[OutlineItem]

    def to_dict(self) -> dict:
        return asdict(self)


def validate_outline(o: Outline, brief: Brief) -> List[str]:
    errs = []
    n = len(o.items)
    if n != brief.slide_count:
        errs.append(f"outline has {n} items, brief asked for {brief.slide_count}")
    if not any(i.layout_hint == "section" for i in o.items) and n >= 12:
        errs.append("decks of 12+ slides need at least one section divider")
    covered = " ".join(i.title.lower() for i in o.items)
    for req in brief.must_include:
        if req.lower() not in covered:
            errs.append(f"must_include not found in outline: {req!r}")
    for ban in brief.must_exclude:
        if ban.lower() in covered:
            errs.append(f"must_exclude appears in outline: {ban!r}")
    return errs


ARC = {
    "inform":    ["cover", "bullets", "bullets", "two_col", "chart", "bullets", "closing"],
    "persuade":  ["cover", "bullets", "kpi_row", "two_col", "chart", "quote", "closing"],
    "sell":      ["cover", "bullets", "chart", "kpi_row", "quote", "closing"],
    "teach":     ["cover", "section", "bullets", "bullets", "chart", "bullets", "closing"],
    "report":    ["cover", "kpi_row", "chart", "table", "bullets", "closing"],
}


def slide_arc(brief: Brief) -> List[str]:
    """Deterministic layout sequence sized to the slide budget.

    The LLM fills content into this arc; it never chooses the order.
    """
    base = list(ARC.get(brief.goal, ARC["inform"]))
    n = brief.slide_count
    if n < len(base):
        return base[: n - 1] + ["closing"]
    # insert section dividers for long decks
    body = base[1:-1]
    while len(base) < n:
        need_dividers = n - len(base) >= 3 and base.count("section") < 3
        if need_dividers:
            base.insert(len(base) // 2, "section")
        else:
            base.insert(-1, "bullets")
    return base[: n - 1] + ["closing"]
