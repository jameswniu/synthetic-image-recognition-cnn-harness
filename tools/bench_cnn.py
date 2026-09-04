"""Time the shipped CNN on the real crops: reports/cnn_latency.json.

This is the only CNN timing the repo quotes, and it is measured rather than typed. The script loads
models/patch-int8.onnx exactly as the pipeline does (PatchScorer, the same pooled Scan sessions),
runs the rules pass once per brief page to get that page's boxes, then times scorer.score() alone
over those boxes: a few warm-up passes, then repeated timed passes, per page. Per crop is the page
time divided by the page's box count. The report names the machine, the worker count, the box
counts and the repeat count, so a laptop number and a server number cannot be confused for each
other. CI never chases this file, because a timing is a property of the box it ran on.

Run: make bench-cnn  (uv run --extra train python tools/bench_cnn.py)
Out: reports/cnn_latency.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess


def _sysctl(key: str) -> str:
    """One sysctl value, or empty off macOS, so the report names the box it ran on."""
    try:
        return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402

SAMPLES = ROOT / "data" / "samples"


def percentile(values: list[float], q: float) -> float:
    """The same rule scripts/telemetry.py uses: the sorted element at q times n, capped at the last."""
    s = sorted(values)
    return s[min(len(s) - 1, int(len(s) * q))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=30, help="timed passes per page")
    ap.add_argument("--warmups", type=int, default=5, help="untimed passes per page before the clock starts")
    ap.add_argument("--out", default="reports/cnn_latency.json")
    args = ap.parse_args()

    # The rules pass supplies the boxes; the model is loaded separately below so the timing covers
    # scoring alone, never detection.
    os.environ["HV_CLASSIFIER"] = "off"
    from hv_checkbox.pipeline import detect_with_page

    pages = []
    for img_path in sorted(SAMPLES.iterdir()):
        if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        img = cv2.imread(str(img_path))
        page, boxes, _ = detect_with_page(img)
        pages.append((img_path.name, page, boxes))

    os.environ.pop("HV_CLASSIFIER", None)
    import onnxruntime as ort
    from hv_checkbox.patch_model import MODEL_PATH, POOL_WORKERS, PatchScorer

    scorer = PatchScorer(MODEL_PATH)

    rows = []
    for name, page, boxes in pages:
        for _ in range(args.warmups):
            scorer.score(page, boxes)
        times = []
        for _ in range(args.repeats):
            t0 = time.perf_counter()
            scorer.score(page, boxes)
            times.append((time.perf_counter() - t0) * 1000.0)
        median = statistics.median(times)
        rows.append({
            "page": name,
            "boxes": len(boxes),
            "median_ms": round(median, 2),
            "p95_ms": round(percentile(times, 0.95), 2),
            "min_ms": round(min(times), 2),
            "us_per_crop": round(1000.0 * median / len(boxes), 1) if boxes else None,
        })
        print(f"{name:14s} {len(boxes):4d} boxes  median {median:7.2f} ms  p95 {percentile(times, 0.95):7.2f} ms  "
              f"{1000.0 * median / max(1, len(boxes)):6.1f} us per crop")

    total_boxes = sum(r["boxes"] for r in rows)
    all_pages_ms = sum(r["median_ms"] for r in rows)
    report = {
        "model": str(MODEL_PATH.relative_to(ROOT)),
        "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
        "what": "scorer.score() over the rules pass's boxes on each brief page, in-process, scoring only",
        "repeats": args.repeats,
        "warmups": args.warmups,
        "pool_workers": POOL_WORKERS,
        "machine": {
            "system": platform.system(),
            "release": platform.mac_ver()[0] or platform.release(),
            "machine": platform.machine(),
            "model": _sysctl("hw.model"),
            "cpu": _sysctl("machdep.cpu.brand_string"),
            "cpu_count": os.cpu_count(),
            "python": platform.python_version(),
            "onnxruntime": ort.__version__,
        },
        "pages": rows,
        "totals": {
            "boxes": total_boxes,
            "all_four_pages_ms": round(all_pages_ms, 2),
            "us_per_crop": round(1000.0 * all_pages_ms / total_boxes, 1) if total_boxes else None,
        },
    }
    out = ROOT / args.out
    out.write_text(json.dumps(report, indent=1))
    print(f"wrote {args.out}: {total_boxes} crops in {all_pages_ms:.1f} ms across the four pages, "
          f"{report['totals']['us_per_crop']} us per crop, {POOL_WORKERS} workers")


if __name__ == "__main__":
    main()
