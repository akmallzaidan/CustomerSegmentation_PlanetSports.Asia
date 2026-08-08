"""Generate assets/logo.png — a compact navy brand badge for the sidebar.

Run once (or whenever you want to regenerate the logo):
    python scripts/make_logo.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "assets", "logo.png")

W, H = 560, 150
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)


def rounded(xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


# Badge with a simple vertical gradient (navy -> accent).
badge = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
bd = ImageDraw.Draw(badge)
for y in range(120):
    t = y / 120
    r = int(46 + (56 - 46) * t)
    g = int(110 + (189 - 110) * t)
    b = int(247 + (248 - 247) * t)
    bd.line([(0, y), (120, y)], fill=(r, g, b, 255))
mask = Image.new("L", (120, 120), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, 119, 119], radius=30, fill=255)
img.paste(badge, (16, 15), mask)


def load_font(size, bold=True):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# "PS" monogram inside the badge.
draw.text((44, 40), "PS", font=load_font(52), fill=(255, 255, 255, 255))

# Wordmark.
draw.text((156, 34), "PlanetSports", font=load_font(40), fill=(248, 250, 252, 255))
draw.text((158, 82), "SEGMENTATION AI", font=load_font(22, bold=False), fill=(56, 189, 248, 255))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print(f"Wrote {OUT}")
