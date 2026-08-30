# Approach, tradeoffs, and what it cannot do

## What I decided first

The brief asks for a service that finds every checkbox on a document image and says whether it is marked. I read the four sample pages before writing any code. They are the assignment.

One is a clean scan. One has blue shaded rows. One has a watermark stamped across several boxes. The last is a photograph. It carries skew, compression noise, a tick instead of an X, ink so faded it is barely there, and a pen stroke running through an empty box. Four pages, four different problems, one of them deliberately unanswerable.

That told me the interesting part is not detection. It is knowing which boxes have a right answer and which ones do not. So I built the grading before I built the system.

## What good means, before how

Three separate things define correct here, and none of them is my opinion.

The first is the four pages themselves, labeled box by box. I seeded those labels from an early run and then corrected them by eye, which biases them toward what the software already finds. I have stated that bias rather than hidden it, and the next two referees exist partly to counter it.

The second is the blank official forms. The agencies publish them, and a blank form has a useful property: nothing on it is marked. Rendered at full resolution, every square is a checkbox and every one is empty. A missed box or an invented mark there is a mistake with no argument available. That gives roughly two hundred boxes of free, unarguable ground truth.

The third is human judgment, collected properly. I built a small labeling tool and put seventy-six close-up crops in it. A person answered one question about each crop: marked, empty, not a checkbox at all, or genuinely unclear. The crops mixed hard cases from the real pages with synthetic ones I generated. Some had circles instead of X marks, a mark scribbled out, or a single stroke. Others had handwriting crossing an empty box, broken borders, or faded and rotated versions.

Those answers were collected before the thresholds were tuned, and they settled things I could not have decided alone. A scribbled-out box is not a marked box; it is a box struck from the form. A stray pen line through a box is not a mark. A circle drawn in a box is a case nobody should answer confidently. All of that is written down in POLICY.md, and the system is measured against it.

Those three referees answer whether the system is right. They do not answer the question underneath, which is right according to whom. A circle drawn inside a box, a box filled in and then struck out, a tick that overshoots the border: each has a defensible answer in both directions, and none of them belongs to me. One lender wants the circle counted and another wants it sent to a person, and both are correct about their own files.

So the acceptance criteria are a file rather than constants in the classifier. `policy.json` carries the thresholds and the three rulings people actually argue about, each taking `filled`, `empty`, or `route`, and `POLICY.md` is the same decisions in prose. `scripts/compare_policies.py` scores two of them against each other on the same pages: two boxes read differently and agreement with the answer key moves from 285 of 286 to 286 of 286, with no source file touched.

The stricter policy is not simply the better one, which is the part worth sitting with. It gets the scan-faded X right by refusing to overrule ink on a fragmented mark, and that same rule would let a scribbled-out box report as filled. Choosing which of those errors to carry is a business decision, and putting it in a file is how it stops being mine.

On top of the labels sits a generator. It draws marks into the known boxes of the blank forms and then damages the page on purpose: rotation, shrinking, compression, blur, shading, watermarks, stray pen. Because it knows where it put every mark, the labels come free and transform with the geometry. It is ordinary code with a fixed seed, no model involved, and regenerating it identically is one of the checks that has to pass. That check has already earned its place by catching a real bug.

## Two readers, and a reader that knows when to stop

Detection runs twice, independently.

The first reader knows nothing about appraisals. It separates ink from paper, keeps only the straight horizontal and vertical strokes, and looks for small closed squares of a size the page itself votes on. Everything that lives inside a checkbox is diagonal or curved. A mark, a watermark, and handwriting all vanish from that view, and the empty interior shows up as a hole.

The second reader knows one thing more: these are standard federal forms. It recognizes which form it is looking at from the pattern of ruled lines, then matches the boxes it expects against the boxes the first reader found, row by row.

Getting that second reader working took the evening's most useful failure. The textbook method matches distinctive points between two images, and it does not work here, because two software vendors rendering the same federal form use different fonts and different spacing. I measured it: the best possible uniform stretch still leaves individual sections off by anywhere from a hundred and thirty pixels in one direction to nearly four hundred in the other. Vendors reflow the sections independently. What survives is the order of the ruled lines, so the alignment matches sequences rather than stretching coordinates.

Where both readers agree, the box is settled. Where they disagree, nothing is quietly dropped: the box is reported with a note saying why it is in question.

Reading the mark itself is layered. How much ink is inside the box settles the easy majority. Shape settles what quantity cannot. One dominant stroke crossing the box is a mark even when it is thin. A scatter of specks is text rather than a mark. A stroke that keeps going well past the border is handwriting passing through, and that one is traced across the whole page rather than guessed from the crop.

A small trained model rides alongside as a second opinion on the mark. It is deliberately tiny, about twenty-five thousand parameters, because with four real pages any extra capacity would be spent memorizing my own generator. It can raise confidence when it agrees and flag a box when it does not, and it can never overrule the deterministic read.

## Where the AI sits, and what that costs

Nothing in the reading path is an AI model. That path is ordinary image processing: a median of 284 ms per page on one processor core measured across 61 pages, roughly four millionths of a dollar, and identical output on identical input forever. Through the HTTP service the round trip is p50 392 ms, and that gap is the web layer rather than the reading. That last property is not aesthetic. When someone asks in twelve months why a file recorded a particular answer, the system can be re-run to show them.

The AI sits behind the exception queue, which on these pages holds 0.7% of boxes. Only a flagged box, cropped to a thumbnail, is ever sent to a model. Two inexpensive models look at it independently; a stronger one settles it only when they disagree. Every call is recorded, and replays come from the record, so offline behavior stays reproducible.

That design is arithmetic before it is philosophy. A cropped checkbox is about a hundred tokens of image. A whole page is about two thousand, and a full-page answer runs to thousands more because it has to list every box and its coordinates. Sending every page to a strong model costs roughly forty times more per page than flagging and asking about the small fraction that is genuinely unclear, and published work on document AI finds checkbox reading is a specific weak spot for vision models. Spending more to get less is a bad trade twice over.

There is a version of this argument that goes further and says never use a model. I do not believe that either. The faded X and the pen stroke are cases where two careful people disagree, and that is exactly where a second opinion is worth buying, so long as it cannot invent a box, cannot delete one, and cannot act without leaving a record.

## Tradeoffs I chose

Deterministic first and learning second, because auditability is the product in this domain and every threshold here is inspectable.

Knowledge about forms as data rather than code, so a new form revision is a file, not a release.

Synthetic coverage instead of scraped data, because the forms are public and standardized while the marks are the variable, and synthesis buys exact labels at the cost of a creator's blind spots. Those blind spots are why the four real pages and the human labels are graded separately.

A small model instead of a large one, for the reason given above.

The two obvious alternatives fail in opposite directions, and naming how is part of choosing. The way this was built five years ago is an OCR engine plus a trained object detector, and the published numbers are respectable: F1 0.88 for a YOLOv8-large checkbox detector over three hundred mixed documents, around 96% for a YOLOv5 build. It does not lose on accuracy. It loses because the definition of a mark is frozen inside the weights, so a customer who wants circles counted needs a labelling round and a retrain, and there is nowhere to look up why any single box was read the way it was. The way it would be built today is to send the whole page to a frontier vision model, which pays about forty times more per page to read something a hundred pixels wide, gives up determinism, and ships whole customer documents to a third party to answer a question that never needed to leave the building.

Where this approach would be the wrong one is worth saying too. On thousands of unseen layouts, with no requirement to explain any single answer and no customer disagreeing about what counts as a mark, the frontier model is the right call and everything here is over-engineering. This problem is the opposite of that on all three counts.

## What it cannot do

The faded mark on the photographed page is unresolved by design. The system flags it rather than deciding it, and in a strict count that costs a point.

One checkbox on that same page is printed so faintly that the labeler called it a box and the software cannot see it at all. That is a real miss and it is counted.

Rejecting a candidate is the one place this system removes evidence instead of flagging it, and that is a real tradeoff rather than a free win. A candidate is only rejected when two independent things are true at once: its height is off the page's own median, and its interior holds several small ink blobs with no dominant stroke. A genuine mark is one stroke, so a marked box does not satisfy the second condition; but an empty box that is both an odd size and has print bleeding into it would be removed rather than queried. Across the nine real pages, both blank forms and the entire synthetic corpus that rule fires on exactly one candidate, the invented box it was written for. The alternative was to keep the candidate and flag it rather than remove it, and an adversarial reviewer pushed for exactly that three times, so it is worth saying why I went the other way. Dropping candidates is what a detector does: the aspect floor drops narrow table cells, the ring-ink filter drops holes punched in solid black bars, and the size consensus drops letter holes. Three of the regression rows exist to assert those stay dropped. A rule that never removed anything would return every square-ish region on the page with a note attached, which moves the work to a person instead of doing it. What I owe instead is that each rule be narrow, measured, recorded and reversible, and that is what the paragraph above describes. If this were carrying real files I would want the disagreement settled by data rather than by argument: measure how often the rule fires across a few thousand real pages, and how often a person disagrees with it, which is the same disagreement-sampling loop the roadmap opens with.

It is also resolution-dependent, and I would rather say so than let someone find it: the rule needs the interior text to still resolve into separate blobs, so on the same page rendered at half size the invented box survives. That is the honest shape of the tradeoff, and it argues for normalising resolution on the way in rather than for a cleverer rule. Every rejection is recorded and returned under `?explain=true`, so the removal can be audited rather than taken on trust, and a regression row fails the build if that particular box ever comes back at full size.

The small trained model is not yet paying for itself, and the measurement says so plainly. Switched on it changes no answer on any of the four pages, and it takes the review queue from 2 boxes to 19 by disputing 17 the rules read correctly. On one held-out page it disputes 37 of 118. A second opinion that never changes the answer and triples or quadruples the review bill is a cost with no benefit attached, so every flag rate in this repo is quoted for both configurations rather than for the flattering one. The fix is to let its disagreement count only where the deterministic read is already near a boundary, and to grade that on the queue it produces.

Downscaling has a floor. Below roughly thirteen pixels per box the size estimate loses its footing, and the correct fix is normalizing resolution before the page arrives rather than pushing the detector further.

One of the three form types has no publicly published blank, so that page runs on the first reader alone and says so in its output.

Real-world variety is thin. The brief supplied four pages, and after finishing I found five more: completed sample reports published by three unrelated appraisal offices, none of them seen during the build. The four standard appraisals among them each returned 118 boxes, matching the blank federal form exactly, with nothing flagged by the deterministic core. The fifth was a condominium form the system has no template for; it read all 88 boxes correctly, matched the wrong form at a perfect score, and was saved by the agreement check behind it, which found only 68 of 118 expected positions and marked the reading untrusted.

Those nine pages are still not a benchmark. The five held-out ones carry no box-by-box labels, so I checked them by eye rather than scoring them, and all nine come from a narrow slice of the software that produces these documents. Closing that gap means running against real volume, sampling where the two readers disagree, and putting those crops in front of a person, which is the first step of the roadmap.

The labels on the four pages were seeded by the software before correction, and that shortcut cost me. Reviewing them by eye caught most of the errors but not all. One box the detector had invented around a printed word survived into the label file, where it then graded itself as correct. What caught it was the second reader counting four boxes in a row the official form gives three. It could not say which one was wrong, and in fact accused a real checkbox, because it matches expected positions in order and the invented box came first. I had written that disagreement off as a quirk of the vendor's rendering, which was wrong. The detector now checks a candidate against the size of the other boxes on the page and looks for text inside it, and the bad label is gone. The lesson generalizes: ground truth seeded from the system under test hides exactly the errors that system is prone to.

## How I worked

I directed an AI coding agent through this build the way I run production work. Grading first, a measurement before each design commitment rather than after, every change scored against frozen references, and each failure the tests surfaced turned into a permanent check or a new question for the human labeler.

The architecture, the tradeoffs, and the words here are mine. The agent multiplied the hours. The commit history is the audit trail, including the parts that did not work.
