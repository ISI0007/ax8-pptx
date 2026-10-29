"""End-to-end: brief -> arc -> (canned model JSON) -> Deck -> pptx."""
import json, os
from ax8pptx.intake import Brief, Outline, OutlineItem, slide_arc, validate_brief
from ax8pptx.pipeline import build_prompt, deck_from_json, check
from ax8pptx.render import render
from ax8pptx import fit

brief = Brief(topic="Why agentic PPT engines beat prompt-to-slide tools",
              audience="technical founders", goal="persuade",
              slide_count=10, theme="midnight",
              must_include=["clarification card", "native charts"])
assert not validate_brief(brief), validate_brief(brief)

arc = slide_arc(brief)
print("arc:", arc)
assert len(arc) == 10 and arc[0] == "cover" and arc[-1] == "closing"

outline = Outline(title="Agentic decks", subtitle="Engine over prompt",
                  items=[OutlineItem(title=f"s{i}", intent="x", layout_hint=l)
                         for i, l in enumerate(arc)])
print("prompt chars:", len(build_prompt(brief, outline)))

# --- canned model output (what the LLM would return) ---
raw = json.dumps({
  "title": "Engine, not prompt",
  "subtitle": "Why agentic PPT pipelines outperform prompt-to-slide tools",
  "slides": [
    {"layout":"cover","title":"Engine, not prompt","subtitle":"A validated brief, a fixed arc, a renderer that measures"},
    {"layout":"bullets","title":"Prompt-to-slide fails in one place","bullets":[
        "The model picks both the content and the geometry, and gets geometry wrong",
        "Every slide re-invents its own margins, so the deck drifts",
        "The clarification card fixes intent before any slide is generated"],
     "sources":["internal field notes"]},
    {"layout":"kpi_row","title":"Measured differences","kpis":[
        {"value":"0","label":"Repair prompts on open"},
        {"value":"100%","label":"Editable native charts"},
        {"value":"1.4s","label":"Single-slide revision"}]},
    {"layout":"two_col","title":"Two layers","left_title":"Spec",
     "left_bullets":["Content slots only","No coordinates","Validated up front"],
     "right_title":"Render","right_bullets":["Owns geometry","Owns tokens","Native objects"]},
    {"layout":"chart","title":"Revision cost","chart":{
        "kind":"column","categories":["Whole deck","Outline","One slide"],
        "series":[{"name":"seconds","values":[48,11,1.4]}],"y_title":"seconds"},
     "bullets":["Structured specs make surgical edits possible"],
     "sources":["benchmark, 20-slide brief"]},
    {"layout":"quote","quote":"The model should never draw. It should decide what goes where.","attribution":"design principle"},
    {"layout":"bullets","title":"Clarification card","bullets":[
        "Five questions, all cheap to answer",
        "Each answer maps to a render decision, not just prompt text",
        "Kills the most expensive failure: a well-executed wrong deck"],
     "sources":["Skywork.ai product analysis"]},
    {"layout":"table","title":"Coverage","table":[
        ["Layout","Purpose"],["bullets","up to 6 points"],["chart","native, editable"],["table","tabular data"],["kpi_row","2-4 metrics"]]},
    {"layout":"bullets","title":"What is still missing","bullets":[
        "Live research crawl and citation resolution",
        "Automated visual regression on rendered slides",
        "Image generation for cover and section art"]},
    {"layout":"closing","title":"Ship the engine","subtitle":"Then the rest is content"}
  ]
})

deck = deck_from_json(raw, brief)
errs = check(deck, brief)
print("gate errors:", errs)
assert not errs

os.makedirs("ax8pptx/out", exist_ok=True)
out = "ax8pptx/out/pipeline_deck.pptx"
render(deck, out)
print("WROTE", os.path.abspath(out), os.path.getsize(out), "bytes")

# text-fit sanity: a 180-char bullet at body size in a half-column must shrink
box = fit.Box(width_in=5.0, height_in=3.2)
long_bullets = ["x" * 110 for _ in range(5)]
print("est height @16pt:", round(fit.est_height(long_bullets, box, 16), 2), "in")
print("fitted size:", fit.fit_size(long_bullets, box, 16), "pt")
print("needs split:", fit.needs_split(long_bullets, box))
print("OK")
