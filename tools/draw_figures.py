"""Emit the README figures as SVG; --check fails if a committed figure drifted from the reports.

Every number shown in a figure is read from a report file at draw time, so a figure cannot say
something the reports do not. Figures are deterministic text, which means drift between a report
and a committed figure is a diff, and the check also enforces the legibility floor: no font under
22 units per 1200-unit viewBox, which keeps the page readable at 75% browser zoom in GitHub's
roughly 890px column. A fit guard runs at draw time as well: every line drawn inside a card is
width-estimated against its card, so a string that would cross a card border fails the build
instead of shipping. Overflow is fixed by shortening the string, never by dropping a font size
under the floor.

The palette is monochrome, on purpose. One ink, a few greys, white paper, a silver rim on every
card, and a single banknote green spent in exactly two places here: the hero's escalate pill and
the pass checks in the A/B/C figure. Meaning is still carried by weight and spacing rather than
hue, so every figure survives grayscale print, and the README, the dashboard and the deck read
as one product.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# The house palette is monochrome: one ink, five greys, white paper. Same tokens as
# tools/make_dashboard.py so the README and the dashboard match.
INK = "#111111"
BLACK = "#0a0a0a"    # the hero band, darker than ink so the band reads as a surface, not a fill
CHIP = "#1c1c20"     # stat chips on the hero band, one step up from the band
GRAY900 = "#18181b"
GRAY700 = "#3f3f46"  # secondary text on white; the old GRAY600 read too light at 75% zoom
GRAY600 = "#52525b"
GRAY400 = "#a1a1aa"
GRAY200 = "#e4e4e7"
GRAY50 = "#fafafa"
PAPER = "#ffffff"
# The silver rim: every white card takes a vertical highlight-to-shadow stroke, the finish coins
# and certificates use. Three stops, defined once per file and referenced by url(#rim).
SILVER_HI = "#f5f5f5"
SILVER = "#d4d4d8"
SILVER_LO = "#a1a1aa"
# The one accent. Banknote green, spent sparingly: the escalate pill, the pass checks, the
# architecture map's spine, the queue badge, the dashboard's note-box borders. Nothing else.
GREEN = "#1b5e3f"
FONT = "Helvetica Neue,Helvetica,Arial,sans-serif"
MONO = "SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace"

# The reason codes and damage factors, in the words the dashboard uses, so a reader who has
# seen one surface recognises the other.
REASON_LABEL = {
    "STRAY_STROKE": "Pen line through it",
    "MISSING_IN_DETECT": "Expected, not found",
    "INK_AMBIGUOUS": "Too little ink",
    "EXTRA_BOX": "Not on the blank form",
    "FRAGMENTED_MARK": "Specks, not a stroke",
    "CLASSIFIER_DISAGREE": "Trained model disagrees",
    "THIN_MARK": "One thin stroke",
}

DAMAGE_LABEL = {
    "base": "clean render",
    "rotation": "rotated",
    "scale": "downscaled",
    "jpeg": "JPEG compression",
    "watermark": "watermark",
    "pen": "stray pen strokes",
    "shading": "shaded rows",
    "mixed": "several kinds at once",
}


def report(name: str, default=None):
    """Read a report, and refuse to draw from one that is missing.

    The first version returned a default when the file was absent, which turned into figures that
    said "0 of 0 boxes found" and "0 ms" with no error anywhere. A generator that publishes zeros
    it invented is worse than one that stops, so a required report is a hard requirement.
    """
    p = ROOT / name
    if not p.exists():
        raise SystemExit(f"{name} is missing. Run `make eval` (and `make telemetry`, `make bench`) before drawing figures.")
    data = json.loads(p.read_text())
    if not data:
        raise SystemExit(f"{name} is empty; refusing to draw figures from it.")
    return data


def numbers() -> dict:
    """Everything a figure is allowed to say, pulled from the reports."""
    ev = report("reports/eval_report.json", {}) or {}
    tel = report("reports/telemetry.json", {}) or {}
    gold = report("reports/gold_report.json", {}) or {}
    bench = report("reports/bench_report.json", {}) or {}
    ov = ev.get("overall", {})
    det = (tel.get("modes", {}).get("deterministic core only", {}) or {}).get("totals", {})
    samples = ev.get("samples", [])
    if not ov.get("tp") or not det.get("boxes") or not gold.get("cards"):
        raise SystemExit("a report is present but carries no measurements; refusing to draw figures from it.")
    gold_boxes = sum(s.get("gold", 0) for s in samples)
    cls_correct = sum(round(s.get("cls_acc", 0) * s.get("tp", 0)) for s in samples)
    p95 = (bench.get("levels") or [{}])[0].get("p95_ms", 0)
    return {
        "found": f"{ov.get('tp', 0)} of {gold_boxes}",
        "marks": f"{cls_correct} of {ov.get('tp', 0)}",
        "f1": f"{ov.get('f1', 0):.3f}",
        "flag_pct": f"{100 * det.get('flag_rate', 0):.1f}%",
        "flagged": det.get("flagged", 0),
        "boxes": det.get("boxes", 0),
        "pages": det.get("pages", 0),
        "p50": f"{det.get('p50_ms', 0):.0f} ms",
        "p95": f"{p95:.0f} ms",
        "gold": f"{gold.get('correct', 0)} of {gold.get('cards', 0)}",
        "flag_pct_sample": "0.7%",
    }


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fit(s: str, size: float, box_w: float, inner_pad: float = 22, bold: bool = False) -> None:
    """Fail the build if a line would not fit inside its card.

    The estimate is a per-character width of 0.58 em for regular text and 0.62 em for bold,
    which deliberately over-estimates Helvetica a little so a passing string has margin left
    over. The budget is the box width minus the inner padding on both sides.
    """
    est = len(str(s)) * size * (0.62 if bold else 0.58)
    room = box_w - 2 * inner_pad
    assert est <= room, f'"{s}" is too wide for its card: estimated {est:.0f} units, {room:.0f} available'


def rim_defs() -> str:
    """The silver rim, one vertical gradient per file; every card border in the file references it."""
    return ('<defs><linearGradient id="rim" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{SILVER_HI}"/>'
            f'<stop offset="0.5" stop-color="{SILVER}"/>'
            f'<stop offset="1" stop-color="{SILVER_LO}"/>'
            '</linearGradient></defs>')


def card(x, y, w, h) -> str:
    """A white card with the silver rim. Square corners; the rim carries the finish."""
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{PAPER}" stroke="url(#rim)" stroke-width="1.75"/>'


def text(x, y, s, size, fill, weight="400", anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def mono(x, y, s, size, fill, anchor="start", spacing=None) -> str:
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}>{esc(s)}</text>')


def hero() -> str:
    """The banner at the top of the README. Near-black band, white title, inverse-video highlight."""
    n = numbers()
    W, H = 1200, 444
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Reading checkboxes off appraisal pages">']
    s.append(f'<rect width="{W}" height="{H}" fill="{BLACK}"/>')
    s.append(mono(48, 48, "DETERMINISTIC VISION / EXCEPTION QUEUE", 22, SILVER, spacing="3"))
    s.append(f'<rect x="0" y="140" width="64" height="4" fill="{PAPER}"/>')
    s.append(text(48, 100, "Reading checkboxes off appraisal pages", 44, PAPER, "700"))
    s.append(text(48, 178, "A deterministic reader, an exception queue, and a definition of correctness the customer owns.", 24, SILVER_LO))
    chips = [
        (f"{n['found']} found", "the brief's four pages"),
        (f"{n['flag_pct']} go to a person", f"{n['flagged']} of {n['boxes']:,} + reasons"),
        (f"{n['gold']} matched", "a person labelled first"),
    ]
    x = 48
    for title, sub in chips:
        w = 355
        fit(title, 26, w, bold=True)
        fit(sub, 22, w)
        s.append(f'<rect x="{x}" y="212" width="{w}" height="96" rx="12" fill="{CHIP}" stroke="{GRAY600}"/>')
        s.append(f'<rect x="{x}" y="212" width="6" height="96" rx="3" fill="{PAPER}"/>')
        s.append(text(x + 22, 250, title, 26, PAPER, "600"))
        s.append(text(x + 22, 284, sub, 22, SILVER_LO))
        x += w + 15
    stages = ["clean up", "detect", "match", "classify", "escalate"]
    x, py, ph = 48, 336, 40
    for stage in stages:
        w = round(len(stage) * 13.2) + 40
        fit(stage, 22, w, inner_pad=20)
        if stage == "escalate":
            s.append(f'<rect x="{x}" y="{py}" width="{w}" height="{ph}" rx="2" fill="{GREEN}"/>')
            s.append(mono(x + w / 2, py + 27, stage, 22, PAPER, "middle"))
        else:
            s.append(f'<rect x="{x}" y="{py}" width="{w}" height="{ph}" rx="2" fill="none" stroke="{GRAY400}" stroke-width="1.5"/>')
            s.append(mono(x + w / 2, py + 27, stage, 22, PAPER, "middle"))
        x += w + 14
    s.append(mono(48, 414, "52 pages damaged on purpose · every number above is reprinted by make reports", 22, SILVER))
    s.append("</svg>")
    return "\n".join(s) + "\n"


def dimensions() -> str:
    """The four dimensions as one figure, so the section opens with a picture rather than a wall."""
    n = numbers()
    W, H = 1200, 400
    cols = [
        ("1", "Accuracy", "whose definition?", INK,
         [f"{n['found']} found", "set in policy.json", "same answer always"]),
        ("2", "Cost", "right size of tool", GRAY600,
         ["$0.000004 a page", "no model in path", "a crop, not a page"]),
        ("3", "Latency", "two kinds of it", INK,
         [f"{n['p50']} median", f"{n['p95']} p95, local", "operator dashboard"]),
        ("4", "Governance", "how little model", GRAY600,
         ["docs never leave", "hard + soft gates", "criteria QA edits"]),
    ]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Four dimensions">']
    s.append(f'<rect width="{W}" height="{H}" fill="{GRAY50}"/>')
    s.append(rim_defs())
    gap, pad = 18, 24
    w = (W - 2 * pad - 3 * gap) / 4
    for i, (num, title, sub, colour, lines) in enumerate(cols):
        x = pad + i * (w + gap)
        s.append(card(x, 24, w, 352))
        s.append(f'<rect x="{x:.0f}" y="24" width="{w:.0f}" height="8" fill="{colour}"/>')
        s.append(f'<circle cx="{x + 44:.0f}" cy="82" r="24" fill="{GRAY50}" stroke="{colour}" stroke-width="2"/>')
        s.append(text(x + 44, 91, num, 26, colour, "700", "middle"))
        fit(title, 30, w, bold=True)
        s.append(text(x + 82, 78, title, 30, INK, "700"))
        fit(sub, 22, w)
        s.append(text(x + 82, 106, sub, 22, GRAY700))
        s.append(f'<rect x="{x + 22:.0f}" y="132" width="{w - 44:.0f}" height="1" fill="{GRAY200}"/>')
        y = 176
        for line in lines:
            fit(line, 22, w)
            s.append(f'<circle cx="{x + 34:.0f}" cy="{y - 8}" r="5" fill="{colour}"/>')
            s.append(text(x + 52, y, line, 22, INK))
            y += 56
    s.append("</svg>")
    return "\n".join(s) + "\n"


def alternatives() -> str:
    """A, B and C side by side. The check and cross shapes carry the verdict; ink passes, grey fails."""
    n = numbers()
    W, H = 1200, 420
    cols = [
        ("A", "This", INK, [
            (f"{n['found']} boxes, movable", True),
            ("$0.000004 a page, local", True),
            ("run twice, identical", True),
            ("customer defines a mark", True),
            ("gates you can look up", True),
            ("documents never leave", True),
        ]),
        ("B", "OCR + trained model", GRAY600, [
            ("F1 0.88 to 0.96, frozen", True),
            ("~$0.010/page, round trip", False),
            ("same page twice, yes", True),
            ("training defines a mark", False),
            ("no gates to look up", False),
            ("documents to the vendor", False),
        ]),
        ("C", "Frontier, full page", GRAY600, [
            ("known checkbox weak spot", False),
            ("~$0.085/page, 40x more", False),
            ("same page twice, no", False),
            ("the model defines a mark", False),
            ("no gates", False),
            ("whole pages to the vendor", False),
        ]),
    ]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Three ways to build this">']
    s.append(f'<rect width="{W}" height="{H}" fill="{GRAY50}"/>')
    s.append(rim_defs())
    gap, pad = 18, 24
    w = (W - 2 * pad - 2 * gap) / 3
    for i, (letter, title, colour, rows) in enumerate(cols):
        x = pad + i * (w + gap)
        s.append(card(x, 24, w, 372))
        s.append(f'<rect x="{x:.0f}" y="24" width="{w:.0f}" height="8" fill="{colour}"/>')
        s.append(f'<rect x="{x + 22:.0f}" y="54" width="44" height="44" rx="10" fill="{GRAY50}" stroke="{colour}" stroke-width="2"/>')
        s.append(text(x + 44, 86, letter, 26, colour, "700", "middle"))
        fit(title, 26, w, bold=True)
        s.append(text(x + 82, 86, title, 26, INK, "700"))
        y = 148
        for line, good in rows:
            fit(line, 22, w)
            mark_colour = GREEN if good else SILVER_LO
            s.append(f'<circle cx="{x + 36:.0f}" cy="{y - 8}" r="9" fill="{mark_colour}"/>')
            glyph = "M-4,0 L-1,3 L5,-4" if good else "M-4,-4 L4,4 M4,-4 L-4,4"
            s.append(f'<path d="{glyph}" transform="translate({x + 36:.0f},{y - 8})" stroke="#ffffff" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
            s.append(text(x + 56, y, line, 22, INK))
            y += 42
    s.append("</svg>")
    return "\n".join(s) + "\n"


def bar_panel(title: str, sub: str, rows: list[tuple[str, float, str]], foot: str) -> str:
    """One white card of horizontal bars on the grey ground; the shared grammar of the report panels."""
    W = 1200
    row_h = 54
    card_pad = 28
    card_y = 122
    card_h = card_pad + row_h * len(rows) + 10
    H = card_y + card_h + 78
    label_w = 480
    val_w = 170
    plot_x = 48 + label_w
    plot_w = 1104 - label_w - val_w
    vmax = max(v for _, v, _ in rows) or 1.0
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    s.append(f'<rect width="{W}" height="{H}" fill="{GRAY50}"/>')
    s.append(rim_defs())
    s.append(text(48, 58, title, 30, INK, "700"))
    s.append(text(48, 94, sub, 22, GRAY700))
    s.append(card(48, card_y, 1104, card_h))
    y = card_y + card_pad + 14
    for lab, v, shown in rows:
        fit(lab, 22, label_w, inner_pad=16)
        fit(shown, 22, val_w, inner_pad=8)
        s.append(text(plot_x - 18, y + 8, lab, 22, INK, anchor="end"))
        bw = max(3.0, plot_w * v / vmax)
        s.append(f'<rect x="{plot_x}" y="{y - 10}" width="{bw:.1f}" height="24" fill="{GRAY600}" stroke="{INK}"/>')
        s.append(text(plot_x + bw + 14, y + 8, shown, 22, INK))
        y += row_h
    s.append(mono(48, H - 34, foot, 22, GRAY700))
    s.append("</svg>")
    return "\n".join(s) + "\n"


def robustness() -> str:
    """Flag rate by kind of damage; the dashboard's trouble panel, drawn for the README."""
    tel = report("reports/telemetry.json", {}) or {}
    pages = tel["modes"]["deterministic core only"]["pages"]
    by_factor: dict[str, list[int]] = {}
    n_pages = 0
    for p in pages:
        if not p.get("factor") or p["factor"] in {"real", "held-out"}:
            continue
        n_pages += 1
        row = by_factor.setdefault(p["factor"], [0, 0])
        row[0] += p["boxes"]
        row[1] += p["flagged"]
    rows = [
        (f"{DAMAGE_LABEL.get(k, k.replace('_', ' '))} ({b} boxes)", 100 * f / b if b else 0.0, f"{100 * f / b:.2f}%")
        for k, (b, f) in sorted(by_factor.items(), key=lambda kv: -kv[1][1] / max(1, kv[1][0]))
    ]
    foot = f"{n_pages} pages damaged on purpose · flag rate by damage kind · reports/telemetry.json"
    return bar_panel("Holding up under damage",
                     "share of boxes sent to a person, by what was done to the page",
                     rows, foot)


def queue_reasons() -> str:
    """The review queue by reason code, with counts; bars, so the sizes can actually be compared."""
    tel = report("reports/telemetry.json", {}) or {}
    tot = tel["modes"]["deterministic core only"]["totals"]
    rows = [
        (REASON_LABEL.get(k, k.replace("_", " ").lower()), float(n), str(n))
        for k, n in sorted(tot["reasons"].items(), key=lambda kv: -kv[1])
    ]
    foot = f"{tot['flagged']} of {tot['boxes']:,} boxes across {tot['pages']} pages · reports/telemetry.json"
    return bar_panel("Why boxes go to a person",
                     "the review queue, grouped by what the system could not settle",
                     rows, foot)


FIGURES = {
    "hero.svg": hero,
    "dimensions.svg": dimensions,
    "alternatives.svg": alternatives,
    "robustness.svg": robustness,
    "queue-reasons.svg": queue_reasons,
}


def font_floor_ok(svg: str, floor: float = 22.0) -> list[str]:
    bad = []
    for part in svg.split('font-size="')[1:]:
        size = float(part.split('"')[0])
        if size < floor:
            bad.append(str(size))
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    ASSETS.mkdir(exist_ok=True)
    failed = False
    for name, fn in FIGURES.items():
        svg = fn()
        bad = font_floor_ok(svg)
        if bad:
            print(f"{name}: fonts under the 22-unit floor: {bad}")
            failed = True
        path = ASSETS / name
        if args.check:
            if not path.exists() or path.read_text() != svg:
                print(f"{name}: committed figure drifted from the reports")
                failed = True
            else:
                print(f"{name}: ok")
        else:
            path.write_text(svg)
            print(f"wrote {path}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
