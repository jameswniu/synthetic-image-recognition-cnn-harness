"""Draw detections on a page for debugging and for the docs."""

from __future__ import annotations

import cv2
import numpy as np

from hv_checkbox.types import Box

GREEN = (0, 170, 0)
RED = (0, 0, 220)
AMBER = (0, 160, 255)


def draw(image: np.ndarray, boxes: list[Box], thickness: int | None = None, labels: bool = False) -> np.ndarray:
    out = image.copy()
    t = thickness or max(2, image.shape[1] // 900)
    for b in boxes:
        colour = AMBER if b.reasons else (GREEN if b.is_checked else RED)
        cv2.rectangle(out, (b.x1, b.y1), (b.x2, b.y2), colour, t)
        if labels:
            cv2.putText(out, f"{b.ink:.2f}", (b.x1, max(0, b.y1 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, colour, 1, cv2.LINE_AA)
    return out
