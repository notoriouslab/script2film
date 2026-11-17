"""Makes the share-preview image docs/site/og.jpg (1200×630), used by every page's og:image.

  python3 tools/site/make_og.py [--font path/to/NotoSansTC-Variable.ttf]

Run it only when the image should change; it is not part of the regular site build (build_en.py). The background is
docs/site/hero-poster.jpg, cropped to 1200×630, blurred and darkened toward the site's dark background; on top,
"Script2Film" in large type (the "2" in the site's gold, as in the page header) and the English home page's subtitle below it.
The font is Noto Sans TC from assets/fonts/ (see docs/INSTALL.md); it is read, not copied. Same input, same output.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()

import argparse, pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from site_config import OG_IMAGE, OG_IMAGE_SIZE  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "site" / "hero-poster.jpg"
DST = ROOT / "docs" / OG_IMAGE
SUBTITLE = "A video and explainer toolkit for AI agents"   # docs/en/index.html, the hero's <p class="sub">
BG = (20, 24, 31)        # site.css dark --bg  #14181f
FG = (236, 231, 216)     # site.css dark --fg  #ece7d8
GOLD = (216, 185, 94)    # site.css dark --gold #d8b95e
MUTED = (200, 204, 212)


def font(path, size, weight):
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_axes([weight])
    return f


def make(font_path):
    W, H = OG_IMAGE_SIZE
    im = Image.open(SRC).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    # soften and darken so the frame's own lettering does not compete: blur, then a veil that is
    # heaviest on the left (where the text sits) and over the top half
    im = im.filter(ImageFilter.GaussianBlur(5))
    veil = Image.new("RGB", (W, H), BG)
    mask = Image.new("L", (W, H))
    mask.putdata([min(240, round(175 + 55 * max(0.0, 1 - i / (W * 0.85)) + 30 * max(0.0, 1 - j / (H * 0.55))))
                  for j in range(H) for i in range(W)])
    im = Image.composite(veil, im, mask)
    d = ImageDraw.Draw(im)
    big, sub = font(font_path, 132, 800), font(font_path, 44, 500)
    left, base = 80, 330
    parts = [("Script", FG), ("2", GOLD), ("Film", FG)]
    cx = left
    for text, col in parts:
        d.text((cx, base), text, font=big, fill=col, anchor="ls")
        cx += d.textlength(text, font=big)
    d.rectangle((left, base + 34, left + 120, base + 40), fill=GOLD)
    d.text((left, base + 110), SUBTITLE, font=sub, fill=MUTED, anchor="ls")
    assert cx < W - 40 and left + d.textlength(SUBTITLE, font=sub) < W - 40, "text runs off the image"
    DST.parent.mkdir(parents=True, exist_ok=True)
    im.save(DST, "JPEG", quality=85, optimize=True)
    return DST


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", default=str(ROOT / "assets" / "fonts" / "NotoSansTC-Variable.ttf"))
    out = make(ap.parse_args().font)
    print(f"{out.relative_to(ROOT)}: {Image.open(out).size}, {out.stat().st_size // 1024} KB")
