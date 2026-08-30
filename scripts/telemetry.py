"""Run the pipeline over every page in the repo and record what it did, page by page.

This exists because the eval reports only ever stored a count of flagged boxes, never a breakdown
of WHY they were flagged. "1.4% of boxes went to review" is a budget line. "Most of them were
INK_AMBIGUOUS on shaded rows" is something an operator can act on, and that is the difference
between a number and an instrument.

The corpus is 61 real pages: 52 synthetic ones built by damaging blank federal forms on purpose,
the 4 pages the brief supplied, and 5 completed appraisals from three offices that were never used
while building anything. Both classifier modes run, because the queues those two produce differ by
almost 10x and quoting one without the other is the flattering half.

Run: uv run python scripts/telemetry.py
Out: reports/telemetry.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import Counter
from pathlib import Path

import cv2

from hv_checkbox.escalate import ROUTED
from hv_checkbox.patch_model import load_scorer
from hv_checkbox.pipeline import detect_with_page, reset_template_cache

ROOT = Path(__file__).resolve().parent.parent
SYNTH = ROOT / "data" / "synth"
SAMPLES = ROOT / "data" / "samples"
HOLDOUT = ROOT / "data" / "holdout"

MODES = [("deterministic core only", "off"), ("deterministic core + patch classifier", "")]


def corpus() -> list[dict]:
    """Every page, tagged with where it came from and what was done to it."""
    pages: list[dict] = []

    manifest = {}
    mpath = SYNTH / "manifest.json"
    if mpath.exists():
        manifest = {p["name"]: p for p in json.loads(mpath.read_text())["pages"]}
    for sub in ("sweep", "mixed"):
        for png in sorted((SYNTH / sub).glob("*.png")):
            meta = manifest.get(png.stem, {})
            pages.append(
                {
                    "name": png.stem,
                    "path": png,
                    "corpus": f"synth-{sub}",
                    "form": meta.get("form"),
                    "factor": meta.get("factor"),
                    "level": meta.get("level"),
                }
            )

    for img in sorted(SAMPLES.iterdir()):
        if img.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            pages.append({"name": img.name, "path": img, "corpus": "sample", "form": None, "factor": "real", "level": None})

    for img in sorted(HOLDOUT.glob("*.png")):
        pages.append({"name": img.stem, "path": img, "corpus": "holdout", "form": None, "factor": "held-out", "level": None})

    return pages


def run_page(entry: dict) -> dict:
    img = cv2.imread(str(entry["path"]))
    if img is None:
        return {**{k: v for k, v in entry.items() if k != "path"}, "error": "unreadable"}
    t0 = time.perf_counter()
    _, boxes, meta = detect_with_page(img)
    elapsed = (time.perf_counter() - t0) * 1000.0

    reasons: Counter[str] = Counter()
    for b in boxes:
        reasons.update(b.reasons)
    rejected: Counter[str] = Counter()
    for r in meta.get("rejected", []):
        rejected.update(r["reasons"] or ["SIZE_CONSENSUS"])

    witness = meta.get("witness") or {}
    return {
        **{k: v for k, v in entry.items() if k != "path"},
        "boxes": len(boxes),
        "checked": sum(1 for b in boxes if b.is_checked),
        "flagged": sum(1 for b in boxes if b.reasons),
        "routed": sum(1 for b in boxes if any(r in ROUTED for r in b.reasons)),
        "reasons": dict(reasons),
        "rejected": dict(rejected),
        "elapsed_ms": round(elapsed, 1),
        "matched_form": meta.get("form"),
        "registration": meta.get("registration"),
        "witness_agree": witness.get("agree"),
        "witness_projected": witness.get("projected"),
        "trusted": witness.get("trusted"),
        "width": meta.get("width"),
        "height": meta.get("height"),
    }


def totals(pages: list[dict]) -> dict:
    ok = [p for p in pages if "error" not in p]
    boxes = sum(p["boxes"] for p in ok)
    flagged = sum(p["flagged"] for p in ok)
    reasons: Counter[str] = Counter()
    for p in ok:
        reasons.update(p["reasons"])
    ms = sorted(p["elapsed_ms"] for p in ok)
    return {
        "pages": len(ok),
        "boxes": boxes,
        "checked": sum(p["checked"] for p in ok),
        "flagged": flagged,
        "flag_rate": round(flagged / boxes, 4) if boxes else 0.0,
        "reasons": dict(reasons.most_common()),
        "p50_ms": round(statistics.median(ms), 1) if ms else 0.0,
        "p95_ms": round(ms[min(len(ms) - 1, int(len(ms) * 0.95))], 1) if ms else 0.0,
        "mean_ms": round(statistics.fmean(ms), 1) if ms else 0.0,
        "trusted_pages": sum(1 for p in ok if p.get("trusted")),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/telemetry.json")
    args = ap.parse_args()

    entries = corpus()
    print(f"{len(entries)} pages: " + ", ".join(f"{k}={v}" for k, v in Counter(e["corpus"] for e in entries).items()))
    if not any(e["corpus"].startswith("synth") for e in entries):
        print("note: data/synth is empty, so this run measures the sample pages only. Run `make synth` first to rebuild the damaged corpus the shipped telemetry.json was measured on.")

    # The second mode is published under a classifier label. load_scorer() returns None on any
    # load failure, and the pipeline then quietly runs rules-only, so without this check a fresh
    # environment without the train extra would ship rules-only numbers labeled as the classifier.
    if load_scorer() is None:
        raise SystemExit("patch classifier unavailable: run `make telemetry` (uses --extra train) so onnxruntime and models/patch-int8.onnx can load")

    result: dict = {"corpus_size": len(entries), "modes": {}}
    for label, env in MODES:
        if env:
            os.environ["HV_CLASSIFIER"] = env
        else:
            os.environ.pop("HV_CLASSIFIER", None)
        reset_template_cache()
        print(f"\n{label}")
        pages = []
        for i, e in enumerate(entries, 1):
            pages.append(run_page(e))
            if i % 15 == 0 or i == len(entries):
                print(f"  {i}/{len(entries)}")
        t = totals(pages)
        result["modes"][label] = {"pages": pages, "totals": t}
        print(f"  {t['boxes']} boxes, {t['flagged']} flagged ({t['flag_rate'] * 100:.1f}%), p50 {t['p50_ms']} ms")
        print(f"  reasons: {t['reasons']}")

    Path(args.out).write_text(json.dumps(result, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
