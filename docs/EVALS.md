# Evals: the gates and bands the loop iterates against

The frozen gold set (`data/gold_set.json`, labeled by a human in the booth) defines what filled
means; the page labels (`data/labels/`) define where the boxes are; the golden blank forms
(`data/golden/`) define what a false fill is. This file turns those into pass/fail gates and numeric
bands so every iteration gets an unambiguous verdict from `make test` and `make eval`.

## Industry anchors (verified by a two-engine research pass, 2026-08-27, lead scan cross-refuted)

| Reference | Number | Source |
|---|---|---|
| YOLOv8-large checkbox detector (Tatsu), 300 mixed-document test set | F1 0.88 | tatsu.gitbook.io document-understanding whitepaper |
| YOLOv5 checkbox detect+classify on templated forms (Evoke), 696/231 images | ~96% production accuracy | evoketechnologies.com blog |
| EfficientNet-B0 checkbox state classifier (wendys-llc), UI crops | ~95% val accuracy | huggingface.co/wendys-llc/checkbox-classifier |
| Azure Document Intelligence Layout (selection marks) | $10 per 1,000 pages | Azure pricing summaries, 2026 |
| CheckboxQA (Snowflake Labs, 2025): VLMs underperform on checkbox-dependent QA | benchmark, no single number | arxiv.org/abs/2504.10419 |
| Published checkbox P/R on appraisal forms specifically | none found | confirmed absent by both engines |

Framing consequence: no public appraisal-form checkbox benchmark exists, so the bars below are
self-set against this project's own baseline and the general-document anchors above, stated as such.

## Tier 1: deterministic gates (code, hard pass/fail, every run must be all green)

| Gate | Check | Where |
|---|---|---|
| Serving contract | `/detect` returns exactly `{"boxes": [{"bbox", "is_checked"}]}`, 400 on non-image, `/healthz` ok, overlay is a PNG | `tests/test_api.py` |
| Golden blank forms | every box on each blank golden render found; zero read as filled | `tests/test_tier1.py` |
| Regression slice | every row in `data/regressions.jsonl` holds (tick, pen loop, sidebar hole, narrow cell, watermarked box, clean anchor, the invented box around printed text) | `tests/test_tier1.py` |
| Audit trail coordinates | a rejected candidate is reported in the same coordinate space as the boxes, including on pages small enough to be processed at 2x | `tests/test_pipeline.py` |
| Policy is the shipped policy | `policy.json` matches the defaults every published number was measured with, field by field | `tests/test_policy.py` |
| A policy change reaches an answer | the two shipped policies read at least one box differently, so the seam is real rather than decorative | `tests/test_policy.py` |
| Frozen referee integrity | no gold-card crop location enters training data | `tests/test_tier1.py` + `scripts/train.py` exclusion |
| Reproducibility | `scripts/synth.py --seed 11` regenerates the synthetic set byte-identically | validation batch (digest compare) |
| Docker | image builds; in-container `/detect` round-trip returns plausible counts | validation batch |
| Escalation is bounded | with the flag off, zero model calls; with it on, only reason-coded boxes are sent | `escalate.py` routing set |

## Tier 2: statistical bands (measured every iteration; in-band = good, out = iterate)

| Metric | Band | Reading at freeze | Verdict |
|---|---|---|---|
| Detection F1 at IoU 0.5, each real sample | at or above 0.98 | 0.988 / 1.000 / 1.000 / 1.000 | in band |
| Detection F1, synthetic sweeps at rotation up to 5 deg, JPEG down to q22, pen, shading, watermark | at or above 0.95 | worst 0.965 (shading) | in band |
| Detection F1, scale sweep down to 0.5x (boxes ~27 px) | at or above 0.95; 0.4x reported honestly | 0.980 at 0.5x; 0.990 at 0.4x after the small-page upscale fix | in band |
| Classification accuracy on matched boxes, real samples | at or above 0.97 | 0.976 / 1.000 / 1.000 / 1.000 (overall 0.997) | in band |
| Classification accuracy on gold cards (hard-graded rulings) | at or above 0.90; unsure cards excluded and required to route | 39 hard-graded cards, agreement 0.9231 | in band |
| Ambiguity rate on clean renders, deterministic core | at or below 3% of boxes | 0 of 118 on the clean URAR render | in band |
| Ambiguity rate across the whole 61-page corpus, deterministic core | at or below 5% of boxes | 138 of 5,872 (2.4%); 0 of 560 on the held-out real appraisals | in band |
| Hardest single damage condition, share of boxes routed | at or below 12% | shading at 9.05%, against 1.03% for rotation | in band |
| Ambiguity rate, same render with the patch classifier on | at or below 3% of boxes | 15 of 118 (12.7%) | OUT OF BAND, see the roadmap: the model disputes boxes the rule read correctly and changes no answer |
| Witness agreement (structure vs template) on same-form pages | at or above 0.9 snap rate | 118/118 and 79/79; partial crop and unmatched form correctly fail the trust gate | in band |
| Latency, full page through `/detect` | p95 at or below 400 ms per page single-worker | p50 392 ms, p95 457 ms | ITERATE: the register scale search dominates; coarse-to-fine search is the queued fix |
| Judge lane | disputes adjudicated with recorded votes; replay reproduces every verdict | implemented and off; no live credential was spent before freeze, so `judge_votes.json` ships empty | stated honestly |

## The loop

synthesize, then evaluate against this file, then: any tier-1 red gets fixed first; else improve the
worst out-of-band tier-2 row, usually with data or a named filter, not architecture. Each iteration
appends one row to `iterations.md` (run id, what changed, the headline numbers), so the improvement
story is auditable end to end. Failures found by the sweeps become regression rows or booth cards,
which is how the edge-case set grows without anyone hand-hunting for them.
