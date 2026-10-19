#!/usr/bin/env python3
"""Check a data map (rpt/v1 file with `containers`) before sending it, and write its preview.

    python3 check_datamap.py <file>.yaml --config rpt-config.yaml --catalogues catalogues
        # errors, warnings, figures by tool and by type of data
    python3 check_datamap.py <file>.yaml --config rpt-config.yaml --catalogues catalogues \
        --preview [--destination "<where>"] > apercu.md
        # the sending preview: everything that will be sent, and only that
    python3 check_datamap.py <file>.yaml --lang fr     # messages in French

A data map says where the organization's data is kept and how it is laid out: one container per
place of a tool (folder, file, sheet, database, CRM object, pipeline, channel, label, project),
never a value of the data (references/format-datamap-v1.md). The script calls build_rpt.py (the
referential's tool, copied into this folder), with the tools and data sources of the
organization's catalogues (--catalogues), completed by the common data types of ../references/.
It adds the checks of a file about to be sent:

- `written_by`, `read_by` and `owner` stay empty: the merge links the containers to the tasks
  and roles of the referential;
- the texts carry no personal or confidential data: e-mail addresses, phone numbers, amounts
  (refused by build_rpt.py), first names, postal addresses, ages, words of HR or health topics
  (the detectors of preview_rpt.py);
- a container without a type of data or a tool of the file or the catalogues is refused.

Exit code 1 if an error remains.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCES = os.path.normpath(os.path.join(HERE, "..", "references"))
# In a packaged skill, build_rpt.py, rpt_i18n.py and preview_rpt.py are next to this script; in
# the repository, the first two are in teamstarter-os/tools/ and the third in the cartography skill.
REPO_TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "tools"))
REPO_PREVIEW = os.path.normpath(os.path.join(HERE, "..", "..",
                                             "ts-general-check-process-cartography", "scripts"))
for _folder in (REPO_TOOLS, REPO_PREVIEW, HERE):
    if os.path.exists(_folder) and _folder not in sys.path:
        sys.path.insert(0, _folder)
import rpt_i18n  # noqa: E402
from rpt_i18n import t as tr  # noqa: E402

LINKS = ("written_by", "read_by", "owner")
MESSAGES = {
    "dm.pyyaml_missing": {
        "en": "PyYAML is missing: run `pip install pyyaml`, then run this script again.",
        "fr": "PyYAML manque : lancer `pip install pyyaml`, puis relancer ce script."},
    "dm.no_containers": {
        "en": "{file}: no `containers` list: a data map describes at least one container",
        "fr": "{file} : pas de liste `containers` : une carte des données décrit au moins un "
              "contenant"},
    "dm.link": {
        "en": "{id}: `{field}` stays empty in a data map sent for merging: the merge links the "
              "containers to the tasks and roles of the referential (format §4)",
        "fr": "{id} : `{field}` reste vide dans une carte des données envoyée à la fusion : la "
              "fusion relie les contenants aux tâches et aux rôles du référentiel (format §4)"},
    "dm.alert": {
        "en": "{id} · {field}: {label} — \"{excerpt}\": replace it with a placeholder "
              "([Client], [First name], [Number], [YYYY-MM-DD]) or remove it",
        "fr": "{id} · {field} : {label} — « {excerpt} » : le remplacer par un gabarit "
              "([Client], [Prénom], [Numéro], [AAAA-MM-JJ]) ou le retirer"},
    "dm.alert_word": {
        "en": "{id} · {field}: {label} — \"{excerpt}\": check that this place is not private "
              "or confidential (then leave it out), or reword",
        "fr": "{id} · {field} : {label} — « {excerpt} » : vérifier que cet emplacement n'est "
              "pas privé ou confidentiel (sinon le retirer), ou reformuler"},
    "dm.value": {
        "en": "{id} · {field}: {kind} — \"{excerpt}\": a data map holds no value of the data; "
              "write a placeholder or remove it",
        "fr": "{id} · {field} : {kind} — « {excerpt} » : une carte des données ne contient "
              "aucune valeur de la donnée ; écrire un gabarit ou la retirer"},
    "dm.number": {"en": "file or project number", "fr": "numéro de dossier ou de projet"},
    "dm.untaxed": {"en": "amount", "fr": "montant"},
    "dm.figures": {
        "en": "{containers} container(s) in {tools} tool(s), for {types} type(s) of data; "
              "size known for {sized}, last change known for {dated}",
        "fr": "{containers} contenant(s) dans {tools} outil(s), pour {types} type(s) de "
              "données ; taille connue pour {sized}, dernière modification connue pour {dated}"},
    "dm.by_tool": {"en": "By tool: {items}", "fr": "Par outil : {items}"},
    "dm.by_type": {"en": "By type of data: {items}", "fr": "Par type de données : {items}"},
    "dm.fresh": {
        "en": "Last change: {fresh} within 7 days, {recent} within 30, {aging} within 90, "
              "{old} within 180, {stale} older, {unknown} unknown",
        "fr": "Dernière modification : {fresh} à 7 jours ou moins, {recent} à 30, {aging} à 90, "
              "{old} à 180, {stale} plus anciennes, {unknown} inconnues"},
    # The preview.
    "dm.p.title": {"en": "# Data map — what will be sent",
                   "fr": "# Carte des données — ce qui sera envoyé"},
    "dm.p.intro": {
        "en": "This file describes where the data is kept and how it is laid out: the places "
              "of {tools} tool(s), their size and the date of their last change. It holds no "
              "content: no document, no message, no value of a field. It will go to "
              "{destination}.",
        "fr": "Ce fichier décrit où la donnée est rangée et comment elle est organisée : les "
              "emplacements de {tools} outil(s), leur taille et la date de leur dernière "
              "modification. Il ne contient aucun contenu : aucun document, aucun message, "
              "aucune valeur de champ. Il ira dans {destination}."},
    "dm.p.meta": {"en": "Made by {authors} on {date}. Tools read: {tools}.",
                  "fr": "Fait par {authors} le {date}. Outils lus : {tools}."},
    "dm.p.alerts": {"en": "## Alerts of the automatic check", "fr": "## Alertes du contrôle automatique"},
    "dm.p.no_alert": {"en": "No alert.", "fr": "Aucune alerte."},
    "dm.p.header": {
        "en": "| Container | Kind | Type of data | Size | Last change | Columns or properties |",
        "fr": "| Contenant | Nature | Type de données | Taille | Dernière modification | "
              "Colonnes ou propriétés |"},
    "dm.p.declared": {"en": "## Declared in the file", "fr": "## Déclarés dans le fichier"},
    "dm.p.notes": {"en": "Notes", "fr": "Notes"},
    "dm.p.file": {"en": "## The file as it will be sent", "fr": "## Le fichier tel qu'il sera envoyé"},
    "dm.p.file_intro": {
        "en": "Every field, including those the tables above do not show.",
        "fr": "Tous les champs, y compris ceux que les tableaux ci-dessus ne montrent pas."},
    "dm.p.changed": {"en": " ({n} changed in 90 days)", "fr": " ({n} modifiés en 90 jours)"},
}
rpt_i18n.register(MESSAGES)
CATALOGUES = [None]


# Values the detectors of preview_rpt.py do not look for: a file or project number
# (« 2024-017 »), an amount written without a currency but with HT or TTC (« 4800 HT »).
EXTRA = (("dm.number", re.compile(r"(?<![\d-])(?:19|20)\d{2}[-_/]\d{2,4}(?![-/]?\d)")),
         ("dm.untaxed", re.compile(r"\b\d[\d\s\u202f.,]*\s?(?:HT|TTC|H\.T\.|T\.T\.C\.)(?!\w)")))


# The fields of free text, where a value could hide; the others hold ids, dates, closed values,
# counts or links, checked by build_rpt.py.
TEXT_FIELDS = {"title", "organization", "team", "sources", "notes", "name", "description",
               "where", "path", "holds", "naming", "fields", "formats", "items", "tools"}


def texts(data):
    """(where, field, text) for every text of the file: meta, declared tools and data sources,
    containers, at any depth. `meta.authors` is left out: it names the person, on purpose."""
    out = []

    def walk(value, where, field):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, where, f"{field}.{k}" if field else str(k))
        elif isinstance(value, list):
            for v in value:
                walk(v, where, field)
        elif isinstance(value, str):
            out.append((where, field, value))
    walk({k: v for k, v in (data.get("meta") or {}).items() if k in TEXT_FIELDS}, "meta", "")
    for kind in ("tools", "data_sources", "containers"):
        for item in data.get(kind) or []:
            if isinstance(item, dict):
                walk({k: v for k, v in item.items() if k in TEXT_FIELDS},
                     str(item.get("id")), "")
    return out


def alerts(data, preview_rpt, build_rpt):
    """(errors, warnings) on the texts of the whole file: the values build_rpt.py refuses in a
    container (e-mail, phone, amount), wherever they are; the detectors of preview_rpt.py
    (first names, addresses, ages, words of private subjects) and EXTRA as warnings."""
    errors, warnings = [], []
    authors = [str(a) for a in (data.get("meta") or {}).get("authors") or []]
    keep = ("unit", "where", "notes", "name", "description")
    for where, field, text in texts(data):
        last = field.split(".")[-1]
        if "." in field and last not in keep:
            continue
        for name in authors:  # the person named on purpose, in the title
            text = text.replace(name, "")
        for kind, pattern in build_rpt.CONTENT_PATTERNS:
            errors += [tr("dm.value", id=where, field=field, kind=tr(build_rpt.CONTENT_WORDS[kind]),
                          excerpt=m.group(0).strip()) for m in pattern.finditer(text)]
        values = [(label, m.group(0).strip()) for label, pattern in preview_rpt.PATTERNS
                  for m in pattern.finditer(text)]
        values += [(label, m.group(0).strip()) for label, pattern in EXTRA
                   for m in pattern.finditer(text)]
        values += [("preview.alert.first_name", m.group(1))
                   for m in preview_rpt.FIRST_NAME.finditer(text)]
        warnings += [tr("dm.alert", id=where, field=field, label=tr(label), excerpt=x)
                     for label, x in values if not any(x in e for e in errors)]
        low = text.lower()
        warnings += [tr("dm.alert_word", id=where, field=field, excerpt=m.group(0),
                        label=tr("preview.alert.word", label=tr(label)))
                     for label, words in preview_rpt.WORDS.items()
                     for w in words for m in [re.search(r"\b" + w, low)] if m]
    return errors, warnings


# The warnings of build_rpt.py that a data map cannot act on: nobody is named before the merge,
# no task cites a declared type of data, a declared type has no `tools` (its tools are those of
# its containers).
IGNORED = ("warn.container_no_writer", "warn.source_unused", "warn.source_without_tool")


def is_message(key, message):
    """Whether `message` is the message `key` of rpt_i18n.py, in any language."""
    for text in rpt_i18n.MESSAGES[key].values():
        pattern = re.sub(r"\\\{\w+\\\}", ".*", re.escape(text))
        if re.fullmatch(pattern, message, re.S):
            return True
    return False


def load(path):
    import build_rpt
    ref, errors = build_rpt.load(path, catalogue_dir=CATALOGUES[0] or REFERENCES)
    if CATALOGUES[0]:
        build_rpt.borrow(ref, REFERENCES)
    return ref, errors


def check(path, preview_rpt):
    """(errors, warnings, ref) of one data map."""
    import yaml
    import build_rpt
    ref, errors = load(path)
    name = os.path.basename(path)
    if errors:
        return errors, [], ref
    if not ref["containers"]:
        return [tr("dm.no_containers", file=name)], [], ref
    errors = [tr("dm.link", id=c.get("id"), field=f) for c in ref["containers"] for f in LINKS
              if c.get(f)]
    for c in ref["containers"]:
        for f in LINKS:
            c.pop(f, None)
    more, warnings = build_rpt.validate(ref)
    # A value in a container is refused by build_rpt.py and found again, with every other
    # field of the file, by alerts(): reported once.
    errors += [e for e in more if not is_message("check.container_content", e)]
    warnings = [w for w in warnings if not any(is_message(k, w) for k in IGNORED)]
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    more, found = alerts(data, preview_rpt, build_rpt)
    errors += more
    warnings += found
    if not errors:
        build_rpt.enrich(ref)
    return errors, warnings, ref


def names(ref, list_name):
    import build_rpt
    return {x["id"]: build_rpt.entry_name(x) or x["id"] for x in ref[list_name]}


def figures(ref):
    import build_rpt
    conts = ref["containers"]
    tools, types = names(ref, "tools"), names(ref, "data_sources")
    per_tool, per_type, fresh = {}, {}, {}
    for c in conts:
        per_tool[c["tool"]] = per_tool.get(c["tool"], 0) + 1
        per_type[c["data"]] = per_type.get(c["data"], 0) + 1
        fresh[c.get("_fresh")] = fresh.get(c.get("_fresh"), 0) + 1
    sized = sum(1 for c in conts if (c.get("items") or {}).get("count") is not None)
    dated = sum(1 for c in conts if (c.get("freshness") or {}).get("last_modified"))
    return [tr("dm.figures", containers=len(conts), tools=len(per_tool), types=len(per_type),
               sized=sized, dated=dated),
            tr("dm.by_tool", items=", ".join(f"{tools.get(k, k)} {v}" for k, v in
                                             sorted(per_tool.items(), key=lambda x: -x[1]))),
            tr("dm.by_type", items=", ".join(f"{types.get(k, k)} {v}" for k, v in
                                             sorted(per_type.items(), key=lambda x: -x[1]))),
            tr("dm.fresh", **{k: fresh.get(k, 0) for k in build_rpt.DATAMAP_FRESHNESS})]


def cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def preview(path, ref, warnings, preview_rpt):
    """Everything that will be sent, in Markdown: the containers tool by tool, nested by parent,
    every field written, the declared tools and data sources, the alerts."""
    import yaml
    import build_rpt
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    meta = data.get("meta") or {}
    tools, types = names(ref, "tools"), names(ref, "data_sources")
    conts = ref["containers"]
    used = sorted({c["tool"] for c in conts}, key=lambda t: str(tools.get(t, t)))
    lines = [tr("dm.p.title"), "",
             tr("dm.p.intro", tools=len(used), destination=preview_rpt.destination()), "",
             tr("dm.p.meta", authors=", ".join(map(str, meta.get("authors") or [])) or "—",
                date=meta.get("updated") or "—",
                tools=", ".join(str(tools.get(t, t)) for t in used)), "",
             tr("dm.p.alerts"), ""]
    lines += [f"- {w}" for w in warnings] or [tr("dm.p.no_alert")]
    by_id = {c["id"]: c for c in conts}

    def depth(c):
        n, x = 0, c
        while x.get("parent") in by_id and n < 20:
            n, x = n + 1, by_id[x["parent"]]
        return n

    def walk(c, out):
        out.append(c)
        for k in c.get("_children") or []:
            if k in by_id:
                walk(by_id[k], out)
    for tool in used:
        lines += ["", f"## {tools.get(tool, tool)}", "", tr("dm.p.header"),
                  "|---|---|---|---|---|---|"]
        order = []
        for c in conts:
            if c["tool"] == tool and c.get("parent") not in by_id:
                walk(c, order)
        for c in order:
            items = c.get("items") or {}
            size = (("≈ " if items.get("approx") else "") + f"{items['count']} "
                    f"{items.get('unit') or ''}").strip() if items.get("count") is not None else ""
            fr = c.get("freshness") or {}
            when = fr.get("last_modified") or ""
            if fr.get("modified_90d") is not None:
                when += tr("dm.p.changed", n=fr["modified_90d"])
            state = "" if c.get("state", "active") == "active" else \
                f" ({build_rpt.label('container_state', c['state'], default=c['state'])})"
            place = f"{'↳ ' * depth(c)}{c['id']} {c.get('name')}{state}" + \
                (f" · `{c['path']}`" if c.get("path") else "")
            lines.append(f"| {cell(place)} | {cell(build_rpt.label('container_kind', c.get('kind'), default=c.get('kind')))} | "
                         f"{cell(types.get(c['data'], c['data']))} | {cell(size)} | {cell(when)} | "
                         f"{cell(', '.join(map(str, c.get('fields') or [])))} |")
        extra = [c for c in order if c.get("holds") or c.get("naming") or c.get("notes")
                 or c.get("url")]
        if extra:
            lines += ["", f"**{tr('dm.p.notes')}**", ""]
            lines += [f"- {c['id']}: " + " · ".join(
                cell(x) for x in (c.get("holds"), c.get("naming") and f"`{c['naming']}`",
                                  c.get("url"), c.get("notes")) if x) for c in extra]
    declared = [(k, x) for k in ("tools", "data_sources") for x in data.get(k) or []]
    if declared:
        lines += ["", tr("dm.p.declared"), ""]
        lines += [f"- {x.get('id')} — {build_rpt.entry_name(x) or ''}" for _, x in declared]
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    lines += ["", tr("dm.p.file"), "", tr("dm.p.file_intro"), "", "```yaml", raw.rstrip(), "```"]
    return "\n".join(lines).rstrip() + "\n"


def main(argv):
    import preview_rpt
    dest, argv = preview_rpt.split_option(argv, "destination")
    if dest:
        os.environ["RPT_DESTINATION"] = dest
    argv = preview_rpt.use_config(argv)
    catalogues, argv = preview_rpt.split_option(argv, "catalogues")
    if catalogues:
        CATALOGUES[0] = os.path.abspath(catalogues)
    lang, argv = preview_rpt.split_lang(argv)
    rpt_i18n.set_language(rpt_i18n.resolve(lang))
    paths = [a for a in argv if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return 2
    try:
        import yaml  # noqa: F401
    except ImportError:
        print(tr("dm.pyyaml_missing"))
        return 2
    import build_rpt
    build_rpt.setup_language(lang)
    status = 0
    for path in paths:
        errors, warnings, ref = check(path, preview_rpt)
        if "--preview" in argv and not errors:
            sys.stdout.write(preview(path, ref, warnings, preview_rpt))
            continue
        for line in ([tr("cli.error", message=e) for e in errors]
                     + [tr("cli.warning", message=w) for w in warnings]):
            print(line)
        print(tr("cli.summary", errors=len(errors), warnings=len(warnings)))
        if errors:
            status = 1
            continue
        print()
        print("\n".join(figures(ref)))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
