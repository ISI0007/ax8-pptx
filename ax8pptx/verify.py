"""Structural verification - reopen the file and assert on the object graph."""
import zipfile, sys
from pptx import Presentation

path = sys.argv[1]
prs = Presentation(path)
print("slides:", len(prs.slides))
print("size_in:", round(prs.slide_width/914400, 3), "x", round(prs.slide_height/914400, 3))
charts = tables = textboxes = 0
for i, s in enumerate(prs.slides, 1):
    kinds = []
    for sh in s.shapes:
        if sh.has_chart:
            charts += 1; kinds.append("chart")
        elif sh.has_table:
            tables += 1; kinds.append("table")
        elif sh.has_text_frame and sh.text_frame.text.strip():
            textboxes += 1; kinds.append("text")
    print(f"  slide {i}: {len(s.shapes)} shapes -> {sorted(set(kinds))}")
print("charts:", charts, "tables:", tables, "textboxes:", textboxes)

# repair-detection proxy: every part must be valid XML and rels must resolve
with zipfile.ZipFile(path) as z:
    bad = z.testzip()
    print("zip integrity:", "OK" if bad is None else f"CORRUPT {bad}")
    xml_parts = [n for n in z.namelist() if n.endswith(".xml") or n.endswith(".rels")]
    import xml.etree.ElementTree as ET
    errs = []
    for n in xml_parts:
        try:
            ET.fromstring(z.read(n))
        except ET.ParseError as e:
            errs.append(f"{n}: {e}")
    print("xml parts:", len(xml_parts), "parse errors:", errs if errs else "none")
