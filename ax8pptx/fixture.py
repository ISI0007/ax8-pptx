"""Canned deck used for offline mode and regression testing."""

FIXTURE_JSON = r'''
{
  "title": "AX8 PPTX",
  "subtitle": "A validated pipeline from brief to rendered deck",
  "slides": [
    {"layout":"cover","title":"AX8 PPTX","subtitle":"Brief, arc, research, render. One command."},
    {"layout":"bullets","title":"Four capabilities, one pipeline","bullets":[
        "Live model call with a strict JSON contract",
        "Research crawl that fills real citations",
        "Deterministic generated cover art",
        "Structural regression so decks never silently drift"],
     "sources":["AX8 PPTX build log"]},
    {"layout":"kpi_row","title":"Engine status","kpis":[
        {"value":"9","label":"Layouts shipped"},
        {"value":"3","label":"Themes"},
        {"value":"100%","label":"Native editable objects"},
        {"value":"0","label":"Repair prompts"}]},
    {"layout":"two_col","title":"Two layers","left_title":"Spec",
     "left_bullets":["Content slots only","No coordinates","Validated before render"],
     "right_title":"Render","right_bullets":["Owns geometry","Owns tokens","Native charts"]},
    {"layout":"chart","title":"Where time goes","chart":{
        "kind":"column","categories":["Research","Outline","Compose","Render"],
        "series":[{"name":"seconds","values":[24,6,31,1.4]}],"y_title":"seconds"},
     "bullets":["Composition dominates","Render is effectively free"],
     "sources":["internal timing"]},
    {"layout":"quote","quote":"The model should never draw. It should decide what goes where.","attribution":"design principle"},
    {"layout":"table","title":"Capability coverage","table":[
        ["Capability","Status"],["Live LLM call","wired"],["Research crawl","wired"],
        ["Image generation","local + remote"],["Visual regression","structural"]]},
    {"layout":"bullets","title":"What remains","bullets":[
        "Pixel diff needs LibreOffice or PowerPoint installed",
        "SERP scraping is best-effort and rate limited",
        "Remote image backend needs an image API key"]},
    {"layout":"section","title":"Ship it","subtitle":"02"},
    {"layout":"closing","title":"AX8 PPTX","subtitle":"Brief to deck, verified"}
  ]
}
'''
