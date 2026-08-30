# Checkbox Detection: Workflow and Labeling Guide

The take-home in one sentence: given a scanned appraisal page, find every checkbox and say whether it is filled, through `POST /detect`.

## The loop (who does what)

```
taxonomy (below)
   -> booth cards (~75, spread across the taxonomy, a third of them synthetic judgment cases)
   -> JAMES LABELS them (the human judgment that defines "filled")
   -> frozen gold set + written policy per judgment class
   -> golden blank forms (free detection truth) + seeded synthetic pages (policy-guided degradations)
   -> two deterministic witnesses + state classifier -> eval against the frozen sets -> iterate
   -> edge miner turns sweep failures into the next round of booth cards
   -> FastAPI serving + Dockerfile, deterministic-only by default, escalation behind a flag
   -> writeup + figures
```

James is the policy judge: he labels the cards, rules on the unsure ones, and reviews the metrics whenever he likes. Claude runs everything else. James is in the loop at exactly one door, the submission. Everything else is reversible.

## The decision being made

For every square on the page the system answers two questions: is this a checkbox at all, and if so did someone mean to select it. Two ways to be wrong on each, with different costs. A missed box silently drops a field from the underwriting record. A phantom box invents one. Reading an empty box as filled asserts something the appraiser never said; reading a filled box as empty loses what they did say. On a form where one box switches a property between "manufactured home" and "site built", either error is a decision error downstream, so the system is built to know when it does not know and to route those cases rather than guess.

## Scenario taxonomy: label against these

Samples come from real appraisal forms (URAR 1004, the Market Conditions Addendum 1004MC, the Manufactured Home report 1004C) plus synthetic cards built from a clean render. The magenta outline marks the square the card asks about.

Anchor classes (expected to be easy; they sanity-check the labeler and the model):

| Class | Shape | Expected |
|---|---|---|
| A | Printed box, clean X | Filled |
| B | Printed box, nothing inside | Empty |
| C | Printed box inside a blue-shaded cell, black X | Filled |
| D | Printed box with a watermark stroke crossing it, no mark | Empty |
| E | Printed box, thick or slightly overshooting X | Filled |
| F | A letter's hole, a narrow table cell, a rendering artifact | Not a checkbox |

Judgment classes (your labels set the policy; there is no textbook answer):

| Class | Shape | The tension |
|---|---|---|
| G | Scan-faded X, only specks of the strokes survive | Was it marked, or is this noise? |
| H | Tick, circle, single diagonal, partial mark | Which mark shapes count as selection? |
| I | An X then dense scribble over it | Selected then retracted, or emphatically selected? |
| J | Handwriting or a pen loop passing through an otherwise empty box | Stray ink is not a selection, but where is the line? |
| K | Broken, faint, or hand-drawn box borders | Still a checkbox when the printing failed? |
| L | Heavy JPEG, blur, rotation | Same answer as the clean version, or unsure past some point? |
| M | Radio-style circle, signature or initials cell | Checkbox, or a different control entirely? |

## What your labels produce

1. A frozen gold set of cards the pipeline is never tuned on: the referee.
2. A written policy per judgment class, which steers how synthetic pages are generated and what the ambiguous band means.
3. The operating thresholds: where the ink rule and the patch classifier stop deciding on their own and start routing.

## Measurement (the zero and the one)

The zero: a plain contour-and-threshold detector with a fixed ink threshold, the thing every quick solution does. The one: two witnesses that agree on the easy cases, a state reader that knows its own ambiguous band, and a routed remainder, all scored on the frozen sets and on synthetic sweeps, inside a serving budget that leaves room for a document pipeline in front of it.
