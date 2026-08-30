"""Fail the build when a README badge says something the repo no longer measures.

The badge wall at the top of README.md hard-codes four numbers: how many tests are green, the
eval F1, the share of boxes sent to a person, and the size of the model. Each of those is a
claim, and a claim that nothing rechecks is a claim that drifts. This gate recomputes what it
can and exits nonzero on the first mismatch, so a stale badge fails CI instead of shipping.

Two layers, selected by a mode argument, because the two ways a badge goes stale are different
defects. `committed` is the consistency layer: it reads the reports out of HEAD with git show,
so a commit that edits a badge without re-measuring, or re-measures without updating the badge,
fails on its own content. It also asserts the committed telemetry describes the advertised
corpus, 61 pages and 5,872 boxes, because a queue percentage quoted against the wrong
denominator is wrong even when the arithmetic is right. `fresh` is the behavior layer: after
`make synth` and `make reports` rebuild the reports in a hermetic checkout, it checks the fresh
F1 and the fresh flag population, so a code change that alters what the system finds or flags
fails even though it touched no report and no badge.

The hermetic checkout is synth plus samples only, 56 pages and 5,312 boxes: the five held-out
appraisals are fetched from third-party sites and deliberately stay out of CI. They contribute
zero flags, so those 56 pages carry the full flag population of 138, and fresh mode pins all
three numbers rather than re-deriving the badge's 2.4%, whose denominator needs the holdout.
The committed reports stay the published record; CI never chases machine timings.

Run: uv run --with onnx --extra dev --extra train python tools/check_claims.py committed
     uv run --with onnx --extra dev --extra train python tools/check_claims.py fresh
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The corpus the queue badge advertises: 52 synthetic pages, the 4 from the brief, and the
# 5 held-out appraisals. The dashboard quotes its queue share against these same totals.
ADVERTISED_PAGES = 61
ADVERTISED_BOXES = 5872

# The same run without the holdout, which is everything a hermetic checkout can rebuild.
# The holdout pages flag nothing, so the flag population is intact.
HERMETIC_PAGES = 56
HERMETIC_BOXES = 5312
HERMETIC_FLAGGED = 138


def badge_claims() -> dict[str, str]:
    """The four numbers the README asserts, pulled from its shields URLs."""
    text = (ROOT / "README.md").read_text()
    patterns = {
        "tests": r"img\.shields\.io/badge/tests-(\d+)_green",
        "f1": r"img\.shields\.io/badge/eval-F1_([0-9.]+)-",
        "queue": r"img\.shields\.io/badge/queue-([0-9.]+)%25",
        "weights": r"img\.shields\.io/badge/model-(\d+)K_weights",
    }
    claims = {}
    for name, pat in patterns.items():
        m = re.search(pat, text)
        if not m:
            raise SystemExit(f"README.md carries no {name} badge matching {pat}; the wall changed shape, update this gate with it.")
        claims[name] = m.group(1)
    return claims


def committed_report(path: str) -> dict:
    """A report as HEAD holds it, so the check binds the commit, not the working tree."""
    out = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"git show HEAD:{path} failed:\n{out.stderr.strip()}")
    return json.loads(out.stdout)


def working_report(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def measured_tests() -> int:
    """What pytest would actually run, from its own collector, not a number typed anywhere."""
    out = subprocess.run(
        ["uv", "run", "--extra", "dev", "python", "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    m = re.search(r"(\d+) tests? collected", out.stdout)
    if not m:
        raise SystemExit(f"could not find a 'N tests collected' line in pytest's output:\n{out.stdout[-800:]}{out.stderr[-800:]}")
    return int(m.group(1))


def f1_of(ev: dict) -> float:
    """Overall F1 from an eval report, rounded the way the badge rounds it."""
    return round(ev["overall"]["f1"], 3)


def totals_of(tel: dict) -> dict:
    """The totals of the default rules-only run, the same fields the dashboard reads."""
    return tel["modes"]["deterministic core only"]["totals"]


def queue_of(totals: dict) -> float:
    """flag_rate as a percentage through a one-decimal format, exactly as the dashboard
    prints its "Sent to a person" KPI, so this number and that one cannot disagree."""
    return float(f"{100 * totals['flag_rate']:.1f}")


def measured_weights_k() -> int:
    """Parameters in the shipped model, in thousands rounded down, summed from its tensors."""
    import onnx

    model = onnx.load(str(ROOT / "models" / "patch-int8.onnx"))
    count = 0
    for init in model.graph.initializer:
        n = 1
        for d in init.dims:
            n *= d
        count += n
    return count // 1000


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "committed"
    if mode not in ("committed", "fresh"):
        raise SystemExit(f"unknown mode {mode!r}: this gate runs as `committed` or `fresh`.")
    claims = badge_claims()
    failed = False

    def check(name: str, badge, measured) -> None:
        nonlocal failed
        if badge == measured:
            print(f"{name}: claim OK ({badge})")
        else:
            print(f"{name}: claim FAIL (badge {badge}, measured {measured})")
            failed = True

    if mode == "committed":
        totals = totals_of(committed_report("reports/telemetry.json"))
        if totals["pages"] != ADVERTISED_PAGES or totals["boxes"] != ADVERTISED_BOXES:
            print(f"claim FAIL (queue measured on {totals['pages']} pages / {totals['boxes']:,} boxes, "
                  f"advertised {ADVERTISED_PAGES} / {ADVERTISED_BOXES:,})")
            sys.exit(1)
        check("tests", int(claims["tests"]), measured_tests())
        check("eval F1", float(claims["f1"]), f1_of(committed_report("reports/eval_report.json")))
        check("queue %", float(claims["queue"]), queue_of(totals))
        check("weights K", int(claims["weights"]), measured_weights_k())
    else:
        totals = totals_of(working_report("reports/telemetry.json"))
        check("eval F1", float(claims["f1"]), f1_of(working_report("reports/eval_report.json")))
        got = (totals["pages"], totals["boxes"], totals["flagged"])
        want = (HERMETIC_PAGES, HERMETIC_BOXES, HERMETIC_FLAGGED)
        if got == want:
            print(f"queue flags: claim OK ({HERMETIC_FLAGGED} flagged on {HERMETIC_PAGES} pages / {HERMETIC_BOXES:,} boxes)")
        else:
            print(f"queue flags: claim FAIL (measured {got[0]} pages / {got[1]:,} boxes / {got[2]} flagged, "
                  f"expected {want[0]} / {want[1]:,} / {want[2]})")
            failed = True
        check("weights K", int(claims["weights"]), measured_weights_k())

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
