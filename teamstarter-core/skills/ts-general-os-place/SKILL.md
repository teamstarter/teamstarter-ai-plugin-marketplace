---
name: ts-general-os-place
description: "When a member of the organization has produced a content with Claude (a document, a deck, a sheet, a page, a published artifact, an export, any generated file), ask whether it has a place in the organization's OS; if it does, give it one with its chain of data: declare it in the OS with the data it is made from and when it must be updated (or the process that updates it), store the file in the right folder of the shared Drive under the right name, and have that place described in the data layer of the OS (the data map). Leaves out private contents (payroll, HR files, health, confidential finance and legal files, capital, the board, credentials). Proposes everything and moves, renames or sends nothing without the person's approval. Use at the end of a conversation that produced a content, when the organization's global context asks for it, or when someone asks 'does this belong in the OS?', 'where should this go?', « ça a sa place dans l'OS ? », « range ce fichier », « inscris ça dans l'OS »."
metadata:
  version: "1.1 (2026-10-27)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-os-place; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Give a content its place in the OS

Speak and write to the person in their language; this file is in English.

The organization's OS is the set of files that describe how it works: the referential of roles,
processes and tasks, its zones and insights, its artifacts (`artifacts.yaml`) and its data map
(`data-map.yaml`, where each kind of data is kept). A content made with Claude and left in a
conversation, or put loose at the root of the Drive, is lost to the others, and the OS cannot
say where it is, what it is made from, or when it is out of date. This skill asks one question
about each content produced, and when the answer is yes, it gives the content three things:

1. **its entry in the OS**, with its chain of data: what it is made from, and when it must be
   updated, or the process that updates it;
2. **its place in the Drive**: the folder where people of the organization look for it, under the
   name the folder uses;
3. **its place in the data map**: the folder is described there, so that the OS knows where this
   kind of content is kept.

This skill decides and routes; the work of each step is done by the skill that already does it,
named at each step. Over time the Drive gets tidier and the OS describes more of what the
organization produces.

## When

- A conversation produced a content meant to be kept: a document, a deck, a spreadsheet, a page,
  a published artifact (claude.ai page, explorer, dashboard, canvas), an export, a generated
  file. Propose this skill once, at the end, never in the middle of the work.
- Someone asks whether a content belongs in the OS, or where to store it.

Not for an answer given in the conversation, a message sent, a ticket created (they are already
in their place), nor for a one-off personal content. In a session where nobody can answer
(autonomous worker, routine), propose nothing: write in the recap what would be placed and where.

## The organization's configuration

Read it as the skill `ts-general-rpt-file` does: the line `Config RPT (rpt-config.yaml) : <link>`
of the organization's instructions gives its address; never guess a value. It gives the folder of
the referential (`referential.drive_folder` or `referential.repository_path`), the intake folder
(`intake.drive_folder`, id `intake.drive_folder_id`) and what is never described or stored
(`privacy.excluded`, `privacy.not_filed`). In the referential, read `data-map.yaml` (the
places), `artifacts.yaml` (the artifacts), `os-structure.yaml` (the zones), `data-sources.yaml`
(the kinds of data) and `index-taches.json` (the tasks), when they exist.

## Step 1 — Is it a secret?

A content about payroll, an HR file (contract, review, recruitment of a named person, a warning),
health, confidential finance, a confidential legal file (a dispute, a contract under
negotiation), the capital, the shareholders or the board, credentials, or a subject of
`privacy.not_filed` or `privacy.excluded`, stays out of the OS and out of the shared Drive. Say
so in one sentence, suggest the person keeps it in their own space or in the restricted folder
their team uses, and stop. Do not describe it, not even as a placeholder.

## Step 2 — Does it have a place in the OS?

Yes when at least one is true:

- someone else, or the same person later, will look for it again;
- it is made from the organization's data (a figure, a list, a synthesis of documents) or feeds a
  decision;
- it will have to be redone or updated: each week, at each client, at each release.

No for a draft, a test, a content that only served the conversation. When the answer is no, say
it in one sentence and stop. When it is unclear, ask: "Will someone need this again?"

Then name what kind of content it is, which decides the next steps:

| Kind | Examples | Entry in the OS |
|---|---|---|
| **Deliverable of a task** of the referential | the monthly report of a client, the minutes of a workshop | the task's entry: skill `ts-general-rpt-file` (it stores the file where `output_files` says) |
| **Artifact**: a page or a file others consult, assembled from data | an explorer, a dashboard, a kit, a deck sent to a team, a white paper | an entry of `artifacts.yaml` |
| **Reference document**: written once, read often | a study, a procedure, a model, a brief | no entry of its own: its folder in the data map (step 5) |

## Step 3 — Its chain of data

List what the content is made from: the files, sheets, tools and conversations its figures and
facts come from. For each input, find it in the OS: a zone of `os-structure.yaml`, an insight, a
kind of data of `data-sources.yaml`, a place of `data-map.yaml`. Then:

- **an input the OS has**: name its id;
- **an input the OS does not have**: say it ("the figures come from a sheet the OS does not know
  of"). A file input gets its own place by this same skill, after the content; a tool's data
  is named as a kind of data to add;
- **when it must be updated**: ask, if the content does not say it. "When is a new version
  expected: never, at each change of its inputs, each week, each month, at each <event>?" The
  answer is the cycle (`refresh.cycle`: `once`, `on-change`, `daily`, `weekly`, `monthly`,
  `quarterly`, `manual`). A content that can be redone without anyone (a script, a skill) names
  that method (`produced_by`) and the agent that redoes it; otherwise the cycle is `manual` and
  the owner redoes it.

Never invent an input, a method or a cycle: what nobody knows is written as unknown.

For an **artifact**, this gives its entry: `depends_on` (the inputs), `produced_by` (the skill or
script), `refresh` (cycle, agent), `owner` (a person), `notify` (who is told of a new version on
Slack: the owner in a private message, or the existing channel where its readers already work,
never a general channel). With the organization's repository, write the entry in
`artifacts.yaml` in the session's PR; without it, write a file
`UPDATE-ARTIFACT-<slug>-<YYYY-MM-DD>.md` with these fields, show it in full, and after the
person's approval drop it in the intake folder, where the next pass of the OS turns it into the
entry. When the referential has a guide to declaring artifacts
(`README_declarer-agent-ou-artefact.md` next to `artifacts.yaml`), follow its model.

For a **deliverable of a task**, the chain is the task's: an input or a cycle its entry does not
say goes in an observation (skill `ts-general-rpt-observe`).

## Step 4 — Its place in the Drive

A deliverable of a task: the skill `ts-general-rpt-file` does this step; go to step 5.

Otherwise, find the folder in `data-map.yaml`: the containers of the shared Drive
(`tool: saas:google-drive`) whose kind of data (`data`), `holds` or `path` match the content, the
active ones first (`state: active`). Never the root of the Drive and never a container that
holds loose files waiting to be sorted. Then propose, in one message:

"This <kind> goes in `<path>` (<what the folder holds>), named `<name>` after the folder's
pattern (`naming`). Shall I put it there?"

The name follows the folder's `naming`, with the real values in place of the placeholders. When
no container fits, propose the closest parent folder and a new subfolder, and say that the data
map does not know of it yet. When the data map does not exist, ask the person where the team
keeps this kind of content.

After the approval: create or move the file there with the Google Drive connector (or the
connector of the tool that holds it), under that name. Same rules as `ts-general-rpt-file`, step
4: a copy, never an overwrite without a second approval; a new subfolder only with an approval
for that subfolder; delete nothing. Say what was done, with the link.

## Step 5 — Its place in the data map

The folder where the content went is a place of the data map:

- **described and still true** (`holds`, `naming`): nothing to write;
- **described but no longer true** (a new kind of file in it, a new naming), or **not described**
  (a new subfolder, a folder the data map does not know): it must be described.

To describe it, use the skill `ts-general-data-crawl` on that one folder: it reads its metadata
only, writes the container in the format of the data map, shows the preview and, after approval,
drops the file in the intake folder. With the organization's repository (Claude Code), write the
container in `OS/Operations/data-map.yaml` in the session's PR instead, and run
`python3 tools/build_rpt.py --dir OS/Operations --validate-only --warnings`.

A container describes the place, never the content: no client name, no amount, no person (the
rules of `ts-general-data-crawl`).

## Step 6 — Say what was placed

In three lines at most: the link of the stored file, the entry written or proposed (artifact,
observation, container), and what is left to do and by whom.

## Rules

- One proposal per conversation. Nothing is moved, renamed, created or sent without the person's
  approval of that action; the preview shows what will be sent.
- No client name, no personal data, no content of the file in what goes to the OS: an entry
  names a place, a pattern, an input, a cycle.
- Read only the folders needed to find the place, and name each folder before reading it.
