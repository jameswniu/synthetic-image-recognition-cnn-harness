"""Witness B: golden-form projection via monotone line matching.

Uniform scaling cannot align two vendors' renderings of the same form: measured on the photo
sample, per-section vertical offsets range from -133 to +396 px under the best global fit, because
vendors re-flow section heights independently. What survives the re-flow is the order and character
of the ruling lines (long section separators, short row lines) and, within a row, the order of the
boxes. So alignment is correspondence, not scaling: a dynamic-programming alignment of the
horizontal-line sequences gives a piecewise-linear vertical map, each mapped row matches its boxes
to detected boxes in order, and only rows with matched support may place template-only boxes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from hv_checkbox.normalize import Page
from hv_checkbox.types import Box

GOLDEN_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "golden"
MIN_MATCH = 0.35  # matched fraction of line peaks below which the page is not this form


@dataclass
class Template:
    name: str
    peaks_y: list[tuple[float, float]]
    boxes: list[list[int]]
    width: int
    height: int


@dataclass
class Registration:
    form: str
    score: float
    knots: list[tuple[float, float]]  # (template_y, page_y) matched line pairs


def line_profile(ink: np.ndarray) -> np.ndarray:
    w = ink.shape[1]
    longh = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, int(w * 0.15)), 1)))
    return (longh > 0).sum(1).astype(np.float64)


def peaks(profile: np.ndarray, min_frac: float = 0.2, min_gap: int = 8) -> list[tuple[float, float]]:
    """Cluster a line-position profile into (position, weight) peaks; weight is the line length."""
    thr = max(float(profile.max()) * min_frac, 1.0)
    out: list[tuple[float, float]] = []
    i, n = 0, len(profile)
    while i < n:
        if profile[i] >= thr:
            j = i
            while j < n and profile[j] >= thr:
                j += 1
            pos, w = (i + j - 1) / 2.0, float(profile[i:j].max())
            if out and pos - out[-1][0] < min_gap:
                if w > out[-1][1]:
                    out[-1] = (pos, w)
            else:
                out.append((pos, w))
            i = j
        else:
            i += 1
    return out


def align_peaks(tp: list[tuple[float, float]], pp: list[tuple[float, float]], lookback: int = 4, skip_cost: float = 0.3) -> list[tuple[int, int]]:
    """Monotone local alignment of two line sequences. Returns matched (template_idx, page_idx) pairs."""
    m, n = len(tp), len(pp)
    if m < 2 or n < 2:
        return []
    NEG = -1e9
    dp = np.full((m, n), NEG)
    bk = np.full((m, n, 2), -1, dtype=int)

    def wsim(a: float, b: float) -> float:
        return min(a, b) / max(a, b)

    for i in range(m):
        for j in range(n):
            base = wsim(tp[i][1], pp[j][1])
            dp[i, j] = base  # a local path may start anywhere
            for pi in range(max(0, i - lookback), i):
                for pj in range(max(0, j - lookback), j):
                    if dp[pi, pj] <= NEG / 2:
                        continue
                    dt, dpg = tp[i][0] - tp[pi][0], pp[j][0] - pp[pj][0]
                    if dt <= 0 or dpg <= 0:
                        continue
                    r = dpg / dt
                    if not (0.45 <= r <= 2.2):
                        continue
                    cand = dp[pi, pj] + base - skip_cost * ((i - pi - 1) + (j - pj - 1))
                    if cand > dp[i, j]:
                        dp[i, j] = cand
                        bk[i, j] = (pi, pj)
    i, j = np.unravel_index(int(dp.argmax()), dp.shape)
    pairs: list[tuple[int, int]] = []
    while i >= 0 and j >= 0:
        pairs.append((int(i), int(j)))
        i, j = bk[i, j]
    return pairs[::-1]


def load_templates(golden_dir: Path = GOLDEN_DIR) -> list[Template]:
    out = []
    for png in sorted(golden_dir.glob("*.png")):
        cache = png.with_suffix(".boxes.json")
        if not cache.exists():
            continue
        img = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
        ink = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, max(15, int(img.shape[1] * 0.012)) | 1, 15)
        out.append(Template(png.stem, peaks(line_profile(ink)), json.loads(cache.read_text())["boxes"], img.shape[1], img.shape[0]))
    return out


def register(page: Page, templates: list[Template]) -> Registration | None:
    pk = peaks(line_profile(page.ink))
    best: Registration | None = None
    for t in templates:
        pairs = align_peaks(t.peaks_y, pk)
        if len(pairs) < 3:
            continue
        score = len(pairs) / max(3, min(len(t.peaks_y), len(pk)))
        knots = []
        for i, j in pairs:
            if not knots or (t.peaks_y[i][0] > knots[-1][0] and pk[j][0] > knots[-1][1]):
                knots.append((t.peaks_y[i][0], pk[j][0]))
        if len(knots) >= 3 and (best is None or score > best.score):
            best = Registration(t.name, round(float(score), 3), knots)
    if best is None or best.score < MIN_MATCH:
        return None
    return best


def apply_map(knots: list[tuple[float, float]], y: float) -> float:
    tx = np.array([k[0] for k in knots])
    px = np.array([k[1] for k in knots])
    if y <= tx[0]:
        slope = (px[1] - px[0]) / max(1.0, tx[1] - tx[0])
        return float(px[0] + (y - tx[0]) * slope)
    if y >= tx[-1]:
        slope = (px[-1] - px[-2]) / max(1.0, tx[-1] - tx[-2])
        return float(px[-1] + (y - tx[-1]) * slope)
    return float(np.interp(y, tx, px))


def _rows(boxes: list[list[int]], side: float) -> list[list[list[int]]]:
    rows: list[list[list[int]]] = []
    for b in sorted(boxes, key=lambda b: ((b[1] + b[3]) / 2, b[0])):
        cy = (b[1] + b[3]) / 2
        if rows and abs(cy - (rows[-1][0][1] + rows[-1][0][3]) / 2) < side * 0.8:
            rows[-1].append(b)
        else:
            rows.append([b])
    return [sorted(r, key=lambda b: b[0]) for r in rows]


def _match_row(trow: list[list[int]], band: list[Box]) -> list[tuple[int, int]]:
    """Order-preserving match of template boxes to detected boxes in one row band."""
    m, n = len(trow), len(band)
    if m == 0 or n == 0:
        return []
    if m == n:
        return [(i, i) for i in range(m)]
    NEG = -1e9
    dp = np.full((m, n), NEG)
    bk = np.full((m, n, 2), -1, dtype=int)
    for i in range(m):
        for j in range(n):
            dp[i, j] = 1.0
            for pi in range(max(0, i - 3), i):
                for pj in range(max(0, j - 3), j):
                    if dp[pi, pj] <= NEG / 2:
                        continue
                    dt = (trow[i][0] - trow[pi][0])
                    dg = (band[j].x1 - band[pj].x1)
                    if dt <= 0 or dg <= 0:
                        continue
                    r = dg / dt
                    if not (0.4 <= r <= 2.5):
                        continue
                    cand = dp[pi, pj] + 1.0 - 0.3 * ((i - pi - 1) + (j - pj - 1))
                    if cand > dp[i, j]:
                        dp[i, j] = cand
                        bk[i, j] = (pi, pj)
    i, j = np.unravel_index(int(dp.argmax()), dp.shape)
    pairs = []
    while i >= 0 and j >= 0:
        pairs.append((int(i), int(j)))
        i, j = bk[i, j]
    return pairs[::-1]


def place(reg: Registration, template: Template, detected: list[Box], side: int, min_agree: float = 0.75) -> tuple[list[Box], dict]:
    """Match template boxes to detections row by row; add row-supported template-only boxes when trusted."""
    stats = {"projected": len(template.boxes), "agree": 0, "template_only": 0, "detect_only": 0, "trusted": False}
    matched_ids: set[int] = set()
    extras: list[Box] = []
    for trow in _rows(template.boxes, side / max(1e-6, _row_scale(reg))):
        cy_t = float(np.mean([(b[1] + b[3]) / 2 for b in trow]))
        cy_p = apply_map(reg.knots, cy_t)
        if cy_p < -side or cy_p > 10**7:
            continue
        band = sorted((d for d in detected if abs(d.cy - cy_p) < side * 0.55 and id(d) not in matched_ids), key=lambda d: d.x1)
        pairs = _match_row(trow, band)
        for i, j in pairs:
            matched_ids.add(id(band[j]))
            if "template" not in band[j].witnesses:
                band[j].witnesses = band[j].witnesses + ["template"]
            stats["agree"] += 1
        # extrapolate a missing box only when the row is otherwise fully explained: every detected
        # box in the band matched. A row that disagrees with the template is routed, not padded.
        if len(pairs) >= 2 and len(pairs) < len(trow) and len(pairs) == len(band):
            a = np.polyfit([trow[i][0] for i, _ in pairs], [band[j].x1 for _, j in pairs], 1)
            for i, tb in enumerate(trow):
                if any(i == pi for pi, _ in pairs):
                    continue
                x1 = float(np.polyval(a, tb[0]))
                w = (tb[2] - tb[0]) * float(a[0])
                h = w / max(0.5, (tb[2] - tb[0]) / (tb[3] - tb[1]))
                box = Box(int(x1), int(cy_p - h / 2), int(x1 + w), int(cy_p + h / 2), witnesses=["template"])
                box.reasons = ["MISSING_IN_DETECT"]
                extras.append(box)
    rate = stats["agree"] / len(template.boxes) if template.boxes else 0.0
    stats["trusted"] = rate >= min_agree
    out = list(detected)
    if stats["trusted"]:
        good = [e for e in extras if e.w > 3 and e.h > 3]
        out += good
        stats["template_only"] = len(good)
        for d in detected:
            if id(d) not in matched_ids:
                d.reasons = d.reasons + ["EXTRA_BOX"]
                stats["detect_only"] += 1
    return sorted(out, key=lambda b: (b.y1, b.x1)), stats


def _row_scale(reg: Registration) -> float:
    t0, p0 = reg.knots[0]
    t1, p1 = reg.knots[-1]
    return (p1 - p0) / max(1.0, t1 - t0)
