"""Per-sample floors against the corrected page labels. These are the numbers the docs quote."""

import pytest

from scripts.evaluate import score_sample

FLOORS = {
    # sample: (min detection F1, min classification accuracy)
    # sample_1 carries two labeler-ruled hard cases by design: the faint grey box the detector
    # cannot see (a counted miss) and the scan-faded X that stays routed rather than decided.
    "sample_1.jpg": (0.97, 0.95),
    "sample_2.png": (0.99, 0.99),
    "sample_5.png": (0.99, 0.99),
    "sample_7.png": (0.99, 0.99),
}


@pytest.mark.parametrize("name", sorted(FLOORS))
def test_sample_floors(name):
    r = score_sample(name)
    f1_floor, cls_floor = FLOORS[name]
    assert r["f1"] >= f1_floor, f"{name}: detection f1 {r['f1']} under {f1_floor} (fp={r['fp_boxes']}, fn={r['fn_boxes']})"
    assert r["cls_acc"] >= cls_floor, f"{name}: cls {r['cls_acc']} under {cls_floor} (wrong={r['cls_wrong']})"
    assert r["elapsed_ms"] < 2000, f"{name}: {r['elapsed_ms']} ms is past any reasonable page budget"


def test_rejected_candidates_use_reported_coordinates():
    """A rejected candidate is quoted in the same space as the boxes beside it.

    Pages narrower than MIN_WIDTH are processed at 2x and reported at 1x. The audit trail for a
    hard-dropped candidate was serialised before that conversion, so on an upscaled page it pointed
    at coordinates twice as far down the page as the thing it described, which reads as evidence
    while being wrong. sample_1 at half size exercises the upscale path and produces real rejects,
    so this does not pass by having nothing to check.
    """
    from pathlib import Path

    import cv2

    from hv_checkbox.pipeline import MIN_WIDTH, detect_with_page

    full = cv2.imread(str(Path(__file__).resolve().parent.parent / "data" / "samples" / "sample_1.jpg"))
    img = cv2.resize(full, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    assert img.shape[1] < MIN_WIDTH, "this test needs a page small enough to be upscaled"
    _, _, meta = detect_with_page(img)
    assert meta.get("upscaled") == 2, "the upscale path did not run, so this test proves nothing"
    assert meta["rejected"], "no rejected candidates, so this test proves nothing"
    h, w = img.shape[:2]
    for r in meta["rejected"]:
        x1, y1, x2, y2 = r["bbox"]
        assert 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h, f"reject {r} falls outside the reported {w}x{h} page"
