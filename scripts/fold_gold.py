"""Fold the labeler's booth answers into the frozen gold set and the page labels.

Input: the booth download (hv_gold_labels_v1.json) plus data/cards/cards.json (the card metadata,
including each card's source image, bbox, stratum, and the detector's read at generation time).

Outputs:
  data/gold_set.json   the frozen referee: every card with its human label; never trained on
  policy_draft.md      counts and disagreements per stratum, raw material for POLICY.md
  data/labels updates  where the human ruling contradicts a seeded page label (real cards only):
                       Filled/Empty flip the state; Unsure and Not-a-checkbox set ignore=true
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "data" / "cards" / "cards.json"
LABELS = ROOT / "data" / "labels"
GOLD = ROOT / "data" / "gold_set.json"
MEANING = {"F": "filled", "E": "empty", "N": "not_a_checkbox", "U": "unsure"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("booth_json", help="path to the downloaded hv_gold_labels_v1.json")
    args = ap.parse_args()
    booth = json.loads(Path(args.booth_json).read_text())
    labels: dict[str, str] = booth["labels"]
    cards = {c["id"]: c for c in json.loads(CARDS.read_text())}

    gold_cards = []
    for cid, card in cards.items():
        if cid not in labels:
            continue
        gold_cards.append(
            {
                "id": cid,
                "source": card["source"],
                "bbox": card["bbox"],
                "stratum": card["stratum"],
                "note": card.get("note", ""),
                "detector_ink": card.get("detector_ink"),
                "label": MEANING[labels[cid]],
            }
        )
    GOLD.write_text(json.dumps({"savedAt": booth.get("savedAt"), "notes": booth.get("notes", ""), "cards": gold_cards}, indent=1))

    # stratum summary and disagreements with the detector's generation-time read
    by_stratum: dict[str, Counter] = defaultdict(Counter)
    disagreements = []
    for g in gold_cards:
        by_stratum[g["stratum"]][g["label"]] += 1
        ink = g.get("detector_ink")
        if g["source"] != "synthetic" and ink is not None:
            det = "filled" if ink > 0.10 else "empty"
            if g["label"] in ("filled", "empty") and det != g["label"]:
                disagreements.append(g)

    # fold real-card rulings back into the page labels
    changed = 0
    for lab_path in sorted(LABELS.glob("*.json")):
        data = json.loads(lab_path.read_text())
        touched = False
        for g in gold_cards:
            if g["source"] != data["source"]:
                continue
            gx = (g["bbox"][0] + g["bbox"][2]) / 2
            gy = (g["bbox"][1] + g["bbox"][3]) / 2
            for b in data["boxes"]:
                cx = (b["bbox"][0] + b["bbox"][2]) / 2
                cy = (b["bbox"][1] + b["bbox"][3]) / 2
                if abs(cx - gx) + abs(cy - gy) > 8:
                    continue
                if g["label"] in ("filled", "empty"):
                    want = g["label"] == "filled"
                    if b["is_checked"] != want or b.get("ignore"):
                        b["is_checked"], b["ignore"] = want, False
                        b["note"] = f"labeler: {g['label']} ({g['id']})"
                        touched = True
                        changed += 1
                else:
                    if not b.get("ignore"):
                        b["ignore"] = True
                        b["note"] = f"labeler: {g['label']} ({g['id']})"
                        touched = True
                        changed += 1
        if touched:
            lab_path.write_text(json.dumps(data, indent=1))

    lines = ["# Policy draft from the booth session", ""]
    lines.append(f"Cards labeled: {len(gold_cards)} of {len(cards)}. Page labels changed: {changed}.")
    lines.append("")
    lines.append("| stratum | filled | empty | not a checkbox | unsure |")
    lines.append("|---|---|---|---|---|")
    for s in sorted(by_stratum):
        c = by_stratum[s]
        lines.append(f"| {s} | {c['filled']} | {c['empty']} | {c['not_a_checkbox']} | {c['unsure']} |")
    lines.append("")
    if disagreements:
        lines.append("Labeler vs detector read, real cards only:")
        for g in disagreements:
            lines.append(f"- {g['id']} {g['source']} {g['bbox']} ink={g['detector_ink']}: labeler says {g['label']} ({g['note']})")
    (ROOT / "docs" / "policy_draft.md").write_text("\n".join(lines) + "\n")
    print(f"gold_set.json: {len(gold_cards)} cards; page labels changed: {changed}; policy_draft.md written")
    if booth.get("notes"):
        print("labeler notes:", booth["notes"])


if __name__ == "__main__":
    main()
