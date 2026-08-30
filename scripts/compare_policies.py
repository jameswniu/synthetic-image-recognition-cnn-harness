"""Same code, same pages, two definitions of what counts as a mark.

The point this makes in a room: accuracy on this problem is not one number the detector owns. It is
a number that moves when somebody else changes their mind about what a mark is, and the person who
gets to change their mind is the customer, in a file, without us shipping anything.

Run: uv run python scripts/compare_policies.py
     uv run python scripts/compare_policies.py --a policy.json --b policy-strict.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from hv_checkbox import policy as policy_module
from hv_checkbox.pipeline import detect_with_page

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
PAGES = ["sample_1.jpg", "sample_2.png", "sample_5.png", "sample_7.png"]


def read(name: str, pol: policy_module.Policy) -> dict[tuple, tuple]:
    policy_module.use(pol)
    img = cv2.imread(str(SAMPLES / name))
    _, boxes, _ = detect_with_page(img)
    return {tuple(b.bbox): (b.is_checked, round(b.confidence, 3), tuple(b.reasons)) for b in boxes}


def labels(name: str) -> dict[tuple, bool]:
    data = json.loads((ROOT / "data" / "labels" / Path(name).with_suffix(".json").name).read_text())
    return {tuple(b["bbox"]): bool(b["is_checked"]) for b in data["boxes"] if not b.get("ignore")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="policy.json")
    ap.add_argument("--b", default="policy-strict.json")
    args = ap.parse_args()

    pa, pb = policy_module.load(args.a), policy_module.load(args.b)
    print(f"A = {args.a} ({pa.name})    B = {args.b} ({pb.name})")
    print(
        f"  rulings A: thin={pa.thin_single_stroke} stray={pa.stray_stroke_through_box} "
        f"fragmented={pa.scribbled_or_fragmented} band=[{pa.ambiguous_low}, {pa.ambiguous_high}]"
    )
    print(
        f"  rulings B: thin={pb.thin_single_stroke} stray={pb.stray_stroke_through_box} "
        f"fragmented={pb.scribbled_or_fragmented} band=[{pb.ambiguous_low}, {pb.ambiguous_high}]\n"
    )

    total_diff = correct_a = correct_b = scored = 0
    for name in PAGES:
        a, b, gold = read(name, pa), read(name, pb), labels(name)
        diff = [k for k in a if a[k][0] != b[k][0] or a[k][2] != b[k][2]]
        total_diff += len(diff)
        for k, want in gold.items():
            if k in a:
                scored += 1
                correct_a += a[k][0] == want
                correct_b += b[k][0] == want
        print(f"{name:14s} {len(a):3d} boxes, {len(diff)} read differently")
        for k in sorted(diff):
            want = gold.get(k)
            mark = ""
            if want is not None and a[k][0] != b[k][0]:
                mark = "   <- B agrees with the label" if b[k][0] == want else "   <- A agrees with the label"
            print(f"    {list(k)}{mark}")
            print(f"      A: checked={str(a[k][0]):5s} conf={a[k][1]:<5} {list(a[k][2])}")
            print(f"      B: checked={str(b[k][0]):5s} conf={b[k][1]:<5} {list(b[k][2])}")
            if want is not None:
                print(f"      label: {want}")

    print(f"\nagreement with the labels, {scored} boxes scored")
    print(f"  A {correct_a}/{scored} = {correct_a / scored:.4f}")
    print(f"  B {correct_b}/{scored} = {correct_b / scored:.4f}")
    print("\nNo source file changed between these two runs. Only the policy did.")


if __name__ == "__main__":
    main()
