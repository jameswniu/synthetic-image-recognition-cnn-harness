"""Referee: score the pipeline against page-level labels.

Labels live in data/labels/<sample>.json:
  {"source": "sample_1.jpg", "boxes": [{"bbox": [x1, y1, x2, y2], "is_checked": true, "ignore": false, "note": ""}, ...]}

Detection is matched greedily by IoU at 0.5. A ground-truth box marked ignore is neither a miss when
undetected nor a hit when detected; it is simply left out (used for artifacts that are not checkboxes
and for cards the labeler marked unsure).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from hv_checkbox.overlay import draw
from hv_checkbox.pipeline import detect_with_page
from hv_checkbox.types import Box, iou

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
LABELS = ROOT / "data" / "labels"


def load_labels(path: Path) -> list[Box]:
    data = json.loads(path.read_text())
    out = []
    for b in data["boxes"]:
        x1, y1, x2, y2 = b["bbox"]
        box = Box(x1, y1, x2, y2, is_checked=bool(b.get("is_checked", False)))
        box.reasons = ["IGNORE"] if b.get("ignore") else []
        out.append(box)
    return out


def match(pred: list[Box], gold: list[Box], thr: float = 0.5) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Greedy IoU matching. Returns (pairs, unmatched_pred, unmatched_gold) by index."""
    if not pred or not gold:
        return [], list(range(len(pred))), list(range(len(gold)))
    m = np.zeros((len(pred), len(gold)))
    for i, p in enumerate(pred):
        for j, g in enumerate(gold):
            m[i, j] = iou(p, g)
    pairs, used_p, used_g = [], set(), set()
    for _ in range(min(len(pred), len(gold))):
        i, j = np.unravel_index(int(m.argmax()), m.shape)
        if m[i, j] < thr:
            break
        pairs.append((int(i), int(j)))
        used_p.add(int(i))
        used_g.add(int(j))
        m[i, :] = -1
        m[:, j] = -1
    return pairs, [i for i in range(len(pred)) if i not in used_p], [j for j in range(len(gold)) if j not in used_g]


def score_sample(name: str, thr: float = 0.5, samples_dir: Path | None = None, labels_dir: Path | None = None) -> dict:
    img = cv2.imread(str((samples_dir or SAMPLES) / name))
    gold = load_labels((labels_dir or LABELS) / (Path(name).stem + ".json"))
    t0 = time.perf_counter()
    page, pred, meta = detect_with_page(img)
    elapsed = (time.perf_counter() - t0) * 1000
    pairs, fp_idx, fn_idx = match(pred, gold, thr)
    ignored_gold = {j for j, g in enumerate(gold) if "IGNORE" in g.reasons}
    pairs_scored = [(i, j) for i, j in pairs if j not in ignored_gold]
    fp = [i for i in fp_idx]
    fn = [j for j in fn_idx if j not in ignored_gold]
    tp = len(pairs_scored)
    precision = tp / (tp + len(fp)) if tp + len(fp) else 0.0
    recall = tp / (tp + len(fn)) if tp + len(fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    cls_correct = sum(1 for i, j in pairs_scored if pred[i].is_checked == gold[j].is_checked)
    cls_acc = cls_correct / tp if tp else 0.0
    return {
        "sample": name,
        "gold": len(gold) - len(ignored_gold),
        "ignored": len(ignored_gold),
        "pred": len(pred),
        "tp": tp,
        "fp": len(fp),
        "fn": len(fn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "cls_acc": round(cls_acc, 4),
        "cls_wrong": [pred[i].bbox for i, j in pairs_scored if pred[i].is_checked != gold[j].is_checked],
        "ambiguous": sum(1 for p in pred if p.reasons),
        "fp_boxes": [pred[i].bbox for i in fp],
        "fn_boxes": [gold[j].bbox for j in fn],
        "elapsed_ms": round(elapsed, 1),
        "box_side": page.box_side,
        "form": meta.get("form"),
        "registration": meta.get("registration"),
        "witness": meta.get("witness"),
        "_page": page,
        "_pred": pred,
        "_gold": gold,
    }


def write_overlay(result: dict, out_dir: Path) -> Path:
    page, pred, gold = result["_page"], result["_pred"], result["_gold"]
    img = draw(page.image, pred)
    t = max(2, page.width // 900)
    for j, g in enumerate(gold):
        colour = (200, 200, 200) if "IGNORE" in g.reasons else (255, 120, 0)
        cv2.rectangle(img, (g.x1 - 3, g.y1 - 3), (g.x2 + 3, g.y2 + 3), colour, 1)
    for bb in result["fn_boxes"]:
        cv2.rectangle(img, (bb[0] - 6, bb[1] - 6), (bb[2] + 6, bb[3] + 6), (255, 0, 255), t)
    for bb in result["fp_boxes"]:
        cv2.rectangle(img, (bb[0] - 6, bb[1] - 6), (bb[2] + 6, bb[3] + 6), (0, 200, 255), t)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (Path(result["sample"]).stem + "-overlay.png")
    cv2.imwrite(str(path), img)
    return path


def run(samples: list[str] | None = None, overlays: Path | None = None) -> list[dict]:
    names = samples or sorted(p.name for p in SAMPLES.iterdir() if (LABELS / (p.stem + ".json")).exists())
    results = []
    for name in names:
        r = score_sample(name)
        if overlays:
            write_overlay(r, overlays)
        results.append(r)
    return results


def summarize(results: list[dict]) -> dict:
    tp = sum(r["tp"] for r in results)
    fp = sum(r["fp"] for r in results)
    fn = sum(r["fn"] for r in results)
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    cls = sum(round(r["cls_acc"] * r["tp"]) for r in results) / tp if tp else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4), "recall": round(rc, 4),
            "f1": round(2 * p * rc / (p + rc), 4) if p + rc else 0.0, "cls_acc": round(cls, 4)}


def public(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def score_synth(synth_dir: Path) -> list[dict]:
    """Aggregate metrics per (factor, level) across every labeled synthetic page under synth_dir."""
    rows: dict[tuple[str, str], list[dict]] = {}
    for lab in sorted(synth_dir.rglob("*.json")):
        if lab.name == "manifest.json":
            continue
        data = json.loads(lab.read_text())
        png = lab.with_suffix(".png")
        if "params" not in data or not png.exists():
            continue
        r = score_sample(png.name, samples_dir=png.parent, labels_dir=lab.parent)
        key = (str(data["params"]["factor"]), str(data["params"]["level"]))
        rows.setdefault(key, []).append(r)
    out = []
    for (factor, level), rs in sorted(rows.items()):
        s = summarize(rs)
        out.append({"factor": factor, "level": level, "pages": len(rs), **s})
    return out


def score_gold_cards() -> dict:
    """Agreement with the frozen gold cards that carry page coordinates and a hard human answer.

    Unsure and not-a-checkbox rulings and suspected misclicks are excluded from hard grading by
    policy; synthetic cards carry no page coordinates and are scored by the patch classifier's
    validation instead.
    """
    gold = json.loads((ROOT / "data" / "gold_set.json").read_text())["cards"]
    cache: dict[str, list[Box]] = {}
    total = correct = 0
    misses = []
    for g in gold:
        if g["source"] == "synthetic" or g["label"] not in ("filled", "empty") or g.get("suspected_misclick"):
            continue
        if g["source"] not in cache:
            img = cv2.imread(str(SAMPLES / g["source"]))
            cache[g["source"]] = detect_with_page(img)[1]
        x1, y1, x2, y2 = g["bbox"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        near = [b for b in cache[g["source"]] if abs(b.cx - cx) + abs(b.cy - cy) < 18]
        want = g["label"] == "filled"
        total += 1
        if near and near[0].is_checked == want:
            correct += 1
        else:
            misses.append({"id": g["id"], "source": g["source"], "bbox": g["bbox"], "label": g["label"], "found": bool(near)})
    return {"cards": total, "correct": correct, "accuracy": round(correct / total, 4) if total else None, "misses": misses}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=None)
    ap.add_argument("--overlays", default=None)
    ap.add_argument("--samples", nargs="*")
    ap.add_argument("--synth", default=None, help="score a synthetic set instead: path to data/synth")
    ap.add_argument("--gold", action="store_true", help="score agreement with the frozen gold cards instead")
    ap.add_argument("--require-classifier", action="store_true",
                    help="fail rather than quietly reporting rule-only numbers under a classifier heading")
    args = ap.parse_args()
    if args.gold:
        r = score_gold_cards()
        print(f"gold cards graded {r['cards']}, agreement {r['accuracy']}, misses {r['misses']}")
        if args.report:
            Path(args.report).write_text(json.dumps(r, indent=1))
        return
    if args.synth:
        rows = score_synth(Path(args.synth))
        print(f"{'factor':10s} {'level':>6s} {'pages':>5s} {'tp':>5s} {'fp':>4s} {'fn':>4s} {'prec':>6s} {'rec':>6s} {'f1':>6s} {'cls':>6s}")
        for r in rows:
            print(f"{r['factor']:10s} {r['level']:>6s} {r['pages']:5d} {r['tp']:5d} {r['fp']:4d} {r['fn']:4d} {r['precision']:6.3f} {r['recall']:6.3f} {r['f1']:6.3f} {r['cls_acc']:6.3f}")
        if args.report:
            Path(args.report).write_text(json.dumps(rows, indent=1))
        return
    results = run(args.samples, Path(args.overlays) if args.overlays else None)
    from hv_checkbox.pipeline import _scorer

    on = _scorer() is not None
    mode = "deterministic core + patch classifier" if on else "deterministic core only"
    if args.require_classifier and not on:
        raise SystemExit("classifier run asked for, but the patch scorer would not load: install the train extra and clear HV_CLASSIFIER=off")
    print("mode: " + mode)
    print(f"{'sample':14s} {'gold':>5s} {'pred':>5s} {'tp':>4s} {'fp':>4s} {'fn':>4s} {'prec':>6s} {'rec':>6s} {'f1':>6s} {'cls':>6s} {'amb':>4s} {'ms':>7s}")
    for r in results:
        print(f"{r['sample']:14s} {r['gold']:5d} {r['pred']:5d} {r['tp']:4d} {r['fp']:4d} {r['fn']:4d} {r['precision']:6.3f} {r['recall']:6.3f} {r['f1']:6.3f} {r['cls_acc']:6.3f} {r['ambiguous']:4d} {r['elapsed_ms']:7.1f}")
    s = summarize(results)
    print(f"{'overall':14s} {'':5s} {'':5s} {s['tp']:4d} {s['fp']:4d} {s['fn']:4d} {s['precision']:6.3f} {s['recall']:6.3f} {s['f1']:6.3f} {s['cls_acc']:6.3f}")
    if args.report:
        Path(args.report).write_text(json.dumps({"mode": mode, "samples": [public(r) for r in results], "overall": s}, indent=1))


if __name__ == "__main__":
    main()
