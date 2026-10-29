"""Design token system - the core of perceived quality.
Every visual decision is a variable here. Never hardcode colors/sizes in renderers.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class Palette:
    name: str
    bg: str          # slide background
    surface: str     # card / panel fill
    text: str        # primary text
    muted: str       # secondary text
    accent: str      # brand accent
    accent2: str     # secondary accent (charts)
    line: str        # rules, borders


@dataclass
class TypeScale:
    """Font sizes in points. Ratio-locked so hierarchy never breaks."""
    display: int = 44    # section dividers, cover
    h1: int = 32         # slide title
    h2: int = 22         # subhead
    body: int = 16       # bullets
    small: int = 12      # captions, source lines
    font_family: str = "Inter"


@dataclass
class Grid:
    """Slide is 13.333 x 7.5 in (16:9). Margins define the safe area."""
    margin_x: float = 0.85
    margin_y: float = 0.62
    gutter: float = 0.32
    slide_w: float = 13.333
    slide_h: float = 7.5

    @property
    def content_w(self) -> float:
        return self.slide_w - 2 * self.margin_x

    @property
    def content_h(self) -> float:
        return self.slide_h - 2 * self.margin_y


@dataclass
class Theme:
    palette: Palette
    type_scale: TypeScale = field(default_factory=TypeScale)
    grid: Grid = field(default_factory=Grid)

    def to_dict(self) -> dict:
        return asdict(self)


# --- Shipped themes -------------------------------------------------------

THEMES: Dict[str, Theme] = {
    "midnight": Theme(
        palette=Palette(
            name="midnight",
            bg="0B1020", surface="151C33", text="F5F7FF", muted="8B93B0",
            accent="4F7CFF", accent2="22D3A6", line="26304D",
        ),
    ),
    "paper": Theme(
        palette=Palette(
            name="paper",
            bg="FFFFFF", surface="F4F5F7", text="12141A", muted="6B7280",
            accent="1D4ED8", accent2="E8590C", line="E1E4EA",
        ),
    ),
    "sand": Theme(
        palette=Palette(
            name="sand",
            bg="FBF7F0", surface="F2E9DC", text="2A2118", muted="8A7860",
            accent="B4552D", accent2="4A7C59", line="E0D2BE",
        ),
        type_scale=TypeScale(font_family="Georgia"),
    ),
}


def get_theme(name: str) -> Theme:
    if name not in THEMES:
        raise KeyError(f"unknown theme {name!r}; available: {list(THEMES)}")
    return THEMES[name]


def rgb(hex_str: str):
    """'4F7CFF' -> RGBColor. Accepts optional leading #."""
    from pptx.dml.color import RGBColor
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
