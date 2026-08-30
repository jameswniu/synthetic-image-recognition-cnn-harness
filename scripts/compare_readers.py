"""Three readers, one answer key: the verdict table for the dashboard.

The same 286 hand-keyed boxes on the brief's pages, read three ways. Rules alone, which is what
ships. The CNN alone, with its own uncertainty band (under 0.10 empty, over 0.90 marked, between
goes to a person). And both together, where a disagreement joins the queue. Writes
compare_readers_report.json so the dashboard's comparison is computed, never typed.

Run: uv run --extra train python scripts/compare_readers.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import cv2  # noqa: E402

import hv_checkbox.pipeline as pipeline  # noqa: E402
from hv_checkbox.patch_model import load_scorer  # noqa: E402


def _iou(a: tuple, b: tuple) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua else 0.0


ROOT = Path(__file__).resolve().parent.parent
scorer = load_scorer()
if scorer is None:
    raise SystemExit("classifier unavailable: run with `uv run --extra train`")

rows = {k: {"graded": 0, "queue": 0, "right": 0, "wrong": 0} for k in ("rules", "cnn", "both")}


def run_page(img, mode):
    """A real pipeline pass in the named mode; no emulation anywhere."""
    os.environ["HV_CLASSIFIER"] = "off" if mode == "rules" else ""
    if mode == "both":
        os.environ.pop("HV_CLASSIFIER", None)
    pipeline._SCORER = "unset"
    pipeline.reset_template_cache()
    return pipeline.detect_with_page(img)


# Grades the classification stage on the boxes detection produced: the denominator is the
# shared set of detected boxes, identical for every mode. Detection misses (the brief's
# 287th box) are graded by `make eval`, not here; this table does not re-count them.
def grade(row, boxes, truth):
    for b in boxes:
        t = next((x[1] for x in truth if _iou((b.x1, b.y1, b.x2, b.y2), x[0]) >= 0.5), None)
        if t is None:
            continue
        row["graded"] += 1
        if b.reasons:
            row["queue"] += 1
        elif b.is_checked == t:
            row["right"] += 1
        else:
            row["wrong"] += 1


for lab_path in sorted((ROOT / "data" / "labels").glob("*.json")):
    lab = json.loads(lab_path.read_text())
    img_file = next(p for p in (ROOT / "data" / "samples").iterdir() if p.stem == lab_path.stem)
    img = cv2.imread(str(img_file))
    truth = [(tuple(b["bbox"]), bool(b["is_checked"])) for b in lab["boxes"] if not b.get("ignore")]

    page, boxes, _ = run_page(img, "rules")
    grade(rows["rules"], boxes, truth)

    # The CNN alone reads the rules pass's geometry; its uncertainty band is its queue.
    matched = [(b, next((x[1] for x in truth if _iou((b.x1, b.y1, b.x2, b.y2), x[0]) >= 0.5), None)) for b in boxes]
    matched = [(b, t) for b, t in matched if t is not None]
    for prob, (b, t) in zip([float(x) for x in scorer.score(page, [b for b, _ in matched])], matched):
        rows["cnn"]["graded"] += 1
        if 0.10 < prob < 0.90:
            rows["cnn"]["queue"] += 1
        elif (prob >= 0.5) == t:
            rows["cnn"]["right"] += 1
        else:
            rows["cnn"]["wrong"] += 1

    _, boxes_b, _ = run_page(img, "both")
    grade(rows["both"], boxes_b, truth)

(ROOT / "reports" / "compare_readers_report.json").write_text(json.dumps(rows, indent=1))
print(json.dumps(rows, indent=1))
