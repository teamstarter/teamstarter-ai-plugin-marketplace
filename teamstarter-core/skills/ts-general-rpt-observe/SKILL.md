---
name: ts-general-rpt-observe
description: "Propose the diff of a task of the organization's RPT referential when a work session with Claude learned something its entry does not say: duration, frequency, tools, data and AI access, method, where the deliverable goes, template, status, a missing task, or a blocker (a new problem that keeps the task from progressing, a known blocker in progress, resolved or dropped). Finds the task, compares the session with the entry, shows the diff and, after the person's approval, writes an observation (rpt-observation/v1): in the session's PR with Claude Code, in the intake folder (read from the organization's rpt-config.yaml) from claude.ai. Use at the end of a work task done with Claude, after a skill, a scheduled task, an agent or a connector of a task was created or changed (the agent's own entry included), when the global context asks for it, or when someone says 'update this task's entry', « mets à jour la fiche de cette tâche » or « ce bloqueur est levé »."
metadata:
  version: "1.11 (2026-10-26)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-rpt-observe; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Propose the diff of a task of the RPT referential

Speak and write to the person in their language; this file is in English.

The organization describes each task of the company in the RPT referential: its input, its
deliverable, its tools, its data, its duration, its automation status. Most entries have gaps:
83% of tasks have no measured duration, 92% have no link to a written method. A session that does
the task sees them. This skill reports them without an interview.

It also reports what keeps the task from progressing. The organization keeps its **blockers** in
a register, `blockers.yaml` in the referential folder (README_operations.md §1.14): one entry per
problem, with the tasks it holds back, its type and the state of its resolution. A session that
hits a problem (access refused, data missing, decision awaited, tool broken) proposes a new
blocker; a session that sees a known blocker move (someone works on it, it was lifted, it no
longer matters) proposes its new state.

It never writes in the referential. It writes an **observation**: a file that proposes changes,
field by field, with the value before, the value after and the sentence that proves them. The
person or team that maintains the referential (`intake.merged_by`) merges them in batches, after a
GO (skill `ts-general-rpt-merge`).

The person sees everything that is sent and gives their approval before it is sent.

**The organization's configuration.** The skill carries no data of any organization. The organization's
instructions (the global context Claude receives in every conversation) give the address of its
configuration, on a line such as `Config RPT (rpt-config.yaml) : <link>`: the Drive link of
the file, or of the folder at whose root it is (or its link in a repository). This file says where the referential
and the index are (`referential`: `drive_folder` on Drive, `repository` and `repository_path` in a
repository, `tools_path` for `build_rpt.py`, `explorer` for the explorer), and where observations
go (`intake`: the intake folder `drive_folder`, with Drive id `drive_folder_id`, the intake address
`email`, `observations_repository_path` in a repository, and `merged_by`, who merges them). Read it
first; this text says "the intake folder", "the intake address", "the referential folder" for these
values. An `rpt-config.yaml` that the person adds to the conversation replaces the one at the
address.

To read it: a `drive.google.com` link, with the Google Drive connector (the file whose id is
in the link; for a folder link, the file named `rpt-config.yaml` in that folder); a `github.com`
link, with the GitHub connector, or in Claude Code the file of a clone of that repository;
otherwise, fetch the link (a public file only). Without an address in the instructions, search
Drive for a file named `rpt-config.yaml` and have the person confirm it is their
organization's. If none works, ask the person to add the file to the conversation; it is in the
folder the organization's instructions link to. Never guess a value.

**Without a referential.** An observation completes an entry of the referential. When the
organization has no referential yet (no `index-taches.json` in the referential folder, which is
normal before the first maps are merged, or no OS at all), there is no entry to complete: say so
in one sentence and propose the mapping (`ts-general-check-process-cartography`) instead, which
needs nothing but `rpt-config.yaml`. Write no observation.

## When

- At the end of a work task done with Claude, when the organization's global context asks for it
  (`global_context` of the configuration), or when the task's prompt says so.
- After a change to the **tooling** of a task, even when the session felt like maintenance: a
  skill written or changed, a scheduled task or a routine created or changed, an agent improved,
  a connector added. These change what the entry says (status, tools, method, who does it,
  frequency, blockers). Find the tasks first: those whose `tools` or `method` cite the skill
  (`skills` list of the index), or whose blockers name the tool.
- When someone asks to update a task's entry, or to note what was just learned.

Not for a conversation that is not a work task, nor in a session where nobody can answer
(autonomous worker, routine): sending requires a person's approval. There, write in the run's
recap, in one line per task, what would change in its entry ("TECH-T11.16: status M → S,
blocker BLK-102 lifted"), so that the person who reads the recap can launch this skill. If the session learned
nothing that the entry does not already say, say so in one sentence and stop.

## Step 1 — Find the task

In this order:

1. **The id is given**: in the prompt copied from the explorer ("task CSM-T6.19 of the RPT
   referential", « tâche CSM-T6.19 du référentiel RPT »), in a ticket or in a message.
2. **A skill used in the session serves a task**: the `skills` list of the index gives the tasks
   that cite it.
3. **Otherwise, search the index** for the tasks of the person's team whose name, role or type
   match the work done. Propose one to three tasks and ask which one with the question tool; the
   last answer is "None: it is a new task".

The index is the file `index-taches.json` in the referential folder:

| Where you work | Where to read the index and the entries |
|---|---|
| Claude Code, in the organization's repository (`referential.repository`) | `referential.repository_path` |
| claude.ai, with the Google Drive connector | The Drive folder `referential.drive_folder`; search for the file by its name |
| claude.ai, without the Drive connector | Ask for the task id: the explorer shows it (`referential.explorer`) |

In the index, `tasks` gives for each task `[name, role, type, status]` (`columns`), `roles` the
file of each role, `aliases` the current id of an old id.

## Step 2 — Read the entry, then what is already pending

Open the role file (`roles.<role>.file` in the index) and read the task's block. For a change to
the AI's access to a data source, also read the source in `data-sources.yaml`. Then read, in
`blockers.yaml` (same folder as the index), the blockers whose `tasks` list the task, whatever
their state. Keep the values as written: they become the `before` values.

Observations are merged in batches: between two merges, the entry does not change, and other
sessions may already have proposed what you are about to see. Read them before comparing. An
observation covers a single task, and its name ends with the task in lower case, dots turned into
hyphens (`CSM-T6.19` → `…-csm-t6-19.yaml`):

| Where you work | How to read what is pending for the task |
|---|---|
| Claude Code, in the organization's repository | `python3 <referential.tools_path>build_rpt.py --observations --validate-only --task <id>` (without `--validate-only`, the script also rewrites the referential's views and today's survey, which would end up in the session's PR); with the Google Drive connector, also the intake folder (next row) |
| claude.ai, with the Google Drive connector | List the files of the intake folder (query `parentId = '<intake.drive_folder_id>'`) and those of the referential's `observations` folder, next to `index-taches.json`; keep those whose name ends with `-<task>.yaml` and read them. Compare the end of the names yourself: Drive's title search only matches the start of words |
| claude.ai, without the Drive connector | Nothing to read: the merge will group duplicates |

A change on a known blocker is in a file of its own, whose name ends with the blocker's id
(`BLK-12` → `…-blk-12.yaml`): for each blocker of the task, read those too
(`--observations --validate-only --task BLK-12` in the repository). A new blocker is in the file of the first task
it holds back, so it shows up with the task's own changes.

In these files, ignore changes that have a `result`: they are already processed. The others are
**pending**: count their values as already known.

## Step 3 — Compare the session with the entry and with what is pending

For each field of the table in `references/format-observation.md`, ask yourself whether the
session showed it differently from the entry. The most frequent cases:

- the duration of the work (`measure`), when the entry has none;
- a skill, an agent or a software used (`tools`), a data source read (`data`), and the AI's access
  to that source (the connector worked, or was missing);
- the link to the method followed or written (`method`);
- where the deliverable was stored (`output_files`) and the template it started from
  (`templates`): the skill `ts-general-rpt-file` passes you what it recorded;
- an OKR key result that the deliverable moves directly (`okrs`), when the entry names none.

**Blockers.** Then ask yourself whether the session hit a problem that keeps the task from
progressing, or saw a known blocker move. Two shapes (reference, "Blockers"):

- **A new blocker** (`blocker: new`): the session hit a problem that no blocker of the task
  describes: an access refused, data missing or out of reach, a decision awaited, a tool broken
  or missing, a connector absent, a licence, a provider that does not answer. `after` gives its
  text (the problem in one sentence, in the organization's language), its type, the tasks it
  holds back, and, when known, the role that can lift it (`owner`). A problem that a blocker of
  the task already describes is not a new blocker: if it now holds back another task too,
  propose its `tasks` with that task added.
- **A known blocker that moves** (`blocker: BLK-12`, one field per change): `state` to
  `in_progress` (someone works on it), `resolved` (it was lifted: also propose `resolution`, what
  lifted it: "connector enabled", "access granted by the admin", "decision taken at the
  committee") or `dropped` (it no longer matters: `resolution` says why); `open` again if a
  resolved blocker is back. Also `text`, `type`, `tasks` or `owner` when the session shows them
  differently.

The skill never deletes a blocker. A blocker that no longer applies is `resolved` or `dropped`;
the register keeps it, with its dates, so that one can see what was lifted and how long it took.

Only the work problem goes into a blocker: no content of a message, of an e-mail or of a
document, no client name, no name of the person who refused or did not answer. "No access to the
CRM exports", not what was said or by whom. A problem the person mentions without the session
seeing it is `declared`; a problem you only suppose is not written: ask the person, and write it
as `declared` if they confirm it.

The `blocker` and `blocker_type` fields of a task are no longer proposed: in the referential, they
are computed from the register.

**Agents.** When the session created or changed a scheduled task, a routine or a managed agent,
look it up in `agents.yaml` (same folder as the index). An agent can get better without any
task's status changing: a new step in its skill, a new schedule, one more task, a stage reached.
Propose it on the agent (reference, "Agents"): `agent: new` with its entry when it is not in the
register, otherwise `agent: <id>` with one field per change (`stage`, `schedule`, `tasks`,
`skills`, `notify`, `state`…), in a file named after the agent. The tasks it does change in their
own files (`status`, `by`, `tools`).

Do not propose again what is already pending:

- same field, same value already pending, whoever the person: write nothing;
- a measure (`measure`): only one pending per person and per task. If this person already has
  one, do not add one; another person adds theirs (the merge takes the median);
- a new task already proposed for the same role under a similar name: write nothing;
- a value different from the pending one (another location, another tool): propose it, with the
  entry's value as `before`; the merge will choose.

If, once what is already pending is removed, the session brings nothing: say in one sentence
that the entry and the pending observations already say what the session showed, and stop.

Rules:

- One change per field. `before` copies the entry, `after` gives the complete value.
- Only what the session showed (`observed`) or what the person said (`declared`). Nothing
  inferred without evidence.
- The status changes only according to "The status" in the reference: one execution with Claude
  does not move a task to C or S unless the person says they will do it that way from now on. Ask
  them if it is the only new fact.
- Confidentiality: no client name (in a pattern, `[Client]`), no content of the deliverable, no
  personal data other than a person's name in `by`.

## Step 4 — Show the diff and ask for approval

Show a table: task (or blocker), field, before, after, origin (seen or said), evidence. A new
blocker shows on one row: "new blocker", its text, type and tasks. Under the table, say
in one line what is already pending and that you do not propose again. Then say, in the
person's language:

> "Here is everything that will be sent, and nothing else. The observation will go to
> <intake.merged_by>, who will merge it into the referential after validation."

and ask with the question tool "Shall I send it as is?", with three answers: "Send as is",
"Change something", "Send nothing". Send only after an approval given **after** this table; an
older approval does not count. On "Change something", correct, show the table again and ask
again.

## Step 5 — Write the file and check it

Write the file in the `rpt-observation/v1` format (reference and
`assets/2026-10-06-alex-csm-t6-19.yaml`, `assets/2026-10-13-alex-blk-12.yaml`). **One file
per target**: the changes to one task, the new tasks of one role, the AI's access to one data
source, or the changes to one known blocker. A new blocker goes into the file of the first task
of its `tasks` (with that task's other changes, if any). Name:
`YYYY-MM-DD-<first name>-<target>.yaml`, the target in lower case with hyphens (`csm-t6-19`,
`csm-r6`, `data-pipe-et-prospects`, `blk-12`): the next session finds what is pending by this
name. Several tasks or blockers in the same session: one file per target. Check each file:

- in the repository: `python3 <referential.tools_path>build_rpt.py --observation <file>`; if the
  script reports the observation as stale, `before` is no longer the entry's value: read the
  entry again;
- in claude.ai: `python3 scripts/build_rpt.py --observation <file>` (form only).

The script prints its messages in the organization's language. Fix each error before sending.

## Step 6 — Send

**In Claude Code** (organization's repository): write the file in
`intake.observations_repository_path`. Remote session: commit it on the session's branch, in the
PR of the work done (`docs(no-ref): observation RPT <task>` if it is a separate commit). Local
session: add it to the git index (`git add`) and let the developer commit. Never modify the role
file: the merge does that.

**In claude.ai**: first give the file to download, then try in this order and stop at the first
one that works:

1. **Google Drive.** With the connector's file creation tool, create the file in the intake
   folder: parent folder `intake.drive_folder_id`, title = the file name, content = the YAML
   text, type `text/plain`, conversion to Google Docs disabled. Check that the created file is
   indeed `text/plain`; a Google Doc cannot be merged: then move on to e-mail and report the
   Google Doc to delete.
2. **E-mail** to the intake address: subject
   `Observation RPT — <task> — <first name> — <YYYY-MM-DD>`, plain-text body with one sentence
   ("RPT observation produced with the skill ts-general-rpt-observe.", in the person's language)
   then the complete YAML. If the tool only makes a draft, create it and ask the person to send
   it.
3. **The folder of the configuration**, if the intake folder does not exist and there is no
   intake address: create the file there as in point 1 (the folder of the link in the
   organization's instructions).
4. **By hand**: the person drops the file in the intake folder
   (`https://drive.google.com/drive/folders/` followed by `intake.drive_folder_id`), or gives it
   to <intake.merged_by>.

Tell the person what was done (file path, Drive link, e-mail or upload left to do).

## What happens next

`python3 <referential.tools_path>build_rpt.py --observations --validate-only` lists the pending changes, with
identical proposals together. `intake.merged_by` merges them in batches with
`ts-general-rpt-merge` (section on merging observations): plan, GO, then
`build_rpt.py --apply-observation` writes the accepted changes into the entries, marks each
change `result: merged` or `rejected`, and closes the duplicates of an applied change. A new
blocker enters `blockers.yaml` with the next free id, `opened` = the date of the observation; a
blocker set to `resolved` or `dropped` takes the date of the observation as `resolved`. The
changes table of the reports then shows what changed.

## Skill files

| File | When to read it |
|---|---|
| `references/format-observation.md` | At steps 3 and 5: the fields, the values, the status, what the file never contains. |
| `assets/2026-10-06-alex-csm-t6-19.yaml` | At step 5: a valid observation on a task, with a new blocker, named according to the rule, whose structure to copy. |
| `assets/2026-10-13-alex-blk-12.yaml` | At step 5: a valid observation on a known blocker (resolved, with its resolution). |
| `scripts/build_rpt.py` | In claude.ai, at step 5: `--observation <file>`. In the repository, it is `<referential.tools_path>build_rpt.py`. |
