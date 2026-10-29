"""Outline -> Deck pipeline.

Two responsibilities:
  1. emit the JSON contract the LLM must answer in (prompt side)
  2. assemble a validated Deck from the LLM's JSON (trust side)

The LLM never picks layouts or order - the arc from intake.py does.
"""

import json
from typing import List

from .spec import Deck, Slide, ChartSpec, ChartSeries, validate_deck
from .intake import Brief, Outline, OutlineItem, slide_arc, validate_brief, validate_outline


SPEC_SCHEMA = """{
  "title": "deck title (<= 60 chars)",
  "subtitle": "one line (<= 110 chars)",
  "slides": [
    {
      "layout": "<from the provided arc, in order>",
      "title": "<= 60 chars",
      "subtitle": "optional kicker, <= 50 chars",
      "bullets": ["<= 110 chars each", "max 6 items"],
      "left_title": "...", "left_bullets": ["..."],
      "right_title": "...", "right_bullets": ["..."],
      "kpis": [{"value": "42%", "label": "<= 40 chars"}],
      "chart": {"kind": "column|bar|line|pie", "categories": ["..."],
                "series": [{"name": "...", "values": [1, 2, 3]}], "y_title": "..."},
      "quote": "...", "attribution": "...",
      "table": [["Header A", "Header B"], ["cell", "cell"]],
      "notes": "speaker notes <= 400 chars",
      "sources": ["source url or name"]
    }
  ]
}"""


def build_prompt(brief: Brief, outline: Outline) -> str:
    """The exact instruction block. Deterministic, no chat framing."""
    arc = [i.layout_hint for i in outline.items]
    lines = [
        "You are a presentation composer. Return JSON only. No prose, no markdown fences.",
        "",
        f"BRIEF: {json.dumps(brief.to_dict(), ensure_ascii=False)}",
        f"OUTLINE: {json.dumps(outline.to_dict(), ensure_ascii=False)}",
        f"LAYOUT ARC (use exactly this order, {len(arc)} slides): {json.dumps(arc)}",
        "",
        "RULES:",
        "1. Fill every slide in the arc. Do not add, drop, merge, or reorder slides.",
        "2. Respect every character limit. Shorter is better; the renderer enforces fit.",
        "3. Only include fields the layout uses. A 'chart' slide needs 'chart'.",
        "4. Chart values must be numbers. Categories and values must be equal length.",
        "5. Every factual claim needs an entry in that slide's 'sources'.",
        "6. No deck-level 'theme' field; the renderer sets it.",
        "7. If a slide has no data, use prose bullets - never invent numbers.",
        "",
        "RESPONSE SCHEMA:",
        SPEC_SCHEMA,
    ]
    return "\n".join(lines)


def deck_from_json(raw: str, brief: Brief) -> Deck:
    """Parse LLM output into a Deck. Tolerates fences and stray prose."""
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.split("```")[1]
        if txt.lstrip().startswith("json"):
            txt = txt.lstrip()[4:]
    start, end = txt.find("{"), txt.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in model output")
    data = json.loads(txt[start:end + 1])

    slides: List[Slide] = []
    for s in data.get("slides", []):
        chart = None
        if isinstance(s.get("chart"), dict):
            cd = s["chart"]
            chart = ChartSpec(
                kind=cd.get("kind", "column"),
                categories=[str(c) for c in cd.get("categories", [])],
                series=[ChartSeries(name=str(x.get("name", "")),
                                    values=[float(v) for v in x.get("values", [])])
                        for x in cd.get("series", [])],
                y_title=str(cd.get("y_title", "")),
            )
        slides.append(Slide(
            layout=s.get("layout", "bullets"),
            title=s.get("title", "") or "",
            subtitle=s.get("subtitle", "") or "",
            bullets=[str(b) for b in s.get("bullets", [])],
            left_title=s.get("left_title", "") or "",
            left_bullets=[str(b) for b in s.get("left_bullets", [])],
            right_title=s.get("right_title", "") or "",
            right_bullets=[str(b) for b in s.get("right_bullets", [])],
            kpis=s.get("kpis", []) or [],
            chart=chart,
            quote=s.get("quote", "") or "",
            attribution=s.get("attribution", "") or "",
            table=[[str(c) for c in row] for row in s.get("table", [])],
            notes=s.get("notes", "") or "",
            sources=[str(x) for x in s.get("sources", [])],
        ))

    return Deck(
        title=data.get("title", brief.topic),
        subtitle=data.get("subtitle", ""),
        author="",
        theme=brief.theme,
        slides=slides,
    )


def check(deck: Deck, brief: Brief) -> List[str]:
    """All gates in one place: brief, arc length, per-slide validity."""
    errs = validate_brief(brief)
    if errs:
        return errs
    if len(deck.slides) != brief.slide_count:
        errs.append(f"deck has {len(deck.slides)} slides, brief asked for {brief.slide_count}")
    errs.extend(validate_deck(deck))
    return errs
