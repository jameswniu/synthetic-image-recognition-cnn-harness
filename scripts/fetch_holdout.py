"""Fetch the held-out pages: filled sample appraisals published by working appraisers.

These are public demo reports with fictional borrowers, produced by three unrelated appraisal
offices on a la mode's TOTAL software. None of them was seen while building or tuning anything
here, which is the point: the four pages in data/samples came with the brief, so they cannot
answer whether this generalizes.

Run: uv run python scripts/fetch_holdout.py && uv run python scripts/fetch_holdout.py --score
"""

from __future__ import annotations

import argparse
import subprocess
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "holdout"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# (local name, url, the page number that carries the form grid)
PAGES = [
    ("piekos-fha-1004", "https://piekos.appraiserxsites.com/xSites/Appraisers/piekos/Content/UploadedFiles/FHA_1004_DEMO.pdf", 1),
    ("piekos-va-1004", "https://piekos.appraiserxsites.com/xSites/Appraisers/piekos/Content/UploadedFiles/VA_1004_DEMO.pdf", 1),
    ("piekos-condo-1073", "https://piekos.appraiserxsites.com/xSites/Appraisers/piekos/Content/UploadedFiles/CONV_1073_DEMO.pdf", 1),
    ("realvals-1004", "https://realvals.com/wp-content/uploads/2019/04/1004_Appraisal_Report_Sample.pdf", 3),
    ("keyrealty-fha-1004", "https://www.keyrealtyandappraisal.com/xsites/appraisers/keyrealty/content/uploadedfiles/sample%20appraisal%20fha%2082009.pdf", 4),
]


def download(url: str, dest: Path) -> None:
    """Fetch one PDF. Falls back to curl, because one of these hosts serves an incomplete
    certificate chain: it sends the leaf without the intermediate. System TLS tolerates that
    and Python's ssl module does not, so a pure-urllib fetcher fails on a server that browsers
    and curl load without complaint."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
    except Exception as e:
        print(f"  urllib failed ({type(e).__name__}), retrying with curl")
        subprocess.run(["curl", "-sSL", "-A", UA, "-o", str(dest), url], check=True)


def fetch() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, url, page in PAGES:
        pdf = OUT / f"{name}.pdf"
        try:
            if not pdf.exists():
                download(url, pdf)
                print(f"downloaded {pdf.name}")
            stem = OUT / f"{name}-p{page}"
            if not list(OUT.glob(f"{name}-p{page}*.png")):
                subprocess.run(["pdftoppm", "-r", "300", "-png", "-f", str(page), "-l", str(page), str(pdf), str(stem)], check=True)
                print(f"rendered {stem.name}")
        except Exception as e:
            failed.append((name, f"{type(e).__name__}: {e}"))
            pdf.unlink(missing_ok=True)
    for name, why in failed:
        print(f"could not fetch {name}: {why}")
    if failed:
        print("These are third-party sites and any of them may move or go offline; the rest still score.")


def score() -> None:
    import cv2

    from hv_checkbox.escalate import ROUTED
    from hv_checkbox.pipeline import _scorer, detect_with_page

    # State the mode. The flag column moves a lot between the two, so a table that does not say
    # which one produced it is a table you cannot check against the README.
    print("mode: " + ("deterministic core + patch classifier" if _scorer() is not None else "deterministic core only"))
    print(f"{'page':26s} {'boxes':>5s} {'marked':>6s} {'flagged':>7s} {'form recognized':>16s}")
    for png in sorted(OUT.glob("*.png")):
        _, boxes, meta = detect_with_page(cv2.imread(str(png)))
        w = meta.get("witness") or {}
        known = "yes" if w.get("trusted") else "no, read without one"
        flagged = sum(1 for b in boxes if set(b.reasons) & ROUTED)
        print(f"{png.stem[:26]:26s} {len(boxes):5d} {sum(b.is_checked for b in boxes):6d} {flagged:7d} {known:>16s}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true")
    args = ap.parse_args()
    fetch()
    if args.score:
        score()
