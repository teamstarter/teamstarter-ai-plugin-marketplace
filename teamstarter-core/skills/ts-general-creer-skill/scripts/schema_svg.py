#!/usr/bin/env python3
"""Draw the diagram of a skill as an SVG: its inputs, its steps, its outputs.

Usage:
    python3 scripts/schema_svg.py schema.json > <skill-name>-schema.svg
    python3 scripts/schema_svg.py schema.json --out <skill-name>-schema.svg

schema.json:
    {
      "name": "cr-reunion-client",
      "title": "Comptes rendus de réunion client",
      "description": "Rédige le compte rendu d'une réunion client à partir des notes.",
      "inputs":  [{"label": "Notes de réunion", "detail": "message de l'utilisateur", "step": 1}],
      "steps":   [{"label": "Lire les notes", "detail": "repère décisions et actions"}],
      "outputs": [{"label": "Compte rendu", "detail": "Google Docs, dossier Clients", "step": 3}]
    }

`step` (optional) is the number of the step an input feeds, or that produces an output:
by default, inputs go to the first step and outputs come from the last one. `detail` is
optional. Standard library only.
"""

import argparse
import json
import sys
from xml.sax.saxutils import escape

WIDTH = 1000
MARGIN = 32
GAP = 60
SIDE_WIDTH = 250
STEP_WIDTH = WIDTH - 2 * MARGIN - 2 * SIDE_WIDTH - 2 * GAP
PADDING = 12
BOX_GAP = 16
LABEL_SIZE = 14
DETAIL_SIZE = 12
LINE_HEIGHT = 1.35
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

COLORS = {
    "background": "#ffffff",
    "title": "#101828",
    "text": "#344054",
    "muted": "#667085",
    "arrow": "#98a2b3",
    "inputs": ("#eef4ff", "#5b7fd6"),
    "steps": ("#ffffff", "#d0d5dd"),
    "outputs": ("#ecfdf3", "#2f9a63"),
    "panel": "#f9fafb",
    "number": "#344054",
}


def wrap(text, font_size, width):
    """Greedy word wrap, from an average character width of 0.55 em."""
    max_chars = max(8, int(width / (font_size * 0.55)))
    lines, line = [], ""
    for word in str(text or "").split():
        candidate = f"{line} {word}".strip()
        if len(candidate) <= max_chars:
            line = candidate
        else:
            if line:
                lines.append(line)
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            line = word
    if line:
        lines.append(line)
    return lines


def measure(item, width):
    """Lines of the label and of the detail of a box, and the height of the box."""
    label = wrap(item.get("label", ""), LABEL_SIZE, width - 2 * PADDING)
    detail = wrap(item.get("detail", ""), DETAIL_SIZE, width - 2 * PADDING)
    height = 2 * PADDING + len(label) * LABEL_SIZE * LINE_HEIGHT
    if detail:
        height += 4 + len(detail) * DETAIL_SIZE * LINE_HEIGHT
    return label, detail, height


def text_block(x, y, lines, size, color, weight="normal"):
    out = []
    for index, line in enumerate(lines):
        baseline = y + size + index * size * LINE_HEIGHT
        out.append(
            f'<text x="{x:.1f}" y="{baseline:.1f}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}">{escape(line)}</text>'
        )
    return out


def box(x, y, width, item, fill, stroke, offset_x=0):
    label, detail, height = measure(item, width - offset_x)
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height:.1f}" rx="10" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    ]
    text_x = x + PADDING + offset_x
    parts += text_block(text_x, y + PADDING - 2, label, LABEL_SIZE, COLORS["text"], "600")
    if detail:
        detail_y = y + PADDING - 2 + len(label) * LABEL_SIZE * LINE_HEIGHT + 4
        parts += text_block(text_x, detail_y, detail, DETAIL_SIZE, COLORS["muted"])
    return parts, height


def column(items, x, width, top, colors, numbered=False):
    """The boxes of a column, and the vertical centre of each box."""
    parts, centres, y = [], [], top
    for index, item in enumerate(items):
        offset = 30 if numbered else 0
        box_parts, height = box(x, y, width, item, *colors, offset_x=offset)
        parts += box_parts
        if numbered:
            cx, cy = x + PADDING + 11, y + PADDING + 9
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" fill="{COLORS["number"]}"/>')
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 4:.1f}" font-size="12" font-weight="700" '
                f'fill="#ffffff" text-anchor="middle">{index + 1}</text>'
            )
        centres.append(y + height / 2)
        y += height + BOX_GAP
    return parts, centres, y - BOX_GAP


def side_column(items, x, top, colors, anchors):
    """Boxes of the inputs or outputs, level with their step when there is room.

    Consecutive boxes tied to the same step form a group centred on that step.
    """
    parts, centres, y, index = [], [], top, 0
    while index < len(items):
        end = index
        while end + 1 < len(items) and anchors[end + 1] == anchors[index]:
            end += 1
        heights = [measure(item, SIDE_WIDTH)[2] for item in items[index:end + 1]]
        group_height = sum(heights) + BOX_GAP * (len(heights) - 1)
        y = max(y, anchors[index] - group_height / 2)
        for item, height in zip(items[index:end + 1], heights):
            box_parts, _ = box(x, y, SIDE_WIDTH, item, *colors)
            parts += box_parts
            centres.append(y + height / 2)
            y += height + BOX_GAP
        index = end + 1
    return parts, centres, (y - BOX_GAP if items else top)


def arrow(x1, y1, x2, y2):
    middle = (x1 + x2) / 2
    return (
        f'<path d="M {x1:.1f} {y1:.1f} C {middle:.1f} {y1:.1f}, {middle:.1f} {y2:.1f}, '
        f'{x2:.1f} {y2:.1f}" fill="none" stroke="{COLORS["arrow"]}" stroke-width="1.5" '
        f'marker-end="url(#arrow)"/>'
    )


def step_index(item, default, count):
    try:
        number = int(item.get("step", default + 1))
    except (TypeError, ValueError):
        number = default + 1
    return min(max(number, 1), count) - 1


def header(schema):
    parts, y = [], MARGIN
    title = schema.get("title") or schema.get("name", "")
    title_lines = wrap(title, 22, WIDTH - 2 * MARGIN)
    parts += text_block(MARGIN, y, title_lines, 22, COLORS["title"], "700")
    y += len(title_lines) * 22 * LINE_HEIGHT
    if schema.get("title") and schema.get("name"):
        parts += text_block(MARGIN, y + 2, [schema["name"]], 12, COLORS["muted"])
        y += 12 * LINE_HEIGHT + 2
    description = wrap(schema.get("description", ""), 14, WIDTH - 2 * MARGIN)
    if description:
        parts += text_block(MARGIN, y + 6, description, 14, COLORS["text"])
        y += 6 + len(description) * 14 * LINE_HEIGHT
    return parts, y + 24


def render(schema):
    inputs = schema.get("inputs") or []
    steps = schema.get("steps") or []
    outputs = schema.get("outputs") or []
    if not steps:
        raise ValueError("the schema needs at least one step")

    parts, top = header(schema)
    x_in, x_steps = MARGIN, MARGIN + SIDE_WIDTH + GAP
    x_out = x_steps + STEP_WIDTH + GAP
    for x, width, name in ((x_in, SIDE_WIDTH, "ENTRÉES"), (x_steps, STEP_WIDTH, "ÉTAPES"),
                           (x_out, SIDE_WIDTH, "SORTIES")):
        parts.append(
            f'<text x="{x + width / 2:.1f}" y="{top:.1f}" font-size="12" font-weight="700" '
            f'fill="{COLORS["muted"]}" text-anchor="middle" letter-spacing="1">{name}</text>'
        )
    top += 16

    step_parts, step_centres, steps_bottom = column(
        steps, x_steps + 12, STEP_WIDTH - 24, top + 12, COLORS["steps"], numbered=True
    )
    in_targets = [step_centres[step_index(i, 0, len(steps))] for i in inputs]
    out_sources = [step_centres[step_index(o, len(steps) - 1, len(steps))] for o in outputs]
    in_parts, in_centres, in_bottom = side_column(inputs, x_in, top, COLORS["inputs"], in_targets)
    out_parts, out_centres, out_bottom = side_column(
        outputs, x_out, top, COLORS["outputs"], out_sources
    )
    bottom = max(steps_bottom + 12, in_bottom, out_bottom)

    parts.append(
        f'<rect x="{x_steps}" y="{top:.1f}" width="{STEP_WIDTH}" height="{bottom - top:.1f}" '
        f'rx="14" fill="{COLORS["panel"]}" stroke="#eaecf0"/>'
    )
    for upper, lower in zip(step_centres, step_centres[1:]):
        x = x_steps + STEP_WIDTH / 2
        parts.append(
            f'<line x1="{x:.1f}" y1="{upper:.1f}" x2="{x:.1f}" y2="{lower:.1f}" '
            f'stroke="#eaecf0" stroke-width="2"/>'
        )
    parts += step_parts + in_parts + out_parts
    for centre, target in zip(in_centres, in_targets):
        parts.append(arrow(x_in + SIDE_WIDTH, centre, x_steps + 10, target))
    for centre, source in zip(out_centres, out_sources):
        parts.append(arrow(x_steps + STEP_WIDTH - 12, source, x_out - 2, centre))

    height = bottom + MARGIN
    title = escape(schema.get("title") or schema.get("name", "Skill"))
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
        f'viewBox="0 0 {WIDTH} {height:.0f}" font-family="{FONT}" role="img">',
        f"<title>{title}</title>",
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" '
        f'fill="{COLORS["arrow"]}"/></marker></defs>',
        f'<rect width="100%" height="100%" fill="{COLORS["background"]}"/>',
        *parts,
        "</svg>",
        "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("schema", help="the JSON file of the skill's inputs, steps and outputs")
    parser.add_argument("--out", help="the SVG file to write (default: standard output)")
    args = parser.parse_args()
    with open(args.schema, encoding="utf-8") as handle:
        svg = render(json.load(handle))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(svg)
    else:
        sys.stdout.write(svg)


if __name__ == "__main__":
    main()
