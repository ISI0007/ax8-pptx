"""AX8 PPTX - one command: topic -> researched, illustrated, rendered deck.

    python -m ax8pptx.cli "Your topic" --audience "CTO" --goal persuade --slides 10

Behaviour:
  * with DEEPSEEK_API_KEY set  -> live LLM generation
  * without it                 -> dry run (prints the prompt, exits 2)
  * --offline                  -> canned fixture deck, always renderable
  * --research                 -> crawl citation sources before generating
  * --no-art                   -> skip generated cover art
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from .intake import Brief, Outline, OutlineItem, slide_arc, validate_brief
from .pipeline import build_prompt, deck_from_json, check
from .render import render
from .research import crawl, citation_block, search_urls
from .images import make_cover_art


def _outline_from_brief(brief: Brief, arc):
    return Outline(
        title=brief.topic,
        subtitle=f"A {brief.goal} deck for {brief.audience}",
        items=[OutlineItem(title=f"slide {i+1}", intent=brief.topic, layout_hint=l)
               for i, l in enumerate(arc)],
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ax8pptx")
    ap.add_argument("topic", nargs="?", default="")
    ap.add_argument("--audience", default="general professional")
    ap.add_argument("--goal", default="inform",
                    choices=["inform", "persuade", "sell", "teach", "report"])
    ap.add_argument("--slides", type=int, default=10)
    ap.add_argument("--theme", default="midnight")
    ap.add_argument("--must-include", default="")
    ap.add_argument("--research", action="store_true", help="crawl citation sources first")
    ap.add_argument("--seeds", default="", help="comma-separated URLs for research")
    ap.add_argument("--no-art", action="store_true", help="skip generated cover art")
    ap.add_argument("--offline", action="store_true", help="use canned fixture (no LLM)")
    ap.add_argument("--out", default="")
    ap.add_argument("--print-prompt", action="store_true")
    a = ap.parse_args(argv)

    brief = Brief(topic=a.topic, audience=a.audience, goal=a.goal,
                  slide_count=a.slides, theme=a.theme,
                  must_include=[x.strip() for x in a.must_include.split(",") if x.strip()])
    errs = validate_brief(brief)
    if errs:
        print("brief errors:", errs, file=sys.stderr)
        return 2

    arc = slide_arc(brief)
    outline = _outline_from_brief(brief, arc)
    prompt = build_prompt(brief, outline)

    # --- research -------------------------------------------------------
    if a.research:
        seeds = [s.strip() for s in a.seeds.split(",") if s.strip()]
        if not seeds:
            seeds = search_urls(a.topic)
        if seeds:
            srcs = crawl(seeds, a.topic)
            good = [s for s in srcs if s.score >= 0]
            print(f"research: {len(good)}/{len(srcs)} sources reachable")
            if good:
                prompt += "\n\nCITATIONS (cite only from this list):\n" + citation_block(good)
        else:
            print("research: no seeds resolved (SERP blocked)", file=sys.stderr)

    if a.print_prompt or (not a.offline and not os.environ.get("DEEPSEEK_API_KEY")):
        print(prompt)
        if not a.offline:
            print("\n[no DEEPSEEK_API_KEY - dry run]", file=sys.stderr)
            return 2
        return 0

    # --- generate -------------------------------------------------------
    if a.offline:
        from .fixture import FIXTURE_JSON as raw
        _fix = deck_from_json(raw, brief)
        if len(_fix.slides) != brief.slide_count:
            print(f"note: fixture has {len(_fix.slides)} slides; using that count, not {brief.slide_count}",
                  file=sys.stderr)
            brief.slide_count = len(_fix.slides)
    else:
        from .llm import complete, LLMError
        try:
            raw = complete(prompt, system="Return valid JSON only.")
        except LLMError as e:
            print(f"LLM failed: {e}", file=sys.stderr)
            return 3

    deck = deck_from_json(raw, brief)
    gate = check(deck, brief)
    if gate:
        print("gate errors:", gate, file=sys.stderr)
        return 4

    # --- art ------------------------------------------------------------
    if not a.no_art:
        from .tokens import get_theme
        try:
            t = get_theme(deck.theme)
            seed = f"{deck.title}|{deck.subtitle}|{deck.theme}"
            art_dir = os.path.join(ROOT, "out", "art")
            os.makedirs(art_dir, exist_ok=True)
            art = os.path.join(art_dir, f"cover_{abs(hash(seed)) % 10**10}.jpg")
            make_cover_art(art, seed, t.palette.accent, t.palette.accent2, t.palette.bg)
            deck.art_path = art
        except Exception as e:
            print(f"art skipped: {e}", file=sys.stderr)

    out = a.out or os.path.join(ROOT, "out", f"{abs(hash(deck.title)) % 10**8}.pptx")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    render(deck, out)
    print(f"WROTE {os.path.abspath(out)} ({os.path.getsize(out)} bytes, {len(deck.slides)} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
