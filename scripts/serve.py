"""HTTP API: POST /detect returns the required schema; optional explain and overlay views for debugging."""

from __future__ import annotations

import time

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from hv_checkbox.overlay import draw
from hv_checkbox.pipeline import detect_with_page

app = FastAPI(title="hv-checkbox", version="0.1.0")


class BoxOut(BaseModel):
    bbox: list[int]
    is_checked: bool


class DetectOut(BaseModel):
    boxes: list[BoxOut]


def _decode(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if img is None or img.size == 0:
        raise HTTPException(status_code=400, detail="file is not a decodable image")
    return img


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/detect")
async def detect(file: UploadFile = File(...), explain: bool = Query(False), escalate: bool = Query(False)) -> JSONResponse:
    t0 = time.perf_counter()
    img = _decode(await file.read())
    page, boxes, meta = detect_with_page(img)
    if escalate:
        from hv_checkbox.escalate import Escalator, enabled

        if enabled():
            meta["escalated"] = Escalator().route(page, boxes, source=file.filename or "upload")
        else:
            meta["escalated"] = "disabled (set HV_ESCALATE=1 and provide an Anthropic credential)"
    if not explain:
        return JSONResponse({"boxes": [{"bbox": b.bbox, "is_checked": bool(b.is_checked)} for b in boxes]})
    return JSONResponse(
        {
            "boxes": [
                {
                    "bbox": b.bbox,
                    "is_checked": bool(b.is_checked),
                    "confidence": b.confidence,
                    "ink": b.ink,
                    "reasons": b.reasons,
                    "witnesses": b.witnesses,
                }
                for b in boxes
            ],
            "meta": {
                "width": int(img.shape[1]),
                "height": int(img.shape[0]),
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                **meta,
            },
        }
    )


@app.post("/detect/overlay")
async def detect_overlay(file: UploadFile = File(...)) -> Response:
    img = _decode(await file.read())
    page, boxes, _ = detect_with_page(img)
    ok, buf = cv2.imencode(".png", draw(page.image, boxes))
    if not ok:
        raise HTTPException(status_code=500, detail="could not encode overlay")
    return Response(content=buf.tobytes(), media_type="image/png")
