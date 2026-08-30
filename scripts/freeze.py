"""Render the results tables for the docs from the report files, so no number is ever typed by hand.

Run after `make eval`, the synth sweep, and `make bench`; paste the output into README.md and
docs/approach.md at freeze. If a report is missing its table is skipped and named.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    out: list[str] = []
    eval_p = ROOT / "reports" / "eval_report.json"
    if eval_p.exists():
        d = json.loads(eval_p.read_text())
        out.append("Real samples, detection at IoU 0.5 against the corrected page labels:")
        out.append("")
        out.append("| sample | boxes | precision | recall | F1 | state accuracy | routed | form witness |")
        out.append("|---|---|---|---|---|---|---|---|")
        for s in d["samples"]:
            w = s.get("witness") or {}
            witness = f"{s.get('form')} ({w.get('agree', 0)}/{w.get('projected', 0)} agree)" if s.get("form") and w.get("trusted") else "structure only"
            out.append(
                f"| {s['sample']} | {s['gold']} | {s['precision']:.3f} | {s['recall']:.3f} | {s['f1']:.3f} | {s['cls_acc']:.3f} | {s['ambiguous']} | {witness} |"
            )
        o = d["overall"]
        out.append(f"| overall | {o['tp'] + o['fn']} | {o['precision']:.3f} | {o['recall']:.3f} | {o['f1']:.3f} | {o['cls_acc']:.3f} | | |")
        out.append("")
    else:
        out.append("(eval_report.json missing)")
    synth_p = ROOT / "reports" / "synth_report.json"
    if synth_p.exists():
        rows = json.loads(synth_p.read_text())
        out.append("Synthetic sweeps (labeled pages generated from the blank golden forms, seed 11):")
        out.append("")
        out.append("| factor | levels | worst F1 | worst state accuracy |")
        out.append("|---|---|---|---|")
        by: dict[str, list[dict]] = {}
        for r in rows:
            by.setdefault(r["factor"], []).append(r)
        for factor in sorted(by):
            rs = by[factor]
            levels = ", ".join(str(r["level"]) for r in rs)
            out.append(f"| {factor} | {levels} | {min(r['f1'] for r in rs):.3f} | {min(r['cls_acc'] for r in rs):.3f} |")
        out.append("")
    else:
        out.append("(synth_report.json missing)")
    bench_p = ROOT / "reports" / "bench_report.json"
    if bench_p.exists():
        b = json.loads(bench_p.read_text())
        out.append(f"Serving ({Path(b['image']).name} through /detect, quiet machine):")
        out.append("")
        out.append("| concurrency | req/s | p50 ms | p95 ms |")
        out.append("|---|---|---|---|")
        for r in b["levels"]:
            out.append(f"| {r['concurrency']} | {r['req_per_s']} | {r['p50_ms']} | {r['p95_ms']} |")
        out.append("")
    else:
        out.append("(bench_report.json missing)")
    print("\n".join(out))


if __name__ == "__main__":
    main()
