#!/usr/bin/env python3
"""Reusable SVG design system for production-grade analytical reports."""

from __future__ import annotations

from html import escape
from typing import Iterable

WIDTH = 1200

# Neutral foundation
CANVAS = "#EEF3F8"
PAPER = "#FFFFFF"
INK = "#0B1324"
INK_SOFT = "#263449"
MUTED = "#617084"
QUIET = "#8B98A9"
GRID = "#D9E2EC"
GRID_DARK = "#B9C6D5"
NAVY = "#0B1F3A"
NAVY_2 = "#13345B"
MIDNIGHT = "#07152A"

# Restrained categorical roots. Tints are used for surfaces, never to encode a
# second meaning that is absent from labels or shapes.
BLUE = "#246BFD"
BLUE_DARK = "#174EA6"
BLUE_TINT = "#E8F0FF"
TEAL = "#008C82"
TEAL_DARK = "#006E67"
TEAL_TINT = "#DDF5F2"
GOLD = "#C69214"
GOLD_DARK = "#8B6400"
GOLD_TINT = "#FFF2C7"
CORAL = "#D85B43"
CORAL_DARK = "#A63C2A"
CORAL_TINT = "#FCE7E2"
VIOLET = "#7257D9"
VIOLET_DARK = "#5038A6"
VIOLET_TINT = "#EEEAFE"
MAGENTA = "#B9487C"
MAGENTA_DARK = "#8C2E5B"
MAGENTA_TINT = "#F9E6EF"
GREEN = "#4E7D32"
GREEN_DARK = "#355B20"
GREEN_TINT = "#E8F2DF"

SUCCESS = "#26734D"
SUCCESS_TINT = "#E3F3EA"
WARNING = "#B06A00"
WARNING_TINT = "#FFF0D8"
DANGER = "#B33A3A"
DANGER_TINT = "#FBE7E7"

FONT_STACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif'
MONO_STACK = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

DOMAIN_THEME_RULES = [
    # Specific decision environments precede generic cross-cutting disciplines.
    (("health", "clinical", "biostat", "population"), (TEAL, TEAL_DARK, TEAL_TINT)),
    (("urban", "planning", "regeneration"), (CORAL, CORAL_DARK, CORAL_TINT)),
    (("marketing",), (MAGENTA, MAGENTA_DARK, MAGENTA_TINT)),
    (("supply", "operations", "system"), (GREEN, GREEN_DARK, GREEN_TINT)),
    (("behavior", "decision science"), (GOLD, GOLD_DARK, GOLD_TINT)),
    (
        ("finance", "financial", "fintech", "credit", "capital", "accounting"),
        (VIOLET, VIOLET_DARK, VIOLET_TINT),
    ),
    (
        ("artificial intelligence", "responsible ai", "ai ", "technology"),
        (BLUE, BLUE_DARK, BLUE_TINT),
    ),
    (("policy", "governance"), (GOLD, GOLD_DARK, GOLD_TINT)),
]

CATEGORY_PALETTE = [BLUE, TEAL, GOLD, CORAL, VIOLET, MAGENTA, GREEN]


def theme_for(domain: str) -> tuple[str, str, str]:
    """Return accent, dark accent, and tint for a domain label."""
    normalized = f"{domain.casefold()} "
    for tokens, theme in DOMAIN_THEME_RULES:
        if any(token in normalized for token in tokens):
            return theme
    return BLUE, BLUE_DARK, BLUE_TINT


def wrap_words(value: str, chars: int) -> list[str]:
    words = value.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + len(word) + 1 <= chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def text(
    x: float,
    y: float,
    value: str,
    *,
    css: str = "label",
    anchor: str = "start",
    fill: str | None = None,
    transform: str | None = None,
) -> str:
    attrs = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'class="{css}"', f'text-anchor="{anchor}"']
    if fill:
        # Inline style intentionally overrides class-level default fills.
        attrs.append(f'style="fill:{fill}"')
    if transform:
        attrs.append(f'transform="{transform}"')
    return f'<text {" ".join(attrs)}>{escape(value)}</text>'


def wrapped_text(
    x: float,
    y: float,
    value: str,
    *,
    chars: int,
    line_height: int = 18,
    css: str = "label",
    anchor: str = "start",
    fill: str | None = None,
) -> str:
    return "\n".join(
        text(
            x,
            y + index * line_height,
            line,
            css=css,
            anchor=anchor,
            fill=fill,
        )
        for index, line in enumerate(wrap_words(value, chars))
    )


def rounded_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str = PAPER,
    stroke: str = GRID,
    radius: int = 14,
    stroke_width: float = 1,
) -> str:
    elevation = (
        f'<rect x="{x + 2:.1f}" y="{y + 6:.1f}" width="{width:.1f}" '
        f'height="{height:.1f}" rx="{radius}" fill="{MIDNIGHT}" opacity=".055"/>'
        if fill == PAPER and radius >= 14 and stroke != "none"
        else ""
    )
    return (
        elevation
        +
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"'
        f'/>'
    )


def pill(
    x: float,
    y: float,
    label: str,
    *,
    fill: str,
    foreground: str,
    width: float | None = None,
    stroke: str = "none",
) -> tuple[str, float]:
    actual_width = width or max(62, 22 + len(label) * 7.2)
    markup = [
        rounded_rect(
            x,
            y,
            actual_width,
            28,
            fill=fill,
            stroke=stroke,
            radius=14,
        ),
        text(x + actual_width / 2, y + 19, label, css="pill", anchor="middle", fill=foreground),
    ]
    return "\n".join(markup), actual_width


def progress_bar(
    x: float,
    y: float,
    width: float,
    value: float,
    *,
    color: str,
    background: str = "#E8EDF3",
    height: float = 10,
    marker: float | None = None,
) -> str:
    bounded = min(1.0, max(0.0, value))
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{height / 2:.1f}" fill="{background}"/>',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width * bounded:.1f}" '
        f'height="{height:.1f}" rx="{height / 2:.1f}" fill="{color}"/>',
    ]
    if marker is not None:
        marker_x = x + width * min(1.0, max(0.0, marker))
        parts.append(
            f'<line x1="{marker_x:.1f}" y1="{y - 4:.1f}" x2="{marker_x:.1f}" '
            f'y2="{y + height + 4:.1f}" stroke="{INK}" stroke-width="1.5"/>'
        )
    return "\n".join(parts)


def chart_header(
    title_value: str,
    subtitle: str,
    *,
    accent: str,
    kicker: str = "DECISION INTELLIGENCE",
) -> str:
    return "\n".join(
        [
            f'<rect width="{WIDTH}" height="118" fill="{NAVY}"/>',
            f'<rect width="{WIDTH}" height="118" fill="url(#headerGrid)"/>',
            f'<rect width="10" height="118" fill="{accent}"/>',
            f'<rect x="34" y="19" width="4" height="16" rx="2" fill="{accent}"/>',
            text(48, 31, kicker, css="kicker", fill=accent),
            text(42, 68, title_value, css="title", fill=PAPER),
            text(42, 96, subtitle, css="subtitle", fill="#C7D4E4"),
            f'<rect x="933" y="20" width="139" height="24" rx="12" fill="{NAVY_2}" '
            f'stroke="#36516F"/>',
            text(1002.5, 36, "MODEL-BOUND EVIDENCE", css="micro", anchor="middle", fill="#AFC0D3"),
            f'<circle cx="1125" cy="58" r="31" fill="none" stroke="{accent}" stroke-width="2"/>',
            f'<circle cx="1125" cy="58" r="10" fill="{accent}"/>',
            f'<circle cx="1125" cy="58" r="52" fill="none" stroke="#49627F" stroke-width="1" opacity=".7"/>',
            f'<line x1="1065" y1="58" x2="1185" y2="58" stroke="#49627F" stroke-width="1"/>',
            f'<line x1="1125" y1="5" x2="1125" y2="111" stroke="#49627F" stroke-width="1"/>',
        ]
    )


def chart_footer(
    y: float,
    *,
    source: str = "Source: decision-results.json",
    note: str = "Synthetic demonstration · values shown directly",
) -> str:
    return "\n".join(
        [
            f'<line x1="36" y1="{y - 22:.1f}" x2="{WIDTH - 36}" y2="{y - 22:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>',
            text(42, y, source, css="footnote"),
            text(WIDTH - 42, y, note, css="footnote", anchor="end"),
            text(
                WIDTH / 2,
                y,
                "HIGH-STAKES ANALYTICS & DECISION LAB · EDITORIAL EVIDENCE SYSTEM",
                css="micro",
                anchor="middle",
                fill=QUIET,
            ),
        ]
    )


def svg_document(
    title_value: str,
    subtitle: str,
    body: str,
    *,
    height: int,
    description: str,
    accent: str = BLUE,
    kicker: str = "DECISION INTELLIGENCE",
    source: str = "Source: decision-results.json",
    note: str = "Synthetic demonstration · values shown directly",
) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title_value)}</title>
<desc id="desc">{escape(description)}</desc>
<defs>
  <pattern id="headerGrid" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r=".85" fill="#FFFFFF" opacity=".12"/>
  </pattern>
</defs>
<style>
  text {{ font-family: {FONT_STACK}; }}
  .kicker {{ font-size: 11px; font-weight: 800; letter-spacing: 1.6px; }}
  .title {{ font-size: 28px; font-weight: 780; letter-spacing: -0.35px; }}
  .subtitle {{ font-size: 14px; }}
  .section {{ fill: {INK}; font-size: 17px; font-weight: 720; }}
  .label {{ fill: {INK_SOFT}; font-size: 14px; }}
  .small {{ fill: {MUTED}; font-size: 12px; }}
  .eyebrow {{ fill: {MUTED}; font-size: 10.5px; font-weight: 800; letter-spacing: 1px; }}
  .value {{ fill: {INK}; font-size: 16px; font-weight: 750; font-variant-numeric: tabular-nums; }}
  .big {{ fill: {INK}; font-size: 30px; font-weight: 800; font-variant-numeric: tabular-nums; }}
  .display {{ fill: {INK}; font-size: 38px; font-weight: 820; font-variant-numeric: tabular-nums; }}
  .mono {{ fill: {INK_SOFT}; font-size: 12.5px; font-family: {MONO_STACK}; font-variant-numeric: tabular-nums; }}
  .pill {{ font-size: 11px; font-weight: 760; letter-spacing: .25px; }}
  .footnote {{ fill: {QUIET}; font-size: 10.5px; }}
  .micro {{ fill: {QUIET}; font-size: 8.5px; font-weight: 800; letter-spacing: 1px; }}
</style>
<rect width="{WIDTH}" height="{height}" fill="{CANVAS}"/>
<circle cx="1180" cy="{height - 30}" r="120" fill="{accent}" opacity=".035"/>
<circle cx="36" cy="{height - 5}" r="86" fill="{accent}" opacity=".025"/>
{chart_header(title_value, subtitle, accent=accent, kicker=kicker)}
{body}
{chart_footer(height - 18, source=source, note=note)}
</svg>
"""


def score_tint(value: float, accent: str, tint: str) -> tuple[str, str]:
    """Return a quiet surface and legible foreground; magnitude is labeled directly."""
    bounded = min(1.0, max(0.0, value))
    if bounded >= 0.76:
        return accent, PAPER
    if bounded >= 0.48:
        return tint, INK
    return PAPER, INK


def path_donut(
    cx: float,
    cy: float,
    radius: float,
    value: float,
    *,
    color: str,
    background: str = "#DCE4ED",
    stroke_width: float = 14,
) -> str:
    circumference = 2 * 3.141592653589793 * radius
    bounded = min(1.0, max(0.0, value))
    return "\n".join(
        [
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" '
            f'stroke="{background}" stroke-width="{stroke_width}"/>',
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius - stroke_width:.1f}" '
            f'fill="none" stroke="{GRID}" stroke-width="1" opacity=".8"/>',
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
            f'stroke-dasharray="{circumference * bounded:.1f} {circumference:.1f}" '
            f'transform="rotate(-90 {cx:.1f} {cy:.1f})"/>',
        ]
    )


def categorical_colors(items: Iterable[str], *, preferred: str | None = None, accent: str = BLUE) -> dict[str, str]:
    colors: dict[str, str] = {}
    offset = 0
    for item in items:
        if item == preferred:
            colors[item] = accent
        else:
            while CATEGORY_PALETTE[offset % len(CATEGORY_PALETTE)] == accent:
                offset += 1
            colors[item] = CATEGORY_PALETTE[offset % len(CATEGORY_PALETTE)]
            offset += 1
    return colors
