#!/usr/bin/env python3
"""
Convertit un markdown simple en document JSON tiptap (ProseMirror), le format des
sections de fiche projet Teamstarter (wordingTranslated.type = "tiptap"), avec les attrs
posés par l'UI (textAlign, start, color).

Usage :
    python3 tiptap.py fichier.md               # JSON sur stdout
    python3 tiptap.py fichier.md -o out.json
    echo "Texte **gras**" | python3 tiptap.py -

Supporté : paragraphes (séparés par une ligne vide ou un saut de ligne), puces "- " / "* ",
listes numérotées "1. ", gras **…**, italique *…* (hors puces). Le reste est traité en texte.
Stdlib uniquement.
"""

import json
import re
import sys

INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


def inline(text):
    nodes = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            nodes.append({"type": "text", "marks": [{"type": "bold"}], "text": part[2:-2]})
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            nodes.append({"type": "text", "marks": [{"type": "italic"}], "text": part[1:-1]})
        else:
            nodes.append({"type": "text", "text": part})
    return nodes


def paragraph(text):
    return {"type": "paragraph", "attrs": {"textAlign": "left"}, "content": inline(text.strip())}


def list_item(text):
    return {"type": "listItem", "attrs": {"color": None}, "content": [paragraph(text)]}


def convert(md):
    doc = []
    current_list = None  # (type, items)
    for raw in md.splitlines():
        line = raw.rstrip()
        m_bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        m_num = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if m_bullet or m_num:
            kind = "bulletList" if m_bullet else "orderedList"
            text = (m_bullet or m_num).group(1)
            if current_list is None or current_list["type"] != kind:
                current_list = {"type": kind, "content": []}
                if kind == "orderedList":
                    current_list["attrs"] = {"start": 1}
                doc.append(current_list)
            current_list["content"].append(list_item(text))
            continue
        current_list = None
        if not line.strip():
            continue
        line = re.sub(r"^#+\s*", "", line)  # titres → paragraphe simple
        doc.append(paragraph(line))
    return {"type": "doc", "content": doc}


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    src = args[0]
    out = None
    if "-o" in args:
        out = args[args.index("-o") + 1]
    md = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    result = json.dumps(convert(md), ensure_ascii=False, indent=2)
    if out:
        open(out, "w", encoding="utf-8").write(result)
        print(f"OK — {out}")
    else:
        print(result)


if __name__ == "__main__":
    main()
