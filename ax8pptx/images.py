"""Image generation for cover and section art.

Two backends:
  * local  - deterministic generative gradient art (no network, no key)
  * remote - any OpenAI-compatible images endpoint, if a key is present

Local is the default so a deck never fails for lack of a key, and the
output is reproducible for visual regression.
"""

import hashlib
import math
import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter


def _palette_from(seed: str, accent: str, accent2: str, bg: str):
    def rgb(h):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return rgb(bg), rgb(accent), rgb(accent2)


def gradient_art(seed: str, accent: str, accent2: str, bg: str,
                 size=(1600, 900)) -> Image.Image:
    """Deterministic abstract art: diagonal gradient + seeded soft blobs."""
    w, h = size
    bg_rgb, a1, a2 = _palette_from(seed, accent, accent2, bg)
    img = Image.new("RGB", size, bg_rgb)
    px = img.load()

    # diagonal base gradient between the two accents, heavily mixed toward bg
    for y in range(h):
        for x in range(0, w, 2):
            t = (x / w) * 0.62 + (y / h) * 0.38
            c = tuple(int(bg_rgb[i] + (a1[i] - bg_rgb[i]) * t * 0.55) for i in range(3))
            px[x, y] = c
            if x + 1 < w:
                px[x + 1, y] = c

    # seeded blobs
    digest = hashlib.sha256(seed.encode()).digest()
    layer = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(7):
        cx = int(digest[(i * 3) % 32] / 255 * w)
        cy = int(digest[(i * 3 + 1) % 32] / 255 * h)
        r = int((digest[(i * 3 + 2) % 32] / 255) * (w * 0.34) + w * 0.12)
        col = a2 if i % 2 else a1
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=w * 0.07))
    img = Image.blend(img, layer, alpha=0.30)

    # subtle vignette so text stays legible
    vig = Image.new("L", size, 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-w * 0.3, -h * 0.4, w * 1.3, h * 1.4], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(radius=w * 0.12))
    dark = Image.new("RGB", size, bg_rgb)
    img = Image.composite(img, dark, vig)
    return img


def make_cover_art(out_path: str, seed: str, accent: str, accent2: str,
                   bg: str, size=(1600, 900)) -> str:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    gradient_art(seed, accent, accent2, bg, size).save(out_path, quality=92)
    return out_path


def remote_art(prompt: str, out_path: str, api_key: Optional[str] = None,
               endpoint: str = "https://api.openai.com/v1/images/generations",
               model: str = "gpt-image-1") -> str:
    """Optional: any OpenAI-compatible image endpoint."""
    import base64, json, urllib.request
    key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no OPENAI_API_KEY for remote image generation")
    body = json.dumps({"model": model, "prompt": prompt, "size": "1536x1024"}).encode()
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        payload = json.loads(r.read().decode())
    b64 = payload["data"][0]["b64_json"]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return out_path
