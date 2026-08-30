"""Page normalization: luminance binarization and checkbox size estimation.

Colour is deliberately not used for structure. The red watermark on one of the
samples overwrites box borders, and a saturation-gated mask cuts gaps in them;
luminance keeps the border and the h/v opening removes the diagonal text anyway.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Page:
    image: np.ndarray  # BGR, original
    gray: np.ndarray
    ink: np.ndarray  # 255 where dark
    box_side: int  # estimated checkbox side in px

    @property
    def width(self) -> int:
        return self.image.shape[1]

    @property
    def height(self) -> int:
        return self.image.shape[0]


def binarize(gray: np.ndarray, block: int = 31, c: int = 15) -> np.ndarray:
    block = max(3, block | 1)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block, c)


def enclosed_holes(
    lines: np.ndarray, lo: int, hi: int, min_fill: float = 0.8, aspect: tuple[float, float] = (0.78, 1.4)
) -> list[tuple[int, int, int, int]]:
    """Connected components of the background enclosed by line structure, filtered to square-ish holes.

    The aspect floor of 0.78 is load-bearing: the narrow first-column cells on the 1004MC addendum
    measure ~41x54 (0.76) while every real checkbox across the samples sits between 1.0 and 1.26.
    """
    n, _, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(lines), connectivity=4)
    out = []
    for i in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[i])
        if lo <= w <= hi and lo <= h <= hi and aspect[0] <= w / h <= aspect[1] and area / (w * h) > min_fill:
            out.append((x, y, w, h))
    return out


def open_lines(ink: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    k = max(3, int(k))
    h = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (k, 1)))
    v = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, k)))
    return h, v


def estimate_box_side(ink: np.ndarray, width: int) -> int:
    """Pass one of the two-pass size estimate: open with a small kernel, take the mode of hole sizes.

    The vote is restricted to holes of 0.8% to 2.5% of the page width. Letter holes ("o", "e") sit
    around 0.5 to 0.6% at every render scale, and letting them vote is exactly how the estimator
    collapsed on a 0.4x downscale (the sweep caught F1 dropping to 0.55 before this floor existed).
    Falls back to 1.2% of the page width when the page has too few holes to vote.
    """
    h, v = open_lines(ink, width * 0.005)
    lines = cv2.bitwise_or(h, v)
    holes = enclosed_holes(lines, int(width * 0.008), int(width * 0.025))
    if len(holes) < 5:
        return max(8, int(width * 0.012))
    sides = np.array([max(w, hh) for _, _, w, hh in holes])
    hist, edges = np.histogram(sides, bins=np.arange(sides.min(), sides.max() + 3, 2))
    mode = edges[int(hist.argmax())] + 1
    return int(max(8, mode))


def load_page(image: np.ndarray) -> Page:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    width = image.shape[1]
    ink = binarize(gray, block=max(15, int(width * 0.012)) | 1, c=15)
    side = estimate_box_side(ink, width)
    return Page(image=image, gray=gray, ink=ink, box_side=side)
