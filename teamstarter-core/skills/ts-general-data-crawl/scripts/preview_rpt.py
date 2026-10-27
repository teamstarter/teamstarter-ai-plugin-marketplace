#!/usr/bin/env python3
"""Sending preview of an rpt/v1 map: everything that will be sent, and only that.

    python3 preview_rpt.py <map>.rpt.yaml [<other map>.rpt.yaml …] > apercu.md
    python3 preview_rpt.py <map>.rpt.yaml --lang fr > apercu.md   # labels in French (default:
                                    # RPT_LANG, else organization.language of rpt-config.yaml, else en)
    python3 preview_rpt.py <map>.rpt.yaml --config rpt-config.yaml > apercu.md
                                    # the organization's configuration (default: RPT_CONFIG)
    python3 preview_rpt.py <map>.rpt.yaml --config rpt-config.yaml --destination "<where>"
                                    # where the maps really go, when it is not the intake of
                                    # the configuration (a folder that does not exist yet)

Writes in Markdown every field of every element of the file (nothing is summed up or left out),
the list of the people named, and the alerts of the check for personal or confidential data.
This check does not see everything: a family name alone, a first name missing from FIRST_NAMES,
a private subject described without the words of WORDS pass without an alert. Several files
(one map per hat) give a single preview, map after map. This text is used as is for the
artifact shown to the person before sending. Its labels are in the language of the run (the
organization's by default); the content of the map stays as written.
"""
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# In a packaged skill, rpt_i18n.py (and build_rpt.py) are next to this script; in the
# repository, they are in teamstarter-os/tools/.
REPO_TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "tools"))
for _folder in (REPO_TOOLS, HERE):
    if os.path.exists(os.path.join(_folder, "rpt_i18n.py")) and _folder not in sys.path:
        sys.path.insert(0, _folder)
import rpt_i18n  # noqa: E402
from rpt_i18n import t as tr  # noqa: E402


MESSAGES = {
    "preview.pyyaml_missing": {
        "en": "PyYAML is missing: run `pip install pyyaml`, then run this script again.",
        "fr": "PyYAML manque : lancer `pip install pyyaml`, puis relancer ce script."},
    # Where the maps go (the organization's rpt-config.yaml).
    "preview.the_org": {"en": "the organization", "fr": "l'organisation"},
    "preview.dest_drive": {"en": "the Drive folder `{folder}` of {org}",
                           "fr": "le dossier Drive `{folder}` de {org}"},
    "preview.dest_email": {"en": "an e-mail to {email}", "fr": "un e-mail à {email}"},
    "preview.dest_or": {"en": " (or ", "fr": " (ou "},
    "preview.dest_default": {"en": "the intake folder of {org}",
                             "fr": "le dossier de dépôt de {org}"},
    "preview.dest": {"en": "{where}{seen}, whether Claude or you make the drop",
                     "fr": "{where}{seen}, que le dépôt soit fait par Claude ou par toi"},
    # Sections.
    "preview.kind.roles": {"en": "Roles", "fr": "Rôles"},
    "preview.kind.processes": {"en": "Processes", "fr": "Processus"},
    "preview.kind.tasks": {"en": "Tasks", "fr": "Tâches"},
    "preview.kind.data_sources": {"en": "Data sources declared in the file",
                                  "fr": "Sources de données déclarées dans le fichier"},
    "preview.kind.tools": {"en": "Tools declared in the file",
                           "fr": "Outils déclarés dans le fichier"},
    "preview.kind.blockers": {"en": "Blockers", "fr": "Bloqueurs"},
    "preview.kind.people": {"en": "The person mapped", "fr": "La personne cartographiée"},
    "preview.kind.agents": {"en": "Recurring agents", "fr": "Agents récurrents"},
    "preview.mapped": {"en": "person mapped", "fr": "personne cartographiée"},
    # The blockers of the map: count by state, then those still open or being resolved.
    "preview.blockers_count": {
        "en": "{total} blocker(s): {states}.",
        "fr": "{total} bloqueur(s) : {states}."},
    "preview.blockers_current": {
        "en": "Still holding tasks back:", "fr": "Bloquent encore des tâches :"},
    "preview.blocker_item": {"en": "- {id} ({type}, {state}): {text} — {tasks}",
                             "fr": "- {id} ({type}, {state}) : {text} — {tasks}"},
    "preview.blockers_none_current": {"en": "None is still open.",
                                      "fr": "Aucun n'est encore ouvert."},
    "preview.title": {"en": "# Sending preview — {title}", "fr": "# Aperçu de l'envoi — {title}"},
    "preview.intro": {
        "en": "Here is **everything** that will be sent, and nothing else: neither the sources "
              "read nor the conversation. Destination: {destination}. Nothing leaves without "
              "your approval.",
        "fr": "Voici **tout** ce qui sera envoyé, et rien d'autre : ni les sources lues, ni la "
              "conversation. Destination : {destination}. Rien ne part sans ton accord."},
    "preview.file": {
        "en": "**File**: `{file}` · {roles} role(s), {processes} process(es), {tasks} task(s), "
              "{blockers} blocker(s), {sources} data source(s) and {tools} tool(s) declared",
        "fr": "**Fichier** : `{file}` · {roles} rôle(s), {processes} processus, {tasks} "
              "tâche(s), {blockers} bloqueur(s), {sources} source(s) de données et {tools} "
              "outil(s) déclaré(s)"},
    "preview.review_title": {"en": "## Check first", "fr": "## À vérifier en priorité"},
    "preview.people": {
        "en": "**People and roles named** as holders, doers or fallbacks (tools excepted). A "
              "first name or a name is allowed only there; everywhere else, the map gives the "
              "role.",
        "fr": "**Personnes et rôles cités** comme titulaires, exécutants ou replis (les outils "
              "exceptés). Un prénom ou un nom n'est admis que là ; partout ailleurs, la carte "
              "dit le rôle."},
    "preview.person": {"en": "- {name}: {places}", "fr": "- {name} : {places}"},
    "preview.check": {
        "en": "**Automatic check** (possible personal or confidential data):",
        "fr": "**Contrôle automatique** (données personnelles ou confidentielles possibles) :"},
    # An alert: a dash, where, the label, then the excerpt between quotes.
    "preview.alert": {"en": "- {where}: {label} — \"{excerpt}\"",
                      "fr": "- {where} : {label} — « {excerpt} »"},
    "preview.no_alert": {"en": "- No alert.", "fr": "- Aucune alerte."},
    "preview.header": {"en": "## Header", "fr": "## En-tête"},
    "preview.header_where": {"en": "header", "fr": "en-tête"},
    "preview.author": {"en": "author", "fr": "auteur"},
    "preview.several": {"en": "# Sending preview — {count} maps",
                        "fr": "# Aperçu de l'envoi — {count} cartes"},
    "preview.several_intro": {
        "en": "One map per hat: {names}. Each is shown in full below.",
        "fr": "Une carte par casquette : {names}. Chacune est montrée en entier ci-dessous."},
    # Fields and values.
    "preview.bullet": {"en": "- **{label}**: {value}", "fr": "- **{label}** : {value}"},
    "preview.bullet_head": {"en": "- **{label}**:", "fr": "- **{label}** :"},
    "preview.pair": {"en": "{label}: {value}", "fr": "{label} : {value}"},
    "preview.relevance": {"en": "{score} ({axes}; × {payback})",
                          "fr": "{score} ({axes} ; × {payback})"},
    "preview.yes": {"en": "yes", "fr": "oui"},
    "preview.no": {"en": "no", "fr": "non"},
    "preview.internal_only": {"en": "internal working data only",
                              "fr": "données de travail internes seulement"},
    # Alert labels.
    "preview.alert.email": {"en": "e-mail address", "fr": "adresse e-mail"},
    "preview.alert.phone": {"en": "phone number", "fr": "numéro de téléphone"},
    "preview.alert.address": {"en": "postal address", "fr": "adresse postale"},
    "preview.alert.zip": {"en": "postcode and town", "fr": "code postal et ville"},
    "preview.alert.amount": {"en": "amount", "fr": "montant"},
    "preview.alert.age": {"en": "age", "fr": "âge"},
    "preview.alert.word": {"en": "word to check ({label})", "fr": "mot à vérifier ({label})"},
    "preview.alert.health": {"en": "health or private life", "fr": "santé ou vie privée"},
    "preview.alert.hr": {"en": "HR", "fr": "RH"},
    "preview.alert.company": {"en": "company health", "fr": "santé de l'entreprise"},
    "preview.alert.name": {"en": "name outside the allowed fields",
                           "fr": "nom hors des champs admis"},
    "preview.alert.first_name": {"en": "possible first name outside the allowed fields",
                                 "fr": "prénom possible hors des champs admis"},
}
rpt_i18n.register(MESSAGES)


def setup_language(cli=None):
    """The language of the run: --lang, else RPT_LANG, else organization.language of the
    configuration (read by build_rpt), else English."""
    try:
        import build_rpt
        return build_rpt.setup_language(cli)
    except ImportError:  # no build_rpt or no PyYAML: the configuration cannot be read
        return rpt_i18n.set_language(rpt_i18n.resolve(cli))


def destination():
    """Where the maps go: --destination when the skill chose another place (RPT_DESTINATION),
    else the intake of the organization's configuration (the file of --config or RPT_CONFIG), in
    the current language."""
    if os.environ.get("RPT_DESTINATION"):
        return os.environ["RPT_DESTINATION"]
    intake, org = {}, tr("preview.the_org")
    try:
        import yaml
        with open(os.environ.get("RPT_CONFIG") or "", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        intake, org = cfg.get("intake") or {}, (cfg.get("organization") or {}).get("name") or org
    except (OSError, ImportError):
        pass
    where = [tr("preview.dest_drive", folder=intake["drive_folder"], org=org)
             if intake.get("drive_folder") else "",
             tr("preview.dest_email", email=intake["email"]) if intake.get("email") else ""]
    where = tr("preview.dest_or").join(w for w in where if w) + (")" if all(where) else "")
    seen = f", {intake['visibility']}" if intake.get("visibility") else ""
    return tr("preview.dest", where=where or tr("preview.dest_default", org=org), seen=seen)


def __getattr__(name):
    """DESTINATION is computed when read, in the language of the run."""
    if name == "DESTINATION":
        return destination()
    raise AttributeError(name)


KINDS = ("roles", "processes", "tasks", "data_sources", "tools")
# Written once, at the top level of the person's first map (format §12): sent too, so shown too.
EXTRA_KINDS = ("people", "agents")
# The blockers of the map (references/format-rpt-v1.md §11): shown after the tasks they hold back.
BLOCKER_STATES = ("open", "in_progress", "resolved", "dropped")
NAME_FIELDS = ("holders", "by", "fallback")
CATALOGUE = os.path.normpath(os.path.join(HERE, "..", "references", "tools.yaml"))
# The label of each field, by language.
LABELS = {
    "name": {"en": "name", "fr": "nom"},
    "title": {"en": "title", "fr": "titre"},
    "organization": {"en": "organization", "fr": "organisation"},
    "team": {"en": "team", "fr": "équipe"},
    "authors": {"en": "authors", "fr": "auteurs"},
    "updated": {"en": "date", "fr": "date"},
    "detector": {"en": "produced by", "fr": "produit par"},
    "sources": {"en": "sources", "fr": "sources"},
    "notes": {"en": "notes", "fr": "notes"},
    "role": {"en": "role", "fr": "rôle"},
    "departments": {"en": "departments", "fr": "départements"},
    "state": {"en": "state", "fr": "état"},
    "mission": {"en": "mission", "fr": "mission"},
    "holders": {"en": "holders", "fr": "titulaires"},
    "fallback": {"en": "human fallback", "fr": "repli humain"},
    "entries": {"en": "entries", "fr": "entrées"},
    "routing": {"en": "routing", "fr": "aiguillage"},
    "gates": {"en": "human gates", "fr": "portes humaines"},
    "supervision": {"en": "supervision", "fr": "supervision"},
    "criteria": {"en": "conditions", "fr": "conditions"},
    "level": {"en": "level", "fr": "niveau"},
    "verdict": {"en": "verdict", "fr": "verdict"},
    "gaps": {"en": "gaps", "fr": "manques"},
    "aliases": {"en": "former ids", "fr": "anciens identifiants"},
    "trigger": {"en": "trigger", "fr": "déclencheur"},
    "steps": {"en": "steps", "fr": "étapes"},
    "exit": {"en": "exit proof", "fr": "preuve de sortie"},
    "fixed_path": {"en": "fixed path", "fr": "chemin fixe"},
    "blockers": {"en": "blockers", "fr": "blocages"},
    "automation": {"en": "automation", "fr": "automatisation"},
    "tools": {"en": "tools", "fr": "outils"},
    "next": {"en": "next processes", "fr": "processus suivants"},
    "replaced_by": {"en": "replaced by", "fr": "remplacé par"},
    "input": {"en": "input", "fr": "entrée"},
    "output": {"en": "deliverable", "fr": "livrable"},
    "by": {"en": "done by", "fr": "fait par"},
    "status": {"en": "status", "fr": "statut"},
    "target": {"en": "target", "fr": "cible"},
    "blocker": {"en": "what is missing", "fr": "ce qui manque"},
    "blocker_type": {"en": "type of what is missing", "fr": "type de ce qui manque"},
    "build": {"en": "cost to automate", "fr": "coût pour automatiser"},
    "measure": {"en": "measure", "fr": "mesure"},
    "stakes": {"en": "stakes", "fr": "enjeu"},
    "minutes": {"en": "minutes", "fr": "minutes"},
    "runs": {"en": "times per month", "fr": "fois par mois"},
    "basis": {"en": "origin", "fr": "origine"},
    "text": {"en": "text", "fr": "texte"},
    "size": {"en": "size", "fr": "taille"},
    "kind": {"en": "form", "fr": "forme"},
    "frequency": {"en": "frequency", "fr": "fréquence"},
    "what": {"en": "what", "fr": "quoi"},
    "from": {"en": "from", "fr": "de"},
    "volume": {"en": "volume", "fr": "volume"},
    "case": {"en": "case", "fr": "cas"},
    "to": {"en": "handled by", "fr": "traité par"},
    "type": {"en": "type", "fr": "type"},
    "entry": {"en": "automatic entry", "fr": "entrée automatique"},
    "key_tasks": {"en": "key tasks", "fr": "tâches clés"},
    "where": {"en": "where", "fr": "où"},
    "description": {"en": "description", "fr": "description"},
    "relevance": {"en": "relevance", "fr": "pertinence"},
    "reach": {"en": "reach", "fr": "portée"},
    "effort": {"en": "effort", "fr": "effort"},
    "describability": {"en": "describability", "fr": "descriptabilité"},
    "payback": {"en": "payback", "fr": "retour sur investissement"},
    "data": {"en": "data", "fr": "données"},
    "tool": {"en": "tool", "fr": "outil"},
    "connector": {"en": "AI access", "fr": "accès de l'IA"},
    "sensitivity": {"en": "sensitivity", "fr": "sensibilité"},
    "handoffs": {"en": "handoffs", "fr": "passages de main"},
    "via": {"en": "through", "fr": "par"},
    "issues": {"en": "what goes wrong", "fr": "ce qui coince"},
    "method": {"en": "written method", "fr": "méthode écrite"},
    "okrs": {"en": "key results", "fr": "résultats clés"},
    "output_files": {"en": "where the deliverable goes", "fr": "où va le livrable"},
    "input_files": {"en": "where the files it reads are", "fr": "où sont les fichiers lus"},
    "templates": {"en": "templates", "fr": "modèles"},
    "tasks": {"en": "tasks held back", "fr": "tâches bloquées"},
    "opened": {"en": "first seen on", "fr": "vu la première fois le"},
    "resolved": {"en": "closed on", "fr": "levé le"},
    "resolution": {"en": "what lifted it", "fr": "ce qui l'a levé"},
    "owner": {"en": "who can lift it", "fr": "qui peut le lever"},
    "source": {"en": "found in", "fr": "trouvé dans"},
    "evidence": {"en": "where and when", "fr": "où et quand"},
}
RELEVANCE_AXES = ("reach", "frequency", "effort", "describability", "payback")
PATTERNS = (
    # The domain ends with letters: « skill@2.5 » (meta.detector) is not an address.
    ("preview.alert.email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b")),
    ("preview.alert.phone", re.compile(
        r"(?<![\w.])(?:\+\d{2,3}[\s.]?(?:\(0\)[\s.]?)?[1-9]|0[1-9])(?:[\s.-]?\d{2}){4}(?!\w)")),
    ("preview.alert.address", re.compile(r"\b\d{1,4}(?:\s?(?:bis|ter))?,?\s+(?:rue|avenue|av\.|"
                                         r"boulevard|bd|place|chemin|allée|impasse|quai|route)\b",
                                         re.IGNORECASE)),
    # An English street address: « 12 Baker Street », « 5 Elm Rd. » (case kept: « 3 Google
    # Drive » or « 2 dossiers » are not addresses).
    ("preview.alert.address", re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s+"
                                         r"(?:Street|St\.|Road|Rd\.|Avenue|Ave\.|Lane|"
                                         r"Boulevard)(?!\w)")),
    ("preview.alert.zip", re.compile(r"\b\d{5}\s+[A-ZÉÈ][a-zéèêëàâîïôöûüç-]+")),
    ("preview.alert.amount", re.compile(
        r"\d[\d\s.,]*\s?(?:€|k€|K€|M€|euros?\b|EUR\b|USD\b|GBP\b|dollars?\b)|[$£]\s?\d[\d,.]*\d|[$£]\s?\d")),
    ("preview.alert.age", re.compile(r"\b\d{2}\s?(?:ans|years? old)\b")),
)
# Word beginnings (regular expressions), in French and in English, to have reviewed: they often
# signal private, HR or financial content, sometimes a plain activity. Matched on lower case.
WORDS = {
    "preview.alert.health": [
        # French
        "maladie", "malade", "médecin", "médical", "thérap", "kiné", "ostéopath", "psycholog",
        "psychiatr", "dentist", "hôpita", "enceinte", "grossesse", "handicap", "hospitalis",
        "blessure", "décès", "deuil", "domicile", "né le", "née le", "sexe", "marié", "divorc",
        "vacances",
        # English
        "health", "illness", "sick", "doctor", "medical", "therap", "physio", "hospital",
        "pregnan", "disabilit", "injur", "death", "bereave", "funeral", "home address",
        "born on", "date of birth", "married", "spouse", "vacation"],
    "preview.alert.hr": [
        # French
        "salaire", "rémunération", "commission", "prime", "licenci", "rupture conventionnelle",
        "démission", "sanction", "disciplinaire", "harcèlement", r"prud.?hom",
        r"conflit (?:avec|entre)", "fâch", "entretien annuel", "évaluation individuelle",
        "revue de performance", "arrêt de travail", "congé mat", "congé pat", "mutuelle",
        # English
        "salary", "salaries", "pay rise", "compensation", "bonus", "layoff", "laid off",
        "dismiss", "fired", "resign", "disciplinary", "harass", "lawsuit", "tribunal",
        r"conflict (?:with|between)", "annual review", "performance review",
        "individual evaluation", "sick leave", "maternity leave", "paternity leave",
        "health insurance"],
    "preview.alert.company": [
        # French
        r"santé (?:de l'entreprise|financière)", "trésorerie", "runway", "levée de fonds",
        "valorisation", "endettement", r"dettes? (?:financières?|bancaires?)", "emprunt",
        "faillite", "redressement", "plan social", "confidentiel", "chiffre d'affaires",
        # English
        "cash flow", "cash position", "fundrais", "valuation", "debt", "bank loan", "bankrupt",
        "insolven", "receivership", "redundanc", "confidential", "revenue"],
}
# Common first names: written outside the fields for names, they often designate a third party
# (an employee, a client, a candidate) whose name must not be sent.
FIRST_NAMES = """
Adam Adèle Adrien Agathe Agnès Aïcha Alain Alban Albert Alexandra Alexandre Alexis Alice Aline
Alix Amandine Amélie Anaïs Andréa André Anne Annie Anthony Antoine Antonin Arnaud Arthur Audrey
Augustin Aurélie Aurélien Axel Aymeric Baptiste Barbara Basile Bastien Béatrice Benjamin Benoît
Bernard Bertrand Blandine Brigitte Bruno Camille Capucine Carine Carole Caroline Catherine Cécile
Cédric Céline Chantal Charles Charlotte Chloé Christelle Christian Christine Christophe Claire
Clara Clarisse Claudine Clémence Clément Coralie Corentin Corinne Cyril Cyrille Damien Daniel
Daphné David Delphine Denis Diane Didier Dominique Dorian Dylan Edouard Édouard Élisa Élise Élodie
Éloïse Emma Emmanuel Emmanuelle Émile Émilie Enzo Éric Estelle Étienne Eugénie Eva Évelyne Fabien
Fabienne Fabrice Fanny Farid Fatima Félix Fernand Flavie Florence Florent Florian Francis Franck
François Françoise Frédéric Frédérique Gabriel Gabrielle Gaël Gaëlle Gaétan Gaspard Geneviève
Georges Gérald Gérard Géraldine Ghislain Gilbert Gilles Grégoire Grégory Guillaume Gustave Guy
Hélène Henri Hervé Hugo Hugues Inès Irène Isabelle Jacqueline Jacques Jean Jeanne Jérémie Jérémy
Jérôme Joël Johan Jonathan Joseph Josiane Julia Julie Julien Juliette Justine Karim Karine Kevin
Laetitia Laura Laure Laurence Laurent Léa Léna Léo Léon Léonie Lina Lionel Lisa Loïc Louis Louise
Luc Lucas Lucie Ludovic Lydie Madeleine Maël Maëlle Magali Manon Marc Marcel Margaux Margot
Marianne Marie Marine Marion Martin Martine Mathéo Mathias Mathieu Mathilde Mathis Matthieu Maxime
Mélanie Mélissa Michel Michèle Mickaël Mohamed Monique Morgane Muriel Myriam Nadia Nadine Nathalie
Nathan Nicolas Nicole Noah Noé Noémie Océane Olivia Olivier Pascal Pascale Patricia Patrick Paul
Pauline Philippe Pierre Quentin Rachel Rachid Raphaël Raphaëlle Rémi Rémy Renaud René Richard
Robert Robin Romain Romane Rudy Sabine Sabrina Salomé Samia Samuel Sandra Sandrine Sarah Sébastien
Serge Simon Simone Solène Sonia Sophie Stéphane Stéphanie Sylvain Sylvie Tanguy Théo Théophile
Thibault Thibaut Thierry Thomas Timothée Tristan Valentin Valentine Valérie Vanessa Véronique
Victor Vincent Virginie Xavier Yann Yannick Yasmine Yves Yvonne Zoé
""".split()
FIRST_NAME = re.compile(r"(?<![\w-])((?:" + "|".join(sorted(FIRST_NAMES, key=len, reverse=True))
                        + r")(?:-[A-ZÉÈ][\w'’]+)?(?: [A-ZÉÈ][\w'’-]+)?)(?![\w-])")


def label_of(key):
    """The label of a field in the current language; the key itself when it has none."""
    texts = LABELS.get(str(key))
    if texts is None:
        return key
    return texts.get(rpt_i18n.language()) or texts[rpt_i18n.LANGUAGES[0]]


def fmt(value):
    if value is None:
        return "?"
    if isinstance(value, bool):
        return tr("preview.yes") if value else tr("preview.no")
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return " ; ".join(fmt(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(tr("preview.pair", label=label_of(k),
                            value=rpt_i18n.label("connector", v) if k == "connector" else fmt(v))
                         for k, v in value.items())
    return rpt_i18n.label("basis", value) if isinstance(value, str) else str(value)


def relevance_text(value):
    """"24/36 (reach: 1, frequency: 3, effort: 1, describability: 3; × payback: 3)"; "?" when no
    axis of the sum is estimated. The score is (reach + frequency + effort + describability) ×
    payback; an unknown payback counts 1."""
    notes = [(label_of(a), value.get(a)) for a in RELEVANCE_AXES]
    known = [v if isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 3 else None
             for _, v in notes]
    base = sum(v or 0 for v in known[:-1])
    score = f"{base * (known[-1] or 1)}/{3 * (len(RELEVANCE_AXES) - 1) * 3}" if base else "?"
    parts = [tr("preview.pair", label=label, value=fmt(v)) for label, v in notes]
    return tr("preview.relevance", score=score, axes=", ".join(parts[:-1]), payback=parts[-1])


def bullet(key, value):
    label = label_of(key)
    if key == "relevance" and isinstance(value, dict):
        return [tr("preview.bullet", label=label, value=relevance_text(value))]
    if key == "sensitivity" and isinstance(value, list):
        return [tr("preview.bullet", label=label,
                   value=", ".join(rpt_i18n.label("sensitivity", v, default=str(v))
                                   for v in value) or tr("preview.internal_only"))]
    if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        return [tr("preview.bullet_head", label=label)] + [f"  - {fmt(v)}" for v in value]
    return [tr("preview.bullet", label=label, value=fmt(value))]


def texts(data):
    """(where, field, text) for each text value of the file."""
    out = []

    def walk(value, where, key):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, f"{where} · {label_of(k)}", str(k))
        elif isinstance(value, list):
            for v in value:
                walk(v, where, key)
        elif isinstance(value, str):
            out.append((where, key, value))

    walk(data.get("meta") or {}, tr("preview.header_where"), "meta")
    for kind in KINDS + ("blockers",):
        for item in data.get(kind) or []:
            walk({k: v for k, v in item.items() if k != "id"}, str(item.get("id")), kind)
    return out


def person_names(data):
    """The values of the fields for names that look like a first name or a proper name."""
    return [n for n in people(data)
            if re.fullmatch(r"[A-ZÉÈÀÂÎÔ][\w'’-]+(?: [A-ZÉÈÀÂÎÔ][\w'’-]+)*", n)
            and not n.isupper()]


def alerts(data):
    """What looks like personal or confidential data: (where, what, excerpt), the label in the
    current language."""
    found, names, tools = [], person_names(data), tool_names(data)
    for where, key, text in texts(data):
        for label, pattern in PATTERNS:
            found += [(where, tr(label), m.group(0).strip()) for m in pattern.finditer(text)]
        low = text.lower()
        for label, words in WORDS.items():
            found += [(where, tr("preview.alert.word", label=tr(label)), m.group(0))
                      for w in words for m in [re.search(r"\b" + w, low)] if m]
        if key in NAME_FIELDS + ("authors",):
            continue
        known = [n for n in names if re.search(r"\b" + re.escape(n) + r"\b", text)]
        found += [(where, tr("preview.alert.name"), n) for n in known]
        found += [(where, tr("preview.alert.first_name"), m.group(1))
                  for m in FIRST_NAME.finditer(text)
                  if m.group(1).split()[0] not in " ".join(known).split()
                  and m.group(1).lower() not in tools]
    return found


def tool_names(data):
    """Names and ids of the tools, in lower case: those of the file and those of the catalogue."""
    tools = list(data.get("tools") or [])
    if os.path.exists(CATALOGUE):
        import yaml
        with open(CATALOGUE, encoding="utf-8") as f:
            tools += (yaml.safe_load(f) or {}).get("tools") or []
    names = {"claude"}
    for t in tools:
        tid, name = str(t.get("id", "")).lower(), str(t.get("name", "")).lower()
        names |= {tid, tid.split(":")[-1], name, name.split(" (")[0]}
    return names


def people(data):
    """Each person or role of the fields where a name is allowed (tools excepted), and where."""
    tools, seen = tool_names(data), {}
    for author in (data.get("meta") or {}).get("authors") or []:
        if str(author).lower() not in tools:
            seen.setdefault(str(author), []).append(tr("preview.author"))
    for item in data.get("people") or []:
        if isinstance(item, dict) and item.get("name"):
            seen.setdefault(str(item["name"]), []).append(tr("preview.mapped"))
    for kind in ("roles", "processes", "tasks"):
        for item in data.get(kind) or []:
            for field in NAME_FIELDS:
                values = item.get(field)
                for v in values if isinstance(values, list) else [values] if values else []:
                    if str(v).lower() not in tools:
                        seen.setdefault(str(v), []).append(f"{item.get('id')} ({label_of(field)})")
    return seen


def header(path, data):
    meta = data.get("meta") or {}
    n = {kind: len(data.get(kind) or []) for kind in KINDS}
    return [tr("preview.title", title=meta.get("title") or os.path.basename(path)), "",
            tr("preview.intro", destination=destination()), "",
            tr("preview.file", file=os.path.basename(path), roles=n["roles"],
               processes=n["processes"], tasks=n["tasks"],
               blockers=len(data.get("blockers") or []), sources=n["data_sources"],
               tools=n["tools"]), ""]


def review(data):
    lines = [tr("preview.review_title"), "", tr("preview.people"), ""]
    lines += [tr("preview.person", name=name, places=", ".join(places))
              for name, places in people(data).items()]
    lines += ["", tr("preview.check"), ""]
    found = alerts(data)
    lines += [tr("preview.alert", where=where, label=label, excerpt=excerpt)
              for where, label, excerpt in found]
    return lines + ([] if found else [tr("preview.no_alert")]) + [""]


def render(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    lines = header(path, data) + review(data) + [tr("preview.header"), ""]
    for key, value in (data.get("meta") or {}).items():
        lines += bullet(key, value)
    for kind in KINDS:
        if data.get(kind):
            lines += ["", f"## {tr('preview.kind.' + kind)}"]
        for item in data.get(kind) or []:
            lines += ["", f"### {item.get('id')} — {item.get('name', '')}", ""]
            for key, value in item.items():
                if key not in ("id", "name") and value not in (None, "", []):
                    lines += bullet(key, value)
        if kind == "tasks":
            lines += blockers(data.get("blockers") or [])
    for kind in EXTRA_KINDS:
        items = [x for x in data.get(kind) or [] if isinstance(x, dict)]
        if items:
            lines += ["", f"## {tr('preview.kind.' + kind)}"]
        for item in items:
            lines += ["", f"### {item.get('id')} — {item.get('name', '')}", ""]
            for key, value in item.items():
                if key not in ("id", "name") and value not in (None, "", []):
                    lines += bullet(key, value)
    return "\n".join(lines).rstrip() + "\n"


def blocker_label(table, code):
    """The label of a blocker's type or state; the code itself when it has none."""
    return rpt_i18n.label(table, code, default=str(code)) if isinstance(code, str) else fmt(code)


def blockers(items):
    """The blockers of the map: the count by state, those still open or being resolved, then
    each one in full (everything that will be sent)."""
    if not items:
        return []
    states = [b.get("state") for b in items]
    counts = ", ".join(f"{blocker_label('blocker_state', s)} {states.count(s)}"
                       for s in BLOCKER_STATES if states.count(s))
    lines = ["", f"## {tr('preview.kind.blockers')}", "",
             tr("preview.blockers_count", total=len(items), states=counts), ""]
    current = [b for b in items if b.get("state") in ("open", "in_progress")]
    lines += [tr("preview.blockers_current")] if current else [tr("preview.blockers_none_current")]
    lines += [tr("preview.blocker_item", id=b.get("id"),
                 type=blocker_label("blocker_type", b.get("type")),
                 state=blocker_label("blocker_state", b.get("state")), text=fmt(b.get("text")),
                 tasks=fmt(b.get("tasks"))) for b in current]
    for b in items:
        lines += ["", f"### {b.get('id')} — {fmt(b.get('text'))}", ""]
        for key, value in b.items():
            if key in ("id", "text") or value in (None, "", []):
                continue
            if key in ("type", "state"):
                table = "blocker_type" if key == "type" else "blocker_state"
                lines.append(tr("preview.bullet", label=label_of(key),
                                value=blocker_label(table, value)))
            else:
                lines += bullet(key, value)
    return lines


def render_all(paths):
    """One file: its preview. Several (one map per hat): the list, then each preview in full,
    its headings one level down."""
    if len(paths) == 1:
        return render(paths[0])
    names = ", ".join(f"`{os.path.basename(p)}`" for p in paths)
    lines = [tr("preview.several", count=len(paths)), "",
             tr("preview.several_intro", names=names), ""]
    for path in paths:
        lines += ["---", "", re.sub(r"^(#+) ", r"#\1 ", render(path), flags=re.M)]
    return "\n".join(lines).rstrip() + "\n"


def split_option(argv, name):
    """The value of `--<name>` (or `--<name>=x`), and the other arguments."""
    value, rest, it = None, [], iter(argv)
    for arg in it:
        if arg == f"--{name}":
            value = next(it, None)
        elif arg.startswith(f"--{name}="):
            value = arg.split("=", 1)[1]
        else:
            rest.append(arg)
    return value, rest


def split_lang(argv):
    """The value of `--lang` (or `--lang=xx`), and the other arguments."""
    return split_option(argv, "lang")


def use_config(argv):
    """Take `--config <file>`: the organization's configuration, for this run and the scripts
    it calls (RPT_CONFIG). Returns the other arguments."""
    config, rest = split_option(argv, "config")
    if config:
        os.environ["RPT_CONFIG"] = os.path.abspath(config)
    return rest


def main(argv):
    dest, argv = split_option(argv, "destination")
    if dest:
        os.environ["RPT_DESTINATION"] = dest
    lang, argv = split_lang(use_config(argv))
    setup_language(lang)
    paths = [a for a in argv if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return 2
    try:
        sys.stdout.write(render_all(paths))
    except ImportError:
        print(tr("preview.pyyaml_missing"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
