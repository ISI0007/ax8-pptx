"""End-to-end smoke test: build a real deck and render it."""

import os
from ax8pptx.spec import Deck, Slide, ChartSpec, ChartSeries
from ax8pptx.render import render

deck = Deck(
    title="Skydeck — Engine Test",
    subtitle="A template-driven presentation engine that renders native, editable PPTX",
    author="Built for Yaseen",
    theme=os.environ.get("THEME", "midnight"),
    slides=[
        Slide(layout="cover",
              title="Skydeck",
              subtitle="AI-native decks that open clean in PowerPoint",
              notes="Cover slide."),
        Slide(layout="section", subtitle="01", title="Why decks fail"),
        Slide(layout="bullets",
              title="Three failure modes of AI-generated decks",
              subtitle="What we designed against",
              bullets=[
                  "Text overflows its box because the model never measures the container",
                  "Layouts are re-invented per slide, so type scale and margins drift",
                  "Charts are pasted as images and cannot be edited or restyled",
                  "Revision means regenerating everything instead of one slide",
              ],
              sources=["Field notes, 2026"]),
        Slide(layout="kpi_row",
              title="What a constrained renderer buys you",
              subtitle="Measured on the same 20-slide brief",
              kpis=[
                  {"value": "0", "label": "PowerPoint repair prompts on open"},
                  {"value": "100%", "label": "Native, editable chart objects"},
                  {"value": "<2s", "label": "Render time for a 20-slide deck"},
                  {"value": "1", "label": "Slide regenerated on revision"},
              ]),
        Slide(layout="chart",
              title="Revision cost: whole-deck vs single-slide",
              subtitle="Seconds to redo one slide",
              chart=ChartSpec(
                  kind="column",
                  categories=["Whole deck reroll", "Outline regen", "Single slide"],
                  series=[ChartSeries(name="Seconds", values=[48, 11, 1.4])],
                  y_title="seconds",
              ),
              bullets=[
                  "Whole-deck reroll costs ~48s of model time",
                  "Single-slide regeneration is near instant because the spec is structured",
                  "This is why slides are objects, not text blobs",
              ]),
        Slide(layout="two_col",
              title="Architecture",
              subtitle="Two layers, one contract",
              left_title="Spec layer",
              left_bullets=[
                  "Dataclass per slide layout",
                  "Content slots only, no geometry",
                  "Validated before render",
                  "Serialises to JSON for the model",
              ],
              right_title="Render layer",
              right_bullets=[
                  "Layout registry owns all coordinates",
                  "Design tokens own all colour and type",
                  "Native charts and tables",
                  "Output is an editable .pptx",
              ]),
        Slide(layout="table",
              title="Layout coverage",
              subtitle="Shipped in v0.1",
              table=[
                  ["Layout", "Purpose", "Status"],
                  ["cover", "Title slide", "shipped"],
                  ["section", "Chapter divider", "shipped"],
                  ["bullets", "Up to 6 points", "shipped"],
                  ["two_col", "Comparison", "shipped"],
                  ["kpi_row", "2-4 metrics", "shipped"],
                  ["chart", "Native column/bar/line/pie", "shipped"],
                  ["table", "Tabular data", "shipped"],
              ]),
        Slide(layout="quote",
              title="",
              quote="The model should never draw. It should decide what goes where.",
              attribution="— the whole design principle"),
        Slide(layout="closing",
              title="Ready to build on",
              subtitle="Template system → outline pipeline → render → verify"),
    ],
)

out = os.path.join("out", f"demo_{deck.theme}.pptx")
os.makedirs(os.path.dirname(out), exist_ok=True)
render(deck, out)
print("WROTE", os.path.abspath(out), os.path.getsize(out), "bytes")
