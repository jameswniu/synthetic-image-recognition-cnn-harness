"""How big the crop the escalation lane sends is, in image tokens: reports/crop_tokens.json.

The escalation lane never sends a page. It sends one zoomed-in box, built by escalate.crop_png: the
box grown by 2.2 times its own size on every side, scaled so the box itself is about 260 pixels
across, with a magenta outline drawn on. This script builds that exact crop for every box the rules
pass finds on the four brief pages and counts its image tokens under the rule Anthropic documents
for the Claude API: tokens = width * height / 750. No downscale applies, because every crop sits far
below the 1,568 pixel long edge at which the API starts shrinking an image. The report carries the
per-page medians, the median over every box, and the boxes the shipped run actually routes, so the
figure in the README is a measurement of the real crop geometry rather than a guess.

Run: make crop-tokens  (HV_CLASSIFIER=off uv run python tools/crop_tokens.py)
Out: reports/crop_tokens.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from hv_checkbox.escalate import ROUTED, crop_png  # noqa: E402
from hv_checkbox.pipeline import detect_with_page  # noqa: E402

SAMPLES = ROOT / "data" / "samples"
PIXELS_PER_TOKEN = 750.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/crop_tokens.json")
    args = ap.parse_args()

    pages = []
    every: list[float] = []
    routed = []
    for img_path in sorted(SAMPLES.iterdir()):
        if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        img = cv2.imread(str(img_path))
        page, boxes, _ = detect_with_page(img)
        tokens = []
        for b in boxes:
            png = crop_png(page, b)
            crop = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
            h, w = crop.shape[:2]
            t = w * h / PIXELS_PER_TOKEN
            tokens.append(t)
            if set(b.reasons) & ROUTED:
                routed.append({"page": img_path.name, "bbox": b.bbox, "reasons": b.reasons,
                               "crop_px": [w, h], "tokens": round(t, 1)})
        every.extend(tokens)
        pages.append({
            "page": img_path.name,
            "boxes": len(boxes),
            "box_px": [round(statistics.median(b.w for b in boxes)), round(statistics.median(b.h for b in boxes))],
            "median_tokens": round(statistics.median(tokens), 1),
            "min_tokens": round(min(tokens), 1),
            "max_tokens": round(max(tokens), 1),
        })
        print(f"{img_path.name:14s} {len(boxes):4d} boxes  median {statistics.median(tokens):6.1f} tokens  "
              f"min {min(tokens):6.1f}  max {max(tokens):6.1f}")

    report = {
        "rule": "tokens = crop width * crop height / 750, the Claude API's documented image estimate; no downscale, every crop is under the 1,568 px long edge",
        "crop": "src/hv_checkbox/escalate.py crop_png: the box grown 2.2x on every side, scaled so the box is about 260 px across",
        "pages": pages,
        "routed": routed,
        "totals": {
            "boxes": len(every),
            "median_tokens": round(statistics.median(every), 1),
            "median_tokens_rounded": round(statistics.median(every)),
        },
    }
    out = ROOT / args.out
    out.write_text(json.dumps(report, indent=1))
    print(f"wrote {args.out}: median {statistics.median(every):.1f} tokens over {len(every)} boxes, "
          f"{len(routed)} routed on the shipped run")


if __name__ == "__main__":
    main()
