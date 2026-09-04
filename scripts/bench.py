"""Async stress harness for the served API: latency percentiles and throughput per concurrency step.

Bench on a quiet machine and on the artifact that actually ships (the Docker image or `make serve`);
a box warmed by a training run reads 2x slow and the number is hygiene, not truth.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = ROOT / "data" / "samples" / "sample_1.jpg"


async def worker(client: httpx.AsyncClient, url: str, payload: bytes, name: str, n: int, times: list[float]) -> None:
    for _ in range(n):
        t0 = time.perf_counter()
        r = await client.post(url, files={"file": (name, payload, "image/jpeg")})
        r.raise_for_status()
        times.append((time.perf_counter() - t0) * 1000)


async def run_level(url: str, payload: bytes, name: str, total: int, concurrency: int) -> dict:
    times: list[float] = []
    async with httpx.AsyncClient(timeout=60) as client:
        t0 = time.perf_counter()
        per = max(1, total // concurrency)
        await asyncio.gather(*[worker(client, url, payload, name, per, times) for _ in range(concurrency)])
        wall = time.perf_counter() - t0
    times.sort()
    return {
        "concurrency": concurrency,
        "requests": len(times),
        "wall_s": round(wall, 2),
        "req_per_s": round(len(times) / wall, 1),
        "p50_ms": round(statistics.median(times), 1),
        "p95_ms": round(times[int(len(times) * 0.95) - 1], 1),
        "max_ms": round(times[-1], 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/detect")
    ap.add_argument("--image", default=str(DEFAULT_IMAGE))
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--concurrency", default="1,4,8")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()
    payload = Path(args.image).read_bytes()
    rows = []
    for c in [int(x) for x in args.concurrency.split(",")]:
        r = asyncio.run(run_level(args.url, payload, Path(args.image).name, args.n, c))
        rows.append(r)
        print(r)
    if args.report:
        # The report names the page relative to the repo, so a run from a different checkout path
        # produces the same file and a reader can find the page it timed.
        image = Path(args.image).resolve()
        shown = str(image.relative_to(ROOT)) if image.is_relative_to(ROOT) else args.image
        Path(args.report).write_text(json.dumps({"image": shown, "levels": rows}, indent=1))


if __name__ == "__main__":
    main()
