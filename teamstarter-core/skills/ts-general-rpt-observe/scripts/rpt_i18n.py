"""The texts a person reads from the RPT scripts, in every language they exist in.

What the RPT scripts write in code is English; what a person reads is in their language. Every
message and every label of build_rpt.py lives here once, as a map by language code. Adding a
language means adding one entry per message and per label (a column), never touching the
scripts. A message missing in the current language is shown in the first language of
LANGUAGES, English.

    import rpt_i18n
    rpt_i18n.set_language("fr")
    rpt_i18n.t("check.required_missing", where="ex.rpt.yaml EX-T1.1", key="name")
    rpt_i18n.t("md.roles", lang="en")          # one text in another language than the current
    rpt_i18n.labels("status", "en")            # {"A": "automated", ...}

The current language is chosen once per run by the script (build_rpt.setup_language): `--lang`,
else the environment variable RPT_LANG, else `organization.language` of rpt-config.yaml, else
English. A message takes its values by name ({where}, {key}); a literal brace is written `{{`
or `}}`. A placeholder is never called `lang`: that name selects the language.

Another script (rpt_delta.py, rpt_match.py, validate_rpt.py, preview_rpt.py) adds its own
messages with register(), under its own prefix (delta., match., validate., preview.); a key that
already exists keeps its texts.
"""
import os
import re

LANGUAGES = ("en", "fr")  # the first one is the fallback
ENV = "RPT_LANG"
_STATE = {"lang": LANGUAGES[0]}
LANGUAGE_RE = re.compile(r"^[a-z]{2,3}$")


def set_language(lang):
    """Make `lang` the current language and return it. An empty or malformed value gives the
    fallback; a well-formed code without messages (de) is kept: catalogue texts may exist in it,
    and each message falls back to English."""
    code = str(lang or "").strip().lower()
    _STATE["lang"] = code if LANGUAGE_RE.match(code) else LANGUAGES[0]
    return _STATE["lang"]


def language():
    """The current language code."""
    return _STATE["lang"]


def resolve(cli=None, configured=None, environ=None):
    """The language of a run: `cli` (--lang), else RPT_LANG, else `configured` (the
    organization's language), else the fallback. A malformed value is skipped."""
    environ = os.environ if environ is None else environ
    for value in (cli, environ.get(ENV), configured):
        code = str(value or "").strip().lower()
        if LANGUAGE_RE.match(code):
            return code
    return LANGUAGES[0]


def t(key, /, lang=None, **values):
    """The message `key` in `lang` (default: the current language), its {placeholders} filled
    with `values`. Unknown key: KeyError (a typo in a script must fail its tests)."""
    texts = MESSAGES[key]
    text = texts.get(lang or _STATE["lang"]) or texts[LANGUAGES[0]]
    return text.format(**values)


def labels(name, lang=None):
    """One label table, {code: text} in `lang` (default: the current language)."""
    lang = lang or _STATE["lang"]
    return {code: texts.get(lang) or texts[LANGUAGES[0]] for code, texts in LABELS[name].items()}


def label(name, code, lang=None, default=None):
    """The label of one code; `default` (else the code itself) when the table has none."""
    texts = LABELS[name].get(code)
    if texts is None:
        return code if default is None else default
    return texts.get(lang or _STATE["lang"]) or texts[LANGUAGES[0]]


def register(messages):
    """Add the messages of another script. A key already defined keeps its texts (a script
    loaded twice registers the same keys twice); give each script its own prefix: delta.*,
    match.*, validate.*, preview.*."""
    for key, texts in messages.items():
        MESSAGES.setdefault(key, texts)


# ------------------------------------------------------------------------------- labels
# {table: {code: {language: text}}}. The explorer receives every table in every language.

LABELS = {
    # The blockers of the register (README_operations.md §1.14): their type and their state.
    "blocker_type": {
        "connector": {"en": "connector", "fr": "connecteur"},
        "method": {"en": "method to write", "fr": "méthode à écrire"},
        "tool": {"en": "tool to build", "fr": "outil à construire"},
        "decision": {"en": "decision to make", "fr": "décision à prendre"},
        "data": {"en": "data", "fr": "données"},
        "licence": {"en": "licence", "fr": "licence"},
        "access": {"en": "access", "fr": "accès"},
        "security": {"en": "security", "fr": "sécurité"},
        "budget": {"en": "budget", "fr": "budget"},
        "organization": {"en": "organization", "fr": "organisation"},
        "provider": {"en": "provider", "fr": "prestataire"},
        "other": {"en": "other", "fr": "autre"}},
    # The rights of the AI in a tool (README_operations.md §1.7).
    "right_action": {
        "read": {"en": "read", "fr": "lire"},
        "search": {"en": "search", "fr": "chercher"},
        "create": {"en": "create", "fr": "créer"},
        "update": {"en": "update", "fr": "modifier"},
        "delete": {"en": "delete", "fr": "supprimer"},
        "send": {"en": "send", "fr": "envoyer"},
        "run": {"en": "run", "fr": "lancer"},
        "other": {"en": "other", "fr": "autre"}},
    "right_state": {
        "enabled": {"en": "enabled", "fr": "activé"},
        "available": {"en": "offered, not enabled", "fr": "proposé, pas activé"},
        "unavailable": {"en": "not offered", "fr": "absent du connecteur"}},
    "blocker_state": {
        "open": {"en": "open", "fr": "ouvert"},
        "in_progress": {"en": "being resolved", "fr": "en cours de résolution"},
        "resolved": {"en": "resolved", "fr": "résolu"},
        "dropped": {"en": "dropped", "fr": "abandonné"}},
    # The structure of the company's OS (README_operations.md §1.15): what a zone holds, how far
    # a flow that feeds it is set up, what an insight is and where it stands.
    "zone_holds": {
        "reference": {"en": "reference knowledge", "fr": "savoir de référence"},
        "findings": {"en": "findings", "fr": "constats"},
        "records": {"en": "one record per entity", "fr": "une fiche par entité"},
        "process": {"en": "method and work in progress", "fr": "méthode et travail en cours"},
        "briefs": {"en": "distilled documents", "fr": "documents distillés"}},
    # The data map (README_operations.md §1.20): how recently a container changed, what it is,
    # whether it is still used.
    # Files to place (README_operations.md §1.20): the side of a task, the status of its files,
    # what a team answered to a proposal.
    "file_side": {
        "out": {"en": "deliverable", "fr": "livrable"},
        "in": {"en": "input", "fr": "entrée"}},
    "place_status": {
        "placed": {"en": "placed", "fr": "rangé"},
        "none": {"en": "no file", "fr": "pas de fichier"},
        "private": {"en": "not disclosed", "fr": "non communiqué"},
        "tree": {"en": "named by the data map only",
                 "fr": "nommé par la carte des données seulement"},
        "proposed": {"en": "proposed", "fr": "proposé"},
        "to_choose": {"en": "to choose", "fr": "à choisir"},
        "missing": {"en": "no folder in the tree", "fr": "aucun dossier dans l'arbre"}},
    # A branch of the tree no task writes or reads: tasks probably use it, or a task is missing.
    "untasked_status": {
        "to_link": {"en": "tasks to link", "fr": "tâches à relier"},
        "to_deduce": {"en": "task to deduce", "fr": "tâche à déduire"}},
    "place_decision": {
        "validated": {"en": "validated", "fr": "validé"},
        "elsewhere": {"en": "given elsewhere", "fr": "indiqué ailleurs"},
        "no_file": {"en": "no file", "fr": "pas de fichier"},
        "private": {"en": "not disclosed", "fr": "non communiqué"}},
    "freshness": {
        "fresh": {"en": "7 days or less", "fr": "7 jours ou moins"},
        "recent": {"en": "8 to 30 days", "fr": "8 à 30 jours"},
        "aging": {"en": "31 to 90 days", "fr": "31 à 90 jours"},
        "old": {"en": "91 to 180 days", "fr": "91 à 180 jours"},
        "stale": {"en": "more than 180 days", "fr": "plus de 180 jours"},
        "unknown": {"en": "unknown", "fr": "inconnue"}},
    "container_kind": {
        "folder": {"en": "folder", "fr": "dossier"},
        "file": {"en": "file", "fr": "fichier"},
        "document": {"en": "document", "fr": "document"},
        "spreadsheet": {"en": "spreadsheet", "fr": "tableur"},
        "presentation": {"en": "presentation", "fr": "présentation"},
        "database": {"en": "database", "fr": "base de données"},
        "page": {"en": "page", "fr": "page"},
        "object": {"en": "CRM object", "fr": "objet CRM"},
        "pipeline": {"en": "pipeline", "fr": "pipeline"},
        "list": {"en": "list", "fr": "liste"},
        "channel": {"en": "channel", "fr": "canal"},
        "label": {"en": "label", "fr": "libellé"},
        "project": {"en": "project", "fr": "projet"},
        "board": {"en": "board", "fr": "tableau"},
        "view": {"en": "view", "fr": "vue"},
        "other": {"en": "other", "fr": "autre"}},
    "container_state": {
        "active": {"en": "in use", "fr": "utilisé"},
        "archived": {"en": "archived", "fr": "archivé"},
        "duplicate": {"en": "duplicate", "fr": "doublon"},
        "unused": {"en": "unused", "fr": "inutilisé"}},
    "feed_state": {
        "live": {"en": "in place", "fr": "en place"},
        "manual": {"en": "by hand", "fr": "à la main"},
        "possible": {"en": "possible", "fr": "possible"}},
    "insight_kind": {
        "question": {"en": "question", "fr": "question"},
        "finding": {"en": "finding", "fr": "constat"}},
    "insight_state": {
        "answered": {"en": "answered", "fr": "répondue"},
        "partial": {"en": "partly answered", "fr": "en partie répondue"},
        "unanswered": {"en": "unanswered", "fr": "sans réponse"},
        "emerging": {"en": "emerging", "fr": "émergent"},
        "confirmed": {"en": "confirmed", "fr": "confirmé"},
        "acted": {"en": "being acted on", "fr": "traité"},
        "closed": {"en": "no longer true", "fr": "clos"}},
    # Access of a person's AI to the OS, recurring agents (README_operations.md §1.16).
    "access_mode": {
        "connector": {"en": "connector", "fr": "connecteur"},
        "local": {"en": "local folder shared with the AI", "fr": "dossier local partagé à l'IA"},
        "repository": {"en": "code repository", "fr": "dépôt de code"},
        "none": {"en": "no access", "fr": "aucun accès"}},
    "access_state": {
        "works": {"en": "works", "fr": "vérifié"},
        "not_found": {"en": "OS folder not found", "fr": "dossier de l'OS introuvable"},
        "unchecked": {"en": "not checked", "fr": "pas vérifié"},
        "none": {"en": "no access", "fr": "aucun accès"},
        "unknown": {"en": "not surveyed", "fr": "pas relevé"}},
    "person_state": {
        "active": {"en": "active", "fr": "active"},
        "left": {"en": "left the company", "fr": "a quitté l'entreprise"},
        "excluded": {"en": "out of the mapping's scope", "fr": "hors du périmètre de la carto"}},
    "agent_kind": {
        "managed-agent": {"en": "managed agent", "fr": "agent managé"},
        "routine": {"en": "Routine", "fr": "Routine"},
        "scheduled-task": {"en": "scheduled task", "fr": "tâche planifiée"},
        "worker": {"en": "worker", "fr": "worker"}},
    "source_scope": {
        "role": {"en": "specific to a role", "fr": "propre à un rôle"},
        "team": {"en": "specific to a team", "fr": "propre à une équipe"},
        "shared": {"en": "shared, kept by a role", "fr": "partagée, tenue par un rôle"},
        "transverse": {"en": "transverse", "fr": "transverse"},
        "unused": {"en": "no active task", "fr": "aucune tâche active"}},
    "os_status": {
        "included": {"en": "included", "fr": "incluse"},
        "to_add": {"en": "to add to the OS", "fr": "à ajouter à l'OS"},
        "excluded": {"en": "excluded on purpose", "fr": "exclue volontairement"},
        "undecided": {"en": "to decide", "fr": "à décider"}},
    "ai_profile": {
        "augmented": {"en": "Augmented organization", "fr": "Organisation augmentée"},
        "industrializer": {"en": "Industrializer", "fr": "Industrialisateur"},
        "delegator": {"en": "Delegator", "fr": "Délégateur"},
        "executor": {"en": "Executor", "fr": "Exécutant"},
        "controller": {"en": "Controller", "fr": "Contrôleur"},
        "investor": {"en": "Investor", "fr": "Investisseur"},
        "cautious": {"en": "Cautious and equipped", "fr": "Prudent outillé"},
        "manual": {"en": "Manual", "fr": "Manuel"}},
    "agent_stage": {
        "functional": {"en": "functional", "fr": "fonctionnel"},
        "efficient": {"en": "efficient", "fr": "efficace"},
        "refined": {"en": "refined", "fr": "affiné"}},
    "agent_state": {
        "construction": {"en": "being built", "fr": "en construction"},
        "live": {"en": "running", "fr": "en service"},
        "paused": {"en": "paused", "fr": "en pause"},
        "retired": {"en": "retired", "fr": "retiré"}},
    "decision_kind": {
        "offer": {"en": "offer", "fr": "offre"},
        "target": {"en": "target", "fr": "cible"},
        "positioning": {"en": "positioning", "fr": "positionnement"},
        "strategy": {"en": "strategy", "fr": "stratégie"},
        "roadmap": {"en": "roadmap", "fr": "roadmap"},
        "pricing": {"en": "pricing", "fr": "prix"},
        "method": {"en": "method", "fr": "méthode"}},
    "decision_state": {
        "active": {"en": "active", "fr": "active"},
        "proposed": {"en": "proposed", "fr": "proposée"},
        "retired": {"en": "retired", "fr": "retirée"}},
    "artifact_goal": {
        "understand": {"en": "understand", "fr": "comprendre"},
        "share": {"en": "share", "fr": "partager"},
        "decide": {"en": "decide", "fr": "décider"}},
    "artifact_state": {
        "live": {"en": "up to date", "fr": "à jour"},
        "stale": {"en": "out of date", "fr": "périmé"},
        "retired": {"en": "retired", "fr": "retiré"}},
    "status": {
        "A": {"en": "automated", "fr": "automatisée"},
        "S": {"en": "skilled", "fr": "skillisée"},
        "C": {"en": "conversational", "fr": "conversationnelle"},
        "M": {"en": "manual", "fr": "manuelle"},
        "J": {"en": "judgment", "fr": "jugement"}},
    "basis": {
        "observed": {"en": "found in a source", "fr": "relevé dans une source"},
        "declared": {"en": "declared", "fr": "déclaré"},
        "inferred": {"en": "inferred, to confirm", "fr": "déduit, à confirmer"}},
    "automation": {
        "end-to-end": {"en": "automated end to end", "fr": "automatisé de bout en bout"},
        "once-launched": {"en": "automated once launched", "fr": "automatisé une fois lancé"},
        "one-change-away": {"en": "one change away", "fr": "à un changement près"},
        "assisted": {"en": "assisted", "fr": "assisté"},
        "manual": {"en": "manual", "fr": "manuel"},
        "routing": {"en": "routing (not a fixed path)", "fr": "aiguillage (pas un chemin fixe)"}},
    # How the AI reaches the data of a tool (README_operations.md §1.7); None: not known yet.
    "connector": {
        "native": {"en": "Claude native MCP", "fr": "MCP natif Claude"},
        "mcp": {"en": "added MCP server", "fr": "serveur MCP ajouté"},
        "api": {"en": "API or script", "fr": "API ou script"},
        "export": {"en": "manual export", "fr": "export à la main"},
        "none": {"en": "not connected", "fr": "pas connecté"},
        None: {"en": "to be specified", "fr": "à préciser"}},
    # Categories of sensitive data and AI rules (README_operations.md §1.8).
    "sensitivity": {
        "internal": {"en": "Internal", "fr": "Interne"},
        "public": {"en": "Public", "fr": "Public"},
        "personal": {"en": "Personal data", "fr": "Données personnelles"},
        "client": {"en": "Client data", "fr": "Données de clients"},
        "hr": {"en": "HR data", "fr": "Données RH"},
        "internal_confidential": {"en": "Internal confidential", "fr": "Confidentiel interne"},
        "regulated": {"en": "Secret or regulated", "fr": "Secret ou réglementé"},
        "credentials": {"en": "Credentials and secrets", "fr": "Identifiants et secrets"}},
    "sensitivity_def": {
        "internal": {"en": "Non-confidential working information.",
                     "fr": "Information de travail non confidentielle."},
        "public": {"en": "Already published or meant to be.",
                   "fr": "Déjà publié ou destiné à l'être."},
        "personal": {"en": "What identifies a person: name, e-mail, phone, behaviour.",
                     "fr": "Ce qui identifie une personne : nom, e-mail, téléphone, "
                           "comportement."},
        "client": {"en": "Data and documents of a client, often under a confidentiality clause.",
                   "fr": "Données et documents d'un client, souvent sous clause de "
                         "confidentialité."},
        "hr": {"en": "Headcount, arrivals and departures, organization, positions.",
               "fr": "Effectifs, entrées et sorties, organisation, postes."},
        "internal_confidential": {
            "en": "Non-public finances, strategy, intellectual property (code included).",
            "fr": "Finances non publiques, stratégie, propriété intellectuelle (code compris)."},
        "regulated": {
            "en": "Sensitive personal data (health, opinions, biometrics), individual files and "
                  "named salaries, trade secrets, data under a regulatory or contractual "
                  "obligation.",
            "fr": "Données personnelles sensibles (santé, opinions, biométrie), dossiers "
                  "individuels et rémunérations nominatives, secret des affaires, données sous "
                  "obligation réglementaire ou contractuelle."},
        "credentials": {"en": "Logins, passwords, API keys, technical secrets.",
                        "fr": "Identifiants, mots de passe, clés d'API, secrets techniques."}},
    # What to check for one category, whatever its rule (charter template, art. 8.3).
    "sensitivity_note": {
        "client": {"en": "For a document received from a client, first check its "
                         "confidentiality clause.",
                   "fr": "Pour un document reçu d'un client, vérifier d'abord sa clause de "
                         "confidentialité."}},
    "ai_rule": {
        "allowed": {"en": "Allowed", "fr": "Autorisé"},
        "validated": {"en": "Validated tools", "fr": "Outils validés"},
        "minimized": {"en": "Minimize", "fr": "Minimiser"},
        "confidential": {"en": "Tools validated for confidential data",
                         "fr": "Outils validés pour le confidentiel"},
        "authorization": {"en": "Written authorization required",
                          "fr": "Autorisation écrite requise"},
        "forbidden": {"en": "Forbidden", "fr": "Interdit"}},
    "ai_rule_text": {
        "allowed": {"en": "Without restriction in professional tools.",
                    "fr": "Sans restriction dans les outils professionnels."},
        "validated": {"en": "In the professional tools the company has validated.",
                      "fr": "Dans les outils professionnels validés par l'entreprise."},
        "minimized": {
            "en": "In validated tools, passing only what the task needs; pseudonymize or "
                  "anonymize when possible; any new use is reported to the person in charge of "
                  "personal data (DPO).",
            "fr": "Dans les outils validés, en ne transmettant que ce qui sert la tâche ; "
                  "pseudonymiser ou anonymiser quand c'est possible ; tout nouvel usage est "
                  "signalé à la personne chargée des données personnelles (DPO)."},
        "confidential": {
            "en": "Only in tools validated for the confidential level, passing only what the "
                  "task needs.",
            "fr": "Seulement dans les outils validés pour le niveau confidentiel, en ne "
                  "transmettant que ce qui sert la tâche."},
        "authorization": {
            "en": "Forbidden without a prior written authorization of the body that decides "
                  "(AI committee or management).",
            "fr": "Interdit sauf autorisation écrite préalable de l'instance qui tranche "
                  "(comité IA ou direction)."},
        "forbidden": {"en": "Never passed to an AI.", "fr": "Jamais transmis à une IA."}},
}


# ----------------------------------------------------------------------------- messages
# {key: {language: text}}. Prefixes: load (reading files), check (errors), warn (warnings),
# config (rpt-config.yaml), obs (observations), apply (applying observations), md (the
# referentiel.md view), prompt (values filled into PROMPT.md), stats (--stats), okrs (--okrs),
# cli (command line), fmt and word (small pieces).

MESSAGES = {
    # Reading the files.
    "hint.flow": {
        "en": " — in a list between brackets [...] or braces {{...}}, put in quotes any text "
              "that contains a comma, \":\" or \"?\" (README_operations.md §3.2)",
        "fr": " — dans une liste entre crochets [...] ou accolades {{...}}, mettre entre "
              "guillemets tout texte qui contient une virgule, « : » ou « ? » "
              "(README_operations.md §3.2)"},
    "load.yaml_unreadable": {
        "en": "{file}: unreadable YAML ({error}){hint}",
        "fr": "{file}: YAML illisible ({error}){hint}"},
    "load.format_missing": {
        "en": "{file}: `format: {format}` missing",
        "fr": "{file}: `format: {format}` absent"},
    "load.unknown_top_key": {
        "en": "{file}: unknown top-level key `{key}`",
        "fr": "{file}: clé de premier niveau inconnue `{key}`"},
    "load.policy_twice": {
        "en": "{file}: `ai_policy` already declared in {other}",
        "fr": "{file}: `ai_policy` déjà déclarée dans {other}"},
    "load.policy_not_mapping": {
        "en": "{file}: `ai_policy` must be a mapping {{{keys}}}",
        "fr": "{file}: `ai_policy` doit être un objet {{{keys}}}"},
    "load.investment_twice": {
        "en": "{file}: `ai_investment` already declared in {other}",
        "fr": "{file}: `ai_investment` déjà déclaré dans {other}"},
    "load.investment_not_mapping": {
        "en": "{file}: `ai_investment` must be a mapping {{{keys}}}",
        "fr": "{file}: `ai_investment` doit être un objet {{{keys}}}"},
    "load.meta_unknown_key": {
        "en": "{file}: `meta` has an unknown field `{key}`",
        "fr": "{file}: `meta` a un champ inconnu `{key}`"},

    # Errors of the referential.
    "check.not_a_text": {
        "en": "{where}: `{key}` contains {value}, which is not a text{hint}",
        "fr": "{where}: `{key}` contient {value}, qui n'est pas un texte{hint}"},
    "check.required_missing": {
        "en": "{where}: required field `{key}` missing",
        "fr": "{where}: champ obligatoire `{key}` absent"},
    "check.unknown_field_comma": {
        "en": "{where}: unknown field `{key}` (unquoted comma in a list between braces?)",
        "fr": "{where}: champ inconnu `{key}` (virgule non protégée dans une liste entre "
              "accolades ?)"},
    "check.unknown_field": {
        "en": "{where}: unknown field `{key}`",
        "fr": "{where}: champ inconnu `{key}`"},
    "check.sub_unknown_field": {
        "en": "{where}: `{sub}` has an unknown field `{key}`",
        "fr": "{where}: `{sub}` a un champ inconnu `{key}`"},
    "check.localized": {
        "en": "{where}: `{key}` = {value}, expected a text or a map {{language: text}} "
              "(en, fr…)",
        "fr": "{where}: `{key}` = {value}, attendu un texte ou une table {{langue: texte}} "
              "(en, fr…)"},
    "check.localized_list": {
        "en": "{where}: `{key}` = {value}, expected a list of texts or a map "
              "{{language: [texts]}} (en, fr…)",
        "fr": "{where}: `{key}` = {value}, attendu une liste de textes ou une table "
              "{{langue: [textes]}} (en, fr…)"},
    "check.enum": {
        "en": "{where}: `{field}` = {value}, expected {expected}",
        "fr": "{where}: `{field}` = {value}, attendu {expected}"},
    "check.not_an_id": {
        "en": "{where}: `{field}` = {value} is not an id",
        "fr": "{where}: `{field}` = {value} n'est pas un identifiant"},
    "check.dangling": {
        "en": "{where}: `{field}` points to {value}, which is not in the referential",
        "fr": "{where}: `{field}` renvoie à {value}, absent du référentiel"},
    "check.wrong_kind": {
        "en": "{where}: `{field}` = {value} should be a {kinds}",
        "fr": "{where}: `{field}` = {value} devrait être un {kinds}"},
    "check.departments_empty": {
        "en": "{where}: `departments` empty",
        "fr": "{where}: `departments` vide"},
    "check.department_unknown": {
        "en": "{where}: unknown department `{department}`",
        "fr": "{where}: département inconnu `{department}`"},
    "check.id_malformed": {
        "en": "{where}: malformed {kind} id",
        "fr": "{where}: identifiant de {kind} mal formé"},
    "check.id_used": {
        "en": "{where}: id already used in {file}",
        "fr": "{where}: identifiant déjà utilisé dans {file}"},
    "check.synonym_taken": {
        "en": "{list} {id}: \"{word}\" already names {other}",
        "fr": "{list} {id}: « {word} » désigne déjà {other}"},
    "check.tool_prefix": {
        "en": "{where}: the id prefix must be the type `{type}`",
        "fr": "{where}: le préfixe de l'identifiant doit être le type `{type}`"},
    "check.source_os_shape": {
        "en": "{where}: `os` must be a mapping (status, reason).",
        "fr": "{where} : `os` doit être un dictionnaire (status, reason)."},
    "check.source_os_reason": {
        "en": "{where}: a source excluded from the OS says why (`os.reason`).",
        "fr": "{where} : une source exclue de l'OS dit pourquoi (`os.reason`)."},
    "check.source_tools_not_list": {
        "en": "{where}: `tools` = {value}, expected a list of {{tool, where, connector}}",
        "fr": "{where}: `tools` = {value}, attendu une liste de {{tool, where, connector}}"},
    "check.source_tool_not_mapping": {
        "en": "{where}: `tools` contains {value}, expected {{tool, where, connector}}",
        "fr": "{where}: `tools` contient {value}, attendu {{tool, where, connector}}"},
    "check.source_tool_missing": {
        "en": "{where}: an element of `tools` has no `tool`",
        "fr": "{where}: un élément de `tools` n'a pas de `tool`"},
    "check.tool_unknown": {
        "en": "{where}: unknown tool `{tool}`",
        "fr": "{where}: outil inconnu `{tool}`"},
    "check.tool_twice": {
        "en": "{where}: tool `{tool}` cited twice",
        "fr": "{where}: outil `{tool}` cité deux fois"},
    "check.queue_shape": {
        "en": "{where}: `queue` = {value}, expected {{count, unit, at, basis, source}} (198 tickets waiting on 2026-10-17: {{count: 198, unit: tickets, at: '2026-10-17'}})",
        "fr": "{where}: `queue` = {value}, attendu {{count, unit, at, basis, source}} (198 tickets en attente le 2026-10-17 : {{count: 198, unit: tickets, at: '2026-10-17'}})"},
    "check.queue_count": {
        "en": "{where}: `queue.count` = {value}, expected a number, 0 or more",
        "fr": "{where}: `queue.count` = {value}, attendu un nombre, 0 ou plus"},
    "check.queue_at": {
        "en": "{where}: `queue.at` = {value}, expected the date of the measure (YYYY-MM-DD)",
        "fr": "{where}: `queue.at` = {value}, attendu la date de la mesure (AAAA-MM-JJ)"},
    "check.volume_shape": {
        "en": "{where}: `trigger.volume` = {value}, expected {{count, kind, unit}}, a month (200 e-mails a month: {{count: 200, kind: document, unit: e-mails}})",
        "fr": "{where}: `trigger.volume` = {value}, attendu {{count, kind, unit}}, par mois (200 e-mails par mois : {{count: 200, kind: document, unit: e-mails}})"},
    "check.volume_count": {
        "en": "{where}: `trigger.volume.count` = {value}, expected a positive number of documents or events a month",
        "fr": "{where}: `trigger.volume.count` = {value}, attendu un nombre positif de documents ou d'événements par mois"},
    "check.volume_unit": {
        "en": "{where}: `trigger.volume.unit` empty: what the documents or events are (e-mails, letters, meetings), or no `unit`",
        "fr": "{where}: `trigger.volume.unit` vide : ce que sont les documents ou les événements (e-mails, lettres, réunions), ou pas de `unit`"},
    "check.process_step_inactive": {
        "en": "{where}: active process, step {step} not active",
        "fr": "{where}: processus actif, étape {step} non active"},
    "check.okrs_not_list": {
        "en": "{where}: `okrs` must be a list of KR ids",
        "fr": "{where}: `okrs` doit être une liste d'identifiants de KR"},
    "check.okrs_bad_id": {
        "en": "{where}: `okrs` = {value}, expected a KR id (`O1.2.KR1`)",
        "fr": "{where}: `okrs` = {value}, attendu un identifiant de KR (`O1.2.KR1`)"},
    "check.kr_unknown": {
        "en": "{where}: unknown KR `{kr}` (okrs.yaml)",
        "fr": "{where}: KR inconnu `{kr}` (okrs.yaml)"},
    "check.okr_parent": {
        "en": "{where}: `parent` = {value} is not another objective of okrs.yaml",
        "fr": "{where}: `parent` = {value} n'est pas un autre objectif de okrs.yaml"},
    "check.okr_loop": {
        "en": "{where}: `parent` = {value} makes a loop of objectives",
        "fr": "{where}: `parent` = {value} forme une boucle d'objectifs"},
    "check.team_unknown": {
        "en": "{where}: unknown team `{team}`",
        "fr": "{where}: équipe inconnue `{team}`"},
    "check.shared_kr": {
        "en": "{where}: `shared_key_results` points to `{kr}`, which is not a KR of another "
              "objective",
        "fr": "{where}: `shared_key_results` renvoie à `{kr}`, qui n'est pas un KR d'un autre "
              "objectif"},
    "check.kr_id": {
        "en": "{where}: KR id expected `{okr}.KR<n>`",
        "fr": "{where}: identifiant de KR attendu `{okr}.KR<n>`"},
    "check.not_a_number": {
        "en": "{where}: `{field}` = {value}, expected a number",
        "fr": "{where}: `{field}` = {value}, attendu un nombre"},
    "check.type_bad": {
        "en": "{where}: `type` = {value}, expected a `tt:…` id of task-types.yaml",
        "fr": "{where}: `type` = {value}, attendu un identifiant `tt:…` de task-types.yaml"},
    "check.type_unknown": {
        "en": "{where}: unknown type `{value}` (task-types.yaml)",
        "fr": "{where}: type inconnu `{value}` (task-types.yaml)"},
    "check.relevance_not_mapping": {
        "en": "{where}: `relevance` = {value}, expected {{{axes}}}",
        "fr": "{where}: `relevance` = {value}, attendu {{{axes}}}"},
    "check.axis_retired": {
        "en": "{where}: `relevance.{axis}` no longer exists: {why}",
        "fr": "{where}: `relevance.{axis}` n'existe plus : {why}"},
    "check.simplicity_retired": {
        "en": "replaced on 2026-09-30 by `describability` (structured input, deliverable and "
              "method, README_operations.md §1.6); remove `simplicity` and rate "
              "`describability`, the simplicity rating does not carry over",
        "fr": "remplacée le 2026-09-30 par `describability` (entrée, livrable et méthode "
              "structurés, README_operations.md §1.6) ; retirer `simplicity` et noter "
              "`describability`, la note de simplicité ne se reporte pas"},
    "check.axis_value": {
        "en": "{where}: `{field}` = {value}, expected 1, 2, 3 or null",
        "fr": "{where}: `{field}` = {value}, attendu 1, 2, 3 ou null"},
    "check.measure_not_mapping": {
        "en": "{where}: `measure` = {value}, expected {{minutes, runs, basis}}",
        "fr": "{where}: `measure` = {value}, attendu {{minutes, runs, basis}}"},
    "check.positive": {
        "en": "{where}: `measure.{key}` = {value}, expected a number above 0",
        "fr": "{where}: `measure.{key}` = {value}, attendu un nombre supérieur à 0"},
    "check.plan_shape": {
        "en": "{where} = {value}, expected {{tool, plan, tier, modes}}",
        "fr": "{where} = {value}, attendu {{tool, plan, tier, modes}}"},
    "check.amount": {
        "en": "{where}: `{key}` = {value}, expected {{{keys}}} with an amount above 0",
        "fr": "{where}: `{key}` = {value}, attendu {{{keys}}} avec un montant supérieur à 0"},
    "check.cost_minutes": {
        "en": "{where}: `cost_ratio.minutes` = {value}, expected the minutes of human work the "
              "amount pays for (30 for « 5 euros for 30 minutes »)",
        "fr": "{where}: `cost_ratio.minutes` = {value}, attendu les minutes de travail humain "
              "que le montant paie (30 pour « 5 euros pour 30 minutes »)"},
    "check.enforced": {
        "en": "{where}: `enforced` = {value}, expected true or false",
        "fr": "{where}: `enforced` = {value}, attendu true ou false"},
    "check.stakes_not_mapping": {
        "en": "{where}: `stakes` = {value}, expected {{level, text}}",
        "fr": "{where}: `stakes` = {value}, attendu {{level, text}}"},
    "check.job_not_mapping": {
        "en": "{where}: `job` = {value}, expected {{when, so_that}}",
        "fr": "{where}: `job` = {value}, attendu {{when, so_that}}"},
    "check.job_part": {
        "en": "{where}: `job.{key}` is missing or empty; the job needs both parts",
        "fr": "{where}: `job.{key}` manque ou est vide ; le job a besoin de ses deux parties"},
    "check.job_lead": {
        "en": "{where}: `job.{key}` starts with « {value} »: write it without its leading words, "
              "the views add « When » and « so that »",
        "fr": "{where}: `job.{key}` commence par « {value} » : l'écrire sans ses mots d'entrée, "
              "les vues ajoutent « Quand » et « pour que »"},
    "check.build_not_mapping": {
        "en": "{where}: `build` = {value}, expected {{size, kind}}",
        "fr": "{where}: `build` = {value}, attendu {{size, kind}}"},
    "check.sensitivity_not_list": {
        "en": "{where}: `sensitivity` = {value}, expected a list among {values}, or [] for "
              "internal data",
        "fr": "{where}: `sensitivity` = {value}, attendu une liste parmi {values}, ou [] pour "
              "des données internes"},
    "check.basis_not_mapping": {
        "en": "{where}: `basis` = {value}, expected {{field: observed | declared | inferred}}",
        "fr": "{where}: `basis` = {value}, attendu {{champ: observed | declared | inferred}}"},
    "check.basis_field": {
        "en": "{where}: `basis` cites `{key}`, which is not a field to source",
        "fr": "{where}: `basis` cite `{key}`, qui n'est pas un champ à sourcer"},
    "check.method": {
        "en": "{where}: `method` = {value}, expected a URL (https://…) or the id of a tool of "
              "the catalogue (skill:…, reference:…)",
        "fr": "{where}: `method` = {value}, attendu une URL (https://…) ou l'identifiant d'un "
              "outil du catalogue (skill:…, reference:…)"},
    "check.files_not_mapping": {
        "en": "{where}: expected {{kind, url, pattern, tool, what, container}}",
        "fr": "{where}: attendu {{kind, url, pattern, tool, what, container}}"},
    "check.files_kind_missing": {
        "en": "{where}: `kind` missing (file, folder, none or private)",
        "fr": "{where}: `kind` absent (file, folder, none ou private)"},
    "check.files_none_alone": {
        "en": "{where}: `kind: {kind}` (none: the task keeps no file on this side; private: where "
              "is not disclosed) is the only entry of its list",
        "fr": "{where}: `kind: {kind}` (none : la tâche ne garde pas de fichier de ce côté ; "
              "private : l'emplacement n'est pas communiqué) est la seule entrée de sa liste"},
    "check.files_private_place": {
        "en": "{where}: `kind: private` says the place is not disclosed: no `url`, `pattern` or "
              "`container`",
        "fr": "{where}: `kind: private` dit que l'emplacement n'est pas communiqué : ni `url`, "
              "ni `pattern`, ni `container`"},
    "check.url": {
        "en": "{where}: `url` = {value}, expected a URL (https://…)",
        "fr": "{where}: `url` = {value}, attendu une URL (https://…)"},
    "check.file_needs_url": {
        "en": "{where}: a fixed file (`kind: file`) has a `url`",
        "fr": "{where}: un fichier fixe (`kind: file`) a une `url`"},
    "check.url_or_pattern": {
        "en": "{where}: `url` or `pattern` expected",
        "fr": "{where}: `url` ou `pattern` attendu"},
    "check.template_not_mapping": {
        "en": "{where}: expected {{url, tool, what}} with a `url`",
        "fr": "{where}: attendu {{url, tool, what}} avec une `url`"},
    "check.template_url": {
        "en": "{where}: `url` = {value}, expected a URL (https://…) or the id of a tool of the "
              "catalogue",
        "fr": "{where}: `url` = {value}, attendu une URL (https://…) ou l'identifiant d'un "
              "outil du catalogue"},
    "check.handoffs_not_list": {
        "en": "{where}: `handoffs` = {value}, expected a list of {{to, what, via, issues}}",
        "fr": "{where}: `handoffs` = {value}, attendu une liste de {{to, what, via, issues}}"},
    "check.handoff_not_mapping": {
        "en": "{where}: `handoffs` contains {value}, expected {{to, what, via, issues}}",
        "fr": "{where}: `handoffs` contient {value}, attendu {{to, what, via, issues}}"},
    "check.handoff_missing": {
        "en": "{where}: a handoff (`handoffs`) has no `{key}`",
        "fr": "{where}: un passage de main (`handoffs`) n'a pas de `{key}`"},
    "check.rules_not_mapping": {
        "en": "{where}: `rules` = {value}, expected {{category: rule}}",
        "fr": "{where}: `rules` = {value}, attendu {{catégorie: règle}}"},
    "check.rules_category": {
        "en": "{where}: `rules` cites `{key}`, expected a category among {values}",
        "fr": "{where}: `rules` cite `{key}`, attendu une catégorie parmi {values}"},

    # Warnings of the referential.
    "warn.skilled_without_skill": {
        "en": "{where}: status S (skilled), but `tools` cites no skill, agent or routine: C (conversational) if the AI only helps in a chat, or the skill to cite",
        "fr": "{where} : statut S (skillisée), mais `tools` ne cite aucun skill, agent ou routine : C (conversationnelle) si l'IA aide seulement dans un chat, sinon le skill à citer"},
    "warn.no_config": {
        "en": "{folder}: no rpt-config.yaml (here, in its two parent folders, --config or RPT_CONFIG): the views are built without a global context or an intake address",
        "fr": "{folder} : aucune rpt-config.yaml (ici, dans ses deux dossiers parents, --config ou RPT_CONFIG) : les vues sont construites sans contexte global ni adresse de dépôt"},
    "warn.source_owner_no_task": {
        "en": "{where}: owner {owner} has no active task that cites this source (who keeps it "
              "up to date?, README_operations.md §1.7)",
        "fr": "{where}: le responsable {owner} n'a aucune tâche active qui cite cette source "
              "(qui la tient à jour ?, README_operations.md §1.7)"},
    "warn.source_without_tool": {
        "en": "{where}: data source without a tool (where is it?)",
        "fr": "{where}: source de données sans outil (où se trouve-t-elle ?)"},
    "warn.sensitivity_unsaid": {
        "en": "{where}: sensitivity not stated (`sensitivity`, README_operations.md §1.8)",
        "fr": "{where}: sensibilité non dite (`sensitivity`, README_operations.md §1.8)"},
    "warn.retired_without_replacement": {
        "en": "{where}: retired process without `replaced_by`",
        "fr": "{where}: processus retiré sans `replaced_by`"},
    "warn.process_too_short": {
        "en": "{where}: {count} step(s) — a process has at least two tasks",
        "fr": "{where}: {count} étape(s) — un processus a au moins deux tâches"},
    "warn.task_without_by": {
        "en": "{where}: {status} task without `by` (who does it?)",
        "fr": "{where}: tâche {status} sans `by` (qui la fait ?)"},
    "warn.task_without_type": {
        "en": "{where}: task without `type` (task-types.yaml, README_operations.md §1.11; the "
              "merge assigns it)",
        "fr": "{where}: tâche sans `type` (task-types.yaml, README_operations.md §1.11 ; la "
              "fusion l'attribue)"},
    "check.blocker_tasks": {
        "en": "{where}: `tasks` must list the ids of the tasks the blocker holds back "
              "(README_operations.md §1.14)",
        "fr": "{where}: `tasks` doit lister les ids des tâches que le bloqueur retient "
              "(README_operations.md §1.14)"},
    "check.blocker_date": {
        "en": "{where}: `{field}` = {value} is not a date YYYY-MM-DD",
        "fr": "{where}: `{field}` = {value} n'est pas une date AAAA-MM-JJ"},
    "check.blocker_resolved_missing": {
        "en": "{where}: a blocker in state `{state}` gives the date it was closed (`resolved`)",
        "fr": "{where}: un bloqueur à l'état `{state}` donne la date de sa clôture (`resolved`)"},
    "check.blocker_resolved_open": {
        "en": "{where}: `resolved` is only written once the blocker is resolved or dropped "
              "(state `{state}`)",
        "fr": "{where}: `resolved` ne s'écrit qu'une fois le bloqueur résolu ou abandonné "
              "(état `{state}`)"},
    "check.blocker_dates_order": {
        "en": "{where}: `resolved` comes before `opened`",
        "fr": "{where}: `resolved` est antérieur à `opened`"},
    "warn.blocker_twice": {
        "en": "{where}: same problem as {other}: one blocker, several tasks in its `tasks`",
        "fr": "{where}: même problème que {other} : un seul bloqueur, plusieurs tâches dans "
              "son `tasks`"},
    "warn.blocker_no_resolution": {
        "en": "{where}: closed without `resolution`: say what lifted it, or why it is dropped",
        "fr": "{where}: clos sans `resolution` : dire ce qui l'a levé, ou pourquoi il est "
              "abandonné"},
    "warn.blocker_tasks_done": {
        "en": "{where}: still open while all its tasks are automated or retired: resolved?",
        "fr": "{where}: encore ouvert alors que toutes ses tâches sont automatisées ou "
              "retirées : résolu ?"},
    "warn.task_blocker_field": {
        "en": "{where}: `blocker` / `blocker_type` on the task: in the referential, a blocker "
              "is an entry of {file} (README_operations.md §1.14)",
        "fr": "{where}: `blocker` / `blocker_type` sur la tâche : dans le référentiel, un "
              "bloqueur est une entrée de {file} (README_operations.md §1.14)"},
    "check.rights_not_list": {
        "en": "{where}: `rights` is a list of {{action, what, state}} (README_operations.md §1.7)",
        "fr": "{where}: `rights` est une liste de {{action, what, state}} (README_operations.md "
              "§1.7)"},
    "md.rights_title": {"en": "### Rights of the AI by tool", "fr": "### Droits de l'IA par outil"},
    "md.rights_intro": {
        "en": "What the AI may do in each tool through its connector: enabled here, offered by "
              "the connector but not enabled, not offered (README_operations.md §1.7).",
        "fr": "Ce que l'IA peut faire dans chaque outil par son connecteur : activé chez nous, "
              "proposé par le connecteur mais pas activé, absent du connecteur "
              "(README_operations.md §1.7)."},
    "md.rights_header": {
        "en": "| Tool | Enabled | Offered, not enabled | Not offered | Checked on |",
        "fr": "| Outil | Activé | Proposé, pas activé | Absent du connecteur | Relevé le |"},
    # The structure of the OS and the insights (README_operations.md §1.15).
    "check.zone_parent": {
        "en": "{where}: `parent` {parent} is not a zone of the OS, or the zones form a loop",
        "fr": "{where}: `parent` {parent} n'est pas une zone de l'OS, ou les zones bouclent"},
    "check.feed_shape": {
        "en": "{where}: each flow of `feeds` is a mapping with `from` (a data source `data:…` "
              "or a zone `os:…`) and `state` (live, manual, possible)",
        "fr": "{where}: chaque flux de `feeds` est un dictionnaire avec `from` (une source "
              "`data:…` ou une zone `os:…`) et `state` (live, manual, possible)"},
    "check.feed_from": {
        "en": "{where}: `from` {value} is neither a data source of the catalogue nor a zone",
        "fr": "{where}: `from` {value} n'est ni une source du catalogue ni une zone"},
    "check.feed_insight": {
        "en": "{where}: `insights` cites {value}, missing from the insight register",
        "fr": "{where}: `insights` cite {value}, absent du registre des insights"},
    "check.insight_state": {
        "en": "{where}: a {kind} has the state {expected}, not {value}",
        "fr": "{where}: un insight de type {kind} a l'état {expected}, pas {value}"},
    "check.insight_number": {
        "en": "{where}: `{field}` is a whole number of at least 1 ({value})",
        "fr": "{where}: `{field}` est un nombre entier d'au moins 1 ({value})"},
    "check.insight_accounts": {
        "en": "{where}: `accounts` ({accounts}) cannot exceed `count` ({count})",
        "fr": "{where}: `accounts` ({accounts}) ne peut pas dépasser `count` ({count})"},
    "check.insight_dates": {
        "en": "{where}: `{field}` is a date YYYY-MM-DD ({value}), `first_seen` before "
              "`last_seen`",
        "fr": "{where}: `{field}` est une date AAAA-MM-JJ ({value}), `first_seen` avant "
              "`last_seen`"},
    # The data map (README_operations.md §1.20).
    "check.container_count": {
        "en": "{where}: `{field}` is a whole number, 0 or more ({value})",
        "fr": "{where}: `{field}` est un nombre entier, 0 ou plus ({value})"},
    "check.container_url": {
        "en": "{where}: `url` is an https:// link ({value})",
        "fr": "{where}: `url` est un lien https:// ({value})"},
    "check.container_content": {
        "en": "{where}: `{field}` holds {kind} ({value}): the data map describes where the data "
              "is and how it is laid out, never a value of it; write a placeholder such as "
              "[Client] or [Amount]",
        "fr": "{where}: `{field}` contient {kind} ({value}) : la carte des données dit où est "
              "la donnée et comment elle est rangée, jamais une de ses valeurs ; écrire un "
              "gabarit comme [Client] ou [Montant]"},
    "check.container_cycle": {
        "en": "{where}: the containers form a loop through `parent`",
        "fr": "{where}: les contenants bouclent par `parent`"},
    "check.container_parent_tool": {
        "en": "{where}: its `parent` {parent} is in the tool {tool}; a container sits in the "
              "tool of its parent",
        "fr": "{where}: son `parent` {parent} est dans l'outil {tool} ; un contenant est dans "
              "l'outil de son parent"},
    "warn.zone_path": {
        "en": "{where}: the folder {path} does not exist in the OS",
        "fr": "{where}: le dossier {path} n'existe pas dans l'OS"},
    "warn.insight_file": {
        "en": "{where}: the file {path} does not exist in the OS",
        "fr": "{where}: le fichier {path} n'existe pas dans l'OS"},
    "warn.insight_no_feed": {
        "en": "{where}: no flow of the OS names this insight (`feeds[].insights` of a zone)",
        "fr": "{where}: aucun flux de l'OS ne nomme cet insight (`feeds[].insights` d'une zone)"},
    "warn.finding_no_count": {
        "en": "{where}: a finding gives the number of facts behind it (`count`) and of distinct "
              "accounts or people (`accounts`)",
        "fr": "{where}: un constat donne le nombre de faits qui le fondent (`count`) et de "
              "comptes ou de personnes distincts (`accounts`)"},
    "warn.files_one_side": {
        "en": "{where}: `{field}` names {container}, which does not name the task in `{link}` "
              "(data-map.yaml): write the link on both sides",
        "fr": "{where}: `{field}` nomme {container}, qui ne nomme pas la tâche dans `{link}` "
              "(data-map.yaml) : écrire le lien des deux côtés"},
    "warn.container_no_writer": {
        "en": "{where}: nobody is named for this active container: no task writes it "
              "(`written_by`) and no role owns it (`owner`)",
        "fr": "{where}: personne n'est nommé pour ce contenant actif : aucune tâche ne l'écrit "
              "(`written_by`) et aucun rôle n'en est responsable (`owner`)"},
    "check.shared_shape": {
        "en": "{where}: `shared` is a mapping with `channel` (slack, teams…), `audience` (all, or a list of team codes), `state` (works, not_found, unchecked), and optionally `reaches: os`, `checked`, `basis`, `evidence`, `notes`",
        "fr": "{where} : `shared` est un dictionnaire avec `channel` (slack, teams…), `audience` (all, ou une liste de codes d'équipe), `state` (works, not_found, unchecked), et en option `reaches: os`, `checked`, `basis`, `evidence`, `notes`"},
    "check.access_shape": {
        "en": "{where}: `os_access` is a list of mappings, each with `mode` (connector, local, "
              "repository, none) and `state` (works, not_found, unchecked)",
        "fr": "{where}: `os_access` est une liste de dictionnaires, chacun avec `mode` (connector, "
              "local, repository, none) et `state` (works, not_found, unchecked)"},
    "check.person_shared": {
        "en": "{where}: « {value} » alone can be several people ({names}): write the first and "
              "last name",
        "fr": "{where}: « {value} » seul peut désigner plusieurs personnes ({names}) : écrire le "
              "prénom et le nom"},
    "check.access_state": {
        "en": "{where}: an access gives its `state` (works, not_found, unchecked)",
        "fr": "{where}: un accès donne son `state` (works, not_found, unchecked)"},
    "warn.agent_config": {
        "en": "{where}: `config` = {path} is not a file of the repository",
        "fr": "{where} : `config` = {path} n'est pas un fichier du dépôt"},
    "check.agent_notify_shape": {
        "en": "{where}: `notify` is a list of {{channel, to, when, notes}}",
        "fr": "{where} : `notify` est une liste de {{channel, to, when, notes}}"},
    "check.agent_stage_shape": {
        "en": "{where}: `stage` is a mapping (level, checked, basis, evidence)",
        "fr": "{where} : `stage` est un dictionnaire (level, checked, basis, evidence)"},
    "check.agent_stage_evidence": {
        "en": "{where}: `stage.evidence` says what proves the stage (runs without repair, model, "
              "messages)",
        "fr": "{where} : `stage.evidence` dit ce qui prouve le stade (runs sans réparation, "
              "modèle, messages)"},
    "check.agent_stage": {
        "en": "{where}: stage `{level}` declared, criteria missing: {missing} "
              "(README_operations.md §1.16)",
        "fr": "{where} : stade `{level}` déclaré, critères manquants : {missing} "
              "(README_operations.md §1.16)"},
    "warn.agent_no_task": {
        "en": "{where}: a running agent names the tasks it does (`tasks`)",
        "fr": "{where}: un agent en service nomme les tâches qu'il fait (`tasks`)"},
    "warn.decision_no_source": {
        "en": "{where}: an active decision names what it depends on (`depends_on`: insights, "
              "zones, decisions, data sources)",
        "fr": "{where}: une décision active nomme ce dont elle dépend (`depends_on` : insights, "
              "zones, décisions, sources de données)"},
    "warn.artifact_no_source": {
        "en": "{where}: an artifact names what it depends on (`depends_on`)",
        "fr": "{where}: un artefact nomme ce dont il dépend (`depends_on`)"},
    "warn.artifact_refresh_incomplete": {
        "en": "{where}: an artifact regenerated without anyone asking (`refresh.cycle`) names "
              "what it is still missing: {missing}",
        "fr": "{where} : un artefact régénéré sans que personne le demande (`refresh.cycle`) "
              "nomme ce qui lui manque encore : {missing}"},
    "check.artifact_declared": {
        "en": "{where}: an artifact in use declares `{key}` (README_operations.md §1.17: who "
              "answers for it, when it is made again)",
        "fr": "{where} : un artefact en usage déclare `{key}` (README_operations.md §1.17 : qui "
              "en répond, quand il est refait)"},
    "check.refresh_shape": {
        "en": "{where}: `refresh` is a mapping with `cycle` (on-change, daily, weekly, monthly, "
              "quarterly, manual, once), `by` (the agent that regenerates it) and `notes`",
        "fr": "{where} : `refresh` est un dictionnaire avec `cycle` (on-change, daily, weekly, "
              "monthly, quarterly, manual, once), `by` (l'agent qui le régénère) et `notes`"},
    "check.generated_with_shape": {
        "en": "{where}: `generated_with` is a mapping with `tool` (the skill of tools.yaml), "
              "`version` (its version that made the published version) and `date`",
        "fr": "{where} : `generated_with` est un dictionnaire avec `tool` (le skill de "
              "tools.yaml), `version` (sa version qui a fait la version publiée) et `date`"},
    "check.artifact_slack_to": {
        "en": "{where}: a Slack notification goes to a person (`person:` id, sent as a direct "
              "message) or to a channel (`#name`), not {value}",
        "fr": "{where} : une notification Slack va à une personne (id `person:`, envoyée en "
              "message privé) ou à un canal (`#nom`), pas {value}"},
    "check.purpose_shape": {
        "en": "{where}: `purpose` is a mapping with `goal` (understand, share, decide), "
              "`audience` and, to decide, `question`",
        "fr": "{where}: `purpose` est un dictionnaire avec `goal` (understand, share, decide), "
              "`audience` et, pour décider, `question`"},
    "check.purpose_question": {
        "en": "{where}: an artifact made to decide names the question its reviewer answers "
              "(`purpose.question`)",
        "fr": "{where}: un artefact fait pour décider nomme la question que son relecteur "
              "tranche (`purpose.question`)"},
    "md.decisions_title": {"en": "## Business decisions and artifacts",
                           "fr": "## Décisions métier et artefacts"},
    "md.decisions_intro": {
        "en": "{products} products. Decisions: {active} active, {proposed} proposed, {retired} "
              "retired; {traced} name what they depend on. Artifacts: {understand} to "
              "understand, {share} to share, {decide} to decide.",
        "fr": "{products} produits. Décisions : {active} actives, {proposed} proposées, "
              "{retired} retirées ; {traced} nomment ce dont elles dépendent. Artefacts : "
              "{understand} pour comprendre, {share} pour partager, {decide} pour décider."},
    "md.decisions_header": {
        "en": "| Decision | Kind | State | Depends on | Decided through | Shared by | Activates |",
        "fr": "| Décision | Genre | État | Dépend de | Décidée avec | Partagée par | Active |"},
    "md.artifacts_header": {
        "en": "| Artifact | Goal | For | Depends on | Produced by | State |",
        "fr": "| Artefact | But | Pour | Dépend de | Produit par | État |"},
    "md.people_title": {"en": "## Access to the OS", "fr": "## Accès à l'OS"},
    "md.people_intro": {
        "en": "{total} people. The AI of {works} of them reaches the OS (coverage {coverage} %); "
              "{unchecked} not checked, {not_found} with the folder not found, {none} without "
              "access, {unknown} not surveyed.",
        "fr": "{total} personnes. L'IA de {works} d'entre elles atteint l'OS (couverture "
              "{coverage} %) ; {unchecked} pas vérifiées, {not_found} dont le dossier est "
              "introuvable, {none} sans accès, {unknown} pas relevées."},
    "md.people_header": {"en": "| Person | Teams | Last map | Access | How |",
                         "fr": "| Personne | Équipes | Dernière carte | Accès | Comment |"},
    "md.people_maps": {
        "en": "{mapped} of them sent a map ({base}); maps of {fresh} of them are 30 days old "
              "or less, {never} never sent one (README_operations.md §1.16).",
        "fr": "{mapped} d'entre elles ont envoyé une carte ({base}) ; la dernière carte de "
              "{fresh} d'entre elles a 30 jours ou moins, {never} n'en ont jamais envoyé "
              "(README_operations.md §1.16)."},
    "md.people_base_headcount": {"en": "out of a headcount of {n}",
                                 "fr": "sur un effectif de {n}"},
    "md.people_base_known": {"en": "no headcount in rpt-config.yaml",
                             "fr": "pas d'effectif dans rpt-config.yaml"},
    "md.never": {"en": "never", "fr": "jamais"},
    "md.agents_title": {"en": "## Recurring agents", "fr": "## Agents récurrents"},
    "md.agents_intro": {
        "en": "{live} running, {construction} being built, {paused} paused, {retired} retired. "
              "Stages: {functional} functional, {efficient} efficient, {refined} refined, {none} "
              "not yet functional. Cost of the agents billed on the API: ${per_month} a month.",
        "fr": "{live} en service, {construction} en construction, {paused} en pause, {retired} "
              "retirés. Stades : {functional} fonctionnels, {efficient} efficaces, {refined} "
              "affinés, {none} pas encore fonctionnels. Coût des agents facturés à l'API : "
              "{per_month} $ par mois."},
    "md.agents_header": {"en": "| Agent | Kind | State | Stage | When | Tasks | People | Cost |",
                         "fr": "| Agent | Genre | État | Stade | Quand | Tâches | Personnes | Coût |"},
    "md.cost_included": {"en": "included in the subscription", "fr": "inclus dans l'abonnement"},
    "md.cost_run": {"en": "${v} / run", "fr": "{v} $ / run"},
    "md.cost_month": {"en": " · ${v} / month", "fr": " · {v} $ / mois"},
    "md.cost_estimate": {"en": " (estimate)", "fr": " (estimation)"},
    "check.cost_shape": {
        "en": "{where}: `cost` is a mapping (billing, per_run, model, tokens_in, tokens_out, "
              "web_searches, minutes, runs, currency, measured, basis, notes)",
        "fr": "{where}: `cost` est un dictionnaire (billing, per_run, model, tokens_in, "
              "tokens_out, web_searches, minutes, runs, currency, measured, basis, notes)"},
    "check.cost_number": {
        "en": "{where}: `cost.{field}` is a number, 0 or more ({value})",
        "fr": "{where}: `cost.{field}` est un nombre, 0 ou plus ({value})"},
    "check.cost_model": {
        "en": "{where}: `cost.model` {value} has no known rate ({models})",
        "fr": "{where}: `cost.model` {value} n'a pas de tarif connu ({models})"},
    "md.os_title": {"en": "## Structure of the OS", "fr": "## Structure de l'OS"},
    "md.datamap_title": {"en": "## Where the data is", "fr": "## Où est la donnée"},
    "md.datamap_intro": {
        "en": "{total} active containers, for {sources} of the {all} data sources of the "
              "catalogue; {owned} with a responsible role. Last change: {fresh} within 7 days, "
              "{recent} within 30, {aging} within 90, {old} within 180, {stale} older, "
              "{unknown} unknown.",
        "fr": "{total} contenants actifs, pour {sources} des {all} sources de données du "
              "catalogue ; {owned} avec un rôle responsable. Dernière modification : {fresh} à "
              "7 jours ou moins, {recent} à 30, {aging} à 90, {old} à 180, {stale} plus "
              "anciennes, {unknown} inconnues."},
    "md.datamap_header": {
        "en": "| Container | Data | Tool · place | Size | Freshness | Responsible (holders) |",
        "fr": "| Contenant | Donnée | Outil · emplacement | Taille | Fraîcheur | "
              "Responsable (titulaires) |"},
    "md.datamap_nobody": {"en": "nobody named", "fr": "personne de nommé"},
    "md.files_title": {"en": "## Files to place", "fr": "## Fichiers à ranger"},
    "md.files_intro": {
        "en": "{tasks} active tasks keep files (their deliverable or their input is a file, their "
              "data is in a tool that stores files) without anything saying where: {proposed} "
              "sides with a folder of the data map proposed, {to_choose} where no folder "
              "stands out, {missing} with no folder in the tree for their data. {placed} "
              "sides of tasks already have their place. A person of the team validates each "
              "proposal on the page « Files to place » of the explorer; the observation that "
              "records the answer writes the place into the task and the task into the folder "
              "(README_operations.md §1.20).",
        "fr": "{tasks} tâches actives gardent des fichiers (leur livrable ou leur entrée est un "
              "fichier, leur donnée est dans un outil qui stocke des fichiers) sans que rien ne "
              "dise où : {proposed} côtés avec un dossier de la carte des données proposé, "
              "{to_choose} où aucun dossier ne se détache, {missing} sans dossier dans "
              "l'arbre pour leur donnée. {placed} côtés de tâches ont déjà leur emplacement. Une "
              "personne de l'équipe valide chaque proposition dans la page « Fichiers à ranger » "
              "de l'explorateur ; l'observation qui garde la réponse écrit l'emplacement dans la "
              "tâche et la tâche dans le dossier (README_operations.md §1.20)."},
    "md.files_header": {
        "en": "| Task — deliverable or input | Side | Status | Folder proposed (or data without "
              "a folder) |",
        "fr": "| Tâche — livrable ou entrée | Côté | Statut | Dossier proposé (ou donnée sans "
              "dossier) |"},
    "md.files_missing_title": {
        "en": "### Folders missing from the tree", "fr": "### Dossiers manquants dans l'arbre"},
    "md.files_missing_header": {
        "en": "| Data | Tool | Tasks that keep files there | Only described there |",
        "fr": "| Donnée | Outil | Tâches qui y gardent des fichiers | Seulement décrit |"},
    "md.files_unknown_title": {
        "en": "### Links of the tasks the data map does not have",
        "fr": "### Liens des tâches absents de la carte des données"},
    "md.files_unknown_header": {"en": "| Link | Tasks |", "fr": "| Lien | Tâches |"},
    "md.files_untasked_title": {
        "en": "### Folders without a task", "fr": "### Dossiers sans tâche"},
    "md.files_untasked_intro": {
        "en": "{n} branches of the tree are written and read by no task, nor are the containers "
              "under them. A task without a folder lacks an instruction (where its files go); a "
              "folder without a task shows work the referential does not describe. {to_link} are "
              "probably used by the tasks listed (same data in the same tool and words in "
              "common, or proposed above): validate the proposal, or add them to `written_by` or "
              "`read_by`. {to_deduce} are used by no task of the referential: a task is missing; "
              "ask the role in charge or the people who work in them, and map it (skill "
              "ts-general-check-process-cartography). The most recently changed first.",
        "fr": "{n} branches de l'arbre ne sont écrites ni lues par aucune tâche, pas plus que "
              "les contenants qu'elles contiennent. Une tâche sans dossier manque d'une "
              "consigne (où vont ses fichiers) ; un dossier sans tâche montre un travail que le "
              "référentiel ne décrit pas. {to_link} sont probablement utilisées par les tâches "
              "listées (même donnée dans le même outil et mots en commun, ou proposées plus "
              "haut) : valider la proposition, ou les ajouter à `written_by` ou `read_by`. "
              "{to_deduce} ne sont utilisées par aucune tâche du référentiel : il manque une "
              "tâche ; demander au rôle responsable ou aux personnes qui y travaillent, et la "
              "cartographier (skill ts-general-check-process-cartography). Les plus récemment "
              "modifiées d'abord."},
    "md.files_untasked_header": {
        "en": "| Container | Tool · place | Last change | Status | Tasks that probably use it |",
        "fr": "| Contenant | Outil · emplacement | Dernière modification | Statut | Tâches qui "
              "l'utilisent probablement |"},
    "md.files_age": {"en": "{n} d ago", "fr": "il y a {n} j"},
    "md.files_owner": {"en": "kept by {role}", "fr": "tenu par {role}"},
    "md.files_loose": {
        "en": "Files left loose, described as one container ({n}): {ids}.",
        "fr": "Fichiers laissés en vrac, décrits comme un seul contenant ({n}) : {ids}."},
    "md.datamap_days": {"en": " ({n} d)", "fr": " ({n} j)"},
    "md.os_intro": {
        "en": "{zones} zones, {documents} documents. Flows: {live} in place, {manual} by hand, "
              "{possible} possible. Insights: {questions} questions, {findings} findings.",
        "fr": "{zones} zones, {documents} documents. Flux : {live} en place, {manual} à la "
              "main, {possible} possibles. Insights : {questions} questions, {findings} "
              "constats."},
    "md.os_header": {
        "en": "| Zone | Folder | Holds | Documents | Fed by | Insights |",
        "fr": "| Zone | Dossier | Contenu | Documents | Alimentée par | Insights |"},
    "md.os_integration": {
        "en": "Integration of the OS: {filled} leaves filled out of {leaves}, {live} without "
              "anyone; {with_facts} insights backed by facts out of {insights}, {fed_live} fed "
              "by a flow in place, {used} used (a finding acted on, a question answered); "
              "{reading} people out of {people} whose AI reads the OS.",
        "fr": "Intégration de l'OS : {filled} feuilles remplies sur {leaves}, dont {live} sans "
              "personne ; {with_facts} insights étayés par des faits sur {insights}, dont "
              "{fed_live} alimentés par un flux en place, {used} utilisés (un constat traité, "
              "une question répondue) ; {reading} personnes sur {people} dont l'IA lit l'OS."},
    "md.os_maturity": {
        "en": "Maturity of the zones: {none} without data, {data} with raw data, {insights} with "
              "insights drawn from the data, {auto} with data and insights that come in on their "
              "own.",
        "fr": "Maturité des zones : {none} sans données, {data} avec des données brutes, "
              "{insights} avec des insights tirés des données, {auto} avec des données et des "
              "insights qui entrent seuls."},
    "md.profile_title": {"en": "## AI profile", "fr": "## Profil IA"},
    "md.profile_company": {
        "en": "The company is **{profile}**{het}: execution at level {execution}, delegation at "
              "level {delegation}, infrastructure at level {infrastructure}, sharing with the AI "
              "at level {sharing}, control at level {control}, investment at level {investment} "
              "(levels 0 to 4, the mean of its teams weighted by their active tasks, rounded "
              "down; README_operations.md §1.18).",
        "fr": "L'entreprise est **{profile}**{het} : exécution au palier {execution}, "
              "délégation au palier {delegation}, infrastructure au palier {infrastructure}, "
              "partage avec l'IA au palier {sharing}, maîtrise au palier {control}, "
              "investissement au palier {investment} (paliers 0 à 4, la moyenne de ses équipes "
              "pondérée par leurs tâches actives, arrondie vers le bas ; README_operations.md "
              "§1.18)."},
    "md.profile_het": {
        "en": ", heterogeneous (its teams go from level {lo} to level {hi} in execution)",
        "fr": ", hétérogène (ses équipes vont du palier {lo} au palier {hi} en exécution)"},
    "md.profile_grade": {
        "en": "Grade **{letter}**: {points} points out of 24, the sum of the six levels "
              "(F 0-3, D 4-7, C 8-11, B 12-15, A 16-19, S 20-24){next}.",
        "fr": "Note **{letter}** : {points} points sur 24, la somme des six paliers "
              "(F 0-3, D 4-7, C 8-11, B 12-15, A 16-19, S 20-24){next}."},
    "md.profile_next": {
        "en": "; next grade: {letter}, from {points} points",
        "fr": " ; note suivante : {letter}, à partir de {points} points"},
    "md.profile_header": {
        "en": "| Team | Active tasks | Execution | Delegation | Infrastructure | Sharing | "
              "Control | Investment | Grade | Profile |",
        "fr": "| Équipe | Tâches actives | Exécution | Délégation | Infrastructure | Partage | "
              "Maîtrise | Investissement | Note | Profil |"},
    "md.os_freshness": {
        "en": "Freshness of the zones (their most recent dated document): {fresh} within 7 days, "
              "{recent} within 30, {aging} within 90, {old} within 180, {stale} older, {undated} "
              "without a dated document.",
        "fr": "Fraîcheur des zones (leur document daté le plus récent) : {fresh} à 7 jours ou "
              "moins, {recent} à 30, {aging} à 90, {old} à 180, {stale} plus anciennes, {undated} "
              "sans document daté."},
    "md.os_possible_title": {
        "en": "### Leaves to fill", "fr": "### Feuilles à remplir"},
    "md.os_possible_header": {
        "en": "| From | Tool | Into | What | Insights it would feed |",
        "fr": "| Depuis | Outil | Vers | Quoi | Insights qu'il alimenterait |"},
    "md.insights_title": {"en": "### Insights", "fr": "### Insights"},
    "md.insights_header": {
        "en": "| Id | Kind | Insight | Zone | State | Facts · accounts | Data |",
        "fr": "| Id | Type | Insight | Zone | État | Faits · comptes | Données |"},
    "md.blockers_title": {"en": "## Blockers", "fr": "## Bloqueurs"},
    "md.blockers_intro": {
        "en": "What keeps tasks from moving towards their target (README_operations.md §1.14): "
              "{open} open or being resolved, {done} resolved or dropped. Hours: what the "
              "blocked active tasks would give back per month and per person.",
        "fr": "Ce qui empêche des tâches d'avancer vers leur cible (README_operations.md "
              "§1.14) : {open} ouverts ou en cours, {done} résolus ou abandonnés. Heures : ce "
              "que les tâches actives bloquées rendraient par mois et par personne."},
    "md.blockers_header": {
        "en": "| Id | Problem | Type | State | Tasks | Since | Hours/month | Closed |",
        "fr": "| Id | Problème | Type | État | Tâches | Depuis | Heures/mois | Clos |"},
    "warn.too_many_krs": {
        "en": "{where}: {count} KRs in `okrs`: is the link direct? (2 at most, "
              "README_operations.md §1.13)",
        "fr": "{where}: {count} KR dans `okrs` : le lien est-il direct ? (au plus 2, "
              "README_operations.md §1.13)"},
    "warn.okr_without_kr": {
        "en": "{where}: objective without KR: an objective without an indicator cannot be "
              "measured",
        "fr": "{where}: objectif sans KR : un objectif sans indicateur ne se mesure pas"},
    "warn.activity_kr": {
        "en": "{where}: activity KR (`kind: activity`): it counts what is done, not the result",
        "fr": "{where}: KR d'activité (`kind: activity`) : il compte ce qu'on fait, pas le "
              "résultat"},
    "warn.no_rule": {
        "en": "{where}: no rule for the category `{category}`, which sources cite",
        "fr": "{where}: aucune règle pour la catégorie `{category}`, que des sources citent"},
    "warn.measure_effort": {
        "en": "{where}: `measure.minutes` = {minutes} gives an effort of {expected}, "
              "`relevance.effort` is {effort}: correct the effort rating",
        "fr": "{where}: `measure.minutes` = {minutes} donne un effort de {expected}, "
              "`relevance.effort` vaut {effort} : corriger la note d'effort"},
    "warn.tool_unused": {
        "en": "{where}: tool cited by no task and no process",
        "fr": "{where}: outil cité par aucune tâche ni aucun processus"},
    "warn.source_unused": {
        "en": "{where}: data source cited by no task",
        "fr": "{where}: source de données citée par aucune tâche"},

    # The organization's configuration (rpt-config.yaml).
    "config.not_mapping": {
        "en": "{where}: the file is not a YAML mapping",
        "fr": "{where} : le fichier n'est pas une table YAML"},
    "config.format": {
        "en": "{where}: `format: {format}` missing",
        "fr": "{where} : `format: {format}` absent"},
    "config.unknown_key": {
        "en": "{where}: unknown key `{key}`",
        "fr": "{where} : clé inconnue `{key}`"},
    "config.missing": {
        "en": "{where}: `{key}` missing",
        "fr": "{where} : `{key}` absent"},
    "config.referential_where": {
        "en": "{where}: `referential` says where the referential lives (`drive_folder` or "
              "`repository_path`)",
        "fr": "{where} : `referential` dit où vit le référentiel (`drive_folder` ou "
              "`repository_path`)"},
    "config.explorer_url": {
        "en": "{where}: `referential.explorer` must be an https:// URL",
        "fr": "{where} : `referential.explorer` doit être une URL https://"},
    "config.config_url": {
        "en": "{where}: `referential.config_url` = {value} must be an https:// link to this "
              "file or to the folder at whose root it is",
        "fr": "{where} : `referential.config_url` = {value} doit être un lien https:// vers ce "
              "fichier ou vers le dossier à la racine duquel il est"},
    "config.context_url": {
        "en": "{where}: `global_context` must cite `referential.config_url` ({value}): the "
              "skills find the configuration through the organization's instructions",
        "fr": "{where} : `global_context` doit citer `referential.config_url` ({value}) : les "
              "skills trouvent la configuration par les instructions de l'organisation"},
    "config.intake_where": {
        "en": "{where}: `intake` says where the maps arrive (`drive_folder` or `email`)",
        "fr": "{where} : `intake` dit où arrivent les cartes (`drive_folder` ou `email`)"},
    "config.email": {
        "en": "{where}: `intake.email` = {value} is not an address",
        "fr": "{where} : `intake.email` = {value} n'est pas une adresse"},
    "config.team_incomplete": {
        "en": "{where}: team {value} without `code` or `name`",
        "fr": "{where} : équipe {value} sans `code` ou `name`"},
    "config.team_code": {
        "en": "{where}: malformed team code `{code}` (lower case, digits, -)",
        "fr": "{where} : code d'équipe `{code}` mal formé (minuscules, chiffres, -)"},
    "config.team_twice": {
        "en": "{where}: team code `{code}` listed twice",
        "fr": "{where} : code d'équipe `{code}` en double"},
    "config.catalogue": {
        "en": "{where}: `catalogues.{key}` = {value}, expected a .yaml file name",
        "fr": "{where} : `catalogues.{key}` = {value}, attendu un nom de fichier .yaml"},
    "config.skill": {
        "en": "{where}: skill {value} without `name` or `where`",
        "fr": "{where} : skill {value} sans `name` ou `where`"},
    "config.context_long": {
        "en": "{where}: `global_context` has {size} characters, {max} at most (organization "
              "instructions)",
        "fr": "{where} : `global_context` fait {size} caractères, au plus {max} (instructions "
              "de l'organisation)"},
    "warn.person_gone": {
        "en": "{where}: {name} is `{state}` in people.yaml: give the work to the person who does "
              "it now (README_operations.md §1.16)",
        "fr": "{where} : {name} est `{state}` dans people.yaml : donner le travail à la personne "
              "qui le fait aujourd'hui (README_operations.md §1.16)"},
    "check.maps_shape": {
        "en": "{where}: `maps` = {value}: a list of `{{hat, date}}`, the team code of each map "
              "merged and its date ('YYYY-MM-DD') (README_operations.md §1.16)",
        "fr": "{where} : `maps` = {value} : une liste de `{{hat, date}}`, le code d'équipe de "
              "chaque carte fusionnée et sa date ('AAAA-MM-JJ') (README_operations.md §1.16)"},
    "config.headcount": {
        "en": "{where}: team `{code}`: `headcount` = {value}, expected a whole number of people "
              "(0 or more)",
        "fr": "{where} : équipe `{code}` : `headcount` = {value}, attendu un nombre entier de "
              "personnes (0 ou plus)"},
    "config.no_headcount": {
        "en": "{where}: teams without `headcount` ({codes}): write how many people each team "
              "has, so the explorer shows how much of the organization the maps cover "
              "(README_operations.md §3.3)",
        "fr": "{where} : équipes sans `headcount` ({codes}) : écrire combien de personnes compte "
              "chaque équipe, pour que l'explorateur montre quelle part de l'organisation les "
              "cartes couvrent (README_operations.md §3.3)"},
    "config.language": {
        "en": "{where}: `organization.language` = {value}, expected one of {languages}; "
              "messages are shown in English",
        "fr": "{where} : `organization.language` = {value}, attendu l'une de {languages} ; "
              "les messages s'affichent en anglais"},
    "config.team_unused": {
        "en": "rpt-config.yaml: team `{team}` used by the roles, missing from `teams`",
        "fr": "rpt-config.yaml : équipe `{team}` utilisée par les rôles, absente de `teams`"},

    # Values filled into PROMPT.md ({{organization}}, {{intake}}, {{archive}}).
    "prompt.drive": {
        "en": "to drop in the Drive folder `{folder}`",
        "fr": "à déposer dans le dossier Drive `{folder}`"},
    "prompt.email": {
        "en": "to send to {email}",
        "fr": "à envoyer à {email}"},
    "prompt.or": {"en": ", or ", "fr": ", ou "},
    "prompt.organization": {"en": "your organization", "fr": "votre organisation"},
    "prompt.back": {"en": "to send back to this person", "fr": "à renvoyer à cette personne"},
    "prompt.archive": {
        "en": "the folder of the maps already merged",
        "fr": "le dossier des cartes déjà fusionnées"},

    # Observations (README_operations.md §4.1).
    "obs.format": {
        "en": "{where}: `format: {format}` expected on the first line",
        "fr": "{where}: `format: {format}` attendu en première ligne"},
    "obs.meta_unknown": {
        "en": "{where}: unknown `meta.{key}`",
        "fr": "{where}: `meta.{key}` inconnu"},
    "obs.date": {
        "en": "{where}: `meta.date` expected, as YYYY-MM-DD",
        "fr": "{where}: `meta.date` attendu, au format AAAA-MM-JJ"},
    "obs.observer": {
        "en": "{where}: `meta.observer` expected: the person who approved sending it",
        "fr": "{where}: `meta.observer` attendu : la personne qui a validé l'envoi"},
    "obs.changes": {
        "en": "{where}: `changes` expected, a list of at least one change",
        "fr": "{where}: `changes` attendu, une liste d'au moins un changement"},
    "obs.one_target": {
        "en": "{where}: an observation is about one target (a task, the new tasks of a role or "
              "a data source), here {targets}: one file per target",
        "fr": "{where}: une observation porte sur une seule cible (une tâche, les tâches "
              "nouvelles d'un rôle ou une source de données), ici {targets} : un fichier par "
              "cible"},
    "obs.file_name": {
        "en": "{where}: expected name YYYY-MM-DD-<first name>-{slug}.yaml (the date, the "
              "person, then the target)",
        "fr": "{where}: nom attendu AAAA-MM-JJ-<prénom>-{slug}.yaml (la date, la personne, "
              "puis la cible)"},
    "obs.change_not_mapping": {
        "en": "{where}: expected {{task, field, before, after, basis, evidence}}",
        "fr": "{where}: attendu {{task, field, before, after, basis, evidence}}"},
    "obs.basis": {
        "en": "{where}: `basis` expected: observed (seen in the session) or declared (said by "
              "the person)",
        "fr": "{where}: `basis` attendu : observed (vu dans la session) ou declared (dit par "
              "la personne)"},
    "obs.evidence": {
        "en": "{where}: `evidence` expected: the sentence that says where the fact comes from",
        "fr": "{where}: `evidence` attendu : la phrase qui dit d'où vient le fait"},
    "obs.evidence_long": {
        "en": "{where}: `evidence` too long ({size} characters, {max} at most): a fact, not a "
              "content",
        "fr": "{where}: `evidence` trop long ({size} caractères, {max} au plus) : un fait, pas "
              "un contenu"},
    "obs.task_or_data": {
        "en": "{where}: a change is about a task (`task`), about the AI's access to a data "
              "source (`data` and `tool`), about a blocker of the register (`blocker`) or "
              "about a recurring agent (`agent`)",
        "fr": "{where}: un changement porte sur une tâche (`task`), sur l'accès de l'IA à une "
              "source de données (`data` et `tool`), sur un bloqueur du registre (`blocker`) "
              "ou sur un agent récurrent (`agent`)"},
    "obs.new_agent_shape": {
        "en": "{where}: a new agent is written `agent: new`, `field: agent`, and `after` its "
              "entry (id, name, kind, state, and what is known: schedule, tasks, skills…)",
        "fr": "{where}: un nouvel agent s'écrit `agent: new`, `field: agent`, et `after` sa "
              "fiche (id, name, kind, state, et ce qu'on sait : schedule, tasks, skills…)"},
    "obs.new_agent_missing": {
        "en": "{where}: the new agent has no `{key}`",
        "fr": "{where}: le nouvel agent n'a pas de `{key}`"},
    "obs.agent_id": {
        "en": "{where}: an agent id is written `ag:<name>` in lower case ({value})",
        "fr": "{where}: un id d'agent s'écrit `ag:<nom>` en minuscules ({value})"},
    "obs.agent_exists": {
        "en": "{where}: the agent {agent} is already in agents.yaml: propose its fields one by "
              "one (`agent: {agent}`)",
        "fr": "{where}: l'agent {agent} est déjà dans agents.yaml : proposer ses champs un par "
              "un (`agent: {agent}`)"},
    "obs.agent_unknown": {
        "en": "{where}: the agent {agent} is not in agents.yaml",
        "fr": "{where}: l'agent {agent} n'est pas dans agents.yaml"},
    "obs.label_new_agent": {"en": "new agent", "fr": "nouvel agent"},
    "obs.new_blocker_shape": {
        "en": "{where}: a new blocker is written `blocker: new`, `field: blocker`, `after: "
              "{{text, type, tasks}}` (README_operations.md §1.14)",
        "fr": "{where}: un nouveau bloqueur s'écrit `blocker: new`, `field: blocker`, `after: "
              "{{text, type, tasks}}` (README_operations.md §1.14)"},
    "obs.blocker_unknown": {
        "en": "{where}: the blocker {blocker} is not in the register",
        "fr": "{where}: le bloqueur {blocker} n'est pas dans le registre"},
    "obs.label_new_blocker": {"en": "new blocker", "fr": "nouveau bloqueur"},
    "obs.field": {
        "en": "{where}: `field` = {value}, expected: {fields}",
        "fr": "{where}: `field` = {value}, attendu : {fields}"},
    "obs.task_unknown": {
        "en": "{where}: unknown task `{task}`",
        "fr": "{where}: tâche inconnue `{task}`"},
    "obs.already": {
        "en": "{where}: already in the referential ({id} `{field}`)",
        "fr": "{where}: déjà dans le référentiel ({id} `{field}`)"},
    "obs.stale": {
        "en": "{where}: stale: {id} `{field}` is now {now}, the observation started from "
              "{before}",
        "fr": "{where}: périmé : {id} `{field}` vaut maintenant {now}, l'observation partait "
              "de {before}"},
    "obs.text_list": {
        "en": "{where}: `{key}` expected a list of texts",
        "fr": "{where}: `{key}` attendu une liste de textes"},
    "obs.new_task_shape": {
        "en": "{where}: a new task is written `task: new`, `field: task`, and `after` with at "
              "least `name`, `role`, `input` and `output`",
        "fr": "{where}: une tâche nouvelle s'écrit `task: new`, `field: task`, et `after` avec "
              "au moins `name`, `role`, `input` et `output`"},
    "obs.new_task_missing": {
        "en": "{where}: new task without `{key}`",
        "fr": "{where}: tâche nouvelle sans `{key}`"},
    "obs.connector_field": {
        "en": "{where}: a change on a data source has `field: connector`",
        "fr": "{where}: un changement sur une source de données a `field: connector`"},
    "obs.tool_expected": {
        "en": "{where}: `tool` expected: the tool where the AI reaches the data",
        "fr": "{where}: `tool` attendu : l'outil où l'IA atteint la donnée"},
    "obs.source_unknown": {
        "en": "{where}: unknown data source `{data}`",
        "fr": "{where}: source de données inconnue `{data}`"},
    "obs.not_a_tool_of": {
        "en": "{where}: `{tool}` is not a tool of {data}",
        "fr": "{where}: `{tool}` n'est pas un outil de {data}"},
    # --observations
    "obs.pending": {
        "en": "observations: {changes} pending change(s) in {files} file(s)",
        "fr": "observations : {changes} changement(s) en attente dans {files} fichier(s)"},
    "obs.pending_oldest": {
        "en": ", the oldest of {date}",
        "fr": ", le plus ancien du {date}"},
    "obs.title_new": {"en": "new tasks of the role", "fr": "tâches nouvelles du rôle"},
    "obs.title_data": {"en": "AI access", "fr": "accès de l'IA"},
    "obs.median": {
        "en": "  measure: {count} measures, median {median}",
        "fr": "  measure : {count} mesures, médiane {median}"},
    "obs.to_decide": {
        "en": "  {label}: {count} different values, to decide",
        "fr": "  {label} : {count} valeurs différentes, à trancher"},
    "obs.line": {
        "en": "  {label}: {before} → {after} [{bases}] — {count} observation(s): {who}",
        "fr": "  {label} : {before} → {after} [{bases}] — {count} observation(s) : {who}"},
    "obs.span": {"en": "from {start} to {end}", "fr": "du {start} au {end}"},
    "obs.evidence_line": {
        "en": "    \"{evidence}\" ({files})",
        "fr": "    « {evidence} » ({files})"},

    # Applying observations (--apply-observation).
    "apply.skipped": {"en": "{label}: {reason}", "fr": "{label} : {reason}"},
    "apply.new_task": {
        "en": "new task, to be written by the merge",
        "fr": "tâche nouvelle, à écrire par la fusion"},
    "apply.not_found": {"en": "not found", "fr": "introuvable"},
    "apply.borrowed": {
        "en": "borrowed from {file}, to change there",
        "fr": "emprunté à {file}, à changer là-bas"},
    "apply.already_note": {
        "en": "already in the referential",
        "fr": "déjà dans le référentiel"},
    "apply.tool_absent": {
        "en": "tool {tool} missing from the source",
        "fr": "outil {tool} absent de la source"},
    "apply.stale": {"en": "stale ({field} = {value})", "fr": "périmé ({field} = {value})"},
    "apply.task_absent": {"en": "task missing from its file", "fr": "tâche absente de son fichier"},

    # The referentiel.md view.
    "md.name": {"en": "RPT referential — generated view", "fr": "Référentiel RPT — vue générée"},
    "md.title": {
        "en": "# Referential of roles, processes and tasks — generated view",
        "fr": "# Référentiel des rôles, processus et tâches — vue générée"},
    "md.intro": {
        "en": "> File generated by `python3 teamstarter-os/tools/build_rpt.py` from the files\n"
              "> `*.rpt.yaml` of this folder. Do not edit it: edit the YAML, then run the tool "
              "again.\n"
              "> The model and the rules: [README_operations.md](./README_operations.md). The "
              "figures\n"
              "> count the active tasks; coverage = automated / (tasks − judgment).\n"
              "> Relevance of a task = (reach (P) + frequency (F) + effort (E) + describability "
              "(D))\n"
              "> × payback (R), each rated 1 to 3 (README_operations.md §1.6), out of {max}; an "
              "unknown axis counts 0 in the sum, an unknown payback counts 1;\n"
              "> \"?\": no axis of the sum estimated. Data of a task: the data sources\n"
              "> it reads or writes (`data-sources.yaml`, README_operations.md §1.7).",
        "fr": "> Fichier généré par `python3 teamstarter-os/tools/build_rpt.py` à partir des "
              "fichiers\n"
              "> `*.rpt.yaml` de ce dossier. Ne pas l'éditer : éditer le YAML, puis relancer "
              "l'outil.\n"
              "> Le modèle et les règles : [README_operations.md](./README_operations.md). Les "
              "chiffres\n"
              "> portent sur les tâches actives ; couverture = automatisées / (tâches − "
              "jugement).\n"
              "> Pertinence d'une tâche = (portée (P) + fréquence (F) + effort (E) + "
              "descriptabilité (D))\n"
              "> × retour sur investissement (R), chacun noté de 1 à 3 (README_operations.md "
              "§1.6), sur {max} ; un axe inconnu compte 0 dans la somme, un retour inconnu "
              "compte 1 ;\n"
              "> « ? » : aucun axe de la somme estimé. Données d'une tâche : les sources de "
              "données\n"
              "> qu'elle lit ou écrit (`data-sources.yaml`, README_operations.md §1.7)."},
    "md.figures": {"en": "## In figures", "fr": "## En chiffres"},
    "md.teams_header": {
        "en": "| Team | Roles | Active processes | Proposed processes | Tasks | A | S | C | M | J | "
              "Coverage |",
        "fr": "| Équipe | Rôles | Processus actifs | Processus proposés | Tâches | A | S | C | M | J "
              "| Couverture |"},
    "md.team_automated": {"en": "automated team", "fr": "équipe automatisée"},
    "md.departments_header": {
        "en": "| Department | Tasks | A | S | C | M | J | Coverage |",
        "fr": "| Département | Tâches | A | S | C | M | J | Couverture |"},
    "md.shared": {
        "en": "- Active tasks that are steps of several processes: {count} ({ids}).",
        "fr": "- Tâches actives étapes de plusieurs processus : {count} ({ids})."},
    "md.chains": {
        "en": "- Chains of production: {count}, of which {linked} of several processes; {volume} with the volume that enters them (README §1.19).",
        "fr": "- Chaînes de production : {count}, dont {linked} de plusieurs processus ; {volume} avec le volume qui y entre (README §1.19)."},
    "md.loose": {
        "en": "- Active tasks outside any process: {count}.",
        "fr": "- Tâches actives hors de tout processus : {count}."},
    "md.rated": {
        "en": "- Active tasks whose relevance is estimated: {rated} of {total}.",
        "fr": "- Tâches actives dont la pertinence est estimée : {rated} sur {total}."},
    "md.typed": {
        "en": "- Active tasks filed under a task type: {typed} of {total} ({used} types used of "
              "the {catalogue} of the catalogue `task-types.yaml`).",
        "fr": "- Tâches actives rangées dans un type de tâche : {typed} sur {total} ({used} "
              "types utilisés sur {catalogue} du catalogue `task-types.yaml`)."},
    "md.library_line": {
        "en": "- Skills and agents cited by active tasks: {tools}, serving {types} types; "
              "{several} serve several.",
        "fr": "- Skills et agents cités par des tâches actives : {tools}, qui servent {types} "
              "types ; {several} en servent plusieurs."},
    "md.sources_title": {"en": "## Data sources", "fr": "## Sources de données"},
    "md.sources_intro": {
        "en": "Each task cites in `data` the business data it reads or writes;\n"
              "[data-sources.yaml](./data-sources.yaml) says which tool holds each one and\n"
              "how the AI reaches it (README_operations.md §1.7).",
        "fr": "Chaque tâche cite dans `data` les données métier qu'elle lit ou écrit ;\n"
              "[data-sources.yaml](./data-sources.yaml) dit dans quel outil se trouve chacune "
              "et\n"
              "comment l'IA y accède (README_operations.md §1.7)."},
    "md.connectors_title": {
        "en": "### Connectors to activate first",
        "fr": "### Connecteurs à activer en priorité"},
    "md.connectors_intro": {
        "en": "Tools that hold the data of active tasks and that the AI does not reach\n"
              "yet (not connected, manual export, access to be specified), by number of manual,\n"
              "conversational or skilled tasks, then by estimated gain.",
        "fr": "Outils qui contiennent les données de tâches actives et que l'IA n'atteint pas\n"
              "encore (pas connecté, export à la main, accès à préciser), par nombre de tâches\n"
              "manuelles, conversationnelles ou skillisées, puis par gain estimé."},
    "md.connectors_header": {
        "en": "| Tool | AI access | Data | M, C or S tasks | Active tasks | Estimated gain |",
        "fr": "| Outil | Accès de l'IA | Données | Tâches M, C ou S | Tâches actives | Gain estimé |"},
    "md.gain": {
        "en": "≈ {hours} h/month ({count} estimated task(s))",
        "fr": "≈ {hours} h/mois ({count} tâche(s) estimée(s))"},
    "md.sources_list": {"en": "### The sources", "fr": "### Les sources"},
    "md.sources_os": {
        "en": "In the OS: {included} sources included (a flow brings them in), {to_add} to add "
              "(a flow is possible), {excluded} excluded on purpose, {undecided} not decided "
              "(no flow, no choice written).",
        "fr": "Dans l'OS : {included} sources incluses (un flux les fait entrer), {to_add} à "
              "ajouter (un flux est possible), {excluded} exclues volontairement, {undecided} "
              "non décidées (aucun flux, aucun choix écrit)."},
    "md.sources_scope": {
        "en": "Scope (§1.7, from the active tasks that cite each source): {role} specific to a "
              "role, {team} specific to a team, {shared} shared between teams and kept by a role "
              "(`owner`), {transverse} transverse (shared, no owner), {unused} cited by no active "
              "task.",
        "fr": "Portée (§1.7, d'après les tâches actives qui citent chaque source) : {role} "
              "propres à un rôle, {team} propres à une équipe, {shared} partagées entre équipes "
              "et tenues par un rôle (`owner`), {transverse} transverses (partagées, sans "
              "responsable), {unused} citées par aucune tâche active."},
    "md.scope_cell": {"en": "{scope}: {who}", "fr": "{scope} : {who}"},
    "md.sources_header": {
        "en": "| Source | Scope | In the OS | Sensitivity (AI rule) | Tools (AI access) "
              "| Active tasks | A | S | C | M | J |",
        "fr": "| Source | Portée | Dans l'OS | Sensibilité (règle IA) | Outils (accès de l'IA) "
              "| Tâches actives | A | S | C | M | J |"},
    "md.pair": {"en": "{name}: {value}", "fr": "{name} : {value}"},
    "md.separator": {"en": "; ", "fr": " ; "},
    "md.policy_none": {
        "en": "AI policy: none (`ai-policy.yaml`); the rules of the categories are to be "
              "decided.",
        "fr": "Politique IA : aucune (`ai-policy.yaml`) ; les règles des catégories sont à "
              "décider."},
    "md.policy": {
        "en": "AI policy: {name} ({origin}); who decides borderline cases: {who}. Rules: "
              "{rules}.",
        "fr": "Politique IA : {name} ({origin}) ; qui tranche les cas limites : {who}. "
              "Règles : {rules}."},
    "md.policy_who_none": {"en": "to be named", "fr": "à désigner"},
    "md.policy_borrowed": {
        "en": "default rules, borrowed from OS/Operations",
        "fr": "règles par défaut, empruntées à OS/Operations"},
    "md.policy_unnamed": {"en": "unnamed", "fr": "sans nom"},
    "md.to_classify": {"en": "to classify", "fr": "à classer"},
    "md.rule_to_decide": {"en": "rule to decide", "fr": "règle à décider"},
    "md.roles": {"en": "## Roles", "fr": "## Rôles"},
    "md.role_team": {
        "en": "- **Team**: {team} · **Departments**: {departments}",
        "fr": "- **Équipe** : {team} · **Départements** : {departments}"},
    "md.role_holders": {
        "en": "- **Holders**: {holders} · **Fallback**: {fallback}",
        "fr": "- **Titulaires** : {holders} · **Repli** : {fallback}"},
    "md.role_level": {
        "en": "- **Level reached**: {level} · **Conditions**: {criteria}",
        "fr": "- **Niveau atteint** : {level} · **Conditions** : {criteria}"},
    "md.role_tasks": {
        "en": "- **Active tasks**: {total} (A {A}, S {S}, C {C}, M {M}, J {J}) · coverage {coverage}",
        "fr": "- **Tâches actives** : {total} (A {A}, S {S}, C {C}, M {M}, J {J}) · couverture "
              "{coverage}"},
    "md.role_verdict": {"en": "- **Verdict**: {verdict}", "fr": "- **Verdict** : {verdict}"},
    "md.gaps": {"en": "**Gaps**", "fr": "**Manques**"},
    "md.routing": {"en": "**Routing**", "fr": "**Aiguillage**"},
    "md.routing_header": {
        "en": "| Incoming case | Handled by | Status |",
        "fr": "| Cas en entrée | Traité par | Statut |"},
    "md.proposed": {"en": " *(proposed)*", "fr": " *(proposé)*"},
    "md.processes": {"en": "**Processes**", "fr": "**Processus**"},
    "md.process": {
        "en": "- **{id} — {name}** · {state} · {automation}. Trigger: {trigger}. Steps: "
              "{steps}. Exit: {exit}.",
        "fr": "- **{id} — {name}** · {state} · {automation}. Déclencheur : {trigger}. "
              "Étapes : {steps}. Sortie : {exit}."},
    "md.handoff": {
        "en": " Hands over to {to}: {what}",
        "fr": " Passe la main à {to} : {what}"},
    "md.handoff_via": {"en": ", through {via}", "fr": ", par {via}"},
    "md.handoff_issues": {"en": "; what goes wrong: {issues}", "fr": " ; ce qui coince : {issues}"},
    "md.tasks": {"en": "**Tasks**", "fr": "**Tâches**"},
    "md.tasks_header": {
        "en": "| Id | Task | Type | Input → deliverable | Tools | Data | Status | Target | "
              "Relevance | State |",
        "fr": "| Id | Tâche | Type | Entrée → livrable | Outils | Données | Statut | Cible | "
              "Pertinence | État |"},
    "md.okrs_title": {
        "en": "## Objectives and key results (OKR)",
        "fr": "## Objectifs et résultats clés (OKR)"},
    "md.okrs_intro": {
        "en": "A task links to the KRs its deliverable moves (README_operations.md §1.13). "
              "Hours: what people would get back per month, tasks at their target.",
        "fr": "Une tâche se relie aux KR que son livrable fait bouger (README_operations.md "
              "§1.13). Heures : ce que les personnes récupéreraient par mois, tâches à leur "
              "cible."},
    "md.okrs_header": {
        "en": "| Objective | KR | Tasks | Automated | Hours/month |",
        "fr": "| Objectif | KR | Tâches | Automatisées | Heures/mois |"},
    "md.shared_kr": {"en": " (shared)", "fr": " (partagé)"},
    "md.unlinked": {
        "en": "Active tasks linked to no KR: {total}, by team: {teams}.",
        "fr": "Tâches actives reliées à aucun KR : {total}, par équipe : {teams}."},
    "md.library_title": {
        "en": "## Skills and agents by task type",
        "fr": "## Skills et agents par type de tâche"},
    "md.library_intro": {
        "en": "The skills and agents cited by active tasks, filed by the type of those tasks "
              "(README_operations.md §1.11), with the number of tasks that cite them.",
        "fr": "Les skills et les agents cités par les tâches actives, rangés par le type de "
              "ces tâches (§1.11 de README_operations.md), avec le nombre de tâches qui les "
              "citent."},
    "md.library_header": {
        "en": "| Task type | Skills and agents | Teams |",
        "fr": "| Type de tâche | Skills et agents | Équipes |"},
    "md.without_type": {"en": "without type", "fr": "sans type"},
    "html.organization": {"en": "the organization", "fr": "l'organisation"},
    "html.title": {"en": "AI mapping {org}", "fr": "Cartographie IA {org}"},
    "html.description": {
        "en": "The roles, processes and tasks of an organization, by team and by department, "
              "with what is automated, how relevant automating it is and the data sources of each "
              "task. Page generated by teamstarter-os/tools/build_rpt.py from "
              "teamstarter-os/OS/Operations/.",
        "fr": "Les rôles, processus et tâches d'une organisation, par équipe et par département, "
              "avec ce qui est automatisé, la pertinence de l'automatiser et les sources de "
              "données de chaque tâche. Page générée par teamstarter-os/tools/build_rpt.py depuis "
              "teamstarter-os/OS/Operations/.",
    },

    # --okrs
    "okrs.kr": {
        "en": "{kr}{shared}: {count} task(s), {automated} automated, {hours} h/month — {tasks}",
        "fr": "{kr}{shared} : {count} tâche(s), {automated} automatisée(s), {hours} h/mois — "
              "{tasks}"},
    "okrs.unlinked": {
        "en": "without KR, team {team}: {count} — {ids}",
        "fr": "sans KR, équipe {team} : {count} — {ids}"},

    # --stats
    "stats.types": {
        "en": "types: {typed} active tasks of {active} filed under a type, {used} types used of "
              "{catalogue}",
        "fr": "types : {typed} tâches actives sur {active} rangées dans un type, {used} types "
              "utilisés sur {catalogue}"},
    "stats.skills": {
        "en": "skills: {tools} skills and agents cited by active tasks, {types} types served, "
              "{several} serve several types",
        "fr": "skills : {tools} skills et agents cités par des tâches actives, {types} types "
              "servis, {several} servent plusieurs types"},
    "stats.team": {
        "en": "{team}: {roles} roles, {processes} active processes (+{proposed} proposed), "
              "{total} active tasks A {A} S {S} C {C} M {M} J {J}, coverage {coverage}",
        "fr": "{team}: {roles} rôles, {processes} processus actifs (+{proposed} proposés), "
              "{total} tâches actives A {A} S {S} C {C} M {M} J {J}, couverture {coverage}"},
    "stats.team_automated": {"en": " — automated team", "fr": " — équipe automatisée"},
    "stats.department": {
        "en": "  {department}: {total} tasks, coverage {coverage}",
        "fr": "  {department}: {total} tâches, couverture {coverage}"},
    "stats.since": {
        "en": "Since the snapshot (relevé) of {date}: {up} task(s) more automated, ≈ {hours} "
              "h/month less, {connectors} connector(s) activated, {added} task(s) added",
        "fr": "Depuis le relevé du {date} : {up} tâche(s) plus automatisée(s), ≈ {hours} "
              "h/mois en moins, {connectors} connecteur(s) activé(s), {added} tâche(s) "
              "ajoutée(s)"},

    # Command line.
    "cli.error": {"en": "ERROR  {message}", "fr": "ERREUR  {message}"},
    "cli.warning": {"en": "warning  {message}", "fr": "attention  {message}"},
    "cli.config_summary": {
        "en": "{errors} error(s) — {file}",
        "fr": "{errors} erreur(s) — {file}"},
    "cli.not_found": {"en": "{file}: not found", "fr": "{file} : introuvable"},
    "cli.config_yaml": {
        "en": "{file}: unreadable YAML ({error})",
        "fr": "{file} : YAML illisible ({error})"},
    "cli.formatted": {"en": "formatted: {files}", "fr": "formaté : {files}"},
    "cli.nothing_to_change": {"en": "nothing to change", "fr": "rien à changer"},
    "cli.observation_summary": {
        "en": "{errors} error(s), {warnings} warning(s) — {scope}",
        "fr": "{errors} erreur(s), {warnings} avertissement(s) — {scope}"},
    "cli.scope_referential": {"en": "against the referential", "fr": "contre le référentiel"},
    "cli.scope_form": {
        "en": "the form only (no referential here)",
        "fr": "forme seulement (pas de référentiel ici)"},
    "cli.blank_company": {
        "en": "--empty needs the organization's name: --company \"Acme\"",
        "fr": "--empty demande le nom de l'organisation : --company \"Acme\""},
    "cli.blank_drive": {
        "en": "--drive {url}: expected the link of a Drive folder (https://…)",
        "fr": "--drive {url} : un lien de dossier Drive est attendu (https://…)"},
    "cli.blank_written": {
        "en": "{file}: blank explorer of {org} written",
        "fr": "{file} : explorateur vierge de {org} écrit"},
    "cli.copy_first": {
        "en": "{file}: copy it first into {folder}/ of the referential, where it is checked and "
              "kept (README_operations.md §4.1)",
        "fr": "{file} : à copier d'abord dans {folder}/ du référentiel, où il est vérifié et "
              "gardé (README_operations.md §4.1)"},
    "cli.due_header": {
        "en": "{count} artifact(s) to regenerate on {today}",
        "fr": "{count} artefact(s) à régénérer le {today}"},
    "cli.due_line": {
        "en": "{id} {name} — cycle {cycle}, by {by}, skill {skill}, {url}",
        "fr": "{id} {name} — cycle {cycle}, par {by}, skill {skill}, {url}"},
    "cli.due_never": {
        "en": "never published (`updated` is missing)",
        "fr": "jamais publié (`updated` manque)"},
    "cli.due_cycle": {
        "en": "cycle {cycle}: last published {days} days ago",
        "fr": "cycle {cycle} : dernière publication il y a {days} jours"},
    "cli.due_inputs": {
        "en": "inputs changed since the last publication: {changed}",
        "fr": "entrées changées depuis la dernière publication : {changed}"},
    "cli.due_skill": {
        "en": "{tool} has a new version: {before} → {after}",
        "fr": "{tool} a une nouvelle version : {before} → {after}"},
    "cli.due_notify": {
        "en": "tell: {channel} {to} ({when})",
        "fr": "prévenir : {channel} {to} ({when})"},
    "cli.summary": {
        "en": "{errors} error(s), {warnings} warning(s)",
        "fr": "{errors} erreur(s), {warnings} avertissement(s)"},
    "cli.warnings_hint": {"en": " (--warnings to read them)", "fr": " (--warnings pour les lire)"},
    "cli.applied": {"en": "applied: {items}", "fr": "appliqué : {items}"},
    "cli.closed": {
        "en": "closed, already in the referential: {items}",
        "fr": "fermé, déjà dans le référentiel : {items}"},
    "cli.left": {"en": "left: {item}", "fr": "laissé : {item}"},
    "cli.placements_written": {
        "en": "observations written: {files}", "fr": "observations écrites : {files}"},
    "cli.placements_team": {
        "en": "{team}: {n} task(s) to place", "fr": "{team} : {n} tâche(s) à ranger"},
    "cli.placements_task": {
        "en": "  {task} {name} — {side}: « {text} »",
        "fr": "  {task} {name} — {side} : « {text} »"},
    "cli.placements_proposed": {
        "en": "    → proposed: {place} {url}", "fr": "    → proposé : {place} {url}"},
    "cli.placements_to_choose": {
        "en": "    → to choose: {place} {url}", "fr": "    → à choisir : {place} {url}"},
    "cli.placements_missing": {
        "en": "    → no folder in the tree for {data} in {tool}",
        "fr": "    → aucun dossier dans l'arbre pour {data} dans {tool}"},
    "cli.placements_folder": {
        "en": "Folder missing: {data} in {tool} — {tasks}",
        "fr": "Dossier manquant : {data} dans {tool} — {tasks}"},
    "cli.placements_unknown": {
        "en": "Link the data map does not have: {url} — {tasks}",
        "fr": "Lien absent de la carte des données : {url} — {tasks}"},
    "cli.placements_untasked": {
        "en": "Folder without a task ({status}): {place}{likely}",
        "fr": "Dossier sans tâche ({status}) : {place}{likely}"},
    "placements.skip": {"en": "{item} ({reason})", "fr": "{item} ({reason})"},
    "placements.bad_decision": {
        "en": "expected a side out or in, and a decision validated, elsewhere, no_file or "
              "private",
        "fr": "attendu un côté out ou in, et une décision validated, elsewhere, no_file ou "
              "private"},
    "placements.already": {
        "en": "the task's `{field}` already says where", "fr": "`{field}` de la tâche dit déjà où"},
    "placements.no_container": {
        "en": "{value} is not a container of the data map",
        "fr": "{value} n'est pas un contenant de la carte des données"},
    "placements.no_place": {
        "en": "neither a container nor a link (https://…)",
        "fr": "ni contenant ni lien (https://…)"},
    "placements.someone": {"en": "team", "fr": "équipe"},
    "placements.evidence": {
        "en": "Place {decision} by {by} on {date}, page « Files to place » of the RPT explorer.",
        "fr": "Emplacement {decision} par {by} le {date}, page « Fichiers à ranger » de "
              "l'explorateur RPT."},
    "placements.source": {
        "en": "RPT explorer, page « Files to place »",
        "fr": "explorateur RPT, page « Fichiers à ranger »"},
    "cli.datamap_same": {
        "en": "{id} {name} → updates {match}",
        "fr": "{id} {name} → met à jour {match}"},
    "cli.datamap_new": {
        "en": "{id} {name} → new container ({tool} · {path})",
        "fr": "{id} {name} → nouveau contenant ({tool} · {path})"},
    "cli.datamap_candidates": {
        "en": "    tasks that reach this data in this tool: {tasks}",
        "fr": "    tâches qui atteignent cette donnée dans cet outil : {tasks}"},
    "cli.datamap_unseen": {
        "en": "{id} {name} ({tool} · {path}) → not seen by the crawl, under a path it read",
        "fr": "{id} {name} ({tool} · {path}) → pas vu par le crawl, sous un chemin qu'il a lu"},
    "cli.stale": {
        "en": "Stale views: {files} — run build_rpt.py again without --check",
        "fr": "Vues périmées : {files} — relancer build_rpt.py sans --check"},

    # Small pieces.
    "fmt.percent": {"en": "{value}%", "fr": "{value} %"},
    "word.or": {"en": " or ", "fr": " ou "},
    "word.none": {"en": "none", "fr": "aucune"},
    "word.nothing": {"en": "nothing", "fr": "rien"},
    "word.content_email": {"en": "an e-mail address", "fr": "une adresse e-mail"},
    "word.content_phone": {"en": "a phone number", "fr": "un numéro de téléphone"},
    "word.content_amount": {"en": "an amount", "fr": "un montant"},
}
