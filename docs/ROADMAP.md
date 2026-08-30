# Roadmap: from take-home to production

The ladder, in the order the rungs pay for themselves. Each rung keeps the deterministic core as the
cross-check and grows the golden set; nothing on it replaces the referee structure, only feeds it.

## 1. Real scans at volume

The honest gap tonight is distribution: four real pages and one scanner. The first production step
is boring and decisive: run the pipeline in shadow over real appraisal uploads, sample disagreements
between the two witnesses (and later between rule and model), and route those crops to human
labelers through the same booth. Disagreement sampling spends review effort exactly where the
information is; the agreement rate doubles as a drift alarm that fires before anyone labels anything.

## 2. Template registry as data

Every form revision (1004, 1004MC, 1004C, the condo and desktop variants, both GSE brandings) gets a
golden render, extracted coordinates, and a UAD field name per box, all versioned. Form identity
then does double duty: field semantics come free with the template ("this box is
`PropertyRightsAppraised = FeeSimple`"), which is what the downstream decisioning actually consumes.
A page that matches no template is itself a signal (new vendor rendering, new revision) and lands in
a queue, not in silent degradation.

## 3. Detector lane behind the same referees

When labeled real scans exist, fine-tune a small detector (the YOLO family is the well-trodden path;
public checkbox models reach F1 ~0.88 on mixed documents) with the deterministic pipeline as its
auto-labeler and disagreement filter. It ships only if it beats the deterministic core on the same
frozen sets, and the two run as cross-checks either way: structural disagreement stays the routing
signal at every rung.

## 4. State classifier upgrades

The measured problem comes first. On the four sample pages the patch CNN changes no answer and
raises 17 disagreements on boxes the rule read correctly, taking the review queue from 2 boxes to
19. As a flag-raiser it currently generates noise, so the first change is to let its disagreement
count only where the deterministic read is already near a boundary, and to grade that change on the
queue it produces rather than on accuracy, which it does not move either way. Calibration is the
measurement that tells you where that boundary sits.

The tiny patch CNN is deliberately small. With volume, calibrate it (temperature scaling against the
gold cards), then grow it only as the gold set proves the headroom. The escalation lane's recorded
verdicts become weak labels for exactly the crops the cheap readers find hard, which is the only
place capacity is worth buying.

## 5. The judge under governance

The VLM voters and judge stay bounded: routed crops only, votes recorded, replayable, and evaluated
as their own model against a dispute set with known answers. Under model risk management (SR 11-7,
superseded April 2026 by SR 26-2 / OCC Bulletin 2026-13), that is the difference between a
component that can pass validation and one that cannot: deterministic validated extraction
auto-feeds decisioning; non-deterministic components are inventoried, monitored, and human-backed
where they touch credit-critical fields.

## 6. Page-level semantics

Checkbox groups carry constraints the box-level system does not know yet: exactly-one-of groups
(Occupant), conditional requirements (an "If yes, describe" that must be blank when No is marked),
cross-field consistency. Encoding those as deterministic validations over the extracted states is
cheap, catches upstream mistakes that box-level metrics cannot see, and produces the reason codes
underwriters actually want.
