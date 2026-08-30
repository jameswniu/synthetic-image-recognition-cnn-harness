"""Filled-vs-empty state from the ink inside a box, with a confidence and reason codes.

Three kinds of evidence, in order of trust:
  ink fraction        an X, a solid fill, a scribble: lots of ink in the interior
  mark span           a tick or a single thin stroke: little ink, but one component crossing the box
  stray-stroke trace  a pen line passing THROUGH the box keeps going outside it; a real mark lives inside
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from hv_checkbox import policy as policy_module
from hv_checkbox.normalize import Page
from hv_checkbox.policy import Policy
from hv_checkbox.types import Box

# These moved into policy.py so a customer can change what counts as a mark without touching this
# file. The names survive because the numbers are worth reading next to the code that uses them,
# and because POLICY.md cites them; they are the defaults, not the values in force.
THRESHOLD = policy_module.DEFAULT.ink_filled
BAND = (policy_module.DEFAULT.ambiguous_low, policy_module.DEFAULT.ambiguous_high)
SCALE = policy_module.DEFAULT.confidence_scale
SPAN_MIN = policy_module.DEFAULT.thin_mark_span
STRAY_OUTSIDE = policy_module.DEFAULT.stray_outside


def interior(page: Page, box: Box, inset: float = 0.15) -> np.ndarray:
    ix, iy = int(box.w * inset), int(box.h * inset)
    return page.ink[box.y1 + iy : box.y2 - iy, box.x1 + ix : box.x2 - ix]


def ink_fraction(page: Page, box: Box) -> float:
    crop = interior(page, box)
    return float(crop.mean() / 255.0) if crop.size else 0.0


def mark_stats(page: Page, box: Box) -> tuple[int, float, float, float]:
    """(component count, largest area share, largest span, outside fraction of the largest mark).

    Span is the largest interior component's bbox diagonal over the box diagonal. The outside
    fraction traces that component in a padded window of the full-page ink: how much of it lies
    beyond the box grown 25%, which separates a tick (contained) from a pen line passing through.
    """
    crop = interior(page, box)
    if crop.size == 0:
        return 0, 0.0, 0.0, 0.0
    n, labels, stats, _ = cv2.connectedComponentsWithStats(crop, connectivity=8)
    if n <= 1:
        return 0, 0.0, 0.0, 0.0
    areas = stats[1:, cv2.CC_STAT_AREA]
    k = int(areas.argmax()) + 1
    lw, lh = float(stats[k, cv2.CC_STAT_WIDTH]), float(stats[k, cv2.CC_STAT_HEIGHT])
    span = math.hypot(lw, lh) / math.hypot(box.w, box.h)
    # trace the largest mark in a padded window of the page
    pad = int(max(box.w, box.h) * 1.2)
    wx1, wy1 = max(0, box.x1 - pad), max(0, box.y1 - pad)
    wx2, wy2 = min(page.width, box.x2 + pad), min(page.height, box.y2 + pad)
    window = page.ink[wy1:wy2, wx1:wx2]
    nw, wl = cv2.connectedComponents(window, connectivity=8)
    ys, xs = np.nonzero(labels == k)
    if len(xs) == 0:
        return int(n - 1), float(areas.max() / crop.size), span, 0.0
    ix, iy = int(box.w * 0.15), int(box.h * 0.15)
    seed_label = wl[ys[0] + (box.y1 + iy - wy1), xs[0] + (box.x1 + ix - wx1)]
    comp = wl == seed_label
    gy1, gy2 = box.y1 - wy1 - int(box.h * 0.25), box.y2 - wy1 + int(box.h * 0.25)
    gx1, gx2 = box.x1 - wx1 - int(box.w * 0.25), box.x2 - wx1 + int(box.w * 0.25)
    inside = comp[max(0, gy1) : gy2, max(0, gx1) : gx2].sum()
    outside_frac = float(1.0 - inside / max(1, comp.sum()))
    return int(n - 1), float(areas.max() / crop.size), span, outside_frac


def _rule(box: Box, ruling: str) -> None:
    """Apply a customer ruling to a box some rule has singled out, boolean only.

    The reason code is appended by the caller either way, so the box is flagged for review whatever
    the ruling says. What the ruling settles is the boolean that rides along with it, per POLICY.md
    rule 5: "filled" and "empty" state an answer, "route" leaves the ink lean standing and lets the
    reason code speak. Confidence stays with the caller, because each rule caps it differently and
    those caps are what the published numbers were measured against.
    """
    if ruling == "filled":
        box.is_checked = True
    elif ruling == "empty":
        box.is_checked = False


def classify(page: Page, box: Box, policy: Policy | None = None) -> Box:
    pol = policy or policy_module.active()
    ink = ink_fraction(page, box)
    n, largest, span, outside = mark_stats(page, box) if ink > 0.01 else (0, 0.0, 0.0, 0.0)
    p = 1.0 / (1.0 + math.exp(-(ink - pol.ink_filled) / pol.confidence_scale))
    box.ink = round(ink, 4)
    box.is_checked = ink > pol.ink_filled
    box.confidence = round(abs(p - 0.5) * 2, 4)
    reasons: list[str] = list(box.reasons)  # keep witness-gate codes (MISSING_IN_DETECT, EXTRA_BOX)
    # dominance compares the largest mark to the total ink, not to the crop area: a thin X is
    # dominant at 20% ink, and comparing to the crop was exactly how clean X marks stayed "ambiguous"
    dominance = largest / ink if ink > 1e-6 else 0.0
    # span is measured inside the 15%-inset interior, whose own diagonal is 0.70 of the box's, so
    # 0.45 is a strong crossing; a threshold at 0.7 was unreachable by construction (measured X: 0.52)
    clear_mark = (
        span >= pol.clear_mark_span
        and dominance >= pol.clear_mark_dominance
        and ink > pol.clear_mark_ink
        and outside <= pol.stray_outside
    )
    if clear_mark:
        # one dominant stroke crossing the box: shape evidence settles what raw ink cannot
        box.is_checked = True
        box.confidence = max(box.confidence, 0.9)
    elif pol.ambiguous_low <= ink <= pol.ambiguous_high:
        reasons.append("INK_AMBIGUOUS")
    if box.is_checked and n >= pol.fragment_components and largest < pol.fragment_largest and ink < pol.fragment_ink_ceiling:
        # many small specks and no dominant stroke: text in a cell, or a box scribbled out
        reasons.append("FRAGMENTED_MARK")
        _rule(box, pol.scribbled_or_fragmented)
        box.confidence = min(box.confidence, 0.3)
    if not box.is_checked and span >= pol.thin_mark_span and ink > pol.thin_mark_ink:
        if outside > pol.stray_outside:
            # the stroke keeps going well past the box: handwriting passing through, not a selection
            reasons.append("STRAY_STROKE")
            _rule(box, pol.stray_stroke_through_box)
        else:
            # one thin contained stroke crossing the box: a tick or a light X
            reasons.append("THIN_MARK")
            if pol.thin_single_stroke == "filled":
                box.is_checked = True
                box.confidence = min(0.75, round(span, 2))
            else:
                # empty states the answer, route leaves the ink lean standing; both are unresolved
                # enough that the confidence has to come down and the reason code has to travel
                _rule(box, pol.thin_single_stroke)
                box.confidence = min(box.confidence, 0.4)
    if box.is_checked and outside > pol.stray_outside and ink < pol.fragment_ink_ceiling:
        reasons.append("STRAY_STROKE")
        _rule(box, pol.stray_stroke_through_box)
        box.confidence = min(box.confidence, 0.4)
    box.reasons = reasons
    return box
