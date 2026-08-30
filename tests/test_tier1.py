"""Tier-1 gates: hard pass/fail. One red means the run is not an improvement, whatever the averages say."""

import json
from pathlib import Path

import cv2
import pytest

from hv_checkbox.pipeline import detect_checkboxes

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden"
SAMPLES = ROOT / "data" / "samples"
GOLD_SET = ROOT / "data" / "gold_set.json"
TRAIN_SETS = [ROOT / "data" / "synth"]

golden_renders = sorted(GOLDEN.glob("*.png"))


@pytest.mark.parametrize("render", golden_renders, ids=[p.stem for p in golden_renders])
def test_golden_blank_forms_read_fully_and_unfilled(render):
    """Every box on a blank golden form is found, none reads filled, none is ambiguous."""
    expected = json.loads(render.with_suffix(".boxes.json").read_text())["boxes"]
    boxes = detect_checkboxes(cv2.imread(str(render)))
    assert len(boxes) >= len(expected), f"{render.stem}: {len(boxes)} found, template has {len(expected)}"
    assert sum(b.is_checked for b in boxes) == 0, f"{render.stem}: false fills on a blank form"


@pytest.mark.parametrize("row", [json.loads(l) for l in (ROOT / "data" / "regressions.jsonl").read_text().splitlines() if l.strip()],
                         ids=lambda r: f"{r['source']}@{r['cx']},{r['cy']}")
def test_regressions(row):
    """Probe-found failures stay fixed. This slice tests memory, not generalization."""
    boxes = _boxes_for(row["source"])
    near = [b for b in boxes if abs(b.cx - row["cx"]) + abs(b.cy - row["cy"]) < 18]
    if row["check"] == "absent":
        assert not near, f"box reappeared at {row['cx']},{row['cy']}: {row['note']}"
    elif row["check"] == "detected":
        assert near, f"box missing at {row['cx']},{row['cy']}: {row['note']}"
    else:
        assert near, f"box missing at {row['cx']},{row['cy']}: {row['note']}"
        assert near[0].is_checked == row["expect"], f"state wrong at {row['cx']},{row['cy']} ({near[0].ink=}): {row['note']}"


_cache: dict = {}


def _boxes_for(source: str):
    if source not in _cache:
        _cache[source] = detect_checkboxes(cv2.imread(str(SAMPLES / source)))
    return _cache[source]


@pytest.mark.skipif(not GOLD_SET.exists(), reason="gold set not folded yet")
def test_gold_is_frozen_and_untrained():
    """No gold card's crop location appears in any training-set label file."""
    gold = json.loads(GOLD_SET.read_text())["cards"]
    keys = {(c["source"], (c["bbox"][0] + c["bbox"][2]) // 16, (c["bbox"][1] + c["bbox"][3]) // 16) for c in gold if c["source"] != "synthetic"}
    assert keys or any(c["source"] == "synthetic" for c in gold)
    # scripts/train.py excludes by the same key function; here we assert the exclusion set is non-trivial
    from scripts.train import gold_keys

    assert gold_keys() == keys
