---
name: ts-general-rpt-setup
description: "Set up the RPT referential (roles, processes, tasks) in an organization: run a short interview with the person who sets it up, write their organization's rpt-config.yaml file (name, language, Drive folders of the referential and of the intake, intake address, teams and their codes, owners, confidentiality, Claude global context text), check it with the shipped script, show it to them in full, then, after their approval, put it at the root of the organization's OS folder; optionally propose the structure of their OS (its zones, the data that could feed each one, the questions it would answer) and say what to do next. Use when someone wants to set up RPT, the mapping of roles and tasks, or the Teamstarter skills in their company, fill in an rpt-config.yaml or its template, or says 'configure RPT for my company', 'set up RPT', « configure RPT pour ma boîte » or « mets en place RPT »."
metadata:
  version: "1.10 (2026-10-21)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-rpt-setup; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Set up RPT in an organization

Speak and write to the person in their language, and ask the interview questions in that
language; this file is in English.

The RPT referential describes the **roles**, the **processes** and the **tasks** of an
organization, with, for each task, what is automated, run by the AI with a skill, helped by a chat, done by hand or decided
by a person. Three skills keep it up to date: the mapping (`ts-general-check-process-cartography`),
the observation (`ts-general-rpt-observe`) and the storing of deliverables (`ts-general-rpt-file`).

These skills contain nothing specific to an organization. They read a single file,
`rpt-config.yaml`, placed at the root of the organization's OS folder: its name, its language,
where the referential lives, where maps arrive, its teams, who is responsible for what, what is
never sent, and the text to paste into Claude's instructions. This skill writes that file with the
person who sets RPT up. Count 15 minutes.

You read no source without approval, you create no folder or file without approval, and the
person sees the whole file before it is put in place.

## Skill files

| File | When to read it |
|---|---|
| `references/rpt-config.template.yaml` | Before step 1: each field, with what it expects. It is the template you fill in. |
| `assets/exemple-rpt-config.yaml` | At step 5: a file filled in for a fictitious organization, whose form to copy. |
| `scripts/build_rpt.py` | At step 5: `python3 scripts/build_rpt.py --config-check rpt-config.yaml` checks the file. At step 7: `python3 scripts/build_rpt.py --dir <folder> --catalogues references --validate-only --warnings` checks the structure of the OS. |
| `references/data-sources.yaml` | At step 7: the kinds of business data a flow comes from (`from: data:…`). |
| `assets/os-structure.template.yaml`, `assets/insights.template.yaml` | At step 7: the zones of an OS, the flows that could feed them and the questions they would answer, drawn from Teamstarter's own OS. |

## Asking a question

Every question goes through the question tool when you have it: at most four questions per call,
closed answers, the recommended answer first with "(Recommended)" in the person's language, and
the person can always write something else. Without this tool, ask the questions as a numbered
list. Do not ask again a question that a previous message already answers.

## Step 1 — The organization and the person

Ask, in a single call:

1. the name of the organization, as its teams write it;
2. in one sentence, what it does;
3. the working language (`organization.language`, a language code such as `en` or `fr`; propose
   the language of the conversation first). The scripts print their messages in this language,
   and the referential's content (role names, task names, missions) is written in it;
4. the first and last name of the person who will maintain the referential: they will merge the maps that
   the teams send. If it is a team, its name ("the operations team").

A first and last name is the only personal data in the file: never a personal e-mail address, a
phone number.

## Step 2 — The folders

To start, RPT needs a single folder that the teams can read: the one that holds `rpt-config.yaml`.
The mapping works with this file alone, without an OS, a referential or catalogues: the first
maps can be made the day the file is in place (Vincent, 2026-10-18). The configuration still
names three folders, on the organization's Drive (Google Drive, or the equivalent it uses), under
an OS folder; the referential and the folder of merged maps can stay planned paths until the
first merge creates them:

| Folder | What it contains | Field |
|---|---|---|
| `<Organization>/OS/Operations/` | The referential: the role files, the task index | `referential.drive_folder` |
| `<Organization>/OS/to-process/` | The intake folder: the maps and observations sent by the teams | `intake.drive_folder` |
| `<Organization>/OS/documents-processed/Operations/` | The maps already merged | `referential.archive_drive_folder` |

Propose this folder layout, or ask where the organization already stores its shared documents and
adapt the paths. The intake folder is the one that should exist from the start: without it and
without an intake address, the skills drop the maps and observations in the folder of the
configuration. Then:

- **with the Google Drive connector**: ask for approval, then search whether these folders exist.
  If they do not exist and the tool can create a folder, propose to create them and do it only
  after a "yes". Take the intake folder's id from the tool's response (`intake.drive_folder_id`);
- **without the connector**: ask the person to create the folders, then to paste the link of the
  intake folder. The id is the end of the link, after `folders/`.

Then ask for:

- an intake e-mail address, for those who have no access to the Drive (a team address, not a
  personal address); without an address, `email: null`;
- who can read the intake folder (`intake.visibility`): the whole organization, or a team. The
  maps there are readable by these people: say so.

If the organization has a code repository where it keeps its documents, `repository` and
`repository_path` say so; otherwise `null`. `explorer` stays `null` as long as no explorer is
published.

## Step 3 — The teams

A team's code prefixes the ids of its roles and tasks (`sales` → `SALES-R1`, `SALES-T1.2`); it no
longer changes afterwards. Ask for the organization's teams, and propose as answers the most
common ones, which it keeps, renames or completes. Give the team names in the person's language:

| Code | Team (en) | Équipe (fr) | What it covers (`scope`) |
|---|---|---|---|
| `dir` | Management | Direction | management, strategy |
| `product` | Product | Produit | product, design |
| `tech` | Tech | Tech | development, infrastructure |
| `sales` | Sales | Ventes | sales, account development |
| `sdr` | Prospecting | Prospection | prospecting, appointment setting |
| `csm` | Customer success | Succès client | customer success, account support |
| `support` | Support | Support | customer support |
| `mkt` | Marketing | Marketing | marketing, communication |
| `rh` | HR | RH | HR, recruitment |
| `fin` | Finance | Finance | finance, administration, legal |
| `ops` | Operations | Opérations | production, logistics, purchasing |

The `scope` is written in the organization's language. A code is written in lower case, digits
and hyphens, short (2 to 8 characters), one per team. A person with several jobs will make one map
per team: there is no "everything" team.

Then ask, in a single question, **how many people the organization counts**
(`organization.headcount`, each person once) **and how many work in each team** (`teams[].headcount`,
a person who works for two teams counts in both): the explorer compares them with the people who
sent a map, for the company and team by team, and says who to remind. Show the teams kept, each
with an empty number to fill; "I don't know" leaves the number out (the script then warns, and the
coverage is computed on the people the referential knows).

## Step 4 — Confidentiality and owners

The file carries the default rule: nothing private, no internal review, no HR discussion, no
company health, no personal data other than the first and last name of a person who holds a role
or does a task, no client name. Ask whether the
organization wants to add a subject to the list (a confidential project, a subsidiary), without
describing it beyond its name.

Ask who is responsible for the AI policy (what an AI can receive, by type of data): a first and
last name, or "nobody for now" (`first_name: null`). Without their own policy, the skills apply the privacy
rules written in them.

## Step 5 — Write and check the file

Start from `references/rpt-config.template.yaml` and replace each `<…>`; the example
`assets/exemple-rpt-config.yaml` shows the form of each field. For `global_context`, keep the
template's text, in the organization's language, and replace the organization's name, the link
of the OS folder and the example id (a code of its teams): the text must fit in 900 characters,
to fit in the organization's instructions. The link of the OS folder (`<Organization>/OS/`, where
the file goes) is `referential.config_url` and goes on the `Config RPT` line: take it with the
Google Drive connector (the folder's URL), or ask the person to copy it from Drive. It is how the
skills, the same for every organization, find this file.

Write `rpt-config.yaml`, then run:

```bash
python3 scripts/build_rpt.py --config-check rpt-config.yaml
```

The script prints its messages in the organization's language. Fix each error and run it again
until it reports no error. A value between `<…>` that remains is a forgotten question: ask it.
Without a tool to run a script, read the file field by field against the template and tell the
person it was not checked by the script.

## Step 6 — Show, then put in place

Show the file **in full**, in an artifact if there is one, otherwise in a code block. Say what it
contains in three lines: the folders, the teams, who merges. Then ask with the question tool
"Shall I put it in place as is?", answers "Put in place as is" and "Change something". An approval
given before this display does not count.

After the approval, give the file to download, then:

1. **Google Drive**: create `rpt-config.yaml` in the folder `<Organization>/OS/`, next to the
   intake folder, as plain text (`text/plain`), conversion to Google Docs disabled. Check that the
   created file is not a Google Doc; otherwise, say so and ask the person to put the downloaded
   file there themselves.
2. **Without the connector**: the person puts the downloaded file at that location.

The skills find this file through the organization's instructions: `referential.config_url`
is the address where people open it (the link of the folder `<Organization>/OS/`, known before
the file exists, or the file's own link once it is in place), and `global_context` cites it on
the line `Config RPT (rpt-config.yaml) : <address>` (the script refuses a `global_context`
that does not cite it). Whoever uses the skills needs read access to this folder.

## Step 7 — The structure of the OS (optional)

An OS is worth what goes into it. Choosing which data enters it is choosing which questions it
can answer. This step shows the person how much their OS could hold. Ask first, with the question
tool: "Shall we also sketch the structure of your OS: its zones, the data that could feed them,
the questions they would answer? (10 minutes)", answers "Yes (Recommended)" and "Later".

With a "yes":

1. Read `assets/os-structure.template.yaml` and `assets/insights.template.yaml`. Show the zones as
   a short tree (name and one line each), then ask which ones the organization has or wants,
   which ones it names differently, and what is missing. Keep only what they choose.
2. For each flow of the kept zones, ask in which tool the organization keeps that data (its CRM,
   its meeting recorder, its survey tool, its help center), and whether something already brings
   it into the OS: a pipeline, a skill or a routine (`live`), someone by hand (`manual`), or
   nothing yet (`possible`, the template's default). Write the tool's name in `notes` when it is
   not in a tool catalogue: never invent an id.
3. Show the template's questions; ask which ones matter, and which questions the organization
   asks itself that are missing. Each kept question stays `unanswered`: the answers and the
   findings come later, from the data the flows bring in. Never invent a finding.
4. Write the two files in a working folder, then run
   `python3 scripts/build_rpt.py --dir <folder> --catalogues references --validate-only --warnings`
   and fix every error.
5. Show both files in full, with this sentence first: how many zones, how many flows in place,
   by hand and possible, and the three possible flows that would feed the most questions. Say
   that the OS is a tree: each zone is a branch, each flow a leaf, and a `possible` leaf is a
   leaf to fill — the opportunity tree of their OS, which the explorer shows dashed. Give the
   first level of integration (leaves filled out of all leaves, questions answered: none yet). Ask
   "Shall I put them in place as is?" and put them in the referential folder
   (`referential.drive_folder`, `<Organization>/OS/Operations/`), after a "yes" only, as plain
   text; if that folder does not exist yet, propose to create it, or put them next to
   `rpt-config.yaml`.

The structure holds no data of the organization: names of zones, of tools and questions only. No
client name, no person, no figure.

## Step 8 — What comes next

Tell the person, in this order:

1. Install the RPT skills in Claude (Settings, Capabilities, Skills), for the whole
   organization if the plan allows it: the same `.skill` files as every organization, given by
   the person who gave them this skill. They carry no value of any organization.
2. Paste the `global_context` text into the organization's instructions (or into their profile
   preferences): its `Config RPT` line is how the skills find `rpt-config.yaml`.
3. Have a first team mapped: in Claude, ask "map my roles and my processes" (« fais la carte de
   mes rôles et de mes process »). Nothing else is needed: no OS, no referential, no catalogue.
   The map arrives in the intake folder; the person who maintains the referential merges it,
   which creates the referential.
4. To know where the organization's data is (which tool, which folder, how fresh, who keeps
   it), have the people who reach the shared tools run the skill `ts-general-data-crawl` ("map
   where our data is", « cartographie nos données »): it describes the places of their Drive,
   Notion, HubSpot, Slack, Gmail and Jira without reading any content, and drops the data map in
   the same intake folder.

A change of folder, address or team is made in `rpt-config.yaml`; run this skill again with the
existing file, or edit it and check it with the script. The skills read the file at each use: no
new package is needed. When the file moves, update `referential.config_url` and the `Config RPT`
line, then the organization's instructions.

## What the skill does not do

- It does not map: that is `ts-general-check-process-cartography`, once installed.
- It reads no document of the organization and asks nothing about its activity beyond one
  sentence, its tools, and, at step 7, the questions it asks itself.
- It creates or moves nothing without approval, and keeps no personal data other than the first
  and last name of the people named in the file.
