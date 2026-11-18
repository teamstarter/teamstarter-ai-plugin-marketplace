#!/usr/bin/env python3
"""Find the marks of generated interfaces in HTML, CSS and component files.

    python3 scripts/check_ui.py page.html
    python3 scripts/check_ui.py src/components/ --allow uppercase,font
    python3 scripts/check_ui.py page.html --list-rules

Reads .html .htm .css .scss .jsx .tsx .js .ts .vue .svelte files (a folder is read recursively).
Prints one line per mark, `file:line`, FAIL (remove it unless the design system asks for it) or
WARN (check whether it carries information here). Exit 0 when there is no FAIL, 1 otherwise,
2 on a usage error.

`--allow` takes rule ids, separated by commas, that the organization's design system specifies
(for example `uppercase` when its type scale has capital eyebrows): they are not reported.

Not read: HTML comments, CSS and JS comments, the content of <code> and <pre> (a command or an id
is copied as it is). Counted marks (pills, large radii, palette) are reported once per file.

What a script cannot see (nested cards, a templated landing page, invented testimonials, density)
is in the skill's checklist: references/catalog.md.

Standard library only, so that it runs wherever the skill is installed.
"""
import argparse
import os
import re
import sys

EXTENSIONS = (".html", ".htm", ".css", ".scss", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage", "__pycache__"}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
PURPLE_HEX = r"#(?:6366f1|4f46e5|4338ca|818cf8|8b5cf6|7c3aed|6d28d9|a78bfa|a855f7|9333ea|c084fc|d946ef)\b"
PURPLE_TW = r"(?:indigo|violet|purple|fuchsia)-\d{2,3}"

# (id, severity, rule, regex). Text marks look at the whole file once comments, <code> and <pre>
# are blanked; class and CSS marks cover CSS, style attributes and utility classes.
MARKS = [
    ("em-dash", "FAIL", "em dash in the text: comma, colon, parentheses or two sentences",
     re.compile("[\u2014\u2015]")),
    ("separator", "FAIL", "« · » or « • » as a separator: spacing, a comma or a second line",
     re.compile(r"[ \t\u00a0][\u00b7\u2022][ \t\u00a0]")),
    ("emoji", "FAIL", "emoji as an icon or a decoration: an icon of the system, or nothing",
     EMOJI),
    ("bold-label", "FAIL", "bold label followed by a colon: plain text, or rewrite",
     re.compile(r"<(b|strong)\b[^>]*>(?![A-Z0-9][A-Z0-9.\-]*</)[^<]{1,60}?(?:\s*:\s*</\1>|</\1>\s*:)")),
    ("gradient-text", "FAIL", "gradient text (background-clip: text): one solid color",
     re.compile(r"(?:-webkit-)?background-clip\s*:\s*text|\bbg-clip-text\b")),
    ("side-bar", "FAIL", "accent bar on one side of a block: tint the surface or use a label",
     re.compile(r"border-(?:left|right|inline-start|inline-end)(?:-width)?\s*:\s*(?:[3-9]|\d{2,})px"
                r"|box-shadow\s*:\s*inset\s+(?:[3-9]|\d{2,})px\s+0"
                r"|\bborder-[lrse]-(?:4|8|\[(?:[3-9]|\d{2,})px\])(?![\w-])")),
    ("uppercase", "FAIL", "spaced capitals as a label style: sentence case, hierarchy by weight and size",
     re.compile(r"text-transform\s*:\s*uppercase"
                r"|[\"'`][^\"'`\n]*(?<![\w-])uppercase(?![\w-])[^\"'`\n]*[\"'`]")),
    ("letter-spacing", "WARN", "letter-spacing added to small text: usually goes with spaced capitals",
     re.compile(r"letter-spacing\s*:\s*(?!0|normal|-)|(?<![\w-])tracking-(?:wide|wider|widest|\[\d)")),
    ("purple-gradient", "FAIL", "purple or indigo gradient: the default palette of generated pages",
     re.compile(r"(?:linear|radial|conic)-gradient\([^;)]*(?:" + PURPLE_HEX + r"|indigo|violet|purple)"
                r"|\b(?:from|via|to)-" + PURPLE_TW + r"\b")),
    ("glow", "FAIL", "colored glow under an element: emphasis by contrast, size and place",
     re.compile(r"\bshadow-(?:indigo|violet|purple|fuchsia|blue|cyan|pink|sky)-\d{2,3}\b"
                r"|box-shadow\s*:\s*0\s+0\s+\d{2,}px[^;]*(?:" + PURPLE_HEX + r"|rgba?\((?!0,\s*0,\s*0))")),
    ("blur-blob", "FAIL", "blurred color blob behind the content: a plain background",
     re.compile(r"filter\s*:\s*blur\(\s*(?:[4-9]\d|\d{3,})px|\bblur-(?:2xl|3xl)\b")),
    ("sparkles", "FAIL", "sparkles as the sign of AI: name the capability instead",
     re.compile(r"<Sparkles?\b|import[^;\n]*\bSparkles?\b|['\"](?:sparkles?|auto_awesome)['\"]"
                r"|✨|>auto_awesome<")),
    ("transition-all", "WARN", "transition on every property: name the properties that change",
     re.compile(r"transition\s*:\s*all\b|(?<![\w-])transition-all(?![\w-])")),
    ("pulse", "WARN", "pulsing or pinging indicator: a static dot and a label, unless the state is live",
     re.compile(r"\banimate-(?:pulse|ping)\b|animation\s*:[^;]*\b(?:pulse|ping)\b")),
    ("glass", "WARN", "frosted glass: only for a layer over moving content",
     re.compile(r"backdrop-filter\s*:\s*blur|\bbackdrop-blur(?:-\w+)?\b")),
    ("dot-grid", "WARN", "dot-grid or line-grid texture: a background that says nothing about the product",
     re.compile(r"radial-gradient\([^)]*\b[12]px\b[^)]*\)[^;]*;[^}]*background-size|\bbg-(?:grid|dot)(?:-[\w-]+)?\b")),
    ("scroll-reveal", "WARN", "fade-in on scroll: static by default, animate the one moment that needs it",
     re.compile(r"\bdata-aos\b|\bwhileInView\b|\bfade-?in-?up\b|\banimate-fade-in\w*")),
    ("count-up", "WARN", "count-up numbers: show the number; check it is real and sourced",
     re.compile(r"\bCountUp\b|\bcount-?up\b", re.I)),
    ("shortcut-hint", "WARN", "keyboard shortcut hint: keep it only if the shortcut works",
     re.compile("⌘")),
    ("font", "WARN", "default font of generated pages: confirm it is the organization's font",
     re.compile(r"font-family\s*:\s*['\"]?(?:Inter|Roboto|Poppins|Space Grotesk|Geist|Fraunces"
                r"|Plus Jakarta Sans|Instrument Serif|Playfair Display)\b")),
    ("claude-palette", "WARN", "Claude's own palette (cream, terracotta): on someone else's page it is a mark",
     re.compile(r"#(?:f4f1ea|faf9f5|f0eee6|d97757|c96442|cc785c)\b", re.I)),
    ("unicode-icon", "WARN", "text symbol used as an icon (▸ ▾ ↗ ✕ →): an icon of the system",
     re.compile("[\u25b8\u25be\u2197\u2715\u2716]|[\u2192\u2197]\\s*</(?:a|button)>")),
    ("numbered-marker", "WARN", "numbered markers 01, 02, 03 on content that is not a sequence",
     re.compile(r">\s*0[1-9]\.?\s*<")),
    ("hover-scale", "WARN", "card that grows on hover: only on cards that open something, the same on all",
     re.compile(r"\bhover:scale-1\d{2}\b|:hover\s*\{[^}]*transform\s*:\s*scale\(1\.\d")),
    ("marquee", "WARN", "scrolling marquee (logos, quotes): a static list, if the proof is real",
     re.compile(r"<marquee\b|\banimate-marquee\b|@keyframes\s+marquee", re.I)),
]
COUNTED = [
    ("pill", "WARN", 6, "pill-shaped radius used {n} times: pills for tags and counters only",
     re.compile(r"border-radius\s*:\s*(?:9{3,}px|50vh|100vmax|var\(--[\w-]*full\))|(?<![\w-])rounded-full(?![\w-])")),
    ("radius", "WARN", 8, "large radius on {n} surfaces: one radius per level, some things square",
     re.compile(r"(?<![\w-])rounded-(?:2xl|3xl)(?![\w-])|border-radius\s*:\s*(?:2[4-9]|[3-9]\d)px")),
    ("generic-cta", "WARN", 3, "generic button label used {n} times: say what happens on click",
     re.compile(r">\s*(?:En savoir plus|Découvrir|Commencer|Get started|Learn more|Discover|Explore)"
                r"\s*(?:[→↗]\s*)?<", re.I)),
    ("palette", "WARN", 3, "indigo or violet used {n} times: confirm it is the brand's color",
     re.compile(r"\b(?:bg|text|border|ring|fill|stroke)-" + PURPLE_TW + r"\b|" + PURPLE_HEX)),
]
RULE_IDS = [m[0] for m in MARKS] + [c[0] for c in COUNTED]


def blank(match):
    return re.sub(r"[^\n]", " ", match.group(0))


def prepare(text):
    """Comments, <code> and <pre> blanked; line numbers kept."""
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"/\*.*?\*/", blank, text, flags=re.S)
    text = re.sub(r"(?m)(^|[\s;{}(),])//[^\n]*", lambda m: m.group(1) + blank(m)[len(m.group(1)):], text)
    text = re.sub(r"\{/\*.*?\*/\}", blank, text, flags=re.S)
    text = re.sub(r"<(code|pre)\b[^>]*>.*?</\1>", blank, text, flags=re.S | re.I)
    return text


def files_of(paths):
    for path in paths:
        if os.path.isdir(path):
            for folder, dirs, names in os.walk(path):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for name in sorted(names):
                    if name.endswith(EXTENSIONS):
                        yield os.path.join(folder, name)
        else:
            yield path


def check_text(text, allow=()):
    """[(severity, line, rule id, message, excerpt)] for one file's content."""
    text = prepare(text)
    lines = text.split("\n")
    found = []

    def at(pos):
        n = text.count("\n", 0, pos)
        return n + 1, lines[n].strip()[:110]

    for rid, severity, message, rx in MARKS:
        if rid in allow:
            continue
        for m in rx.finditer(text):
            line, excerpt = at(m.start())
            found.append((severity, line, rid, message, excerpt))
    for rid, severity, threshold, message, rx in COUNTED:
        if rid in allow:
            continue
        hits = [m.start() for m in rx.finditer(text)]
        if len(hits) >= threshold:
            line, excerpt = at(hits[0])
            found.append((severity, line, rid, message.format(n=len(hits)), excerpt))
    seen, out = set(), []
    for item in sorted(found, key=lambda f: (f[1], f[0] != "FAIL", f[2])):
        if (item[1], item[2]) not in seen:
            seen.add((item[1], item[2]))
            out.append(item)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="files or folders")
    parser.add_argument("--allow", default="", help="rule ids the design system specifies, comma-separated")
    parser.add_argument("--list-rules", action="store_true", help="print the rule ids and exit")
    args = parser.parse_args(argv)
    if args.list_rules:
        for rid, severity, message, _ in MARKS:
            print(f"{rid:16} {severity}  {message}")
        for rid, severity, threshold, message, _ in COUNTED:
            print(f"{rid:16} {severity}  {message.format(n=f'{threshold}+')}")
        return 0
    if not args.paths:
        parser.error("give at least one file or folder")
    allow = {a.strip() for a in args.allow.split(",") if a.strip()}
    unknown = allow - set(RULE_IDS)
    if unknown:
        parser.error(f"unknown rule id(s): {', '.join(sorted(unknown))} (see --list-rules)")
    fails = warns = read = 0
    for path in files_of(args.paths):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"cannot read {path}: {e}", file=sys.stderr)
            return 2
        read += 1
        for severity, line, rid, message, excerpt in check_text(content, allow):
            print(f"{severity}  {path}:{line}  [{rid}] {message}\n      {excerpt}")
            fails += severity == "FAIL"
            warns += severity == "WARN"
    print(f"\n{read} file(s): {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
