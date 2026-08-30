"""Seed page-level labels from the detector, then apply hand corrections.

The detector output is a draft, not truth. Corrections below were made by eye against zoomed crops:
boxes the detector missed are added, non-checkbox artifacts are marked ignore, and states the ink rule
got wrong are flipped. Every correction carries a note so the bias of seeding from the detector stays visible.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2

from hv_checkbox.pipeline import detect_checkboxes

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
LABELS = ROOT / "data" / "labels"

# (x1, y1, x2, y2, is_checked, note): boxes to add that the detector does not find
ADD = {
    "sample_1.jpg": [],
    "sample_2.png": [],
    "sample_5.png": [],
    "sample_7.png": [],
}
# (cx, cy, note): detections to drop as not checkboxes
DROP: dict[str, list[tuple[int, int, str]]] = {
    "sample_1.jpg": [(55, 11, "hole in the black sidebar bar, not a checkbox")],
    "sample_2.png": [],
    "sample_5.png": [],
    "sample_7.png": [],
}
# (cx, cy, note): artifacts that are not checkboxes, kept as ignore
IGNORE: dict[str, list[tuple[int, int, int, int, str]]] = {
    "sample_1.jpg": [(285, 188, 306, 211, "Neighborhood Boundaries text-field artifact, not a checkbox")],
    "sample_2.png": [],
    "sample_5.png": [],
    "sample_7.png": [],
}
# (cx, cy, is_checked, note): state corrections
FLIP: dict[str, list[tuple[int, int, bool, str]]] = {
    "sample_1.jpg": [
        (208, 624, True, "Electricity Public: scan-faded X, strokes survive only as specks"),
        (286, 624, True, "Electricity Other: check-mark tick, not an X"),
        (724, 503, False, "No Zoning: a pen loop crosses the box, no selection mark"),
    ],
    "sample_2.png": [],
    "sample_5.png": [],
    "sample_7.png": [],
}


def near(box, cx, cy, tol=14):
    return abs((box["bbox"][0] + box["bbox"][2]) / 2 - cx) <= tol and abs((box["bbox"][1] + box["bbox"][3]) / 2 - cy) <= tol


def main() -> None:
    LABELS.mkdir(parents=True, exist_ok=True)
    for name in ["sample_1.jpg", "sample_2.png", "sample_5.png", "sample_7.png"]:
        img = cv2.imread(str(SAMPLES / name))
        boxes = [{"bbox": b.bbox, "is_checked": bool(b.is_checked), "ignore": False, "note": "seeded"} for b in detect_checkboxes(img)]
        for cx, cy, note in DROP[name]:
            boxes = [b for b in boxes if not near(b, cx, cy)]
        for cx, cy, state, note in FLIP[name]:
            for b in boxes:
                if near(b, cx, cy):
                    b["is_checked"] = state
                    b["note"] = note
        for x1, y1, x2, y2, state, note in ADD[name]:
            boxes.append({"bbox": [x1, y1, x2, y2], "is_checked": state, "ignore": False, "note": note})
        for x1, y1, x2, y2, note in IGNORE[name]:
            boxes.append({"bbox": [x1, y1, x2, y2], "is_checked": False, "ignore": True, "note": note})
        boxes.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
        (LABELS / (Path(name).stem + ".json")).write_text(json.dumps({"source": name, "boxes": boxes}, indent=1))
        print(name, len(boxes), "boxes,", sum(b["is_checked"] for b in boxes), "checked,", sum(b["ignore"] for b in boxes), "ignored")


if __name__ == "__main__":
    main()
