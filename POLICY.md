# Checkbox Policy (frozen 2026-08-27)

Extracted from the labeler's 76-card session in the Checkbox Booth (`labeling/labeling-booth.html`). This
file is the human-judgment ground truth that steers synthetic generation, the ambiguous band, and
the escalation lane. The labeled set itself is `data/gold_set.json`, frozen, never trained on.

## Class policies as labeled

Anchors came back clean: every confident filled anchor confirmed, the negatives (letter holes,
narrow cells, sidebar artifacts) all ruled not-a-checkbox. Two anchor cards came back filled where
the 6x crop shows a plainly empty box; they are recorded as answered, flagged as suspected
misclicks, and excluded from hard grading pending the labeler's confirmation.

1. An intentional mark of any shape selects the box. Every one of the detector's ambiguous-band
   reads (ink between 3% and 35%) that showed a deliberate mark was ruled filled, six of six,
   including the scan-faded X whose strokes survive only as specks. The band leans filled; when the
   system cannot decide, it routes rather than calling empty.
2. Stray ink is not a selection. All three synthetic stray-stroke cards and the real pen loop
   through the No Zoning box were ruled empty. A stroke that passes through and keeps going is
   handwriting, not intent, which is exactly what the stroke trace tests.
3. A scribbled-out box is struck from the form. All three scribble cards were ruled not-a-checkbox:
   obliteration removes the control entirely rather than filling it. The system should route these
   (FRAGMENTED_MARK or the escalation lane), never report them as filled.
4. Circles, single diagonal strokes, and radio-style circles are genuinely unsure, eight cards
   across the three shapes. They are boundary cases by policy: excluded from hard grading, required
   to sit in the ambiguous band or route, never confidently decided either way.
5. The check-mark tick is unsure by the labeler's ruling. The pipeline reads it as a contained
   dominant stroke and reports filled with moderate confidence, and it stays in the routed set so
   the escalation lane or a reviewer sees it; that treatment is consistent with the filled-leaning
   band and the unsure ruling both.
6. Hand-drawn boxes are checkboxes (one filled, one empty, as drawn). Print quality does not decide
   control-hood by itself.
7. Degradation can destroy a checkbox. Two of three heavily faded or JPEG-crushed cards were ruled
   not-a-checkbox: past some damage the square stops being a control and becomes noise. The third
   was readable and ruled on its mark.
8. The faint grey square beside Neighborhood Boundaries is an empty checkbox by ruling. The
   detector misses it (the border sits far below every threshold), and that miss is counted
   honestly in the metrics rather than defined away.

## Boundary set

Nine cards were ruled unsure (the tick, the circles, the partial strokes, the radio circles, one
broken-border card). They are excluded from hard accuracy grading; a good system sits near the
threshold on them or routes them, and being confidently wrong in either direction counts against it.

## Consequences wired into the system

The ambiguous ink band routes instead of deciding; the stroke trace separates stray ink from marks;
fragmented marks are downgraded; scribbled-out and mutilated boxes belong to the routed set; the
escalation lane and the review queue exist because the policy says unsure is an answer. Where the
API must still return a boolean for a routed box, it reports the deterministic lean and carries the
reason codes alongside, so a downstream consumer can distinguish a decided box from a routed one.
