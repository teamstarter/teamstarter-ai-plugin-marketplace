#!/usr/bin/env python3
"""Validate the RPT referential (roles, processes, tasks) and generate its views.

The referential is every `*.yaml` file of a folder whose `format` is `rpt/v1`
(default: teamstarter-os/OS/Operations/). Rules: OS/Operations/README_operations.md.

    python3 teamstarter-os/tools/build_rpt.py            # validate, write referentiel.md, rpt-explorer.html,
                                                         # the snapshot (relevé) of the day, releves/<date>.json,
                                                         # and the table of changes, releves/changements.json
    python3 teamstarter-os/tools/build_rpt.py --check    # validate, fail if a generated file is stale
    python3 teamstarter-os/tools/build_rpt.py --format   # rewrite the YAML files in canonical style
    python3 teamstarter-os/tools/build_rpt.py --stats    # print coverage per team and department
    python3 teamstarter-os/tools/build_rpt.py --dir <folder|file> --validate-only   # any rpt/v1 referential
    python3 teamstarter-os/tools/build_rpt.py --lang en  # messages in English (default: RPT_LANG, else
                                                         # organization.language of rpt-config.yaml)

A folder or file other than OS/Operations borrows the departments, task types, tools and data
sources it does not declare from OS/Operations, or from the folder given by --catalogues (the skill
ts-general-check-process-cartography ships this script with the generic departments and common
data types only; it reads the organization's catalogues at each use, from the rpt-config.yaml
whose address the organization's instructions give, and its validate_rpt.py passes them with
--catalogues). The views of such a folder show only the borrowed entries its maps cite; a
referential of another organization never borrows Teamstarter's AI policy.

Configuration. The views of --dir are built with its organization's rpt-config.yaml (the
organization's name, its intake, its global context): --config FILE, else the environment
variable RPT_CONFIG, else rpt-config.yaml in --dir or one of its two parents (an OS keeps it at
its root, next to OS/Operations/). A folder without one is built without a configuration, never
with Teamstarter's.

Languages. The messages a person reads come from rpt_i18n.py (shipped next to this script), in
the language of the run: --lang, else the environment variable RPT_LANG, else
`organization.language` of rpt-config.yaml, else English. The generated views (referentiel.md,
the explorer) are written in the organization's language, whatever the language of the run, so
that --check gives the same answer to everyone. The texts of the catalogues (name, description,
examples, aliases of departments, task types and data sources) are maps by language code
(`name: {en: Sales, fr: Ventes}`) or plain texts, taken as they are for every language.

Exit code 1 when the referential has errors (or, with --check, a stale view).
"""
import argparse
import datetime
import glob
import html
import json
import math
import os
import re
import statistics
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rpt_i18n  # noqa: E402
from rpt_i18n import t as tr  # noqa: E402 (here `t` names a task)
DEFAULT_DIR = os.path.normpath(os.path.join(HERE, "..", "OS", "Operations"))
TEMPLATE = os.path.join(HERE, "rpt_explorer.template.html")
PROMPT = os.path.normpath(os.path.join(HERE, "..", "skills", "ts-general-rpt-map", "PROMPT.md"))
FORMAT = "rpt/v1"
LISTS = ("departments", "task_types", "tools", "data_sources", "okrs", "roles", "processes",
         "tasks", "blockers", "os_zones", "insights", "people", "agents", "products",
         "decisions", "artifacts", "containers")
KIND_OF_LIST = {"departments": "department", "task_types": "task_type", "tools": "tool",
                "data_sources": "data_source", "okrs": "okr",
                "roles": "role", "processes": "process", "tasks": "task",
                "blockers": "blocker", "os_zones": "os_zone", "insights": "insight",
                "people": "person", "agents": "agent", "products": "product",
                "decisions": "decision", "artifacts": "artifact", "containers": "container"}
# The referential's blocker register (README_operations.md §1.14).
BLOCKERS_FILE = "blockers.yaml"
# The structure of the company's OS and its insights (README_operations.md §1.15).
OS_STRUCTURE_FILE = "os-structure.yaml"
INSIGHTS_FILE = "insights.yaml"
# Who reaches the OS and how, and the agents that run recurring tasks (README_operations.md §1.16).
PEOPLE_FILE = "people.yaml"
AGENTS_FILE = "agents.yaml"
# The products, the business decisions and the artifacts of the OS (README_operations.md §1.17).
DECISIONS_FILE = "decisions.yaml"
ARTIFACTS_FILE = "artifacts.yaml"
# Where the data of the organization is, container by container, and who keeps it
# (README_operations.md §1.20).
DATA_MAP_FILE = "data-map.yaml"
# Catalogues a referential other than OS/Operations borrows (load, borrow).
CATALOGUES = (("departments", "departments.yaml"), ("task_types", "task-types.yaml"),
              ("tools", "tools.yaml"), ("data_sources", "data-sources.yaml"),
              ("okrs", "okrs.yaml"))

# Key order = canonical order written by --format. First keys are required.
KEYS = {
    "department": ["id", "name", "name_en", "description", "examples", "aliases"],
    # A task type (task-types.yaml, README_operations.md §1.11): a job another company would
    # name the same way. `department: null` = transverse.
    "task_type": ["id", "name", "name_en", "department", "description", "aliases"],
    # `rights`: what the AI may do in the tool through its connector, right by right, with the
    # state of each (README_operations.md §1.7); `rights_checked`: when they were last read.
    "tool": ["id", "name", "type", "where", "status", "description", "rights", "rights_checked",
             "shared", "aliases"],
    "data_source": ["id", "name", "description", "sensitivity", "tools", "basis", "notes",
                    "aliases", "sources", "os"],
    # An objective of the company and its key results (okrs.yaml, README_operations.md §1.13).
    # A task contributes to key results (`okrs`), not to an objective as a whole.
    "okr": ["id", "name", "level", "parent", "teams", "owner", "period", "state", "key_results",
            "shared_key_results", "basis", "notes", "aliases", "sources"],
    "role": ["id", "name", "team", "departments", "state", "mission", "holders", "fallback",
             "entries", "routing", "gates", "supervision", "criteria", "level", "verdict", "gaps",
             "basis", "notes", "aliases", "sources"],
    "process": ["id", "name", "role", "departments", "state", "replaced_by", "trigger", "steps",
                "gates", "exit", "fixed_path", "blockers", "automation", "tools", "next",
                "handoffs", "basis", "notes", "aliases", "sources"],
    "task": ["id", "name", "role", "departments", "type", "state", "replaced_by", "aliases",
             "job", "trigger",
             "input", "output", "output_files", "templates", "tools", "data", "okrs", "method",
             "by",
             "status", "target", "blocker",
             "blocker_type", "build", "frequency", "measure", "queue", "stakes", "relevance",
             "basis", "notes", "sources"],
    # A place where data is kept, in a tool (data-map.yaml, README_operations.md §1.20): a Drive
    # folder, a Notion database, a HubSpot object, a Slack channel, a Gmail label, a Jira
    # project. Its structure only, never its content: what one item is, how many, the names of
    # the columns or properties, the dates, the tasks that write and read it.
    "container": ["id", "name", "tool", "kind", "parent", "data", "path", "url", "holds",
                  "items", "formats", "naming", "fields", "freshness", "activity", "written_by",
                  "read_by", "owner", "sensitivity", "access", "state", "duplicate_of", "basis",
                  "notes", "sources"],
    # A problem that keeps tasks from moving towards their target (blockers.yaml,
    # README_operations.md §1.14). `basis` is one value here: how the problem is known.
    "blocker": ["id", "text", "type", "state", "tasks", "opened", "resolved", "resolution",
                "owner", "source", "basis", "evidence", "notes", "sources"],
    # A zone of the company's OS (os-structure.yaml, README_operations.md §1.15): a folder, what
    # it holds, who keeps it, and the flows that feed it (`feeds`).
    "os_zone": ["id", "name", "path", "parent", "holds", "description", "owner", "feeds",
                "basis", "notes", "sources"],
    # A question the OS answers, or a finding: facts said in different words, grouped into one
    # statement and counted (insights.yaml, README_operations.md §1.15).
    "insight": ["id", "kind", "text", "zone", "state", "count", "accounts", "first_seen",
                "last_seen", "file", "action", "owner", "tasks", "okrs", "basis", "evidence",
                "notes", "sources"],
    # A person of the organization, first and last name, and the ways their AI reaches the OS
    # (people.yaml, README_operations.md §1.16).
    "person": ["id", "name", "aliases", "os_access", "ai_plan", "maps", "notes", "sources"],
    # An agent that runs recurring tasks without being launched by hand: a managed agent, a
    # Routine, a scheduled task of a person's Claude, a worker (agents.yaml, §1.16).
    "agent": ["id", "name", "kind", "platform", "state", "stage", "schedule", "owner", "people",
              "tasks", "skills", "data", "zones", "cost", "config", "log", "notify", "basis",
              "notes", "sources"],
    # What the business decisions activate (decisions.yaml, README_operations.md §1.17).
    "product": ["id", "name", "url", "tool", "notes", "sources"],
    # A choice made by the company to create value, from facts and other decisions (§1.17).
    "decision": ["id", "name", "kind", "zone", "path", "state", "date", "decided_by",
                 "depends_on", "decided_through", "activates", "basis", "notes", "sources"],
    # The output of a process, made to understand, share or help decide (§1.17).
    "artifact": ["id", "name", "url", "path", "zone", "produced_by", "depends_on", "purpose",
                 "state", "updated", "basis", "notes", "sources"],
}
REQUIRED = {"department": {"id", "name"}, "task_type": {"id", "name", "department"},
            "tool": {"id", "name", "type", "status"},
            "data_source": {"id", "name"},
            "okr": {"id", "name", "level"},
            "role": {"id", "name", "team", "departments", "mission"},
            "process": {"id", "name", "role", "state", "steps"},
            "task": {"id", "name", "role", "state", "status"},
            "blocker": {"id", "text", "type", "state", "tasks", "opened"},
            "os_zone": {"id", "name"},
            "insight": {"id", "kind", "text", "zone", "state"},
            "person": {"id", "name"},
            "agent": {"id", "name", "kind", "state"},
            "product": {"id", "name"},
            "decision": {"id", "name", "kind", "state"},
            "artifact": {"id", "name", "purpose"},
            "container": {"id", "name", "tool", "kind", "data"}}
# `detector`: the skill that produced a map and its version (README_operations.md §4.2, deltas).
META_KEYS = ["title", "organization", "team", "authors", "updated", "detector", "sources", "notes"]
# Lists of texts or ids. Between [...], an unquoted " : " turns an element into a mapping
# without any parse error (`[Sources écartées : messagerie]`): check_keys reports it.
TEXT_LISTS = ("departments", "holders", "gates", "gaps", "aliases", "sources", "steps", "tools",
              "next", "by", "authors", "examples", "data", "sensitivity", "okrs", "teams",
              "shared_key_results", "tasks", "people", "skills", "zones", "formats", "fields",
              "written_by", "read_by")
# The texts of a catalogue entry (departments, task types, data sources) that exist in several
# languages: a map by language code, or a plain text (or list) taken as it is for every language.
# `name_en` is retired (its value is `name.en`), still accepted.
LOCALIZED_TEXTS = ("name", "name_en", "description")
LOCALIZED_LISTS = ("examples", "aliases")
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}$")
SUB_KEYS = {"entries": ["what", "from", "trigger", "volume"],
            "handoffs": ["to", "what", "via", "issues"],
            "routing": ["case", "to", "status", "state"],
            "trigger": ["what", "type", "by", "volume"],
            "criteria": ["entry", "routing", "key_tasks", "fallback", "supervision"],
            "relevance": ["reach", "frequency", "effort", "describability", "payback"],
            # Measured duration and rate of a task, what is at stake when it is late or wrong,
            # the cost to automate it (README_operations.md §1.6).
            "measure": ["minutes", "runs", "basis"],
            # The stock waiting at the input of a task at a date (README_operations.md §1.19).
            "queue": ["count", "unit", "at", "basis", "source"],
            "stakes": ["level", "text"],
            # The structure of a container of the data map (README_operations.md §1.20): how
            # many items, when it last changed, how many people edit it, how the AI reaches it.
            "items": ["count", "unit", "approx"],
            "freshness": ["last_modified", "modified_90d", "checked"],
            "activity": ["editors_90d", "viewers_90d"],
            "access": ["connector", "state"],
            "build": ["size", "kind"],
            # What a task is for (README_operations.md §3.1): « When <when>, I want <name>, so
            # that <so_that>. »
            "job": ["when", "so_that"],
            # A right of the AI in a tool (README_operations.md §1.7): an action on an object,
            # enabled here, offered by the connector but not enabled, or not offered at all.
            "rights": ["action", "what", "state", "via", "basis", "notes"],
            # A flow that feeds a zone of the OS (README_operations.md §1.15): from a data source
            # (through one of its tools) or from another zone, by a skill or by hand, in place or
            # only possible, and the insights it feeds.
            "feeds": ["from", "tool", "skill", "what", "state", "cadence", "insights", "basis",
                      "notes"],
            # A way the AI of a person reaches the OS (README_operations.md §1.16).
            "os_access": ["mode", "tool", "state", "checked", "basis", "evidence", "notes"],
            # The AI licence of a person (README_operations.md §1.18): its tool, its plan, its
            # tier and the modes it gives.
            "ai_plan": ["tool", "plan", "tier", "modes", "checked", "basis", "evidence", "notes"],
            # What a run of an agent costs (README_operations.md §1.16): measured (`per_run`, the
            # `list_cost` of a session) or estimated from its tokens, searches and runtime.
            "cost": ["billing", "per_run", "model", "tokens_in", "tokens_out", "web_searches",
                     "minutes", "runs", "currency", "measured", "basis", "notes"],
            # The stage an agent reached (README_operations.md §1.16): functional, efficient,
            # refined; what proves the criteria no file can show.
            "stage": ["level", "checked", "basis", "evidence"],
            # Who an agent tells, how and when (README_operations.md §1.16).
            "notify": ["channel", "to", "when", "notes"],
            # The tools of a data source: where the data is, how the AI reaches it. The `tools`
            # of a task or a process are ids (texts): only the mappings are checked.
            "tools": ["tool", "where", "connector", "notes"],
            # Where the deliverable of a task goes: a fixed file updated at each run, or the
            # folder where each run's file goes, with its name pattern; the template files it
            # starts from (README_operations.md §1.12).
            "output_files": ["kind", "url", "pattern", "tool", "what"],
            "templates": ["url", "tool", "what"],
            # A key result of an objective (okrs.yaml, README_operations.md §1.13): what is
            # measured, in which unit, the threshold (`direction` min: at least, max: at most),
            # the period it is counted over, where it is measured.
            "key_results": ["id", "name", "metric", "unit", "direction", "target", "per",
                            "baseline", "kind", "data", "notes"]}
# Relevance of a task (README_operations.md §1.6): five axes rated 1 to 3, or null. The score
# is the sum of the first four multiplied by the payback, (P + F + E + D) × R, out of 36: an
# unknown axis adds 0 to the sum, an unknown payback multiplies by 1. The letters label the
# axes in the views: « 24/36 (P1 F3 E1 D3 × R3) ».
RELEVANCE_BASE = ("reach", "frequency", "effort", "describability")
RELEVANCE_FACTOR = "payback"
RELEVANCE_AXES = RELEVANCE_BASE + (RELEVANCE_FACTOR,)
RELEVANCE_LETTERS = "PFEDR"
RELEVANCE_MAX = 3 * len(RELEVANCE_BASE) * 3
# Axes that no longer exist, with what replaced them. Their rating does not carry over: the new
# axis measures something else.
# Values: the key of the message that says what to do (rpt_i18n.py).
RELEVANCE_RETIRED = {"simplicity": "check.simplicity_retired"}
# Estimated gain of a task (README_operations.md §1.6): the hours a person gets back per month
# when the task reaches its target = runs per month × hours per run × share of those hours that
# the step removes. Runs per month come from the `frequency` text when it states a rate
# (« environ 30 par semaine »), else from relevance.frequency; hours per run from
# relevance.effort. No target, or a target that is not more automated than the status: A.
GAIN_RUNS = {1: 1 / 12, 2: 4, 3: 20}
GAIN_HOURS = {1: 0.25, 2: 1, 3: 3}
# The share of a task's manual time that a person still spends on it, by status (README §1.2):
# a conversational task (C, the AI only talks) keeps three quarters of it, a skilled one (S, the
# AI runs a method through a skill, a person validates) half. GAIN_SHARE, the share a step
# removes, is the difference between two statuses; TIME_LEFT also gives the hours a task no
# longer takes when its status changes between two relevés.
TIME_LEFT = {"M": 1, "C": 0.75, "S": 0.5, "A": 0}
STATUS_RANK = {"J": 0, "M": 1, "C": 2, "S": 3, "A": 4}
GAIN_SHARE = {(a, b): TIME_LEFT[a] - TIME_LEFT[b] for a in TIME_LEFT for b in TIME_LEFT
              if STATUS_RANK[b] > STATUS_RANK[a]}
# The statuses of a task, from the most to the least automated (counts, tables).
STATUS_ORDER = "ASCMJ"
# The statuses where a person still does part of the work that the AI could take: the action
# plan sorts them.
OPEN_STATUSES = ("M", "C", "S")
# What enters a process (`trigger.volume`, README_operations.md §1.19): a number of documents
# or of events a month (`kind`), with an optional label of what they are (`unit`: e-mails).
VOLUME_KINDS = ("document", "event")
# Full automation starts at the head of a chain (README_operations.md §1.19): the priority of a
# task whose target is A is its score × (1 + UPSTREAM_WEIGHT × its place from the end of its
# chain, 1 at the head, 0 at the end).
UPSTREAM_WEIGHT = 0.5
PER_MONTH = {"jour": 21, "semaine": 4.33, "mois": 1, "trimestre": 1 / 3, "an": 1 / 12,
             "année": 1 / 12}
COUNT_WORDS = {"moins d'une": 0.5, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4,
               "cinq": 5, "six": 6, "dix": 10, "quelques": 3, "plusieurs": 3, "une dizaine": 10,
               "une quinzaine": 15, "une vingtaine": 20, "une trentaine": 30}
RATE_RE = re.compile(r"\b(moins d'une|une (?:dizaine|quinzaine|vingtaine|trentaine)|\d+(?:[.,]\d+)?"
                     r"|quelques|plusieurs|une?|deux|trois|quatre|cinq|six|dix)\b"
                     r"(?!\s*(?:min|h\b|heure))[^.;:]*?"
                     r"\bpar (jour|semaine|mois|trimestre|an|année)\b")
EVERY_RE = re.compile(r"\b(?:chaque|tous les|toutes les) (jour|semaine|mois|trimestre|an|année"
                      r"|lundi|mardi|mercredi|jeudi|vendredi)")
EVERY_N_RE = re.compile(r"\b(?:tous|toutes) les (deux|trois|quatre|six|\d+) (jour|semaine|mois)")
# The same rates written in English (« about 30 per week », « every day », « every two weeks »):
# the content of a referential is in the organization's language. The French forms are read
# first.
PER_MONTH_EN = {"day": 21, "week": 4.33, "month": 1, "quarter": 1 / 3, "year": 1 / 12,
                "monday": 4.33, "tuesday": 4.33, "wednesday": 4.33, "thursday": 4.33,
                "friday": 4.33}
COUNT_WORDS_EN = {"less than once": 0.5, "less than one": 0.5, "once": 1, "twice": 2, "one": 1,
                  "a": 1, "an": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                  "ten": 10, "a few": 3, "several": 3, "a dozen": 12, "about ten": 10}
RATE_EN_RE = re.compile(r"\b(less than once|less than one|a few|several|a dozen|about ten"
                        r"|\d+(?:[.,]\d+)?|once|twice|one|two|three|four|five|six|ten|an?)\b"
                        r"(?!\s*(?:min|h\b|hours?\b))[^.;:]*?"
                        r"\b(?:per|a|an|each) (day|week|month|quarter|year)\b")
EVERY_EN_RE = re.compile(r"\b(?:every|each) (day|week|month|quarter|year|monday|tuesday"
                         r"|wednesday|thursday|friday)\b")
EVERY_N_EN_RE = re.compile(r"\bevery (two|three|four|six|\d+) (day|week|month)s\b")
ID_RE = {
    "role": re.compile(r"^[A-Z][A-Z0-9]*-R\d+[a-z]?$"),
    "process": re.compile(r"^[A-Z][A-Z0-9]*-P\d+[a-z]?$"),
    "task": re.compile(r"^[A-Z][A-Z0-9]*-T\d+(\.\d+)?[a-z]?$"),
    "tool": re.compile(r"^(skill|agent|managed-agent|hook|ci|bot|script|saas|reference|routine"
                       r"|command):[a-z0-9][a-z0-9._-]*$"),
    "department": re.compile(r"^[a-z][a-z0-9-]*$"),
    "task_type": re.compile(r"^tt:[a-z0-9][a-z0-9-]*$"),
    "data_source": re.compile(r"^data:[a-z0-9][a-z0-9-]*$"),
    "okr": re.compile(r"^O\d+(\.\d+)*[a-z]?$"),
    "key_result": re.compile(r"^O\d+(\.\d+)*[a-z]?\.KR\d+$"),
    "blocker": re.compile(r"^BLK-\d+$"),
    "os_zone": re.compile(r"^os:[a-z0-9][a-z0-9-]*$"),
    "insight": re.compile(r"^INS-\d+$"),
    "person": re.compile(r"^person:[a-z0-9][a-z0-9-]*$"),
    "agent": re.compile(r"^ag:[a-z0-9][a-z0-9-]*$"),
    "product": re.compile(r"^prod:[a-z0-9][a-z0-9-]*$"),
    "decision": re.compile(r"^dec:[a-z0-9][a-z0-9-]*$"),
    "artifact": re.compile(r"^art:[a-z0-9][a-z0-9-]*$"),
    "container": re.compile(r"^DC-\d+$"),
}
# The three stages of an agent (README_operations.md §1.16), in Teamstarter's order of work: make
# it work, then make it efficient, then refine it for the people it serves.
AGENT_STAGES = ("functional", "efficient", "refined")
RECAP_WHEN = ("daily", "weekly", "monthly")


ENUMS = {
    "status": {"A", "S", "C", "M", "J"}, "state": {"active", "proposed", "retired"},
    "trigger": {"auto", "event", "schedule", "manual"},
    "automation": {"end-to-end", "once-launched", "one-change-away", "assisted", "manual",
                   "routing"},
    "criterion": {"yes", "partial", "no"}, "level": {"01", "02", "03"},
    # `managed-agent`: an agent of the Claude platform, kept as a file in managed-agents/.
    "tool_type": {"skill", "agent", "managed-agent", "hook", "ci", "bot", "script", "saas",
                  "reference", "routine", "command"},
    "tool_status": {"live", "deprecated", "removed", "external"},
    "route_status": {"A", "S", "C", "M", "J", "-"},
    "connector": {"native", "mcp", "api", "export", "none"},
    # What is missing to reach the target (`blocker_type`), where a measure comes from, the
    # size and the kind of the work to automate a task (README_operations.md §1.6).
    "blocker_type": {"connector", "method", "tool", "decision", "data", "licence", "other"},
    # A blocker of the register (README_operations.md §1.14): the types of `blocker_type` and the
    # categories of the platform's project blockers; how far its resolution is; where it was
    # found.
    "blocker_kind": {"connector", "method", "tool", "decision", "data", "licence", "access",
                     "security", "budget", "organization", "provider", "other"},
    "blocker_state": {"open", "in_progress", "resolved", "dropped"},
    # The structure of the OS (README_operations.md §1.15).
    "zone_holds": {"reference", "findings", "records", "process", "briefs"},
    "feed_state": {"live", "manual", "possible"},
    "insight_kind": {"question", "finding"},
    # Access to the OS and recurring agents (README_operations.md §1.16).
    "access_mode": {"connector", "local", "repository", "none"},
    "licence_tier": {"free", "standard", "premium"},
    "access_state": {"works", "not_found", "unchecked"},
    "agent_kind": {"managed-agent", "routine", "scheduled-task", "worker"},
    "agent_state": {"construction", "live", "paused", "retired"},
    "agent_stage": set(AGENT_STAGES),
    "notify_channel": {"slack", "email"},
    "notify_when": {"run", "result", "failure", "daily", "weekly", "monthly"},
    "billing": {"api", "subscription"},
    # Business decisions and artifacts (README_operations.md §1.17).
    "decision_kind": {"offer", "target", "positioning", "strategy", "roadmap", "pricing",
                      "method"},
    "artifact_goal": {"understand", "share", "decide"},
    "artifact_state": {"live", "stale", "retired"},
    # A container of the data map (README_operations.md §1.20): what it is in its tool, and
    # whether it is still in use.
    "container_kind": {"folder", "file", "document", "spreadsheet", "presentation", "database",
                       "page", "object", "pipeline", "list", "channel", "label", "project",
                       "board", "view", "other"},
    "container_state": {"active", "archived", "duplicate", "unused"},
    # The rights of the AI in a tool (README_operations.md §1.7).
    "right_action": {"read", "search", "create", "update", "delete", "send", "run", "other"},
    "right_state": {"enabled", "available", "unavailable"},
    "blocker_source": {"map", "observation", "slack", "email", "ticket", "meeting", "merge",
                       "other"},
    "basis": {"declared", "observed"},
    "build_size": {"S", "M", "L"},
    "build_kind": {"prompt", "skill", "agent", "workflow", "script", "feature", "connector"},
    # What a data source holds, the rule an AI policy gives it (§1.8), how a fact is known
    # (`basis`, §1.9).
    # The place of a data source in the OS (README_operations.md §1.7): `excluded` is a
    # choice, with its reason; `included` and `to_add` are read from the flows of the OS when
    # not declared.
    "os_status": {"included", "to_add", "excluded"},
    "sensitivity": {"public", "personal", "client", "hr", "internal_confidential", "regulated",
                    "credentials"},
    "ai_rule": {"allowed", "validated", "minimized", "confidential", "authorization",
                "forbidden"},
    "fact_basis": {"observed", "declared", "inferred"},
    "output_kind": {"file", "folder"},
    # An observation (README_operations.md §4.1): where it was made, how the fact is known, what
    # the merge did with it.
    "surface": {"claude-code", "claude-ai", "other"},
    "observation_basis": {"observed", "declared"},
    "result": {"merged", "rejected"},
    # Objectives and key results (README_operations.md §1.13).
    "okr_level": {"company", "branch", "team"},
    "kr_unit": {"EUR", "percent", "score", "count", "hours", "days"},
    "kr_direction": {"min", "max"},
    "kr_per": {"month", "quarter", "year", "none"},
    "kr_kind": {"outcome", "activity"},
}
# The effort rating that a measured duration gives (relevance.effort, §1.6): under 30 minutes,
# up to 2 h, more.
EFFORT_BY_MINUTES = ((30, 1), (120, 2))
# How the AI reaches the data of a tool (README_operations.md §1.7). null: not known yet. The
# first three give the AI access; the others are the connectors to activate. Labels: the table
# "connector" of rpt_i18n.LABELS.
CONNECTOR_ORDER = ("native", "mcp", "api", "export", "none", None)
CONNECTED = {"native", "mcp", "api"}
# A relevé is the state of the referential at its update date (README_operations.md §4): one
# JSON file per date in releves/, written by the build. A v2 relevé keeps the facts the hours of a
# task come from (frequency, ratings, measure): the hours of every v2 relevé are recomputed with
# today's rules, so two dates stay comparable. A v1 relevé (until 2026-10-05) keeps the hours of
# its date and neither the target, the type nor the tools of a task. The table of changes,
# releves/changements.json, is generated from the successive relevés.
RELEVES = "releves"
RELEVE_FORMAT = "rpt-releve/v2"
RELEVE_FORMATS = ("rpt-releve/v1", RELEVE_FORMAT)
RELEVE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
CHANGES = "changements.json"
CHANGES_FORMAT = "rpt-changements/v1"
# Sensitivity and AI policy (README_operations.md §1.8). A data source lists what it holds
# (`sensitivity`; `[]`: internal working data only, the category `internal`). The AI policy
# (`ai_policy`, in ai-policy.yaml) gives each category a rule; a referential without one borrows
# that of OS/Operations, whose rules come from Teamstarter's charter template (art. 8, 11 and
# annex 1). A task gets the rules of the categories of its data; the strictest decides.
SENSITIVITY_ORDER = ("internal", "public", "personal", "client", "hr", "internal_confidential",
                     "regulated", "credentials")
# Their labels, definitions and notes: the tables "sensitivity", "sensitivity_def",
# "sensitivity_note", "ai_rule" and "ai_rule_text" of rpt_i18n.LABELS.
AI_RULES = ("allowed", "validated", "minimized", "confidential", "authorization", "forbidden")
POLICY_KEYS = ["name", "source", "version", "decided_by", "tools", "rules", "notes"]
# The budget policy of the organization (README_operations.md §1.18, `ai_investment` in
# ai-investment.yaml): what the AI may cost for some minutes of human work it does
# (`cost_ratio`), whether that ratio is enforced, the monthly amount the AI may spend
# (`budget`). Never borrowed. The licence of each person is in `ai_plan` (people.yaml or the
# person's map).
INVESTMENT_KEYS = ["cost_ratio", "enforced", "budget", "decided_by", "checked", "basis",
                   "evidence", "notes"]
# The modes a licence gives: `thinking` (the AI reasons before it answers), `work` (it works
# on files and tools: Cowork, Claude Code, artifacts, generation of assets).
LICENCE_MODES = ("thinking", "work")
AMOUNT_KEYS = {"budget": ["amount", "currency", "period"],
               "cost_ratio": ["amount", "currency", "minutes"]}
# The fields whose origin `basis` may give: every field of the element but these.
BASIS_EXCLUDED = {"id", "name", "basis", "notes", "aliases", "sources", "state", "replaced_by"}
# Lower-case words a person's name may hold (is_person).
NAME_PARTICLES = {"de", "du", "des", "d'", "la", "le", "van", "von", "da", "di", "del", "ben", "el"}


# --------------------------------------------------------------------------- languages

def localized(value, lang=None):
    """A text of a catalogue entry in one language. A map {language: text} gives `lang`
    (default: the language of the run), else English, else its first value; a plain text or
    list is the same in every language; None stays None."""
    if not isinstance(value, dict):
        return value
    for code in (lang or rpt_i18n.language(), rpt_i18n.LANGUAGES[0]):
        if value.get(code) not in (None, "", []):
            return value[code]
    return next((v for v in value.values() if v not in (None, "", [])), None)


def localized_list(value):
    """Every text of a field in all its languages, in order, each once: the values of a map
    {language: [texts]} or {language: text}, of a plain list, or a single text. Used to match
    words (aliases, names) whatever the language they are written in."""
    if isinstance(value, dict):
        values = [x for v in value.values() for x in (v if isinstance(v, list) else [v])]
    else:
        values = value if isinstance(value, list) else [value]
    out = []
    for x in values:
        if x not in (None, "") and x not in out:
            out.append(x)
    return out


def entry_name(item, lang=None):
    """The name of a catalogue entry in `lang`: its `name` map, or, in the former form, `name_en`
    in English and `name` otherwise."""
    name = item.get("name")
    if not isinstance(name, dict) and item.get("name_en") and \
            (lang or rpt_i18n.language()) == "en":
        return item["name_en"]
    return localized(name, lang)


def all_aliases(item):
    """The aliases of an entry in every language (a plain list belongs to every language)."""
    return localized_list(item.get("aliases"))


# The configuration of the referential being built (main: use_config). None = not chosen yet
# (a module that imports build_rpt): RPT_CONFIG, else Teamstarter's. "" = no configuration.
ACTIVE_CONFIG = None


def config_path():
    """The organization's configuration: the one main chose for --dir (use_config), else the
    file named by RPT_CONFIG, else rpt-config.yaml at the root of Teamstarter's OS. A packaged
    skill carries no configuration: it reads the file at the address the organization's
    instructions give, saves it, and its scripts take it with --config."""
    if ACTIVE_CONFIG is not None:
        return ACTIVE_CONFIG
    return os.environ.get("RPT_CONFIG") or CONFIG


def find_config(folder):
    """rpt-config.yaml of the referential in `folder`: in the folder or in one of its two
    parents (an OS keeps it at its root, next to OS/Operations/). None when there is none."""
    here = os.path.abspath(folder if os.path.isdir(folder) else os.path.dirname(folder))
    for _ in range(3):
        path = os.path.join(here, "rpt-config.yaml")
        if os.path.exists(path):
            return path
        here = os.path.dirname(here)
    return None


def use_config(cli, folder):
    """Choose the configuration of the referential in `folder`: --config, else RPT_CONFIG,
    else the rpt-config.yaml found next to it (find_config). Without one, the views are built
    with no configuration: never with Teamstarter's, which would put its global context and
    its intake address in another organization's explorer. Returns the path, or ""."""
    global ACTIVE_CONFIG
    ACTIVE_CONFIG = cli or os.environ.get("RPT_CONFIG") or find_config(folder) or ""
    return ACTIVE_CONFIG


def other_organization():
    """True when the configuration in use is not Teamstarter's: a referential of another
    organization, which must not borrow Teamstarter's AI policy."""
    path = config_path()
    return bool(path) and os.path.abspath(path) != os.path.abspath(CONFIG)


def org_language(cfg=None):
    """`organization.language` of the configuration (default: the one config_path() finds)
    when the messages exist in it, else English."""
    if cfg is None:
        try:
            cfg = load_config(config_path())
        except yaml.YAMLError:
            cfg = None
    org = cfg.get("organization") if isinstance(cfg, dict) else None
    code = str((org if isinstance(org, dict) else {}).get("language") or "").strip().lower()
    return code if code in rpt_i18n.LANGUAGES else rpt_i18n.LANGUAGES[0]


def setup_language(cli=None, cfg=None):
    """Set the language of the run and return it: `cli` (--lang), else RPT_LANG, else the
    organization's language, else English. validate_rpt.py calls it too."""
    return rpt_i18n.set_language(rpt_i18n.resolve(cli, org_language(cfg)))


def view_language():
    """The language of the generated views (referentiel.md, the explorer, notes written in
    observation files): the organization's, whatever the language of the run."""
    return org_language()


def label(table, code, lang=None, default=None):
    """The label of `code` in a table of rpt_i18n.LABELS (status, basis, automation, connector,
    sensitivity, sensitivity_def, sensitivity_note, ai_rule, ai_rule_text)."""
    return rpt_i18n.label(table, code, lang, default)


# ----------------------------------------------------------------------------- loading

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def yaml_files(path):
    """The rpt/v1 files of a folder (or the single file given)."""
    if os.path.isfile(path):
        return [path]
    return sorted(glob.glob(os.path.join(path, "*.yaml")))


def normalize(value, key=None):
    """YAML 1.1 reads dates as date objects and yes/no as booleans: bring dates back to text,
    and the yes/no of `criteria` back to "yes"/"no" (`fixed_path` stays a boolean)."""
    if isinstance(value, bool) and key == "criteria":
        return "yes" if value else "no"
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        inner = "criteria" if key == "criteria" else None
        return {str(k): normalize(v, inner or str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, key) for v in value]
    return value


def load(path, catalogues=True, catalogue_dir=DEFAULT_DIR, policy=True):
    """Read every file; return (referential, errors). Keeps the file of each entity.

    A referential other than the catalogue folder (a mapping sent by someone, a client's
    folder) borrows the departments, the tool catalogue and the data sources of that folder
    (OS/Operations by default) for the ids it does not declare itself; borrowed entries are
    marked `_borrowed` and never reported as unused. `policy=False`: the AI policy of that
    folder is not borrowed (another organization's referential, borrow_policy)."""
    ref = {name: [] for name in LISTS}
    ref["files"], ref["ai_policy"], ref["ai_investment"], errors = {}, None, None, []
    ref["dir"] = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path))
    for f in yaml_files(path):
        try:
            data = yaml.safe_load(read_text(f)) or {}
        except yaml.YAMLError as exc:
            hint = tr("hint.flow") if "flow" in str(exc) else ""
            errors.append(tr("load.yaml_unreadable", file=os.path.basename(f), error=exc,
                            hint=hint))
            continue
        errors += read_file(f, data, ref)
    catalogue_dir = os.path.abspath(catalogue_dir)
    if catalogues and os.path.abspath(path) != catalogue_dir:
        borrow(ref, catalogue_dir, policy)
    return ref, errors


def borrow(ref, folder=DEFAULT_DIR, policy=True):
    label = "OS/Operations" if folder == DEFAULT_DIR else os.path.basename(folder)
    policy_file = os.path.join(folder, "ai-policy.yaml")
    if policy and ref["ai_policy"] is None and os.path.exists(policy_file):
        policy = (yaml.safe_load(read_text(policy_file)) or {}).get("ai_policy")
        if isinstance(policy, dict):
            ref["ai_policy"] = dict(normalize(policy), _file=f"{label}/ai-policy.yaml",
                                    _borrowed=True)
    for list_name, file_name in CATALOGUES:
        declared = {x.get("id") for x in ref[list_name]}
        source = os.path.join(folder, file_name)
        # The OKR are a whole: a map that writes its own borrows none of the folder's.
        if not os.path.exists(source) or (list_name == "okrs" and declared):
            continue
        for item in (yaml.safe_load(read_text(source)) or {}).get(list_name) or []:
            if item.get("id") not in declared:
                item = normalize(item)
                item["_file"], item["_borrowed"] = f"{label}/{file_name}", True
                ref[list_name].append(item)


def read_file(f, data, ref):
    name = os.path.basename(f)
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        return [tr("load.format_missing", file=name, format=FORMAT)]
    errors = [tr("load.unknown_top_key", file=name, key=k)
              for k in data if k not in ("format", "meta", "ai_policy", "ai_investment") + LISTS]
    if data.get("ai_policy") is not None:
        if ref["ai_policy"] is not None:
            errors.append(tr("load.policy_twice", file=name, other=ref["ai_policy"]["_file"]))
        elif not isinstance(data["ai_policy"], dict):
            errors.append(tr("load.policy_not_mapping", file=name, keys=", ".join(POLICY_KEYS)))
        else:
            ref["ai_policy"] = dict(normalize(data["ai_policy"]), _file=name)
    if data.get("ai_investment") is not None:
        if ref.get("ai_investment") is not None:
            errors.append(tr("load.investment_twice", file=name,
                             other=ref["ai_investment"]["_file"]))
        elif not isinstance(data["ai_investment"], dict):
            errors.append(tr("load.investment_not_mapping", file=name,
                             keys=", ".join(INVESTMENT_KEYS)))
        else:
            ref["ai_investment"] = dict(normalize(data["ai_investment"]), _file=name)
    meta = normalize(data.get("meta") or {})
    errors += [tr("load.meta_unknown_key", file=name, key=k) for k in meta if k not in META_KEYS]
    errors += check_text_lists(meta, f"{name} meta")
    ref["files"][name] = meta
    for list_name in LISTS:
        for item in data.get(list_name) or []:
            item = normalize(item) if isinstance(item, dict) else {"id": repr(item)}
            item["_file"] = name
            ref[list_name].append(item)
    return errors


# -------------------------------------------------------------------------- validation

def index(ref):
    """id → entity, for every kind, former ids (aliases) included. The aliases of a department
    or of a task type are synonyms used to classify a mapping, not ids: they stay out of the
    index."""
    idx = {}
    for list_name in LISTS:
        for item in ref[list_name]:
            idx[item.get("id")] = item
            if list_name not in ("departments", "task_types"):
                for alias in former_ids(list_name, item):
                    idx.setdefault(alias, item)
    for okr in ref["okrs"]:
        for kr in okr.get("key_results") or []:
            if isinstance(kr, dict) and kr.get("id"):
                idx.setdefault(kr["id"], dict(kr, _okr=okr.get("id")))
    return idx


def former_ids(list_name, item):
    """The aliases of an entry that are former ids. A data source may also hold synonyms
    (words, in several languages): only its aliases written as ids (`data:…`) are former ids."""
    aliases = all_aliases(item)
    if list_name == "data_sources":
        return [a for a in aliases if isinstance(a, str) and ID_RE["data_source"].match(a)]
    return aliases


def kind_of_id(value):
    for kind in ("role", "process", "task", "tool", "data_source", "key_result", "okr",
                 "blocker", "os_zone", "insight", "person", "agent", "product", "decision",
                 "artifact", "container"):
        if isinstance(value, str) and ID_RE[kind].match(value):
            return kind
    return None


def check_text_lists(item, where, skip=()):
    """A list of texts whose element is a mapping or a list: an unquoted ":" between [...]."""
    return [tr("check.not_a_text", where=where, key=key, value=repr(value), hint=tr("hint.flow"))
            for key in TEXT_LISTS if key not in skip and isinstance(item.get(key), list)
            for value in item[key] if isinstance(value, (dict, list))]


def check_localized(item, where):
    """The texts of a catalogue entry that may be maps by language: `name`, `description` a
    text or {language: text}; `examples`, `aliases` a list of texts or {language: [texts]}."""
    errors = []
    for key in LOCALIZED_TEXTS:
        value = item.get(key)
        if isinstance(value, dict) and not (
                value and all(LANGUAGE_CODE.match(str(k)) and isinstance(v, str)
                              for k, v in value.items())):
            errors.append(tr("check.localized", where=where, key=key, value=repr(value)))
        elif isinstance(value, list):
            errors.append(tr("check.localized", where=where, key=key, value=repr(value)))
    for key in LOCALIZED_LISTS:
        value = item.get(key)
        if isinstance(value, dict) and not all(
                LANGUAGE_CODE.match(str(k)) and isinstance(v, list)
                and all(isinstance(x, str) for x in v) for k, v in value.items()):
            errors.append(tr("check.localized_list", where=where, key=key, value=repr(value)))
    return errors


def check_keys(kind, item, where):
    errors = [tr("check.required_missing", where=where, key=k)
              for k in REQUIRED[kind] if k not in item]
    errors += [tr("check.unknown_field_comma", where=where, key=k)
               for k in item if not k.startswith("_") and k not in KEYS[kind]]
    errors += check_text_lists(item, where, ("tools",) if kind == "data_source" else ())
    if kind in ("department", "task_type", "data_source", "os_zone"):
        errors += check_localized(item, where)
    by = (item.get("trigger") or {}).get("by") if isinstance(item.get("trigger"), dict) else None
    errors += check_text_lists({"by": by}, f"{where} trigger") if by else []
    for sub, allowed in SUB_KEYS.items():
        values = item.get(sub)
        for value in values if isinstance(values, list) else [values] if values else []:
            if isinstance(value, dict):
                errors += [tr("check.sub_unknown_field", where=where, sub=sub, key=k)
                           for k in value
                           if k not in allowed
                           and not (sub == "relevance" and k in RELEVANCE_RETIRED)]
    return errors


def check_enum(where, field, value, enum_name):
    if value is None or value in ENUMS[enum_name]:
        return []
    return [tr("check.enum", where=where, field=field, value=repr(value),
              expected=sorted(ENUMS[enum_name]))]


def check_ref(where, field, value, idx, expected=None):
    """A value that looks like an id must exist (and be of the expected kind). `idx` None: no
    referential at hand, only the form and the kind are checked."""
    kind = kind_of_id(value)
    if kind is None:
        return [tr("check.not_an_id", where=where, field=field, value=repr(value))] \
            if expected else []
    if idx is not None and value not in idx:
        return [tr("check.dangling", where=where, field=field, value=value)]
    if expected and kind not in expected:
        return [tr("check.wrong_kind", where=where, field=field, value=value,
                  kinds=tr("word.or").join(expected))]
    return []


def check_departments(where, item, dept_ids, required=False):
    depts = item.get("departments")
    if not depts:
        return [tr("check.departments_empty", where=where)] if required else []
    return [tr("check.department_unknown", where=where, department=d)
            for d in depts if d not in dept_ids]


def validate(ref):
    """Return (errors, warnings). An error makes the referential unusable."""
    errors, warnings = [], []
    idx = index(ref)
    dept_ids = {d.get("id") for d in ref["departments"]}
    tool_ids = {t.get("id") for t in ref["tools"]}
    type_ids = {x.get("id") for x in ref["task_types"]}
    errors += check_ids(ref)
    e, w = check_policy(ref, idx)
    errors, warnings = errors + e + check_investment(ref, idx), warnings + w
    for d in ref["departments"]:
        errors += check_keys("department", d, f"{d['_file']} {d.get('id')}")
    for x in ref["task_types"]:
        where = f"{x['_file']} {x.get('id')}"
        errors += check_keys("task_type", x, where)
        if x.get("department") is not None and x.get("department") not in dept_ids:
            errors.append(tr("check.department_unknown", where=where,
                            department=x.get("department")))
    for t in ref["tools"]:
        errors += check_tool(t)
    for d in ref["data_sources"]:
        e, w = check_data_source(d, tool_ids)
        errors, warnings = errors + e, warnings + w
    # Borrowed objectives were checked in their own folder: their teams and owners are not in a map.
    teams = {r.get("team") for r in ref["roles"]}
    for o in [o for o in ref["okrs"] if not o.get("_borrowed")]:
        e, w = check_okr(o, idx, teams)
        errors, warnings = errors + e, warnings + w
    for r in ref["roles"]:
        errors += check_role(r, idx, dept_ids)
    for p in ref["processes"]:
        e, w = check_process(p, idx, dept_ids, tool_ids)
        errors, warnings = errors + e, warnings + w
    for t in ref["tasks"]:
        e, w = check_task(t, idx, dept_ids, tool_ids, type_ids)
        errors, warnings = errors + e, warnings + w
    e, w = check_blockers(ref, idx)
    errors, warnings = errors + e, warnings + w
    e, w = check_os(ref, idx)
    errors, warnings = errors + e, warnings + w
    for x in ref["people"]:
        errors += check_person(x, idx)
    warnings += check_shared_names(ref)
    for a in ref["agents"]:
        e, w = check_agent(a, idx)
        errors, warnings = errors + e, warnings + w
    for x in ref["products"]:
        errors += check_keys("product", x, f"{x['_file']} {x.get('id')}")
        if x.get("tool") is not None:
            errors += check_ref(f"{x['_file']} {x.get('id')}", "tool", x["tool"], idx,
                                expected=["tool"])
    for d in ref["decisions"]:
        e, w = check_decision(d, idx)
        errors, warnings = errors + e, warnings + w
    for a in ref["artifacts"]:
        e, w = check_artifact(a, idx)
        errors, warnings = errors + e, warnings + w
    for c in ref["containers"]:
        e, w = check_container(c, idx)
        errors, warnings = errors + e, warnings + w
    errors += check_container_tree(ref)
    warnings += check_orphans(ref)
    return errors, warnings


def check_ids(ref):
    """Ids are well formed and unique; a former id (alias) of a role, process, task, tool or data
    source follows the id format of its kind; a synonym (a name or an alias, in any language)
    belongs to one department, one task type, one data source only."""
    errors, seen = [], {}
    for list_name in LISTS:
        kind = KIND_OF_LIST[list_name]
        for item in ref[list_name]:
            ids = [item.get("id")]
            if kind in ("role", "process", "task", "tool", "data_source", "okr"):
                ids += former_ids(list_name, item)
            for value in ids:
                where = f"{item['_file']} {value}"
                if not isinstance(value, str) or not (ID_RE[kind].match(value) or
                                                      (kind == "tool" and ":" in value)):
                    errors.append(tr("check.id_malformed", where=where, kind=kind))
                elif value in seen:
                    errors.append(tr("check.id_used", where=where, file=seen[value]))
                seen[value] = item["_file"]
    for list_name in ("departments", "task_types", "data_sources"):
        errors += check_synonyms(list_name, ref[list_name])
    return errors


def synonyms_of(list_name, item):
    """The words that name a catalogue entry, every language together: its id, its names and
    its aliases. For a data source: its aliases that are words, not former ids (two maps may
    name their sources alike)."""
    if list_name == "data_sources":
        return [a for a in all_aliases(item) if a not in former_ids(list_name, item)]
    return [item.get("id")] + localized_list(item.get("name")) + \
        localized_list(item.get("name_en")) + all_aliases(item)


def check_synonyms(list_name, items):
    errors, synonyms = [], {}
    for d in items:
        for word in synonyms_of(list_name, d):
            key = str(word).lower()
            if key in synonyms and synonyms[key] != d.get("id"):
                errors.append(tr("check.synonym_taken", list=list_name, id=d.get("id"),
                                word=word, other=synonyms[key]))
            synonyms[key] = d.get("id")
    return errors


def check_tool(t):
    where = f"{t['_file']} {t.get('id')}"
    errors = check_keys("tool", t, where)
    errors += check_enum(where, "type", t.get("type"), "tool_type")
    errors += check_enum(where, "status", t.get("status"), "tool_status")
    prefix = str(t.get("id", "")).split(":")[0]
    if t.get("type") and prefix != t.get("type"):
        errors.append(tr("check.tool_prefix", where=where, type=t.get("type")))
    return errors + check_rights(t, where) + check_shared(t, where)


# A shared assistant (README_operations.md §1.18): a bot that people reach in the team's chat
# tool, whose AI is connected to the company's data. `audience`: `all` or team codes;
# `reaches: os` when its AI reads the OS; `state`, `checked`, `basis`, `evidence` as for the
# access of a person (§1.16).
SHARED_KEYS = ("channel", "audience", "reaches", "state", "checked", "basis", "evidence", "notes")


def check_shared(t, where):
    s = t.get("shared")
    if s is None:
        return []
    at = f"{where} shared"
    aud = s.get("audience") if isinstance(s, dict) else None
    if not isinstance(s, dict) or not s.get("channel") or not s.get("state") or \
            not (aud == "all" or (isinstance(aud, list) and aud and
                                  all(TEAM_RE.match(str(x)) for x in aud))) or \
            s.get("reaches") not in (None, "os") or set(s) - set(SHARED_KEYS):
        return [tr("check.shared_shape", where=at)]
    errors = check_enum(at, "state", s.get("state"), "access_state")
    errors += check_enum(at, "basis", s.get("basis"), "fact_basis")
    if s.get("checked") is not None and not DATE_RE.match(str(s["checked"])):
        errors.append(tr("check.blocker_date", where=at, field="checked",
                         value=repr(s["checked"])))
    return errors


def shared_assistants(ref):
    """The shared assistants whose AI reads the OS (README_operations.md §1.18): a tool in use
    with `shared.reaches: os` and `shared.state: works`."""
    return [t for t in ref["tools"] if isinstance(t.get("shared"), dict)
            and t.get("status") in ("live", "external") and t["shared"].get("reaches") == "os"
            and t["shared"].get("state") == "works"]


def check_rights(t, where):
    """`rights: [{action, what, state, via, basis, notes}]` of a tool (README_operations.md §1.7):
    each right names an action and its object, and says whether it is enabled here, offered by
    the connector without being enabled, or not offered."""
    rights = t.get("rights")
    if rights is None:
        return []
    if not isinstance(rights, list):
        return [tr("check.rights_not_list", where=where)]
    errors = []
    for i, r in enumerate(rights):
        at = f"{where} rights[{i}]"
        if not isinstance(r, dict):
            errors.append(tr("check.rights_not_list", where=where))
            continue
        errors += [tr("check.required_missing", where=at, key=k)
                   for k in ("action", "what", "state") if not r.get(k)]
        errors += check_enum(at, "action", r.get("action"), "right_action")
        errors += check_enum(at, "state", r.get("state"), "right_state")
        errors += check_enum(at, "via", r.get("via"), "connector")
        errors += check_enum(at, "basis", r.get("basis"), "fact_basis")
    checked = t.get("rights_checked")
    if checked is not None and not DATE_RE.match(str(checked)):
        errors.append(tr("check.blocker_date", where=where, field="rights_checked",
                         value=repr(checked)))
    return errors


def check_data_source(d, tool_ids):
    """The tools of a data source exist, each once, with a known connector (or null)."""
    where = f"{d['_file']} {d.get('id')}"
    errors = check_keys("data_source", d, where)
    entries = d.get("tools") or []
    if not isinstance(entries, list):
        return errors + [tr("check.source_tools_not_list", where=where, value=repr(entries))], []
    seen = set()
    for e in entries:
        if not isinstance(e, dict):
            errors.append(tr("check.source_tool_not_mapping", where=where, value=repr(e)))
            continue
        tool = e.get("tool")
        if not tool:
            errors.append(tr("check.source_tool_missing", where=where))
        elif tool not in tool_ids:
            errors.append(tr("check.tool_unknown", where=where, tool=tool))
        elif tool in seen:
            errors.append(tr("check.tool_twice", where=where, tool=tool))
        seen.add(tool)
        errors += check_enum(where, f"tools.connector ({tool})", e.get("connector"), "connector")
    errors += check_sensitivity(d, where) + check_basis("data_source", d, where)
    if d.get("os") is not None:
        if not isinstance(d["os"], dict):
            errors.append(tr("check.source_os_shape", where=where))
        else:
            errors += check_enum(where, "os.status", d["os"].get("status"), "os_status")
            reason = str(d["os"].get("reason") or "").strip()
            if d["os"].get("status") == "excluded" and not reason:
                errors.append(tr("check.source_os_reason", where=where))
    # A borrowed source without tools is a kind of data the map says where it keeps.
    warnings = [] if entries or d.get("_borrowed") else [tr("warn.source_without_tool", where=where)]
    if d.get("sensitivity") is None and not d.get("_borrowed"):
        warnings.append(tr("warn.sensitivity_unsaid", where=where))
    return errors, warnings


def check_role(r, idx, dept_ids):
    where = f"{r['_file']} {r.get('id')}"
    errors = check_keys("role", r, where) + check_departments(where, r, dept_ids, required=True)
    errors += check_enum(where, "state", r.get("state"), "state")
    errors += check_enum(where, "level", r.get("level"), "level")
    for key, value in (r.get("criteria") or {}).items():
        errors += check_enum(where, f"criteria.{key}", value, "criterion")
    for entry in r.get("entries") or []:
        errors += check_enum(where, "entries.trigger", entry.get("trigger"), "trigger")
    for route in r.get("routing") or []:
        errors += check_enum(where, "routing.status", route.get("status"), "route_status")
        errors += check_enum(where, "routing.state", route.get("state"), "state")
        errors += check_ref(where, "routing.to", route.get("to"), idx)
    return errors + check_basis("role", r, where)


def check_process(p, idx, dept_ids, tool_ids):
    where = f"{p['_file']} {p.get('id')}"
    errors = check_keys("process", p, where) + check_departments(where, p, dept_ids)
    errors += check_enum(where, "state", p.get("state"), "state")
    errors += check_enum(where, "automation", p.get("automation"), "automation")
    errors += check_ref(where, "role", p.get("role"), idx, expected=["role"])
    trigger = p.get("trigger") or {}
    errors += check_enum(where, "trigger.type", trigger.get("type"), "trigger")
    for by in trigger.get("by") or []:
        errors += check_ref(where, "trigger.by", by, idx)
    errors += check_volume(trigger.get("volume"), where)
    for step in p.get("steps") or []:
        errors += check_ref(where, "steps", step, idx, expected=["task"])
        if p.get("state") == "active" and idx.get(step, {}).get("state") != "active":
            errors.append(tr("check.process_step_inactive", where=where, step=step))
    for nxt in p.get("next") or []:
        errors += check_ref(where, "next", nxt, idx, expected=["process"])
    errors += [tr("check.tool_unknown", where=where, tool=x) for x in p.get("tools") or []
               if x not in tool_ids]
    errors += check_handoffs(p, where, idx) + check_basis("process", p, where)
    return errors, check_process_shape(p, where, idx)


def check_volume(v, where):
    """`trigger.volume`: what enters the process a month, `{count, kind, unit}`: a number of
    documents or of events (`kind`), and what they are (`unit`, optional: e-mails)."""
    if v is None:
        return []
    if not isinstance(v, dict):
        return [tr("check.volume_shape", where=where, value=repr(v))]
    errors = [tr("check.sub_unknown_field", where=where, sub="trigger.volume", key=k)
              for k in v if k not in ("count", "kind", "unit")]
    if not positive(v.get("count")):
        errors.append(tr("check.volume_count", where=where, value=repr(v.get("count"))))
    if v.get("kind") not in VOLUME_KINDS:
        errors.append(tr("check.enum", where=where, field="trigger.volume.kind",
                         value=repr(v.get("kind")), expected=list(VOLUME_KINDS)))
    if "unit" in v and (not isinstance(v["unit"], str) or not v["unit"].strip()):
        errors.append(tr("check.volume_unit", where=where))
    return errors


def check_process_shape(p, where, idx):
    """Warnings on processes that the model says are not processes."""
    if p.get("state") == "retired":
        if not p.get("replaced_by"):
            return [tr("warn.retired_without_replacement", where=where)]
        return []
    steps = p.get("steps") or []
    if len(steps) < 2 and p.get("automation") != "routing":
        return [tr("warn.process_too_short", where=where, count=len(steps))]
    return []


def check_task(t, idx, dept_ids, tool_ids, type_ids=()):
    where = f"{t['_file']} {t.get('id')}"
    errors = check_keys("task", t, where) + check_departments(where, t, dept_ids)
    errors += check_type(t, where, type_ids)
    errors += check_enum(where, "state", t.get("state"), "state")
    errors += check_enum(where, "status", t.get("status"), "status")
    errors += check_enum(where, "target", t.get("target"), "status")
    errors += check_ref(where, "role", t.get("role"), idx, expected=["role"])
    errors += [tr("check.tool_unknown", where=where, tool=x) for x in t.get("tools") or []
               if x not in tool_ids]
    errors += [e for x in t.get("data") or []
               for e in check_ref(where, "data", x, idx, expected=["data_source"])]
    errors += check_relevance(t, where)
    errors += check_enum(where, "blocker_type", t.get("blocker_type"), "blocker_type")
    errors += check_measure(t, where) + check_queue(t, where) + check_stakes(t, where) \
        + check_build(t, where) \
        + check_job(t, where)
    errors += check_method(t, where, idx) + check_basis("task", t, where)
    errors += check_files(t, where, idx)
    e, warnings = check_task_okrs(t, where, idx, check_ids=bool(okr_ids(idx)))
    errors += e
    warnings += measure_warnings(t, where)
    if t.get("status") in ("M", "J") and not t.get("by"):
        warnings.append(tr("warn.task_without_by", where=where, status=t.get("status")))
    # A skilled task runs its method through a skill or an agent (README_operations.md §1.2).
    if t.get("status") == "S" and not any((idx.get(x) or {}).get("type") in SKILL_TOOL_TYPES
                                          for x in t.get("tools") or []):
        warnings.append(tr("warn.skilled_without_skill", where=where))
    if type_ids and t.get("state") == "active" and not t.get("type"):
        warnings.append(tr("warn.task_without_type", where=where))
    return errors, warnings


def check_blockers(ref, idx):
    """The blocker register (README_operations.md §1.14): each entry, then the same problem
    written twice, and, in the referential, the tasks that still write their own `blocker`
    (moved to blockers.yaml)."""
    errors, warnings, seen = [], [], {}
    for b in ref["blockers"]:
        e, w = check_blocker(b, idx)
        errors, warnings = errors + e, warnings + w
        key = re.sub(r"\W+", " ", str(b.get("text") or "").lower()).strip()
        if key and key in seen and b.get("state") not in ("resolved", "dropped"):
            warnings.append(tr("warn.blocker_twice", where=f"{b['_file']} {b.get('id')}",
                               other=seen[key]))
        seen.setdefault(key, b.get("id"))
    if os.path.abspath(ref.get("dir") or "") == os.path.abspath(DEFAULT_DIR):
        warnings += [tr("warn.task_blocker_field", where=f"{t['_file']} {t.get('id')}",
                        file=BLOCKERS_FILE)
                     for t in ref["tasks"] if t.get("blocker") or t.get("blocker_type")]
    return errors, warnings


def check_blocker(b, idx):
    where = f"{b['_file']} {b.get('id')}"
    errors = check_keys("blocker", b, where)
    errors += check_enum(where, "type", b.get("type"), "blocker_kind")
    errors += check_enum(where, "state", b.get("state"), "blocker_state")
    errors += check_enum(where, "source", b.get("source"), "blocker_source")
    errors += check_enum(where, "basis", b.get("basis"), "fact_basis")
    tasks = b.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append(tr("check.blocker_tasks", where=where))
    else:
        errors += [e for x in tasks for e in check_ref(where, "tasks", x, idx, expected=["task"])]
    if b.get("owner") is not None:
        errors += check_ref(where, "owner", b.get("owner"), idx, expected=["role"])
    for field in ("opened", "resolved"):
        value = b.get(field)
        if value is not None and not DATE_RE.match(str(value)):
            errors.append(tr("check.blocker_date", where=where, field=field, value=repr(value)))
    closed = b.get("state") in ("resolved", "dropped")
    if closed and not b.get("resolved"):
        errors.append(tr("check.blocker_resolved_missing", where=where, state=b.get("state")))
    if not closed and b.get("resolved"):
        errors.append(tr("check.blocker_resolved_open", where=where, state=b.get("state")))
    if b.get("resolved") and b.get("opened") and str(b["resolved"]) < str(b["opened"]):
        errors.append(tr("check.blocker_dates_order", where=where))
    warnings = []
    if closed and not b.get("resolution"):
        warnings.append(tr("warn.blocker_no_resolution", where=where))
    if idx and not closed and isinstance(tasks, list) and tasks and all(
            (idx.get(x) or {}).get("state") == "retired" or (idx.get(x) or {}).get("status") == "A"
            for x in tasks if x in idx) and all(x in idx for x in tasks):
        warnings.append(tr("warn.blocker_tasks_done", where=where))
    if isinstance(b.get("evidence"), str) and len(b["evidence"]) > EVIDENCE_MAX:
        errors.append(tr("obs.evidence_long", where=where, size=len(b["evidence"]),
                         max=EVIDENCE_MAX))
    return errors, warnings


# The states an insight takes, by kind (README_operations.md §1.15).
INSIGHT_STATES = {"question": ("answered", "partial", "unanswered"),
                  "finding": ("emerging", "confirmed", "acted", "closed")}
FEED_RANK = {"live": 0, "manual": 1, "possible": 2}


def os_root(ref):
    """The root of the company's OS when the referential sits in it (`<root>/OS/Operations`),
    where the zones' folders and the insights' files are looked for; None otherwise."""
    folder = os.path.abspath(ref.get("dir") or "")
    parent = os.path.dirname(folder)
    return os.path.dirname(parent) if os.path.basename(parent) == "OS" else None


def check_os(ref, idx):
    """The structure of the OS and the insight register (README_operations.md §1.15)."""
    errors, warnings = [], []
    root = os_root(ref)
    zones = {z.get("id"): z for z in ref["os_zones"]}
    insights = {i.get("id") for i in ref["insights"]}
    sources = {d.get("id") for d in ref["data_sources"]}
    fed = set()
    for z in ref["os_zones"]:
        e, w, names = check_zone(z, idx, (zones, sources, insights), root)
        errors, warnings, fed = errors + e, warnings + w, fed | names
    for i in ref["insights"]:
        e, w = check_insight(i, idx, zones, root)
        errors, warnings = errors + e, warnings + w
        if i.get("id") not in fed:
            warnings.append(tr("warn.insight_no_feed", where=f"{i['_file']} {i.get('id')}"))
    return errors, warnings


def zone_loops(z, zones):
    """True when following `parent` from this zone comes back to it or leaves the zones."""
    seen, current = set(), z
    while current.get("parent") is not None:
        if current.get("id") in seen or current["parent"] not in zones:
            return True
        seen.add(current.get("id"))
        current = zones[current["parent"]]
    return False


def check_zone(z, idx, known, root):
    """`known`: the zones by id, the ids of the data sources, the ids of the insights."""
    zones, sources, insights = known
    where = f"{z['_file']} {z.get('id')}"
    errors = check_keys("os_zone", z, where)
    errors += check_enum(where, "holds", z.get("holds"), "zone_holds")
    errors += check_enum(where, "basis", z.get("basis"), "fact_basis")
    if z.get("parent") is not None and zone_loops(z, zones):
        errors.append(tr("check.zone_parent", where=where, parent=z.get("parent")))
    if z.get("owner") is not None:
        errors += check_ref(where, "owner", z.get("owner"), idx, expected=["role"])
    warnings = []
    if root and z.get("path") and not os.path.isdir(os.path.join(root, str(z["path"]))):
        warnings.append(tr("warn.zone_path", where=where, path=z["path"]))
    names = set()
    feeds = z.get("feeds") or []
    if not isinstance(feeds, list):
        return errors + [tr("check.feed_shape", where=where)], warnings, names
    for n, f in enumerate(feeds, 1):
        at = f"{where} feeds[{n}]"
        if not isinstance(f, dict) or not f.get("from") or not f.get("state"):
            errors.append(tr("check.feed_shape", where=at))
            continue
        errors += check_enum(at, "state", f.get("state"), "feed_state")
        errors += check_enum(at, "basis", f.get("basis"), "fact_basis")
        if f["from"] not in zones and resolve(idx, f["from"]) not in sources:
            errors.append(tr("check.feed_from", where=at, value=f["from"]))
        for field in ("tool", "skill"):
            if f.get(field) is not None:
                errors += check_ref(at, field, f[field], idx, expected=["tool"])
        for x in f.get("insights") or []:
            if x not in insights:
                errors.append(tr("check.feed_insight", where=at, value=x))
            names.add(x)
    return errors, warnings, names


def check_insight(i, idx, zones, root):
    where = f"{i['_file']} {i.get('id')}"
    errors = check_keys("insight", i, where)
    errors += check_enum(where, "kind", i.get("kind"), "insight_kind")
    errors += check_enum(where, "basis", i.get("basis"), "fact_basis")
    allowed = INSIGHT_STATES.get(i.get("kind"))
    if allowed and i.get("state") not in allowed:
        errors.append(tr("check.insight_state", where=where, kind=i.get("kind"),
                         expected=", ".join(allowed), value=repr(i.get("state"))))
    if i.get("zone") not in zones:
        errors += check_ref(where, "zone", i.get("zone"), idx, expected=["os_zone"]) or \
            [tr("check.dangling", where=where, field="zone", value=i.get("zone"))]
    for field in ("count", "accounts"):
        value = i.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)
                                  or value < 1):
            errors.append(tr("check.insight_number", where=where, field=field, value=value))
    if isinstance(i.get("count"), int) and isinstance(i.get("accounts"), int) \
            and i["accounts"] > i["count"]:
        errors.append(tr("check.insight_accounts", where=where, accounts=i["accounts"],
                         count=i["count"]))
    for field in ("first_seen", "last_seen"):
        value = i.get(field)
        if value is not None and not DATE_RE.match(str(value)):
            errors.append(tr("check.insight_dates", where=where, field=field, value=value))
    if i.get("first_seen") and i.get("last_seen") and \
            str(i["last_seen"]) < str(i["first_seen"]):
        errors.append(tr("check.insight_dates", where=where, field="last_seen",
                         value=i["last_seen"]))
    for x in i.get("tasks") or []:
        errors += check_ref(where, "tasks", x, idx, expected=["task"])
    for x in i.get("okrs") or []:
        errors += check_ref(where, "okrs", x, idx, expected=["key_result", "okr"])
    if i.get("owner") is not None:
        errors += check_ref(where, "owner", i.get("owner"), idx, expected=["role"])
    if isinstance(i.get("evidence"), str) and len(i["evidence"]) > EVIDENCE_MAX:
        errors.append(tr("obs.evidence_long", where=where, size=len(i["evidence"]),
                         max=EVIDENCE_MAX))
    warnings = []
    if i.get("kind") == "finding" and not i.get("count"):
        warnings.append(tr("warn.finding_no_count", where=where))
    if root and i.get("file") and not os.path.exists(os.path.join(root, str(i["file"]))):
        warnings.append(tr("warn.insight_file", where=where, path=i["file"]))
    return errors, warnings


def check_plan(plan, where, idx=None):
    """The AI licence of a person: {tool, plan, tier, modes} (README_operations.md §1.18)."""
    if plan is None:
        return []
    at = f"{where} ai_plan"
    if not isinstance(plan, dict):
        return [tr("check.plan_shape", where=at, value=repr(plan))]
    errors = check_enum(at, "tier", plan.get("tier"), "licence_tier") + \
        check_enum(at, "basis", plan.get("basis"), "fact_basis")
    if plan.get("tool") is not None:
        errors += check_ref(at, "tool", plan["tool"], idx, expected=["tool"])
    modes = plan.get("modes") or []
    if not isinstance(modes, list) or any(m not in LICENCE_MODES for m in modes):
        errors.append(tr("check.enum", where=at, field="modes", value=repr(modes),
                         expected=list(LICENCE_MODES)))
    return errors


def check_person(x, idx=None):
    """A person and the ways their AI reaches the OS (README_operations.md §1.16)."""
    where = f"{x['_file']} {x.get('id')}"
    errors = check_keys("person", x, where) + check_plan(x.get("ai_plan"), where, idx)
    errors += check_maps(x.get("maps"), where)
    access = x.get("os_access") or []
    if not isinstance(access, list):
        return errors + [tr("check.access_shape", where=where)]
    for n, a in enumerate(access, 1):
        at = f"{where} os_access[{n}]"
        if not isinstance(a, dict) or not a.get("mode"):
            errors.append(tr("check.access_shape", where=at))
            continue
        errors += check_enum(at, "mode", a.get("mode"), "access_mode")
        errors += check_enum(at, "state", a.get("state"), "access_state")
        errors += check_enum(at, "basis", a.get("basis"), "fact_basis")
        if a.get("mode") != "none" and not a.get("state"):
            errors.append(tr("check.access_state", where=at))
        if a.get("tool") is not None:
            errors += check_ref(at, "tool", a["tool"], idx, expected=["tool"])
        if a.get("checked") is not None and not DATE_RE.match(str(a["checked"])):
            errors.append(tr("check.blocker_date", where=at, field="checked",
                             value=repr(a["checked"])))
        if isinstance(a.get("evidence"), str) and len(a["evidence"]) > EVIDENCE_MAX:
            errors.append(tr("obs.evidence_long", where=at, size=len(a["evidence"]),
                             max=EVIDENCE_MAX))
    return errors


def check_maps(maps, where):
    """`maps`: the maps of the person merged into the referential, one entry per map, `{hat,
    date}`: the code of the team of the map (`meta.team`) and its date (README_operations.md
    §1.16). The merge adds the entry."""
    if maps is None:
        return []
    if not isinstance(maps, list):
        return [tr("check.maps_shape", where=where, value=repr(maps))]
    return [tr("check.maps_shape", where=f"{where} maps[{n}]", value=repr(m))
            for n, m in enumerate(maps, 1)
            if not (isinstance(m, dict) and set(m) <= {"hat", "date"}
                    and TEAM_RE.match(str(m.get("hat") or ""))
                    and DATE_RE.match(str(m.get("date") or "")))]


def map_coverage(ref, cfg=None, today=None):
    """How much of the organization the referential describes, and how recent it is
    (README_operations.md §1.16): per person, the date of their last map, its age on `today`
    (the update date of the referential) and its level on the scale of the zones of the OS
    (FRESHNESS); per team of the configuration, its headcount (`teams[].headcount`), the people
    who sent a map for it, and the people the referential knows in it who did not; and the
    people to remind: never mapped first, then the oldest last maps from « aging » on."""
    today = today or last_updated(ref)[:10]
    if not today:
        return None
    day = datetime.date.fromisoformat(today)
    people = []
    for x in ref["people"]:
        maps = [m for m in x.get("maps") or [] if isinstance(m, dict) and m.get("date")]
        last = max((str(m["date"]) for m in maps), default=None)
        days = (day - datetime.date.fromisoformat(last)).days if last else None
        people.append({"id": x.get("id"), "name": x.get("name"), "teams": x.get("_teams") or [],
                       "maps": len(maps), "hats": sorted({str(m.get("hat")) for m in maps}),
                       "last": last, "days": days,
                       "level": freshness_level(days) if days is not None else None})
    teams = []
    for t in (cfg or {}).get("teams") or []:
        if not isinstance(t, dict) or not t.get("code"):
            continue
        code = str(t["code"])
        mapped = [p for p in people if code in p["hats"]]
        known = [p for p in people if code in p["teams"] and code not in p["hats"]]
        if not (mapped or known or t.get("headcount")):
            continue
        teams.append({"code": code, "name": t.get("name"), "headcount": t.get("headcount"),
                      "mapped": len(mapped), "missing": [p["id"] for p in known]})
    counts = [t.get("headcount") for t in (cfg or {}).get("teams") or [] if isinstance(t, dict)]
    headcount = sum(c for c in counts if isinstance(c, int)) or None
    never = sorted((p for p in people if not p["last"]), key=lambda p: str(p["name"]))
    old = sorted((p for p in people if p["level"] in ("aging", "old", "stale")),
                 key=lambda p: -p["days"])
    return {"today": today, "people": people, "teams": teams, "headcount": headcount,
            "headcount_complete": bool(counts) and all(isinstance(c, int) for c in counts),
            "mapped": sum(1 for p in people if p["last"]), "known": len(people),
            "remind": [p["id"] for p in never + old]}


def check_agent(a, idx, criteria=True):
    """A recurring agent and what it does (README_operations.md §1.16). `criteria` False: the
    stage is checked for its form only (an observation read without the referential)."""
    where = f"{a['_file']} {a.get('id')}"
    errors = check_keys("agent", a, where)
    errors += check_enum(where, "kind", a.get("kind"), "agent_kind")
    errors += check_enum(where, "state", a.get("state"), "agent_state")
    errors += check_enum(where, "basis", a.get("basis"), "fact_basis")
    for field, kinds in (("platform", ["tool"]), ("owner", ["role"])):
        if a.get(field) is not None:
            errors += check_ref(where, field, a[field], idx, expected=kinds)
    for field, kinds in (("tasks", ["task"]), ("skills", ["tool"]), ("people", ["person"]),
                         ("data", ["data_source"]), ("zones", ["os_zone"])):
        for x in a.get(field) or []:
            errors += check_ref(where, field, x, idx, expected=kinds)
    c = a.get("cost")
    if c is not None and not isinstance(c, dict):
        errors.append(tr("check.cost_shape", where=where))
    elif c:
        errors += check_enum(where, "cost.billing", c.get("billing"), "billing")
        errors += check_enum(where, "cost.basis", c.get("basis"), "fact_basis")
        for field in ("per_run", "tokens_in", "tokens_out", "web_searches", "minutes", "runs"):
            value = c.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or value < 0):
                errors.append(tr("check.cost_number", where=where, field=field, value=value))
        if c.get("model") is not None and c["model"] not in MODEL_PRICES:
            errors.append(tr("check.cost_model", where=where, value=c["model"],
                             models=", ".join(sorted(MODEL_PRICES))))
    errors += check_agent_stage(a, where, criteria)
    warnings = []
    if a.get("state") == "live" and not a.get("tasks"):
        warnings.append(tr("warn.agent_no_task", where=where))
    config = a.get("config")
    # A path of the repository is checked when the repository is at hand (not in a packaged skill).
    if config and not str(config).startswith("https://") and \
            os.path.isdir(os.path.join(REPO_ROOT, ".git")) and \
            not os.path.exists(os.path.join(REPO_ROOT, str(config))):
        warnings.append(tr("warn.agent_config", where=where, path=config))
    return errors, warnings


def check_agent_stage(a, where, criteria=True):
    """The stage of an agent and its notifications (README_operations.md §1.16): a stage is
    declared with its evidence, and only when the criteria a file can show are met, its own and
    those of the stages before it."""
    errors = []
    notify = a.get("notify")
    if notify is not None and not isinstance(notify, list):
        errors.append(tr("check.agent_notify_shape", where=where))
    for n in notify if isinstance(notify, list) else []:
        if not isinstance(n, dict):
            errors.append(tr("check.agent_notify_shape", where=where))
            continue
        errors += check_enum(where, "notify.channel", n.get("channel"), "notify_channel")
        errors += check_enum(where, "notify.when", n.get("when"), "notify_when")
    stage = a.get("stage")
    if stage is None:
        return errors
    if not isinstance(stage, dict):
        return errors + [tr("check.agent_stage_shape", where=where)]
    errors += check_enum(where, "stage.level", stage.get("level"), "agent_stage")
    errors += check_enum(where, "stage.basis", stage.get("basis"), "fact_basis")
    if stage.get("level") in AGENT_STAGES and not stage.get("evidence"):
        errors.append(tr("check.agent_stage_evidence", where=where))
    reached = AGENT_STAGES[:AGENT_STAGES.index(stage["level"]) + 1] \
        if stage.get("level") in AGENT_STAGES and criteria else ()
    criteria = agent_criteria(a)
    missing = [k for st in reached for k, ok in criteria[st] if not ok]
    if missing:
        errors.append(tr("check.agent_stage", where=where, level=stage["level"],
                         missing=", ".join(missing)))
    return errors


# What a decision or an artifact may depend on: facts (zones, data sources), insights, decisions.
DEPENDS_ON = ["os_zone", "insight", "decision", "data_source"]


def check_decision(d, idx):
    """A business decision (README_operations.md §1.17): what it depends on, what was used to
    decide it, what it activates."""
    where = f"{d['_file']} {d.get('id')}"
    errors = check_keys("decision", d, where)
    errors += check_enum(where, "kind", d.get("kind"), "decision_kind")
    errors += check_enum(where, "state", d.get("state"), "state")
    errors += check_enum(where, "basis", d.get("basis"), "fact_basis")
    for field, kinds in (("zone", ["os_zone"]), ("decided_by", ["role"])):
        if d.get(field) is not None:
            errors += check_ref(where, field, d[field], idx, expected=kinds)
    for field, kinds in (("depends_on", DEPENDS_ON), ("decided_through", ["artifact", "task"]),
                         ("activates", ["product"])):
        for x in d.get(field) or []:
            errors += check_ref(where, field, x, idx, expected=kinds)
    if d.get("date") is not None and not DATE_RE.match(str(d["date"])):
        errors.append(tr("check.blocker_date", where=where, field="date", value=repr(d["date"])))
    warnings = [tr("warn.decision_no_source", where=where)] \
        if d.get("state") == "active" and not d.get("depends_on") else []
    return errors, warnings


def check_artifact(a, idx):
    """An artifact (README_operations.md §1.17): what it depends on and what it is made for —
    understand, share, or help decide (then the question its reviewer answers)."""
    where = f"{a['_file']} {a.get('id')}"
    errors = check_keys("artifact", a, where)
    errors += check_enum(where, "state", a.get("state"), "artifact_state")
    errors += check_enum(where, "basis", a.get("basis"), "fact_basis")
    if a.get("zone") is not None:
        errors += check_ref(where, "zone", a["zone"], idx, expected=["os_zone"])
    for field, kinds in (("depends_on", DEPENDS_ON), ("produced_by", ["tool", "task"])):
        for x in a.get(field) or []:
            errors += check_ref(where, field, x, idx, expected=kinds)
    p = a.get("purpose")
    if not isinstance(p, dict):
        errors.append(tr("check.purpose_shape", where=where))
    else:
        errors += check_enum(where, "purpose.goal", p.get("goal"), "artifact_goal")
        if not p.get("goal"):
            errors.append(tr("check.purpose_shape", where=where))
        if p.get("goal") == "decide" and not p.get("question"):
            errors.append(tr("check.purpose_question", where=where))
    if a.get("updated") is not None and not DATE_RE.match(str(a["updated"])):
        errors.append(tr("check.blocker_date", where=where, field="updated",
                         value=repr(a["updated"])))
    warnings = [tr("warn.artifact_no_source", where=where)] if not a.get("depends_on") else []
    return errors, warnings


# ---------------------------------------------------------------------- the data map

# What a container of the data map must never hold (README_operations.md §1.20): its structure
# says where the data is and how it is laid out, never a value of it. An e-mail address, a phone
# number or an amount in a name, a path, a naming pattern or a column name is a value.
CONTENT_PATTERNS = (
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("phone", re.compile(r"(?:\+\d{2}\s?|\b0)[1-9](?:[\s.-]?\d{2}){4}\b")),
    ("amount", re.compile(r"\d[\d\s\u202f.,]*\s?(?:€|k€|M€|\$|£|EUR|USD|euros?|dollars?)(?!\w)",
                          re.I)),
)
# The word of each kind of value, in the messages.
CONTENT_WORDS = {"email": "word.content_email", "phone": "word.content_phone",
                 "amount": "word.content_amount"}
CONTAINER_TEXTS = ("name", "path", "holds", "naming", "fields", "formats", "notes", "sources")
WRITERS = ["task", "tool", "agent"]


def container_content(c):
    """The values a container holds by mistake: (field, kind of value, excerpt)."""
    found = []
    items = c.get("items") if isinstance(c.get("items"), dict) else {}
    texts = [(f, c.get(f)) for f in CONTAINER_TEXTS] + [("items.unit", items.get("unit"))]
    for field, values in texts:
        for v in values if isinstance(values, list) else [values]:
            if v is None:
                continue
            for kind, pattern in CONTENT_PATTERNS:
                found += [(field, kind, m.group(0).strip()) for m in pattern.finditer(str(v))]
    return found


def check_container(c, idx):
    """A container of the data map (README_operations.md §1.20): a place of a tool where data is
    kept, with its structure and never its content."""
    where = f"{c['_file']} {c.get('id')}"
    errors = check_keys("container", c, where)
    errors += check_enum(where, "kind", c.get("kind"), "container_kind")
    errors += check_enum(where, "state", c.get("state"), "container_state")
    errors += check_enum(where, "basis", c.get("basis"), "fact_basis")
    for field, kinds in (("tool", ["tool"]), ("data", ["data_source"]), ("parent", ["container"]),
                         ("owner", ["role"]), ("duplicate_of", ["container"])):
        if c.get(field) is not None:
            errors += check_ref(where, field, c[field], idx, expected=kinds)
    for field in ("written_by", "read_by"):
        for x in c.get(field) or []:
            errors += check_ref(where, field, x, idx, expected=WRITERS)
    for x in c.get("sensitivity") or []:
        errors += check_enum(where, "sensitivity", x, "sensitivity")
    access = c.get("access") if isinstance(c.get("access"), dict) else {}
    errors += check_enum(where, "access.connector", access.get("connector"), "connector")
    errors += check_enum(where, "access.state", access.get("state"), "access_state")
    fresh = c.get("freshness") if isinstance(c.get("freshness"), dict) else {}
    for field in ("last_modified", "checked"):
        if fresh.get(field) is not None and not DATE_RE.match(str(fresh[field])):
            errors.append(tr("check.blocker_date", where=where, field=f"freshness.{field}",
                             value=repr(fresh[field])))
    counts = [("items.count", (c.get("items") or {}).get("count")
               if isinstance(c.get("items"), dict) else None),
              ("freshness.modified_90d", fresh.get("modified_90d"))]
    activity = c.get("activity") if isinstance(c.get("activity"), dict) else {}
    counts += [(f"activity.{k}", activity.get(k)) for k in ("editors_90d", "viewers_90d")]
    for field, value in counts:
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)
                                  or value < 0):
            errors.append(tr("check.container_count", where=where, field=field,
                             value=repr(value)))
    if c.get("url") is not None and not str(c["url"]).startswith("https://"):
        errors.append(tr("check.container_url", where=where, value=repr(c["url"])))
    errors += [tr("check.container_content", where=where, field=field,
                  kind=tr(CONTENT_WORDS[kind]), value=excerpt)
               for field, kind, excerpt in container_content(c)]
    warnings = []
    if c.get("state", "active") == "active" and not (c.get("written_by") or c.get("owner")):
        warnings.append(tr("warn.container_no_writer", where=where))
    return errors, warnings


def check_container_tree(ref):
    """A container is not its own ancestor, and sits in the tool of its parent."""
    by_id = {c.get("id"): c for c in ref["containers"]}
    errors = []
    for c in ref["containers"]:
        seen, x = set(), c
        while isinstance(x, dict) and x.get("parent"):
            if x["parent"] in seen or x["parent"] == c.get("id"):
                errors.append(tr("check.container_cycle", where=f"{c['_file']} {c.get('id')}"))
                break
            seen.add(x["parent"])
            x = by_id.get(x["parent"])
        parent = by_id.get(c.get("parent"))
        if parent and parent.get("tool") != c.get("tool"):
            errors.append(tr("check.container_parent_tool", where=f"{c['_file']} {c.get('id')}",
                             parent=parent.get("id"), tool=parent.get("tool")))
    return errors


def container_age(c, today=None):
    """Days between the last change of a container and the date it was checked (else today)."""
    fresh = c.get("freshness") if isinstance(c.get("freshness"), dict) else {}
    try:
        last = datetime.date.fromisoformat(str(fresh.get("last_modified")))
    except ValueError:
        return None
    try:
        ref_day = datetime.date.fromisoformat(str(fresh.get("checked")))
    except ValueError:
        ref_day = today or datetime.date.today()
    return max(0, (ref_day - last).days)


def link_containers(ref, idx):
    """Each container gets who keeps it and who uses it (README_operations.md §1.20): the tasks
    that write it and read it, the roles that own it (its `owner`, else the roles of the tasks
    that write it) and their holders, the active tasks that reach its data in its tool without
    saying whether they write or read it (`candidates`), its age in days and whether it is
    fresh, recent, aging, old or stale (FRESHNESS, the scale of the zones of the OS), unknown
    without a date. Each data source gets the
    containers that hold it."""
    tasks = {t["id"]: t for t in ref["tasks"]}
    roles = {r["id"]: r for r in ref["roles"]}
    children = {}
    for c in ref["containers"]:
        children.setdefault(c.get("parent"), []).append(c.get("id"))
    for c in ref["containers"]:
        writers = [resolve(idx, x) for x in c.get("written_by") or []]
        readers = [resolve(idx, x) for x in c.get("read_by") or []]
        owners = [c["owner"]] if c.get("owner") else []
        for x in writers:
            role = (tasks.get(x) or {}).get("role")
            if role and role not in owners:
                owners.append(role)
        holders = []
        for r in owners:
            for h in (roles.get(r) or {}).get("holders") or []:
                name = human_name(h)
                if is_person(name) and name not in holders:
                    holders.append(name)
        known = set(writers) | set(readers)
        c["_writers"], c["_readers"], c["_owners"], c["_holders"] = writers, readers, owners, holders
        c["_candidates"] = [x for x in datamap_candidates(ref, c) if x not in known]
        c["_children"] = children.get(c.get("id"), [])
        age = container_age(c)
        c["_age"] = age
        c["_fresh"] = "unknown" if age is None else freshness_level(age)
    for d in ref["data_sources"]:
        d["_containers"] = [c["id"] for c in ref["containers"] if c.get("data") == d.get("id")]


def path_key(c):
    """A container's place in its tool, written the same way whatever the case, the slashes and
    the placeholders: « Clients/[Client]/2. Propositions/ » and « clients/[client]/2. propositions »
    are one place."""
    path = re.sub(r"\[[^\]]*\]", "[]", str(c.get("path") or c.get("name") or "")).lower()
    return (c.get("tool"), re.sub(r"\s+", " ", path.strip("/ ")))


def datamap_plan(existing, incoming):
    """For each container of a crawl, the container of the data map it is (same url, else same
    tool and path) or `None` for a new one (README_operations.md §1.20, merge)."""
    by_url = {c.get("url"): c for c in existing if c.get("url")}
    by_path = {path_key(c): c for c in existing}
    return [(c, (by_url.get(c["url"]) if c.get("url") else None) or by_path.get(path_key(c)))
            for c in incoming]


DATAMAP_FRESHNESS = ("fresh", "recent", "aging", "old", "stale", "unknown")


def datamap_stats(ref):
    """Figures of the data map: containers, by tool and by freshness, those without an owner,
    the data sources that have containers."""
    live = [c for c in ref["containers"] if c.get("state", "active") == "active"]
    tools = {}
    for c in live:
        tools[c.get("tool")] = tools.get(c.get("tool"), 0) + 1
    return {"containers": len(live),
            "tools": dict(sorted(tools.items(), key=lambda kv: -kv[1])),
            "fresh": {k: sum(1 for c in live if c.get("_fresh") == k)
                      for k in DATAMAP_FRESHNESS},
            "owned": sum(1 for c in live if c.get("_owners")),
            "sources": sum(1 for d in ref["data_sources"] if d.get("_containers")),
            "all_sources": len(ref["data_sources"])}


def okr_ids(idx):
    return {k for k, v in idx.items() if isinstance(v, dict) and "_okr" in v}


def check_task_okrs(t, where, idx, check_ids=True):
    """The key results a task contributes to (README_operations.md §1.13): ids `O…KRn` of
    okrs.yaml. Without a catalogue of OKRs (a mapping checked away from OS/Operations), only
    their form is checked. More than two: the link is probably too loose."""
    values = t.get("okrs") or []
    if not isinstance(values, list):
        return [tr("check.okrs_not_list", where=where)], []
    errors = [tr("check.okrs_bad_id", where=where, value=repr(v))
              for v in values if not isinstance(v, str) or not ID_RE["key_result"].match(v)]
    if check_ids:
        errors += [tr("check.kr_unknown", where=where, kr=v) for v in values
                   if isinstance(v, str) and ID_RE["key_result"].match(v)
                   and "_okr" not in (idx.get(v) or {})]
    warnings = [tr("warn.too_many_krs", where=where, count=len(values))] \
        if len(values) > 2 else []
    return errors, warnings


def okr_ancestors(okr_id, idx):
    """The objectives above `okr_id`, nearest first; stops at a loop."""
    seen = []
    while okr_id and okr_id not in seen:
        seen.append(okr_id)
        okr_id = (idx.get(okr_id) or {}).get("parent")
    return seen


def check_okr(o, idx, teams):
    """An objective: its keys, level, parent (an objective, never itself), teams and owner, and
    its key results (README_operations.md §1.13)."""
    where = f"{o['_file']} {o.get('id')}"
    errors = check_keys("okr", o, where) + check_enum(where, "level", o.get("level"), "okr_level")
    errors += check_enum(where, "state", o.get("state"), "state")
    parent = o.get("parent")
    if parent is not None and (parent == o.get("id") or (idx.get(parent) or {}).get("_file") is None
                               or not ID_RE["okr"].match(str(parent))):
        errors.append(tr("check.okr_parent", where=where, value=repr(parent)))
    elif parent is not None and o.get("id") in okr_ancestors(parent, idx):
        errors.append(tr("check.okr_loop", where=where, value=repr(parent)))
    errors += [tr("check.team_unknown", where=where, team=x) for x in o.get("teams") or []
               if teams and x not in teams]
    if o.get("owner") is not None:
        errors += check_ref(where, "owner", o.get("owner"), idx, expected=["role"])
    krs = [k for k in o.get("key_results") or [] if isinstance(k, dict)]
    for kr in krs:
        errors += check_key_result(kr, o, where, idx)
    shared = o.get("shared_key_results") or []
    errors += [tr("check.shared_kr", where=where, kr=k) for k in shared
               if "_okr" not in (idx.get(k) or {}) or idx[k]["_okr"] == o.get("id")]
    warnings = [tr("warn.okr_without_kr", where=where)] if not krs and not shared else []
    warnings += [tr("warn.activity_kr", where=f"{where} {kr.get('id')}") for kr in krs
                 if kr.get("kind") == "activity"]
    return errors, warnings


def check_key_result(kr, o, where, idx):
    kr_where = f"{where} {kr.get('id')}"
    errors = [tr("check.required_missing", where=kr_where, key=k)
              for k in ("id", "name", "unit", "direction", "target", "per") if k not in kr]
    if not str(kr.get("id", "")).startswith(f"{o.get('id')}.KR") \
            or not ID_RE["key_result"].match(str(kr.get("id", ""))):
        errors.append(tr("check.kr_id", where=kr_where, okr=o.get("id")))
    for field, enum in (("unit", "kr_unit"), ("direction", "kr_direction"), ("per", "kr_per"),
                        ("kind", "kr_kind")):
        errors += check_enum(kr_where, field, kr.get(field), enum)
    for field in ("target", "baseline"):
        value = kr.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            errors.append(tr("check.not_a_number", where=kr_where, field=field, value=repr(value)))
    errors += [e for x in kr.get("data") or []
               for e in check_ref(kr_where, "data", x, idx, expected=["data_source"])]
    return errors


def check_type(t, where, type_ids):
    """The type of a task is a task type of the catalogue. Without a catalogue (a mapping
    checked by the skill, which does not ship task-types.yaml), only its form is checked."""
    value = t.get("type")
    if value is None:
        return []
    if not isinstance(value, str) or not ID_RE["task_type"].match(value):
        return [tr("check.type_bad", where=where, value=repr(value))]
    if type_ids and value not in type_ids:
        return [tr("check.type_unknown", where=where, value=value)]
    return []


def check_relevance(t, where):
    rel = t.get("relevance")
    if rel is None:
        return []
    if not isinstance(rel, dict):
        return [tr("check.relevance_not_mapping", where=where, value=repr(rel),
                   axes=", ".join(RELEVANCE_AXES))]
    retired = [tr("check.axis_retired", where=where, axis=axis, why=tr(why))
               for axis, why in RELEVANCE_RETIRED.items() if axis in rel]
    return retired + [tr("check.axis_value", where=where, field=f"relevance.{axis}",
                         value=repr(rel[axis]))
                      for axis in RELEVANCE_AXES
                      if rel.get(axis) is not None and axis_value(rel[axis]) is None]


def positive(value):
    """A number above 0 (True is not a number)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def check_measure(t, where):
    """`measure: {minutes, runs, basis}`: minutes per run and runs per month, for one person."""
    m = t.get("measure")
    if m is None:
        return []
    if not isinstance(m, dict):
        return [tr("check.measure_not_mapping", where=where, value=repr(m))]
    errors = [tr("check.positive", where=where, key=k, value=repr(m.get(k)))
              for k in ("minutes", "runs") if m.get(k) is not None and not positive(m.get(k))]
    return errors + check_enum(where, "measure.basis", m.get("basis"), "basis")


def check_queue(t, where):
    """`queue: {count, unit, at, basis, source}`: how much waits at the input of the task on the
    date `at` (198 tickets merged and not tested on 2026-10-17), read where `source` says."""
    q = t.get("queue")
    if q is None:
        return []
    if not isinstance(q, dict):
        return [tr("check.queue_shape", where=where, value=repr(q))]
    count = q.get("count")
    errors = [] if isinstance(count, (int, float)) and not isinstance(count, bool) and count >= 0 \
        else [tr("check.queue_count", where=where, value=repr(count))]
    if not (isinstance(q.get("at"), str) and DOC_DATE.fullmatch(q["at"])):
        errors.append(tr("check.queue_at", where=where, value=repr(q.get("at"))))
    return errors + check_enum(where, "queue.basis", q.get("basis"), "basis")


def check_stakes(t, where):
    """`stakes: {level, text}`: what happens when the task is late or wrong, 1 to 3."""
    st = t.get("stakes")
    if st is None:
        return []
    if not isinstance(st, dict):
        return [tr("check.stakes_not_mapping", where=where, value=repr(st))]
    level = st.get("level")
    return [] if level is None or axis_value(level) else \
        [tr("check.axis_value", where=where, field="stakes.level", value=repr(level))]


JOB_LEADS = {"when": ("quand ", "when "), "so_that": ("pour que ", "pour qu'", "so that ")}


def check_job(t, where):
    """`job: {when, so_that}`: the situation that starts the task and the result it is for, each
    a non-empty text without its leading words (« Quand », « pour que »), which the views add."""
    j = t.get("job")
    if j is None:
        return []
    if not isinstance(j, dict):
        return [tr("check.job_not_mapping", where=where, value=repr(j))]
    errors = [tr("check.unknown_field", where=where, key=f"job.{k}") for k in j
              if k not in SUB_KEYS["job"]]
    for k in SUB_KEYS["job"]:
        v = j.get(k)
        if not isinstance(v, str) or not v.strip():
            errors.append(tr("check.job_part", where=where, key=k))
        elif v.strip().lower().startswith(JOB_LEADS[k]):
            errors.append(tr("check.job_lead", where=where, key=k, value=v.split()[0]))
    return errors


def check_build(t, where):
    """`build: {size, kind}`: the work to bring the task to its target."""
    b = t.get("build")
    if b is None:
        return []
    if not isinstance(b, dict):
        return [tr("check.build_not_mapping", where=where, value=repr(b))]
    return check_enum(where, "build.size", b.get("size"), "build_size") + \
        check_enum(where, "build.kind", b.get("kind"), "build_kind")


def check_sensitivity(d, where):
    """`sensitivity`: what a data source holds, among the categories of §1.8 ([] : internal)."""
    s = d.get("sensitivity")
    if s is None:
        return []
    if not isinstance(s, list):
        return [tr("check.sensitivity_not_list", where=where, value=repr(s),
                   values=sorted(ENUMS["sensitivity"]))]
    return [e for x in s for e in check_enum(where, "sensitivity", x, "sensitivity")]


def check_basis(kind, item, where):
    """`basis: {field: observed | declared | inferred}`: how each fact is known (§1.9). A key
    is a field of the element, or `field.sub` for a field made of sub-fields."""
    b = item.get("basis")
    if b is None:
        return []
    if not isinstance(b, dict):
        return [tr("check.basis_not_mapping", where=where, value=repr(b))]
    errors = []
    for key, value in b.items():
        field, _, sub = str(key).partition(".")
        if field not in KEYS[kind] or field in BASIS_EXCLUDED or \
                (sub and sub not in SUB_KEYS.get(field, ())):
            errors.append(tr("check.basis_field", where=where, key=key))
        errors += check_enum(where, f"basis.{key}", value, "fact_basis")
    return errors


def check_method(t, where, idx):
    """`method`: where the written method of the task lives, a URL or a tool of the catalogue."""
    m = t.get("method")
    if m is None:
        return []
    if isinstance(m, str) and re.match(r"https?://\S+$", m):
        return []
    if kind_of_id(m) == "tool":
        return check_ref(where, "method", m, idx, expected=["tool"])
    return [tr("check.method", where=where, value=repr(m))]


URL_RE = re.compile(r"https?://\S+$")


def check_files(t, where, idx):
    """`output_files`: each entry a fixed file (`kind: file`, its `url`) or the folder where the
    file of each run goes (`kind: folder`, its `url` and/or the `pattern` of the path and name,
    placeholders in brackets: « Clients/[Client]/kickoff-[AAAA-MM-JJ].pptx »). `templates`: the
    files the deliverable starts from, a URL or a tool of the catalogue. `tool`: where the file
    lives, a tool of the catalogue (README_operations.md §1.12)."""
    errors = []
    for i, f in enumerate(t.get("output_files") or []):
        at = f"{where} output_files[{i}]"
        if not isinstance(f, dict):
            errors.append(tr("check.files_not_mapping", where=at))
            continue
        errors += check_enum(at, "kind", f.get("kind"), "output_kind")
        if not f.get("kind"):
            errors.append(tr("check.files_kind_missing", where=at))
        if f.get("url") is not None and not (isinstance(f["url"], str) and URL_RE.match(f["url"])):
            errors.append(tr("check.url", where=at, value=repr(f["url"])))
        if f.get("kind") == "file" and not f.get("url"):
            errors.append(tr("check.file_needs_url", where=at))
        if not f.get("url") and not f.get("pattern"):
            errors.append(tr("check.url_or_pattern", where=at))
        errors += check_ref(at, "tool", f.get("tool"), idx, expected=["tool"]) \
            if f.get("tool") else []
    for i, x in enumerate(t.get("templates") or []):
        at = f"{where} templates[{i}]"
        url = x.get("url") if isinstance(x, dict) else None
        if not url:
            errors.append(tr("check.template_not_mapping", where=at))
        elif not URL_RE.match(str(url)) and kind_of_id(url) != "tool":
            errors.append(tr("check.template_url", where=at, value=repr(url)))
        elif kind_of_id(url) == "tool":
            errors += check_ref(at, "url", url, idx, expected=["tool"])
        if isinstance(x, dict) and x.get("tool"):
            errors += check_ref(at, "tool", x["tool"], idx, expected=["tool"])
    return errors


def check_handoffs(p, where, idx):
    """`handoffs: [{to, what, via, issues}]`: who takes over the work after the process (a
    process or a role, of another team most often), what is handed over, through which tool or
    data source, and what goes wrong there (§1.10)."""
    hs = p.get("handoffs")
    if hs is None:
        return []
    if not isinstance(hs, list):
        return [tr("check.handoffs_not_list", where=where, value=repr(hs))]
    errors = []
    for h in hs:
        if not isinstance(h, dict):
            errors.append(tr("check.handoff_not_mapping", where=where, value=repr(h)))
            continue
        errors += [tr("check.handoff_missing", where=where, key=k)
                   for k in ("to", "what") if not h.get(k)]
        if h.get("to"):
            errors += check_ref(where, "handoffs.to", h["to"], idx)
        if h.get("via"):
            errors += check_ref(where, "handoffs.via", h["via"], idx,
                                expected=["tool", "data_source"])
    return errors


def check_policy(ref, idx):
    """`ai_policy`: one rule per category of §1.8 (`internal` for internal data only)."""
    policy = ref.get("ai_policy")
    if not policy:
        return [], []
    where = f"{policy['_file']} ai_policy"
    errors = [tr("check.unknown_field", where=where, key=k) for k in policy
              if not k.startswith("_") and k not in POLICY_KEYS]
    rules = policy.get("rules") or {}
    if not isinstance(rules, dict):
        return errors + [tr("check.rules_not_mapping", where=where, value=repr(rules))], []
    errors += [tr("check.rules_category", where=where, key=k, values=list(SENSITIVITY_ORDER))
               for k in rules if k not in SENSITIVITY_ORDER]
    errors += [e for k, v in rules.items() for e in check_enum(where, f"rules.{k}", v, "ai_rule")]
    errors += [tr("check.tool_unknown", where=where, tool=x) for x in policy.get("tools") or []
               if x not in idx]
    used = {c for d in ref["data_sources"] for c in d.get("sensitivity") or ["internal"]
            if d.get("sensitivity") is not None}
    warnings = [tr("warn.no_rule", where=where, category=c)
                for c in SENSITIVITY_ORDER if c in used and not rules.get(c)]
    return errors, warnings


def check_investment(ref, idx):
    """`ai_investment`: cost_ratio {amount, currency, minutes} (5 euros for 30 minutes of human
    work), enforced true or false, budget {amount, currency, period}."""
    inv = ref.get("ai_investment")
    if not inv:
        return []
    where = f"{inv['_file']} ai_investment"
    errors = [tr("check.unknown_field", where=where, key=k) for k in inv
              if not k.startswith("_") and k not in INVESTMENT_KEYS]
    for key, keys in AMOUNT_KEYS.items():
        v = inv.get(key)
        if v is None:
            continue
        if not isinstance(v, dict) or not positive(v.get("amount")):
            errors.append(tr("check.amount", where=where, key=key, value=repr(v),
                             keys=", ".join(keys)))
            continue
        errors += [tr("check.sub_unknown_field", where=where, sub=key, key=k) for k in v
                   if k not in keys]
    ratio = inv.get("cost_ratio")
    if isinstance(ratio, dict) and not positive(ratio.get("minutes")):
        errors.append(tr("check.cost_minutes", where=where, value=repr(ratio.get("minutes"))))
    if inv.get("enforced") is not None and not isinstance(inv["enforced"], bool):
        errors.append(tr("check.enforced", where=where, value=repr(inv["enforced"])))
    errors += check_enum(where, "basis", inv.get("basis"), "fact_basis")
    return errors


def effort_from_minutes(minutes):
    return next((rating for limit, rating in EFFORT_BY_MINUTES if minutes <= limit), 3)


def measure_warnings(t, where):
    """A measured duration that contradicts the effort rating: the measure decides."""
    m = t.get("measure") if isinstance(t.get("measure"), dict) else {}
    rel = t.get("relevance") if isinstance(t.get("relevance"), dict) else {}
    effort = axis_value(rel.get("effort"))
    if not (positive(m.get("minutes")) and effort):
        return []
    expected = effort_from_minutes(m["minutes"])
    return [] if expected == effort else \
        [tr("warn.measure_effort", where=where, minutes=m["minutes"], expected=expected,
            effort=effort)]


def axis_value(value):
    """A relevance axis as 1, 2 or 3; None for null or anything else (True is not 1)."""
    return value if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 3 \
        else None


def relevance_score(t):
    """(P + F + E + D) × R, 0 to 36: an unknown axis adds 0 to the sum, an unknown payback
    multiplies by 1."""
    rel = t.get("relevance") if isinstance(t.get("relevance"), dict) else {}
    base = sum(axis_value(rel.get(axis)) or 0 for axis in RELEVANCE_BASE)
    return base * (axis_value(rel.get(RELEVANCE_FACTOR)) or 1)


def runs_per_month(t):
    """(runs per month, True when read from the `frequency` text), or (None, False)."""
    text = str(t.get("frequency") or "").lower().replace("’", "'")
    rate = RATE_RE.search(text)
    if rate:
        count = COUNT_WORDS.get(rate.group(1)) or float(rate.group(1).replace(",", "."))
        return count * PER_MONTH[rate.group(2)], True
    every_n = EVERY_N_RE.search(text)
    if every_n:
        n = COUNT_WORDS.get(every_n.group(1)) or float(every_n.group(1))
        return PER_MONTH[every_n.group(2)] / n, True
    every = EVERY_RE.search(text)
    if every:
        return PER_MONTH.get(every.group(1), PER_MONTH["semaine"]), True
    english = runs_per_month_en(text)
    if english:
        return english, True
    rel = t.get("relevance") if isinstance(t.get("relevance"), dict) else {}
    frequency = axis_value(rel.get("frequency"))
    return (GAIN_RUNS[frequency], False) if frequency else (None, False)


def runs_per_month_en(text):
    """Runs per month read from a `frequency` text written in English, None without a rate."""
    rate = RATE_EN_RE.search(text)
    if rate:
        count = COUNT_WORDS_EN.get(rate.group(1)) or float(rate.group(1).replace(",", "."))
        return count * PER_MONTH_EN[rate.group(2)]
    every_n = EVERY_N_EN_RE.search(text)
    if every_n:
        n = COUNT_WORDS_EN.get(every_n.group(1)) or float(every_n.group(1))
        return PER_MONTH_EN[every_n.group(2)] / n
    every = EVERY_EN_RE.search(text)
    return PER_MONTH_EN[every.group(1)] if every else None


def run_numbers(t):
    """(runs per month, hours per run, True when the runs come from the `frequency` text) of a
    task, whatever its status; None when the frequency or the effort is unknown. A measure
    (`measure.minutes`, `measure.runs`) replaces the ratings and the frequency text."""
    m = t.get("measure") if isinstance(t.get("measure"), dict) else {}
    rel = t.get("relevance") if isinstance(t.get("relevance"), dict) else {}
    effort = axis_value(rel.get("effort"))
    run_hours = m["minutes"] / 60 if positive(m.get("minutes")) else GAIN_HOURS.get(effort)
    if positive(m.get("runs")):
        runs, from_text = m["runs"], False
    else:
        runs, from_text = runs_per_month(t)
    return (runs, run_hours, from_text) if runs and run_hours else None


def task_gain(t):
    """Hours a person gets back per month when the task reaches its target, with the numbers it
    comes from; None for an A or J task, or when the frequency or the effort is unknown."""
    status, target = t.get("status"), t.get("target")
    if STATUS_RANK.get(target, -1) <= STATUS_RANK.get(status, 9):
        target = "A"
    share, numbers = GAIN_SHARE.get((status, target)), run_numbers(t)
    if not (share and numbers):
        return None
    runs, run_hours, from_text = numbers
    gain = {"hours": round(runs * run_hours * share, 1), "runs": round(runs, 2),
            "run_hours": round(run_hours, 2), "share": share, "target": target,
            "from_text": from_text}
    m = t.get("measure") if isinstance(t.get("measure"), dict) else {}
    if positive(m.get("minutes")) or positive(m.get("runs")):
        gain["basis"] = m.get("basis") or "declared"
    return gain


def check_orphans(ref):
    used = {x for t in ref["tasks"] + ref["processes"] for x in t.get("tools") or []}
    # A skill that brings data into a zone of the OS is in use (README_operations.md §1.15).
    used |= {f.get(k) for z in ref["os_zones"] for f in z.get("feeds") or []
             if isinstance(f, dict) for k in ("tool", "skill")}
    # So is a skill or a platform a recurring agent runs (§1.16).
    used |= {x for a in ref["agents"] for x in (a.get("skills") or []) + [a.get("platform")]}
    # And a skill that produces an artifact (§1.17).
    used |= {x for a in ref["artifacts"] for x in a.get("produced_by") or []}
    idx = index(ref)
    cited = {resolve(idx, x) for t in ref["tasks"] for x in t.get("data") or []}
    return [tr("warn.tool_unused", where=f"{t['_file']} {t['id']}")
            for t in ref["tools"]
            if t.get("id") not in used and t.get("type") == "skill" and not t.get("_borrowed")] + \
        [tr("warn.source_unused", where=f"{d['_file']} {d['id']}")
         for d in ref["data_sources"] if d.get("id") not in cited and not d.get("_borrowed")]


# ------------------------------------------------------------------------ computed view

def resolve(idx, value):
    """Canonical id of an id or alias."""
    item = idx.get(value)
    return item.get("id") if item else value


def enrich(ref):
    """Add computed fields: effective departments, processes of each task, step statuses."""
    idx = index(ref)
    roles = {r["id"]: r for r in ref["roles"]}
    member = {}
    for p in ref["processes"]:
        p["_depts"] = p.get("departments") or roles.get(p["role"], {}).get("departments", [])
        p["_steps"] = [resolve(idx, s) for s in p.get("steps") or []]
        if p.get("state") != "retired":
            for step in p["_steps"]:
                member.setdefault(step, []).append(p["id"])
    sources = {d["id"]: d for d in ref["data_sources"]}
    for t in ref["tasks"]:
        t["_depts"] = t.get("departments") or roles.get(t["role"], {}).get("departments", [])
        t["_processes"] = member.get(t["id"], [])
        t["_score"] = relevance_score(t)
        t["_gain"] = task_gain(t)
        t["_data_links"] = data_links(t, sources, idx)
        t["_ai"] = ai_view(t, sources, ref.get("ai_policy"), idx)
    ref["_chains"] = link_chains(ref, idx)
    link_containers(ref, idx)
    link_blockers(ref, idx)
    link_os(ref, idx)
    link_people(ref)
    link_decisions(ref)
    return ref


def process_links(ref, idx):
    """The order of the active processes (README_operations.md §1.19): p comes before q when p
    names q in `next`, when q is triggered by a task of p (`trigger.by`), or when a handoff of p
    goes to q. Pairs (p, q), each once."""
    live = {p["id"]: p for p in ref["processes"] if p.get("state") == "active"}
    owner = {}
    for p in live.values():
        for step in p["_steps"]:
            owner.setdefault(step, []).append(p["id"])
    pairs = []
    for q in live.values():
        for nxt in q.get("next") or []:
            pairs.append((q["id"], resolve(idx, nxt)))
        for by in (q.get("trigger") or {}).get("by") or []:
            pairs += [(p, q["id"]) for p in owner.get(resolve(idx, by), [])]
        for h in q.get("handoffs") or []:
            if isinstance(h, dict) and resolve(idx, h.get("to")) in live:
                pairs.append((q["id"], resolve(idx, h["to"])))
    seen, out = set(), []
    for a, b in pairs:
        if a in live and b in live and a != b and (a, b) not in seen:
            seen.add((a, b))
            out.append((a, b))
    return live, out


def process_ranks(ids, pairs):
    """The rank of each process in its chain: the longest path from a process nothing comes
    before. A loop (a ticket sent back to an earlier step) is cut where it closes: a depth-first
    walk from the heads drops the links that go back to a process still on the walk."""
    succ, preds = {i: [] for i in ids}, {i: 0 for i in ids}
    for a, b in pairs:
        succ[a].append(b)
        preds[b] += 1
    for i in ids:
        succ[i].sort()
    heads = [i for i in ids if not preds[i]] + [i for i in ids if preds[i]]
    state, order, kept = {}, [], set()
    for h in heads:
        if h in state:
            continue
        state[h] = 1
        stack = [(h, iter(succ[h]))]
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                state[node] = 2
                order.append(node)
                stack.pop()
            elif state.get(nxt) != 1:
                kept.add((node, nxt))
                if nxt not in state:
                    state[nxt] = 1
                    stack.append((nxt, iter(succ[nxt])))
    rank = {i: 0 for i in ids}
    for node in reversed(order):
        for nxt in succ[node]:
            if (node, nxt) in kept:
                rank[nxt] = max(rank[nxt], rank[node] + 1)
    return rank


def task_hours(t):
    """Hours a month people spend on a task (runs × hours per run), 0 for an automated task,
    None when the frequency or the effort is unknown."""
    if t.get("status") == "A":
        return 0
    numbers = run_numbers(t)
    return round(numbers[0] * numbers[1], 1) if numbers else None


def task_flow(t, crew=1):
    """How fast work goes through a task (README_operations.md §1.19): the hours of a run
    (`run`), the runs a month for one person (`runs`), and when a stock is measured at its input
    (`queue`), the days that stock waits at the pace of the task (`wait_days`: count ÷ (runs a
    month × the people who do it) × 30.4): two people who each do 40 a month empty the queue at
    80 a month."""
    out, numbers, q = {}, run_numbers(t), t.get("queue")
    if numbers:
        out["runs"], out["run"] = round(numbers[0], 2), round(numbers[1], 2)
    if isinstance(q, dict) and isinstance(q.get("count"), (int, float)):
        out["queue"] = {k: q[k] for k in ("count", "unit", "at", "basis", "source") if k in q}
        # The pace needs the runs only: a task measured in runs without a duration has one.
        m = t.get("measure") if isinstance(t.get("measure"), dict) else {}
        runs = out.get("runs") or (m["runs"] if positive(m.get("runs")) else runs_per_month(t)[0])
        if runs:
            out["wait_days"] = round(q["count"] / (runs * crew) * 30.4)
    return out


def link_chains(ref, idx):
    """The chains of production (README_operations.md §1.19): the active processes that follow
    one another, each chain from the process nothing comes before to the last one. A chain
    gets its processes with their rank, its tasks in order with their hours, the volume that
    enters it, the task where full automation starts (the first one not automated), and its
    balance: the hours of its heaviest task over its lightest one. Each task gets its place in
    its chain and its priority (score × the upstream factor when its target is A)."""
    live, pairs = process_links(ref, idx)
    ids = sorted(live)
    group = {i: i for i in ids}

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for a, b in pairs:
        group[root(a)] = root(b)
    rank = process_ranks(ids, pairs)
    tasks = {t["id"]: t for t in ref["tasks"]}
    members = {}
    for i in ids:
        members.setdefault(root(i), []).append(i)
    chains = []
    for procs in members.values():
        procs.sort(key=lambda i: (rank[i], i))
        chains.append(chain_view(procs, live, rank, pairs, tasks, role_people(ref)))
    chains.sort(key=lambda c: (-len(c["processes"]), -(c["hours"] or 0), c["id"]))
    for t in ref["tasks"]:
        t["_priority"] = t["_score"]
    for c in chains:
        last = max((x["at"] for x in c["tasks"]), default=0) or 1
        for x in c["tasks"]:
            t = tasks[x["id"]]
            if t.get("_chain") and t["_chain"]["at"] <= x["at"]:
                continue
            upstream = 1 - x["at"] / last
            full = (t.get("_gain") or {}).get("target") == "A"
            t["_chain"] = {"chain": c["id"], "at": x["at"], "upstream": round(upstream, 2)}
            t["_priority"] = round(t["_score"] * (1 + UPSTREAM_WEIGHT * upstream), 1) \
                if full else t["_score"]
    return chains


def chain_view(procs, live, rank, pairs, tasks, names=frozenset()):
    """One chain: its processes in order, its tasks with their place (`at`, the rank of their
    process plus their place among its steps), hours and status, the volume entering its first
    process, where full automation starts, its balance, and the task whose measured stock
    waits the longest (`stock`)."""
    head = procs[0]
    inside = set(procs)
    steps, seen = [], set()
    for i in procs:
        p = live[i]
        n = len(p["_steps"]) or 1
        for j, step in enumerate(p["_steps"]):
            t = tasks.get(step)
            if not t or step in seen or t.get("state") != "active":
                continue
            seen.add(step)
            steps.append(dict({"id": step, "process": i, "at": round(rank[i] + j / n, 3),
                               "status": t.get("status"), "hours": task_hours(t)},
                              **task_flow(t, people(t, names))))
    known = [x["hours"] for x in steps if x["hours"]]
    volume = (live[head].get("trigger") or {}).get("volume")
    start = next((x["id"] for x in steps if x["status"] != "A"), None)
    queued = [x for x in steps if x.get("queue")]
    return {"id": head, "name": live[head].get("name"),
            "processes": [{"id": i, "rank": rank[i]} for i in procs],
            "links": [[a, b] for a, b in pairs if a in inside and b in inside],
            "volume": {k: volume[k] for k in ("count", "kind", "unit") if k in volume}
            if isinstance(volume, dict) and positive(volume.get("count"))
            and volume.get("kind") in VOLUME_KINDS else None,
            "tasks": steps, "start": start,
            "hours": round(sum(known), 1) if known else None,
            "bottleneck": max(steps, key=lambda x: x["hours"] or 0)["id"] if known else None,
            "imbalance": round(max(known) / min(known), 1) if len(known) > 1 else None,
            "unmeasured": sum(1 for x in steps if x["hours"] is None),
            "stock": max(queued, key=lambda x: (x.get("wait_days") or 0, x["queue"]["count"]))["id"]
            if queued else None}


ACCESS_RANK = {"works": 0, "unchecked": 1, "not_found": 2}
# Rates used to estimate the cost of a run of an agent billed on the API, in USD
# (platform.claude.com/docs/en/about-claude/pricing, read on 2026-10-13): input and output per
# million tokens, a web search, an hour of Managed Agents session runtime.
MODEL_PRICES = {"claude-fable-5-1": (10.0, 50.0), "claude-opus-5-5": (4.0, 20.0),
                "claude-opus-5": (5.0, 25.0), "claude-sonnet-5-5": (2.0, 10.0),
                "claude-sonnet-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50),
                "claude-haiku-4-5": (1.0, 5.0)}
WEB_SEARCH_PRICE = 0.01
SESSION_HOUR_PRICE = 0.08


def agent_criteria(a):
    """The criteria of each stage that the files show (§1.16), as (key, met) pairs. The others
    (runs without repair, lightest model, messages written for the reader) are attested by
    `stage.evidence`."""
    c = a.get("cost") if isinstance(a.get("cost"), dict) else {}
    notify = [n for n in a.get("notify") or [] if isinstance(n, dict)] \
        if isinstance(a.get("notify"), list) else []
    measured = c.get("billing") == "subscription" or \
        (c.get("per_run") is not None and bool(c.get("measured")))
    return {"functional": [("live", a.get("state") == "live"), ("tasks", bool(a.get("tasks")))],
            "efficient": [("cost_measured", measured), ("config", bool(a.get("config"))),
                          ("log", bool(a.get("log")))],
            "refined": [("slack", any(n.get("channel") == "slack" for n in notify)),
                        ("recap", any(n.get("channel") == "email" and n.get("when") in RECAP_WHEN
                                      for n in notify)),
                        ("failure", any(n.get("when") in ("failure", "run") for n in notify))]}


def agent_progress(a):
    """Where an agent stands (§1.16): its declared stage, the criteria of every stage, the next
    stage and what it misses to reach it."""
    stage = a.get("stage") if isinstance(a.get("stage"), dict) else {}
    level = stage.get("level") if stage.get("level") in AGENT_STAGES else None
    criteria = agent_criteria(a)
    rank = AGENT_STAGES.index(level) + 1 if level else 0
    nxt = AGENT_STAGES[rank] if rank < len(AGENT_STAGES) else None
    return {"stage": level, "basis": stage.get("basis"), "checked": stage.get("checked"),
            "criteria": {k: [{"key": c, "ok": ok} for c, ok in v] for k, v in criteria.items()},
            "next": nxt, "missing": [c for c, ok in criteria[nxt] if not ok] if nxt else []}


def agent_cost(a):
    """Cost of a run and of a month of an agent (§1.16). A run billed through a subscription
    (a scheduled task of a person's Claude, a Routine) costs nothing more per run. On the API: the
    measured `per_run`, else tokens × the model's rates + web searches + session runtime (Managed
    Agents only). Runs per month: `cost.runs`, else read from `schedule`. None without data."""
    c = a.get("cost") if isinstance(a.get("cost"), dict) else {}
    runs = c.get("runs")
    if runs is None:
        runs, read = runs_per_month({"frequency": a.get("schedule")})
        runs = runs if read else None
    if c.get("billing") == "subscription":
        return {"billing": "subscription", "per_run": 0, "runs": runs, "per_month": 0,
                "currency": c.get("currency") or "USD", "estimated": False}
    per_run, estimated = c.get("per_run"), False
    if per_run is None and c.get("model") in MODEL_PRICES and (c.get("tokens_in") or
                                                              c.get("tokens_out")):
        price_in, price_out = MODEL_PRICES[c["model"]]
        per_run = ((c.get("tokens_in") or 0) * price_in + (c.get("tokens_out") or 0) * price_out) \
            / 1e6 + (c.get("web_searches") or 0) * WEB_SEARCH_PRICE
        if a.get("kind") == "managed-agent":
            per_run += (c.get("minutes") or 0) / 60 * SESSION_HOUR_PRICE
        estimated = True
    if per_run is None:
        return None
    return {"billing": c.get("billing") or "api", "per_run": round(per_run, 3), "runs": runs,
            "per_month": round(per_run * runs, 2) if runs is not None else None,
            "currency": c.get("currency") or "USD", "estimated": estimated}


def link_decisions(ref):
    """Business decisions and artifacts (README_operations.md §1.17), read both ways: each
    decision gets the decisions that depend on it (`_used_by`), the artifacts that share it
    (`_shared_by`: they depend on it) and the artifacts used to decide it; each artifact gets the
    decisions it helped decide (`_decides`); each zone and each insight, the decisions and the
    artifacts that depend on it."""
    for d in ref["decisions"]:
        d["_used_by"] = [x["id"] for x in ref["decisions"]
                         if d.get("id") in (x.get("depends_on") or [])]
        d["_shared_by"] = [a["id"] for a in ref["artifacts"]
                           if d.get("id") in (a.get("depends_on") or [])]
    for a in ref["artifacts"]:
        a["_decides"] = [d["id"] for d in ref["decisions"]
                         if a.get("id") in (d.get("decided_through") or [])]
    for x in ref["os_zones"] + ref["insights"]:
        x["_decisions"] = [d["id"] for d in ref["decisions"]
                           if x.get("id") in (d.get("depends_on") or [])
                           or (x.get("id") == d.get("zone"))]
        x["_artifacts"] = [a["id"] for a in ref["artifacts"]
                           if x.get("id") in (a.get("depends_on") or [])]


def first_name(name):
    return str(name or "").split(" ")[0].lower()


def names_person(people, x, name):
    """Whether `name` (a holder, a `by`) names the person `x` of people.yaml: their name (first and
    last name), one of their aliases, or their first name alone when no one else has it."""
    n = str(name or "").strip().lower()
    if n in {str(a).lower() for a in [x.get("name")] + all_aliases(x) if a}:
        return True
    return " " not in n and first_name(x.get("name")) == n and \
        sum(1 for y in people if first_name(y.get("name")) == n) == 1


def shared_first_names(ref):
    """The first names that two people of people.yaml share: written alone in `holders` or `by`,
    they cannot say which person is meant (README_operations.md §1.16)."""
    seen = {}
    for x in ref["people"]:
        seen.setdefault(first_name(x.get("name")), []).append(x.get("name"))
    return {k: v for k, v in seen.items() if k and len(v) > 1}


def check_shared_names(ref):
    """A holder or a `by` that writes alone a first name two people share."""
    shared, warnings = shared_first_names(ref), []
    def look(where, values):
        for v in values or []:
            n = human_name(v)
            if is_person(n) and n.lower() in shared:
                warnings.append(tr("check.person_shared", where=where, value=n,
                                   names=", ".join(shared[n.lower()])))
    for r in ref["roles"]:
        look(f"{r['_file']} {r.get('id')} holders", r.get("holders"))
    for t in ref["tasks"]:
        look(f"{t['_file']} {t.get('id')} by", t.get("by"))
    return warnings


def link_people(ref):
    """Each person gets the roles they hold (a holder that writes their name, one of their
    aliases, or their first name alone when no one else has it), the teams of those roles, the agents they run, and their access to the
    OS: `works` when one way works, else `unchecked`, `not_found`, `none` (no access), or
    `unknown` (never surveyed) (§1.16). Each
    agent gets the tasks it does that are active."""
    tasks = {t["id"]: t for t in ref["tasks"]}
    shared = shared_assistants(ref)
    for x in ref["people"]:
        x["_roles"] = [r["id"] for r in ref["roles"] if any(
            names_person(ref["people"], x, human_name(h)) for h in r.get("holders") or []
            if human_name(h))]
        x["_teams"] = sorted({r["team"] for r in ref["roles"] if r["id"] in x["_roles"]})
        x["_agents"] = [a["id"] for a in ref["agents"] if x.get("id") in (a.get("people") or [])]
        access = [a for a in x.get("os_access") or [] if isinstance(a, dict)]
        states = [a.get("state") for a in access if a.get("mode") != "none" and a.get("state")]
        x["_access"] = min(states, key=lambda k: ACCESS_RANK.get(k, 9)) if states else \
            "none" if access else "unknown"
        # The shared assistants the person can talk to, whose AI reads the OS (§1.18).
        x["_shared"] = [t["id"] for t in shared if t["shared"]["audience"] == "all"
                        or set(t["shared"]["audience"]) & set(x["_teams"])]
    for a in ref["agents"]:
        a["_active_tasks"] = [t for t in a.get("tasks") or []
                              if (tasks.get(t) or {}).get("state") == "active"]
        a["_cost"] = agent_cost(a)
        a["_progress"] = agent_progress(a)


def zone_files(root, z, zones):
    """The documents of a zone's folder (.md and .yaml files, READMEs and templates aside),
    without those of the folders of its child zones, as paths relative to the zone's folder;
    None when the OS is not at hand."""
    if not root or not z.get("path"):
        return None
    folder = os.path.join(root, str(z["path"]))
    if not os.path.isdir(folder):
        return None
    inner = {os.path.normpath(os.path.join(root, str(c["path"]))) for c in zones
             if c.get("parent") == z.get("id") and c.get("path")}
    found = []
    for here, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if os.path.normpath(os.path.join(here, d)) not in inner)
        found += [os.path.relpath(os.path.join(here, f), folder) for f in sorted(files)
                  if f.endswith((".md", ".yaml")) and not f.startswith(("README", "_"))]
    return found


def zone_documents(root, z, zones):
    """How many documents a zone's folder holds (zone_files); None when the OS is not at hand."""
    files = zone_files(root, z, zones)
    return None if files is None else len(files)


# Freshness of a zone (README_operations.md §1.15): the age in days of its most recent dated
# document on the day the referential was updated. Each level holds up to the given age.
FRESHNESS = (("fresh", 7), ("recent", 30), ("aging", 90), ("old", 180), ("stale", None))
DOC_DATE = re.compile(r"(20\d\d-\d\d-\d\d)")
GENERATED_MARK = "generated_by: teamstarter-os/tools/build_rpt.py"
DOC_DATE_FIELD = re.compile(r"^(?:date|updated|last_updated|last_update|created)\s*:\s*"
                            r"['\"]?(20\d\d-\d\d-\d\d)", re.M)


def document_date(folder, rel):
    """The date of a document: the first date in its path inside the zone (« 2026-10-12-acme.md »,
    « 2026-10/… »), else the `date`, `updated`, `last_updated` or `created` field of its first
    lines; None without one. A view this script generates (`generated_by: …build_rpt.py`) has
    no date: it is written from the referential, not fed by a flow, and reading its date would
    make the build depend on its own previous output."""
    m = DOC_DATE.search(rel)
    if m:
        return m.group(1)
    try:
        with open(os.path.join(folder, rel), encoding="utf-8", errors="ignore") as f:
            head = f.read(3000)
    except OSError:
        return None
    if GENERATED_MARK in head:
        return None
    m = DOC_DATE_FIELD.search(head)
    return m.group(1) if m else None


def freshness_level(days):
    for level, limit in FRESHNESS:
        if limit is None or days <= limit:
            return level
    return FRESHNESS[-1][0]


def zone_freshness(root, z, zones, today):
    """When a zone's data was last brought in: its most recent dated document, its age in days on
    `today` (the update date of the referential) and the level of FRESHNESS; `undated` when none
    of its documents has a date; None without documents."""
    files = zone_files(root, z, zones)
    if not files:
        return None
    folder = os.path.join(root, str(z["path"]))
    dates = [d for d in (document_date(folder, rel) for rel in files) if d and d <= today]
    if not dates:
        return {"level": "undated", "dated": 0, "documents": len(files)}
    return dict(dated_freshness(dates, today), dated=len(dates), documents=len(files))


def dated_freshness(dates, today):
    """The freshness of the most recent of `dates` on `today` (dates after `today` and empty ones
    left out): its date, its age in days and its level of FRESHNESS; `undated` without any."""
    dates = [str(d)[:10] for d in dates if d and DOC_DATE.fullmatch(str(d)[:10]) and str(d)[:10] <= today]
    if not dates:
        return {"level": "undated"}
    latest = max(dates)
    days = max(0, (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(latest)).days)
    return {"level": freshness_level(days), "latest": latest, "days": days}


def file_date(root, rel):
    """The date of a file of the OS given by its path from the root of the OS (an insight's `file`,
    an artifact's `path`): as document_date; None outside an OS or without a path."""
    if not root or not isinstance(rel, str) or not rel:
        return None
    return document_date(root, rel)


def item_freshness(root, item, today):
    """When an insight or an artifact was last brought up to date (README_operations.md §1.15):
    the most recent of its declared date (`last_seen` for an insight, `updated` for an artifact)
    and the date of its file (`file`, `path`)."""
    declared = item.get("last_seen") or item.get("updated")
    return dated_freshness([declared, file_date(root, item.get("file") or item.get("path"))], today)


def feed_connector(f, sources):
    """How the AI reaches the data of a flow: the connector of its tool in the data source (its
    reference tool when the flow names none); None for a flow from another zone."""
    d = sources.get(f.get("from"))
    if not d:
        return None
    tools = [x for x in d.get("tools") or [] if isinstance(x, dict)]
    match = [x for x in tools if x.get("tool") == f.get("tool")] if f.get("tool") else tools[:1]
    return match[0].get("connector") if match else None


OS_STATUS = ("included", "to_add", "excluded", "undecided")


def source_os(d, zones):
    """The place of a data source in the OS (README_operations.md §1.7): the status declared in
    `os` (`excluded` with its reason), else `included` when a flow in place or by hand brings it
    into a zone, `to_add` when only possible flows name it, `undecided` without any flow; with the
    zones its flows feed."""
    feeds = [(z["id"], f.get("state")) for z in zones for f in z.get("_feeds") or []
             if f.get("from") == d.get("id")]
    states = {s for _, s in feeds}
    derived = "included" if states & {"live", "manual"} else "to_add" if "possible" in states \
        else "undecided"
    declared = d.get("os") if isinstance(d.get("os"), dict) else {}
    out = {"status": declared.get("status") or derived, "declared": bool(declared.get("status")),
           "zones": sorted({z for z, s in feeds if s in ("live", "manual")}),
           "possible": sorted({z for z, s in feeds if s == "possible"})}
    if declared.get("reason"):
        out["reason"] = declared["reason"]
    return out


def link_os(ref, idx):
    """The structure of the OS (README_operations.md §1.15). Each zone gets its child zones, its
    documents, its flows with their connector, its insights, and the data sources upstream of it
    (`_upstream`: data source → the least advanced state of the flows that bring it there).
    Each insight gets the flows that name it, the data sources behind them, and its reach: the
    most advanced state of those flows (live, manual, possible). Each insight and each artifact
    gets its freshness (item_freshness)."""
    root = os_root(ref)
    today = last_updated(ref)[:10]
    sources = {d["id"]: d for d in ref["data_sources"]}
    zones = {z.get("id"): z for z in ref["os_zones"]}
    for z in ref["os_zones"]:
        z["_children"] = [c["id"] for c in ref["os_zones"] if c.get("parent") == z.get("id")]
        z["_documents"] = zone_documents(root, z, ref["os_zones"])
        z["_freshness"] = zone_freshness(root, z, ref["os_zones"], today) if today else None
        z["_feeds"] = [dict(f, connector=feed_connector(f, sources),
                            **{"from": resolve(idx, f["from"])})
                       for f in z.get("feeds") or [] if isinstance(f, dict) and f.get("from")]
        z["_insights"] = [i["id"] for i in ref["insights"] if i.get("zone") == z.get("id")]
    for d in ref["data_sources"]:
        d["_os"] = source_os(d, ref["os_zones"])
    memo = {}
    for z in ref["os_zones"]:
        z["_upstream"] = upstream(z.get("id"), zones, sources, memo)
    for i in ref["insights"]:
        i["_feeds"], data = [], {}
        for z in ref["os_zones"]:
            for f in z["_feeds"]:
                if i.get("id") not in (f.get("insights") or []):
                    continue
                i["_feeds"].append({"zone": z["id"], "from": f["from"], "state": f.get("state"),
                                    "tool": f.get("tool"), "skill": f.get("skill"),
                                    "connector": f.get("connector")})
                for d, state in feed_data(f, zones, sources, memo, insight=i["id"]).items():
                    data[d] = min(data.get(d, state), state, key=FEED_RANK.get)
        i["_data"] = data
        states = [f["state"] for f in i["_feeds"] if f.get("state") in FEED_RANK]
        i["_reach"] = min(states, key=FEED_RANK.get) if states else None
    for z in ref["os_zones"]:
        z["_maturity"] = zone_maturity(z, ref["insights"])
    if today:
        for x in ref["insights"] + (ref.get("artifacts") or []):
            x["_freshness"] = item_freshness(root, x, today)


MATURITY = ("none", "data", "insights", "auto")


def zone_maturity(z, insights):
    """Where a zone stands (README_operations.md §1.15): `none` (no document, no flow filled),
    `data` (documents or a flow filled, no insight backed by facts), `insights` (an insight of
    the zone is backed by facts), `auto` (a flow in place feeds the zone and an insight of the
    zone backed by facts is fed by a flow in place). None for a zone that only groups others."""
    feeds = z.get("_feeds") or []
    filled = bool(z.get("_documents")) or any(f.get("state") in ("live", "manual") for f in feeds)
    if z.get("_children") and not filled and not feeds:
        return None
    backed = [i for i in insights if i.get("zone") == z.get("id") and insight_has_facts(i)]
    if backed and any(f.get("state") == "live" for f in feeds) \
            and any(i.get("_reach") == "live" for i in backed):
        return "auto"
    return "insights" if backed else "data" if filled else "none"


def feed_data(f, zones, sources, memo, seen=frozenset(), insight=None):
    """The data sources a flow brings, each with the state it arrives in: the flow's own state,
    or a less advanced one met upstream. For one insight, a possible flow upstream counts only
    when it names that insight: an opening is made for given insights, a running flow carries
    everything the zone holds."""
    state = f.get("state") if f.get("state") in FEED_RANK else "possible"
    if f.get("from") in sources:
        return {f["from"]: state}
    up = upstream(f.get("from"), zones, sources, memo, seen, insight)
    return {d: max(s, state, key=FEED_RANK.get) for d, s in up.items()}


def upstream(zone_id, zones, sources, memo, seen=frozenset(), insight=None):
    key = (zone_id, insight)
    if key in memo:
        return memo[key]
    if zone_id in seen or zone_id not in zones:
        return {}
    seen = set(seen) | {zone_id}
    out = {}
    for f in zones[zone_id].get("_feeds") or []:
        if insight and f.get("state") == "possible" and insight not in (f.get("insights") or []):
            continue
        for d, state in feed_data(f, zones, sources, memo, seen, insight).items():
            out[d] = min(out.get(d, state), state, key=FEED_RANK.get)
    memo[key] = out
    return out



def link_blockers(ref, idx):
    """Each task gets the ids of the blockers that name it (`_blockers`). A task that writes no
    `blocker` of its own gets one from its blockers still open or in progress: their texts, and
    the type of the first one (`_blocker_derived`), so the views and the action plan read the
    same fields as before the register. Each blocker gets its active tasks and their hours per
    month (`_hours`, gain per person times the people who do the task)."""
    tasks = {t["id"]: t for t in ref["tasks"]}
    for t in ref["tasks"]:
        t["_blockers"] = []
    for b in ref["blockers"]:
        ids = [resolve(idx, x) for x in b.get("tasks") or [] if isinstance(x, str)]
        live = [tasks[x] for x in ids if x in tasks and tasks[x].get("state") == "active"]
        b["_active_tasks"] = [t["id"] for t in live]
        b["_hours"] = round(sum((t.get("_gain") or {}).get("hours") or 0 for t in live), 1) \
            if b.get("state") in ("open", "in_progress") else 0
        for x in ids:
            if x in tasks:
                tasks[x]["_blockers"].append(b["id"])
    current = {b["id"]: b for b in ref["blockers"] if b.get("state") in ("open", "in_progress")}
    for t in ref["tasks"]:
        open_ = [current[x] for x in t["_blockers"] if x in current]
        if open_ and not t.get("blocker") and not t.get("blocker_type"):
            t["blocker"] = " ; ".join(str(b.get("text")) for b in open_)
            t["blocker_type"] = open_[0].get("type")
            t["_blocker_derived"] = True


def ai_view(t, sources, policy, idx=None):
    """What the data of a task holds and what the AI policy allows (§1.8): the categories of its
    data sources, the distinct rules they get, the strictest one (None when none is known), the
    categories the policy gives no rule, and the sources not classified yet."""
    rules_of = (policy or {}).get("rules") or {}
    categories, unclassified = set(), []
    for value in t.get("data") or []:
        d = sources.get(resolve(idx, value) if idx else value)
        if d is None:
            continue
        if d.get("sensitivity") is None:
            unclassified.append(d["id"])
        else:
            categories.update(d["sensitivity"] or ["internal"])
    known = {rules_of[c] for c in categories if rules_of.get(c) in AI_RULES}
    # Credentials never block a task: the rule says never to pass them, and an automation is
    # built without them. Another category whose rule is `authorization` or `forbidden` does.
    blocking = {rules_of[c] for c in categories - {"credentials"}
                if rules_of.get(c) in ("authorization", "forbidden")}
    return {"categories": [c for c in SENSITIVITY_ORDER if c in categories],
            "rules": [r for r in AI_RULES if r in known],
            "rule": max(known, key=AI_RULES.index) if known else None,
            "block": max(blocking, key=AI_RULES.index) if blocking else None,
            "undecided": [c for c in SENSITIVITY_ORDER if c in categories
                          and rules_of.get(c) not in AI_RULES],
            "unclassified": unclassified}


def data_links(t, sources, idx=None):
    """The tools in which a task reaches its data, each with its connector: for each data source
    the task cites, the tools of that source that the task cites too, or, when it cites none of
    them, the reference tool of the source, the first of its list (README_operations.md §1.7)."""
    cited, links = set(t.get("tools") or []), []
    for value in t.get("data") or []:
        d = sources.get(resolve(idx, value) if idx else value)
        entries = [e for e in (d or {}).get("tools") or [] if isinstance(e, dict) and e.get("tool")]
        for e in [e for e in entries if e["tool"] in cited] or entries[:1]:
            links.append({"data": d["id"], "tool": e["tool"], "connector": e.get("connector")})
    return links


def connector_rows(ref):
    """One row per tool and access (reached by the AI or not): the data sources the active tasks
    reach through it, those tasks, the M and S ones apart, and their estimated gain. Sorted by
    M and S tasks, gain, tasks. Needs enrich()."""
    rows = {}
    for t in active(ref["tasks"]):
        for link in t.get("_data_links") or []:
            key = (link["tool"], link["connector"] in CONNECTED)
            row = rows.setdefault(key, {"tool": link["tool"], "reached": key[1],
                                        "connectors": set(), "data": set(), "tasks": {}})
            row["connectors"].add(link["connector"])
            row["data"].add(link["data"])
            row["tasks"][t["id"]] = t
    for row in rows.values():
        tasks = list(row["tasks"].values())
        row["ms"] = sum(t["status"] in OPEN_STATUSES for t in tasks)
        row["gains"] = [t["_gain"]["hours"] for t in tasks if t.get("_gain")]
        row["gain"] = round(sum(row["gains"]), 1)
    return sorted(rows.values(), key=lambda r: (-r["ms"], -r["gain"], -len(r["tasks"]),
                                                r["tool"]))


def counts(tasks):
    """Tasks by status and coverage = automated / (tasks − judgement)."""
    c = {s: 0 for s in STATUS_ORDER}
    for t in tasks:
        c[t["status"]] += 1
    c["total"] = sum(c[s] for s in STATUS_ORDER)
    base = c["total"] - c["J"]
    c["coverage"] = round(100 * c["A"] / base) if base else None
    return c


def active(tasks):
    return [t for t in tasks if t.get("state") == "active"]


def stats(ref):
    """Figures per team and per department (active tasks)."""
    teams, depts = {}, {}
    roles = {r["id"]: r for r in ref["roles"]}
    for team in sorted({r["team"] for r in ref["roles"]}):
        tasks = active([t for t in ref["tasks"] if roles[t["role"]]["team"] == team])
        procs = [p for p in ref["processes"] if roles[p["role"]]["team"] == team]
        teams[team] = {"roles": sum(r["team"] == team for r in ref["roles"]),
                       "processes": sum(p["state"] == "active" for p in procs),
                       "proposed": sum(p["state"] == "proposed" for p in procs),
                       "tasks": counts(tasks)}
    for d in ref["departments"]:
        tasks = active([t for t in ref["tasks"] if d["id"] in t["_depts"]])
        depts[d["id"]] = counts(tasks)
    live = active(ref["tasks"])
    types = {"typed": sum(1 for t in live if t.get("type")), "active": len(live),
             "used": len({t["type"] for t in live if t.get("type")}),
             "catalogue": len(ref["task_types"])}
    states = [b.get("state") for b in ref["blockers"]]
    blockers = {k: states.count(k) for k in ("open", "in_progress", "resolved", "dropped")}
    blockers["blocked_tasks"] = sum(1 for t in live if any(
        x in {b["id"] for b in ref["blockers"] if b.get("state") in ("open", "in_progress")}
        for x in t.get("_blockers") or []))
    return {"teams": teams, "departments": depts, "all": counts(live), "types": types,
            "library": library_stats(library(ref)), "blockers": blockers, "os": os_stats(ref),
            "people": people_stats(ref), "agents": agent_stats(ref),
            "data_map": datamap_stats(ref)}


def people_stats(ref):
    """Coverage of the OS: the people whose AI reaches it, by access state and by team (§1.16)."""
    rows = ref["people"]
    by_state = {k: sum(1 for x in rows if x.get("_access") == k)
                for k in ("works", "unchecked", "not_found", "none", "unknown")}
    modes = {m: sum(1 for x in rows if any(isinstance(a, dict) and a.get("mode") == m
                                          and a.get("state") == "works"
                                          for a in x.get("os_access") or []))
             for m in ("connector", "local", "repository")}
    teams = {}
    for x in rows:
        for team in x.get("_teams") or ["?"]:
            row = teams.setdefault(team, {"people": 0, "works": 0})
            row["people"] += 1
            row["works"] += x.get("_access") == "works"
    return {"people": len(rows), "access": by_state, "modes": modes, "teams": teams,
            "coverage": round(100 * by_state["works"] / len(rows)) if rows else 0}


def agent_stats(ref):
    out = {k: sum(1 for a in ref["agents"] if a.get("state") == k)
           for k in ("construction", "live", "paused", "retired")}
    costs = [a.get("_cost") or agent_cost(a) for a in ref["agents"] if a.get("state") != "retired"]
    out["per_month"] = round(sum((c or {}).get("per_month") or 0 for c in costs), 2)
    levels = [(a.get("stage") or {}).get("level") if isinstance(a.get("stage"), dict) else None
              for a in ref["agents"] if a.get("state") != "retired"]
    out["stages"] = {k: levels.count(k) for k in AGENT_STAGES}
    out["stages"]["none"] = sum(1 for x in levels if x not in AGENT_STAGES)
    return out


def insight_has_facts(i):
    """A finding with facts counted, or a question answered at least in part."""
    return bool(i.get("count")) if i.get("kind") == "finding" else \
        i.get("state") in ("partial", "answered")


def insight_used(i):
    """A finding being acted on, or a question answered: the OS changed a decision."""
    return i.get("state") in ("acted", "answered")


def os_integration(ref):
    """How far the OS is integrated (README_operations.md §1.15): its leaves (the flows) filled
    and filled without anyone, its insights backed by facts, fed by a flow in place, used, and
    the people whose AI reads the OS. Each step is a count out of a total."""
    feeds = [f for z in ref["os_zones"] for f in z.get("feeds") or [] if isinstance(f, dict)]
    ins = ref["insights"]
    return {"leaves": len(feeds),
            "filled": sum(1 for f in feeds if f.get("state") in ("live", "manual")),
            "live": sum(1 for f in feeds if f.get("state") == "live"),
            "insights": len(ins),
            "with_facts": sum(1 for i in ins if insight_has_facts(i)),
            "fed_live": sum(1 for i in ins if insight_has_facts(i) and i.get("_reach") == "live"),
            "used": sum(1 for i in ins if insight_used(i)),
            "people": len(ref["people"]),
            "reading": sum(1 for x in ref["people"] if x.get("_access") == "works")}


def os_stats(ref):
    """Figures of the structure of the OS (README_operations.md §1.15)."""
    feeds = [f for z in ref["os_zones"] for f in z.get("feeds") or [] if isinstance(f, dict)]
    insights = {kind: {state: sum(1 for i in ref["insights"]
                                  if i.get("kind") == kind and i.get("state") == state)
                       for state in states}
                for kind, states in INSIGHT_STATES.items()}
    return {"zones": len(ref["os_zones"]),
            "documents": sum(z.get("_documents") or 0 for z in ref["os_zones"]),
            "feeds": {k: sum(1 for f in feeds if f.get("state") == k) for k in FEED_RANK},
            "insights": insights, "integration": os_integration(ref),
            "maturity": {k: sum(1 for z in ref["os_zones"] if z.get("_maturity") == k)
                         for k in MATURITY},
            "freshness": {k: sum(1 for z in ref["os_zones"]
                                 if (z.get("_freshness") or {}).get("level") == k)
                          for k in [f[0] for f in FRESHNESS] + ["undated"]},
            "decisions": {k: sum(1 for d in ref["decisions"] if d.get("state") == k)
                          for k in ("active", "proposed", "retired")},
            "decisions_traced": sum(1 for d in ref["decisions"] if d.get("depends_on")),
            "artifacts": {k: sum(1 for a in ref["artifacts"]
                                 if (a.get("purpose") or {}).get("goal") == k)
                          for k in ("understand", "share", "decide")},
            "products": len(ref["products"])}


# AI profile (README_operations.md §1.18): six axes, each in levels 0 to 4, then a profile.
# Execution: how much of the work the AI does. Delegation: how much the AI decides, the person
# validating, framing, then delegating. Infrastructure: how durably and technically the AI is
# installed, from prompting to agents billed on the API outside personal plans. Sharing: how
# much of its data the AI reaches. Control: whether a person can see and take back what the AI
# does. Investment: what the company pays to use the AI (ai-investment.yaml).
PROFILE_AXES = ("execution", "delegation", "infrastructure", "sharing", "control", "investment")
PROFILES = ("augmented", "industrializer", "delegator", "executor", "controller", "investor",
            "cautious", "manual")
# The profile named after the leading axis, when it reaches level 2; on a tie, in this order.
PROFILE_LEAD = {"infrastructure": "industrializer", "delegation": "delegator",
                "execution": "executor", "control": "controller", "investment": "investor",
                "sharing": "cautious"}
# A team weighs in the spread of a company from 5 % of its active tasks; a spread of 3 levels
# or more in execution makes the company heterogeneous.
PROFILE_TEAM_MIN, PROFILE_SPREAD = 0.05, 3
# A role is framed for the AI when 3 or more of its five delegation criteria are met.
FRAMED_CRITERIA = 3
# The grade of a profile: the sum of the six levels, from 0 to 24 points, read on this scale
# (letter, first point of the grade, rarity of its card).
PROFILE_GRADES = (("F", 0, "common"), ("D", 4, "common"), ("C", 8, "uncommon"),
                  ("B", 12, "uncommon"), ("A", 16, "rare"), ("S", 20, "mythic"))
PROFILE_MAX = 4 * len(PROFILE_AXES)
SKILL_TOOL_TYPES = ("skill", "agent", "managed-agent", "routine")


def _cap(value):
    """The progress inside a level, from 0 to 0.99."""
    return min(0.99, max(0.0, value))


def _missing(share, total, have):
    return max(0, math.ceil(share * total - 1e-9) - have)


def profile_measures(tasks, procs, roles, agents, tool_types, people=0, reading=0,
                     reading_shared=0):
    """What the axes read, for a set of active tasks and what goes with them."""
    def framed(r):
        crit = r.get("criteria") if isinstance(r.get("criteria"), dict) else {}
        return sum(1 for v in crit.values() if v == "yes") >= FRAMED_CRITERIA
    status = {t["id"]: t.get("status") for t in tasks}
    alone = [p for p in procs if any(status.get(s) == "A" for s in p.get("_steps") or [])]
    live = [a for a in agents if a.get("state") == "live"]
    billing = [(a.get("cost") or {}).get("billing") if isinstance(a.get("cost"), dict) else None
               for a in live]
    return {"tasks": len(tasks), "judgment": sum(1 for t in tasks if t.get("status") == "J"),
            "automated": sum(1 for t in tasks if t.get("status") == "A"),
            "assisted": sum(1 for t in tasks if t.get("status") in ("S", "C")),
            "skilled": sum(1 for t in tasks if t.get("status") == "S"),
            "conversational": sum(1 for t in tasks if t.get("status") == "C"),
            "processes": len(procs),
            "proc_assisted": sum(1 for p in procs if p.get("automation") not in (None, "manual")),
            "proc_launched": sum(1 for p in procs if p.get("automation") in
                                 ("once-launched", "routing", "end-to-end")),
            "proc_end_to_end": sum(1 for p in procs if p.get("automation") == "end-to-end"),
            "proc_alone": len(alone), "proc_gated": sum(1 for p in alone if p.get("gates")),
            "roles": len(roles), "framed_roles": sum(1 for r in roles if framed(r)),
            "automated_roles": sum(1 for r in roles if str(r.get("level")) == "03"),
            "with_skill": sum(1 for t in tasks if any(tool_types.get(x) in SKILL_TOOL_TYPES
                                                       for x in t.get("tools") or [])),
            "agents_plan": sum(1 for b in billing if b != "api"),
            "agents_api": sum(1 for b in billing if b == "api"),
            "agents_live": len(live),
            "agents_reporting": sum(1 for a in live
                                    if a.get("owner") and a.get("log") and a.get("notify")),
            "agents_efficient": sum(1 for a in live if (a.get("_progress") or {}).get("stage")
                                    in ("efficient", "refined")),
            "with_data": sum(1 for t in tasks if t.get("_data_links")),
            "reached": sum(1 for t in tasks if t.get("_data_links")
                           and all(x["connector"] in CONNECTED for x in t["_data_links"])),
            "people": people, "reading": reading, "reading_shared": reading_shared}


def axis_execution(m):
    """0 no task with the AI; 1 the AI assists or does under 15 % of the tasks outside judgment;
    2 from 15 %; 3 from 40 %, 10 % done by the AI alone (automated); 4 from 30 % automated."""
    nj = m["tasks"] - m["judgment"]
    ai, auto = m["automated"] + m["assisted"], m["automated"]
    s, a = (ai / nj, auto / nj) if nj else (0, 0)
    if a >= 0.30:
        return 4, 4 + _cap((a - 0.30) / 0.70), None
    if s >= 0.40 and a >= 0.10:
        return 3, 3 + _cap((a - 0.10) / 0.20), ("thirty", _missing(0.30, nj, auto))
    if s >= 0.15:
        need = _missing(0.40, nj, ai)
        return 2, 2 + _cap((s - 0.15) / 0.25), ("forty", need) if need else \
            ("ten", _missing(0.10, nj, auto))
    if ai:
        return 1, 1 + _cap(s / 0.15), ("fifteen", _missing(0.15, nj, ai))
    return 0, 0, ("first", 1)


def axis_delegation(m):
    """0 the person decides everything; 1 the AI proposes, the person validates each output (an
    assisted process); 2 the person launches, the AI chains alone (a process once launched or
    routed by the AI); 3 the person frames, the AI decides within the rules (a process end to
    end and 10 % of the roles framed: 3 of their 5 delegation criteria met); 4 the person
    delegates (a role run with its agents, level 03, and 25 % of the roles framed)."""
    r = m["framed_roles"] / m["roles"] if m["roles"] else 0
    framed10, framed25 = (_missing(x, m["roles"], m["framed_roles"]) for x in (0.10, 0.25))
    if m["proc_end_to_end"] and not framed10:
        if m["automated_roles"] and not framed25:
            return 4, 4 + _cap((r - 0.25) / 0.75), None
        key = "framed" if m["automated_roles"] else "role_framed" if framed25 else "role"
        return 3, 3 + _cap((r - 0.10) / 0.15), (key, framed25)
    if m["proc_launched"]:
        key = "end_to_end_framed" if not m["proc_end_to_end"] and framed10 else \
            "end_to_end" if not m["proc_end_to_end"] else "framed"
        return 2, 2 + _cap(r / 0.10), (key, framed10)
    if m["proc_assisted"]:
        share = m["proc_assisted"] / m["processes"] if m["processes"] else 0
        return 1, 1 + _cap(share / 0.50), ("launched", 1)
    return 0, 0, ("first", 1)


def axis_infrastructure(m):
    """0 no AI; 1 prompting, the AI used in conversation; 2 skills shared by 10 % of the tasks;
    3 that, and an agent in service on a plan (a Routine, a scheduled task); 4 that, and an
    agent in service billed on the API, outside personal plans (a managed agent)."""
    n = m["tasks"]
    k = m["with_skill"] / n if n else 0
    if k >= 0.10 and (m["agents_api"] or m["agents_plan"]):
        if m["agents_api"]:
            return 4, 4 + _cap((m["agents_api"] - 1) / 3), None
        return 3, 3 + _cap((m["agents_plan"] - 1) / 3), ("api", 1)
    if k >= 0.10:
        return 2, 2 + _cap((k - 0.10) / 0.30), ("scheduled", 1)
    if m["with_skill"] or m["automated"] or m["assisted"]:
        return 1, 1 + _cap(k / 0.10), ("skills", _missing(0.10, n, m["with_skill"]))
    return 0, 0, ("first", 1)


def axis_sharing(m, live_share):
    """0 copy and paste; 1 the AI reaches all the data of under half the tasks that use data;
    2 from half; 3 that and 30 % of the people reach the OS through an AI: their own, or a
    shared assistant they can talk to (a bot of the team's chat tool connected to the data,
    §1.18); 4 that and half the leaves of the OS filled by a flow in place."""
    d = m["reached"] / m["with_data"] if m["with_data"] else 0
    o = m["reading"] / m["people"] if m["people"] else 0
    if d >= 0.50 and o >= 0.30:
        if live_share >= 0.50:
            return 4, 4 + _cap((live_share - 0.50) / 0.50), None
        return 3, 3 + _cap((o - 0.30) / 0.70), ("flows", None)
    if d >= 0.50:
        return 2, 2 + _cap(o / 0.30), ("access", _missing(0.30, m["people"], m["reading"]))
    if m["reached"]:
        return 1, 1 + _cap(d / 0.50), ("half", _missing(0.50, m["with_data"], m["reached"]))
    return 0, 0, ("first", 1)


def axis_control(m, policy):
    """0 no AI policy of its own; 1 a written AI policy; 2 that, and half the processes where
    the AI does a step alone (a task A) with a human gate (`gates`); 3 that, and every agent in
    service with an owner, a log of its runs and someone it notifies (§1.16); 4 that, and every
    agent in service at the efficient stage or above (its cost measured)."""
    alone, gated = m["proc_alone"], m["proc_gated"]
    g = gated / alone if alone else 0
    if not policy:
        return 0, 0, ("first", 1)
    if not alone or g < 0.50:
        return 1, 1 + _cap(g / 0.50), ("gates", _missing(0.50, alone, gated)) if alone \
            else ("alone", 1)
    live, rep, eff = m["agents_live"], m["agents_reporting"], m["agents_efficient"]
    if not live or rep < live:
        return 2, 2 + _cap(rep / live if live else 0), ("report", live - rep) if live \
            else ("agent", 1)
    if eff < live:
        return 3, 3 + _cap(eff / live), ("efficient", live - eff)
    return 4, 4 + _cap((g - 0.50) / 0.50), None


def licence_level(plan):
    """The investment level a licence gives: 0 none; 1 the AI without thinking; 2 with
    thinking; 3 a premium account with the work modes."""
    if not isinstance(plan, dict):
        return 0
    modes = plan.get("modes") if isinstance(plan.get("modes"), list) else []
    if plan.get("tier") == "premium" and "work" in modes:
        return 3
    return 2 if "thinking" in modes else 1


def investment_measures(inv, folk):
    """What the investment axis reads: the licence of each person (`ai_plan`), by the level it
    gives; the budget policy of the organization (`ai_investment`): its cost ratio, whether it
    is enforced, its monthly budget."""
    inv = inv or {}
    plans = [licence_level(x.get("ai_plan")) for x in folk if x.get("ai_plan") is not None]
    amount = lambda k: isinstance(inv.get(k), dict) and positive(inv[k].get("amount"))
    return {"surveyed": len(plans), "people": len(folk),
            "seats_access": sum(1 for n in plans if n >= 1),
            "seats_thinking": sum(1 for n in plans if n >= 2),
            "seats_premium": sum(1 for n in plans if n >= 3),
            "budget": amount("budget"), "cost_ratio": amount("cost_ratio"),
            "enforced": inv.get("enforced") is True}


def axis_investment(v):
    """A level is reached when half the people have its access (people without `ai_plan`
    count as without access): 0 no access to the AI; 1 the
    AI without thinking mode; 2 with thinking, without the work modes (Cowork, Claude Code,
    artifacts, assets); 3 premium accounts with the work modes; 4 that, and a budget policy
    that caps what the AI may cost for the human time it gives back (`cost_ratio`), enforced
    (what tells whether an agent costs less than it gives back)."""
    people = v["people"]
    have = [v["seats_access"], v["seats_thinking"], v["seats_premium"]]
    level = sum(1 for n in have if people and n >= 0.50 * people)
    if level == 3:
        if v["cost_ratio"] and v["enforced"]:
            return 4, 4 + _cap(v["seats_premium"] / people - 0.50), None
        return 3, 3 + _cap(v["seats_premium"] / people - 0.50), \
            ("enforce" if v["cost_ratio"] else "ratio", None)
    if not v["surveyed"]:
        return 0, 0, ("survey", None)
    nxt = have[level] / people if people else 0
    return level, level + _cap(nxt / 0.50), (("access", "thinking", "premium")[level],
                                             _missing(0.50, people, have[level]))


def profile_of(levels, sharing_own=None):
    """Augmented (the six axes at 3 or more), else the profile of the leading axis when it
    reaches level 2 (industrializer: infrastructure, delegator: delegation, executor:
    execution, controller: control, investor: investment, cautious and equipped: sharing; on a
    tie, in that order), else manual. `sharing_own`: the sharing level without the shared
    assistants; when sharing leads only thanks to them, the profile is read with that level
    (Vincent, 2026-10-20: the profile stays that of the next axis)."""
    if min(levels[k] for k in PROFILE_AXES) >= 3:
        return "augmented"
    lead = max(PROFILE_LEAD, key=lambda k: levels[k])
    profile = PROFILE_LEAD[lead] if levels[lead] >= 2 else "manual"
    if profile == PROFILE_LEAD["sharing"] and sharing_own is not None \
            and sharing_own < levels["sharing"]:
        return profile_of(dict(levels, sharing=sharing_own))
    return profile


def profile_grade(levels):
    """The grade of the six levels: its letter (F, D, C, B, A, S), its points (0 to 24), the
    rarity of its card, and the next grade with the points it starts at (None at S)."""
    points = sum(levels[k] for k in PROFILE_AXES)
    i = max(n for n, g in enumerate(PROFILE_GRADES) if points >= g[1])
    letter, _, rarity = PROFILE_GRADES[i]
    nxt = PROFILE_GRADES[i + 1] if i + 1 < len(PROFILE_GRADES) else None
    return {"letter": letter, "points": points, "rarity": rarity,
            "next": {"letter": nxt[0], "points": nxt[1]} if nxt else None}


def profile_force(entry):
    """The axis with the best score (level and progress); on a tie, the first of PROFILE_AXES."""
    return max(PROFILE_AXES, key=lambda k: (entry[k]["score"], -PROFILE_AXES.index(k)))


def profile_entry(m, policy, live_share, invest):
    """`invest`: the investment measures of the people of the entry (investment_measures)."""
    axes = {"execution": axis_execution(m), "delegation": axis_delegation(m),
            "infrastructure": axis_infrastructure(m), "sharing": axis_sharing(m, live_share),
            "control": axis_control(m, policy), "investment": axis_investment(invest)}
    out = {"measures": dict(m, **{k: v for k, v in invest.items() if k != "people"})}
    for k, (level, score, nxt) in axes.items():
        out[k] = {"level": level, "score": round(score, 2),
                  "next": {"key": nxt[0], "count": nxt[1]} if nxt else None}
    # The sharing level without the shared assistants (§1.18), for the profile.
    own = axis_sharing(dict(m, reading=m["reading"] - m.get("reading_shared", 0)), live_share)[0]
    out["sharing"]["own"] = own
    levels = {k: out[k]["level"] for k in PROFILE_AXES}
    out.update(profile=profile_of(levels, own), grade=profile_grade(levels),
               force=profile_force(out))
    return out


# What a company decides once for all its teams: when the company stops there, its next step
# is this one, not the teams to bring up.
COMPANY_WIDE_NEXT = {("control", "first"), ("investment", "survey"), ("investment", "ratio"),
                     ("investment", "enforce")}


def company_entry(pooled, teams):
    """The company read from its teams (README_operations.md §1.18): on each axis, the mean of
    the teams' levels weighted by their active tasks; the level is that mean rounded down, the
    score the mean itself. What the next level asks names the teams to bring up, the largest
    first, unless the company stops at a step it decides once for all (COMPANY_WIDE_NEXT). The
    measures stay those of all the company's tasks. Without teams, the pooled reading."""
    weight = {k: t["measures"]["tasks"] for k, t in teams.items()}
    total = sum(weight.values())
    if not total:
        return pooled
    out = dict(pooled)
    for axis in PROFILE_AXES:
        mean = sum(t[axis]["level"] * weight[k] for k, t in teams.items()) / total
        level = min(4, math.floor(mean + 1e-9))
        nxt = None
        if level < 4:
            need, have, up = (level + 1) * total, mean * total, []
            for k in sorted(teams, key=lambda k: -weight[k]):
                if have >= need - 1e-9:
                    break
                if teams[k][axis]["level"] <= level:
                    have += (level + 1 - teams[k][axis]["level"]) * weight[k]
                    up.append(k)
            nxt = {"key": "teams", "count": len(up), "teams": up}
            own = pooled[axis]["next"]
            if own and (axis, own["key"]) in COMPANY_WIDE_NEXT and pooled[axis]["level"] == level:
                nxt = own
        out[axis] = {"level": level, "score": round(mean, 2), "next": nxt}
    own = sum(t["sharing"].get("own", t["sharing"]["level"]) * weight[k]
              for k, t in teams.items()) / total
    out["sharing"]["own"] = min(4, math.floor(own + 1e-9))
    levels = {k: out[k]["level"] for k in PROFILE_AXES}
    out.update(profile=profile_of(levels, out["sharing"]["own"]), grade=profile_grade(levels),
               force=profile_force(out))
    return out


def ai_profile(ref):
    """The AI profile of the company and of each team (README_operations.md §1.18): per axis
    the level (0-4), the score (level and progress toward the next one) and what the next level
    asks; the profile; for the company, its teams' spread in execution. The company's levels
    are the mean of its teams' levels weighted by their active tasks (company_entry); its
    measures are those of all its active tasks. The AI policy and the budget policy are the
    company's, the same for its teams. Needs enrich()."""
    tasks = active(ref["tasks"])
    if not tasks:
        return None
    idx = index(ref)
    team = {r["id"]: r.get("team") for r in ref["roles"]}
    procs = [p for p in ref["processes"] if p.get("state", "active") == "active"]
    owner = {a["id"]: team.get(resolve(idx, a.get("owner")) if a.get("owner") else None)
             for a in ref["agents"]}
    types = {t["id"]: t.get("type") for t in ref["tools"]}
    policy = ref.get("ai_policy") is not None and not ref["ai_policy"].get("_borrowed")
    feeds = [f for z in ref["os_zones"] for f in z.get("feeds") or [] if isinstance(f, dict)]
    live_share = sum(1 for f in feeds if f.get("state") == "live") / len(feeds) if feeds else 0

    def entry(keep, folk):
        ts = [t for t in tasks if keep(team.get(t.get("role")))]
        ps = [p for p in procs if keep(team.get(p.get("role")))]
        rs = [r for r in ref["roles"] if keep(r.get("team")) and r.get("state", "active") == "active"]
        ags = [a for a in ref["agents"] if keep(owner[a["id"]])]
        own = sum(1 for x in folk if x.get("_access") == "works")
        via = sum(1 for x in folk if x.get("_access") != "works" and x.get("_shared"))
        m = profile_measures(ts, ps, rs, ags, types, len(folk), own + via, via)
        return profile_entry(m, policy, live_share,
                             investment_measures(ref.get("ai_investment"), folk))
    teams = {}
    for code in sorted({team.get(t.get("role")) for t in tasks} - {None}):
        teams[code] = entry(lambda tm, code=code: tm == code,
                            [x for x in ref["people"] if code in (x.get("_teams") or [])])
    company = company_entry(entry(lambda tm: True, ref["people"]), teams)
    weigh = [t["execution"]["level"] for t in teams.values()
             if t["measures"]["tasks"] >= PROFILE_TEAM_MIN * len(tasks)]
    spread = [min(weigh), max(weigh)] if weigh else [0, 0]
    company.update(spread=spread, heterogeneous=spread[1] - spread[0] >= PROFILE_SPREAD)
    return {"policy": policy, "live_share": round(live_share, 2), "max": PROFILE_MAX,
            "company": company, "teams": teams}


def last_updated(ref):
    dates = [str(m.get("updated")) for m in ref["files"].values() if m.get("updated")]
    return max(dates) if dates else ""


def public(item):
    """An entity without its private fields, computed fields renamed."""
    out = {k: v for k, v in item.items() if not k.startswith("_")}
    for key in ("_depts", "_processes", "_steps", "_score", "_priority", "_chain", "_gain", "_data_links", "_ai",
                "_blockers", "_blocker_derived", "_active_tasks", "_hours", "_children",
                "_documents", "_feeds", "_insights", "_upstream", "_data", "_reach", "_roles",
                "_teams", "_agents", "_access", "_cost", "_progress", "_maturity", "_used_by",
                "_shared_by", "_decides", "_decisions", "_artifacts", "_freshness", "_os",
                "_writers", "_readers", "_owners", "_holders", "_candidates", "_age", "_fresh",
                "_containers"):
        if key in item:
            out[key[1:]] = item[key]
    return out


def mapping_prompt():
    """The part of PROMPT.md that is pasted into an assistant (after the first rule)."""
    if not os.path.exists(PROMPT):
        return ""
    text = fill_prompt(read_text(PROMPT), load_config())
    parts = re.split(r"\n---\n", text, maxsplit=1)
    return parts[1].strip() + "\n" if len(parts) == 2 else text


def fill_prompt(text, cfg, lang="en"):
    """PROMPT.md with the values of the organization's configuration in place of its
    {{organization}}, {{intake}} and {{archive}} markers (README_operations.md §3.3). The
    values are in `lang`, the language PROMPT.md is written in (English)."""
    cfg = cfg or {}
    intake, ref = cfg.get("intake") or {}, cfg.get("referential") or {}
    where = [tr("prompt.drive", lang, folder=intake["drive_folder"])
             if intake.get("drive_folder") else "",
             tr("prompt.email", lang, email=intake["email"]) if intake.get("email") else ""]
    values = {"organization": (cfg.get("organization") or {}).get("name")
              or tr("prompt.organization", lang),
              "intake": tr("prompt.or", lang).join(w for w in where if w)
              or tr("prompt.back", lang),
              "archive": f"`{ref['archive_drive_folder']}`" if ref.get("archive_drive_folder")
              else tr("prompt.archive", lang)}
    return re.sub(r"\{\{(organization|intake|archive)\}\}", lambda m: values[m.group(1)], text)


CONFIG = os.path.normpath(os.path.join(HERE, "..", "rpt-config.yaml"))
# The repository that holds the OS: the paths of `config` and `log` of an agent are relative to it.
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CONFIG_FORMAT = "rpt-config/v1"
CONTEXT_MAX = 900
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
TEAM_RE = re.compile(r"^[a-z][a-z0-9-]*$")
CONFIG_KEYS = ["format", "updated", "organization", "referential", "intake", "owners", "teams",
               "catalogues", "skills", "privacy", "global_context"]


def load_config(path=None):
    """The organization's configuration (rpt-config.yaml, README_operations.md §3.3): what
    changes from one organization to another; default: the one in use (config_path). None when
    there is none or the file does not exist."""
    path = config_path() if path is None else path
    if not path or not os.path.exists(path):
        return None
    return yaml.safe_load(read_text(path)) or {}


def check_config(cfg, where="rpt-config.yaml"):
    """The errors of a configuration: required fields, forms, team codes, the context length."""
    if not isinstance(cfg, dict):
        return [tr("config.not_mapping", where=where)]
    errors = [tr("config.format", where=where, format=CONFIG_FORMAT)] \
        if cfg.get("format") != CONFIG_FORMAT else []
    errors += [tr("config.unknown_key", where=where, key=k) for k in cfg if k not in CONFIG_KEYS]
    org, ref = cfg.get("organization") or {}, cfg.get("referential") or {}
    intake = cfg.get("intake") or {}
    errors += [tr("config.missing", where=where, key=f"organization.{k}")
               for k in ("name", "language") if not org.get(k)]
    if not (ref.get("drive_folder") or ref.get("repository_path")):
        errors.append(tr("config.referential_where", where=where))
    if not ref.get("index"):
        errors.append(tr("config.missing", where=where, key="referential.index"))
    if ref.get("explorer") and not str(ref["explorer"]).startswith("https://"):
        errors.append(tr("config.explorer_url", where=where))
    if ref.get("config_url") and not str(ref["config_url"]).startswith("https://"):
        errors.append(tr("config.config_url", where=where, value=repr(ref["config_url"])))
    if not (intake.get("drive_folder") or intake.get("email")):
        errors.append(tr("config.intake_where", where=where))
    if intake.get("email") and not EMAIL_RE.match(str(intake["email"])):
        errors.append(tr("config.email", where=where, value=repr(intake["email"])))
    return errors + check_config_lists(cfg, where)


def check_config_lists(cfg, where):
    """The teams, catalogues and skills of a configuration, and its global context."""
    teams = cfg.get("teams") or []
    codes = [t.get("code") for t in teams if isinstance(t, dict)]
    errors = [tr("config.team_incomplete", where=where, value=repr(t)) for t in teams
              if not isinstance(t, dict) or not t.get("code") or not t.get("name")]
    errors += [tr("config.team_code", where=where, code=c) for c in codes
               if c and not TEAM_RE.match(str(c))]
    errors += [tr("config.team_twice", where=where, code=c) for c in sorted(set(codes))
               if c and codes.count(c) > 1]
    errors += [tr("config.headcount", where=where, code=t.get("code"), value=repr(t["headcount"]))
               for t in teams if isinstance(t, dict) and t.get("headcount") is not None
               and not (isinstance(t["headcount"], int) and not isinstance(t["headcount"], bool)
                        and t["headcount"] >= 0)]
    errors += [tr("config.catalogue", where=where, key=k, value=repr(v))
               for k, v in (cfg.get("catalogues") or {}).items()
               if not str(v).endswith(".yaml")]
    errors += [tr("config.skill", where=where, value=repr(s)) for s in cfg.get("skills") or []
               if not isinstance(s, dict) or not s.get("name") or not s.get("where")]
    context = str(cfg.get("global_context") or "")
    url = ((cfg.get("referential") or {}).get("config_url") or "") \
        if isinstance(cfg.get("referential"), dict) else ""
    if url and context.strip() and str(url) not in context:
        errors.append(tr("config.context_url", where=where, value=url))
    if not context.strip():
        errors.append(tr("config.missing", where=where, key="global_context"))
    elif len(context.strip()) > CONTEXT_MAX:
        errors.append(tr("config.context_long", where=where, size=len(context.strip()),
                         max=CONTEXT_MAX))
    return errors


def config_warnings(cfg, where="rpt-config.yaml"):
    """The warnings of a configuration: a language the messages do not exist in (the scripts
    then speak English; the content of the referential stays in that language)."""
    org = (cfg.get("organization") if isinstance(cfg, dict) else None) or {}
    value = org.get("language") if isinstance(org, dict) else None
    teams = [t for t in (cfg.get("teams") if isinstance(cfg, dict) else None) or []
             if isinstance(t, dict) and t.get("code")]
    without = [str(t["code"]) for t in teams if t.get("headcount") is None]
    out = [tr("config.no_headcount", where=where, codes=", ".join(without))] if without else []
    if not value or str(value).strip().lower() in rpt_i18n.LANGUAGES:
        return out
    return out + [tr("config.language", where=where, value=repr(value),
                     languages=", ".join(rpt_i18n.LANGUAGES))]


def config_teams_errors(cfg, ref):
    """The teams the referential uses that the configuration does not list."""
    codes = {t.get("code") for t in (cfg or {}).get("teams") or [] if isinstance(t, dict)}
    used = sorted({r.get("team") for r in ref["roles"] if not r.get("_borrowed")} - codes)
    return [tr("config.team_unused", team=x) for x in used if x] if cfg else []


def claude_context():
    """The text to paste in Claude's global context: `global_context` of rpt-config.yaml."""
    cfg = load_config()
    return str(cfg.get("global_context") or "").strip() + "\n" if cfg else ""


def public_config(cfg):
    """What the explorer shows of the configuration: the organization, its teams, the intake."""
    if not cfg:
        return None
    intake = cfg.get("intake") or {}
    return {"organization": (cfg.get("organization") or {}).get("name"),
            "teams": [{"code": t.get("code"), "name": t.get("name"),
                       "headcount": t.get("headcount")}
                      for t in cfg.get("teams") or [] if isinstance(t, dict)],
            "intake": {"drive_folder": intake.get("drive_folder"), "email": intake.get("email"),
                       "merged_by": intake.get("merged_by")}}


# The label tables the explorer receives in every language, under these names.
EXPLORER_LABELS = {"status": "status", "basis": "basis", "automation": "automation",
                   "connector": "connector", "sensitivity": "sensitivity",
                   "sensitivity_def": "sensitivity_def", "notes": "sensitivity_note",
                   "rules": "ai_rule", "rule_text": "ai_rule_text"}


def explorer_labels(lang):
    """Every label table in one language, as the explorer reads them (EXPLORER_LABELS); the
    key of the unknown connector (None) is "null"."""
    return {name: {("null" if code is None else code): text
                   for code, text in rpt_i18n.labels(table, lang).items()}
            for name, table in EXPLORER_LABELS.items()}


def investment_view(inv):
    """What the explorer shows of `ai_investment`: whether a cost ratio and a budget are set,
    whether the ratio is enforced. The amounts stay in the file: the explorer is shared by
    link."""
    if not inv:
        return None
    return {"cost_ratio": isinstance(inv.get("cost_ratio"), dict),
            "enforced": inv.get("enforced") is True,
            "budget": isinstance(inv.get("budget"), dict),
            "basis": inv.get("basis"), "checked": inv.get("checked")}


def explorer_data(ref):
    """What the explorer shows. Catalogue entries keep their texts by language; `language` is
    the organization's, the explorer's first language; `i18n` holds every label table in
    every language; `ai_labels` keeps the AI tables in the organization's language (older
    templates read it)."""
    policy, lang = ref.get("ai_policy"), view_language()
    labels, cited = explorer_labels(lang), cited_ids(ref)
    return {"format": FORMAT, "updated": last_updated(ref), "stats": stats(ref),
            "prompt": mapping_prompt(), "context": claude_context(),
            "config": public_config(load_config()),
            "coverage": map_coverage(ref, load_config()),
            "relevance_max": RELEVANCE_MAX,
            "history": history_data(ref), "library": library(ref),
            "ai_profile": ai_profile(ref),
            "ai_policy": dict(public(policy), borrowed=bool(policy.get("_borrowed")))
            if policy else None,
            "ai_investment": investment_view(ref.get("ai_investment")),
            "language": lang,
            "languages": list(rpt_i18n.LANGUAGES),
            "i18n": {code: explorer_labels(code) for code in rpt_i18n.LANGUAGES},
            "ai_labels": {"sensitivity": labels["sensitivity"],
                          "sensitivity_def": labels["sensitivity_def"],
                          "notes": labels["notes"],
                          "order": list(SENSITIVITY_ORDER), "rules": labels["rules"],
                          "rule_text": labels["rule_text"], "rule_order": list(AI_RULES)},
            "chains": ref.get("_chains") or [],
            **{name: [public(x) for x in published(ref, name, cited)] for name in LISTS}}


def scalars(value):
    """Every text of a value: its strings, the keys of its dicts."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from scalars(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from scalars(v)
    elif isinstance(value, str):
        yield value


def cited_ids(ref):
    """The ids the referential's own entries cite, and those the borrowed entries they cite
    cite in turn (the department of a task type, the tools of a data source, the objective of a
    key result and its parents). None when nothing is borrowed."""
    borrowed = [x for name in LISTS for x in ref[name] if x.get("_borrowed")]
    if not borrowed:
        return None
    idx = index(ref)

    def ids(items):
        out = set()
        for text in (t for item in items for t in scalars(item)):
            item = idx.get(text)
            if item:
                out.add(item.get("id"))
                if item.get("_okr"):
                    out.add(item["_okr"])
        return out

    used = ids(x for name in LISTS for x in ref[name] if not x.get("_borrowed"))
    while True:
        more = ids(x for x in borrowed if x.get("id") in used) - used
        if not more:
            return used
        used |= more


def for_views(ref):
    """The referential the views are written from: the borrowed catalogue entries it does not
    cite are left out (published), in the explorer and in referentiel.md alike."""
    cited = cited_ids(ref)
    if cited is None:
        return ref
    return dict(ref, **{name: published(ref, name, cited) for name in LISTS})


def published(ref, name, cited):
    """The entries of a list the explorer shows: the referential's own, and the borrowed ones it
    cites. Another organization's explorer never carries Teamstarter's whole catalogues (its
    internal skills, its OKRs)."""
    return [x for x in ref[name] if cited is None or not x.get("_borrowed") or x.get("id") in cited]


# ---------------------------------------------------------------------------- relevés

def human_name(value):
    """A person as `holders` and `by` write them, without what follows in brackets."""
    return str(value).split(" (")[0].strip()


def is_person(name):
    """A role holder that names a person (« Candice », « Quentin Guilluy », « Marie de
    Montfort »), not a team, a role or an agent (« équipe produit », « le CSM du compte »,
    « CSM, Care et sales pour la saisie »): no comma or digit, not all capitals, every word
    capitalised but name particles. The explorer applies the same rule (isPerson)."""
    if not name or re.search(r"[,0-9]", name) or name == name.upper():
        return False
    return all(re.match(r"[A-ZÀ-Ý]", w) or (i > 0 and (w.lower() in NAME_PARTICLES
                                                       or re.match(r"d'[A-ZÀ-Ý]", w)))
               for i, w in enumerate(name.split()))


def role_people(ref):
    """The people of the referential: the role holders that name a person."""
    return {human_name(h) for r in ref["roles"] for h in r.get("holders") or []
            if is_person(human_name(h))}


def people(t, names):
    """How many people do a task: the people of the referential that `by` cites, at least
    one. `by` also names agents, tools, roles and teams (« Claude », « CI », « le CSM du
    compte »), which do not count."""
    return max(1, len({human_name(x) for x in t.get("by") or [] if human_name(x) in names}))


def releve_task(t, names, idx):
    """What a relevé keeps of an active task: its status, target, type, number of people and
    tools (current ids), and the facts its hours come from: the `frequency` text, the frequency
    and effort ratings, the measure (README_operations.md §1.6). An empty field is left out."""
    rel = t.get("relevance") if isinstance(t.get("relevance"), dict) else {}
    m = t.get("measure") if isinstance(t.get("measure"), dict) else {}
    entry = {"status": t["status"]}
    entry.update({k: t[k] for k in ("target", "type") if t.get(k)})
    entry["people"] = people(t, names)
    tools = sorted({resolve(idx, x) for x in t.get("tools") or []})
    if tools:
        entry["tools"] = tools
    if t.get("frequency"):
        entry["frequency"] = str(t["frequency"])
    ratings = {k: rel[k] for k in ("frequency", "effort") if axis_value(rel.get(k))}
    if ratings:
        entry["relevance"] = ratings
    measure = {k: m[k] for k in ("minutes", "runs") if positive(m.get(k))}
    if measure:
        entry["measure"] = measure
    return entry


def releve(ref):
    """The state that two relevés compare: per active task, what releve_task keeps; per data
    link of an active task, the AI's access. Needs enrich()."""
    names, idx = role_people(ref), index(ref)
    tasks, links = {}, {}
    for t in active(ref["tasks"]):
        tasks[t["id"]] = releve_task(t, names, idx)
        for link in t.get("_data_links") or []:
            links[f"{link['data']} {link['tool']}"] = link["connector"]
    return {"format": RELEVE_FORMAT, "date": last_updated(ref), "tasks": tasks, "links": links}


def json_lines(entries):
    """A mapping as JSON, one entry per line (a change shows as one line in a diff)."""
    return ",\n".join(f"  {json.dumps(k, ensure_ascii=False)}: "
                      f"{json.dumps(v, ensure_ascii=False)}" for k, v in sorted(entries.items()))


def render_releve(ref):
    """The relevé as JSON, one task or one data link per line."""
    r = releve(ref)
    return (f'{{\n "format": "{r["format"]}",\n "date": "{r["date"]}",\n'
            f' "tasks": {{\n{json_lines(r["tasks"])}\n }},\n'
            f' "links": {{\n{json_lines(r["links"])}\n }}\n}}\n')


def read_releves(folder):
    """The relevés of a referential folder, v1 and v2, oldest first: [(date, relevé)]."""
    found = []
    for path in sorted(glob.glob(os.path.join(folder, RELEVES, "*.json"))):
        match = RELEVE_NAME.match(os.path.basename(path))
        data = json.loads(read_text(path)) if match else None
        if data and data.get("format") in RELEVE_FORMATS:
            found.append((match.group(1), data))
    return found


def releve_hours(entry):
    """Hours one person spends on a task per month by hand (runs × hours per run), None when
    unknown: recomputed with today's rules from the facts a v2 relevé keeps, as written in a v1
    relevé."""
    if "hours" in entry:
        return entry["hours"]
    numbers = run_numbers(entry)
    return round(numbers[0] * numbers[1], 2) if numbers else None


def hours_freed(old, new, now=None):
    """Hours per month a task no longer takes, all its people together, when its status goes
    from `old` to `new` (negative when it takes more); None when its time is unknown or a
    status is J. The time is that of the earlier relevé, else of the later one, else `now`: the
    time the referential gives the task today (a relevé of September 2026 often predates the
    frequency and effort ratings)."""
    hours = next((h for h in (releve_hours(old), releve_hours(new), now) if h is not None), None)
    left = TIME_LEFT.get(old["status"]), TIME_LEFT.get(new["status"])
    if hours is None or None in left or not old.get("people"):
        return None
    return round(hours * old["people"] * (left[0] - left[1]), 1)


def current_ids(r, idx):
    """A relevé with its tasks under their current ids (a former id, kept in `aliases`, gives
    the current one), its tools and its data links too. An entry under the current id wins
    over one under a former id."""
    tasks = {}
    for key in sorted(r["tasks"], key=lambda k: resolve(idx, k) == k):
        entry = dict(r["tasks"][key])
        if "tools" in entry:
            entry["tools"] = sorted({resolve(idx, x) for x in entry["tools"]})
        tasks[resolve(idx, key)] = entry
    links = {" ".join(resolve(idx, x) for x in k.split(" ", 1)): v
             for k, v in (r.get("links") or {}).items()}
    return {"format": r["format"], "tasks": tasks, "links": links}


def changes_between(prev, date, cur, types, now):
    """The lines of the table of changes between two successive relevés (current ids): a task
    added or removed; its status (with the hours it no longer takes), its number of people;
    between two v2 relevés, its target, its type, each tool added or removed; the AI's access to
    a data link. `type` is the task's type in the referential, else in the relevé; `now` gives
    the time the referential gives each task today."""
    lines, v2 = [], prev["format"] == cur["format"] == RELEVE_FORMAT

    def line(task, entry, field, before, after, **more):
        lines.append({"date": date, "task": task, "type": types.get(task) or entry.get("type"),
                      "field": field, "before": before, "after": after, **more})
    for task in sorted(set(prev["tasks"]) | set(cur["tasks"])):
        old, new = prev["tasks"].get(task), cur["tasks"].get(task)
        if old is None or new is None:
            line(task, old or new, "added" if old is None else "removed",
                 old and old["status"], new and new["status"])
            continue
        if old["status"] != new["status"]:
            line(task, new, "status", old["status"], new["status"],
                 hours=hours_freed(old, new, now.get(task)))
        fields = ("target", "people", "type") if v2 else ("people",)
        for field in fields:
            if old.get(field) != new.get(field) and (v2 or None not in (old.get(field),
                                                                      new.get(field))):
                line(task, new, field, old.get(field), new.get(field))
        tools = (set(old.get("tools") or []), set(new.get("tools") or [])) if v2 else (set(), set())
        for tool in sorted(tools[0] ^ tools[1]):
            line(task, new, "tool", tool if tool in tools[0] else None,
                 tool if tool in tools[1] else None)
    for key in sorted(set(prev["links"]) & set(cur["links"])):
        if prev["links"][key] != cur["links"][key]:
            data, tool = key.split(" ", 1)
            lines.append({"date": date, "data": data, "tool": tool, "field": "access",
                          "before": prev["links"][key], "after": cur["links"][key]})
    return lines


def history(ref):
    """The relevés of the referential up to its update date, whose relevé is the current state,
    under current ids, and the table of changes between successive relevés
    (README_operations.md §4): {"releves": [(date, relevé)], "changes": [line]}. A relevé dated
    after the update date is ignored. Needs enrich()."""
    date = last_updated(ref)
    if not date:
        return {"releves": [], "changes": []}
    found = [(d, r) for d, r in read_releves(ref["dir"]) if d < date] if ref.get("dir") else []
    idx = index(ref)
    rels = [(d, current_ids(r, idx)) for d, r in found + [(date, releve(ref))]]
    types = {t["id"]: t.get("type") for t in ref["tasks"]}
    now = {t["id"]: releve_hours(t) for t in ref["tasks"]}
    changes = []
    for (_, prev), (d, cur) in zip(rels, rels[1:]):
        changes += changes_between(prev, d, cur, types, now)
    return {"releves": rels, "changes": changes}


def render_changes(ref):
    """The table of changes as JSON: the dates of the relevés, then one change per line."""
    h = history(ref)
    lines = ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in h["changes"])
    return (f'{{\n "format": "{CHANGES_FORMAT}",\n'
            f' "releves": {json.dumps([d for d, _ in h["releves"]])},\n'
            f' "changes": [\n{lines}\n ]\n}}\n')


def change_key(c):
    """What a line of the table of changes is about: (kind, task or data source, tool or None).
    An added and a removed line are both about the presence of the task."""
    if c["field"] == "access":
        return "access", c["data"], c["tool"]
    if c["field"] == "tool":
        return "tool", c["task"], c["before"] or c["after"]
    return ("presence" if c["field"] in ("added", "removed") else c["field"]), c["task"], None


def compare(hist, base, date):
    """What changed between the relevé of `base` and that of `date`, from the lines of the table
    of changes dated after `base` up to `date`: the tasks whose status differs (with the hours
    they no longer take, the sum of their lines), the tasks added and removed, the tools added
    to a task, the data links the AI now reaches. A value is compared before the first line and
    after the last one: M → S then S → M is no change."""
    per = {}
    for c in hist["changes"]:
        if base < c["date"] <= date:
            per.setdefault(change_key(c), []).append(c)
    ends = {k: (cs[0]["before"], cs[-1]["after"]) for k, cs in per.items()}
    presence = {k[1]: (cs[0]["field"], cs[-1]["field"]) for k, cs in per.items()
                if k[0] == "presence"}
    moved = []
    for k, cs in per.items():
        if k[0] == "status" and ends[k][0] != ends[k][1] \
                and presence.get(k[1], ("", ""))[1] != "removed":
            known = [c["hours"] for c in cs if c["hours"] is not None]
            moved.append({"id": k[1], "from": ends[k][0], "to": ends[k][1],
                          "hours": round(sum(known), 1) if known else None})
    moved.sort(key=lambda m: (-(m["hours"] or 0), m["id"]))
    keys = sorted(per, key=lambda k: tuple(x or "" for x in k))
    return {"base": base, "date": date, "moved": moved,
            "added": sorted(t for t, p in presence.items() if p == ("added", "added")),
            "removed": sorted(t for t, p in presence.items() if p == ("removed", "removed")),
            "tools": [{"task": k[1], "tool": k[2]} for k in keys
                      if k[0] == "tool" and ends[k][0] is None and ends[k][1] is not None],
            "connectors": [{"data": k[1], "tool": k[2], "from": ends[k][0], "to": ends[k][1]}
                           for k in keys if k[0] == "access"
                           and ends[k][1] in CONNECTED and ends[k][0] not in CONNECTED]}


def history_data(ref):
    """For the explorer: each relevé with its counts, and the table of changes."""
    h = history(ref)
    return {"releves": [{"date": d, **counts(list(r["tasks"].values()))} for d, r in h["releves"]],
            "changes": h["changes"]}


# The tools the library ranks by task type: those that do the work (README_operations.md §1.11).
LIBRARY_KINDS = ("skill", "agent", "managed-agent")


def library(ref, hist=None):
    """The skills and agents by task type (README_operations.md §1.11). For each type of an
    active task that cites one: each tool with the tasks and the teams that cite it, and the
    status changes of those tasks dated on or after the relevé where the tool was added to the
    task (table of changes). A tool already cited in the first relevé that keeps tools has no
    known arrival: no change is counted for it. Types with the most tools first; `type` is None
    for the tasks without a type. Needs enrich()."""
    hist = hist or history(ref)
    idx, kinds = index(ref), {t["id"]: t.get("type") for t in ref["tools"]}
    teams = {r["id"]: r["team"] for r in ref["roles"]}
    added, moves = {}, {}
    for c in hist["changes"]:
        if c["field"] == "tool" and c["after"]:
            added[c["task"], c["after"]] = c["date"]
        elif c["field"] == "status":
            moves.setdefault(c["task"], []).append(c)
    per = {}
    for t in active(ref["tasks"]):
        for tool in dict.fromkeys(resolve(idx, x) for x in t.get("tools") or []):
            if kinds.get(tool) not in LIBRARY_KINDS:
                continue
            e = per.setdefault(t.get("type"), {}).setdefault(
                tool, {"tool": tool, "tasks": [], "teams": set(), "moves": []})
            e["tasks"].append(t["id"])
            e["teams"].add(teams.get(t["role"]))
            since = added.get((t["id"], tool))
            e["moves"] += [{"task": t["id"], "date": c["date"], "from": c["before"],
                            "to": c["after"], "hours": c["hours"]}
                           for c in moves.get(t["id"], []) if since and c["date"] >= since]
    rows = []
    for kind, tools in per.items():
        items = sorted(tools.values(), key=lambda e: (-len(e["tasks"]), e["tool"]))
        for e in items:
            e["teams"] = sorted(x for x in e["teams"] if x)
        rows.append({"type": kind, "tools": items,
                     "teams": sorted({x for e in items for x in e["teams"]})})
    return sorted(rows, key=lambda r: (-len(r["tools"]), r["type"] or "~"))


def library_stats(rows):
    """Skills and agents cited by active tasks, the types they serve, those serving several."""
    served = {}
    for r in rows:
        for e in r["tools"]:
            served.setdefault(e["tool"], set()).add(r["type"])
    return {"tools": len(served), "types": sum(1 for r in rows if r["type"]),
            "several": sum(1 for v in served.values() if len(v) > 1)}


# The index a session reads to find the task it is doing (README_operations.md §4.1), generated
# next to the views: from claude.ai, through the Drive copy of the OS, it is one file to read
# instead of 73.
INDEX = "index-taches.json"
INDEX_FORMAT = "rpt-index/v1"


INDEX_COLUMNS = ["name", "role", "type", "status"]


def task_index(ref):
    """Per role: its name, team and file. Per task not retired: its name, role, type and status
    (INDEX_COLUMNS, in that order). Per former id (`aliases`): the current one. Per skill or
    agent: the tasks that cite it."""
    idx, kinds = index(ref), {t["id"]: t.get("type") for t in ref["tools"]}
    roles = {r["id"]: {"name": r["name"], "team": r.get("team"), "file": r["_file"]}
             for r in ref["roles"]}
    tasks, aliases, skills = {}, {}, {}
    for t in ref["tasks"]:
        if t.get("state") == "retired":
            continue
        tasks[t["id"]] = [t["name"], t["role"], t.get("type"), t["status"]]
        aliases.update({a: t["id"] for a in t.get("aliases") or []})
        for tool in dict.fromkeys(resolve(idx, x) for x in t.get("tools") or []):
            if kinds.get(tool) in LIBRARY_KINDS:
                skills.setdefault(tool, []).append(t["id"])
    return {"format": INDEX_FORMAT, "updated": last_updated(ref), "columns": INDEX_COLUMNS,
            "roles": roles, "tasks": tasks, "aliases": aliases, "skills": skills}


def render_index(ref):
    """The index as JSON, one role, task, former id or skill per line."""
    i = task_index(ref)
    return (f'{{\n "format": "{INDEX_FORMAT}",\n "updated": "{i["updated"]}",\n'
            f' "columns": {json.dumps(i["columns"])},\n'
            + "".join(f' "{k}": {{\n{json_lines(i[k])}\n }},\n'
                      for k in ("roles", "tasks", "aliases"))
            + f' "skills": {{\n{json_lines(i["skills"])}\n }}\n}}\n')


# ----------------------------------------------------------------------- observations
# What a Claude session learns about a task while doing it (README_operations.md §4.1): one file
# per session in observations/, one change per line (a task, a field, the value before and
# after, how the fact is known, the sentence that proves it). The role files change only when
# the merge integrates the observations, after a GO; until then, the views do not change.
OBSERVATIONS = "observations"
OBSERVATION_FORMAT = "rpt-observation/v1"
OBSERVABLE = ("status", "target", "frequency", "measure", "input", "output", "output_files",
              "templates", "tools", "data", "okrs", "method", "by", "blocker", "blocker_type",
              "stakes", "job")
OBSERVATION_META = ["date", "observer", "surface", "source"]
CHANGE_KEYS = ["task", "data", "blocker", "agent", "tool", "field", "before", "after", "basis",
               "evidence", "result", "note"]
# What an observation can change on an agent of agents.yaml, and what a new agent gives
# (README_operations.md §1.16, §4.1): a skill improved, a schedule changed, a task added, a
# stage reached, without any task's status changing.
AGENT_OBSERVABLE = ("state", "stage", "schedule", "tasks", "skills", "data", "people", "zones",
                    "notify", "config", "log", "cost", "owner", "platform")
NEW_AGENT_REQUIRED = ("id", "name", "kind", "state")
# What an observation can change on a blocker of the register, and what a new blocker gives
# (README_operations.md §1.14, §4.1).
BLOCKER_OBSERVABLE = ("state", "resolution", "text", "type", "tasks", "owner")
NEW_BLOCKER_KEYS = ("text", "type", "tasks", "state", "owner", "source", "evidence", "notes")
EVIDENCE_MAX = 300
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_observations(folder):
    """The observation files of a referential folder: [(file name, content or YAMLError)]."""
    found = []
    for path in sorted(glob.glob(os.path.join(folder, OBSERVATIONS, "*.yaml"))):
        try:
            found.append((os.path.basename(path), normalize(yaml.safe_load(read_text(path)))))
        except yaml.YAMLError as exc:
            found.append((os.path.basename(path), exc))
    return found


def check_observations(ref):
    """(errors, warnings) of every observation file of the referential's folder."""
    errors, warnings = [], []
    for name, data in read_observations(ref["dir"]) if ref.get("dir") else []:
        e, w = check_observation(name, data, ref)
        errors, warnings = errors + e, warnings + w
    return errors, warnings


def check_observation(name, data, ref=None):
    """(errors, warnings) of one observation file. With the referential, each change is checked
    against what it names: the task exists, the value after is valid for the field, the value
    before is still the current one (else the change is stale: a warning). Without it (the skill
    in claude.ai), only the form of the file and of the values is checked."""
    if isinstance(data, Exception):
        return [tr("load.yaml_unreadable", file=name, error=data, hint=tr("hint.flow"))], []
    if not isinstance(data, dict) or data.get("format") != OBSERVATION_FORMAT:
        return [tr("obs.format", where=name, format=OBSERVATION_FORMAT)], []
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    errors = [tr("check.unknown_field", where=name, key=k) for k in data
              if k not in ("format", "meta", "changes")]
    errors += [tr("obs.meta_unknown", where=name, key=k) for k in meta
               if k not in OBSERVATION_META]
    if not DATE_RE.match(str(meta.get("date") or "")):
        errors.append(tr("obs.date", where=name))
    if not str(meta.get("observer") or "").strip():
        errors.append(tr("obs.observer", where=name))
    errors += check_enum(f"{name} meta", "surface", meta.get("surface"), "surface")
    changes = data.get("changes")
    if not isinstance(changes, list) or not changes:
        return errors + [tr("obs.changes", where=name)], []
    warnings, ctx = [], observation_context(ref)
    for i, c in enumerate(changes):
        e, w = check_change(c, f"{name} changes[{i}]", ctx)
        errors, warnings = errors + e, warnings + w
    return errors + check_target(name, changes, ctx), warnings


def slug(value):
    """An id as it ends an observation file name: CSM-T6.19 → csm-t6-19, data:crm → data-crm."""
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def change_target(c, idx=None):
    """What a change is about: ("task", its id, the current one when the referential is
    known), ("new", the role of the new task) or ("data", the data source); None if nothing."""
    if not isinstance(c, dict):
        return None
    if "data" in c:
        return ("data", str(c.get("data")))
    if c.get("agent") == "new":
        new_id = (c.get("after") or {}).get("id") if isinstance(c.get("after"), dict) else None
        return ("agent", str(new_id)) if new_id else None
    if c.get("agent"):
        return ("agent", str(c["agent"]))
    if c.get("blocker") == "new":
        # A new blocker belongs with the changes of the first task it holds back.
        tasks = (c.get("after") or {}).get("tasks") if isinstance(c.get("after"), dict) else None
        first = tasks[0] if isinstance(tasks, list) and tasks else None
        item = (idx or {}).get(first) if first else None
        return ("task", str(item["id"] if item else first)) if first else None
    if c.get("blocker"):
        return ("blocker", str(c["blocker"]))
    if c.get("task") == "new":
        role = (c.get("after") or {}).get("role") if isinstance(c.get("after"), dict) else None
        return ("new", str(role)) if role else None
    if c.get("task"):
        item = (idx or {}).get(c["task"])
        return ("task", str(item["id"] if item else c["task"]))
    return None


def check_target(name, changes, ctx):
    """One file, one target (README_operations.md §4.1): the changes of one task, the new tasks
    of one role, or the AI access to one data source. The file name ends with the target, so a
    session finds what already waits for its task by the file name alone."""
    targets = {change_target(c, ctx["idx"] if ctx else None) for c in changes} - {None}
    if len(targets) > 1:
        return [tr("obs.one_target", where=name,
                   targets=", ".join(sorted(x[1] for x in targets)))]
    if not targets:
        return []
    kind, target = targets.pop()
    ends = {slug(target)} | {slug(c.get("task")) for c in changes
                             if kind == "task" and isinstance(c, dict) and c.get("task")
                             and c.get("task") != "new"}
    if not DATE_RE.match(name[:10]) or not any(name.endswith(f"-{e}.yaml") for e in ends):
        return [tr("obs.file_name", where=name, slug=slug(target))]
    return []


def observation_context(ref):
    """What checking a change needs from the referential; None without one."""
    if not ref:
        return None
    return {"ref": ref, "idx": index(ref), "depts": {d.get("id") for d in ref["departments"]},
            "tools": {t.get("id") for t in ref["tools"]},
            "types": {x.get("id") for x in ref["task_types"]}}


def check_change(c, where, ctx):
    if not isinstance(c, dict):
        return [tr("obs.change_not_mapping", where=where)], []
    errors = [tr("check.unknown_field", where=where, key=k) for k in c if k not in CHANGE_KEYS]
    errors += check_enum(where, "basis", c.get("basis"), "observation_basis")
    if not c.get("basis"):
        errors.append(tr("obs.basis", where=where))
    evidence = c.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        errors.append(tr("obs.evidence", where=where))
    elif len(evidence) > EVIDENCE_MAX:
        errors.append(tr("obs.evidence_long", where=where, size=len(evidence), max=EVIDENCE_MAX))
    errors += check_enum(where, "result", c.get("result"), "result")
    if c.get("result"):
        ctx = None  # a processed change is history: the referential may have moved on since
    if sum(k in c for k in ("task", "data", "blocker", "agent")) != 1:
        return errors + [tr("obs.task_or_data", where=where)], []
    if "blocker" in c:
        return check_blocker_change(c, where, ctx, errors)
    if "agent" in c:
        return check_agent_change(c, where, ctx, errors)
    if "data" in c:
        return errors + check_connector_change(c, where, ctx), []
    if c.get("task") == "new":
        return errors + check_new_task(c, where, ctx), []
    if c.get("field") not in OBSERVABLE:
        return errors + [tr("obs.field", where=where, value=repr(c.get("field")),
                            fields=", ".join(OBSERVABLE))], []
    if not ctx:
        stub = {"id": str(c["task"]), "name": "-", "role": "X-R1", "state": "active",
                "status": "M", "_file": where}
        return errors + value_errors(dict(stub, **{c["field"]: c.get("after")}), where), []
    t = ctx["idx"].get(c["task"])
    if not t or t.get("id") not in {x["id"] for x in ctx["ref"]["tasks"]}:
        return errors + [tr("obs.task_unknown", where=where, task=c["task"])], []
    changed = {k: v for k, v in t.items() if k != c["field"]}
    if c.get("after") not in (None, [], ""):
        changed[c["field"]] = c["after"]
    e, _ = check_task(changed, ctx["idx"], ctx["depts"], ctx["tools"], ctx["types"])
    errors += [f"{where}: {x}" for x in e]
    warnings = []
    if not errors:
        now, before = empty_none(t.get(c["field"])), empty_none(c.get("before"))
        if same_value(c["field"], now, c.get("after")):
            warnings.append(tr("obs.already", where=where, id=t["id"], field=c["field"]))
        elif not same_value(c["field"], now, before):
            warnings.append(tr("obs.stale", where=where, id=t["id"], field=c["field"],
                               now=repr(now), before=repr(before)))
    return errors, warnings


def empty_none(value):
    return None if value in (None, [], "", {}) else value


def same_value(field, now, after):
    """True when the value proposed is already the current one. In the referential a measure
    carries its origin (`basis`); in an observation the origin is the change's."""
    if field == "measure":
        now, after = ({k: v for k, v in x.items() if k != "basis"} if isinstance(x, dict) else x
                      for x in (now, after))
    return empty_none(now) == empty_none(after)


def value_errors(t, where):
    """The checks of a task's values that do not need the referential."""
    return (check_enum(where, "status", t.get("status"), "status")
            + check_enum(where, "target", t.get("target"), "status")
            + check_enum(where, "blocker_type", t.get("blocker_type"), "blocker_type")
            + check_measure(t, where) + check_queue(t, where) + check_stakes(t, where)
            + check_job(t, where)
            + check_files(t, where, None)
            + [tr("obs.text_list", where=where, key=k) for k in ("tools", "data", "by")
               if t.get(k) is not None and not (isinstance(t[k], list)
                                                and all(isinstance(x, str) for x in t[k]))])


def check_new_task(c, where, ctx):
    after = c.get("after")
    if c.get("field") != "task" or not isinstance(after, dict):
        return [tr("obs.new_task_shape", where=where)]
    errors = [tr("obs.new_task_missing", where=where, key=k)
              for k in ("name", "role", "input", "output") if not after.get(k)]
    t = dict({"id": "NEW", "state": "active", "status": "M", "_file": where}, **after)
    if not ctx:
        return errors + value_errors(t, where)
    e, _ = check_task(t, ctx["idx"], ctx["depts"], ctx["tools"], ctx["types"])
    return errors + [f"{where}: {x}" for x in e]


def check_blocker_change(c, where, ctx, errors):
    """A change on the register (README_operations.md §1.14): a new blocker (`blocker: new`,
    `field: blocker`, `after` its text, type and tasks) or one field of an existing one."""
    idx = ctx["idx"] if ctx else None
    if c.get("blocker") == "new":
        after = c.get("after")
        if c.get("field") != "blocker" or not isinstance(after, dict):
            return errors + [tr("obs.new_blocker_shape", where=where)], []
        errors += [tr("check.unknown_field", where=where, key=k) for k in after
                   if k not in NEW_BLOCKER_KEYS]
        stub = dict({"id": "BLK-0", "state": "open", "opened": "2000-01-01",
                     "_file": where}, **after)
        e, _ = check_blocker(stub, idx)
        return errors + e, []
    if c.get("field") not in BLOCKER_OBSERVABLE:
        return errors + [tr("obs.field", where=where, value=repr(c.get("field")),
                            fields=", ".join(BLOCKER_OBSERVABLE))], []
    if not ctx:
        stub = {"id": str(c["blocker"]), "text": "-", "type": "other", "state": "open",
                "tasks": ["X-T1"], "opened": "2000-01-01", "_file": where}
        if c["field"] == "state" and c.get("after") in ("resolved", "dropped"):
            stub["resolved"] = "2000-01-02"
        e, _ = check_blocker(dict(stub, **{c["field"]: c.get("after")}), None)
        return errors + e, []
    b = ctx["idx"].get(c["blocker"])
    if not b or b.get("id") not in {x["id"] for x in ctx["ref"]["blockers"]}:
        return errors + [tr("obs.blocker_unknown", where=where, blocker=c["blocker"])], []
    changed = {k: v for k, v in b.items() if k != c["field"]}
    changed[c["field"]] = c.get("after")
    if c["field"] == "state":
        if c.get("after") in ("resolved", "dropped"):
            changed.setdefault("resolved", changed.get("opened"))
        else:
            changed.pop("resolved", None)
    e, _ = check_blocker(changed, ctx["idx"])
    errors += [f"{where}: {x}" for x in e]
    warnings = []
    if not errors:
        now, before = empty_none(b.get(c["field"])), empty_none(c.get("before"))
        if same_value(c["field"], now, c.get("after")):
            warnings.append(tr("obs.already", where=where, id=b["id"], field=c["field"]))
        elif not same_value(c["field"], now, before):
            warnings.append(tr("obs.stale", where=where, id=b["id"], field=c["field"],
                               now=repr(now), before=repr(before)))
    return errors, warnings


def check_agent_change(c, where, ctx, errors):
    """A change on agents.yaml (README_operations.md §1.16): a new agent (`agent: new`, `field:
    agent`, `after` its entry) or one field of an existing one."""
    idx = ctx["idx"] if ctx else None
    if c.get("agent") == "new":
        after = c.get("after")
        if c.get("field") != "agent" or not isinstance(after, dict):
            return errors + [tr("obs.new_agent_shape", where=where)], []
        errors += [tr("obs.new_agent_missing", where=where, key=k) for k in NEW_AGENT_REQUIRED
                   if not after.get(k)]
        if after.get("id") and not ID_RE["agent"].match(str(after["id"])):
            errors.append(tr("obs.agent_id", where=where, value=repr(after["id"])))
        if ctx and after.get("id") in {a.get("id") for a in ctx["ref"]["agents"]}:
            errors.append(tr("obs.agent_exists", where=where, agent=after["id"]))
        e, _ = check_agent(dict(after, _file=where), idx, criteria=bool(ctx))
        return errors + e, []
    if c.get("field") not in AGENT_OBSERVABLE:
        return errors + [tr("obs.field", where=where, value=repr(c.get("field")),
                            fields=", ".join(AGENT_OBSERVABLE))], []
    if not ctx:
        stub = {"id": str(c["agent"]), "name": "-", "kind": "routine", "state": "live",
                "_file": where, c["field"]: c.get("after")}
        e, _ = check_agent(stub, None, criteria=False)
        return errors + e, []
    a = idx.get(c["agent"])
    if not a or a.get("id") not in {x["id"] for x in ctx["ref"]["agents"]}:
        return errors + [tr("obs.agent_unknown", where=where, agent=c["agent"])], []
    changed = {k: v for k, v in a.items() if k != c["field"]}
    if c.get("after") not in (None, [], ""):
        changed[c["field"]] = c["after"]
    e, _ = check_agent(changed, idx)
    errors += [f"{where}: {x}" for x in e]
    warnings = []
    if not errors:
        now, before = empty_none(a.get(c["field"])), empty_none(c.get("before"))
        if same_value(c["field"], now, c.get("after")):
            warnings.append(tr("obs.already", where=where, id=a["id"], field=c["field"]))
        elif not same_value(c["field"], now, before):
            warnings.append(tr("obs.stale", where=where, id=a["id"], field=c["field"],
                               now=repr(now), before=repr(before)))
    return errors, warnings


def check_connector_change(c, where, ctx):
    errors = [] if c.get("field") == "connector" else \
        [tr("obs.connector_field", where=where)]
    errors += check_enum(where, "after", c.get("after"), "connector")
    if not c.get("tool"):
        errors.append(tr("obs.tool_expected", where=where))
    if ctx:
        d = ctx["idx"].get(c["data"])
        if not d or d.get("id") not in {x["id"] for x in ctx["ref"]["data_sources"]}:
            return errors + [tr("obs.source_unknown", where=where, data=c["data"])]
        if c.get("tool") and c["tool"] not in {e.get("tool") for e in d.get("tools") or []}:
            errors.append(tr("obs.not_a_tool_of", where=where, tool=c["tool"], data=d["id"]))
    return errors


def in_observations(ref, path):
    """True when the file is in the observations folder of the referential, where the build
    checks it and the merge keeps it with the result of each change."""
    folder = os.path.join(ref["dir"], OBSERVATIONS) if ref.get("dir") else None
    return bool(folder) and os.path.dirname(os.path.abspath(path)) == os.path.abspath(folder)


def pending_changes(ref):
    """[(file name, meta, change)] for every change the merge has not processed yet."""
    out = []
    for name, data in read_observations(ref["dir"]) if ref.get("dir") else []:
        if isinstance(data, dict):
            out += [(name, data.get("meta") or {}, c) for c in data.get("changes") or []
                    if isinstance(c, dict) and not c.get("result")]
    return out


def target_of(ref, value):
    """The target an id names for --task: a task (former ids included), the new tasks of a
    role, or a data source."""
    item = index(ref).get(value) or {}
    if item.get("id") in {r["id"] for r in ref["roles"]}:
        return ("new", item["id"])
    if str(value).startswith("data:"):
        return ("data", item.get("id") or str(value))
    if ID_RE["blocker"].match(str(value)):
        return ("blocker", str(value))
    if ID_RE["agent"].match(str(value)):
        return ("agent", str(value))
    return ("task", item.get("id") or str(value))


def pending_groups(ref, target=None):
    """{target: {field label: {value after: [(file, meta, change)]}}}: the pending changes,
    identical proposals of several sessions together (README_operations.md §4.1)."""
    idx, out = index(ref), {}
    for name, meta, c in pending_changes(ref):
        key = change_target(c, idx)
        if key is None or (target and key != target):
            continue
        label = f"{c.get('field')} ({c.get('tool')})" if key[0] == "data" else \
            tr("obs.label_new_blocker") if c.get("blocker") == "new" else \
            f"{c.get('blocker')} {c.get('field')}" if c.get("blocker") else \
            tr("obs.label_new_agent") if c.get("agent") == "new" else c.get("field")
        value = json.dumps(c.get("after"), ensure_ascii=False, sort_keys=True)
        out.setdefault(key, {}).setdefault(str(label), {}).setdefault(value, []).append(
            (name, meta, c))
    return out


def median_measure(values):
    """The median of the minutes and of the runs of several measures of one task."""
    out = {}
    for k in ("minutes", "runs"):
        xs = [v[k] for v in values if isinstance(v, dict) and isinstance(v.get(k), (int, float))]
        if xs:
            m = statistics.median(xs)
            out[k] = int(m) if float(m).is_integer() else round(m, 1)
    return out


def who_and_when(rows):
    """"Camille ×2, Ines, from 2026-10-06 to 2026-10-20" for the rows of one group."""
    people = {}
    for _, meta, _ in rows:
        people[str(meta.get("observer"))] = people.get(str(meta.get("observer")), 0) + 1
    dates = sorted(str(meta.get("date")) for _, meta, _ in rows)
    when = dates[0] if dates[0] == dates[-1] else tr("obs.span", start=dates[0], end=dates[-1])
    return ", ".join(p + (f" ×{n}" if n > 1 else "") for p, n in people.items()) + ", " + when


def print_observations(ref, target=None):
    """The pending changes by target, identical proposals counted once (§4.1)."""
    pending = pending_changes(ref)
    print(tr("obs.pending", changes=len(pending), files=len({name for name, _, _ in pending})))
    names = {t["id"]: t["name"] for t in ref["tasks"]}
    names.update({b["id"]: b.get("text") for b in ref["blockers"]})
    names.update({a["id"]: a.get("name") for a in ref["agents"]})
    for key, fields in sorted(pending_groups(ref, target).items()):
        title = {"task": names.get(key[1], ""), "new": tr("obs.title_new"),
                 "data": tr("obs.title_data"), "blocker": names.get(key[1], ""),
                 "agent": names.get(key[1], "") or tr("obs.label_new_agent")}[key[0]]
        print(f"\n{key[1]} {title}".rstrip())
        for field, values in fields.items():
            rows = [r for v in values.values() for r in v]
            if field == "measure" and len(rows) > 1:
                print(tr("obs.median", count=len(rows), median=json.dumps(
                    median_measure([c.get("after") for _, _, c in rows]))))
            elif len(values) > 1:
                print(tr("obs.to_decide", label=field, count=len(values)))
            for value, group in values.items():
                c = group[-1][2]
                print(tr("obs.line", label=field,
                         before=json.dumps(c.get("before"), ensure_ascii=False), after=value,
                         bases=", ".join(sorted({str(x.get("basis")) for _, _, x in group})),
                         count=len(group), who=who_and_when(group)))
                print(tr("obs.evidence_line", evidence=c.get("evidence"),
                         files=", ".join(n for n, _, _ in group)))


def observation_paths(ref):
    return sorted(glob.glob(os.path.join(ref["dir"], OBSERVATIONS, "*.yaml")))


def apply_observation(ref, path, only=None, today=None):
    """Apply to the role files (and to data-sources.yaml) the pending changes of one
    observation file whose value before is still the current one, then mark them `result:
    merged`. `only`: tokens "TASK" or "TASK:field" (or "data:x:connector") to apply; None:
    all. A new task is never applied: the merge writes it with its id. A change whose value is
    already the current one, selected or not, is closed (`merged`, note "already in the
    referential", in the organization's language): that is how the duplicates of an applied
    change leave the queue. Returns the applied, the skipped (with the reason) and the closed
    changes, as texts."""
    today = today or datetime.date.today().isoformat()
    obs = normalize(yaml.safe_load(read_text(path)))
    meta, idx, folder = obs.get("meta") or {}, index(ref), ref["dir"]
    source = f"observation {os.path.basename(path)} ({meta.get('observer')}, {meta.get('date')})"
    files, changed, applied, skipped, closed = {}, set(), [], [], []
    for c in obs.get("changes") or []:
        if "blocker" in c:
            if not c.get("result"):
                apply_blocker_change(ref, c, meta, source, only, files, changed,
                                     (applied, skipped, closed), os.path.basename(path), today)
            continue
        if "agent" in c:
            if not c.get("result"):
                apply_agent_change(ref, c, source, only, files, changed,
                                   (applied, skipped, closed), os.path.basename(path), today)
            continue
        label = f"{c.get('task') or c.get('data')} {c.get('field')}"
        token = {str(c.get("task") or c.get("data")),
                 f"{c.get('task') or c.get('data')}:{c.get('field')}"}
        selected = only is None or bool(token & set(only))
        item = idx.get(c.get("task") or c.get("data"))
        if c.get("result") or (not selected and (not item or item.get("_borrowed"))):
            continue
        if c.get("task") == "new" or not item or item.get("_borrowed"):
            reason = tr("apply.new_task") if c.get("task") == "new" else \
                tr("apply.not_found") if not item else tr("apply.borrowed", file=item["_file"])
            skipped.append(tr("apply.skipped", label=label, reason=reason))
            continue
        path_of = os.path.join(folder, item["_file"])
        data = files.setdefault(path_of, normalize(yaml.safe_load(read_text(path_of))))
        if is_current(data, item["id"], c):
            c["result"], c["note"] = "merged", tr("apply.already_note", view_language())
            closed.append(f"{label} ({os.path.basename(path)})")
            continue
        if not selected:
            continue
        reason = set_value(data, item["id"], c, source)
        if reason:
            skipped.append(tr("apply.skipped", label=label, reason=reason))
            continue
        (data.setdefault("meta", {}))["updated"] = today
        c["result"] = "merged"
        changed.add(path_of)
        applied.append(label)
    for path_of in changed:
        header = header_of(read_text(path_of)) if os.path.exists(path_of) else []
        write_text(path_of, canonical_text(files[path_of], header))
    if applied or closed:
        write_text(path, yaml.dump(obs, Dumper=Dumper, sort_keys=False, allow_unicode=True,
                                   width=10 ** 6))
    return applied, skipped, closed


def apply_blocker_change(ref, c, meta, source, only, files, changed, out, name, today):
    """Apply one change of the register (README_operations.md §1.14). A new blocker takes the
    next free id in blockers.yaml, `opened` the date of the observation; the same problem
    already open on the same tasks closes the change instead. A blocker that becomes resolved
    or dropped takes the date of the observation as `resolved`; reopened, it loses it."""
    applied, skipped, closed = out
    folder, date = ref["dir"], str(meta.get("date") or today)
    new = c.get("blocker") == "new"
    after = c.get("after") if isinstance(c.get("after"), dict) else {}
    first = (after.get("tasks") or [None])[0] if new else None
    label = f"{tr('obs.label_new_blocker')} ({first})" if new else \
        f"{c.get('blocker')} {c.get('field')}"
    token = {str(first), f"{first}:blocker"} if new else \
        {str(c.get("blocker")), f"{c.get('blocker')}:{c.get('field')}"}
    if only is not None and not token & set(only):
        return
    if new:
        path_of = os.path.join(folder, BLOCKERS_FILE)
        if path_of not in files:
            files[path_of] = normalize(yaml.safe_load(read_text(path_of))) \
                if os.path.exists(path_of) else {"format": FORMAT, "meta": {}, "blockers": []}
        data = files[path_of]
        items = data.setdefault("blockers", [])
        key = re.sub(r"\W+", " ", str(after.get("text") or "").lower()).strip()
        if any(re.sub(r"\W+", " ", str(x.get("text") or "").lower()).strip() == key
               and set(x.get("tasks") or []) >= set(after.get("tasks") or [])
               and x.get("state") in ("open", "in_progress") for x in items):
            c["result"], c["note"] = "merged", tr("apply.already_note", view_language())
            closed.append(f"{label} ({name})")
            return
        numbers = [int(x["id"][4:]) for x in ref["blockers"] + items
                   if ID_RE["blocker"].match(str(x.get("id")))]
        entry = {"id": f"BLK-{max(numbers, default=0) + 1}", "text": after.get("text"),
                 "type": after.get("type"), "state": after.get("state") or "open",
                 "tasks": list(after.get("tasks") or []), "opened": date,
                 "owner": after.get("owner"), "source": after.get("source") or "observation",
                 "basis": c.get("basis"), "evidence": after.get("evidence") or c.get("evidence"),
                 "notes": after.get("notes"), "sources": [source]}
        if entry["state"] in ("resolved", "dropped"):
            entry["resolved"] = date
        items.append({k: v for k, v in entry.items() if v not in (None, [], "")})
    else:
        item = index(ref).get(c.get("blocker"))
        if not item or item.get("_borrowed") or "text" not in item:
            skipped.append(tr("apply.skipped", label=label, reason=tr("apply.not_found")))
            return
        path_of = os.path.join(folder, item["_file"])
        data = files.setdefault(path_of, normalize(yaml.safe_load(read_text(path_of))))
        b = next((x for x in data.get("blockers") or [] if x.get("id") == item["id"]), None)
        field = c.get("field")
        if not b:
            skipped.append(tr("apply.skipped", label=label, reason=tr("apply.not_found")))
            return
        if same_value(field, b.get(field), c.get("after")):
            c["result"], c["note"] = "merged", tr("apply.already_note", view_language())
            closed.append(f"{label} ({name})")
            return
        if not same_value(field, b.get(field), c.get("before")):
            skipped.append(tr("apply.skipped", label=label, reason=tr(
                "apply.stale", field=field, value=repr(b.get(field)))))
            return
        if empty_none(c.get("after")) is None:
            b.pop(field, None)
        else:
            b[field] = c.get("after")
        if field == "state":
            if c.get("after") in ("resolved", "dropped"):
                b["resolved"] = date
            else:
                b.pop("resolved", None)
        if source not in (b.get("sources") or []):
            b["sources"] = list(b.get("sources") or []) + [source]
    (data.setdefault("meta", {}))["updated"] = today
    c["result"] = "merged"
    changed.add(path_of)
    applied.append(label)


def apply_agent_change(ref, c, source, only, files, changed, out, name, today):
    """Apply one change of agents.yaml (README_operations.md §1.16). A new agent is added with
    its id; an agent that already has that id closes the change instead."""
    applied, skipped, closed = out
    new = c.get("agent") == "new"
    after = c.get("after") if isinstance(c.get("after"), dict) else {}
    agent_id = after.get("id") if new else c.get("agent")
    label = f"{tr('obs.label_new_agent')} ({agent_id})" if new else f"{agent_id} {c.get('field')}"
    token = {str(agent_id), f"{agent_id}:{'agent' if new else c.get('field')}"}
    if only is not None and not token & set(only):
        return
    folder = ref["dir"]
    if new:
        path_of = os.path.join(folder, AGENTS_FILE)
        if path_of not in files:
            files[path_of] = normalize(yaml.safe_load(read_text(path_of))) \
                if os.path.exists(path_of) else {"format": FORMAT, "meta": {}, "agents": []}
        data = files[path_of]
        items = data.setdefault("agents", [])
        if any(x.get("id") == agent_id for x in items):
            c["result"], c["note"] = "merged", tr("apply.already_note", view_language())
            closed.append(f"{label} ({name})")
            return
        entry = {k: v for k, v in after.items() if v not in (None, [], "")}
        entry.setdefault("basis", c.get("basis"))
        entry["sources"] = list(entry.get("sources") or []) + [source]
        items.append(entry)
    else:
        item = index(ref).get(agent_id)
        if not item or item.get("_borrowed") or item.get("id") not in \
                {a["id"] for a in ref["agents"]}:
            skipped.append(tr("apply.skipped", label=label, reason=tr("apply.not_found")))
            return
        path_of = os.path.join(folder, item["_file"])
        data = files.setdefault(path_of, normalize(yaml.safe_load(read_text(path_of))))
        a = next((x for x in data.get("agents") or [] if x.get("id") == item["id"]), None)
        field = c.get("field")
        if not a:
            skipped.append(tr("apply.skipped", label=label, reason=tr("apply.not_found")))
            return
        if same_value(field, a.get(field), c.get("after")):
            c["result"], c["note"] = "merged", tr("apply.already_note", view_language())
            closed.append(f"{label} ({name})")
            return
        if not same_value(field, a.get(field), c.get("before")):
            skipped.append(tr("apply.skipped", label=label, reason=tr(
                "apply.stale", field=field, value=repr(a.get(field)))))
            return
        if empty_none(c.get("after")) is None:
            a.pop(field, None)
        else:
            a[field] = c.get("after")
        if source not in (a.get("sources") or []):
            a["sources"] = list(a.get("sources") or []) + [source]
    (data.setdefault("meta", {}))["updated"] = today
    c["result"] = "merged"
    changed.add(path_of)
    applied.append(label)


def apply_observations(ref, paths, only=None, today=None):
    """apply_observation on several files, in order: the first file that proposes a value
    applies it, the files after it that propose the same value are closed."""
    applied, skipped, closed = [], [], []
    for path in paths:
        a, s, c = apply_observation(ref, path, only, today)
        applied, skipped, closed = applied + a, skipped + s, closed + c
    return applied, skipped, closed


def is_current(data, item_id, c):
    """True when the value a change proposes is already in the file's data."""
    if "data" in c:
        d = next((x for x in data.get("data_sources") or [] if x.get("id") == item_id), None)
        e = next((x for x in (d or {}).get("tools") or [] if x.get("tool") == c.get("tool")), None)
        return bool(e) and empty_none(e.get("connector")) == empty_none(c.get("after"))
    t = next((x for x in data.get("tasks") or [] if x.get("id") == item_id), None)
    return bool(t) and same_value(c.get("field"), t.get(c.get("field")), c.get("after"))


def set_value(data, item_id, c, source):
    """Set the observed value in the file's data; a reason when the change cannot apply."""
    if "data" in c:
        d = next((x for x in data.get("data_sources") or [] if x.get("id") == item_id), None)
        e = next((x for x in (d or {}).get("tools") or [] if x.get("tool") == c.get("tool")), None)
        if not e:
            return tr("apply.tool_absent", tool=c.get("tool"))
        if empty_none(e.get("connector")) != empty_none(c.get("before")):
            return tr("apply.stale", field="connector", value=repr(e.get("connector")))
        e["connector"] = c.get("after")
        return None
    t = next((x for x in data.get("tasks") or [] if x.get("id") == item_id), None)
    if not t:
        return tr("apply.task_absent")
    field = c["field"]
    if not same_value(field, t.get(field), c.get("before")):
        return tr("apply.stale", field=field, value=repr(t.get(field)))
    after = c.get("after")
    if field == "measure" and isinstance(after, dict) and "basis" not in after:
        after = dict(after, basis=c.get("basis"))  # a measure carries its own origin (§1.6)
    if empty_none(after) is None:
        t.pop(field, None)
    else:
        t[field] = after
    if field != "measure":
        t.setdefault("basis", {})[field] = c.get("basis")
    if source not in (t.get("sources") or []):
        t["sources"] = list(t.get("sources") or []) + [source]
    return None


# ------------------------------------------------------------------------ markdown view
# Every function of the view takes `lang`, the language it is written in: the organization's
# (view_language()) when the build writes referentiel.md. Its labels are in rpt_i18n.LABELS.


def cell(value):
    text = ", ".join(value) if isinstance(value, list) else str(value or "")
    return text.replace("|", "\\|").replace("\n", " ")


def fmt_percent(value, lang=None):
    return tr("fmt.percent", lang, value=value)


def fmt_counts(c, lang=None):
    cov = "—" if c["coverage"] is None else fmt_percent(c["coverage"], lang)
    return f"{c['total']} | {c['A']} | {c['S']} | {c['C']} | {c['M']} | {c['J']} | {cov}"


def md_header(ref, lang=None):
    return [
        "---", f"name: {tr('md.name', lang)}", "status: live",
        f"last_updated: {last_updated(ref)}", GENERATED_MARK,
        "related_files:", "  - ./README_operations.md", "---", "",
        tr("md.title", lang), ""] + tr("md.intro", lang, max=RELEVANCE_MAX).split("\n") + [""]


def md_figures(ref, st, lang=None):
    lines = [tr("md.figures", lang), "", tr("md.teams_header", lang),
             "|---|---|---|---|---|---|---|---|---|---|"]
    for team, s in st["teams"].items():
        lines.append(f"| {team} | {s['roles']} | {s['processes']} | {s['proposed']} | "
                     f"{fmt_counts(s['tasks'], lang)} |")
    lines += ["", tr("md.departments_header", lang), "|---|---|---|---|---|---|---|"]
    for d in ref["departments"]:
        c = st["departments"][d["id"]]
        if c["total"]:
            lines.append(f"| {entry_name(d, lang)} (`{d['id']}`) | "
                         f"{fmt_counts(c, lang)} |")
    tasks = active(ref["tasks"])
    shared = [t["id"] for t in tasks if len(t["_processes"]) > 1]
    loose = [t for t in tasks if not t["_processes"]]
    rated = [t for t in tasks if relevance_score(t)]
    ty, lib = st["types"], st["library"]
    lines += ["", tr("md.shared", lang, count=len(shared), ids=", ".join(shared) or "—"),
              tr("md.loose", lang, count=len(loose)),
              tr("md.chains", lang, count=len(ref.get("_chains") or []),
                 linked=sum(1 for c in ref.get("_chains") or [] if len(c["processes"]) > 1),
                 volume=sum(1 for c in ref.get("_chains") or [] if c["volume"])),
              tr("md.rated", lang, rated=len(rated), total=len(tasks)),
              tr("md.typed", lang, typed=ty["typed"], total=len(tasks), used=ty["used"],
                 catalogue=ty["catalogue"]),
              tr("md.library_line", lang, tools=lib["tools"], types=lib["types"],
                 several=lib["several"])]
    return lines + [""]


def md_profile(ref, lang=None):
    """The AI profile of the company, then of each team (README_operations.md §1.18)."""
    p = ai_profile(ref)
    if not p:
        return []
    c = p["company"]

    def name(e):
        return label("ai_profile", e["profile"], lang, e["profile"])
    het = tr("md.profile_het", lang, lo=c["spread"][0], hi=c["spread"][1]) \
        if c["heterogeneous"] else ""
    g = c["grade"]
    nxt = tr("md.profile_next", lang, letter=g["next"]["letter"], points=g["next"]["points"]) \
        if g["next"] else ""
    lines = [tr("md.profile_title", lang), "",
             tr("md.profile_company", lang, profile=name(c), het=het,
                **{k: c[k]["level"] for k in PROFILE_AXES}), "",
             tr("md.profile_grade", lang, letter=g["letter"], points=g["points"], next=nxt), "",
             tr("md.profile_header", lang), "|---" * (len(PROFILE_AXES) + 4) + "|"]
    for team, e in p["teams"].items():
        lines.append(f"| {team} | {e['measures']['tasks']} | "
                     + " | ".join(str(e[k]["level"]) for k in PROFILE_AXES)
                     + f" | {e['grade']['letter']} | {name(e)} |")
    return lines + [""]


def md_sources(ref, lang=None):
    """The connectors to activate first, then each data source with its tools and its tasks."""
    if not ref["data_sources"]:
        return []
    names = {x["id"]: entry_name(x, lang) or x["id"]
             for x in ref["tools"] + ref["data_sources"]}
    lines = [tr("md.sources_title", lang), ""] + tr("md.sources_intro", lang).split("\n") + \
        ["", tr("md.connectors_title", lang), ""] + \
        tr("md.connectors_intro", lang).split("\n") + \
        ["", tr("md.connectors_header", lang), "|---|---|---|---|---|---|"]
    for row in [r for r in connector_rows(ref) if not r["reached"]]:
        gain = tr("md.gain", lang, hours=fmt_hours(row["gain"], lang), count=len(row["gains"])) \
            if row["gains"] else "—"
        lines.append(f"| {names.get(row['tool'], row['tool'])} (`{row['tool']}`) | "
                     f"{connector_labels(row['connectors'], lang)} | "
                     f"{cell(sorted(names.get(d, d) for d in row['data']))} | {row['ms']} | "
                     f"{len(row['tasks'])} | {gain} |")
    lines += md_rights(ref, names, lang)
    policy = ref.get("ai_policy") or {}
    per = {k: sum(1 for d in ref["data_sources"] if (d.get("_os") or {}).get("status") == k)
           for k in OS_STATUS}
    lines += ["", tr("md.sources_list", lang), "", md_policy(policy, lang), "",
              tr("md.sources_os", lang, **per), "",
              tr("md.sources_header", lang), "|---|---|---|---|---|---|---|---|---|"]
    idx = index(ref)
    for d in ref["data_sources"]:
        c = counts(active([t for t in ref["tasks"]
                           if d["id"] in {resolve(idx, x) for x in t.get("data") or []}]))
        tools = tr("md.separator", lang).join(
            tr("md.pair", lang, name=names.get(e.get("tool"), e.get("tool")),
               value=label("connector", e.get("connector"), lang))
            for e in d.get("tools") or [] if isinstance(e, dict))
        lines.append(f"| {cell(entry_name(d, lang))} (`{d['id']}`) | "
                     f"{label('os_status', (d.get('_os') or {}).get('status'), lang, '—')} | "
                     f"{sensitivity_cell(d, policy, lang)} | "
                     f"{cell(tools) or '—'} | {c['total']} | {c['A']} | {c['S']} | {c['C']} | {c['M']} | "
                     f"{c['J']} |")
    return lines + [""]


def md_rights(ref, names, lang=None):
    """The rights of the AI in each tool it reaches (README_operations.md §1.7): enabled, offered
    but not enabled, not offered."""
    tools = [t for t in ref["tools"] if t.get("rights")]
    if not tools:
        return []
    lines = ["", tr("md.rights_title", lang), "", tr("md.rights_intro", lang), "",
             tr("md.rights_header", lang), "|---|---|---|---|---|"]
    for t in tools:
        by_state = {s: [] for s in ("enabled", "available", "unavailable")}
        for r in t["rights"]:
            if isinstance(r, dict) and r.get("state") in by_state:
                verb = "" if r.get("action") == "other" else \
                    f"{label('right_action', r.get('action'), lang, r.get('action'))} "
                by_state[r["state"]].append(f"{verb}{r.get('what')}")
        lines.append(f"| {names.get(t['id'], t['id'])} (`{t['id']}`) | "
                     + " | ".join(cell(by_state[s]) or "—" for s in by_state)
                     + f" | {t.get('rights_checked', '')} |")
    return lines


def md_policy(policy, lang=None):
    """One line on the AI policy that gives the rules (§1.8)."""
    if not policy:
        return tr("md.policy_none", lang)
    who = policy.get("decided_by") or tr("md.policy_who_none", lang)
    origin = tr("md.policy_borrowed", lang) if policy.get("_borrowed") else \
        f"`{policy.get('_file')}`"
    rules = tr("md.separator", lang).join(
        tr("md.pair", lang, name=label("sensitivity", c, lang), value=label("ai_rule", r, lang))
        for c in SENSITIVITY_ORDER for r in [(policy.get("rules") or {}).get(c)] if r)
    return tr("md.policy", lang, name=policy.get("name") or tr("md.policy_unnamed", lang),
              origin=origin, who=who, rules=rules)


def sensitivity_cell(d, policy, lang=None):
    """The categories of a data source with the rule of each, and how they are known."""
    if d.get("sensitivity") is None:
        return tr("md.to_classify", lang)
    rules = (policy or {}).get("rules") or {}
    text = ", ".join(f"{label('sensitivity', c, lang)} "
                     f"({label('ai_rule', rules.get(c), lang, tr('md.rule_to_decide', lang))})"
                     for c in d["sensitivity"] or ["internal"])
    basis = (d.get("basis") or {}).get("sensitivity")
    return text + (f" — {label('basis', basis, lang)}" if basis in ENUMS["fact_basis"] else "")


def connector_labels(values, lang=None):
    """The labels of the connectors of a row, in the order of CONNECTOR_ORDER."""
    return ", ".join(label("connector", v, lang, str(v)) for v in
                     sorted(values, key=lambda v: CONNECTOR_ORDER.index(v)
                            if v in CONNECTOR_ORDER else 99))


def fmt_hours(hours, lang=None):
    """Hours as the view writes them: one decimal under 10, a decimal comma in French."""
    text = f"{hours:g}" if hours < 10 else str(round(hours))
    return text.replace(".", ",") if (lang or rpt_i18n.language()) == "fr" else text


def md_role(r, ref, idx, lang=None):
    tasks = [t for t in ref["tasks"] if t["role"] == r["id"]]
    c = counts(active(tasks))
    crit = r.get("criteria") or {}
    coverage = fmt_percent(c["coverage"] if c["coverage"] is not None else "—", lang)
    lines = [f"### {r['id']} — {r['name']}", "", r.get("mission", ""), "",
             tr("md.role_team", lang, team=r["team"], departments=cell(r["departments"])),
             tr("md.role_holders", lang, holders=cell(r.get("holders")),
                fallback=r.get("fallback") or "—"),
             tr("md.role_level", lang, level=r.get("level", "—"),
                criteria=", ".join(f"{k} {v}" for k, v in crit.items())),
             tr("md.role_tasks", lang, total=c["total"], A=c["A"], S=c["S"], C=c["C"], M=c["M"],
                J=c["J"],
                coverage=coverage),
             tr("md.role_verdict", lang, verdict=r.get("verdict", "")), ""]
    lines += md_routing(r, idx, lang) + md_processes(r, ref, idx, lang) + md_tasks(tasks, lang)
    if r.get("gaps"):
        lines += [tr("md.gaps", lang), ""] + [f"- {g}" for g in r["gaps"]] + [""]
    return lines


def md_routing(r, idx, lang=None):
    if not r.get("routing"):
        return []
    lines = [tr("md.routing", lang), "", tr("md.routing_header", lang), "|---|---|---|"]
    for route in r["routing"]:
        target = route.get("to")
        name = idx[target]["name"] if target in idx else ""
        text = f"{target} {name}".strip() + (tr("md.proposed", lang)
                                             if route.get("state") == "proposed" else "")
        lines.append(f"| {cell(route.get('case'))} | {cell(text)} | {route.get('status', '')} |")
    return lines + [""]


def md_handoff(h, lang=None):
    return (tr("md.handoff", lang, to=cell(h.get("to")), what=cell(h.get("what")))
            + (tr("md.handoff_via", lang, via=cell(h["via"])) if h.get("via") else "")
            + (tr("md.handoff_issues", lang, issues=cell(h["issues"])) if h.get("issues")
               else "") + ".")


def md_processes(r, ref, idx, lang=None):
    procs = [p for p in ref["processes"] if p["role"] == r["id"]]
    if not procs:
        return []
    lines = [tr("md.processes", lang), ""]
    for p in procs:
        steps = " → ".join(f"{s} ({idx[s]['status']})" for s in p["_steps"] if s in idx)
        lines.append(tr("md.process", lang, id=p["id"], name=p["name"], state=p["state"],
                        automation=label("automation", p.get("automation"), lang, "—"),
                        trigger=cell((p.get("trigger") or {}).get("what")),
                        steps=steps or "—", exit=cell(p.get("exit")))
                     + "".join(md_handoff(h, lang) for h in p.get("handoffs") or []
                               if isinstance(h, dict)))
    return lines + [""]


def md_tasks(tasks, lang=None):
    lines = [tr("md.tasks", lang), "", tr("md.tasks_header", lang),
             "|---|---|---|---|---|---|---|---|---|---|"]
    for t in tasks:
        flow = f"{cell(t.get('input'))} → {cell(t.get('output'))}"
        lines.append(f"| {t['id']} | {cell(t['name'])} | {cell(t.get('type'))} | {flow} | "
                     f"{cell(t.get('tools'))} | "
                     f"{cell(t.get('data'))} | {t['status']} | {t.get('target', '')} | "
                     f"{relevance_label(t)} | {t['state']} |")
    return lines + [""]


def relevance_label(t):
    """"24/36 (P1 F3 E1 D3 × R3)", "5/36 (P2 F? E3 D? × R?)", or "?" when no axis of the sum
    is estimated."""
    score = relevance_score(t)
    if not score:
        return "?"
    rel = t.get("relevance") or {}
    axes = [f"{letter}{axis_value(rel.get(axis)) or '?'}"
            for letter, axis in zip(RELEVANCE_LETTERS, RELEVANCE_AXES)]
    return f"{score}/{RELEVANCE_MAX} ({' '.join(axes[:-1])} × {axes[-1]})"


def render_markdown(ref, lang=None):
    """referentiel.md, in `lang` (default: the organization's language)."""
    lang = lang or view_language()
    idx = index(ref)
    lines = md_header(ref, lang) + md_figures(ref, stats(ref), lang) + md_profile(ref, lang) + \
        md_sources(ref, lang) + \
        [tr("md.roles", lang), ""]
    for r in sorted(ref["roles"], key=lambda x: (x["team"], role_number(x["id"]))):
        lines += md_role(r, ref, idx, lang)
    lines += md_library(ref, lang) + md_okrs(ref, lang) + md_blockers(ref, lang) + \
        md_os(ref, lang) + md_decisions(ref, lang) + md_people(ref, lang) + md_agents(ref, lang) + \
        md_datamap(ref, lang)
    return "\n".join(lines).rstrip() + "\n"


def okr_coverage(ref):
    """Per key result: the active tasks linked to it and the hours a month their people would get
    back at target; per team: the active tasks linked to no key result (README_operations.md
    §1.13). The OKR skills read this (ts-general-okr-gaps)."""
    tasks = [t for t in ref["tasks"] if t.get("state") == "active"]
    teams = {r["id"]: r.get("team") for r in ref["roles"]}
    rows = []
    for o in ref["okrs"]:
        krs = [k for k in o.get("key_results") or [] if isinstance(k, dict)]
        for kr in krs + [{"id": k, "_shared": True} for k in o.get("shared_key_results") or []]:
            linked = [t for t in tasks if kr["id"] in (t.get("okrs") or [])]
            hours = sum((task_gain(t) or {}).get("hours", 0) for t in linked)
            rows.append({"okr": o["id"], "kr": kr["id"], "shared": bool(kr.get("_shared")),
                         "tasks": [t["id"] for t in linked], "hours": round(hours, 1),
                         "automated": sum(1 for t in linked if t.get("status") == "A")})
    unlinked = {}
    for t in tasks:
        if not t.get("okrs"):
            unlinked.setdefault(teams.get(t.get("role")) or "?", []).append(t["id"])
    return rows, unlinked


def md_okrs(ref, lang=None):
    """The OKR section of referentiel.md: the tree, each key result and its tasks."""
    if not ref["okrs"]:
        return []
    rows, unlinked = okr_coverage(ref)
    names = {kr["id"]: kr.get("name") for o in ref["okrs"] for kr in o.get("key_results") or []
             if isinstance(kr, dict)}
    lines = ["", tr("md.okrs_title", lang), "", tr("md.okrs_intro", lang), "",
             tr("md.okrs_header", lang), "|---|---|---|---|---|"]
    for o in ref["okrs"]:
        depth = str(o["id"]).count(".")
        text = f"{'↳ ' * depth}{o['id']} {o.get('name')}" + \
            (tr("md.proposed", lang) if o.get("state") == "proposed" else "")
        for r in [r for r in rows if r["okr"] == o["id"]] or [None]:
            shared = tr("md.shared_kr", lang) if r and r["shared"] else ""
            kr = f"{r['kr']} {names.get(r['kr'], '')}{shared}" if r else "—"
            lines.append(f"| {text} | {kr} | {len(r['tasks']) if r else 0} | "
                         f"{r['automated'] if r else 0} | {r['hours'] if r else 0} |")
            text = ""
    total = sum(len(v) for v in unlinked.values())
    lines += ["", tr("md.unlinked", lang, total=total, teams=", ".join(
        f"{k} {len(v)}" for k, v in sorted(unlinked.items())))]
    return lines


def md_blockers(ref, lang=None):
    """The blocker section of referentiel.md: the open and in-progress blockers first, the
    most hours blocked first, then the resolved and dropped ones, the latest first."""
    if not ref["blockers"]:
        return []
    live = [b for b in ref["blockers"] if b.get("state") in ("open", "in_progress")]
    done = [b for b in ref["blockers"] if b not in live]
    live.sort(key=lambda b: (-(b.get("_hours") or 0), str(b.get("opened"))))
    done.sort(key=lambda b: str(b.get("resolved") or ""), reverse=True)
    lines = ["", tr("md.blockers_title", lang), "",
             tr("md.blockers_intro", lang, open=len(live), done=len(done)), "",
             tr("md.blockers_header", lang), "|---|---|---|---|---|---|---|---|"]
    for b in live + done:
        state = label("blocker_state", b.get("state"), lang, b.get("state"))
        kind = label("blocker_type", b.get("type"), lang, b.get("type"))
        closed = f"{b.get('resolved')} · {cell(b.get('resolution'))}" if b.get("resolved") else ""
        lines.append(f"| {b['id']} | {cell(b.get('text'))} | {kind} | {state} | "
                     f"{cell(b.get('tasks'))} | {b.get('opened', '')} | "
                     f"{fmt_hours(b.get('_hours') or 0, lang) if b in live else ''} | {closed} |")
    return lines


def zones_in_order(ref):
    """The zones depth first, each with its depth; zones whose parent is unknown come first."""
    zones = {z["id"]: z for z in ref["os_zones"]}
    out = []

    def walk(z, depth):
        out.append((z, depth))
        for c in z.get("_children") or []:
            if c in zones:
                walk(zones[c], depth + 1)
    for z in ref["os_zones"]:
        if z.get("parent") not in zones:
            walk(z, 0)
    return out


def feed_label(f, names, lang=None):
    """A flow as the views write it: where it comes from, through which tool, in which state."""
    tool = f" · {names.get(f['tool'], f['tool'])}" if f.get("tool") else ""
    state = label("feed_state", f.get("state"), lang, f.get("state"))
    return f"{names.get(f.get('from'), f.get('from'))}{tool} ({state})"


def md_os(ref, lang=None):
    """The structure of the OS in referentiel.md (README_operations.md §1.15): the zones and the
    flows that feed them, the level of integration, the leaves to fill, the insights."""
    if not ref["os_zones"]:
        return []
    st = os_stats(ref)
    names = {x["id"]: entry_name(x, lang) for x in ref["data_sources"] + ref["tools"]
             + ref["os_zones"]}
    lines = ["", tr("md.os_title", lang), "",
             tr("md.os_intro", lang, zones=st["zones"], documents=st["documents"],
                questions=sum(st["insights"]["question"].values()),
                findings=sum(st["insights"]["finding"].values()), **st["feeds"]), "",
             tr("md.os_integration", lang, **st["integration"]), "",
             tr("md.os_maturity", lang, **st["maturity"]),
             tr("md.os_freshness", lang, **st["freshness"]), "",
             tr("md.os_header", lang), "|---|---|---|---|---|---|"]
    for z, depth in zones_in_order(ref):
        feeds = "<br>".join(feed_label(f, names, lang) for f in z.get("_feeds") or [])
        docs = "" if z.get("_documents") is None else z["_documents"]
        holds = label("zone_holds", z.get("holds"), lang, z.get("holds") or "")
        lines.append(f"| {'↳ ' * depth}{entry_name(z, lang)} | {cell(z.get('path'))} | {holds} | "
                     f"{docs} | {feeds} | {cell(z.get('_insights'))} |")
    possible = [(z, f) for z, _ in zones_in_order(ref) for f in z.get("_feeds") or []
                if f.get("state") == "possible"]
    if possible:
        lines += ["", tr("md.os_possible_title", lang), "", tr("md.os_possible_header", lang),
                  "|---|---|---|---|---|"]
        for z, f in sorted(possible, key=lambda x: -len(x[1].get("insights") or [])):
            tool = names.get(f.get("tool"), f.get("tool") or "")
            lines.append(f"| {names.get(f['from'], f['from'])} | {tool} | {entry_name(z, lang)} | "
                         f"{cell(f.get('what'))} | {cell(f.get('insights'))} |")
    if ref["insights"]:
        lines += ["", tr("md.insights_title", lang), "", tr("md.insights_header", lang),
                  "|---|---|---|---|---|---|---|"]
        for i in ref["insights"]:
            kind = label("insight_kind", i.get("kind"), lang, i.get("kind"))
            state = label("insight_state", i.get("state"), lang, i.get("state"))
            facts = f"{i.get('count')} · {i.get('accounts') or '?'}" if i.get("count") else ""
            data = ", ".join(names.get(d, d) for d in i.get("_data") or {})
            lines.append(f"| {i['id']} | {kind} | {cell(i.get('text'))} | "
                         f"{names.get(i.get('zone'), i.get('zone'))} | {state} | {facts} | "
                         f"{data} |")
    return lines


def md_datamap(ref, lang=None):
    """Where the data is (README_operations.md §1.20): one row per container, under its data
    source, with its tool, its place, its size, its freshness and who keeps it."""
    if not ref["containers"]:
        return []
    st = datamap_stats(ref)
    tools = {t["id"]: t.get("name") for t in ref["tools"]}
    sources = {d["id"]: d for d in ref["data_sources"]}
    lines = ["", tr("md.datamap_title", lang), "",
             tr("md.datamap_intro", lang, total=st["containers"], sources=st["sources"],
                all=st["all_sources"], owned=st["owned"], **st["fresh"]), "",
             tr("md.datamap_header", lang), "|---|---|---|---|---|---|"]

    def order(c):
        return (str(c.get("data")), str(c.get("tool")), str(c.get("path") or c.get("name")))
    for c in sorted(ref["containers"], key=order):
        d = sources.get(c.get("data")) or {}
        items = c.get("items") if isinstance(c.get("items"), dict) else {}
        size = f"{items.get('count')} {items.get('unit') or ''}".strip() \
            if items.get("count") is not None else ""
        fresh = label("freshness", c.get("_fresh"), lang, c.get("_fresh"))
        if c.get("_age") is not None:
            fresh += tr("md.datamap_days", lang, n=c["_age"])
        who = ", ".join(c.get("_owners") or []) + (
            f" ({', '.join(c['_holders'])})" if c.get("_holders") else "")
        lines.append(f"| {c.get('id')} {c.get('name')} | {entry_name(d, lang) or c.get('data')} | "
                     f"{tools.get(c.get('tool'), c.get('tool'))} · `{c.get('path') or ''}` | "
                     f"{size} | {fresh} | {who or tr('md.datamap_nobody', lang)} |")
    return lines


def md_people(ref, lang=None):
    """Who reaches the OS and how (README_operations.md §1.16)."""
    if not ref["people"]:
        return []
    st = people_stats(ref)
    names = {t["id"]: t.get("name") for t in ref["tools"]}
    cov = map_coverage(ref, load_config()) or {"people": []}
    last = {p["id"]: p for p in cov["people"]}
    maps = [tr("md.people_maps", lang, mapped=cov["mapped"],
               base=tr("md.people_base_headcount", lang, n=cov["headcount"])
               if cov.get("headcount") else tr("md.people_base_known", lang),
               fresh=sum(1 for p in cov["people"] if p["days"] is not None and p["days"] <= 30),
               never=sum(1 for p in cov["people"] if not p["last"]))] if cov["people"] else []
    lines = ["", tr("md.people_title", lang), "",
             tr("md.people_intro", lang, total=st["people"], coverage=st["coverage"],
                **st["access"]), *([""] + maps if maps else []), "",
             tr("md.people_header", lang), "|---|---|---|---|---|"]
    for x in sorted(ref["people"], key=lambda x: (ACCESS_RANK.get(x.get("_access"), 9),
                                                  str(x.get("name")))):
        ways = "<br>".join(
            f"{label('access_mode', a.get('mode'), lang, a.get('mode'))}"
            + (f" · {names.get(a.get('tool'), a.get('tool'))}" if a.get("tool") else "")
            + (f" ({label('access_state', a.get('state'), lang, a.get('state'))}"
               + (f", {a['checked']}" if a.get("checked") else "") + ")"
               if a.get("state") else "")
            for a in x.get("os_access") or [] if isinstance(a, dict))
        state = label("access_state", x.get("_access"), lang, x.get("_access"))
        seen = (last.get(x.get("id")) or {}).get("last") or tr("md.never", lang)
        lines.append(f"| {x.get('name')} | {', '.join(x.get('_teams') or [])} | {seen} | "
                     f"{state} | {ways} |")
    return lines


def cost_cell(c, lang=None):
    """« $0.81 / run · $17.82 / month (estimate) », « included in the subscription », or empty."""
    if not c:
        return ""
    if c["billing"] == "subscription":
        return tr("md.cost_included", lang)
    month = tr("md.cost_month", lang, v=f"{c['per_month']:.2f}") if c["per_month"] is not None \
        else ""
    return tr("md.cost_run", lang, v=f"{c['per_run']:.2f}") + month + \
        (tr("md.cost_estimate", lang) if c["estimated"] else "")


def md_agents(ref, lang=None):
    """The agents that run recurring tasks (README_operations.md §1.16)."""
    if not ref["agents"]:
        return []
    st = agent_stats(ref)
    names = {t["id"]: t.get("name") for t in ref["tools"]}
    who = {x["id"]: x.get("name") for x in ref["people"]}
    intro = {k: v for k, v in st.items() if k != "stages"}
    lines = ["", tr("md.agents_title", lang), "",
             tr("md.agents_intro", lang, **intro, **st["stages"]), "",
             tr("md.agents_header", lang), "|---|---|---|---|---|---|---|---|"]
    for a in ref["agents"]:
        kind = label("agent_kind", a.get("kind"), lang, a.get("kind"))
        state = label("agent_state", a.get("state"), lang, a.get("state"))
        level = (a.get("_progress") or agent_progress(a))["stage"]
        stage = label("agent_stage", level, lang, level) if level else "—"
        platform = names.get(a.get("platform"), a.get("platform") or "")
        people_ = ", ".join(who.get(p, p) for p in a.get("people") or [])
        kind += f" · {platform}" if platform else ""
        lines.append(f"| {cell(a.get('name'))} | {kind} | {state} | {stage} | "
                     f"{cell(a.get('schedule'))} | {cell(a.get('tasks'))} | {people_} | "
                     f"{cost_cell(a.get('_cost') or agent_cost(a), lang)} |")
    return lines


def md_decisions(ref, lang=None):
    """The business decisions and the artifacts of the OS (README_operations.md §1.17)."""
    if not ref["decisions"] and not ref["artifacts"]:
        return []
    st = os_stats(ref)
    lines = ["", tr("md.decisions_title", lang), "",
             tr("md.decisions_intro", lang, products=st["products"],
                traced=st["decisions_traced"], **st["decisions"], **st["artifacts"])]
    if ref["decisions"]:
        lines += ["", tr("md.decisions_header", lang), "|---|---|---|---|---|---|---|"]
        for d in ref["decisions"]:
            kind = label("decision_kind", d.get("kind"), lang, d.get("kind"))
            state = label("decision_state", d.get("state"), lang, d.get("state"))
            lines.append(f"| {d['id']} {cell(d.get('name'))} | {kind} | {state} | "
                         f"{cell(d.get('depends_on'))} | {cell(d.get('decided_through'))} | "
                         f"{cell(d.get('_shared_by'))} | {cell(d.get('activates'))} |")
    if ref["artifacts"]:
        lines += ["", tr("md.artifacts_header", lang), "|---|---|---|---|---|---|"]
        for a in ref["artifacts"]:
            p = a.get("purpose") or {}
            goal = label("artifact_goal", p.get("goal"), lang, p.get("goal") or "")
            state = label("artifact_state", a.get("state"), lang, a.get("state") or "")
            what = p.get("audience") or ""
            what += f" — {p['question']}" if p.get("question") else ""
            lines.append(f"| {a['id']} {cell(a.get('name'))} | {goal} | {cell(what)} | "
                         f"{cell(a.get('depends_on'))} | {cell(a.get('produced_by'))} | "
                         f"{state} |")
    return lines


def print_okrs(ref):
    """--okrs: the coverage of each key result, then the tasks linked to none, by team."""
    rows, unlinked = okr_coverage(ref)
    for r in rows:
        print(tr("okrs.kr", kr=r["kr"], shared=tr("md.shared_kr") if r["shared"] else "",
                 count=len(r["tasks"]), automated=r["automated"], hours=r["hours"],
                 tasks=", ".join(r["tasks"]) or tr("word.none")))
    for team, ids in sorted(unlinked.items()):
        print(tr("okrs.unlinked", team=team, count=len(ids), ids=", ".join(ids)))


def md_library(ref, lang=None):
    """The skills and agents by task type, one row per type (README_operations.md §1.11)."""
    names = {t["id"]: entry_name(t, lang) for t in ref["task_types"]}
    rows = library(ref)
    lines = [tr("md.library_title", lang), "", tr("md.library_intro", lang), "",
             tr("md.library_header", lang), "|---|---|---|"]
    for r in rows:
        kind = f"{names.get(r['type'], r['type'])} (`{r['type']}`)" if r["type"] \
            else tr("md.without_type", lang)
        tools = ", ".join(f"`{e['tool']}` ({len(e['tasks'])})" for e in r["tools"])
        lines.append(f"| {cell(kind)} | {cell(tools)} | {cell(r['teams'])} |")
    return lines + [""]


def role_number(role_id):
    match = re.search(r"-R(\d+)", role_id)
    return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------- HTML view

def render_html(ref):
    template = read_text(TEMPLATE)
    payload = json.dumps(explorer_data(ref), ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")  # keep </script> out of the inline JSON
    org = ((load_config() or {}).get("organization") or {}).get("name") or \
        tr("html.organization", view_language())
    title = tr("html.title", view_language(), org=org)
    template = template.replace("__TITLE__", html.escape(title))
    template = template.replace("__DESCRIPTION__",
                                html.escape(tr("html.description", view_language())))
    template = template.replace("__ORG__", html.escape(str(org)))
    return template.replace("/*__RPT_DATA__*/null", payload)


# ---------------------------------------------------------------------------- formatter

class Dumper(yaml.SafeDumper):
    """Block style for entities, flow style for short lists and short records, lists indented
    under their key, no line folding (a changed word changes one line in a diff)."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _short(data, limit):
    return len(json.dumps(data, ensure_ascii=False)) <= limit


def _list(dumper, data):
    flow = all(isinstance(x, (str, int, float)) for x in data) and _short(data, 90)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)


def _dict(dumper, data):
    flat = all(not isinstance(v, dict) and not (isinstance(v, list) and len(v) > 3)
               for v in data.values())
    # An entity (id) and a tool of a data source (tool) stay in block style, one key per line.
    flow = "id" not in data and "tool" not in data and flat and _short(data, 110)
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=flow)


Dumper.add_representer(list, _list)
Dumper.add_representer(dict, _dict)


def ordered(kind, item):
    order = KEYS[kind]
    # An empty `sensitivity` says « internal data only »: it is kept, unlike other empty lists.
    out = {k: item[k] for k in order
           if k in item and (item[k] not in (None, [], "") or k in REQUIRED[kind]
                             or (k == "sensitivity" and item[k] == []))}
    if isinstance(out.get("basis"), dict):
        rank = {k: i for i, k in enumerate(order)}
        out["basis"] = dict(sorted(out["basis"].items(),
                                   key=lambda kv: (rank.get(str(kv[0]).split(".")[0], 99),
                                                   str(kv[0]))))
    for key in LOCALIZED_TEXTS + LOCALIZED_LISTS:
        if isinstance(out.get(key), dict):
            out[key] = by_language(out[key])
    for sub, keys in SUB_KEYS.items():
        if isinstance(out.get(sub), dict):
            out[sub] = {k: out[sub][k] for k in keys if k in out[sub]}
        elif isinstance(out.get(sub), list):
            out[sub] = [{k: v[k] for k in keys if k in v} if isinstance(v, dict) else v
                        for v in out[sub]]
    return out


def by_language(value):
    """A map by language in canonical order: the languages of the messages (en, fr), then the
    others in alphabetical order."""
    rank = {code: i for i, code in enumerate(rpt_i18n.LANGUAGES)}
    return dict(sorted(value.items(), key=lambda kv: (rank.get(kv[0], len(rank)), str(kv[0]))))


def format_file(path):
    """Rewrite one file in canonical style; keep its header comments."""
    text = read_text(path)
    new = canonical_text(normalize(yaml.safe_load(text)), header_of(text))
    if new != text:
        write_text(path, new)
        return True
    return False


def header_of(text):
    """The comment lines a file starts with."""
    header = []
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        header.append(line)
    return header


def canonical_text(data, header):
    """A referential file in canonical style, after its header comments."""
    out = {"format": data["format"]}
    if data.get("meta"):
        out["meta"] = data["meta"]
    if isinstance(data.get("ai_policy"), dict):
        out["ai_policy"] = {k: data["ai_policy"][k] for k in POLICY_KEYS if k in data["ai_policy"]}
    if isinstance(data.get("ai_investment"), dict):
        out["ai_investment"] = {k: data["ai_investment"][k] for k in INVESTMENT_KEYS
                                if k in data["ai_investment"]}
    for name in LISTS:
        if data.get(name):
            out[name] = [ordered(KIND_OF_LIST[name], x) for x in data[name]]
    body = yaml.dump(out, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=10 ** 6)
    body = re.sub(r"\n(  - id: )", r"\n\n\1", body)
    body = re.sub(r"\n(\w+:\n)", r"\n\n\1", body)
    body = re.sub(r"(\n\w+:\n)\n(  - )", r"\1\2", body)
    return "\n".join(header) + ("\n" if header else "") + body


# --------------------------------------------------------------------------------- main

def outputs(folder, ref):
    """The generated files: the two views, the relevé of the referential's update date, the
    table of changes and the index of the tasks."""
    files = {os.path.join(folder, "referentiel.md"): render_markdown,
             os.path.join(folder, "rpt-explorer.html"): render_html}
    if last_updated(ref):
        files[os.path.join(folder, RELEVES, last_updated(ref) + ".json")] = render_releve
        files[os.path.join(folder, RELEVES, CHANGES)] = render_changes
    files[os.path.join(folder, INDEX)] = render_index
    return files


def write_or_check(ref, folder, check):
    stale = []
    for path, render in outputs(folder, ref).items():
        content = render(ref)
        current = read_text(path) if os.path.exists(path) else None
        if current != content:
            if check:
                stale.append(os.path.basename(path))
            else:
                write_text(path, content)
    return stale


def print_stats(ref):
    st = stats(ref)
    ty = st["types"]
    print(tr("stats.types", typed=ty["typed"], active=ty["active"], used=ty["used"],
             catalogue=ty["catalogue"]))
    pending = pending_changes(ref)
    oldest = min((str(meta.get("date")) for _, meta, _ in pending), default=None)
    print(tr("obs.pending", changes=len(pending), files=len({name for name, _, _ in pending}))
          + (tr("obs.pending_oldest", date=oldest) if oldest else ""))
    lib = st["library"]
    print(tr("stats.skills", tools=lib["tools"], types=lib["types"], several=lib["several"]))
    for team, s in st["teams"].items():
        c = s["tasks"]
        print(tr("stats.team", team=team, roles=s["roles"], processes=s["processes"],
                 proposed=s["proposed"], total=c["total"], A=c["A"], S=c["S"], C=c["C"], M=c["M"],
                 J=c["J"], coverage=fmt_percent(c["coverage"])))
    for dept, c in st["departments"].items():
        if c["total"]:
            print(tr("stats.department", department=dept, total=c["total"],
                     coverage=fmt_percent(c["coverage"])))
    h = history(ref)
    if len(h["releves"]) > 1:
        ev = compare(h, h["releves"][-2][0], h["releves"][-1][0])
        up = [m for m in ev["moved"] if "J" not in (m["from"], m["to"])
              and STATUS_RANK[m["to"]] > STATUS_RANK[m["from"]]]
        print(tr("stats.since", date=ev["base"], up=len(up),
                 hours=round(sum(m["hours"] or 0 for m in up)),
                 connectors=len(ev["connectors"]), added=len(ev["added"])))


def print_problems(errors, warnings=()):
    for e in errors:
        print(tr("cli.error", message=e))
    for w in warnings:
        print(tr("cli.warning", message=w))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", default=DEFAULT_DIR)
    parser.add_argument("--catalogues", default=DEFAULT_DIR,
                        help="folder whose catalogues (departments, task types, tools, data "
                             "sources, AI policy) are borrowed")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--format", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--okrs", action="store_true",
                        help="print each key result with its tasks, then the tasks linked to none")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--warnings", action="store_true", help="print every warning")
    parser.add_argument("--observations", action="store_true",
                        help="list the pending observations, by task, identical ones together")
    parser.add_argument("--task", metavar="ID",
                        help="with --observations: only what waits for this task (a role: its "
                             "new tasks; a data source: the AI access to it)")
    parser.add_argument("--observation", metavar="FILE",
                        help="check one observation file (against the referential when --dir "
                             "holds one, else its form only)")
    parser.add_argument("--apply-observation", metavar="FILE",
                        help="apply the pending changes of an observation file to the role "
                             "files; \"all\": every file of observations/, in order")
    parser.add_argument("--only", help="with --apply-observation: TASK or TASK:field, "
                                       "comma-separated")
    parser.add_argument("--datamap-plan", metavar="FILE",
                        help="the containers of a crawl (data-map) matched against those of "
                             "--dir: same container, or new (README_operations.md §1.20)")
    parser.add_argument("--config", metavar="FILE",
                        help="the organization's rpt-config.yaml; default: the environment "
                             "variable RPT_CONFIG, else rpt-config.yaml in --dir or one of its "
                             "two parents, else none (never Teamstarter's for another folder)")
    parser.add_argument("--config-check", metavar="FILE", nargs="?", const=CONFIG,
                        help="check an organization's rpt-config.yaml (default: the OS's)")
    parser.add_argument("--lang", metavar="CODE",
                        help="language of the messages (en, fr); default: the environment "
                             "variable RPT_LANG, else organization.language of rpt-config.yaml, "
                             "else en. The generated views stay in the organization's language")
    args = parser.parse_args(argv)
    global ACTIVE_CONFIG
    before = ACTIVE_CONFIG
    use_config(args.config, args.dir)
    try:
        return dispatch(args)
    finally:
        ACTIVE_CONFIG = before


def dispatch(args):
    """The run main asks for, once the configuration of --dir is chosen."""
    setup_language(args.lang)
    if args.config_check:
        return check_config_file(args.config_check)
    if args.observation:
        return check_one_observation(args)
    if args.datamap_plan:
        return print_datamap_plan(args)
    if args.format:
        changed = [os.path.basename(f) for f in yaml_files(args.dir) if format_file(f)]
        print(tr("cli.formatted", files=", ".join(changed) or tr("cli.nothing_to_change")))
    return run(args)


def check_config_file(path):
    """--config-check FILE: the errors, then the warnings, of a configuration."""
    warnings = []
    try:
        if os.path.exists(path):
            cfg = load_config(path)
            errors = check_config(cfg, os.path.basename(path))
            warnings = config_warnings(cfg, os.path.basename(path))
        else:
            errors = [tr("cli.not_found", file=path)]
    except yaml.YAMLError as e:
        errors = [tr("cli.config_yaml", file=path, error=e)]
    print_problems(errors, warnings)
    print(tr("cli.config_summary", errors=len(errors), file=path))
    return 1 if errors else 0


def print_datamap_plan(args):
    """--datamap-plan FILE: the crawl checked, then each of its containers matched against the
    data map of --dir: the container it updates, or a new one, with the active tasks of the
    referential that reach its data in its tool (candidates for `written_by`); then the
    containers of the data map, in the tools and under the paths the crawl read, that it did
    not see."""
    catalogue_dir = getattr(args, "catalogues", DEFAULT_DIR)
    crawl, errors = load(args.datamap_plan, catalogue_dir=catalogue_dir)
    if not errors:
        errors, warnings = validate(crawl)
    else:
        warnings = []
    print_problems(errors, warnings if args.warnings else [])
    if errors:
        print(tr("cli.summary", errors=len(errors), warnings=len(warnings)))
        return 1
    ref, ref_errors = load(args.dir, catalogue_dir=catalogue_dir)
    if not ref_errors and not validate(ref)[0]:
        enrich(ref)
    existing = [] if ref_errors else ref["containers"]
    seen = set()
    for c, match in datamap_plan(existing, crawl["containers"]):
        if match:
            seen.add(match.get("id"))
            print(tr("cli.datamap_same", id=c.get("id"), name=c.get("name"),
                     match=match.get("id")))
        else:
            print(tr("cli.datamap_new", id=c.get("id"), name=c.get("name"),
                     tool=c.get("tool"), path=c.get("path") or ""))
        tasks = [] if ref_errors else datamap_candidates(ref, c)
        if tasks:
            print(tr("cli.datamap_candidates", tasks=", ".join(tasks)))
    roots = {path_key(c) for c in crawl["containers"] if not c.get("parent")}
    for c in existing:
        tool, path = path_key(c)
        if c.get("id") not in seen and any(tool == t and path.startswith(p)
                                           for t, p in roots):
            print(tr("cli.datamap_unseen", id=c.get("id"), name=c.get("name"),
                     tool=c.get("tool"), path=c.get("path") or ""))
    return 0


# Words too common to tie a task to a place (README_operations.md §1.20, candidates).
PLACE_STOPWORDS = {"pour", "avec", "dans", "depuis", "chaque", "entre", "from", "with", "into",
                   "each", "their", "leur", "leurs", "client", "clients", "dossier", "dossiers",
                   "fichier", "fichiers", "document", "documents", "donnée", "données", "data",
                   "page", "pages", "folder", "folders", "file", "files", "équipe", "team"}
CANDIDATES_ALL = 8


def place_words(*texts):
    """The stems (first five letters) of the words of 4 letters or more, common words aside."""
    words = re.findall(r"[^\W\d_]{4,}", " ".join(str(t) for t in texts if t).lower())
    return {w[:5] for w in words if w not in PLACE_STOPWORDS}


def datamap_candidates(ref, c):
    """The active tasks of an enriched referential that reach the data of container `c` in its
    tool (their data links). Up to CANDIDATES_ALL of them, all, the closest first; beyond, only
    those whose name, input or output shares a word with the container (name, path, holds,
    naming), the closest first, ten at most."""
    hits = [t for t in ref["tasks"] if t.get("state") == "active"
            and any(l["data"] == c.get("data") and l["tool"] == c.get("tool")
                    for l in t.get("_data_links") or [])]
    place = place_words(c.get("name"), c.get("path"), c.get("holds"), c.get("naming"))
    score = {t["id"]: len(place & place_words(t.get("name"), t.get("input"), t.get("output")))
             for t in hits}
    hits.sort(key=lambda t: (-score[t["id"]], c.get("tool") not in (t.get("tools") or []),
                             t["id"]))
    if len(hits) > CANDIDATES_ALL:
        hits = [t for t in hits if score[t["id"]]][:10]
    return [t["id"] for t in hits]


def check_one_observation(args):
    """--observation FILE: the errors of one observation file, then its pending changes."""
    try:
        data = normalize(yaml.safe_load(read_text(args.observation)))
    except yaml.YAMLError as exc:
        data = exc
    ref = None
    if glob.glob(os.path.join(args.dir, "*.rpt.yaml")):
        ref, load_errors = load(args.dir, catalogue_dir=getattr(args, "catalogues", DEFAULT_DIR))
        ref = None if load_errors else ref
    errors, warnings = check_observation(os.path.basename(args.observation), data, ref)
    print_problems(errors, warnings)
    scope = tr("cli.scope_referential") if ref else tr("cli.scope_form")
    print(tr("cli.observation_summary", errors=len(errors), warnings=len(warnings), scope=scope))
    return 1 if errors else 0


def borrow_policy(args):
    """Whether --dir borrows the AI policy of --catalogues: not when it is Teamstarter's folder
    and the referential is another organization's."""
    folder = os.path.abspath(getattr(args, "catalogues", DEFAULT_DIR))
    return not (folder == os.path.abspath(DEFAULT_DIR) and other_organization())


def run(args):
    ref, errors = load(args.dir, catalogue_dir=getattr(args, "catalogues", DEFAULT_DIR),
                       policy=borrow_policy(args))
    if not errors:
        more, warnings = validate(ref)
        errors += more
        more, obs_warnings = check_observations(ref)
        errors, warnings = errors + more, warnings + obs_warnings
        cfg = load_config()
        if cfg is None and not args.validate_only and \
                os.path.abspath(args.dir) != os.path.abspath(DEFAULT_DIR):
            warnings.append(tr("warn.no_config", folder=args.dir))
        if cfg is not None:
            errors += check_config(cfg) + config_teams_errors(cfg, ref)
            warnings += config_warnings(cfg)
    else:
        warnings = []
    target = getattr(args, "apply_observation", None)
    if target and target != "all" and not in_observations(ref, target):
        errors.append(tr("cli.copy_first", file=target, folder=OBSERVATIONS))
    print_problems(errors, warnings if args.warnings else [])
    print(tr("cli.summary", errors=len(errors), warnings=len(warnings))
          + ("" if args.warnings or not warnings else tr("cli.warnings_hint")))
    if errors:
        return 1
    enrich(ref)
    if target:
        only = [x.strip() for x in args.only.split(",")] if args.only else None
        paths = observation_paths(ref) if target == "all" else [target]
        applied, skipped, closed = apply_observations(ref, paths, only)
        print(tr("cli.applied", items=", ".join(applied) or tr("word.nothing")))
        print(tr("cli.closed", items=", ".join(closed) or tr("word.nothing")))
        for x in skipped:
            print(tr("cli.left", item=x))
        ref, errors = load(args.dir, catalogue_dir=getattr(args, "catalogues", DEFAULT_DIR),
                           policy=borrow_policy(args))
        enrich(ref)
    if getattr(args, "observations", False):
        task = getattr(args, "task", None)
        print_observations(ref, target_of(ref, task) if task else None)
    if args.stats:
        print_stats(ref)
    if getattr(args, "okrs", False):
        print_okrs(ref)
    if args.validate_only:
        return 0
    stale = write_or_check(for_views(ref), args.dir, args.check)
    if stale:
        print(tr("cli.stale", files=", ".join(stale)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
