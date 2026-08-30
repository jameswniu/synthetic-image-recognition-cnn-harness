"""Bounded non-deterministic lane: VLM voters on routed crops, a judge on disputes, everything recorded.

Only boxes the deterministic pipeline routed (ambiguous ink, fragmented marks, stray strokes,
classifier disagreement, template-only finds) ever reach this lane, and only when it is switched on
(HV_ESCALATE=1 plus an Anthropic credential). Two voters of different tiers read the crop blind;
agreement decides with VLM_AGREE. A dispute goes to a stronger judge with the crop, both votes, and
the deterministic evidence; low judge confidence leaves the deterministic answer standing and tags
REVIEW. Every call is recorded in data/judge_votes.json keyed by crop hash, and replays are served
from the record, so the offline behavior is deterministic and the exam is auditable.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

import cv2

from hv_checkbox.normalize import Page
from hv_checkbox.types import Box

VOTES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "judge_votes.json"
ROUTED = {"INK_AMBIGUOUS", "FRAGMENTED_MARK", "STRAY_STROKE", "THIN_MARK", "CLASSIFIER_DISAGREE", "MISSING_IN_DETECT", "EXTRA_BOX"}
VOTERS = ["claude-haiku-4-5", "claude-sonnet-5"]
JUDGE = "claude-opus-5"

VOTER_PROMPT = (
    "This is a zoomed crop from a scanned mortgage appraisal form. The magenta rectangle outlines one "
    "square. Decide two things about that square only. First, is it a checkbox at all (a letter's hole, "
    "a table cell, or a rendering artifact is not). Second, if it is a checkbox, did someone mean to "
    "select it: any intentional mark counts (X, tick, solid fill, circle), stray ink merely passing "
    "through does not. Reply with only JSON: "
    '{"is_checkbox": true|false, "filled": true|false|null, "confidence": 0.0 to 1.0, "why": "under 15 words"}'
)


def enabled() -> bool:
    return os.environ.get("HV_ESCALATE", "") == "1"


def crop_png(page: Page, box: Box) -> bytes:
    gx, gy = int(box.w * 2.2), int(box.h * 2.2)
    x1, y1 = max(0, box.x1 - gx), max(0, box.y1 - gy)
    x2, y2 = min(page.width, box.x2 + gx), min(page.height, box.y2 + gy)
    crop = page.image[y1:y2, x1:x2].copy()
    scale = max(1.0, 260.0 / max(1, box.w * 5))
    crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.rectangle(
        crop,
        (int((box.x1 - x1) * scale) - 3, int((box.y1 - y1) * scale) - 3),
        (int((box.x2 - x1) * scale) + 3, int((box.y2 - y1) * scale) + 3),
        (255, 0, 255),
        2,
    )
    ok, buf = cv2.imencode(".png", crop)
    return buf.tobytes()


def _parse(text: str) -> dict | None:
    try:
        start, end = text.index("{"), text.rindex("}") + 1
        d = json.loads(text[start:end])
        return {"is_checkbox": bool(d.get("is_checkbox")), "filled": d.get("filled"), "confidence": float(d.get("confidence", 0.5)), "why": str(d.get("why", ""))[:120]}
    except Exception:
        return None


class Escalator:
    def __init__(self, votes_path: Path = VOTES_PATH, live: bool | None = None):
        self.votes_path = votes_path
        self.record: dict = json.loads(votes_path.read_text()) if votes_path.exists() else {}
        self.live = enabled() if live is None else live
        self._client = None

    def client(self):
        if self._client is None:
            import anthropic  # optional extra; the deterministic path never imports this

            self._client = anthropic.Anthropic()
        return self._client

    def _ask(self, model: str, png: bytes, prompt: str, max_tokens: int = 400) -> dict | None:
        msg = self.client().messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.standard_b64encode(png).decode()}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        if msg.stop_reason == "refusal":
            return None
        text = next((b.text for b in msg.content if b.type == "text"), "")
        return _parse(text)

    def decide(self, page: Page, box: Box, source: str) -> dict | None:
        png = crop_png(page, box)
        key = hashlib.sha1(png).hexdigest()[:16]
        if key in self.record:
            return self.record[key]["final"] | {"replayed": True}
        if not self.live:
            return None
        votes = []
        for model in VOTERS:
            v = self._ask(model, png, VOTER_PROMPT)
            if v is not None:
                votes.append({"model": model, **v})
        entry: dict = {
            "source": source,
            "bbox": box.bbox,
            "evidence": {"ink": box.ink, "reasons": box.reasons, "witnesses": box.witnesses},
            "votes": votes,
            "judge": None,
        }
        final: dict | None = None
        if len(votes) == 2 and votes[0]["is_checkbox"] == votes[1]["is_checkbox"] and votes[0]["filled"] == votes[1]["filled"] and votes[0]["filled"] is not None:
            final = {"is_checkbox": votes[0]["is_checkbox"], "filled": votes[0]["filled"], "route": "VLM_AGREE", "confidence": round(min(v["confidence"] for v in votes), 2)}
        elif votes:
            judge_prompt = (
                VOTER_PROMPT
                + "\n\nTwo readers disagreed. Their votes: "
                + json.dumps([{k: v[k] for k in ("model", "is_checkbox", "filled", "confidence", "why")} for v in votes])
                + "\nDeterministic evidence for the same square: "
                + json.dumps(entry["evidence"])
                + '\nAdjudicate. Reply with only JSON: {"is_checkbox": true|false, "filled": true|false, "confidence": 0.0 to 1.0, "why": "under 20 words"}'
            )
            j = self._ask(JUDGE, png, judge_prompt, max_tokens=2000)
            entry["judge"] = j
            if j is not None and j["confidence"] >= 0.6:
                final = {"is_checkbox": j["is_checkbox"], "filled": j["filled"], "route": "JUDGED", "confidence": j["confidence"]}
        if final is None:
            final = {"is_checkbox": True, "filled": bool(box.is_checked), "route": "REVIEW", "confidence": box.confidence}
        entry["final"] = final
        self.record[key] = entry
        self.votes_path.parent.mkdir(parents=True, exist_ok=True)
        self.votes_path.write_text(json.dumps(self.record, indent=1))
        return final

    def route(self, page: Page, boxes: list[Box], source: str = "upload") -> int:
        touched = 0
        for b in boxes:
            if not (set(b.reasons) & ROUTED):
                continue
            final = self.decide(page, b, source)
            if final is None:
                continue
            touched += 1
            if not final["is_checkbox"]:
                b.reasons = b.reasons + ["NOT_A_CHECKBOX", final["route"]]
                b.confidence = min(b.confidence, 0.3)
                continue
            if final["filled"] is not None and final["route"] in {"VLM_AGREE", "JUDGED"}:
                b.is_checked = bool(final["filled"])
                b.confidence = max(b.confidence, float(final["confidence"]))
            b.reasons = b.reasons + [final["route"]]
        return touched


def main() -> None:
    import argparse

    from hv_checkbox.pipeline import detect_with_page

    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--live", action="store_true", help="allow real API calls (else replay-only)")
    args = ap.parse_args()
    img = cv2.imread(args.image)
    page, boxes, meta = detect_with_page(img)
    esc = Escalator(live=args.live or enabled())
    n = esc.route(page, boxes, source=Path(args.image).name)
    routed = [b for b in boxes if set(b.reasons) & (ROUTED | {"VLM_AGREE", "JUDGED", "REVIEW"})]
    print(f"{args.image}: {len(boxes)} boxes, {len(routed)} routed, {n} escalated (live={esc.live})")
    for b in routed:
        print(f"  {b.bbox} checked={b.is_checked} conf={b.confidence} ink={b.ink} reasons={b.reasons}")


if __name__ == "__main__":
    main()
