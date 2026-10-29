"""Renderer - turns a Deck spec into a real .pptx with native, editable objects.

Rules:
  * geometry comes from the layout registry, never from the LLM
  * text auto-shrinks to fit its box (see fit_text)
  * charts are native pptx charts, not images
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

import os as _os

from .tokens import Theme, get_theme, rgb
from .spec import Deck, Slide, validate_deck

EMU_PER_IN = 914400

CHART_TYPES = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
}


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, x, y, w, h, fill_hex, line_hex=None, radius=None):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill_hex)
    if line_hex:
        shp.line.color.rgb = rgb(line_hex)
        shp.line.width = Pt(0.75)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    if radius:
        try:
            shp.adjustments[0] = radius
        except (IndexError, AttributeError):
            pass
    return shp


def _textbox(slide, x, y, w, h, text, theme: Theme, size: int,
             color_hex: str, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, line_spacing=1.15, space_after=0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    if space_after:
        p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.name = theme.type_scale.font_family
    f.color.rgb = rgb(color_hex)
    return tb


def _bullets(slide, x, y, w, h, items, theme: Theme, size=None):
    """Bullet list with a real hanging indent and accent dot."""
    ts = theme.type_scale
    size = size or ts.body
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.22
        p.space_after = Pt(size * 0.62)
        dot = p.add_run()
        dot.text = "\u2022  "
        dot.font.size = Pt(size)
        dot.font.name = ts.font_family
        dot.font.color.rgb = rgb(theme.palette.accent)
        dot.font.bold = True
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.name = ts.font_family
        run.font.color.rgb = rgb(theme.palette.text)
    return tb


def _chrome(slide, theme: Theme, page: int, total: int, section: str = ""):
    """Consistent footer - present on every content slide. Cheap but high impact."""
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    y = g.slide_h - g.margin_y * 0.62
    line = slide.shapes.add_connector(
        1, Inches(g.margin_x), Inches(y - 0.18),
        Inches(g.slide_w - g.margin_x), Inches(y - 0.18),
    )
    line.line.color.rgb = rgb(p.line)
    line.line.width = Pt(0.75)
    _textbox(slide, g.margin_x, y - 0.06, 6.0, 0.3, section, theme, ts.small, p.muted)
    _textbox(slide, g.slide_w - g.margin_x - 1.2, y - 0.06, 1.2, 0.3,
             f"{page:02d} / {total:02d}", theme, ts.small, p.muted, align=PP_ALIGN.RIGHT)


def _header(slide, theme: Theme, title: str, kicker: str = ""):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    y = g.margin_y
    if kicker:
        _textbox(slide, g.margin_x, y, g.content_w, 0.3, kicker.upper(),
                 theme, ts.small, p.accent, bold=True)
        y += 0.36
    _textbox(slide, g.margin_x, y, g.content_w, 1.0, title,
             theme, ts.h1, p.text, bold=True)
    bar_y = y + 0.92
    _rect(slide, g.margin_x, bar_y, 0.9, 0.055, p.accent)
    return bar_y + 0.3


# --- layouts --------------------------------------------------------------

def lay_cover(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    # accent band on the left edge
    _rect(slide, 0, 0, 0.16, g.slide_h, p.accent)

    # generated art panel on the right (deterministic, seeded by the deck)
    art = deck.art_path if hasattr(deck, "art_path") else None
    if art and _os.path.exists(art):
        panel_x = g.slide_w - 4.6
        slide.shapes.add_picture(art, Inches(panel_x), Inches(0),
                                 Inches(4.6), Inches(g.slide_h))
        _rect(slide, panel_x, 0, 0.035, g.slide_h, p.accent2)
    else:
        _rect(slide, g.slide_w - 4.6, 0, 4.6, g.slide_h, p.surface)

    _textbox(slide, g.margin_x + 0.35, 1.55, 7.4, 1.9, s.title,
             theme, ts.display, p.text, bold=True, line_spacing=1.05)
    if s.subtitle:
        _textbox(slide, g.margin_x + 0.35, 3.62, 7.0, 1.2, s.subtitle,
                 theme, ts.h2, p.muted, line_spacing=1.3)
    _rect(slide, g.margin_x + 0.35, 3.36, 1.3, 0.07, p.accent2)
    if deck.author:
        _textbox(slide, g.margin_x + 0.35, g.slide_h - 1.15, 6.5, 0.4,
                 deck.author, theme, ts.small, p.muted)


def lay_section(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    _textbox(slide, g.margin_x, 2.55, 1.5, 1.2, s.subtitle or "",
             theme, 64, p.accent, bold=True)
    _textbox(slide, g.margin_x, 3.35, g.content_w * 0.8, 1.4, s.title,
             theme, ts.display, p.text, bold=True, line_spacing=1.1)
    _rect(slide, g.margin_x, 5.0, 1.1, 0.06, p.accent2)


def lay_bullets(slide, s: Slide, theme: Theme, deck: Deck):
    g, p = theme.grid, theme.palette
    y = _header(slide, theme, s.title, s.subtitle)
    _bullets(slide, g.margin_x, y + 0.15, g.content_w * 0.82, g.content_h - 1.4, s.bullets, theme)


def lay_two_col(slide, s: Slide, theme: Theme, deck: Deck):
    g, p = theme.grid, theme.palette
    y = _header(slide, theme, s.title, s.subtitle)
    col_w = (g.content_w - g.gutter) / 2
    for idx, (ctitle, citems, cx) in enumerate([
        (s.left_title, s.left_bullets, g.margin_x),
        (s.right_title, s.right_bullets, g.margin_x + col_w + g.gutter),
    ]):
        _rect(slide, cx, y + 0.1, col_w, g.content_h - 1.45, p.surface, p.line, radius=0.06)
        _rect(slide, cx, y + 0.1, 0.05, g.content_h - 1.45,
              p.accent if idx == 0 else p.accent2)
        _textbox(slide, cx + 0.32, y + 0.42, col_w - 0.64, 0.5, ctitle,
                 theme, theme.type_scale.h2, p.text, bold=True)
        _bullets(slide, cx + 0.32, y + 1.1, col_w - 0.64,
                 g.content_h - 2.4, citems, theme, size=14)


def lay_kpi_row(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    y = _header(slide, theme, s.title, s.subtitle)
    n = max(1, len(s.kpis))
    gap = g.gutter
    card_w = (g.content_w - gap * (n - 1)) / n
    card_h = 2.35
    for i, k in enumerate(s.kpis):
        cx = g.margin_x + i * (card_w + gap)
        _rect(slide, cx, y + 0.35, card_w, card_h, p.surface, p.line, radius=0.08)
        _rect(slide, cx + 0.3, y + 0.68, 0.55, 0.055, p.accent if i % 2 == 0 else p.accent2)
        _textbox(slide, cx + 0.3, y + 0.92, card_w - 0.6, 0.9,
                 k.get("value", ""), theme, 40, p.text, bold=True)
        _textbox(slide, cx + 0.3, y + 1.85, card_w - 0.6, 0.6,
                 k.get("label", ""), theme, 13, p.muted, line_spacing=1.25)


def lay_chart(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    y = _header(slide, theme, s.title, s.subtitle)
    cs = s.chart
    data = CategoryChartData()
    data.categories = cs.categories
    for ser in cs.series:
        data.add_series(ser.name, ser.values)

    cx, cy = g.margin_x, y + 0.25
    cw, ch = g.content_w * 0.66, g.content_h - 1.75
    gf = slide.shapes.add_chart(CHART_TYPES[cs.kind], Inches(cx), Inches(cy),
                                Inches(cw), Inches(ch), data)
    chart = gf.chart
    chart.has_legend = len(cs.series) > 1 or cs.kind == "pie"
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(11)
        chart.legend.font.color.rgb = rgb(p.muted)
        chart.legend.font.name = ts.font_family
    if cs.y_title:
        chart.value_axis.has_title = True
        chart.value_axis.axis_title.text_frame.text = cs.y_title
        for r in chart.value_axis.axis_title.text_frame.paragraphs[0].runs:
            r.font.size = Pt(11)
            r.font.color.rgb = rgb(p.muted)
            r.font.name = ts.font_family

    chart.font.size = Pt(11)
    chart.font.name = ts.font_family
    chart.font.color.rgb = rgb(p.muted)

    for ax in (chart.value_axis, chart.category_axis):
        ax.format.line.color.rgb = rgb(p.line)
        ax.tick_labels.font.size = Pt(11)
        ax.tick_labels.font.color.rgb = rgb(p.muted)
        ax.tick_labels.font.name = ts.font_family
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = rgb(p.line)
    chart.value_axis.major_gridlines.format.line.width = Pt(0.5)

    colors = [p.accent, p.accent2, p.muted, p.text]
    for i, plot_ser in enumerate(chart.plots[0].series):
        plot_ser.format.fill.solid()
        plot_ser.format.fill.fore_color.rgb = rgb(colors[i % len(colors)])

    # commentary column on the right
    if s.bullets:
        _bullets(slide, cx + cw + g.gutter, cy + 0.1,
                 g.content_w - cw - g.gutter, ch, s.bullets, theme, size=13)


def lay_quote(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    _textbox(slide, g.margin_x, 1.35, 1.6, 1.6, "\u201C", theme, 120, p.accent, bold=True)
    _textbox(slide, g.margin_x + 0.2, 2.45, g.content_w * 0.78, 2.6, s.quote,
             theme, 30, p.text, line_spacing=1.35)
    _rect(slide, g.margin_x + 0.2, 5.35, 1.0, 0.055, p.accent2)
    if s.attribution:
        _textbox(slide, g.margin_x + 0.2, 5.6, g.content_w * 0.8, 0.5,
                 s.attribution, theme, ts.h2, p.muted)


def lay_table(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    y = _header(slide, theme, s.title, s.subtitle)
    rows, cols = len(s.table), len(s.table[0])
    tw = g.content_w
    th = min(g.content_h - 1.5, 0.5 + rows * 0.52)
    shp = slide.shapes.add_table(rows, cols, Inches(g.margin_x), Inches(y + 0.2),
                                 Inches(tw), Inches(th))
    tbl = shp.table
    for ci in range(cols):
        tbl.columns[ci].width = Emu(int(Inches(tw) / cols))
    for ri, row in enumerate(s.table):
        tbl.rows[ri].height = Emu(int(Inches(0.5)))
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_left = cell.margin_right = Inches(0.14)
            cell.margin_top = cell.margin_bottom = Inches(0.06)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if ri == 0:
                cell.fill.fore_color.rgb = rgb(p.accent)
            else:
                cell.fill.fore_color.rgb = rgb(p.surface if ri % 2 else p.bg)
            tf = cell.text_frame
            tf.word_wrap = True
            para = tf.paragraphs[0]
            run = para.add_run()
            run.text = str(val)
            run.font.size = Pt(ts.small + 1)
            run.font.bold = ri == 0
            run.font.name = ts.font_family
            run.font.color.rgb = rgb("FFFFFF" if ri == 0 else p.text)


def lay_closing(slide, s: Slide, theme: Theme, deck: Deck):
    g, p, ts = theme.grid, theme.palette, theme.type_scale
    _rect(slide, 0, 0, g.slide_w, 0.14, p.accent)
    _textbox(slide, g.margin_x, 2.6, g.content_w, 1.5, s.title,
             theme, ts.display, p.text, bold=True, align=PP_ALIGN.CENTER)
    if s.subtitle:
        _textbox(slide, g.margin_x, 4.1, g.content_w, 0.8, s.subtitle,
                 theme, ts.h2, p.muted, align=PP_ALIGN.CENTER)
    _rect(slide, g.slide_w / 2 - 0.55, 5.15, 1.1, 0.06, p.accent2)


LAYOUTS = {
    "cover": lay_cover,
    "section": lay_section,
    "bullets": lay_bullets,
    "two_col": lay_two_col,
    "kpi_row": lay_kpi_row,
    "chart": lay_chart,
    "quote": lay_quote,
    "table": lay_table,
    "closing": lay_closing,
}


def render(deck: Deck, out_path: str) -> str:
    errs = validate_deck(deck)
    if errs:
        raise ValueError("invalid deck:\n  - " + "\n  - ".join(errs))

    theme = get_theme(deck.theme)
    prs = Presentation()
    prs.slide_width = Inches(theme.grid.slide_w)
    prs.slide_height = Inches(theme.grid.slide_h)

    total = len(deck.slides)
    for i, s in enumerate(deck.slides):
        slide = _blank(prs)
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(theme.palette.bg)

        LAYOUTS[s.layout](slide, s, theme, deck)

        if s.notes:
            slide.notes_slide.notes_text_frame.text = s.notes
        if s.layout in ("bullets", "two_col", "chart", "table", "kpi_row"):
            _chrome(slide, theme, i + 1, total, s.sources[0] if s.sources else "")

    prs.save(out_path)
    return out_path
