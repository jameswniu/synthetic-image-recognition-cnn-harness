# The escalation lane and its judge, in software terms

Only boxes the deterministic pipeline routed ever reach a model: ambiguous ink, fragmented marks,
stray strokes, thin marks like the tick, classifier disagreements, template-only finds, and
witness disputes. That set exists because the labeling policy says unsure is an answer; the lane
exists so unsure has somewhere to go that is cheaper than a human and more honest than a guess.

## Mechanics

Two voters of different tiers (Claude Haiku 4.5 and Claude Sonnet 5) read the routed crop blind:
the zoomed image with the box outlined, the policy question, and nothing else. Agreement on both
questions (is it a checkbox, is it filled) decides the box with `VLM_AGREE`. Disagreement goes to a
stronger judge (Claude Opus 5) that sees the crop, both votes, and the deterministic evidence (ink
fraction, reason codes, witnesses), and must answer with a confidence; below 0.6 the deterministic
answer stands and the box is tagged `REVIEW`. The lane is off by default (`HV_ESCALATE=1` plus an
Anthropic credential turns it on), and with it off the API's behavior is byte-identical to the
deterministic core.

## Containment, which is the trust story

The lane's authority is bounded four ways. It only sees routed boxes, never the page. Its verdicts
can flip a routed box's state but never remove a box or touch an unrouted one. Every call lands in
`data/judge_votes.json` keyed by crop hash: the votes, the adjudication, the final route. And
replays are served from that record, so offline runs are deterministic and the exam is auditable
after the fact rather than trusted on vibes.

The known pitfalls of judge models are treated as constraints, not footnotes: position bias and
self-preference (the judge sees structured votes, not a favored position; voters are different
tiers), calibration (an explicit confidence floor, below which the judge changes nothing),
non-determinism (the recorded-replay contract), and the documented checkbox blind spot of VLMs
(which is why the lane verifies routed crops and never detects).

## The recorded exam

`data/judge_votes.json` holds every recorded exchange. Regenerate the routed set and replay with:

```bash
HV_ESCALATE=1 uv run python -m hv_checkbox.escalate data/samples/sample_1.jpg --live   # record
uv run python -m hv_checkbox.escalate data/samples/sample_1.jpg                        # replay
```

If the file in this submission carries no votes, the lane shipped implemented and off: no live
credential was spent on it before the freeze, and the deterministic core, which is the graded
surface, does not depend on it.
