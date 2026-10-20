#!/usr/bin/env python3
"""Check an rpt/v1 map before sending it.

    python3 validate_rpt.py <map>.rpt.yaml [<other map>.rpt.yaml …]   # errors, warnings, figures by role
    python3 validate_rpt.py <map>.rpt.yaml --format   # first rewrites the file in the referential's style
    python3 validate_rpt.py <map>.rpt.yaml --since <starting map>.rpt.yaml   # update, last on the line
    python3 validate_rpt.py <map>.rpt.yaml --lang fr  # messages in French (default: RPT_LANG, else
                                                      # organization.language of rpt-config.yaml, else en)
    python3 validate_rpt.py <map>.rpt.yaml --config rpt-config.yaml --catalogues catalogues
        # the organization's configuration and catalogues, read at the start of the session
        # (SKILL.md, "Reading the configuration"); a missing catalogue is normal at the first run

Calls build_rpt.py (the tool of the RPT referential, copied into this folder) with the
departments, tools and data sources of the organization's catalogues (--catalogues), completed
by the generic ones of ../references/ (departments, common data types), then adds nine checks
specific to a map about to be sent: the skill and version that produced it (`meta.detector`),
one code per map (one map per hat), the declared automation
of each process against the statuses of its steps, the relevance of each task, the data sources
of manual, conversational or skilled tasks, the measures (runs per month of every active task,
minutes of the M, C, S and J tasks) and the stakes, the order of the processes (`next`, or
`next: []` at the end of a chain), the blockers (where an inferred one was seen, a task that
still writes its own `blocker`), and possible personal or confidential
data (preview_rpt.py), blocker texts and evidence included. build_rpt.py checks the form of the
`blockers` list (fields, values, dates, tasks of the map), as for the referential's register.
The figures end with the blockers still open and the connectors to activate first. With
`--since` (`--depuis` is accepted too), the map is the update of a map already sent: the script
flags each element of the starting map that disappeared, and sums up what changed. Each file is
checked on its own. Exit code 1 if an error remains in one of them; warnings are fixed before
sending.

The messages are printed in the language of the run, from rpt_i18n.py (copied into this folder
next to build_rpt.py; in the repository, teamstarter-os/tools/).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCES = os.path.normpath(os.path.join(HERE, "..", "references"))
# In a packaged skill, build_rpt.py and rpt_i18n.py are next to this script; in the repository,
# they are in teamstarter-os/tools/.
REPO_TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "tools"))
for _folder in (REPO_TOOLS, HERE):
    if os.path.exists(os.path.join(_folder, "rpt_i18n.py")) and _folder not in sys.path:
        sys.path.insert(0, _folder)
if HERE not in sys.path:
    sys.path.insert(0, HERE)  # preview_rpt.py
import rpt_i18n  # noqa: E402
from rpt_i18n import t as tr  # noqa: E402

SINCE = ("--since", "--depuis")
# The organization's catalogues (--catalogues), read before the generic ones of ../references/.
CATALOGUES = [None]

MESSAGES = {
    "validate.pyyaml_missing": {
        "en": "PyYAML is missing: run `pip install pyyaml`, then run this script again.",
        "fr": "PyYAML manque : lancer `pip install pyyaml`, puis relancer ce script."},
    "validate.data_alert": {
        "en": "data: {where}: {label} — \"{excerpt}\"",
        "fr": "données : {where} : {label} — « {excerpt} »"},
    "validate.codes": {
        "en": "codes {codes} in the map `{team}`: one map per hat, one code per map (SKILL.md, "
              "\"One map per hat\")",
        "fr": "codes {codes} dans la carte `{team}` : une carte par casquette, un seul code par "
              "carte (SKILL.md, « One map per hat »)"},
    "validate.relevance": {
        "en": "{count} task(s) without a complete `relevance` ({ids}): rate {axes}, ask the "
              "person what cannot be estimated, null if they do not know (SKILL.md, \"The "
              "model\")",
        "fr": "{count} tâche(s) sans `relevance` complète ({ids}) : noter {axes}, demander à la "
              "personne ce qui ne s'estime pas, null si elle ne sait pas (SKILL.md, « The "
              "model »)"},
    "validate.data": {
        "en": "{count} M, C or S task(s) without `data` ({ids}): write the data sources they read "
              "or write, ids of catalogues/data-sources.yaml or sources declared in "
              "`data_sources` (SKILL.md, \"The model\")",
        "fr": "{count} tâche(s) M, C ou S sans `data` ({ids}) : écrire les sources de données "
              "qu'elles lisent ou écrivent, identifiants de catalogues/data-sources.yaml ou "
              "sources déclarées dans `data_sources` (SKILL.md, « The model »)"},
    "validate.runs": {
        "en": "{count} active task(s) without `measure.runs` ({ids}): ask how many times a month "
              "it runs, A and J tasks included; an A task gives the runs alone, without minutes "
              "(SKILL.md, \"The model\")",
        "fr": "{count} tâche(s) active(s) sans `measure.runs` ({ids}) : demander combien de fois "
              "par mois elle est faite, tâches A et J comprises ; une tâche A donne le nombre de "
              "fois seul, sans minutes (SKILL.md, « The model »)"},
    "validate.minutes": {
        "en": "{count} M, C, S or J task(s) without `measure.minutes` ({ids}): ask the minutes "
              "a person spends on one run (SKILL.md, \"The model\")",
        "fr": "{count} tâche(s) M, C, S ou J sans `measure.minutes` ({ids}) : demander les "
              "minutes qu'une personne passe sur une exécution (SKILL.md, « The model »)"},
    "validate.stakes": {
        "en": "{count} M, C or S task(s) without `stakes` ({ids}): ask what happens when it is "
              "done late or badly (SKILL.md, \"The model\")",
        "fr": "{count} tâche(s) M, C ou S sans `stakes` ({ids}) : demander ce qui se passe "
              "quand elle est faite en retard ou mal (SKILL.md, « The model »)"},
    "validate.next": {
        "en": "{count} active process(es) without `next` ({ids}): ask which processes start "
              "when it ends; write `next: []` when it ends the chain (SKILL.md, step 4)",
        "fr": "{count} processus actif(s) sans `next` ({ids}) : demander quels processus "
              "démarrent quand il se termine ; écrire `next: []` quand il termine la chaîne "
              "(SKILL.md, step 4)"},
    "validate.detector": {
        "en": "`meta.detector` is {value}, expected \"{expected}\": the skill and the version "
              "that produced the map, so the merge knows what each version proposes (SKILL.md, "
              "step 5)",
        "fr": "`meta.detector` vaut {value}, attendu « {expected} » : le skill et la version qui "
              "ont produit la carte, pour que la fusion sache ce que propose chaque version "
              "(SKILL.md, step 5)"},
    "validate.lost": {
        "en": "{count} element(s) of the starting map missing from this one ({ids}): keep "
              "them, with `state: retired` if they no longer exist (SKILL.md, \"Updating a map "
              "already sent\")",
        "fr": "{count} élément(s) de la carte de départ absent(s) de celle-ci ({ids}) : les "
              "garder, avec `state: retired` s'ils n'existent plus (SKILL.md, « Updating a map "
              "already sent »)"},
    "validate.changes": {
        "en": "Since the starting map: {added} element(s) added ({ids}), {retired} retired, "
              "{status} status change(s), relevance added for {rated} task(s)",
        "fr": "Depuis la carte de départ : {added} élément(s) ajouté(s) ({ids}), {retired} "
              "retiré(s), {status} statut(s) changé(s), pertinence ajoutée pour {rated} "
              "tâche(s)"},
    "validate.none": {"en": "none", "fr": "aucun"},
    "validate.none_f": {"en": "none", "fr": "aucune"},
    "validate.or": {"en": " or ", "fr": " ou "},
    "validate.end_to_end": {
        "en": "{id}: end-to-end, but the trigger is manual or a step is not A",
        "fr": "{id} : end-to-end, mais le déclencheur est manuel ou une étape n'est pas A"},
    "validate.once_launched": {
        "en": "{id}: once-launched, but a step after the launch is not A",
        "fr": "{id} : once-launched, mais une étape après le lancement n'est pas A"},
    "validate.manual": {
        "en": "{id}: manual, but the step statuses give {values} (rule of §7 of "
              "references/format-rpt-v1.md)",
        "fr": "{id} : manual, mais les statuts des étapes donnent {values} (règle du §7 de "
              "references/format-rpt-v1.md)"},
    "validate.total": {"en": "Total", "fr": "Total"},
    "validate.percent": {"en": "{value}%", "fr": "{value} %"},
    "validate.role_summary": {
        "en": "{label}: {total} active tasks (A {A}, S {S}, C {C}, M {M}, J {J}), coverage {cover}",
        "fr": "{label} : {total} tâches actives (A {A}, S {S}, C {C}, M {M}, J {J}), couverture "
              "{cover}"},
    "validate.processes": {
        "en": "Processes that run on their own: {alone} · proposed processes: {proposed}",
        "fr": "Processus qui tournent seuls : {alone} · processus proposés : {proposed}"},
    "validate.connector_item": {
        "en": "{name} ({labels}, {count} M, C or S task(s))",
        "fr": "{name} ({labels}, {count} tâche(s) M, C ou S)"},
    "validate.connectors": {
        "en": "Connectors to activate first: {todo} · already reachable by the AI: {done}",
        "fr": "Connecteurs à activer en premier : {todo} · déjà accessibles à l'IA : {done}"},
    # The blockers of the map (references/format-rpt-v1.md §11; README_operations.md §1.14).
    "validate.blocker_source": {
        "en": "{id}: inferred blocker without `source`: write where it was found (slack, email, "
              "ticket, meeting) (SKILL.md, \"Blockers\")",
        "fr": "{id} : bloqueur déduit sans `source` : écrire où il a été trouvé (slack, email, "
              "ticket, meeting) (SKILL.md, « Blockers »)"},
    "validate.blocker_evidence": {
        "en": "{id}: blocker found in a source ({source}) without `evidence`: write where and "
              "when it was seen (\"Slack #channel, 2026-10-08\", \"ticket DP-6301\"), never "
              "the content of the message (SKILL.md, \"Blockers\")",
        "fr": "{id} : bloqueur trouvé dans une source ({source}) sans `evidence` : écrire où et "
              "quand il a été vu (« Slack #canal, 2026-10-08 », « ticket DP-6301 »), jamais le "
              "contenu du message (SKILL.md, « Blockers »)"},
    "validate.task_blocker": {
        "en": "{count} task(s) still write their own `blocker` ({ids}): move each problem to "
              "the `blockers` list, one entry per problem with the tasks it holds back, its "
              "state and the date it was first seen (SKILL.md, \"Blockers\")",
        "fr": "{count} tâche(s) écrivent encore leur propre `blocker` ({ids}) : déplacer chaque "
              "problème dans la liste `blockers`, une entrée par problème avec les tâches qu'il "
              "bloque, son état et la date où il a été vu la première fois (SKILL.md, "
              "« Blockers »)"},
    "validate.blockers_line": {
        "en": "Blockers: {total} ({states}); still holding tasks back: {current}",
        "fr": "Bloqueurs : {total} ({states}) ; bloquent encore des tâches : {current}"},
    "validate.blocker_item": {"en": "{id} {type} ({tasks})", "fr": "{id} {type} ({tasks})"},
    "validate.relevance_line": {
        "en": "Relevance: estimated for {rated} active task(s) out of {total}; most relevant M "
              "and S tasks: {best}",
        "fr": "Pertinence : estimée pour {rated} tâche(s) active(s) sur {total} ; tâches M et S "
              "les plus pertinentes : {best}"},
}
rpt_i18n.register(MESSAGES)


# The statuses where a person still does part of the work (README_operations.md §1.2): the
# manual, conversational and skilled tasks.
OPEN_STATUSES = ("M", "C", "S")

def main(argv):
    import preview_rpt
    argv = preview_rpt.use_config(argv)
    catalogues, argv = preview_rpt.split_option(argv, "catalogues")
    if catalogues:
        CATALOGUES[0] = os.path.abspath(catalogues)
    lang, argv = split_lang(argv)
    rpt_i18n.set_language(rpt_i18n.resolve(lang))  # until the configuration can be read
    paths, starts = split_args(argv)
    if not paths:
        print(__doc__)
        return 2
    try:
        import yaml  # noqa: F401 — build_rpt needs it
    except ImportError:
        print(tr("validate.pyyaml_missing"))
        return 2
    import build_rpt
    build_rpt.setup_language(lang)
    status = 0
    for path in paths:
        if len(paths) > 1:
            print(f"== {os.path.basename(path)}")
        status = max(status, check(path, "--format" in argv, starts))
        if len(paths) > 1:
            print()
    return status


def split_lang(argv):
    """The value of `--lang` (or `--lang=xx`), and the other arguments."""
    lang, rest, it = None, [], iter(argv)
    for arg in it:
        if arg == "--lang":
            lang = next(it, None)
        elif arg.startswith("--lang="):
            lang = arg.split("=", 1)[1]
        else:
            rest.append(arg)
    return lang, rest


def split_args(argv):
    """The maps to check, then the starting maps given after `--since` (or `--depuis`)."""
    paths, starts, target = [], [], None
    for arg in argv:
        if arg.startswith("-"):
            target = starts if arg in SINCE else None
        else:
            (paths if target is None else target).append(arg)
    return paths, starts


def check(path, reformat, starts=()):
    import yaml
    import build_rpt
    import preview_rpt

    if reformat:
        build_rpt.format_file(path)
    ref, errors = build_rpt.load(path, catalogue_dir=CATALOGUES[0] or REFERENCES)
    if CATALOGUES[0] and os.path.abspath(path) != REFERENCES:
        build_rpt.borrow(ref, REFERENCES)
    warnings = []
    if not errors:
        errors, warnings = build_rpt.validate(ref)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        warnings += detector_warnings(data) + code_warnings(data) + automation_warnings(ref)
        warnings += relevance_warnings(ref, build_rpt.RELEVANCE_AXES) + data_warnings(ref)
        warnings += measure_warnings(ref) + chain_warnings(ref) + blocker_warnings(ref)
        warnings += [tr("validate.data_alert", where=where, label=label, excerpt=excerpt)
                     for where, label, excerpt in preview_rpt.alerts(data)]
        if starts:
            lost, changes = update_check(ref, starting_elements(starts), build_rpt)
            warnings += lost
    for line in ([tr("cli.error", message=e) for e in errors]
                 + [tr("cli.warning", message=w) for w in warnings]):
        print(line)
    print(tr("cli.summary", errors=len(errors), warnings=len(warnings)))
    if errors:
        return 1
    print()
    for line in figures(ref, build_rpt) + ([changes] if starts else []):
        print(line)
    return 0


def skill_detector():
    """`<name>@<version>` of the skill this script belongs to, read in its SKILL.md (one folder
    up, in the repository as in the package); None when it cannot be read."""
    import re
    try:
        with open(os.path.join(HERE, "..", "SKILL.md"), encoding="utf-8") as f:
            head = f.read(4000)
    except OSError:
        return None
    name = re.search(r"(?m)^name:\s*(\S+)", head)
    version = re.search(r"(?m)^\s+version:\s*\"?(\d+(?:\.\d+)*)", head)
    return f"{name.group(1)}@{version.group(1)}" if name and version else None


def detector_warnings(data, expected=None):
    """`meta.detector` names the skill and the version that produced the map: absent or another
    version than the one running this check, it is flagged."""
    expected = expected or skill_detector()
    value = (data.get("meta") or {}).get("detector")
    if not expected or value == expected:
        return []
    return [tr("validate.detector", value=repr(value) if value else tr("validate.none"),
               expected=expected)]


def code_warnings(data):
    """One map per hat: every id carries the code of `meta.team`."""
    team = str((data.get("meta") or {}).get("team") or "").upper()
    ids = [str(x.get("id")) for kind in ("roles", "processes", "tasks")
           for x in data.get(kind) or [] if isinstance(x, dict)]
    other = sorted({i.split("-")[0] for i in ids if team and not i.upper().startswith(team + "-")})
    if not other:
        return []
    return [tr("validate.codes", codes=", ".join(other), team=team.lower())]


def relevance_warnings(ref, axes):
    """The tasks whose relevance is not written, or lacks some of its axes (an unknown axis is
    written null). A retired task is no longer done: it does not need one."""
    missing = [t["id"] for t in ref["tasks"] if t.get("state") != "retired"
               and not (isinstance(t.get("relevance"), dict)
                        and all(axis in t["relevance"] for axis in axes))]
    if not missing:
        return []
    return [tr("validate.relevance", count=len(missing), ids=", ".join(missing),
               axes=", ".join(axes))]


def data_warnings(ref):
    """The manual, conversational or skilled tasks that do not say which data they read or
    write: a connector would help most to automate them."""
    missing = [t["id"] for t in ref["tasks"] if t.get("state") != "retired"
               and t.get("status") in OPEN_STATUSES and not t.get("data")]
    if not missing:
        return []
    return [tr("validate.data", count=len(missing), ids=", ".join(missing))]


def measure_warnings(ref):
    """The active tasks without a measure or without stakes: without them, their gain stays an
    estimate drawn from the ratings, the volume of a chain is unknown, and the action plan cannot
    tell which ones to take first. Every task gives its runs per month, A included (the volume
    that passes through it); a person spends minutes on an M, C, S or J task, none on an A task;
    the stakes are asked where a person still does the work that could change (M, C, S). A
    proposed task does not exist yet: it has nothing to measure."""
    live = [t for t in ref["tasks"] if t.get("state") == "active"]

    def measured(t, key):
        m = t.get("measure")
        return isinstance(m, dict) and m.get(key) is not None

    checks = (("validate.runs", live, lambda t: measured(t, "runs")),
              ("validate.minutes", [t for t in live if t.get("status") in OPEN_STATUSES + ("J",)],
               lambda t: measured(t, "minutes")),
              ("validate.stakes", [t for t in live if t.get("status") in OPEN_STATUSES],
               lambda t: bool(t.get("stakes"))))
    warnings = []
    for key, tasks, ok in checks:
        missing = [t["id"] for t in tasks if not ok(t)]
        if missing:
            warnings.append(tr(key, count=len(missing), ids=", ".join(missing)))
    return warnings


def chain_warnings(ref):
    """The active processes that do not say what follows them: `next` lists the processes that
    start when this one ends, `next: []` says it ends the chain. Without it, the chains of
    production stop at the first process and the volume entering a chain reaches nothing."""
    missing = [p["id"] for p in ref["processes"]
               if p.get("state") == "active" and "next" not in p]
    return [tr("validate.next", count=len(missing), ids=", ".join(missing))] if missing else []


# Where a blocker is seen outside the interview: these sources need a trace (`evidence`).
SIGNAL_SOURCES = ("slack", "email", "ticket", "meeting")
CURRENT = ("open", "in_progress")


def blocker_warnings(ref):
    """The blockers of the map, beyond the form build_rpt.py checks: an inferred blocker says in
    which source it was found, a blocker found in a source says where and when (`evidence`), and
    the tasks that still write their own `blocker` move it to the list (the field stays
    readable, the merge turns it into an entry of the register)."""
    out = []
    for b in ref["blockers"]:
        if b.get("basis") == "inferred" and not b.get("source"):
            out.append(tr("validate.blocker_source", id=b.get("id")))
        source = b.get("source")
        if (source in SIGNAL_SOURCES or b.get("basis") == "inferred") and not b.get("evidence"):
            out.append(tr("validate.blocker_evidence", id=b.get("id"), source=source or "?"))
    old = [t["id"] for t in ref["tasks"] if t.get("state") != "retired"
           and (t.get("blocker") or t.get("blocker_type"))]
    if old:
        out.append(tr("validate.task_blocker", count=len(old), ids=", ".join(old)))
    return out


def blocked_tasks(ref):
    """The ids of the tasks a blocker of the list still holds back (open or in progress)."""
    return {x for b in ref["blockers"] if b.get("state") in CURRENT
            for x in b.get("tasks") or [] if isinstance(x, str)}


def blockers_line(ref):
    """How many blockers by state, and those still open or in progress, with their tasks."""
    if not ref["blockers"]:
        return None
    states = [b.get("state") for b in ref["blockers"]]
    counts = ", ".join(f"{rpt_i18n.label('blocker_state', s)} {states.count(s)}"
                       for s in ("open", "in_progress", "resolved", "dropped")
                       if states.count(s))
    current = [tr("validate.blocker_item", id=b.get("id"),
                  type=rpt_i18n.label("blocker_type", b.get("type")),
                  tasks=", ".join(str(x) for x in b.get("tasks") or []))
               for b in ref["blockers"] if b.get("state") in CURRENT]
    return tr("validate.blockers_line", total=len(states), states=counts,
              current=", ".join(current) or tr("validate.none"))


def starting_elements(paths):
    """The roles, processes and tasks of the starting maps, by id."""
    import yaml
    out = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for kind in ("roles", "processes", "tasks"):
            out.update({str(x["id"]): x for x in data.get(kind) or []
                        if isinstance(x, dict) and x.get("id")})
    return out


def update_check(ref, start, build_rpt):
    """Update: the elements of the starting map that disappeared, and what changed. Only the
    starting elements whose code is the code of an id of the map count."""
    now = {x["id"]: x for kind in ("roles", "processes", "tasks") for x in ref[kind]}
    codes = {i.split("-")[0] for i in now}
    before = {i: x for i, x in start.items() if i.split("-")[0] in codes}
    kept = [i for i in now if i in before]
    lost = [i for i in before if i not in now]
    added = [i for i in now if i not in before]
    retired = [i for i in kept if now[i].get("state") == "retired"
               and before[i].get("state") != "retired"]
    status = [i for i in kept if now[i].get("status") != before[i].get("status")]
    rated = [i for i in kept if build_rpt.relevance_score(now[i])
             and not build_rpt.relevance_score(before[i])]
    warnings = [tr("validate.lost", count=len(lost), ids=", ".join(lost))] if lost else []
    return warnings, tr("validate.changes", added=len(added),
                        ids=", ".join(added) or tr("validate.none"), retired=len(retired),
                        status=len(status), rated=len(rated))


def automation_warnings(ref):
    """A declared automation that the statuses of the steps contradict: higher than they allow
    (end-to-end, once-launched), or manual when the rule of §7 gives another value."""
    blocked = blocked_tasks(ref)
    tasks = {t.get("id"): dict(t, _open_blocker=t.get("id") in blocked) for t in ref["tasks"]}
    out = []
    for p in ref["processes"]:
        steps = [(tasks.get(s) or {}).get("status") for s in p.get("steps") or []]
        manual = (p.get("trigger") or {}).get("type") == "manual"
        if p.get("automation") == "end-to-end" and (manual or any(s != "A" for s in steps)):
            out.append(tr("validate.end_to_end", id=p["id"]))
        if p.get("automation") == "once-launched" and any(s != "A" for s in steps[1:]):
            out.append(tr("validate.once_launched", id=p["id"]))
        values = automation_values(p, tasks) if p.get("automation") == "manual" else set()
        if len(steps) > 1 and values and "manual" not in values:
            out.append(tr("validate.manual", id=p["id"],
                          values=tr("validate.or").join(sorted(values))))
    return out


def automation_values(p, tasks):
    """The values the rule of §7 gives from the statuses of the steps. With a manual trigger, a
    first M step is either a launch task or real work: the file does not say, both readings are
    kept."""
    steps = [tasks.get(s) or {} for s in p.get("steps") or []]
    manual = (p.get("trigger") or {}).get("type") == "manual"
    readings = [steps]
    if manual and steps and steps[0].get("status") == "M":
        readings.append(steps[1:])
    return {automation_value(work, manual) for work in readings}


def automation_value(work, manual):
    """The rule of §7 on the steps that count, the launch task removed."""
    status = [t.get("status") for t in work]
    other = [t for t in work if t.get("status") != "A"]
    if not other:
        return "once-launched" if manual else "end-to-end"
    if len(other) == 1 and (other[0].get("blocker") or other[0].get("_open_blocker")):
        return "one-change-away"
    m = status.count("M")
    if m > status.count("A") and m >= sum(status.count(x) for x in ("S", "C", "J")):
        return "manual"
    return "assisted"


def figures(ref, build_rpt):
    """Active tasks by status and coverage (A / (tasks − J)), by role then in total."""
    lines = []
    for role in ref["roles"]:
        tasks = [t for t in ref["tasks"] if t.get("role") == role.get("id")]
        lines.append(summary(f"{role['id']} {role['name']}", build_rpt, tasks))
    lines.append(summary(tr("validate.total"), build_rpt, ref["tasks"]))
    proposed = [p["id"] for p in ref["processes"] if p.get("state") == "proposed"]
    alone = [p["id"] for p in ref["processes"] if p.get("state") == "active"
             and p.get("automation") in ("end-to-end", "once-launched")]
    lines.append(tr("validate.processes", alone=", ".join(alone) or tr("validate.none"),
                    proposed=", ".join(proposed) or tr("validate.none")))
    lines.append(relevance_line(ref, build_rpt))
    return lines + [x for x in (blockers_line(ref),) if x] + [connectors_line(ref, build_rpt)]


def connectors_line(ref, build_rpt):
    """The tools that hold the data of the active tasks: those the AI does not reach yet, by
    number of M or S tasks, then those it already reaches."""
    build_rpt.enrich(ref)
    names = {t.get("id"): t.get("name") or t.get("id") for t in ref["tools"]}
    rows = build_rpt.connector_rows(ref)
    todo = [tr("validate.connector_item", name=names.get(r["tool"], r["tool"]),
               labels=build_rpt.connector_labels(r["connectors"]), count=r["ms"])
            for r in rows if not r["reached"]]
    done = [names.get(r["tool"], r["tool"]) for r in rows if r["reached"]]
    return tr("validate.connectors", todo=", ".join(todo) or tr("validate.none"),
              done=", ".join(done) or tr("validate.none"))


def relevance_line(ref, build_rpt):
    """How many active tasks have a relevance, and the most relevant M and S tasks."""
    tasks = build_rpt.active(ref["tasks"])
    rated = [t for t in tasks if build_rpt.relevance_score(t)]
    top = sorted((t for t in rated if t.get("status") in OPEN_STATUSES),
                 key=lambda t: -build_rpt.relevance_score(t))[:5]
    best = (", ".join(f"{t['id']} {build_rpt.relevance_label(t)}" for t in top)
            or tr("validate.none_f"))
    return tr("validate.relevance_line", rated=len(rated), total=len(tasks), best=best)


def summary(label, build_rpt, tasks):
    c = build_rpt.counts(build_rpt.active(tasks))
    cover = "—" if c["coverage"] is None else tr("validate.percent", value=c["coverage"])
    return tr("validate.role_summary", label=label, total=c["total"], A=c["A"], S=c["S"],
              C=c["C"], M=c["M"], J=c["J"], cover=cover)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
