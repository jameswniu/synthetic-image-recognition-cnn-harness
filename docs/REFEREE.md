# Referee cards: every number this repo shows a stranger

Built Wed 9/2 on branch referee-card at commit f79a927. Each card was written from the producing script and the committed report, never from the README, and every number that could be rebuilt in under two minutes was rebuilt the same day (results at the end). The Claim line names each card. A stranger with the repo should be able to regenerate any number from its Command line.

## UNTRACEABLE

No script or report in this repo produces these, so they come off the hero, the badges, the slides and the GitHub description until one does.

- "2.5 ms CPU" for the CNN lives only in the GitHub description. No file in the repo carries it. The header comment of src/hv_checkbox/patch_model.py (lines 28 to 68) quotes 6.7 to 8.1 ms per page for a per-crop loop and 55 to 68 microseconds per crop, and a live pass today over the 118 boxes of sample_2.png took 27 to 59 ms per page, 0.23 to 0.50 ms per box. Nothing measured anywhere is 2.5 ms.
- "$0.000004" per page (README.md lines 161, 199 and 365, docs/approach.md line 49, assets/dimensions.svg line 25, assets/alternatives.svg line 14, dashboard.html line 100, deck slides 6 and 9) is a typed literal in tools/make_dashboard.py line 532, tools/make_deck.py lines 476 and 556 and tools/draw_figures.py lines 212 and 251, with no CPU price, formula or report behind it.
- "$0.001", "$0.009", "$0.085" and "~40x more" (README.md lines 162 to 164 and 366, deck slide 6, assets/alternatives.svg line 60) are typed literals in tools/make_deck.py lines 477 to 479, and the 40x does not follow from the table it sits in (0.085 over 0.001 is 85x, over 0.009 is 9x).
- "106 tokens" for a crop and "1,990" for a page (README.md line 157, deck slide 6, docs/approach.md line 53) have no token formula in src/hv_checkbox/escalate.py or anywhere else.
- "268 of 268" settled without a person (dashboard.html line 333) is typed prose in tools/make_dashboard.py line 680, and reports/compare_readers_report.json says the rules settled 284 with 0 wrong, so it is stale as well as unproduced.
- "3.5%" model disputes on synthetic pages (README.md line 281, docs/iterations.md line 16) cannot be rebuilt from reports/telemetry.json under any definition. Dispute tags over the 5,025 synthetic boxes give 2.4%, flagged boxes with the model on give 3.6%, and the 24 mixed pages it trained on give 2.4% and 3.8%. tools/make_dashboard.py lines 495 and 496 compute the tag rates and never print them.
- "-133 to +396 px" section offsets (docs/iterations.md line 13, docs/approach.md line 39), "clean X spans 0.52" (docs/iterations.md line 14, dashboard.html line 393) and "roughly thirteen pixels per box" (docs/approach.md line 83) are one-off build measurements with no script. They are prose, not hero numbers, and should say they were measured once.

- "returned zero boxes for both" cover pages (README.md line 255) has no artifact, because scripts/fetch_holdout.py score() iterates only the five rendered PNGs and never scores a cover page.
- "Two of those gates I checked by deliberately reverting the fix" (README.md line 302, deck slide 12) has no artifact, no log or test records which two or what reverted.

## Mismatches

- The hero alt text (README.md line 2) reads "286 of 287 boxes found, 2.4% sent to a person, 36 of 39 human rulings matched" with no set labels, and the three numbers come from three sets (4 brief pages, 61 mixed pages, 39 gold cards). assets/hero.svg labels each one (lines 10, 14 and 18) and the alt text drops the labels.
- The queue rate on the architecture figures is three different numbers with no set named: README.md lines 99 and 100 (the mermaid) say 99.3% settled and 0.7% flagged, assets/architecture.svg line 43 says 2.4%, deck slide 4 says 97.6% and 2.4%.
- The four-page queue has two denominators. "2 of 287" (dashboard.html lines 86 and 113, README.md line 305, deck slide 10) counts detections, "2 of 286" (dashboard.html line 236, deck slide 14, the docx, reports/compare_readers_report.json) counts detections matched to a scorable label. Both round to 0.7%.
- "286 of 287 found" and "2 of 287 flagged" share a 287 by coincidence. The first 287 is scorable labels, the second is detections, and they match because the one label the detector misses is offset by the one detection sitting on the ignored tick (card 3).
- The latency numbers mix two instruments. dashboard.html lines 95 and 96 and assets/dimensions.svg lines 38 and 40 pair the in-process median (284 ms, reports/telemetry.json) with the HTTP p95 (457 ms, reports/bench_report.json). The in-process p95 is 348 ms and the HTTP p50 is 392 ms. Deck slide 7 says "under half a second for 95 pages in every 100, measured over 61 pages" and the 457 ms came from 40 requests of one page.
- "0.30 s of one CPU core" (README.md lines 161 and 200, deck slides 6 and 9) sits beside "284 ms" everywhere else.
- Deck slide 10 says "Across 61 pages and 5,872 boxes ... never drops below 96.5% correct". The 96.5% is detection F1 on the 52 synthetic pages (reports/synth_report.json, shading 0.9646), not a share read correctly and not measured over 61 pages. README.md line 227 also calls it "correct".
- dashboard.html lines 129 to 141 print 44%, 38%, 11%, 6% and 1% for the reason bubbles. Those are shares of 146 reason tags under a heading (line 113) that says 138 boxes. Deck slide 13 states the 146 correctly.
- "6.6%" is called the model's dispute rate on real pages (README.md line 281, docs/iterations.md line 16), and dispute tags are 55 of 847 (6.5%). 6.6% is the flagged-box rate with the model on (56 of 847, or 19 of 287 on the brief pages), which is what README.md line 163 and deck slide 6 mean by "flag rate".
- POLICY.md line 42 says "Nine cards were ruled unsure" and data/gold_set.json holds 10 (docs/policy_draft.md's table also sums to 10).
- One box has two opposite answer keys. data/gold_set.json card c022 rules the narrow cell at [1723, 898, 1764, 952] on sample_5 an empty checkbox, and data/regressions.jsonl row 4 asserts that the same cell must not be detected at all. It is one of the three gold misses.
- dashboard.html line 244, deck slide 14 and the docx say the CNN "misread both real never-seen test boxes" while the table above them says "settled wrong 1". Both describe the same two boxes: the CNN scores the empty pen-loop box 0.845 (inside the 0.10 to 0.90 band, so counted as queued) and the filled faded X 0.082 (counted as wrong).
- docs/EVALS.md line 50 bands reader agreement at "0.9 snap rate" and the code trusts a page at 0.75 (src/hv_checkbox/template.py line 200), so a page between the two is trusted by the code and out of band on paper.
- "23K weights" (README.md line 14, assets/architecture.svg line 41), "23,000" (dashboard.html line 233) and the counted 23,381 disagree with "about twenty-five thousand parameters" in docs/approach.md line 45.
- reports/bench_report.json was not produced by the Makefile's bench target as written. That target takes scripts/bench.py defaults (sample_1.jpg, 120 requests, concurrency 1, 4 and 8) and the committed report is sample_2.png, 40 requests, concurrency 1 and 4.
- assets/dimensions.svg and assets/alternatives.svg carry numbers with no command footer, while hero.svg line 29, architecture.svg line 59, queue-reasons.svg line 22 and robustness.svg line 31 name the command or the report that reprints them.

- deliverables/dashboard.html line 68 says the 52 damaged pages were made "by damaging those same pages", meaning the brief's four, while README.md line 227, data/README.md line 40 and cards 5 and 6 say they were built from the two blank federal forms.
- POLICY.md lines 27 to 28 say the check-mark tick "stays in the routed set", and reports/telemetry.json flags only the pen loop and the faded X on that page (card 3).
- scripts/train.py line 1 says "a ~25k-parameter CNN" beside docs/approach.md line 45 ("about twenty-five thousand parameters") and the counted 23,381, the same drift as the 23K entry above.
- "-133 to +396 px" also lives in src/hv_checkbox/template.py line 4 as a code comment, so it is a note from the build rather than a measured artifact, and the UNTRACEABLE entry above should read that way.

## Cards

Eight lines each. Intervals are two-sided 95% exact binomial. Line numbers are at commit f79a927.

```
Claim     "286 of 287 boxes found" and "F1 0.998" (README.md line 2 alt text, lines 20, 198 and 223, badge line 12, assets/hero.svg line 9, dimensions.svg line 12, architecture.svg line 10, alternatives.svg line 11, dashboard.html line 85, deck slides 9, 10 and 13, the docx, the GitHub description, docs/EVALS.md line 41)
Unit      checkboxes on the four brief sample pages (42, 118, 48 and 79), the denominator is the 287 labeled boxes that are scored, and F1 0.998 is the harmonic mean of precision 286 of 286 and recall 286 of 287, so the one miss is the whole gap
Match     a predicted box and a labeled box are the same box when they overlap by at least half (intersection over union 0.5 counts, scripts/evaluate.py line 52 breaks only below the threshold), pairs are taken one to one by highest overlap across the whole page with the first index winning an exact tie, an unpaired prediction is a false alarm, an unpaired label is a miss, and a prediction paired with an ignored label is dropped from both counts
Set       288 label boxes in data/labels, seeded by running the detector and then corrected by eye, 282 still carry the "seeded" note and 6 a hand ruling, 10 were deleted by eye along the way, 1 is marked ignore (the tick ruled unsure) and sits outside both counts, and the one miss is a faint grey box the labeler kept and the detector never proposes
Command   make eval, which runs HV_CLASSIFIER=off scripts/evaluate.py with match() at line 41 and thr=0.5, per-page rows and the overall block in reports/eval_report.json (tp 286, fp 0, fn 1), and tools/check_claims.py line 144 fails CI if the badge and the report disagree
Sibling   per page it is 41 of 42, 118 of 118, 48 of 48 and 79 of 79 (F1 0.988 on the photographed page), and on the 52 damaged synthetic pages the worst condition is F1 0.9646 with 8 false alarms and 6 misses on 197 boxes under shading
Bound     one miss in 287 gives an interval on recall of 0.981 to 0.9999, the 287 boxes come from 4 pages by 2 rendering vendors so a third vendor is unmeasured, and the number to beat is v1 scoring 1.0 against labels the detector wrote itself (docs/iterations.md line 10) and the v0 prototype finding 29, 195, 227 and 59 boxes on the same pages (line 9)
Knob      the 0.5 overlap threshold, at 0.7 a slightly shifted box becomes a miss plus a false alarm, at 0.3 two neighbouring boxes can pair
```

```
Claim     "285 of the 286 found" read correctly, "0.997", "40 of the 41 found", "285 of 286 to 286 of 286" (README.md lines 20, 145, 219, 223, 235 and 318, dashboard.html lines 236 and 333, deck slides 5, 10 and 14, the docx, docs/EVALS.md line 44, docs/approach.md line 25, docs/iterations.md lines 11 to 16)
Unit      matched boxes whose reported marked-or-empty boolean equals the label, the denominator is the 286 predictions that paired with a scorable label (the missed box cannot be graded and the ignored tick is dropped), and a flagged box still counts by its boolean, so the faded X counts as wrong even though it was sent to a person
Match     the boolean is_checked on the paired prediction equals is_checked on the label (scripts/evaluate.py line 77), nothing softer, and the overall 0.997 is the pair-weighted mean of the four page rates (line 140), 285 of 286 = 0.99650
Set       the same 286 pairs as card 1, with 92 of the 287 scorable labels marked and 195 empty, the answers on the faded X and the pen-loop box coming from the labeler in the booth (data/labels/sample_1.json notes), and the rulings frozen in policy.json exactly as the numbers were measured (tests/test_policy.py line 30 asserts that)
Command   make eval (cls_acc in reports/eval_report.json), then HV_POLICY=policy-strict.json HV_CLASSIFIER=off uv run python scripts/evaluate.py, or uv run python scripts/compare_policies.py lines 56 to 80, for the 286 of 286 reading
Sibling   under the strict policy the faded X flips to marked and agreement is 286 of 286 with the same 2 boxes still flagged, and counting only boxes settled without a person the rules score 284 of 284 (reports/compare_readers_report.json, right 284, wrong 0), which makes the dashboard's "268 of 268" stale
Bound     one wrong in 286 gives an interval of 0.981 to 0.9999, always answering empty would already score 194 of 286 (67.8%), since the one missed label is an empty box, and the four pages hold 92 marked boxes in total so the marked side rests on fewer than a hundred examples
Knob      ink_filled 0.10 and the scribbled_or_fragmented ruling in policy.json, route or filled rescues the faded X and would also report a scribbled-out box as marked
```

```
Claim     "2" flagged, "0.7% flagged", "99.3% settled", "Two boxes out of 287", "2 of those 287", "2 of 286" (README.md lines 99, 100, 162, 223, 305, 353 and 368, dashboard.html lines 86, 113, 166 and 236, deck slides 5, 6, 10 and 14, the docx, docs/approach.md line 51, docs/iterations.md line 15)
Unit      detected boxes on the four brief pages that carry at least one reason code, 2 of the 287 detections (telemetry) or 2 of the 286 detections matched to a scorable label (compare_readers), both 0.7%, and this 287 is detections while card 1's 287 is labels, they coincide because the one label the detector misses is offset by the one detection sitting on the ignored tick
Match     a box is flagged when its reasons list is non-empty (scripts/telemetry.py line 93, scripts/compare_readers.py line 57), and the two are the No Zoning pen loop (STRAY_STROKE) and the Electricity Public faded X (INK_AMBIGUOUS and FRAGMENTED_MARK), both on the photographed page
Set       the same 4 pages, rules only (HV_CLASSIFIER=off), reason codes as shipped in policy.json, and the tick the labeler called unsure is read marked with no flag, so it is not in the queue even though POLICY.md line 27 says it stays routed
Command   make telemetry (reports/telemetry.json, the 4 rows with corpus "sample", flagged 2, 0, 0 and 0) or make compare (reports/compare_readers_report.json, rules queue 2 of 286)
Sibling   on the 61-page mixed set the rate is 2.4% (card 4), on the 5 held-out appraisals it is 0 of 560, and with the CNN switched on the same four pages flag 19 of 287 (6.6%)
Bound     2 of 287 gives an interval of 0.08% to 2.5%, so the true four-page rate could be three times the headline, and flagging nothing would score the same 285 of 286 while hiding the one wrong answer inside the file, the flag earns its place because that one wrong answer is one of the two flagged boxes
Knob      the ambiguous band ambiguous_low 0.05 to ambiguous_high 0.20 in policy.json, widening it to 0.03 to 0.30 (the strict file) adds one reason to the pen-loop box and changes no count here, and stray_outside 0.50 decides whether a stroke is passing through or marking
```

```
Claim     "2.4% with reasons", "138 of 5,872", "64, 56, 16, 9, 1", "1,868 had a mark", "31 of 61 pages" (README.md lines 2, 13, 267 and 269, assets/hero.svg lines 13 and 14, architecture.svg line 43, queue-reasons.svg lines 9 to 22, dashboard.html lines 70, 80, 81, 90, 91 and 113 to 149, deck slides 4, 12 and 13, docs/EVALS.md line 47, docs/iterations.md line 16, the docx)
Unit      detected boxes carrying at least one reason code over every detected box on the 61-page mixed set (52 synthetic pages damaged on purpose, the 4 brief pages, 5 held-out appraisals), 138 of 5,872 = 2.35%, printed as 2.4% by the one-decimal format tools/check_claims.py line 105 also uses, and the reason counts are tags not boxes (146 tags on 138 boxes, a box can carry two)
Match     flagged means reasons non-empty (scripts/telemetry.py line 93), the rate is flagged over boxes (line 121), the per-reason counts sum every tag on every box (lines 112 to 114), and no label is involved anywhere in this number, it is what the system flagged, not what it got wrong
Set       61 pages with no answer key for 57 of them, 5,872 is a detection count not a label count, 136 of the 138 flags come from the 52 damaged pages, 2 from the brief pages and 0 from the held-out appraisals, and 31 of 61 pages passed the form-match trust check (trusted_pages, line 126)
Command   make telemetry (uv run --extra train python scripts/telemetry.py, totals under "deterministic core only" in reports/telemetry.json), tools/check_claims.py lines 40 to 47 pin 61 pages, 5,872 boxes and 138 flags, and tools/make_dashboard.py draws the reason bubbles from the same file
Sibling   with the CNN on the same set flags 237 of 5,872 (4.0%), on the brief pages alone it is 2 of 287 (0.7%), and the hardest single damage kind is shading at 18 of 199 (9.05%)
Bound     138 of 5,872 gives an interval of 2.0% to 2.8%, but the set is 86% synthetic damage of two blank forms, so it says how the queue behaves under abuse and nothing about a real production mix, where the only evidence is 0 of 560 on five pages
Knob      the damage recipe in scripts/synth.py (seed 11, 26 conditions), harsher shading or more pen lines raise the rate, and dropping the synthetic pages would leave 2 of 847 (0.2%)
```

```
Claim     "shading 9.05%" through "rotation 1.03%", "watermark 4.17%", "pen 3.12%", "downscaled 2.91%", "several kinds 2.72%", "clean render 2.08%", "JPEG 2.07%", "2.69% one flaw each" (README.md line 280, assets/robustness.svg lines 7 to 30, dashboard.html lines 158 to 196, deck slide 13, docs/EVALS.md line 48)
Unit      flagged detections over detections within one damage kind, shading 18 of 199, watermark 8 of 192, pen 6 of 192, scale 17 of 584, mixed 63 of 2,314, base 4 of 192, JPEG 12 of 579 and rotation 8 of 773, sweep pages grouped by the factor field of data/synth/manifest.json and every mixed page in one group
Match     the same flagged rule as card 4 with no labels involved, grouped by factor (tools/make_dashboard.py line 454, using the corpus and factor tags scripts/telemetry.py lines 49 to 61 attach)
Set       2 blank forms (118 and 79 boxes) rendered at 300 DPI, marks drawn in by scripts/synth.py, then one damage each on 28 sweep pages and several at once on 24 mixed pages, so every group except mixed, scale, JPEG and rotation is exactly 2 pages, and the denominators are detections (199 on shading against 197 labels, because shading produces 8 false alarms and 6 misses, a net two more detections than labels)
Command   make telemetry, then tools/make_dashboard.py by_factor at line 454 or tools/draw_figures.py for assets/robustness.svg, whose footer names reports/telemetry.json
Sibling   the same groups scored against their labels give detection F1 0.9646 for shading and 0.9871 for rotation (reports/synth_report.json, card 6), so the queue and the accuracy move together under shading
Bound     shading is 18 of 199 (interval 5.5% to 13.9%) and rotation 8 of 773 (0.45% to 2.0%), every condition sits on 2 pages of one seed, and no group is real paper, so the ordering of kinds is more trustworthy than any single rate
Knob      the damage levels in scripts/synth.py lines 184 to 201 (shading 3 bands, pen 4 lines, rotation 1 to 5 degrees, scale 0.4 to 0.75, JPEG q22 to q60) and seed 11 at line 166
```

```
Claim     "never drops below 96.5% correct", "0.9646", "worst 0.965 (shading)", "0.980 at 0.5x, 0.990 at 0.4x", "52 pages and 5,122 boxes", "26 different ways" (README.md line 227, dashboard.html lines 201 to 228, deck slide 10, docs/EVALS.md lines 42 and 43, assets/hero.svg line 29)
Unit      detection F1 per damage condition on the synthetic pages, the floor being shading with 191 true pairs, 8 false alarms and 6 misses on 197 labeled boxes across 2 pages, F1 0.9646 (precision 0.960, recall 0.970), and 96.5% is that F1, not a share of boxes read correctly
Match     the same at-least-half overlap and one-to-one greedy pairing as card 1 (scripts/evaluate.py score_synth at line 149 calls score_sample per page and summarize at line 134 per condition)
Set       26 conditions times 2 forms = 52 pages and 5,122 labeled boxes (26 times 197), labels generated with the marks so they carry no human judgment and no seeding bias, mark shapes drawn from MARK_WEIGHTS at scripts/synth.py line 34, and the marks are the generator's imagination rather than scanned ink
Command   make synth, then HV_CLASSIFIER=off uv run python scripts/evaluate.py --synth data/synth --report reports/synth_report.json (the Makefile has no target for this report)
Sibling   on the four real pages the same metric is 0.988 to 1.000, and classification accuracy on the shading pages is 0.9895, so the damage costs detection more than mark reading
Bound     each condition is 2 pages of one seed, the shading recall 191 of 197 has an interval of 0.935 to 0.989, and there is no condition harder than 3 shading bands or 5 degrees, so the floor is the floor of this recipe
Knob      the shading band count (3) and its darkness in scripts/synth.py add_shading, and the 0.5 overlap threshold as in card 1
```

```
Claim     "0 of 560", "118 boxes each", "88 boxes", "68 of the 118", "perfect 1.0", marked 45, 46, 38, 37 and 33 (README.md lines 241 to 257 and 279, dashboard.html lines 167 to 169, deck slides 13 and 16, docs/approach.md line 87, docs/EVALS.md line 47)
Unit      detected boxes on 5 completed appraisal pages fetched from three offices, 560 detections in total with 0 carrying a reason code, and "118 each" is the detection count equalling the 118 slots on the blank standard form
Match     no labels exist for these pages, so "found all 88 boxes and got every mark right" (README.md line 251) is a by-eye inspection, the only computed numbers are the detection count, the marked count and the flag count per page (scripts/telemetry.py lines 91 to 94)
Set       data/holdout, fetched by scripts/fetch_holdout.py after the build, kept out of CI and out of the zip, 4 standard-form pages and 1 condominium page the registry has no blank for, and the condominium page matched the standard form at registration 1.0 with 68 of 118 expected positions agreeing, below the 0.75 trust threshold (src/hv_checkbox/template.py line 200), so its second reader was dropped for that page
Command   uv run python scripts/fetch_holdout.py --score, and the 5 rows with corpus "holdout" in reports/telemetry.json (boxes, checked, flagged, the agree field at 68 of 118, trusted false)
Sibling   with the CNN switched on the Key Realty page flags 37 of its 118 boxes and the other four still flag 0, and the brief's photographed page flags 2 of 42 under the same rules
Bound     0 flags in 560 bounds the true rate below 0.66%, the pages are all standard-form renders from three offices on one vendor's software (a la mode TOTAL, scripts/fetch_holdout.py lines 3 to 4) with no photographs or faxes, so a second rendering vendor is unmeasured, and accuracy on them is unmeasured because nobody labeled a box
Knob      the trust threshold min_agree 0.75, lowering it toward 0.57 would have trusted the wrong form match on the condominium page
```

```
Claim     "36 of 39 human rulings matched", "0.9231", "0.92", "76 close-up crops", "39 hard-graded cards", "49 of the 76 have an ink measurement" (README.md lines 2 and 289, assets/hero.svg line 17, dashboard.html lines 105 and 253, deck slide 13, the docx, docs/EVALS.md line 45, POLICY.md line 3, docs/iterations.md line 14)
Unit      gold cards whose ruling the system reproduces, the denominator is the 39 cards from the four real pages ruled filled or empty and not flagged as a suspected misclick (18 filled, 21 empty), out of 76 cards in total
Match     a card is matched to the first detection whose centre lies within 18 pixels of the card centre by city-block distance (scripts/evaluate.py line 188), it counts when that detection exists and its boolean equals the ruling (line 191), and a card with no detection nearby is a miss, which is how 2 of the 3 misses arise
Set       data/gold_set.json, 76 cards ruled by one labeler in the booth before the thresholds were set and frozen 2026-08-27, 27 synthetic cards excluded for having no page coordinates (8 of the 15 not-a-checkbox and 9 of the 10 unsure sit among them), then of the 49 real cards 7 not-a-checkbox, 1 unsure and 2 suspected misclicks (c011, c013) are excluded, leaving 39, and the three misses are c021 (the faint box, never detected), c022 (a narrow cell the regression rows say is not a box) and c055 (the faded X, read empty under the shipped policy)
Command   HV_CLASSIFIER=off uv run python scripts/evaluate.py --gold --report reports/gold_report.json (never regenerated by make reports on purpose, see the Makefile comment at the reports target)
Sibling   under the strict policy c055 flips to marked and the count becomes 37 of 39, and on the 286 page-level pairs the same boolean agrees 285 times
Bound     36 of 39 has an interval of 0.79 to 0.98, always answering empty scores 21 of 39 (53.8%), and the 39 cards were chosen as hard cases and anchors, not sampled at random from the boxes
Knob      the 18-pixel matching radius and the not-a-box rejections (the 0.78 aspect floor named in data/regressions.jsonl row 4), a card sitting on a rejected candidate can never score
```

```
Claim     "118/118 and 79/79" reader agreement, "68 of the 118" (docs/EVALS.md line 50, docs/iterations.md line 13, README.md line 253)
Unit      positions the blank-form reader projects onto the page that land on a box the line reader found, over the positions projected, 118 of 118 on the clean scan and 79 of 79 on the manufactured-home page
Match     a projected slot agrees when a detection sits in its row band within the window place() uses (src/hv_checkbox/template.py lines 200 to 231), the page is trusted when agree over projected is at least 0.75 (min_agree at line 200), and a disagreeing row is flagged rather than padded
Set       the 2 blank forms in data/golden (118 and 79 boxes, extracted once by the detector and checked by the blank-form test), applied to the 4 brief pages, of which the photographed crop (14 of 118) and the addendum (28 of 118) fail trust as intended because one is partial and the other is a form the registry lacks
Command   make eval, then the projected, agree and trusted fields under each sample in reports/eval_report.json
Sibling   on the 5 held-out pages it is 118 of 118 four times and 68 of 118 on the condominium page, and across the 61-page set 31 pages pass the trust check
Bound     two full agreements bound the rates at 0.969 and 0.954 or better, and docs/EVALS.md bands the check at 0.9 while the code trusts at 0.75, so a page between those two is trusted by the code and out of band on paper
Knob      min_agree 0.75 at template.py line 200, and the row window of 0.55 times the box side named in docs/iterations.md line 14
```

```
Claim     "26 green", "26 gates", "26 safety gates" (README.md lines 11, 302 and 444, assets/architecture.svg line 10, deck slides 11 and 12, the docx, the GitHub description)
Unit      test cases pytest collects in tests/, 5 in test_api.py, 5 in test_pipeline.py (4 per-page floors plus 1), 10 in test_tier1.py (2 blank forms, 7 regression rows, 1 frozen-key check) and 6 in test_policy.py
Match     a green test is one that passed on the run, and tools/check_claims.py line 80 reads the count from pytest's own collector rather than from any typed number
Set       the floors in tests/test_pipeline.py lines 7 to 15 are F1 0.97 and accuracy 0.95 on the photographed page and 0.99 on the other three, so a fall from 0.988 to 0.97 would still pass
Command   make test (uv run --extra dev pytest -q), and make claims for the badge check
Sibling   the hard pass-or-fail cases cover 4 pages, 2 blank forms and 7 fixed regressions, none of the 26 runs over the 52 synthetic pages or the held-out appraisals
Bound     a count of tests says nothing about coverage, and the floors sit 1 to 2.6 points below the measured numbers (the photographed page reads 0.9756 against a 0.95 floor), so a small regression passes silently
Knob      the FLOORS dictionary in tests/test_pipeline.py
```

```
Claim     "23K weights ONNX", "23,000 weights in a 29KB file", "23K-weight CNN", "int8 classifier 0.993 held-out", "12 epochs" (README.md line 14, assets/architecture.svg line 41, dashboard.html line 233, the GitHub description, docs/iterations.md line 14, deck notes on slide 14)
Unit      parameter elements summed over every initializer tensor in models/patch-int8.onnx, 23,381 in the served file (23,361 in models/patch.onnx before quantization), floored to thousands, and the file is 29,423 bytes
Match     the 0.993 has no match rule, it is accuracy at a 0.5 probability threshold on the sweep crops printed by scripts/train.py line 141 for the int8 artifact (sha256 b63c8774), served through onnxruntime by src/hv_checkbox/patch_model.py on 32 by 32 crops
Set       training crops are the 24 mixed synthetic pages plus real page crops minus every gold-card location (scripts/train.py lines 41 to 76), validation is the 28 sweep pages, so 0.993 is measured on synthetic marks the generator drew and on no human ruling
Command   make claims (tools/check_claims.py lines 108 to 119 count the weights), and make train (12 epochs, scripts/train.py line 82) reprints the 0.993, not rerun here because it trains
Sibling   on the 286 human-labeled boxes the same model alone is confident on 230 and right on 229, and its disagreement flags 17 more boxes than the rules on the brief pages (card 12)
Bound     0.993 on synthetic validation is a ceiling not a floor, the training record is a printed line with no saved report, and docs/approach.md line 45 says about twenty-five thousand parameters where the count is 23,381
Knob      the quantization to int8 (23,381 against 23,361 elements) and the 0.5 threshold on the printed accuracy
```

```
Claim     "2 of 286, 56 of 286, 19 of 286", "from 2 boxes to 19", "17 boxes", "229 of 230", "15 of 118 (12.7%)", "37 of 118", "misread both real never-seen test boxes", "6.6%" (README.md lines 163, 235, 241 and 281, dashboard.html lines 236 to 245, deck slides 6, 14 and 16 and the slide 14 notes, the docx, docs/EVALS.md line 49, docs/ROADMAP.md line 34, docs/approach.md line 81)
Unit      the 286 detections matched to a scorable label on the brief pages, read three ways, each box landing in exactly one of sent to a person, settled right or settled wrong, and 6.6% is 19 of 287 (or 56 of 847 with the held-out pages) flagged with the model on
Match     no overlap rule, the CNN is models/patch-int8.onnx (sha256 b63c8774) scored over 32 by 32 crops of the rules pass's boxes, a probability between 0.10 and 0.90 is sent to a person and otherwise the 0.5 side is compared to the label (scripts/compare_readers.py lines 79 to 84), and in the both mode a disagreement with the rule adds CLASSIFIER_DISAGREE to the box (grade() at line 51)
Set       the same 286 labels as card 2, the two hard boxes are gold cards and so were excluded from training, the CNN scores the empty pen-loop box 0.845 (queued) and the filled faded X 0.082 (wrong), which is what "misread both" and "settled wrong 1" both describe, and "15 of 118" and "37 of 118" are the clean scan and the Key Realty page in reports/telemetry.json with the model on
Command   make compare (uv run --extra train python scripts/compare_readers.py writes reports/compare_readers_report.json), make telemetry for the 15 of 118, the 37 of 118 and the 19 of 287, and the two probabilities 0.845 and 0.082 come from calling load_scorer().score() on those two crops by hand, since make compare prints only counts and no committed report carries them
Sibling   on the 5,872-box mixed set the model on takes the queue from 138 to 237, and its disagreement tags fall on 55 of 847 real-page boxes against 121 of 5,025 synthetic ones
Bound     one wrong in 230 confident answers gives an interval of 0.976 to 0.9999, the comparison is 286 boxes from 4 pages, and the number to beat is the rules-only row of 2 queued and 0 wrong, which the model fails on queue size alone
Knob      the 0.10 to 0.90 band, narrowing it to 0.25 to 0.75 shrinks the 56 and would move the 0.845 pen loop into the wrong column
```

```
Claim     "284 ms median", "457 ms p95", "p50 392 ms and p95 457 ms", "0.30 s of one CPU core", "under half a second for 95 pages in every 100" (README.md lines 155, 161, 170, 200 and 237, assets/dimensions.svg lines 38 and 40, dashboard.html lines 95 and 96, deck slides 6, 7, 9 and 13, docs/approach.md line 49, docs/EVALS.md line 51)
Unit      two instruments, the in-process time of detect_with_page per page over the 61-page set (median 283.5 ms, p95 347.6 ms, mean 258.9 ms, reports/telemetry.json) and the HTTP round trip of POST /detect for 40 requests of sample_2.png at concurrency 1 (p50 391.9 ms, p95 457.4 ms, max 767.6 ms, reports/bench_report.json)
Match     the in-process p95 is the sorted element at 0.95 times n (scripts/telemetry.py line 124), the HTTP p95 is the element at 0.95 times n minus 1 (scripts/bench.py line 44), each from one run, and no timing is checked by CI (tools/check_claims.py's header says timings are never chased)
Set       one machine and one run, rules only for telemetry, and the bench report was not produced by the Makefile's bench target as written (that target defaults to sample_1.jpg, 120 requests, concurrency 1, 4 and 8), it was run with --image sample_2.png --n 40 --concurrency 1,4
Command   make telemetry (p50_ms in the totals), then make serve and uv run python scripts/bench.py --image data/samples/sample_2.png --n 40 --concurrency 1,4 --report reports/bench_report.json
Sibling   at concurrency 4 the same bench reads p50 1,424 ms and p95 1,817 ms, and the 0.30 s in the cost table is 284 ms rounded up
Bound     40 requests of one page make the p95 the 38th fastest of 40, the third slowest request (scripts/bench.py line 44 takes the ascending index int(40 times 0.95) minus 1), the machine is not named, and a rerun today on a laptop with other jobs running gave p50 1,307 ms in-process and 1,456 ms over HTTP, so the number is a property of the box it ran on
Knob      the template scale search docs/EVALS.md line 51 names, and the 2x upscale for pages under 1,400 px wide (src/hv_checkbox/pipeline.py line 42)
```

```
Claim     "0.99 to the 96 = 38% of the time, so 62% of pages carry at least one wrong answer" (dashboard.html line 403)
Unit      an arithmetic illustration, the chance that a page of 96 boxes is entirely right when each box is right with probability 0.99, 96 being 5,872 boxes over 61 pages (96.26)
Match     none, tools/make_dashboard.py line 706 computes 100 times 0.99 to the power boxes_per_page and its complement
Set       the 0.99 is an assumed per-box rate for a hypothetical reader, not this system's measured 285 of 286
Command   make dashboard
Sibling   at the measured 0.9965 per box the same page is clean 71% of the time, and a full standard form has 118 boxes, where 0.99 gives 31% clean
Bound     it is a formula rather than a measurement, and it assumes box errors are independent, which a shaded row or a bad scan makes false
Knob      the assumed 0.99 and the boxes-per-page average
```

```
Claim     "51 down to 2", "52 to 61", "61 to 4", "4 to 2", "flat since v2" (dashboard.html lines 333 and 391 to 395)
Unit      boxes carrying an ambiguity reason on the four brief pages at each version v1 to v7, summed from the amb column of docs/iterations.md (1/38/12/0 = 51 at v1, 2/0/0/0 = 2 at v7)
Match     tools/make_dashboard.py iteration_history() at line 398 parses the markdown table, and line 519 asserts the first sum is 51 and the last is 2
Set       docs/iterations.md is a hand-written log, the code at v1 to v6 is not in the repo, and the v1 accuracy of 1.0 was scored against labels the detector had written
Command   make dashboard, reading docs/iterations.md
Sibling   the v7 row (2/0/0/0) is the live number card 3 regenerates
Bound     only the last row can be rebuilt, every earlier point is a typed record
Knob      the amb column of the log
```

```
Claim     "2 readers / 12 reason codes", "7 codes reach a person" (assets/architecture.svg lines 9, 46 and 47)
Unit      distinct uppercase reason strings in src/hv_checkbox, 12 in all, and the 7 in the ROUTED set that send a box to a person
Match     ROUTED at src/hv_checkbox/escalate.py line 26 holds INK_AMBIGUOUS, FRAGMENTED_MARK, STRAY_STROKE, THIN_MARK, CLASSIFIER_DISAGREE, MISSING_IN_DETECT and EXTRA_BOX, the other 5 are the escalation verdicts VLM_AGREE, JUDGED and REVIEW and the rejection reasons TEXT_LIKE_SIZE_OUTLIER and NOT_A_CHECKBOX
Set       the shipped code at commit f79a927, and only 5 of the 12 appear as box reasons in reports/telemetry.json rules only (a sixth, CLASSIFIER_DISAGREE, with the model on), THIN_MARK and the three verdicts never fired on this corpus, and the rejected lists in that file also carry TEXT_LIKE_SIZE_OUTLIER once and SIZE_CONSENSUS 43 times, a label scripts/telemetry.py line 86 invents rather than the code emitting it
Command   grep -rhoE '"[A-Z][A-Z_]{4,}"' src/hv_checkbox/*.py | sort | uniq | grep -v '^"HV_' as box reasons, since the bare grep also returns the three HV_ environment names
Sibling   the queue reasons that actually occurred are 5 (card 4)
Bound     a code count is a vocabulary size, not a coverage measure
Knob      the ROUTED set
```

```
Claim     "roughly two hundred boxes of free, unarguable ground truth" (docs/approach.md line 17), the blank official forms as a hard test (README.md lines 180 and 289, deck slide 8)
Unit      checkboxes on the 2 blank official renders in data/golden, 118 on Form 70 page 1 and 79 on Form 70B page 1, 197 in all, every one expected empty
Match     tests/test_tier1.py lines 20 to 26 assert the detector finds at least as many boxes as the .boxes.json file lists and reports zero marked, no overlap pairing is done, so an extra box on a blank form passes
Set       the .boxes.json coordinates were extracted once by the detector itself (data/README.md line 25), so the count is the detector agreeing with its own earlier output, and the blank forms are also the source images for all 52 synthetic pages
Command   make test (the two golden cases in tests/test_tier1.py)
Sibling   the same 197 boxes with marks drawn in score F1 0.9769 on the undamaged render (reports/synth_report.json, base, 7 misses and 2 false alarms), so adding marks alone costs 7 boxes
Bound     2 forms from one publisher at 300 DPI, and a count check that cannot fail on false alarms
Knob      the assertion is at least, not exactly, at tests/test_tier1.py line 25
```

## Cited, not measured here

F1 0.88 (Tatsu YOLOv8-large, 300 documents), about 96% (Evoke YOLOv5), about 95% (wendys-llc EfficientNet-B0) and $10 per 1,000 pages (Azure) are third-party figures sourced in docs/EVALS.md lines 12 to 15. They appear in README.md lines 192, 198 and 199, assets/alternatives.svg lines 34 and 37, deck slide 9, docs/approach.md line 67 and docs/ROADMAP.md line 26, and they keep their source wherever they appear.

## Regenerated live on Wed 9/2

- make eval (report written to a scratch path): tp 286, fp 0, fn 1, F1 0.998, classification 0.997, per page 0.988, 1.000, 1.000, 1.000, flagged 2, 0, 0, 0. Matches.
- HV_POLICY=policy-strict.json make eval: classification 1.000 (286 of 286), still 2 flagged. Matches.
- scripts/evaluate.py --gold: 39 graded, 36 correct, 0.9231, misses c021, c022, c055. Matches.
- scripts/compare_policies.py: 2 boxes read differently, A 285 of 286, B 286 of 286. Matches.
- pytest -q: 26 passed. Matches.
- tools/check_claims.py committed: tests 26, F1 0.998, queue 2.4, weights 23, all OK.
- scripts/evaluate.py --synth data/synth: 26 conditions, shading floor 0.965, scale 0.5 at 0.980, scale 0.4 at 0.990. Matches.
- scripts/telemetry.py (to a scratch path): 5,872 boxes, 138 flagged (2.4%), reasons 64, 56, 16, 9, 1, with the model on 237 flagged and 176 disagreements. Matches, timings aside.
- scripts/compare_readers.py (a scratch copy writing to a scratch path): queue 2, 56, 19, right 284, 229, 267, wrong 0, 1, 0. Matches.
- scripts/bench.py, 40 requests of sample_2.png at concurrency 1 on a busy laptop: p50 1,456 ms, p95 3,025 ms. Does not match, and it is a timing.
- onnx parameter count 23,381 in models/patch-int8.onnx, and the CNN scored 118 crops in 27 to 59 ms per page. The 2.5 ms in the GitHub description matches neither.
