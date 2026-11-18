#!/usr/bin/env python3
"""Find the marks of generated decks in a .pptx, an HTML deck or a markdown outline.

    python3 scripts/check_slides.py deck.pptx
    python3 scripts/check_slides.py deck.md --lang fr
    python3 scripts/check_slides.py slides.html

A markdown outline has one slide per `---` separator, or per `#`/`##` heading when there is no
separator; an HTML deck has one slide per <section>. In a .pptx, the title is the title
placeholder of each slide; speaker notes are not read.

Prints, slide by slide, FAIL (remove it) and WARN (check it), then the marks of the whole deck
(the same layout on every slide, an agenda in a short deck, a closing "Merci"). The text of each
slide also goes through the writing checker (check_writing.py, next to this script in a packaged
skill) when it is there. Exit 0 when there is no FAIL, 1 otherwise, 2 on a usage error.

Standard library only, so that it runs wherever the skill is installed.
"""
import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9'’-]+")
AGENDA = re.compile(r"^(agenda|sommaire|ordre du jour|plan|au programme|programme|overview|contents|table of contents)\b", re.I)
CLOSING = re.compile(r"^(merci|thank you|thanks|questions\s*\??|des questions\s*\??|q\s*&\s*a)\b", re.I)
RECAP = re.compile(r"^(conclusion|en conclusion|en résumé|à retenir|ce qu'il faut retenir|points clés|key takeaways|takeaways|summary|in summary|recap)\b", re.I)
PROCESS = re.compile(r"lorem ipsum|\[(?:insérer|insert|nom|name|votre|your|à compléter|tbd)[^\]]*\]|\bTBD\b|\bXX+\b|\boption [A-C]\b|generated (?:by|from|with)|généré (?:par|avec|depuis)", re.I)


def writing_checker():
    """check_writing.check from the packaged copy, or from the writing skill next door."""
    for folder in (HERE, os.path.join(HERE, "..", "..", "ts-general-deslop-writing", "scripts")):
        if os.path.exists(os.path.join(folder, "check_writing.py")):
            sys.path.insert(0, os.path.normpath(folder))
            try:
                import check_writing
                return check_writing.check
            except ImportError:
                return None
    return None


def slide(title, body, visuals=0, bold_labels=0):
    return {"title": " ".join(title.split()), "body": [b.strip() for b in body if b.strip()],
            "visuals": visuals, "bold_labels": bold_labels}


def read_pptx(path):
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        rels = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
        order = [targets[s.get(f"{{{NS['r']}}}id")] for s in pres.findall("p:sldIdLst/p:sldId", NS)]
        slides = []
        for target in order:
            path = target.lstrip("/").replace("../", "")
            name = path if path.startswith("ppt/") else "ppt/" + path
            root = ET.fromstring(z.read(name))
            title, body, bold_labels = "", [], 0
            for sp in root.iter(f"{{{NS['p']}}}sp"):
                ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
                is_title = ph is not None and ph.get("type") in ("title", "ctrTitle")
                for para in sp.iter(f"{{{NS['a']}}}p"):
                    runs = para.findall("a:r", NS)
                    text = "".join(t.text or "" for t in para.iter(f"{{{NS['a']}}}t"))
                    if not text.strip():
                        continue
                    if is_title:
                        title = (title + " " + text).strip()
                        continue
                    body.append(text)
                    first = runs[0] if runs else None
                    rpr = first.find("a:rPr", NS) if first is not None else None
                    first_text = (first.findtext("a:t", "", NS) if first is not None else "").strip()
                    if rpr is not None and rpr.get("b") == "1" and re.search(r"[:.]$", first_text) \
                            and len(first_text) <= 60 and len(text.strip()) > len(first_text):
                        bold_labels += 1
            raw = z.read(name).decode("utf-8", "ignore")
            visuals = len(re.findall(r"<p:pic\b|/drawingml/2006/chart|<a:tbl\b|/diagram\"", raw))
            slides.append(slide(title, body, visuals, bold_labels))
    return slides


def read_markdown(text):
    parts = re.split(r"(?m)^---\s*$", text)
    if len(parts) == 1:
        parts = re.split(r"(?m)^(?=#{1,2}\s)", text)
    slides = []
    for part in parts:
        lines = [l for l in part.strip().split("\n") if l.strip()]
        if not lines:
            continue
        head = next((l for l in lines if re.match(r"#{1,3}\s", l)), "")
        body = [re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", l) for l in lines if l != head]
        bold = sum(bool(re.match(r"^\s*(?:[-*+]\s+)?\*\*[^*]{1,60}?(?:\*\*\s*[:.]|[:.]\*\*)", l)) for l in lines)
        visuals = sum(bool(re.search(r"!\[|<img|<svg|```mermaid", l)) for l in lines)
        slides.append(slide(re.sub(r"^#{1,3}\s+", "", head), body, visuals, bold))
    return slides


def read_html(text):
    slides = []
    for sec in re.findall(r"<section\b[^>]*>(.*?)</section>", text, flags=re.S | re.I):
        head = re.search(r"<h[12]\b[^>]*>(.*?)</h[12]>", sec, flags=re.S | re.I)
        title = re.sub(r"<[^>]+>", "", head.group(1)) if head else ""
        rest = sec.replace(head.group(0), "", 1) if head else sec
        rest = re.sub(r"<(script|style)\b.*?</\1>", "", rest, flags=re.S | re.I)
        body = [re.sub(r"<[^>]+>", "", b) for b in re.split(r"</(?:p|li|div|h[3-6])>", rest)]
        bold = len(re.findall(r"<(b|strong)\b[^>]*>[^<]{1,60}?(?:\s*:\s*</\1>|</\1>\s*:)", sec))
        visuals = len(re.findall(r"<img\b|<svg\b|<canvas\b|<table\b", sec, flags=re.I))
        slides.append(slide(title, body, visuals, bold))
    return slides


def title_case(title):
    """True when most words after the first, of four letters or more, start with a capital."""
    rest = [w for w in WORD.findall(title)[1:] if len(w) > 3]
    caps = [w for w in rest if w[0].isupper() and not w.isupper()]
    return len(caps) >= 2 and len(caps) >= len(rest) / 2


def check_deck(slides, lang="auto", writing=None, markdown=False):
    """[(severity, where, rule, excerpt)]. With the writing checker, the text marks of each slide
    come from it; without it, a few of them are checked here."""
    found = []
    n = len(slides)
    for i, s in enumerate(slides, 1):
        where, title = f"slide {i}", s["title"]
        text = "\n".join([title] + s["body"])
        if not title:
            found.append(("WARN", where, "no title: say the point of the slide in its title", ""))
        if not writing:
            if EMOJI.search(title) or any(EMOJI.match(b) for b in s["body"]):
                found.append(("FAIL", where, "emoji in a title or as a bullet", title))
            if re.search("[\u2014\u2015]", text):
                found.append(("FAIL", where, "em dash: comma, colon, or two lines", title))
            if re.search(r"\s[\u00b7\u2022]\s", text):
                found.append(("FAIL", where, "« · » as a separator: one item per line", title))
            if title_case(title):
                found.append(("WARN", where, "Title Case title: sentence case", title))
        if s["bold_labels"] and not (writing and markdown):
            found.append(("FAIL", where, f"{s['bold_labels']} bullet(s) opening with a bold label", title))
        for m in PROCESS.finditer(text):
            found.append(("FAIL", where, "process or placeholder text left on the slide", m.group(0)))
        if title.endswith("!"):
            found.append(("WARN", where, "exclamation mark in a title", title))
        if title.endswith(".") and len(WORD.findall(title)) < 12:
            found.append(("WARN", where, "period at the end of a short title", title))
        body_words = sum(len(WORD.findall(b)) for b in s["body"])
        if body_words > 60:
            found.append(("WARN", where, f"{body_words} words of body text: split the slide or cut", title))
        if AGENDA.match(title) and n <= 10:
            found.append(("WARN", where, f"agenda slide in a deck of {n} slides: start with the point", title))
        if RECAP.match(title):
            found.append(("WARN", where, "recap slide: it repeats the deck; end on the decision or the next step", title))
        if i == n and CLOSING.match(title):
            found.append(("WARN", where, "closing « Merci / Questions » slide: end on the decision or the next step", title))
        if writing:
            _, marks = writing("\n\n".join([f"# {title}" if title else ""] + s["body"]), lang, "prose")
            for severity, _, rule, excerpt in marks:
                if "short sentences" in rule:  # a slide is made of fragments
                    continue
                found.append((severity, where, rule, excerpt))
    content = slides[1:-1] if n > 2 else slides
    if content:
        bullets = [len(s["body"]) for s in content]
        same = sum(3 <= b <= 5 for b in bullets)
        if len(content) >= 4 and same / len(content) >= 0.6:
            found.append(("WARN", "deck", f"{same} of {len(content)} slides are a title and 3 to 5 bullets: vary the layout by content", ""))
        topic = sum(0 < len(WORD.findall(s["title"])) <= 3 for s in content)
        if len(content) >= 4 and topic / len(content) >= 0.5:
            found.append(("WARN", "deck", f"{topic} of {len(content)} titles are topic labels: write each slide's point as a sentence", ""))
        if len(content) >= 5 and not any(s["visuals"] for s in content):
            found.append(("WARN", "deck", "no image, chart, table or diagram: show what the text describes", ""))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", help="a .pptx, .html or .md deck")
    parser.add_argument("--lang", choices=("auto", "fr", "en"), default="auto")
    args = parser.parse_args(argv)
    try:
        if args.path.endswith(".pptx"):
            slides = read_pptx(args.path)
        else:
            with open(args.path, encoding="utf-8") as f:
                text = f.read()
            slides = read_html(text) if args.path.endswith((".html", ".htm")) else read_markdown(text)
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as e:
        print(f"cannot read {args.path}: {e}", file=sys.stderr)
        return 2
    if not slides:
        print(f"{args.path}: no slide found", file=sys.stderr)
        return 2
    writing = writing_checker()
    found = check_deck(slides, args.lang, writing, args.path.endswith((".md", ".markdown", ".txt")))
    for severity, where, rule, excerpt in found:
        print(f"{severity}  {where}  {rule}" + (f"\n      {excerpt[:110]}" if excerpt else ""))
    fails = sum(1 for f in found if f[0] == "FAIL")
    note = "" if writing else " (writing checker not found: text rules skipped)"
    print(f"\n{len(slides)} slide(s): {fails} FAIL, {len(found) - fails} WARN{note}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
