"""Photograph the dashboard for the README: assets/dashboard-preview.png.

The preview is a screenshot of the real deliverables/dashboard.html, taken by offscreen headless
chromium, never a mock-up, so the README's picture cannot drift from the deliverable. The crop is
the operator's first screenful of substance: the KPI band and the two panels below it.

The tool also refuses its own output if any pixel of a retired accent palette survives in it.
That is the leak this file exists to close: the preview was a manual screenshot, so it kept
advertising the old theme for days after the dashboard itself moved on. A generated preview can
still go stale in the repo, but it can never be regenerated wrong.

Run: make preview  (depends on `make dashboard`, so the page is fresh when photographed)
Out: assets/dashboard-preview.png
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "deliverables" / "dashboard.html"
OUT = ROOT / "assets" / "dashboard-preview.png"

# The committed preview's frame: 1400 CSS pixels wide, 980 tall, starting just above the KPI
# band so the crop reads KPIs first and the two panels below them, not the header prose.
WIDTH, HEIGHT, TOP = 1400, 980, 450

# Accents from retired themes, in BGR. A single surviving pixel fails the build: the check is
# what makes "the preview matches the current theme" a property instead of an intention.
RETIRED = {
    "amber #d97a1e": (0x1E, 0x7A, 0xD9),
    "indigo #4f46e5": (0xE5, 0x46, 0x4F),
    "navy #1e1b4b": (0x4B, 0x1B, 0x1E),
}


def chromium() -> str:
    """An offscreen-capable chromium. Playwright's headless shell first, newest build wins."""
    shells = sorted(glob.glob(os.path.expanduser(
        "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell")))
    if shells:
        return shells[-1]
    for name in ("chrome-headless-shell", "chromium", "google-chrome"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("no headless chromium found; `npx playwright install chromium` provides one")


def main() -> None:
    if not PAGE.exists():
        raise SystemExit("deliverables/dashboard.html is missing; run `make dashboard` first")
    with tempfile.TemporaryDirectory() as td:
        shot = Path(td) / "full.png"
        # Tall enough that the crop window is fully rendered; --force-device-scale-factor pins
        # CSS pixels to image pixels so the committed file's 1400x980 frame is exact.
        subprocess.run(
            [chromium(), "--headless", f"--screenshot={shot}",
             f"--window-size={WIDTH},{TOP + HEIGHT + 600}", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--default-background-color=FFFFFFFF",
             PAGE.resolve().as_uri()],
            check=True, capture_output=True)
        img = cv2.imread(str(shot))
    if img is None or img.shape[1] != WIDTH or img.shape[0] < TOP + HEIGHT:
        raise SystemExit(f"render came back the wrong shape: {None if img is None else img.shape}")
    crop = img[TOP : TOP + HEIGHT, :WIDTH]
    for name, bgr in RETIRED.items():
        hits = int(np.sum(np.all(np.abs(crop.astype(int) - np.array(bgr)) <= 8, axis=2)))
        if hits:
            raise SystemExit(f"{hits} pixels of retired {name} in the preview; the dashboard theme leaked backwards")
    cv2.imwrite(str(OUT), crop)
    print(f"dashboard-preview.png  {crop.shape[1]}x{crop.shape[0]}  no retired-palette pixels")


if __name__ == "__main__":
    main()
