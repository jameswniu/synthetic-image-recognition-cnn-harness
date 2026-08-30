# Dataset card

Everything the referees run on, what made it, and what it may not represent.

## samples/

The four document images supplied with the assignment, untouched. Three are full-page renders of
standardized appraisal forms (URAR page 1, the Market Conditions Addendum, the Manufactured Home
report page 1); one is a photographed crop of a URAR section from a different rendering vendor, with
skew, JPEG noise, handwriting, a tick, and a scan-faded X. These four are the only real-world data
in the project, and every claim about real pages rests on them alone.

## labels/

Page-level ground truth for the four samples: every checkbox bbox, its state, and an `ignore` flag
for artifacts that are not checkboxes and for cards the labeler ruled unsure. Provenance is stated
per box in its `note`: labels were seeded by running the detector, then corrected against zoomed
crops by eye, then overridden where the booth labeler ruled otherwise. Seeding from the detector
biases the boxes toward what the detector already finds; the golden renders and the booth cards are
the counterweights, and the bias is the first thing to fix with independent labeling in production.

## golden/

Blank official form renders (Freddie Mac Form 70 and Form 70B, 300 DPI via pdftoppm) with
`.boxes.json` coordinate files extracted once by the detector and verified by the blank-form gate:
every box present, none filled. Blank forms make detection ground truth free: nothing on them is a
mark, so any fill read on them is a false positive by construction. Form 71 (the 1004MC twin) has no
public Freddie download; its slot in the registry is a to-do, and the addendum sample stands in.

## cards/ and gold_set.json

The booth cards: crops the human labels, mixing the planted hard cases from the samples, ordinary
anchors, non-checkbox negatives, and synthetic judgment cases (circle marks, scribbled-out marks,
partial strokes, stray handwriting, broken and hand-drawn borders, faint and degraded and rotated
crops, radio circles). `gold_set.json` is the frozen referee built from the human's answers; it is
never trained on, and the exclusion is enforced by a gate, not a convention.

## synth/

Seeded synthetic pages generated from the golden renders by `scripts/synth.py`: policy-shaped marks drawn
into known boxes, then page degradations (rotation, scale, JPEG, blur, noise, shading bands,
colored watermark text, stray pen lines). Labels transform with the geometry, so the set carries
exact ground truth at zero labeling cost. `manifest.json` records the seed; regeneration is
byte-identical and gated. Synthetic marks inherit their creator's imagination, which is the known
cost of synthesis; the sweeps exist to measure robustness, not to prove realism.

## regressions.jsonl

One row per probe-found failure, paired with the behavior that fixes it. The contract is that every
row passes on every run; the slice tests memory of fixed failures, not generalization.

## judge_votes.json

The escalation lane's recorded exam: per routed crop, the voters' answers, the judge's adjudication
when they disagreed, and the final route. Replays are served from this file, so offline behavior is
deterministic and the exam is auditable after the fact.
