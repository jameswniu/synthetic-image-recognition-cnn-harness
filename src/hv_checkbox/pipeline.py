"""The single entry point: image in, classified boxes out, with the two-witness merge when a golden form matches."""

from __future__ import annotations

import cv2
import numpy as np

from hv_checkbox.classify import classify
from hv_checkbox.detect import detect_boxes
from hv_checkbox.normalize import Page, load_page
from hv_checkbox.patch_model import apply_model, load_scorer
from hv_checkbox.template import load_templates, place, register
from hv_checkbox.types import Box

_TEMPLATES: list | None = None
_SCORER: object = "unset"


def _templates() -> list:
    global _TEMPLATES
    if _TEMPLATES is None:
        try:
            _TEMPLATES = load_templates()
        except Exception:
            _TEMPLATES = []
    return _TEMPLATES


def _scorer():
    global _SCORER
    if _SCORER == "unset":
        _SCORER = load_scorer()
    return _SCORER


def reset_template_cache() -> None:
    global _TEMPLATES, _SCORER
    _TEMPLATES = None
    _SCORER = "unset"


MIN_WIDTH = 1400  # below this, borders thin out and break; process at 2x and report original coordinates


def detect_with_page(image: np.ndarray, use_template: bool = True) -> tuple[Page, list[Box], dict]:
    original = image
    upscale = 1
    if image.shape[1] < MIN_WIDTH:
        upscale = 2
        image = cv2.resize(image, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)
    page = load_page(image)
    rejects: list = []
    boxes = detect_boxes(page, rejects=rejects)
    meta: dict = {"form": None, "registration": None, "witness": None}
    if use_template and (ts := _templates()):
        reg = register(page, ts)
        if reg is not None:
            t = next(x for x in ts if x.name == reg.form)
            boxes, stats = place(reg, t, boxes, page.box_side)
            meta.update({"form": reg.form, "registration": reg.score, "witness": stats})
    out = [classify(page, b) for b in boxes]
    if (scorer := _scorer()) is not None:
        apply_model(page, out, scorer)
    if upscale > 1:
        for b in (*out, *rejects):
            b.x1, b.y1, b.x2, b.y2 = b.x1 // upscale, b.y1 // upscale, b.x2 // upscale, b.y2 // upscale
        page.image = original
        meta["upscaled"] = upscale
    # Serialised last, and after the downscale above, so a rejected candidate is quoted in the same
    # coordinates as the boxes it sits beside. An audit trail pointing at the wrong region is worse
    # than none, because it reads as evidence.
    meta["rejected"] = [{"bbox": b.bbox, "reasons": b.reasons} for b in rejects]
    return page, out, meta


def detect_checkboxes(image: np.ndarray) -> list[Box]:
    return detect_with_page(image)[1]
