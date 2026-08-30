"""The policy file is customer-facing, so it gets the same treatment as the serving contract.

Two things have to stay true. The shipped policy.json must reproduce exactly the numbers every
document in this repo quotes, or the README is describing a system nobody is running. And a
different policy must actually change an answer, or the whole claim that a customer can define
accuracy without a code change is decoration.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import pytest

from hv_checkbox import policy as policy_module
from hv_checkbox.pipeline import detect_with_page

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"


@pytest.fixture(autouse=True)
def _restore_policy():
    yield
    policy_module.use(None)


def test_shipped_policy_matches_the_defaults_the_numbers_were_measured_with():
    """policy.json is the file; Policy() is what classify.py falls back to. They must agree.

    If these drift, the published results were produced by one and the shipped repo runs the other,
    which is the same class of defect as reporting a classifier-off number under a classifier-on
    heading. Every field is compared, not a sampled few.
    """
    shipped = policy_module.load(ROOT / "policy.json")
    default = policy_module.DEFAULT
    for field in ("ink_filled", "ambiguous_low", "ambiguous_high", "confidence_scale",
                  "clear_mark_span", "clear_mark_dominance", "clear_mark_ink",
                  "thin_mark_span", "thin_mark_ink", "stray_outside",
                  "fragment_components", "fragment_largest", "fragment_ink_ceiling",
                  "thin_single_stroke", "stray_stroke_through_box", "scribbled_or_fragmented"):
        assert getattr(shipped, field) == getattr(default, field), (
            f"policy.json {field}={getattr(shipped, field)!r} but the code default is "
            f"{getattr(default, field)!r}; one of them produced the published numbers and the other did not"
        )


def test_a_different_policy_actually_changes_an_answer():
    """Non-vacuous by construction: this fails if the two shipped policies read every box alike."""
    img = cv2.imread(str(SAMPLES / "sample_1.jpg"))

    policy_module.use(policy_module.load(ROOT / "policy.json"))
    _, a, _ = detect_with_page(img)
    policy_module.use(policy_module.load(ROOT / "policy-strict.json"))
    _, b, _ = detect_with_page(img)

    lhs = {tuple(x.bbox): x.is_checked for x in a}
    rhs = {tuple(x.bbox): x.is_checked for x in b}
    changed = [k for k in lhs if k in rhs and lhs[k] != rhs[k]]
    assert changed, "the two shipped policies read every box identically, so the demo proves nothing"


def test_a_ruling_outside_the_vocabulary_is_refused():
    """A typo in a customer's file must fail loudly rather than silently fall back to ours."""
    with pytest.raises(ValueError, match="thin_single_stroke"):
        policy_module.from_dict({"name": "typo", "thin_single_stroke": "checked"})


def test_a_threshold_outside_its_own_band_is_refused():
    with pytest.raises(ValueError, match="ambiguous band"):
        policy_module.from_dict({"name": "bad", "ink_filled": 0.9, "ambiguous_low": 0.05, "ambiguous_high": 0.20})


def test_underscore_keys_are_notes_and_load_fine():
    """The shipped files carry _what_this_is and similar. Loading must not choke on them."""
    p = policy_module.from_dict({"name": "noted", "_why": "because", "ink_filled": 0.12,
                                 "ambiguous_low": 0.05, "ambiguous_high": 0.20})
    assert p.ink_filled == 0.12

    for name in ("policy.json", "policy-strict.json"):
        raw = json.loads((ROOT / name).read_text())
        assert any(k.startswith("_") for k in raw), f"{name} lost its explanatory notes"
        policy_module.load(ROOT / name)


def test_a_misspelled_key_fails_loudly_instead_of_falling_back_to_ours():
    """A typo in the customer's file must not silently ship our defaults under their name.

    This is the whole reason the file exists. If `ambigous_high` is quietly dropped, the customer
    believes they widened the review band, the system keeps our band, and nothing anywhere tells
    them otherwise. Wrong answers under their own policy name is the worst available outcome.
    """
    with pytest.raises(ValueError, match="unrecognised key"):
        policy_module.from_dict({"name": "typo", "ambigous_high": 0.30})

    with pytest.raises(ValueError, match="unrecognised key"):
        policy_module.from_dict({"name": "typo", "scribbled_or_fragmented_mark": "route"})
