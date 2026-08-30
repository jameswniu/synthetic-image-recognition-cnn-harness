"""Witness A: structure detector.

Checkboxes are the only small, square, closed regions bounded by straight
horizontal and vertical strokes on a form. Everything else that could be inside
them (X strokes, ticks, watermark text, handwriting) is diagonal or curved and
disappears under a horizontal/vertical morphological opening, so the box
interior shows up as an enclosed hole in the line mask.
"""

from __future__ import annotations

import cv2
import numpy as np

from hv_checkbox.normalize import Page, enclosed_holes, open_lines
from hv_checkbox.types import Box


def _drop_short_segments(mask: np.ndarray, min_len: int, horizontal: bool) -> np.ndarray:
    """Remove line fragments shorter than min_len along their own axis (the residue of thick X strokes)."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = np.zeros(n, dtype=bool)
    axis = cv2.CC_STAT_WIDTH if horizontal else cv2.CC_STAT_HEIGHT
    keep[1:] = stats[1:, axis] >= min_len
    return np.where(keep[labels], 255, 0).astype(np.uint8)


def line_mask(page: Page, kernel_frac: float) -> np.ndarray:
    side = page.box_side
    h, v = open_lines(page.ink, side * kernel_frac)
    h = _drop_short_segments(h, int(side * 0.75), horizontal=True)
    v = _drop_short_segments(v, int(side * 0.75), horizontal=False)
    # extend line ends so borders that stop a pixel short of each other still close
    h = cv2.dilate(h, np.ones((3, 7), np.uint8))
    v = cv2.dilate(v, np.ones((7, 3), np.uint8))
    return cv2.bitwise_or(h, v)


def _dedupe(boxes: list[Box], tol: float) -> list[Box]:
    out: list[Box] = []
    for b in boxes:
        if all(abs(b.cx - o.cx) + abs(b.cy - o.cy) > tol for o in out):
            out.append(b)
    return out


def _text_like(page: Page, b: Box) -> bool:
    """Interior holds several small ink blobs and no dominant stroke: a text cell, not a mark.

    A real mark is one connected stroke (an X, a tick, a fill). Printed text inside a table cell
    breaks into letters. This is the same evidence the classifier uses to refuse a mark; here it is
    a second opinion on whether the region is a checkbox at all.
    """
    ix, iy = int(b.w * 0.15), int(b.h * 0.15)
    crop = page.ink[b.y1 + iy : b.y2 - iy, b.x1 + ix : b.x2 - ix]
    if crop.size == 0:
        return False
    frac = float(crop.mean() / 255.0)
    if not (0.03 < frac < 0.5):
        return False
    n, _, stats, _ = cv2.connectedComponentsWithStats(crop, connectivity=8)
    if n <= 1:
        return False
    areas = stats[1:, cv2.CC_STAT_AREA]
    return int(n - 1) >= 4 and float(areas.max() / crop.size) < 0.08


def _ring_ink(page: Page, b: Box) -> float:
    """Ink density in a ring around the box. A checkbox sits on paper (low); a hole punched in a
    solid black block (a sidebar bar, a logo) is surrounded by ink (high)."""
    m = max(3, int(page.box_side * 0.4))
    x1, y1 = max(0, b.x1 - m), max(0, b.y1 - m)
    x2, y2 = min(page.width, b.x2 + m), min(page.height, b.y2 + m)
    window = page.ink[y1:y2, x1:x2].astype(np.float64)
    total = window.sum()
    inner = page.ink[b.y1 : b.y2, b.x1 : b.x2].astype(np.float64).sum()
    ring_area = (x2 - x1) * (y2 - y1) - b.w * b.h
    return float((total - inner) / (255.0 * ring_area)) if ring_area > 0 else 0.0


def detect_boxes(
    page: Page,
    kernel_fracs: tuple[float, ...] = (0.6, 0.8),
    consensus: float = 0.15,
    rejects: list[Box] | None = None,
) -> list[Box]:
    """Return candidate checkbox boxes in page coordinates, bbox including the border.

    Anything the size-consensus rules throw away is appended to `rejects` when a list is passed, so a
    rejection can be inspected rather than taken on trust. The pipeline surfaces it under
    `?explain=true`. Dropping a candidate is the one place this system removes evidence instead of
    flagging it, so the removal has to be visible.
    """
    side = page.box_side
    lo, hi = int(side * 0.6), int(side * 1.6)
    border = max(2, int(round(side * 0.08)))
    found: list[Box] = []
    for frac in kernel_fracs:
        lines = line_mask(page, frac)
        for x, y, w, h in enclosed_holes(lines, lo, hi):
            found.append(Box(x - border, y - border, x + w + border, y + h + border, witnesses=["structure"]))
    found = _dedupe(found, tol=side * 0.3)
    found = [b for b in found if _ring_ink(page, b) < 0.5]
    if not found:
        return []
    # size consensus: real boxes on one page vary by well under 15%, glyph holes and cells do not match
    sides = np.array([max(b.w, b.h) for b in found])
    med = float(np.median(sides))
    kept = [b for b, s in zip(found, sides) if abs(s - med) / med <= consensus]
    # A table cell that happens to be square-ish imitates a checkbox. Two signals have to agree
    # before one is dropped: its height is off the page's own median (real boxes on a page vary by
    # a few percent; measured range across nine pages is under 9%) AND its interior holds text.
    # Either signal alone is not enough: a form with two box sizes would lose real boxes to the
    # first, and a marked box holding a scribble could trip the second.
    if rejects is not None:
        rejects.extend(b for b, s in zip(found, sides) if abs(s - med) / med > consensus)
    if len(kept) >= 5:
        med_h = float(np.median([b.h for b in kept]))
        survives = [b for b in kept if abs(b.h - med_h) / med_h <= 0.10 or not _text_like(page, b)]
        if rejects is not None:
            keep_ids = {id(b) for b in survives}
            for b in kept:
                if id(b) not in keep_ids:
                    b.reasons = [*b.reasons, "TEXT_LIKE_SIZE_OUTLIER"]
                    rejects.append(b)
        kept = survives
    for b in kept:
        b.x1, b.y1 = max(0, b.x1), max(0, b.y1)
        b.x2, b.y2 = min(page.width, b.x2), min(page.height, b.y2)
    return sorted(kept, key=lambda b: (b.y1, b.x1))
