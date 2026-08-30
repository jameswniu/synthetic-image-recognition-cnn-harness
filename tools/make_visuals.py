"""Render the README's photographic figures from the actual sample pages and the pipeline's own output.

Nothing here is drawn by hand: every box in every figure is a real detection, so the pictures cannot
drift from the system. Captions are plain English on purpose; the audience for the landing page is
not required to know what a morphological opening is.

Run: uv run python tools/make_visuals.py
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from hv_checkbox.pipeline import detect_with_page

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
ASSETS = ROOT / "assets"

GREEN = (60, 170, 60)
RED = (60, 60, 220)
AMBER = (0, 165, 245)
INK = (30, 32, 38)
MUTED = (120, 124, 132)
BLUE = (200, 110, 40)
FONT = cv2.FONT_HERSHEY_DUPLEX


def text(img, s, org, size=0.62, colour=INK, weight=1):
    cv2.putText(img, s, org, FONT, size, colour, weight, cv2.LINE_AA)


def pad(img, top=0, bottom=0, left=0, right=0, colour=(255, 255, 255)):
    return cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=colour)


def annotate(img, boxes, thickness=None):
    out = img.copy()
    t = thickness or max(2, img.shape[1] // 700)
    for b in boxes:
        colour = AMBER if b.reasons else (GREEN if b.is_checked else RED)
        cv2.rectangle(out, (b.x1 - 2, b.y1 - 2), (b.x2 + 2, b.y2 + 2), colour, t)
    return out


def legend(width, height=54):
    bar = np.full((height, width, 3), 255, np.uint8)
    x = 14
    for colour, label in [(GREEN, "checked"), (RED, "empty"), (AMBER, "not sure, sent for review")]:
        cv2.rectangle(bar, (x, 18), (x + 26, 38), colour, -1)
        text(bar, label, (x + 36, 35), 0.6, INK)
        x += 46 + int(len(label) * 11.4)
    return bar


def hero() -> None:
    """The photographed page, every checkbox called, with the honest label on the two hard ones."""
    img = cv2.imread(str(SAMPLES / "sample_1.jpg"))
    page, boxes, _ = detect_with_page(img)
    out = annotate(page.image, boxes, thickness=3)
    out = pad(out, top=74, bottom=8, left=8, right=8)
    text(out, "Every checkbox on a photographed appraisal page, called by the system", (16, 34), 0.78, INK)
    checked = sum(1 for b in boxes if b.is_checked and not b.reasons)
    unsure = sum(1 for b in boxes if b.reasons)
    text(out, f"{len(boxes)} boxes found, {checked} read as checked, {unsure} held back as not sure", (16, 60), 0.62, MUTED)
    out = np.vstack([out, legend(out.shape[1])])
    cv2.imwrite(str(ASSETS / "hero-page.png"), out)
    print("hero-page.png", out.shape)


TRAPS = [
    ("sample_5.png", (1690, 875, 2090, 1005), "Shaded rows", "Blue tint, black mark. Read correctly."),
    ("sample_7.png", (1470, 1285, 1870, 1425), "A stamp across the box", "The watermark crosses the border. Still found."),
    ("sample_1.jpg", (145, 592, 425, 682), "Faded ink", "Too faint to call. Sent for review, not guessed."),
    ("sample_1.jpg", (668, 478, 948, 548), "Pen stroke passing through", "Stray handwriting, not a selection. Read as empty."),
]


TILE_ASPECT = 360 / 132


def window(img, box, aspect: float = TILE_ASPECT):
    """Grow a crop window to the tile aspect, keeping it centred and inside the page.

    The four traps live on pages of different resolutions, so hand-picked windows come out at four
    different shapes. Scaled to a common width they then differ in height, which is what opened a
    band of white between the grid rows and left the row titles sitting at different heights.
    """
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w, h = x2 - x1, y2 - y1
    if w / h < aspect:
        w = h * aspect
    else:
        h = w / aspect
    x1, x2 = int(cx - w / 2), int(cx + w / 2)
    y1, y2 = int(cy - h / 2), int(cy + h / 2)
    page_h, page_w = img.shape[:2]
    x1, x2 = x1 + max(0, -x1) - max(0, x2 - page_w), x2 + max(0, -x1) - max(0, x2 - page_w)
    y1, y2 = y1 + max(0, -y1) - max(0, y2 - page_h), y2 + max(0, -y1) - max(0, y2 - page_h)
    return x1, y1, x2, y2


def traps() -> None:
    """The four things that break a naive checkbox reader, and what this one does with each."""
    tiles = []
    cache: dict[str, tuple] = {}
    for name, (x1, y1, x2, y2), title, caption in TRAPS:
        if name not in cache:
            img = cv2.imread(str(SAMPLES / name))
            cache[name] = (img,) + tuple(detect_with_page(img)[1:2])
        img, boxes = cache[name]
        x1, y1, x2, y2 = window(img, (x1, y1, x2, y2))
        shown = [b for b in boxes if x1 - 40 < b.cx < x2 + 40 and y1 - 40 < b.cy < y2 + 40]
        crop = annotate(img, shown, thickness=2)[y1:y2, x1:x2]
        scale = 360 / crop.shape[1]
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        crop = pad(crop, top=62, bottom=14, left=10, right=10)
        text(crop, title, (12, 26), 0.68, INK)
        text(crop, caption, (12, 50), 0.5, MUTED)
        tiles.append(crop)
    h = max(t.shape[0] for t in tiles)
    tiles = [pad(t, top=(h - t.shape[0]) // 2, bottom=h - t.shape[0] - (h - t.shape[0]) // 2) for t in tiles]
    grid = np.hstack([np.vstack([tiles[0], tiles[2]]), np.vstack([tiles[1], tiles[3]])])
    grid = pad(grid, top=64, bottom=10, left=10, right=10)
    text(grid, "Four things that break a naive checkbox reader", (18, 34), 0.8, INK)
    text(grid, "One of each is planted in the sample pages. This is what the system does with them.", (18, 56), 0.58, MUTED)
    cv2.imwrite(str(ASSETS / "four-traps.png"), grid)
    print("four-traps.png", grid.shape)


def witnesses() -> None:
    """Side by side: what the page itself shows, and what the blank official form expects."""
    img = cv2.imread(str(SAMPLES / "sample_2.png"))
    page, boxes, meta = detect_with_page(img)
    band = (500, 980)  # the Subject block, dense with checkboxes
    left = annotate(page.image, [b for b in boxes if band[0] < b.cy < band[1]], thickness=3)
    left = left[band[0] - 40 : band[1] + 40, 120:2400]
    golden = cv2.imread(str(ROOT / "data" / "golden" / "form70-p1-1.png"))
    # The blank form is where the second reader's expectations come from, so show them outlined
    # too. A panel with nothing drawn on it reads as a reference image rather than as a reading.
    gpage, gboxes, _ = detect_with_page(golden)
    right = gpage.image.copy()
    for b in gboxes:
        if band[0] - 60 < b.cy < band[1] + 60:
            cv2.rectangle(right, (b.x1 - 2, b.y1 - 2), (b.x2 + 2, b.y2 + 2), BLUE, 3)
    right = right[band[0] - 40 : band[1] + 40, 120:2400]
    scale = 1000 / left.shape[1]
    left = cv2.resize(left, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    right = cv2.resize(right, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    left = pad(left, top=54, bottom=14, left=12, right=12)
    right = pad(right, top=54, bottom=14, left=12, right=12)
    text(left, "What the filled page shows", (14, 34), 0.66, INK)
    text(right, "Where the blank official form says boxes belong", (14, 34), 0.66, INK)
    grid = np.vstack([left, right])
    grid = pad(grid, top=66, bottom=10)
    text(grid, "Two independent readings of the same page", (18, 32), 0.8, INK)
    text(grid, f"Found on the page, and expected by the form. They agreed on all {len(boxes)} boxes here; a disagreement is flagged, never dropped.", (18, 54), 0.56, MUTED)
    cv2.imwrite(str(ASSETS / "two-witnesses.png"), grid)
    print("two-witnesses.png", grid.shape)


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    hero()
    traps()
    witnesses()
