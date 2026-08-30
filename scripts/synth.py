"""Policy-driven synthetic page generator.

Takes a blank golden form render (every checkbox known and unfilled), draws selection marks whose
shapes come from the labeling policy (X thin and thick, off-center and overshooting, ticks, solid
fills, partial strokes, circles, scribbles, an occasional blue pen), then degrades the page the way
real appraisal uploads degrade (rotation, scale, JPEG, blur, noise, lighting gradient, colored
watermark text, stray pen lines, shaded bands). Ground truth transforms with the geometry, so every
generated page carries exact labels at zero labeling cost.

Pure code, seeded, no LLM: `synth.py --seed 11` regenerates the set byte-identically, which is a
tier-1 gate. Marks land only inside known boxes; stray pen lines are labeled as nothing at all,
which is the point of them.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import zlib
from pathlib import Path

import cv2
import numpy as np

from hv_checkbox.pipeline import detect_checkboxes

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden"
OUT = ROOT / "data" / "synth"

MARKS = ["x_thin", "x_thick", "x_overshoot", "tick", "solid", "partial", "circle", "scribble"]
MARK_WEIGHTS = [30, 20, 10, 12, 8, 8, 6, 6]


def golden_boxes(render: Path) -> list[list[int]]:
    """Box coordinates for a golden render, extracted once by the detector and cached beside it."""
    cache = render.with_suffix(".boxes.json")
    if cache.exists():
        return json.loads(cache.read_text())["boxes"]
    boxes = [b.bbox for b in detect_checkboxes(cv2.imread(str(render)))]
    cache.write_text(json.dumps({"source": render.name, "boxes": boxes}, indent=1))
    return boxes


def _pen(rng: random.Random) -> tuple[int, int, int]:
    if rng.random() < 0.15:
        return (150, 70, 30)  # blue ballpoint
    g = rng.randint(15, 60)
    return (g, g, g)


def draw_mark(img: np.ndarray, bbox: list[int], kind: str, rng: random.Random) -> None:
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    side = max(w, h)
    t = max(2, int(side * rng.uniform(0.06, 0.14)))
    col = _pen(rng)
    j = lambda: rng.randint(-max(1, side // 10), max(1, side // 10))  # noqa: E731

    def line(a, b):
        cv2.line(img, a, b, col, t, cv2.LINE_AA)

    if kind.startswith("x_"):
        over = int(side * (0.25 if kind == "x_overshoot" else 0.02))
        tt = max(2, int(side * (0.16 if kind == "x_thick" else 0.08)))
        for (ax, ay), (bx, by) in [((x1 - over, y1 - over), (x2 + over, y2 + over)), ((x2 + over, y1 - over), (x1 - over, y2 + over))]:
            cv2.line(img, (ax + j(), ay + j()), (bx + j(), by + j()), col, tt, cv2.LINE_AA)
    elif kind == "tick":
        line((x1 + int(w * 0.18) + j(), y1 + int(h * 0.55) + j()), (x1 + int(w * 0.42), y1 + int(h * 0.8)))
        line((x1 + int(w * 0.42), y1 + int(h * 0.8)), (x2 + int(w * 0.1) + j(), y1 + int(h * 0.1) + j()))
    elif kind == "solid":
        m = int(side * 0.18)
        cv2.rectangle(img, (x1 + m + j() // 2, y1 + m + j() // 2), (x2 - m, y2 - m), col, -1)
    elif kind == "partial":
        line((x1 + j(), y1 + j()), (x2 + j(), y2 + j()))
    elif kind == "circle":
        cv2.circle(img, ((x1 + x2) // 2 + j(), (y1 + y2) // 2 + j()), int(side * 0.32), col, max(2, t - 1), cv2.LINE_AA)
    elif kind == "scribble":
        pts = [(rng.randint(x1, x2), rng.randint(y1, y2)) for _ in range(rng.randint(8, 14))]
        for a, b in zip(pts[:-1], pts[1:]):
            line(a, b)


def add_pen_lines(img: np.ndarray, rng: random.Random, n: int) -> None:
    h, w = img.shape[:2]
    for _ in range(n):
        col = _pen(rng)
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        pts = [(x, y)]
        for _ in range(rng.randint(3, 6)):
            x = int(np.clip(x + rng.randint(-w // 4, w // 4), 0, w - 1))
            y = int(np.clip(y + rng.randint(-h // 10, h // 10), 0, h - 1))
            pts.append((x, y))
        for a, b in zip(pts[:-1], pts[1:]):
            cv2.line(img, a, b, col, rng.randint(3, 5), cv2.LINE_AA)


def add_watermark(img: np.ndarray, rng: random.Random, text: str = "SYNTHETIC SAMPLE COPY") -> None:
    h, w = img.shape[:2]
    layer = np.zeros((h, w), np.uint8)
    scale = w / 500.0
    cv2.putText(layer, text, (int(w * 0.05), int(h * 0.6)), cv2.FONT_HERSHEY_SIMPLEX, scale, 255, max(4, int(scale * 4)), cv2.LINE_AA)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), rng.choice([30, 40, 50]), 1.0)
    layer = cv2.warpAffine(layer, m, (w, h))
    mask = layer > 0
    red = np.array([70, 70, 230], dtype=np.float64)
    img[mask] = (0.45 * img[mask] + 0.55 * red).astype(np.uint8)


def add_shading(img: np.ndarray, rng: random.Random, bands: int) -> None:
    h, w = img.shape[:2]
    tint = np.array([1.0, 0.86, 0.72])  # multiplicative light blue, black ink stays black
    for _ in range(bands):
        y = rng.randint(0, h - h // 10)
        bh = rng.randint(h // 40, h // 12)
        img[y : y + bh] = (img[y : y + bh] * tint).astype(np.uint8)


def rotate(img: np.ndarray, boxes: list[list[int]], deg: float) -> tuple[np.ndarray, list[list[int]]]:
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0)
    out = cv2.warpAffine(img, m, (w, h), borderValue=(255, 255, 255))
    nb = []
    for x1, y1, x2, y2 in boxes:
        pts = np.array([[x1, y1, 1], [x2, y1, 1], [x2, y2, 1], [x1, y2, 1]], dtype=np.float64) @ m.T
        nb.append([int(pts[:, 0].min()), int(pts[:, 1].min()), int(math.ceil(pts[:, 0].max())), int(math.ceil(pts[:, 1].max()))])
    return out, nb


def scale(img: np.ndarray, boxes: list[list[int]], f: float) -> tuple[np.ndarray, list[list[int]]]:
    out = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    return out, [[int(x1 * f), int(y1 * f), int(x2 * f), int(y2 * f)] for x1, y1, x2, y2 in boxes]


def jpeg(img: np.ndarray, q: int) -> np.ndarray:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def make_page(render: Path, rng: random.Random, fill_frac: float = 0.35) -> tuple[np.ndarray, list[dict]]:
    img = cv2.imread(str(render)).copy()
    boxes = golden_boxes(render)
    labels = []
    for bbox in boxes:
        if rng.random() < fill_frac:
            kind = rng.choices(MARKS, MARK_WEIGHTS)[0]
            draw_mark(img, bbox, kind, rng)
            labels.append({"bbox": bbox, "is_checked": True, "ignore": False, "note": kind})
        else:
            labels.append({"bbox": bbox, "is_checked": False, "ignore": False, "note": ""})
    return img, labels


def save(img: np.ndarray, labels: list[dict], name: str, out_dir: Path, params: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / f"{name}.png"), img)
    (out_dir / f"{name}.json").write_text(json.dumps({"source": f"{name}.png", "params": params, "boxes": labels}, indent=1))
    return {"name": name, **params}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--mixed", type=int, default=12, help="random-combination pages per golden form")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    renders = sorted(GOLDEN.glob("*.png"))
    if not renders:
        raise SystemExit("no golden renders in data/golden; run the golden-form step first")
    rng = random.Random(args.seed)
    manifest = []

    # sweeps: one factor at a time, same marks per form, so a metric drop names its cause
    for render in renders:
        stem = render.stem
        base_rng = random.Random(args.seed * 7919 + zlib.crc32(stem.encode()) % 1000)  # crc32: hash() is salted per process
        img, labels = make_page(render, base_rng)
        manifest.append(save(img, labels, f"{stem}-base", out / "sweep", {"form": stem, "factor": "base", "level": 0}))
        for deg in [1, 2, 3, 5]:
            i2, b2 = rotate(img.copy(), [l["bbox"] for l in labels], deg)
            lab = [dict(l, bbox=b) for l, b in zip(labels, b2)]
            manifest.append(save(i2, lab, f"{stem}-rot{deg}", out / "sweep", {"form": stem, "factor": "rotation", "level": deg}))
        for f in [0.75, 0.5, 0.4]:
            i2, b2 = scale(img.copy(), [l["bbox"] for l in labels], f)
            lab = [dict(l, bbox=b) for l, b in zip(labels, b2)]
            manifest.append(save(i2, lab, f"{stem}-scale{int(f*100)}", out / "sweep", {"form": stem, "factor": "scale", "level": f}))
        for q in [60, 35, 22]:
            manifest.append(save(jpeg(img.copy(), q), labels, f"{stem}-jpeg{q}", out / "sweep", {"form": stem, "factor": "jpeg", "level": q}))
        i2 = img.copy()
        add_watermark(i2, random.Random(args.seed + 1))
        manifest.append(save(i2, labels, f"{stem}-watermark", out / "sweep", {"form": stem, "factor": "watermark", "level": 1}))
        i2 = img.copy()
        add_pen_lines(i2, random.Random(args.seed + 2), 4)
        manifest.append(save(i2, labels, f"{stem}-pen", out / "sweep", {"form": stem, "factor": "pen", "level": 4}))
        i2 = img.copy()
        add_shading(i2, random.Random(args.seed + 3), 3)
        manifest.append(save(i2, labels, f"{stem}-shading", out / "sweep", {"form": stem, "factor": "shading", "level": 3}))

    # mixed set: random combinations, the training pool for the patch classifier
    for render in renders:
        for k in range(args.mixed):
            r = random.Random(args.seed * 104729 + k * 31 + zlib.crc32(render.stem.encode()) % 997)
            img, labels = make_page(render, r, fill_frac=r.uniform(0.2, 0.5))
            params: dict = {"form": render.stem, "factor": "mixed", "level": k}
            if r.random() < 0.5:
                add_shading(img, r, r.randint(1, 3))
            if r.random() < 0.4:
                add_watermark(img, r)
            if r.random() < 0.5:
                add_pen_lines(img, r, r.randint(1, 3))
            if r.random() < 0.6:
                img, b2 = rotate(img, [l["bbox"] for l in labels], r.uniform(-2.5, 2.5))
                labels = [dict(l, bbox=b) for l, b in zip(labels, b2)]
            if r.random() < 0.5:
                img, b2 = scale(img, [l["bbox"] for l in labels], r.uniform(0.45, 0.9))
                labels = [dict(l, bbox=b) for l, b in zip(labels, b2)]
            if r.random() < 0.6:
                img = jpeg(img, r.randint(25, 85))
            if r.random() < 0.4:
                img = cv2.GaussianBlur(img, (0, 0), r.uniform(0.6, 1.5))
            manifest.append(save(img, labels, f"{render.stem}-mix{k:02d}", out / "mixed", params))

    (out / "manifest.json").write_text(json.dumps({"seed": args.seed, "pages": manifest}, indent=1))
    print(f"{len(manifest)} synthetic pages under {out} (seed {args.seed})")


if __name__ == "__main__":
    main()
