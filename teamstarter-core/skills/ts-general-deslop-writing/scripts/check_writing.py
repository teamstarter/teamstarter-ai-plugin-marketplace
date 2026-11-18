#!/usr/bin/env python3
"""Find the marks of generated text in a draft (French or English).

    python3 scripts/check_writing.py draft.md
    python3 scripts/check_writing.py draft.md --lang fr --kind email
    cat draft.txt | python3 scripts/check_writing.py -

Prints one line per mark: FAIL (remove it) or WARN (check it in context), with the line number,
the rule and the excerpt. Exit 0 when there is no FAIL, 1 otherwise, 2 on a usage error.

The word and phrase lists are read at each run from references/fr.md and references/en.md
(sections tagged [fail] or [warn]), so the lists and the documentation never drift apart. The
mechanical checks (dashes, separators, bold labels, emoji, headings, rhythm) are below.

Not checked: fenced code blocks, inline code, URLs, HTML comments. Use --kind to say what the
text is: prose (default), doc (documentation), email, social (post), chat (message).

Standard library only, so that it runs wherever the skill is installed.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCES = os.path.normpath(os.path.join(HERE, "..", "references"))
KINDS = ("prose", "doc", "email", "social", "chat")

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[«\"“A-ZÀ-ÖØ-Ý0-9])")
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9'’-]+")
FR_HINTS = {"le", "la", "les", "des", "est", "une", "un", "et", "pour", "dans", "que", "qui",
            "pas", "sur", "avec", "du", "au", "nous", "vous", "ce"}
EN_HINTS = {"the", "and", "is", "of", "to", "a", "in", "that", "for", "with", "on", "you",
            "this", "are", "it", "be", "we"}
DECORATIVE_HEADINGS = {
    "fr": ("conclusion", "en conclusion", "en résumé", "en bref", "pour conclure",
           "le mot de la fin", "pour aller plus loin", "perspectives", "à retenir",
           "ce qu'il faut retenir", "points clés", "introduction", "contexte", "synthèse",
           "et après ?", "un peu de contexte"),
    "en": ("conclusion", "in conclusion", "final thoughts", "wrapping up", "looking ahead",
           "the bigger picture", "key takeaways", "takeaways", "summary", "introduction",
           "overview", "a closer look", "what this means", "why it matters", "next steps",
           "the road ahead", "tl;dr"),
}


LEFTOVERS = re.compile(
    r"oaicite|contentReference\[|utm_source=(?:chatgpt|openai|copilot|perplexity)|referrer=grok"
    r"|\b(?:19|20)\d\d-XX-XX\b|\bINSERT_[A-Z_]+\b|\bexample\.(?:com|org)\b|lorem ipsum"
    r"|\[(?:nom|prénom|name|first name|company|entreprise|client|date|insérer|insert|votre|your"
    r"|à compléter|todo|tbd)\b[^\]\n]{0,40}\]", re.I)


def load_patterns(lang):
    """[(severity, section, hint, compiled regex)] from references/<lang>.md."""
    path = os.path.join(REFERENCES, f"{lang}.md")
    if not os.path.exists(path):
        return []
    patterns, section, severity = [], None, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            head = re.match(r"^###\s+(.+?)\s+\[(fail|warn)\]\s*$", line)
            if head:
                section, severity = head.group(1), head.group(2).upper()
                continue
            if line.startswith("## ") or line.startswith("### "):
                section = severity = None
                continue
            item = re.match(r"^- `([^`]+)`\s*:?\s*(.*)$", line)
            if item and severity:
                label, hint = item.group(1), item.group(2).strip()
                patterns.append((severity, section, hint, compile_pattern(label)))
    return patterns


def compile_pattern(label):
    """`re:...` is a regular expression; otherwise a phrase where … stands for a few words and a
    leading ^ means at the start of a sentence or a line. Case-insensitive, ’ read as '."""
    if label.startswith("re:"):
        return re.compile(label[3:], re.I | re.M)
    start = label.startswith("^")
    phrase = (label[1:] if start else label).replace("’", "'").strip()
    parts = [r"\s+".join(re.escape(w) for w in part.split()) for part in phrase.split("…")]
    body = r"[^.!?\n]{1,60}?".join(parts)
    if re.match(r"\w", phrase[0]):
        body = r"(?<![\w])" + body
    if re.search(r"\w$", phrase):
        body += r"(?![\w])"
    if start:
        body = r"(?:^|(?<=[.!?…]\s)|(?<=[.!?…]\s\s))[ \t]*" + body
    return re.compile(body, re.I | re.M)


def blank(match):
    return re.sub(r"[^\n]", " ", match.group(0))


def prepare(text, keep_urls=False):
    """The text with code, URLs and comments blanked (line numbers kept), ’ read as '."""
    text = text.replace("’", "'")
    text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", blank, text)
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", blank, text)
    if not keep_urls:
        text = re.sub(r"https?://\S+", blank, text)
    return text


def guess_lang(text):
    words = [w.lower() for w in WORD.findall(text)]
    fr = sum(w in FR_HINTS for w in words)
    en = sum(w in EN_HINTS for w in words)
    return "fr" if fr >= en else "en"


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def excerpt(text, start, end):
    left = text.rfind("\n", 0, start) + 1
    right = text.find("\n", end)
    line = text[left:right if right != -1 else len(text)].strip()
    return line if len(line) <= 110 else line[:107] + "..."


def sentences(text):
    """(start offset, sentence) of each sentence of the running text (not headings or lists)."""
    out = []
    for block in re.finditer(r"(?:^(?![#>|\-*+\d]).+\n?)+", text, flags=re.M):
        offset = block.start()
        for part in SENTENCE_END.split(block.group(0)):
            stripped = part.strip()
            if stripped:
                out.append((offset + block.group(0).find(stripped), stripped))
    return out


def check(raw, lang="auto", kind="prose"):
    """[(severity, line, rule, excerpt)] sorted by line."""
    text = prepare(raw)
    lang = guess_lang(text) if lang == "auto" else lang
    found = []
    # Leftovers of the tool or of a template, read before the URLs are blanked.
    with_urls = prepare(raw, keep_urls=True)
    for m in LEFTOVERS.finditer(with_urls):
        if kind == "doc" and m.group(0).lower().startswith("example."):
            continue  # the placeholder domain of documentation (RFC 2606)
        found.append(("FAIL", line_of(with_urls, m.start()),
                      f"leftover of the tool or the template: « {m.group(0)} »",
                      excerpt(with_urls, m.start(), m.end())))

    def add(severity, pos, rule, end=None):
        found.append((severity, line_of(text, pos), rule, excerpt(text, pos, end or pos)))

    for m in re.finditer("[\u200b\u200c\u200d\u2060]|(?<!^)\ufeff", text):
        add("FAIL", m.start(), "invisible character (zero-width space or joiner): delete it")
    for m in re.finditer("[\u2014\u2015]", text):
        add("FAIL", m.start(), "em dash: rewrite with a comma, a colon, parentheses or two sentences")
    for m in re.finditer(r"\w\s[\u2013-]\s\w", text):
        if not re.match(r"^\s*[-*+]\s", text[text.rfind("\n", 0, m.start()) + 1:m.end()]):
            add("WARN", m.start(), "spaced dash used as a clause break: restructure the sentence")
    for m in re.finditer(r"\s\u00b7\s|\s\u2022\s", text):
        add("FAIL", m.start(), "« · » or « • » as a separator: commas, a semicolon, or a new line")
    for m in re.finditer(r"(?m)^[ \t]*(?:[-*+]|\d+[.)])[ \t]+\*\*[^*\n]{1,60}?(?:\*\*\s*[:.]|[:.]\*\*)", text):
        add("FAIL", m.start(), "bold label before the text of a list item: plain sentence instead")
    for m in re.finditer(r"(?m)^[ \t]*\*\*[^*\n]{1,60}?(?:\*\*\s*[:.]|[:.]\*\*)\s+\S", text):
        add("FAIL", m.start(), "bold label opening a paragraph: plain sentence instead")
    for m in re.finditer(r"(?m)^[ \t]*(?:[-*+][ \t]*)?(" + EMOJI.pattern + ")", text):
        add("FAIL", m.start(), "emoji as a bullet or line opener")
    for m in re.finditer(r"(?m)^#{1,6}\s.*$", text):
        heading = m.group(0)
        title = re.sub(r"^#{1,6}\s+", "", heading).strip().rstrip(":").strip()
        if EMOJI.search(heading):
            add("FAIL", m.start(), "emoji in a heading")
        if title.endswith("?"):
            add("WARN", m.start(), "heading as a question: state what the section says")
        if title.lower().rstrip(" ?:") in DECORATIVE_HEADINGS.get(lang, ()):
            add("WARN", m.start(), "decorative heading: name what the section establishes")
        rest = [w for w in WORD.findall(title)[1:] if len(w) > 3]
        caps = [w for w in rest if w[0].isupper() and not w.isupper()]
        if len(caps) >= 2 and len(caps) >= len(rest) / 2:
            add("WARN", m.start(), "Title Case heading: sentence case (keep proper nouns)")
        if kind in ("email", "social", "chat"):
            add("FAIL", m.start(), f"markdown heading in a {kind}")
    if kind in ("email", "social", "chat"):
        for m in re.finditer(r"\*\*[^*\n]+\*\*", text):
            add("FAIL", m.start(), f"markdown bold in a {kind}: it shows as asterisks")
    words = len(WORD.findall(text))
    bangs = [m.start() for m in re.finditer(r"!(?!\[)", text)]
    if bangs and len(bangs) > max(1, words // 300):
        add("WARN", bangs[0], f"{len(bangs)} exclamation marks for {words} words: one at most")
    dots = [m.start() for m in re.finditer(r"\.\.\.|…", text)]
    if len(dots) > 1:
        add("WARN", dots[1], f"{len(dots)} ellipses: one at most, and only to trail off")
    if lang == "fr":
        for m in re.finditer(r"“[^”\n]{1,200}”", text):
            add("WARN", m.start(), "English quotation marks in French: « … »")
    elif "“" in text and re.search(r'(?<![\w])"\w', text):
        add("WARN", text.find("“"), "curly and straight quotation marks mixed: pick one kind")
    if kind == "social":
        tags = re.findall(r"(?<!\w)#\w+", text)
        if len(tags) > 2:
            add("WARN", text.find(tags[2]), f"{len(tags)} hashtags: two at most, in the text")
    run = []
    for start, s in sentences(text):
        n = len(WORD.findall(s))
        run = run + [start] if 0 < n <= 6 else []
        if len(run) == 3:
            add("WARN", run[0], "three short sentences in a row: join them with the link between them")
    for m in re.finditer(r"(?:^|(?<=[.!?]\s))([A-ZÀ-Ý][^.?!\n]{2,40}\?)\s+([A-ZÀ-Ý][^.?!\n]{1,60}[.!])",
                         text, flags=re.M):
        if len(WORD.findall(m.group(1))) <= 5 and len(WORD.findall(m.group(2))) <= 8:
            add("WARN", m.start(), "question answered right after: state the point")
    for severity, section, hint, rx in load_patterns(lang):
        for m in rx.finditer(text):
            said = " ".join(m.group(0).split())
            add(severity, m.start(), f"{section}: « {said} »" + (f", {hint}" if hint else ""),
                m.end())
    seen, out = set(), []
    for item in sorted(found, key=lambda x: (x[1], x[0] != "FAIL", x[2])):
        if (item[1], item[2]) not in seen:
            seen.add((item[1], item[2]))
            out.append(item)
    return lang, out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", help="the draft (a text or markdown file), or - for stdin")
    parser.add_argument("--lang", choices=("auto", "fr", "en"), default="auto")
    parser.add_argument("--kind", choices=KINDS, default="prose")
    args = parser.parse_args(argv)
    if args.path == "-":
        raw = sys.stdin.read()
    else:
        try:
            with open(args.path, encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            print(f"cannot read {args.path}: {e}", file=sys.stderr)
            return 2
    lang, found = check(raw, args.lang, args.kind)
    for severity, line, rule, text in found:
        print(f"{severity}  line {line}  {rule}\n      {text}")
    fails = sum(1 for f in found if f[0] == "FAIL")
    warns = len(found) - fails
    print(f"\n{lang}, {args.kind}: {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
