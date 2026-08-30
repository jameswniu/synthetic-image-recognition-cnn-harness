"""Edge miner: turn measured failures into the next round of booth cards.

Runs the pipeline over every labeled page (the four samples plus the synthetic sweeps and mixed set),
collects the disagreements with ground truth (missed boxes, phantom boxes, wrong states, ambiguous
reads), and packages a capped, seeded sample of them as a second labeling booth. This is the
take-home's stand-in for mining production traces: failures propose the cards, the human rules on
them, the rulings become policy lines, regression rows, and training data. Nobody hand-hunts edge cases.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from make_cards import encode_png, crop_card  # noqa: E402
from evaluate import load_labels, match  # noqa: E402
from hv_checkbox.pipeline import detect_with_page  # noqa: E402
from hv_checkbox.types import Box  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CAP_PER_KIND = 12


def collect(page_png: Path, labels_json: Path) -> list[dict]:
    img = cv2.imread(str(page_png))
    gold = load_labels(labels_json)
    page, pred, _ = detect_with_page(img)
    pairs, fp_idx, fn_idx = match(pred, gold)
    ignored = {j for j, g in enumerate(gold) if "IGNORE" in g.reasons}
    out = []

    def card(box: Box, kind: str, note: str) -> dict:
        return {
            "source": str(page_png.relative_to(ROOT)),
            "bbox": box.bbox,
            "kind": kind,
            "note": note,
            "png": encode_png(crop_card(img, box, page.box_side)),
        }

    for j in fn_idx:
        if j not in ignored:
            out.append(card(gold[j], "missed", "ground truth says a box is here; the detector found nothing"))
    for i in fp_idx:
        out.append(card(pred[i], "phantom", "the detector found a box ground truth does not have"))
    for i, j in pairs:
        if j in ignored:
            continue
        if pred[i].is_checked != gold[j].is_checked:
            out.append(card(pred[i], "state", f"detector says {'filled' if pred[i].is_checked else 'empty'} (ink {pred[i].ink}), truth says the opposite"))
        elif pred[i].reasons:
            out.append(card(pred[i], "ambiguous", ",".join(pred[i].reasons)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--out", default="labeling/labeling-booth-round2.html")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    found: dict[str, list[dict]] = {}
    jobs = []
    for lab in sorted((ROOT / "data" / "labels").glob("*.json")):
        src = json.loads(lab.read_text())["source"]
        jobs.append((ROOT / "data" / "samples" / src, lab))
    for lab in sorted((ROOT / "data" / "synth").rglob("*.json")):
        if lab.name != "manifest.json" and lab.with_suffix(".png").exists():
            jobs.append((lab.with_suffix(".png"), lab))
    for png, lab in jobs:
        for c in collect(png, lab):
            found.setdefault(c["kind"], []).append(c)
    cards = []
    for kind in sorted(found):
        pool = found[kind]
        rng.shuffle(pool)
        cards += pool[:CAP_PER_KIND]
        print(f"{kind}: {len(pool)} found, {min(len(pool), CAP_PER_KIND)} carded")
    rng.shuffle(cards)
    for i, c in enumerate(cards, 1):
        c["id"] = f"r{i:03d}"
    meta = [{k: v for k, v in c.items() if k != "png"} for c in cards]
    (ROOT / "data" / "cards" / "cards-round2.json").write_text(json.dumps(meta, indent=1))
    slim = [{"id": c["id"], "source": c["source"], "bbox": c["bbox"], "png": c["png"]} for c in cards]
    html = (ROOT / "labeling" / "booth_template.html").read_text().replace("__CARDS__", json.dumps(slim).replace("</", "<\\/"))
    (ROOT / args.out).write_text(html)
    print(f"{len(cards)} round-two cards -> {args.out}")


if __name__ == "__main__":
    main()
