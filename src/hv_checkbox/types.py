"""Shared value types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Box:
    """One checkbox in original image pixel coordinates (x1, y1, x2, y2 inclusive-exclusive)."""

    x1: int
    y1: int
    x2: int
    y2: int
    is_checked: bool = False
    confidence: float = 0.0
    ink: float = 0.0
    reasons: list[str] = field(default_factory=list)
    witnesses: list[str] = field(default_factory=list)

    @property
    def bbox(self) -> list[int]:
        return [int(self.x1), int(self.y1), int(self.x2), int(self.y2)]

    @property
    def w(self) -> int:
        return self.x2 - self.x1

    @property
    def h(self) -> int:
        return self.y2 - self.y1

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2


def iou(a: Box, b: Box) -> float:
    ix1, iy1 = max(a.x1, b.x1), max(a.y1, b.y1)
    ix2, iy2 = min(a.x2, b.x2), min(a.y2, b.y2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union else 0.0
