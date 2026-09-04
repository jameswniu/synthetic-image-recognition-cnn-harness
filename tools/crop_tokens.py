"""How big the crop the escalation lane sends is, in image tokens: reports/crop_tokens.json.

The escalation lane never sends a page. It sends one zoomed-in box, built by escalate.crop_png: the
box grown by 2.2 times its own size on every side, scaled so the whole crop comes to about 260 pixels
across and the box itself to about a fifth of that, with a magenta outline drawn on. This script builds that exact crop for every box the rules
pass finds on the four brief pages and counts its visual tokens the way the Claude API vision doc says it bills them: one token per 28 by
28 pixel patch, ceil(w/28) times ceil(h/28), after any downscale the tier's long-edge and token
limits force. A crop never downscales. A whole page does, on both tiers, and both are reported. The report carries the
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



PATCH = 28
TIERS = {
    "standard": {"max_edge": 1568, "max_tokens": 1568},
    "high_res": {"max_edge": 2576, "max_tokens": 4784},
}
DOC = "https://platform.claude.com/docs/en/build-with-claude/vision"


def count_image_tokens(width: int, height: int) -> int:
    """Visual tokens consumed by an image: one token per 28 by 28 pixel patch (the doc's own function)."""
    import math
    return math.ceil(width / PATCH) * math.ceil(height / PATCH)


def resized_size(width: int, height: int, max_edge: int, max_tokens: int) -> tuple[int, int]:
    """The size Claude resizes an image to before padding, the doc's reference implementation verbatim.

    The largest aspect-preserving size whose padded edges fit max_edge and whose token cost fits
    max_tokens, found by binary search along the long edge. An image already inside both limits is
    returned unchanged.
    """
    import math

    def fits(w: int, h: int) -> bool:
        return (
            math.ceil(w / PATCH) * PATCH <= max_edge
            and math.ceil(h / PATCH) * PATCH <= max_edge
            and count_image_tokens(w, h) <= max_tokens
        )

    if fits(width, height):
        return (width, height)
    if height > width:
        resized_h, resized_w = resized_size(height, width, max_edge, max_tokens)
        return (resized_w, resized_h)
    aspect_ratio = width / height
    lo, hi = 1, width
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if fits(mid, max(round(mid / aspect_ratio), 1)):
            lo = mid
        else:
            hi = mid
    return (lo, max(round(lo / aspect_ratio), 1))


def visual_tokens(w: int, h: int, tier: str) -> tuple[int, int, int]:
    """Tokens billed for a w by h image on one tier: (tokens, resized_w, resized_h)."""
    lim = TIERS[tier]
    rw, rh = resized_size(w, h, lim["max_edge"], lim["max_tokens"])
    return count_image_tokens(rw, rh), rw, rh

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/crop_tokens.json")
    args = ap.parse_args()

    pages = []
    page_tokens_all = []
    page_tokens_hi = []
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
            t = visual_tokens(w, h, "standard")[0]
            tokens.append(t)
            if set(b.reasons) & ROUTED:
                routed.append({"page": img_path.name, "bbox": b.bbox, "reasons": b.reasons,
                               "crop_px": [w, h], "tokens": round(t, 1)})
        every.extend(tokens)
        ph, pw = cv2.imread(str(img_path)).shape[:2]
        page_tok = visual_tokens(pw, ph, "standard")[0]
        page_tok_hi = visual_tokens(pw, ph, "high_res")[0]
        page_tokens_all.append(page_tok)
        page_tokens_hi.append(page_tok_hi)
        pages.append({
            "page": img_path.name,
            "page_px": [pw, ph],
            "page_tokens": page_tok,
            "page_tokens_high_res": page_tok_hi,
            "boxes": len(boxes),
            "box_px": [round(statistics.median(b.w for b in boxes)), round(statistics.median(b.h for b in boxes))],
            "median_tokens": round(statistics.median(tokens), 1),
            "min_tokens": round(min(tokens), 1),
            "max_tokens": round(max(tokens), 1),
        })
        print(f"{img_path.name:14s} {len(boxes):4d} boxes  median {statistics.median(tokens):6.1f} tokens  "
              f"min {min(tokens):6.1f}  max {max(tokens):6.1f}")

    report = {
        "rule": "each 28 by 28 pixel patch is one visual token, so an image costs ceil(w/28) times ceil(h/28), downscaled to fit the tier's long-edge and visual-token limits (standard 1,568 px and 1,568 tokens, high resolution 2,576 px and 4,784 tokens), per " + DOC + " read 2026-09-04, resize per the reference implementation on the vision-coordinates page",
        "crop": "src/hv_checkbox/escalate.py crop_png: the box grown 2.2x on every side, scaled so the whole crop is about 260 px across and the box about a fifth of that",
        "pages": pages,
        "routed": routed,
        "totals": {
            "boxes": len(every),
            "median_tokens": round(statistics.median(every), 1),
            "median_tokens_rounded": round(statistics.median(every)),
            "page_median_tokens": round(statistics.median(page_tokens_all)),
            "page_median_tokens_high_res": round(statistics.median(page_tokens_hi)),
        },
    }
    out = ROOT / args.out
    out.write_text(json.dumps(report, indent=1))
    print(f"wrote {args.out}: median {statistics.median(every):.1f} tokens over {len(every)} boxes, "
          f"{len(routed)} routed on the shipped run")


if __name__ == "__main__":
    main()
