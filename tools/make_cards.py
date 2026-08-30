"""Build the labeling booth: zoomed checkbox cards drawn from the four samples plus synthetic judgment cases.

Card strata (hidden from the labeler, recorded in data/cards/cards.json):
  anchor-filled / anchor-empty   confident detector reads, the happy path
  ambiguous                      detector reads inside the ambiguous band or with a reason code
  hard-real                      the planted cases: faded X, pen loop, tick, watermark, blue cells
  negative                       candidates the size consensus rejected (glyph holes, cells) and known artifacts
  synthetic-*                    judgment classes the samples do not contain: broken or faint or hand-drawn
                                 borders, circled and scribbled-out and partial marks, handwriting across an
                                 empty box, heavy JPEG and blur, rotation, radio circles and signature cells

Seeded; regenerates byte-identically.
"""

from __future__ import annotations

import base64
import json
import random
from pathlib import Path

import cv2
import numpy as np

from hv_checkbox.detect import detect_boxes
from hv_checkbox.normalize import load_page
from hv_checkbox.classify import classify
from hv_checkbox.types import Box

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
OUT_DIR = ROOT / "data" / "cards"
SEED = 7

# Planted hard cases, located by the nearest candidate to these points (source, x, y)
HARD_POINTS = {
    "sample_1.jpg": [
        (209, 627, "faded X, Electricity Public"),
        (287, 627, "tick, Electricity Other"),
        (731, 505, "pen loop through No Zoning"),
        (466, 688, "FEMA No, X exits the border"),
        (352, 505, "Legal Nonconforming, faint left border"),
        (295, 199, "Neighborhood Boundaries artifact square"),
    ],
    "sample_7.png": [
        (1518, 1396, "Over 6 mths under the watermark"),
        (1518, 1352, "Over Supply under the watermark"),
        (1518, 1310, "Declining under the watermark"),
        (1127, 1975, "Water box, thick X"),
    ],
    "sample_5.png": [
        (1800, 928, "Declining X inside a blue cell"),
        (1800, 979, "Declining X inside a blue cell, row 2"),
        (2272, 928, "Increasing empty inside a blue cell"),
        (2272, 1178, "Declining empty in blue row"),
    ],
}


def encode_png(img: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def crop_card(image: np.ndarray, box: Box, side: int) -> np.ndarray:
    """Crop the box with one box-width of context on each side, scale so the box is ~140 px, outline it."""
    pad = int(side * 1.1)
    x1, y1 = max(0, box.x1 - pad), max(0, box.y1 - pad)
    x2, y2 = min(image.shape[1], box.x2 + pad), min(image.shape[0], box.y2 + pad)
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        crop = np.full((40, 40, 3), 255, np.uint8)
    scale = max(2.0, min(6.0, 140.0 / max(1, box.w, box.h)))
    crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    bx1, by1 = int((box.x1 - x1) * scale) - 5, int((box.y1 - y1) * scale) - 5
    bx2, by2 = int((box.x2 - x1) * scale) + 5, int((box.y2 - y1) * scale) + 5
    cv2.rectangle(crop, (bx1, by1), (bx2, by2), (255, 0, 255), 2)
    return crop


def nearest(cands: list[Box], x: int, y: int, side: int) -> Box:
    best = min(cands, key=lambda b: abs(b.cx - x) + abs(b.cy - y), default=None)
    if best is None or abs(best.cx - x) + abs(best.cy - y) > side * 1.5:
        h = side // 2
        return Box(x - h, y - h, x + h, y + h, witnesses=["manual"])
    return best


def synthetic_cards(rng: random.Random) -> list[dict]:
    """Judgment classes built from a clean rendered box (sample_2) and a blank canvas."""
    img = cv2.imread(str(SAMPLES / "sample_2.png"))
    page = load_page(img)
    boxes = [classify(page, b) for b in detect_boxes(page)]
    empties = [b for b in boxes if b.ink < 0.01]
    filled = [b for b in boxes if b.ink > 0.15]
    side = page.box_side
    out = []

    def base(box: Box) -> np.ndarray:
        pad = int(side * 1.1)
        return img[box.y1 - pad : box.y2 + pad, box.x1 - pad : box.x2 + pad].copy(), pad

    def finish(tile: np.ndarray, pad: int, box_wh: tuple[int, int], kind: str, note: str):
        w, h = box_wh
        scale = max(2.0, min(6.0, 140.0 / max(w, h)))
        big = cv2.resize(tile, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        cv2.rectangle(big, (int(pad * scale) - 5, int(pad * scale) - 5), (int((pad + w) * scale) + 5, int((pad + h) * scale) + 5), (255, 0, 255), 2)
        out.append({"source": "synthetic", "bbox": [0, 0, w, h], "stratum": "synthetic-" + kind, "note": note, "png": encode_png(big)})

    def stroke(tile, pts, thick=3, colour=(20, 20, 20)):
        for a, b in zip(pts[:-1], pts[1:]):
            cv2.line(tile, a, b, colour, thick, cv2.LINE_AA)

    for _ in range(3):
        b = rng.choice(empties)
        t, pad = base(b)
        w, h = b.w, b.h
        # circle mark instead of an X
        cv2.circle(t, (pad + w // 2, pad + h // 2), int(min(w, h) * 0.32), (30, 30, 30), 3, cv2.LINE_AA)
        finish(t, pad, (w, h), "circle-mark", "circle drawn inside the box")
    for _ in range(3):
        b = rng.choice(empties)
        t, pad = base(b)
        w, h = b.w, b.h
        # single diagonal stroke only (a partial X)
        stroke(t, [(pad + 4, pad + 4), (pad + w - 4, pad + h - 4)], 3)
        finish(t, pad, (w, h), "partial-mark", "one diagonal stroke")
    for _ in range(3):
        b = rng.choice(filled)
        t, pad = base(b)
        w, h = b.w, b.h
        # scribbled out: dense back-and-forth over the X
        pts = [(pad + rng.randint(2, w - 2), pad + rng.randint(2, h - 2)) for _ in range(14)]
        stroke(t, pts, 3)
        finish(t, pad, (w, h), "scribbled-out", "an X then dense scribble over it")
    for _ in range(3):
        b = rng.choice(empties)
        t, pad = base(b)
        w, h = b.w, b.h
        # handwriting stroke crossing an empty box
        y0 = pad + rng.randint(h // 3, 2 * h // 3)
        stroke(t, [(0, y0 + rng.randint(-6, 6)), (pad + w // 2, y0), (t.shape[1] - 1, y0 + rng.randint(-8, 8))], 3, (40, 40, 60))
        finish(t, pad, (w, h), "stray-stroke", "handwriting passes through an empty box")
    for _ in range(3):
        b = rng.choice(rng.choice([empties, filled]))
        t, pad = base(b)
        w, h = b.w, b.h
        # broken border: erase a segment of the top and right border
        cv2.rectangle(t, (pad + w // 4, pad - 2), (pad + 3 * w // 4, pad + 3), (255, 255, 255), -1)
        cv2.rectangle(t, (pad + w - 3, pad + h // 4), (pad + w + 2, pad + 3 * h // 4), (255, 255, 255), -1)
        finish(t, pad, (w, h), "broken-border", "two border segments missing")
    for _ in range(3):
        b = rng.choice(rng.choice([empties, filled]))
        t, pad = base(b)
        w, h = b.w, b.h
        # faint: blend toward white
        t = cv2.addWeighted(t, 0.35, np.full_like(t, 255), 0.65, 0)
        finish(t, pad, (w, h), "faint", "faded to 35% ink")
    for _ in range(3):
        b = rng.choice(rng.choice([empties, filled]))
        t, pad = base(b)
        w, h = b.w, b.h
        # heavy JPEG + blur
        t = cv2.GaussianBlur(t, (0, 0), 1.6)
        ok, buf = cv2.imencode(".jpg", t, [cv2.IMWRITE_JPEG_QUALITY, 22])
        t = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        finish(t, pad, (w, h), "degraded", "blur then JPEG quality 22")
    for _ in range(2):
        b = rng.choice(rng.choice([empties, filled]))
        t, pad = base(b)
        w, h = b.w, b.h
        m = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), rng.choice([-4, 4]), 1.0)
        t = cv2.warpAffine(t, m, (t.shape[1], t.shape[0]), borderValue=(255, 255, 255))
        finish(t, pad, (w, h), "rotated", "rotated 4 degrees")
    for _ in range(2):
        # hand-drawn wobbly box, no printed border
        w = h = side
        pad = int(side * 1.1)
        t = np.full((h + 2 * pad, w + 2 * pad, 3), 255, np.uint8)
        pts = [(pad + rng.randint(-3, 3), pad + rng.randint(-3, 3)), (pad + w + rng.randint(-3, 3), pad + rng.randint(-3, 3)),
               (pad + w + rng.randint(-3, 3), pad + h + rng.randint(-3, 3)), (pad + rng.randint(-3, 3), pad + h + rng.randint(-3, 3))]
        stroke(t, pts + [pts[0]], 2)
        if rng.random() < 0.5:
            stroke(t, [(pad + 5, pad + 5), (pad + w - 5, pad + h - 5)], 3)
            stroke(t, [(pad + w - 5, pad + 5), (pad + 5, pad + h - 5)], 3)
        finish(t, pad, (w, h), "hand-drawn", "box drawn by hand, no printed border")
    for _ in range(2):
        # radio-style circle, not a square box
        w = h = side
        pad = int(side * 1.1)
        t = np.full((h + 2 * pad, w + 2 * pad, 3), 255, np.uint8)
        cv2.circle(t, (pad + w // 2, pad + h // 2), w // 2, (0, 0, 0), 2, cv2.LINE_AA)
        if rng.random() < 0.5:
            cv2.circle(t, (pad + w // 2, pad + h // 2), w // 5, (0, 0, 0), -1, cv2.LINE_AA)
        finish(t, pad, (w, h), "radio-circle", "a radio circle, not a square")
    return out


def main() -> None:
    rng = random.Random(SEED)
    cards: list[dict] = []
    for name in ["sample_1.jpg", "sample_2.png", "sample_5.png", "sample_7.png"]:
        img = cv2.imread(str(SAMPLES / name))
        page = load_page(img)
        kept = [classify(page, b) for b in detect_boxes(page)]
        rejected = [b for b in detect_boxes(page, consensus=10.0) if all(abs(b.cx - k.cx) + abs(b.cy - k.cy) > 4 for k in kept)]
        side = page.box_side
        used: list[Box] = []

        def add(box: Box, stratum: str, note: str = ""):
            if any(abs(box.cx - u.cx) + abs(box.cy - u.cy) < 4 for u in used):
                return
            used.append(box)
            cards.append({"source": name, "bbox": box.bbox, "stratum": stratum, "note": note, "detector_ink": box.ink,
                          "png": encode_png(crop_card(img, box, side))})

        for x, y, note in HARD_POINTS.get(name, []):
            add(nearest(kept + rejected, x, y, side), "hard-real", note)
        for b in [b for b in kept if b.reasons or 0.03 < b.ink < 0.35][:4]:
            add(b, "ambiguous")
        filled_pool = [b for b in kept if b.ink > 0.35 and not b.reasons]
        for b in rng.sample(filled_pool, k=min(4, len(filled_pool))):
            add(b, "anchor-filled")
        empty_pool = [b for b in kept if b.ink < 0.02 and not b.reasons]
        for b in rng.sample(empty_pool, k=min(4, len(empty_pool))):
            add(b, "anchor-empty")
        for b in rng.sample(rejected, k=min(3, len(rejected))):
            b.ink = 0.0
            add(b, "negative", "rejected by size consensus")

    cards += synthetic_cards(rng)
    rng.shuffle(cards)
    for i, c in enumerate(cards, 1):
        c["id"] = f"c{i:03d}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = [{k: v for k, v in c.items() if k != "png"} for c in cards]
    (OUT_DIR / "cards.json").write_text(json.dumps(meta, indent=1))
    slim = [{"id": c["id"], "source": c["source"], "bbox": c["bbox"], "png": c["png"]} for c in cards]
    html = (ROOT / "labeling" / "booth_template.html").read_text().replace("__CARDS__", json.dumps(slim).replace("</", "<\\/"))
    (ROOT / "labeling" / "labeling-booth.html").write_text(html)
    strata: dict[str, int] = {}
    for c in cards:
        strata[c["stratum"]] = strata.get(c["stratum"], 0) + 1
    print(len(cards), "cards ->", ROOT / "labeling" / "labeling-booth.html")
    for k, v in sorted(strata.items()):
        print(f"  {k:22s} {v}")


if __name__ == "__main__":
    main()
