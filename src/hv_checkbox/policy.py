"""What counts as a marked box, as data rather than as constants we ship.

Every number here used to be a module constant in `classify.py`. They are the same numbers; what
changed is where they live. Accuracy on this problem is not a property of the detector, it is a
definition somebody else gets to write down: one lender may want a circle drawn in a box to count
as a selection, another may want it sent to a person, and both are correct for their file. Asking
us to edit `classify.py` for that is the wrong shape.

`POLICY.md` is the prose version of these same decisions, written by the person who labelled the
gold set. This file is the machine-readable half, and the two are meant to be read together.

Resolution order: an explicit path, then `HV_POLICY`, then `policy.json` at the repo root, then
the defaults below. The defaults are exactly the values that were hard-coded before, so a checkout
with no policy file behaves identically to the one that produced every number in the README.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# What the API reports for a box that a rule has singled out. Every one of these still carries a
# reason code, so the box is flagged either way; the choice is only what boolean rides along.
#   "filled"  call it selected
#   "empty"   call it not selected
#   "route"   report the raw ink lean and let the reason code speak, per POLICY.md rule 5
RULINGS = ("filled", "empty", "route")


@dataclass(frozen=True)
class Policy:
    """Acceptance criteria for a single customer."""

    name: str = "default"

    # How much ink inside the box reads as a selection, and the band around it that nobody
    # should be confident about.
    ink_filled: float = 0.10
    ambiguous_low: float = 0.05
    ambiguous_high: float = 0.20
    confidence_scale: float = 0.04

    # One dominant stroke crossing the box settles what raw ink cannot. Span is measured inside
    # the 15% inset interior, whose own diagonal is 0.70 of the box's, so 0.45 is a real crossing.
    clear_mark_span: float = 0.45
    clear_mark_dominance: float = 0.60
    clear_mark_ink: float = 0.06

    # A thin contained stroke: a tick, a light X.
    thin_mark_span: float = 0.55
    thin_mark_ink: float = 0.02

    # A stroke with this share of its pixels outside the grown box is passing through, not marking.
    stray_outside: float = 0.50

    # Many small blobs and no dominant stroke: text in a cell, or a box scribbled out.
    fragment_components: int = 4
    fragment_largest: float = 0.08
    fragment_ink_ceiling: float = 0.50

    # The three rulings a customer actually argues about, in their language.
    thin_single_stroke: str = "filled"
    stray_stroke_through_box: str = "empty"
    scribbled_or_fragmented: str = "empty"

    def __post_init__(self) -> None:
        for field_name in ("thin_single_stroke", "stray_stroke_through_box", "scribbled_or_fragmented"):
            value = getattr(self, field_name)
            if value not in RULINGS:
                raise ValueError(f"policy {self.name!r}: {field_name} is {value!r}, expected one of {RULINGS}")
        if not self.ambiguous_low <= self.ink_filled <= self.ambiguous_high:
            raise ValueError(
                f"policy {self.name!r}: ink_filled {self.ink_filled} must sit inside the ambiguous band "
                f"[{self.ambiguous_low}, {self.ambiguous_high}], or the band cannot do its job"
            )


DEFAULT = Policy()


def from_dict(data: dict) -> Policy:
    """Build a Policy from parsed JSON. Anything not recognised is an error, not a shrug.

    A key beginning with an underscore is a note to the reader and is skipped; the shipped files use
    that for their own explanations. Every other unrecognised key raises.

    Silently dropping a misspelling was the first cut and it was wrong. This file is the customer's
    trust boundary for what counts as a mark, so `ambigous_high` quietly falling back to our default
    would report our answers under their policy name, with nothing failing anywhere they could see.
    A typo in a file that decides what a mark is has to be loud.
    """
    known = {f.name for f in fields(Policy)}
    unknown = sorted(k for k in data if k not in known and not k.startswith("_"))
    if unknown:
        raise ValueError(
            f"policy {data.get('name', '?')!r}: unrecognised key(s) {unknown}. "
            f"Known keys are {sorted(known)}. Prefix a key with _ to keep it as a note."
        )
    return Policy(**{k: v for k, v in data.items() if k in known})


def load(path: str | Path) -> Policy:
    """Read a policy file. Raises if it is missing or malformed, because a policy that silently
    fell back to ours would be the worst of both worlds: the customer's file ignored, our numbers
    reported under their name."""
    p = Path(path)
    data = json.loads(p.read_text())
    if "name" not in data:
        data["name"] = p.stem
    return from_dict(data)


_ACTIVE: Policy | None = None


def active() -> Policy:
    """The policy in force: `HV_POLICY`, else `policy.json` at the repo root, else the defaults."""
    global _ACTIVE
    if _ACTIVE is None:
        env = os.environ.get("HV_POLICY", "").strip()
        if env:
            _ACTIVE = load(env)
        elif (ROOT / "policy.json").exists():
            _ACTIVE = load(ROOT / "policy.json")
        else:
            _ACTIVE = DEFAULT
    return _ACTIVE


def use(policy: Policy | None) -> None:
    """Set the active policy for this process, or pass None to re-resolve from the environment."""
    global _ACTIVE
    _ACTIVE = policy
