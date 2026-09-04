# Referee cards: every number this repo shows a stranger

Built Wed 9/2 on branch referee-card at commit f79a927, and revised Fri 9/4 at commit 974cf48 after the fixes it asked for landed. Each card was written from the producing script and the committed report, never from the README, and every number that could be rebuilt in under two minutes was rebuilt the same day (results at the end). The Claim line names each card. A stranger with the repo should be able to regenerate any number from its Command line.

## Untraceable numbers, and what happened to them

The first revision of this file listed fourteen numbers that no script or report in the repo produced. As of commit 974cf48 none of them is on a reader-facing surface. Twelve were deleted and the sentences around them rewritten. They were "$0.000004", "$0.001", "$0.009", "$0.085" and "~40x" (every cost row now states what a page costs in measured terms, CPU time and the share of boxes that would reach a model), "1,990" tokens for a page, "268 of 268" (the dashboard reads 284 of 284 from reports/compare_readers_report.json), "3.5%" (the sentence now states the flagged-box rate with the model on, 56 of 847), "-133 to +396 px" and "clean X spans 0.52" and "roughly thirteen pixels per box" (the prose says these were measured once during the build and quotes no figure), "returned zero boxes for both" cover pages (deleted, nothing scores a cover page), and "Two of those gates I checked by deliberately reverting the fix" (deleted from the README, the deck and the walkthrough). The same two build measurements survive as code comments in src/hv_checkbox/template.py line 4 and src/hv_checkbox/classify.py line 105, which are notes from the build and not reader-facing.

Two were produced instead of deleted, because a small honest script could produce them. The CNN's timing now comes from tools/bench_cnn.py, which times PatchScorer.score() over the real crops of the four brief pages and writes reports/cnn_latency.json (`make bench-cnn`), and the surfaces quote that file, 3.9 ms for the 118-box page and 30.4 microseconds per crop over all 287 (card 18). The "2.5 ms CPU" in the live GitHub description matched nothing, and that field still carries it until the proposed text in the section at the end of this file is applied by hand. The crop token estimate now comes from tools/crop_tokens.py, which builds the exact crop src/hv_checkbox/escalate.py sends and counts its visual tokens the way the Claude API vision doc bills them, one token per 28 by 28 pixel patch after any downscale the tier forces, writing reports/crop_tokens.json with the doc URL (`make crop-tokens`). The median over the 287 boxes is 110 tokens (card 19) against the 106 that used to be typed under an older 750 pixels per token rule, and the same script counts a whole page on both tiers, 1,550 tokens standard and 4,752 high resolution, which replaces the deleted "1,990" with two numbers that name their tier.

The harvester (`python3 ~/.claude/skills/referee_card/find_claims.py .`) was run at commit 974cf48 and grepped for every removed number. None survives on a reader-facing surface outside this file.

## Mismatches

None remain at the head of referee-card. The drifts the first revision listed were reconciled to one value each, so the weights read 23,381 everywhere (the badge carries the exact count and tools/check_claims.py fails the build on a difference of one), every timing line carries one instrument with its set named, 96.5% is stated as detection F1 on the 52 synthetic pages, the reason-bubble shares are labeled as shares of the 146 tags, "6.6%" is stated as 56 of 847 boxes flagged with the model on, POLICY.md counts ten unsure cards and says the tick is not routed on the shipped run, docs/EVALS.md bands reader agreement at the code's 0.75 and says the /detect latency band is unmeasured on a full form rather than in band, gold card c022 is re-ruled not-a-checkbox so the two answer keys agree, every hero and architecture number carries its set label (asserted by tools/check_claims.py), reports/bench_report.json comes from the Makefile's bench target as written, and assets/dimensions.svg and assets/alternatives.svg carry a command footer.

## Cards

Eight lines each. Intervals are two-sided 95% exact binomial. Line numbers are at commit 974cf48.

```
Claim     "286 of 287 boxes found on the four brief pages" and "F1 0.998" (README.md line 2 alt text, lines 20, 198 and 223, badge line 12, assets/hero.svg line 9, dimensions.svg line 12, architecture.svg lines 10 and 59, alternatives.svg line 11, dashboard.html line 85, deck slides 9, 10 and 13, the docx, the proposed GitHub description, docs/EVALS.md line 41)
Unit      checkboxes on the four brief sample pages (42, 118, 48 and 79), the denominator is the 287 labeled boxes that are scored, and F1 0.998 is the harmonic mean of precision 286 of 286 and recall 286 of 287, so the one miss is the whole gap
Match     a predicted box and a labeled box are the same box when they overlap by at least half (intersection over union 0.5 counts, scripts/evaluate.py line 52 breaks only below the threshold), pairs are taken one to one by highest overlap across the whole page with the first index winning an exact tie, an unpaired prediction is a false alarm, an unpaired label is a miss, and a prediction paired with an ignored label is dropped from both counts
Set       288 label boxes in data/labels, seeded by running the detector and then corrected by eye, 282 still carry the "seeded" note and 6 a hand ruling, 10 were deleted by eye along the way, 1 is marked ignore (the tick ruled unsure) and sits outside both counts, and the one miss is a faint grey box the labeler kept and the detector never proposes
Command   make eval, which runs HV_CLASSIFIER=off scripts/evaluate.py with match() at line 41 and thr=0.5, per-page rows and the overall block in reports/eval_report.json (tp 286, fp 0, fn 1), and the committed layer of tools/check_claims.py fails CI if the badge, the hero alt text and the report disagree
Sibling   per page it is 41 of 42, 118 of 118, 48 of 48 and 79 of 79 (F1 0.988 on the photographed page), and on the 52 damaged synthetic pages the worst condition is F1 0.9646 with 8 false alarms and 6 misses on 197 boxes under shading
Bound     one miss in 287 gives an interval on recall of 0.981 to 0.9999, the 287 boxes come from 4 pages by 2 rendering vendors so a third vendor is unmeasured, and the number to beat is v1 scoring 1.0 against labels the detector wrote itself (docs/iterations.md line 10) and the v0 prototype finding 29, 195, 227 and 59 boxes on the same pages (line 9)
Knob      the 0.5 overlap threshold, at 0.7 a slightly shifted box becomes a miss plus a false alarm, at 0.3 two neighbouring boxes can pair
```

```
Claim     "285 of the 286 found" read correctly, "0.997", "40 of the 41 found", "285 of 286 to 286 of 286" (README.md lines 20, 145, 219, 223, 235 and 316, dashboard.html lines 236 and 333, deck slides 5, 10 and 14, the docx, docs/EVALS.md line 44, docs/approach.md line 25, docs/iterations.md lines 11 to 16)
Unit      matched boxes whose reported marked-or-empty boolean equals the label, the denominator is the 286 predictions that paired with a scorable label (the missed box cannot be graded and the ignored tick is dropped), and a flagged box still counts by its boolean, so the faded X counts as wrong even though it was sent to a person
Match     the boolean is_checked on the paired prediction equals is_checked on the label (scripts/evaluate.py line 77), nothing softer, and the overall 0.997 is the pair-weighted mean of the four page rates (line 140), 285 of 286 = 0.99650
Set       the same 286 pairs as card 1, with 92 of the 287 scorable labels marked and 195 empty, the answers on the faded X and the pen-loop box coming from the labeler in the booth (data/labels/sample_1.json notes), and the rulings frozen in policy.json exactly as the numbers were measured (tests/test_policy.py line 30 asserts that)
Command   make eval (cls_acc in reports/eval_report.json), then HV_POLICY=policy-strict.json HV_CLASSIFIER=off uv run python scripts/evaluate.py, or uv run python scripts/compare_policies.py lines 56 to 80, for the 286 of 286 reading
Sibling   under the strict policy the faded X flips to marked and agreement is 286 of 286 with the same 2 boxes still flagged, and counting only boxes settled without a person the rules score 284 of 284 (reports/compare_readers_report.json, right 284, wrong 0), which dashboard.html line 333 now reads from that file
Bound     one wrong in 286 gives an interval of 0.981 to 0.9999, always answering empty would already score 194 of 286 (67.8%), since the one missed label is an empty box, and the four pages hold 92 marked boxes in total so the marked side rests on fewer than a hundred examples
Knob      ink_filled 0.10 and the scribbled_or_fragmented ruling in policy.json, route or filled rescues the faded X and would also report a scribbled-out box as marked
```

```
Claim     "2 of 287 detections", "0.7%", "Two of 287 detections on the brief pages", "2 of 286 graded" (README.md lines 162, 223, 303, 351, 364 and 366, dimensions.svg line 31, dashboard.html lines 86, 113 and 236, deck slides 6, 10 and 14, the docx, docs/approach.md line 51, docs/iterations.md line 15)
Unit      detected boxes on the four brief pages that carry at least one reason code, 2 of the 287 detections (telemetry) or 2 of the 286 detections matched to a scorable label (compare_readers, now labeled "graded" wherever it appears), both 0.7%, and this 287 is detections while card 1's 287 is labels, they coincide because the one label the detector misses is offset by the one detection sitting on the ignored tick
Match     a box is flagged when its reasons list is non-empty (scripts/telemetry.py line 93, scripts/compare_readers.py line 57), and the two are the No Zoning pen loop (STRAY_STROKE) and the Electricity Public faded X (INK_AMBIGUOUS and FRAGMENTED_MARK), both on the photographed page
Set       the same 4 pages, rules only (HV_CLASSIFIER=off), reason codes as shipped in policy.json, and the tick the labeler called unsure is read marked with no flag, so it is not in the queue, which POLICY.md item 5 now states
Command   make telemetry (reports/telemetry.json, the 4 rows with corpus "sample", flagged 2, 0, 0 and 0) or make compare (reports/compare_readers_report.json, rules queue 2 of 286)
Sibling   on the 61-page mixed set the rate is 2.4% (card 4), on the 5 held-out appraisals it is 0 of 560, and with the CNN switched on the same four pages flag 19 of 287 (6.6%), 56 of 847 with the held-out pages
Bound     2 of 287 gives an interval of 0.08% to 2.5%, so the true four-page rate could be three times the headline, and flagging nothing would score the same 285 of 286 while hiding the one wrong answer inside the file, the flag earns its place because that one wrong answer is one of the two flagged boxes
Knob      the ambiguous band ambiguous_low 0.05 to ambiguous_high 0.20 in policy.json, widening it to 0.03 to 0.30 (the strict file) adds one reason to the pen-loop box and changes no count here, and stray_outside 0.50 decides whether a stroke is passing through or marking
```

```
Claim     "2.4% sent to a person across 61 pages", "138 of 5,872", "64, 56, 16, 9, 1", "1,868 had a mark", "31 of 61 pages", "97.6% settled, 61 pages" (README.md lines 2, 13, 99, 100, 265 and 267, assets/hero.svg lines 13 and 14, architecture.svg lines 43 and 59, queue-reasons.svg lines 9 to 22, dashboard.html lines 70, 80, 81, 90, 91, 100 and 113 to 149, deck slides 4, 12 and 13, docs/EVALS.md line 47, docs/iterations.md line 16, the docx)
Unit      detected boxes carrying at least one reason code over every detected box on the 61-page mixed set (52 synthetic pages damaged on purpose, the 4 brief pages, 5 held-out appraisals), 138 of 5,872 = 2.35%, printed as 2.4% by the one-decimal format tools/check_claims.py also uses, and the reason counts are tags not boxes (146 tags on 138 boxes, a box can carry two), which dashboard.html line 113 says beside the bubble shares
Match     flagged means reasons non-empty (scripts/telemetry.py line 93), the rate is flagged over boxes (line 121), the per-reason counts sum every tag on every box (lines 112 to 114), and no label is involved anywhere in this number, it is what the system flagged, not what it got wrong
Set       61 pages with no answer key for 57 of them, 5,872 is a detection count not a label count, 136 of the 138 flags come from the 52 damaged pages, 2 from the brief pages and 0 from the held-out appraisals, and 31 of 61 pages passed the form-match trust check (trusted_pages, line 126)
Command   make telemetry (uv run --extra train python scripts/telemetry.py, totals under "deterministic core only" in reports/telemetry.json), tools/check_claims.py pins 61 pages, 5,872 boxes and 138 flags and asserts the "61 pages" label on the hero alt text, assets/architecture.svg and the README flowchart, and tools/make_dashboard.py draws the reason bubbles from the same file
Sibling   with the CNN on the same set flags 237 of 5,872 (4.0%), on the brief pages alone it is 2 of 287 (0.7%), and the hardest single damage kind is shading at 18 of 199 (9.05%)
Bound     138 of 5,872 gives an interval of 2.0% to 2.8%, but the set is 86% synthetic damage of two blank forms, so it says how the queue behaves under abuse and nothing about a real production mix, where the only evidence is 0 of 560 on five pages
Knob      the damage recipe in scripts/synth.py (seed 11, 26 conditions), harsher shading or more pen lines raise the rate, and dropping the synthetic pages would leave 2 of 847 (0.2%)
```

```
Claim     "shading 9.05%" through "rotation 1.03%", "watermark 4.17%", "pen 3.12%", "downscaled 2.91%", "several kinds 2.72%", "clean render 2.08%", "JPEG 2.07%", "2.69% one flaw each" (README.md line 278, assets/robustness.svg lines 7 to 30, dashboard.html lines 158 to 196, deck slide 13, docs/EVALS.md line 48)
Unit      flagged detections over detections within one damage kind, shading 18 of 199, watermark 8 of 192, pen 6 of 192, scale 17 of 584, mixed 63 of 2,314, base 4 of 192, JPEG 12 of 579 and rotation 8 of 773, sweep pages grouped by the factor field of data/synth/manifest.json and every mixed page in one group
Match     the same flagged rule as card 4 with no labels involved, grouped by factor (tools/make_dashboard.py by_factor, using the corpus and factor tags scripts/telemetry.py lines 49 to 61 attach)
Set       2 blank forms (118 and 79 boxes) rendered at 300 DPI, marks drawn in by scripts/synth.py, then one damage each on 28 sweep pages and several at once on 24 mixed pages, so every group except mixed, scale, JPEG and rotation is exactly 2 pages, and the denominators are detections (199 on shading against 197 labels, because shading produces 8 false alarms and 6 misses, a net two more detections than labels)
Command   make telemetry, then tools/make_dashboard.py by_factor or tools/draw_figures.py for assets/robustness.svg, whose footer names reports/telemetry.json
Sibling   the same groups scored against their labels give detection F1 0.9646 for shading and 0.9871 for rotation (reports/synth_report.json, card 6), so the queue and the accuracy move together under shading
Bound     shading is 18 of 199 (interval 5.5% to 13.9%) and rotation 8 of 773 (0.45% to 2.0%), every condition sits on 2 pages of one seed, and no group is real paper, so the ordering of kinds is more trustworthy than any single rate
Knob      the damage levels in scripts/synth.py lines 184 to 201 (shading 3 bands, pen 4 lines, rotation 1 to 5 degrees, scale 0.4 to 0.75, JPEG q22 to q60) and seed 11 at line 166
```

```
Claim     "detection F1 on those 52 synthetic pages never drops below 0.965", "0.9646", "worst 0.965 (shading)", "0.980 at 0.5x, 0.990 at 0.4x", "52 pages and 5,122 boxes", "26 different ways" (README.md line 227, dashboard.html lines 200 to 228, deck slide 10, docs/EVALS.md lines 42 and 43, assets/hero.svg line 29)
Unit      detection F1 per damage condition on the synthetic pages, the floor being shading with 191 true pairs, 8 false alarms and 6 misses on 197 labeled boxes across 2 pages, F1 0.9646 (precision 0.960, recall 0.970), and every surface now says detection F1 on the 52 synthetic pages rather than a share read correctly over 61
Match     the same at-least-half overlap and one-to-one greedy pairing as card 1 (scripts/evaluate.py score_synth at line 149 calls score_sample per page and summarize at line 134 per condition)
Set       26 conditions times 2 forms = 52 pages and 5,122 labeled boxes (26 times 197), labels generated with the marks so they carry no human judgment and no seeding bias, mark shapes drawn from MARK_WEIGHTS at scripts/synth.py line 34, and the marks are the generator's imagination rather than scanned ink
Command   make synth, then HV_CLASSIFIER=off uv run python scripts/evaluate.py --synth data/synth --report reports/synth_report.json (the Makefile has no target for this report), and tools/make_deck.py reads the floor from that file rather than typing it
Sibling   on the four real pages the same metric is 0.988 to 1.000, and classification accuracy on the shading pages is 0.9895, so the damage costs detection more than mark reading
Bound     each condition is 2 pages of one seed, the shading recall 191 of 197 has an interval of 0.935 to 0.989, and there is no condition harder than 3 shading bands or 5 degrees, so the floor is the floor of this recipe
Knob      the shading band count (3) and its darkness in scripts/synth.py add_shading, and the 0.5 overlap threshold as in card 1
```

```
Claim     "0 of 560", "118 boxes each", "88 boxes", "68 of the 118", "perfect 1.0", marked 45, 46, 38, 37 and 33 (README.md lines 241 to 253 and 277, dashboard.html lines 167 to 169, deck slides 13 and 16, docs/approach.md line 87, docs/EVALS.md line 47)
Unit      detected boxes on 5 completed appraisal pages fetched from three offices, 560 detections in total with 0 carrying a reason code, and "118 each" is the detection count equalling the 118 slots on the blank standard form
Match     no labels exist for these pages, so "found all 88 boxes and got every mark right" (README.md line 251) is a by-eye inspection, the only computed numbers are the detection count, the marked count and the flag count per page (scripts/telemetry.py lines 91 to 94), and the sentence about two cover pages returning zero boxes is gone because nothing ever scored a cover page
Set       data/holdout, fetched by scripts/fetch_holdout.py after the build, kept out of CI and out of the zip, 4 standard-form pages and 1 condominium page the registry has no blank for, and the condominium page matched the standard form at registration 1.0 with 68 of 118 expected positions agreeing, below the 0.75 trust threshold (src/hv_checkbox/template.py line 200), so its second reader was dropped for that page
Command   uv run python scripts/fetch_holdout.py --score, and the 5 rows with corpus "holdout" in reports/telemetry.json (boxes, checked, flagged, the agree field at 68 of 118, trusted false)
Sibling   with the CNN switched on the Key Realty page flags 37 of its 118 boxes and the other four still flag 0, and the brief's photographed page flags 2 of 42 under the same rules
Bound     0 flags in 560 bounds the true rate below 0.66%, the pages are all standard-form renders from three offices on one vendor's software (a la mode TOTAL, scripts/fetch_holdout.py lines 3 to 4) with no photographs or faxes, so a second rendering vendor is unmeasured, and accuracy on them is unmeasured because nobody labeled a box
Knob      the trust threshold min_agree 0.75, lowering it toward 0.57 would have trusted the wrong form match on the condominium page
```

```
Claim     "36 of 38 human rulings matched", "0.9474", "0.95", "76 close-up crops", "38 hard-graded cards", "49 of the 76 have an ink measurement" (README.md lines 2 and 287, assets/hero.svg line 17, dashboard.html lines 105 and 253, deck slide 13, the docx, docs/EVALS.md line 45, POLICY.md lines 3 and 16, docs/iterations.md line 14)
Unit      gold cards whose ruling the system reproduces, the denominator is the 38 cards from the four real pages ruled filled or empty and not flagged as a suspected misclick (18 filled, 20 empty), out of 76 cards in total
Match     a card is matched to the first detection whose centre lies within 18 pixels of the card centre by city-block distance (scripts/evaluate.py line 188), it counts when that detection exists and its boolean equals the ruling (line 191), and a card with no detection nearby is a miss, which is how 1 of the 2 misses arises
Set       data/gold_set.json, 76 cards ruled by one labeler in the booth before the thresholds were set and frozen 2026-08-27, 27 synthetic cards excluded for having no page coordinates (8 of the 16 not-a-checkbox and 9 of the 10 unsure sit among them), then of the 49 real cards 8 not-a-checkbox (7 from the booth plus c022, re-ruled on 2026-09-03 because its crop is the narrow first-column cell beside the real box, the same cell data/regressions.jsonl row 4 asserts is never detected), 1 unsure and 2 suspected misclicks (c011, c013) are excluded, leaving 38, and the two misses are c021 (the faint box, never detected) and c055 (the faded X, read empty under the shipped policy)
Command   HV_CLASSIFIER=off uv run python scripts/evaluate.py --gold --report reports/gold_report.json (never regenerated by make reports on purpose, see the Makefile comment at the reports target), and the committed layer of tools/check_claims.py holds the hero alt text to that report
Sibling   under the strict policy c055 flips to marked and the count becomes 37 of 38, and on the 286 page-level pairs the same boolean agrees 285 times
Bound     36 of 38 has an interval of 0.82 to 0.99, always answering empty scores 20 of 38 (52.6%), and the 38 cards were chosen as hard cases and anchors, not sampled at random from the boxes
Knob      the 18-pixel matching radius and the not-a-box rejections (the 0.78 aspect floor named in data/regressions.jsonl row 4), a card sitting on a rejected candidate can never score, which is exactly why c022 had to be ruled one way or the other
```

```
Claim     "118/118 and 79/79" reader agreement, "68 of the 118" (docs/EVALS.md line 50, docs/iterations.md line 13, README.md line 253)
Unit      positions the blank-form reader projects onto the page that land on a box the line reader found, over the positions projected, 118 of 118 on the clean scan and 79 of 79 on the manufactured-home page
Match     a projected slot agrees when a detection sits in its row band within the window place() uses (src/hv_checkbox/template.py lines 200 to 231), the page is trusted when agree over projected is at least 0.75 (min_agree at line 200), and a disagreeing row is flagged rather than padded
Set       the 2 blank forms in data/golden (118 and 79 boxes, extracted once by the detector and checked by the blank-form test), applied to the 4 brief pages, of which the photographed crop (14 of 118) and the addendum (28 of 118) fail trust as intended because one is partial and the other is a form the registry lacks
Command   make eval, then the projected, agree and trusted fields under each sample in reports/eval_report.json
Sibling   on the 5 held-out pages it is 118 of 118 four times and 68 of 118 on the condominium page, and across the 61-page set 31 pages pass the trust check
Bound     two full agreements bound the rates at 0.969 and 0.954 or better, and docs/EVALS.md now bands the check at the code's 0.75, so the paper and the code agree on where trust starts
Knob      min_agree 0.75 at template.py line 200, and the row window of 0.55 times the box side named in docs/iterations.md line 14
```

```
Claim     "26 green", "26 gates", "26 test gates", "26 safety gates" (README.md lines 11, 300 and 442, assets/architecture.svg line 10, dimensions.svg line 63, deck slides 11 and 12, the docx, the proposed GitHub description)
Unit      test cases pytest collects in tests/, 5 in test_api.py, 5 in test_pipeline.py (4 per-page floors plus 1), 10 in test_tier1.py (2 blank forms, 7 regression rows, 1 frozen-key check) and 6 in test_policy.py
Match     a green test is one that passed on the run, and tools/check_claims.py measured_tests reads the count from pytest's own collector rather than from any typed number
Set       the floors in tests/test_pipeline.py lines 7 to 15 are F1 0.97 and accuracy 0.95 on the photographed page and 0.99 on the other three, so a fall from 0.988 to 0.97 would still pass
Command   make test (uv run --extra dev pytest -q), and make claims for the badge check
Sibling   the hard pass-or-fail cases cover 4 pages, 2 blank forms and 7 fixed regressions, none of the 26 runs over the 52 synthetic pages or the held-out appraisals, and the claim that two gates were verified by reverting their fix is gone because no log records which two
Bound     a count of tests says nothing about coverage, and the floors sit 1 to 2.6 points below the measured numbers (the photographed page reads 0.9756 against a 0.95 floor), so a small regression passes silently
Knob      the FLOORS dictionary in tests/test_pipeline.py
```

```
Claim     "23,381 weights ONNX", "23,381 weights in a 29KB file", "23,381-weight CNN", "int8 classifier 0.993 held-out", "12 epochs" (README.md line 14, assets/architecture.svg line 41, dashboard.html line 233, docs/approach.md line 45, the proposed GitHub description, docs/iterations.md line 14, deck notes on slide 14)
Unit      parameter elements summed over every initializer tensor in models/patch-int8.onnx, 23,381 in the served file (23,361 in models/patch.onnx before quantization), printed exactly everywhere, and the file is 29,423 bytes
Match     the 0.993 has no match rule, it is accuracy at a 0.5 probability threshold on the sweep crops printed by scripts/train.py line 141 for the int8 artifact (sha256 b63c8774), served through onnxruntime by src/hv_checkbox/patch_model.py on 32 by 32 crops
Set       training crops are the 24 mixed synthetic pages plus real page crops minus every gold-card location (scripts/train.py lines 41 to 76), validation is the 28 sweep pages, so 0.993 is measured on synthetic marks the generator drew and on no human ruling
Command   make claims (tools/check_claims.py measured_weights counts the tensors and fails the build if the badge differs by one), and make train (12 epochs, scripts/train.py line 82) reprints the 0.993, not rerun here because it trains
Sibling   on the 286 human-labeled boxes the same model alone is confident on 230 and right on 229, and its disagreement flags 17 more boxes than the rules on the brief pages (card 12)
Bound     0.993 on synthetic validation is a ceiling not a floor, the training record is a printed line with no saved report, and scripts/train.py line 1 still says "~25k-parameter" in a code comment, which is not reader-facing
Knob      the quantization to int8 (23,381 against 23,361 elements) and the 0.5 threshold on the printed accuracy
```

```
Claim     "2 of 286 graded, 56 of 286, 19 of 286", "from 2 boxes to 19", "17 boxes", "229 of 230", "15 of 118 (12.7%)", "37 of 118", "queued the empty pen loop at p(filled) 0.845 and read the filled faded X as empty at 0.082", "56 of 847 (6.6%)" (README.md lines 163, 235, 241 and 279, dashboard.html lines 236 to 244, deck slides 6, 14 and 16 and the slide 14 notes, the docx, docs/EVALS.md line 49, docs/ROADMAP.md line 34, docs/approach.md line 81, docs/iterations.md line 16)
Unit      the 286 detections matched to a scorable label on the brief pages, read three ways, each box landing in exactly one of sent to a person, settled right or settled wrong, and 6.6% is 56 of 847 boxes flagged with the model on (the 4 brief pages plus the 5 held-out), or 19 of 287 on the brief pages alone
Match     no overlap rule, the CNN is models/patch-int8.onnx (sha256 b63c8774) scored over 32 by 32 crops of the rules pass's boxes, a probability between 0.10 and 0.90 is sent to a person and otherwise the 0.5 side is compared to the label (scripts/compare_readers.py lines 78 to 85), and in the both mode a disagreement with the rule adds CLASSIFIER_DISAGREE to the box (grade() at line 51)
Set       the same 286 labels as card 2, the two hard boxes are gold cards and so were excluded from training, the CNN scores the empty pen-loop box 0.845 (queued) and the filled faded X 0.082 (wrong), which the report now records under hard_cards for every hard-real gold card the detector finds, and "15 of 118" and "37 of 118" are the clean scan and the Key Realty page in reports/telemetry.json with the model on
Command   make compare (uv run --extra train python scripts/compare_readers.py writes reports/compare_readers_report.json, the three rows plus hard_cards), and make telemetry for the 15 of 118, the 37 of 118 and the 56 of 847
Sibling   on the 5,872-box mixed set the model on takes the queue from 138 to 237, and its disagreement tags fall on 55 of 847 real-page boxes against 121 of 5,025 synthetic ones
Bound     one wrong in 230 confident answers gives an interval of 0.976 to 0.9999, the comparison is 286 boxes from 4 pages, and the number to beat is the rules-only row of 2 queued and 0 wrong, which the model fails on queue size alone
Knob      the 0.10 to 0.90 band, narrowing it to 0.25 to 0.75 shrinks the 56 and would move the 0.845 pen loop into the wrong column
```

```
Claim     "273 ms median", "301 ms p95", "p50 50 ms and p95 64 ms", "a median of 50 ms", "273 ms of one CPU core" (README.md lines 155, 161, 170, 199, 200, 237 and 363, assets/dimensions.svg lines 27, 42 and 44, alternatives.svg line 14, dashboard.html lines 95 and 96, deck slides 6, 7, 9 and 13, docs/approach.md line 49, docs/EVALS.md line 51)
Unit      two instruments, never on one line without their names, the in-process time of detect_with_page per page over the 61-page set (median 273.2 ms, p95 300.9 ms, mean 245.0 ms, reports/telemetry.json) and the HTTP round trip of POST /detect for 120 requests of sample_1.jpg at concurrency 1 (p50 50.0 ms, p95 64.4 ms, max 81.5 ms, reports/bench_report.json)
Match     the in-process p95 is the sorted element at 0.95 times n (scripts/telemetry.py line 124), the HTTP p95 is the element at 0.95 times n minus 1 (scripts/bench.py line 44), each from one run, and no timing is checked by CI (tools/check_claims.py's header says timings are never chased)
Set       one machine (an arm64 laptop with 18 cores) and one run on Fri 9/4, rules only for telemetry, and the bench report now comes from the Makefile's bench target exactly as written (sample_1.jpg, 120 requests, concurrency 1, 4 and 8), where the previous report had been run by hand on sample_2.png with 40 requests
Command   make telemetry (p50_ms and p95_ms in the totals), then make serve and make bench (scripts/bench.py with its defaults, writing reports/bench_report.json)
Sibling   at concurrency 4 the same bench reads p50 193 ms and p95 209 ms, at 8 p50 398 ms and p95 439 ms, and the photographed page reads in 47 ms in-process (its telemetry row), which is why its HTTP round trip sits far below the in-process median that the 300 DPI forms dominate
Bound     120 requests of the smallest page make the HTTP p95 the 114th fastest of 120, the previous committed run on a different day read 284 ms in-process and 392 ms over HTTP on a different page, so both numbers are properties of the box and the page they ran on, and the median of 61 pages is 86% synthetic renders of two forms
Knob      the template scale search in src/hv_checkbox/template.py, and the 2x upscale for pages under 1,400 px wide (src/hv_checkbox/pipeline.py line 42)
```

```
Claim     "0.99 to the 96 = 38% of the time, so 62% of pages carry at least one wrong answer" (dashboard.html line 403)
Unit      an arithmetic illustration, the chance that a page of 96 boxes is entirely right when each box is right with probability 0.99, 96 being 5,872 boxes over 61 pages (96.26)
Match     none, tools/make_dashboard.py computes 100 times 0.99 to the power boxes_per_page and its complement
Set       the 0.99 is an assumed per-box rate for a hypothetical reader, not this system's measured 285 of 286
Command   make dashboard
Sibling   at the measured 0.9965 per box the same page is clean 71% of the time, and a full standard form has 118 boxes, where 0.99 gives 31% clean
Bound     it is a formula rather than a measurement, and it assumes box errors are independent, which a shaded row or a bad scan makes false
Knob      the assumed 0.99 and the boxes-per-page average
```

```
Claim     "51 down to 2", "52 to 61", "61 to 4", "4 to 2", "flat since v2" (dashboard.html lines 333 and 391 to 395)
Unit      boxes carrying an ambiguity reason on the four brief pages at each version v1 to v7, summed from the amb column of docs/iterations.md (1/38/12/0 = 51 at v1, 2/0/0/0 = 2 at v7)
Match     tools/make_dashboard.py iteration_history() parses the markdown table, and an assertion holds the first sum to 51 and the last to 2
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
Set       the shipped code at commit 974cf48, and only 5 of the 12 appear as box reasons in reports/telemetry.json rules only (a sixth, CLASSIFIER_DISAGREE, with the model on), THIN_MARK and the three verdicts never fired on this corpus, and the rejected lists in that file also carry TEXT_LIKE_SIZE_OUTLIER once and SIZE_CONSENSUS 43 times, a label scripts/telemetry.py line 86 invents rather than the code emitting it
Command   grep -rhoE '"[A-Z][A-Z_]{4,}"' src/hv_checkbox/*.py | sort | uniq | grep -v '^"HV_' as box reasons, since the bare grep also returns the three HV_ environment names
Sibling   the queue reasons that actually occurred are 5 (card 4)
Bound     a code count is a vocabulary size, not a coverage measure
Knob      the ROUTED set
```

```
Claim     "roughly two hundred boxes of free, unarguable ground truth" (docs/approach.md line 17), the blank official forms as a hard test (README.md lines 180 and 287, deck slide 8)
Unit      checkboxes on the 2 blank official renders in data/golden, 118 on Form 70 page 1 and 79 on Form 70B page 1, 197 in all, every one expected empty
Match     tests/test_tier1.py lines 20 to 26 assert the detector finds at least as many boxes as the .boxes.json file lists and reports zero marked, no overlap pairing is done, so an extra box on a blank form passes
Set       the .boxes.json coordinates were extracted once by the detector itself (data/README.md line 25), so the count is the detector agreeing with its own earlier output, and the blank forms are also the source images for all 52 synthetic pages, which dashboard.html line 68 now says
Command   make test (the two golden cases in tests/test_tier1.py)
Sibling   the same 197 boxes with marks drawn in score F1 0.9769 on the undamaged render (reports/synth_report.json, base, 7 misses and 2 false alarms), so adding marks alone costs 7 boxes
Bound     2 forms from one publisher at 300 DPI, and a count check that cannot fail on false alarms
Knob      the assertion is at least, not exactly, at tests/test_tier1.py line 25
```

```
Claim     "the CNN adds 3.9 ms to a 118-box page", "3.9 ms per 118-box page on CPU", "30.4 us per crop" (dashboard.html line 240, deck slide 14 notes, the proposed GitHub description, reports/cnn_latency.json)
Unit      wall time of PatchScorer.score() over the boxes the rules pass found on one brief page, scoring only, the median of 30 timed passes after 5 warm-ups, and per crop is that median divided by the page's box count (sample_2.png, 118 boxes, 3.92 ms, 33.3 us per crop)
Match     none, tools/bench_cnn.py loads models/patch-int8.onnx through the same PatchScorer the pipeline uses (6 pooled Scan sessions, POOL_WORKERS at src/hv_checkbox/patch_model.py) and times only the score call
Set       the 4 brief pages, 287 crops, on a Mac17,8 (Apple M5 Pro, 18 cores, named in the report's machine block), 8.72 ms for all four pages, 30.4 us per crop, per page 1.04, 3.92, 2.04 and 1.72 ms
Command   make bench-cnn (uv run --extra train python tools/bench_cnn.py --out reports/cnn_latency.json)
Sibling   the pipeline's own page time is 273 ms median in-process (card 13), so the model adds about 1.4% to the page it costs the most, and the classifier mode's p50 in reports/telemetry.json is 274 ms against 273 rules only
Bound     one machine and one run, a number no CI chases, the previous description's "2.5 ms" matched no file, and a live pass on 2026-09-02 that timed a cold session read 27 to 59 ms per page, so a warm pooled scorer and a cold single session are different instruments
Knob      POOL_WORKERS (6 here) and the repeat count
```

```
Claim     "about 110 tokens of image", "one 110-token crop", "110 tokens a crop" (README.md lines 157, 162 and 364, assets/dimensions.svg line 33, deck slide 6, docs/approach.md line 53, reports/crop_tokens.json)
Unit      image tokens of the crop src/hv_checkbox/escalate.py crop_png builds for one box (the box grown 2.2 times its size on every side, scaled so the whole crop is about 260 px across and the box about a fifth of that, a magenta outline drawn on), counted as one visual token per 28 by 28 pixel patch, ceil of width over 28 times ceil of height over 28, the median over every box the rules pass finds on the four brief pages, 110
Match     the patch rule and the tier limits are the Claude API vision doc's own (standard tier 1,568 px long edge and 1,568 tokens, high-resolution tier 2,576 px and 4,784 tokens, URL and read date in the report), a crop never downscales because it sits far below both limits, and the PNG byte size (36 to 71 KB on the two routed crops) is a separate quantity the report does not quote
Set       287 crops on the four brief pages, per-page medians 100, 120, 110 and 100, and the two boxes the shipped run actually routes (both on the photographed page, whose boxes are the smallest) come out at 100 and 100 because their crops are 278 by 255 and 277 by 266 px, ten patches by ten
Command   make crop-tokens (HV_CLASSIFIER=off uv run python tools/crop_tokens.py --out reports/crop_tokens.json)
Sibling   a whole page under the same rule is 1,550 tokens median on the standard tier (the tier's 1,568-token cap does the downscaling) and 4,752 on the high-resolution tier, from the same report, about fourteen and forty-three times the crop, and the tier has to be named or the page number means nothing
Bound     the rule is the vendor's published billing rule as read on 2026-09-04 and it has changed before (the previous revision of this file used 750 pixels per token), and the crop count moves with box size, so a page with 59 px boxes and a page with 23 px boxes land 20 tokens apart
Knob      the 2.2 grow factor and the 260 px target in escalate.crop_png, and the tier the caller is billed on
```

## Cited, not measured here

F1 0.88 (Tatsu YOLOv8-large, 300 documents), about 96% (Evoke YOLOv5), about 95% (wendys-llc EfficientNet-B0) and $10 per 1,000 pages (Azure) are third-party figures sourced in docs/EVALS.md lines 12 to 15. They appear in README.md lines 192, 198 and 199, assets/alternatives.svg lines 34 and 37, deck slides 6 and 9, docs/approach.md line 67 and docs/ROADMAP.md line 26, and they keep their source wherever they appear.

## Regenerated on Fri 9/4

- make eval gives tp 286, fp 0, fn 1, F1 0.998, classification 0.997, per page 0.988, 1.000, 1.000, 1.000, flagged 2, 0, 0, 0. Matches, and the committed report is this run.
- scripts/evaluate.py --gold gives 38 graded, 36 correct, 0.9474, misses c021 and c055. The committed report is this run.
- make telemetry gives 5,872 boxes, 138 flagged (2.4%), reasons 64, 56, 16, 9, 1, with the model on 237 flagged and 176 disagreements, p50 273.2 ms and p95 300.9 ms rules only. Counts match the previous run, the timings are this run's, and the committed report is this run.
- make compare gives queue 2, 56, 19, right 284, 229, 267, wrong 0, 1, 0, plus hard_cards with the pen loop at 0.845 queued and the faded X at 0.082 wrong. The committed report is this run.
- make bench, the target as written, gives 120 requests of sample_1.jpg at concurrency 1 p50 50.0 ms and p95 64.4 ms, and concurrency 4 and 8 p50 193 and 398 ms. The committed report is this run, and because that page is the smallest of the four, docs/EVALS.md line 51 no longer calls the /detect band in band on its strength.
- make bench-cnn gives 287 crops in 8.72 ms across the four pages, 30.4 us per crop, the 118-box page in 3.92 ms. The committed report is this run.
- make crop-tokens gives a median of 110 tokens over 287 crops under the 28-pixel patch rule, the two routed boxes at 100 and 100, and a page at 1,550 standard and 4,752 high resolution. The committed report is this run.
- pytest -q, 26 passed. make claims, tests 26, F1 0.998, queue 2.4, weights 23,381, the three hero labels, the architecture label and the flowchart label, all OK.
- python3 ~/.claude/skills/referee_card/find_claims.py . gives 1,047 claim-shaped snippets, none of the removed numbers among them outside this file.

## GitHub description, proposed and not yet applied

The live About field still reads "23K-weight CNN (ONNX, 2.5 ms CPU)". The replacement below quotes reports/cnn_latency.json and the exact weight count, and is 347 characters against the 350 GitHub allows. It changes a public surface, so it is applied by hand, never by a script.

```
Deterministic pipeline reading checkboxes off appraisal forms, with OpenCV dual-reader detection, customer-owned policy file and human exception queue. A from-scratch 23,381-weight CNN (ONNX int8, 3.9 ms per 118-box page on CPU, make bench-cnn) raced the rules and ships switched off. FastAPI, Docker, 26 test gates, F1 0.998 on the 4 brief pages.
```
