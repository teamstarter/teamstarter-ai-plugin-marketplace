# Format rpt-observation/v1

An observation is a YAML file that proposes changes to tasks of the organization's RPT
referential, to the AI's access to a data source, or to the blocker register (`blockers.yaml`). It writes nothing in the referential: `intake.merged_by` (from
`references/rpt-config.yaml`) merges it in batches, after a GO, with the skill
`ts-general-rpt-merge`. Rules of the referential: `README_operations.md` §4.1, in the referential
folder (`referential.repository_path` in the repository, `referential.drive_folder` on Drive).

The keys and enum values below are in English. The free-text values (`evidence`, `frequency`,
`what`, a new task's name) are written in the person's language.

## The file

```yaml
format: rpt-observation/v1
meta:
  date: '2026-10-06'          # the day of the session, YYYY-MM-DD
  observer: Alex              # the person who approved sending (first name, or first and last name)
  surface: claude-ai          # claude-ai, claude-code or other
  source: PR teamstarter/teamstarter#8740   # optional: the PR, the ticket or the conversation
changes:
  - task: CSM-T6.19           # the task id (an old id works too)
    field: measure            # the field that changes (list below)
    before: null              # the entry's current value, copied as is (null if empty)
    after: {minutes: 45}      # the complete value after the change
    basis: observed           # observed: seen in the session; declared: said by the person
    evidence: The deck was produced in 45 minutes in the session.
```

**One file per target**: the changes to a single task, or the new tasks of a single role, or the
AI's access to a single data source, or the changes to a single known blocker. A new blocker goes
into the file of the first task of its `tasks`. Several tasks in the same session: one file per
task.

**File name**: `YYYY-MM-DD-<first name>-<target>.yaml`, in lower case, the target written with
hyphens in place of dots and colons:

| Target | Name |
|---|---|
| The task `CSM-T6.19` | `2026-10-06-alex-csm-t6-19.yaml` |
| The new tasks of the role `CSM-R6` | `2026-10-06-alex-csm-r6.yaml` |
| The AI's access to `data:pipe-et-prospects` | `2026-10-06-alex-data-pipe-et-prospects.yaml` |
| A new blocker whose `tasks` start with `CSM-T6.19` | `2026-10-06-alex-csm-t6-19.yaml` (with the task's other changes) |
| The known blocker `BLK-12` | `2026-10-13-alex-blk-12.yaml` |

The name is used to find what is pending for a task without opening every file. The script
rejects a file that mixes two targets, or whose name does not end with its target.

## What is already pending

Between two merges, the entry does not change. Before writing, read the task's pending
observations, and those of each blocker that names the task: the files whose name ends with the
target, in the intake folder
(`intake.drive_folder`) and in the referential's `observations/` folder (in the repository:
`build_rpt.py --observations --task <id>`, which also takes a blocker id: `--task BLK-12`). A change that has a `result` is already processed;
the others are pending.

- Same field, same value already pending: do not write it.
- A measure: only one pending per person and per task; the merge takes the median of the
  measures of several people.
- A new task already proposed for the same role under a similar name: do not write it.
- A new blocker already pending or in the register for the same problem: do not write it; if it
  holds back one more task, propose that blocker's `tasks` with the task added.
- A value different from the pending one: write it, with the entry's value as `before`; the
  merge will choose.

## The fields an observation can change

| `field` | `after` | What proves it in the session |
|---|---|---|
| `measure` | `{minutes: 45}`, `{runs: 8}` or both | The duration of the work on the task, seen or said; the number of times per month, said |
| `frequency` | a text: `every Monday`, `about 8 per month` | What the person says about the rhythm |
| `tools` | the complete list of tool ids (`skill:…`, `saas:…`) | A skill, an agent or a software used to do the task |
| `data` | the complete list of sources (`data:…`) | A data source read or written for the task |
| `method` | a URL, or a tool id (`skill:…`) | The written method followed, or written during the session |
| `okrs` | the complete list of key results served (`O1.3.KR1`, at most two) | The session's deliverable directly moves the measure of a KR of `okrs.yaml` (README_operations.md §1.13); a link that is only indirect is not written |
| `output_files` | the complete list of locations (below) | Where the deliverable was stored |
| `templates` | the complete list of templates (below) | The template the deliverable started from |
| `status`, `target` | `A`, `S`, `M` or `J` | See "The status" |
| `input`, `output` | a text | The actual input or deliverable differs from the entry |
| `by` | the complete list of people or agents | Another person does the task |
| `stakes` | `{level: 1, 2 or 3, text: …}` | What the person says about the cost of a delay or an error |
| `job` | `{when: …, so_that: …}` | The person corrects or confirms when the task starts and what it is for (a confirmation changes `inferred` into `declared`) |

For a list, `before` is the current list and `after` the whole list after the change (to add a
skill: copy the entry's tools and add the skill).

What keeps the task from progressing is not written on the task (`blocker`, `blocker_type`): in
the referential, these two fields are computed from the blocker register. Propose a blocker
instead (section "Blockers").

**Where the deliverable goes** (`output_files`), one entry per location:

```yaml
after:
  - kind: file                 # a fixed file, updated at each execution
    url: https://docs.google.com/spreadsheets/d/…
    tool: saas:google-sheets
    what: the account tracking sheet
  - kind: folder               # the folder where each execution's file goes
    url: https://drive.google.com/drive/folders/…
    pattern: Clients/[Client]/2. Support/meeting-[YYYY-MM-DD].pptx
    tool: saas:google-drive
```

The pattern (`pattern`) starts from the folder of `url`; what changes from one execution to the
next is written in square brackets: `[Client]`, `[YYYY-MM-DD]`, `[First name]` (or the same
placeholders in the organization's language: `[AAAA-MM-JJ]`, `[Prénom]`). Never a real client
name.

**The templates** (`templates`): `- {url: https://…, what: meeting deck template}`; `url` can
also be a tool id (`skill:…`) when the template lives in a skill.

**The AI's access to a data source** is changed on the data source, not on the task, in a
separate file (`…-data-pipe-et-prospects.yaml`):

```yaml
  - data: data:pipe-et-prospects
    tool: saas:hubspot
    field: connector
    before: none
    after: native               # native, mcp, api, export or none
    basis: observed
    evidence: The session read the pipeline with the HubSpot connector.
```

**A task missing from the referential**, in a file named after its role (`…-csm-r6.yaml`):

```yaml
  - task: new
    field: task
    after: {name: Send the meeting summary to the sponsor, role: CSM-R6, input: …, output: …, status: M}
    basis: declared
    evidence: The person does it after each meeting; the task is not in the referential.
```

## Blockers

The register `blockers.yaml`, in the referential folder (README_operations.md §1.14), lists the
problems that keep tasks from progressing: one entry per problem (`BLK-<n>`), with its `text`,
its `type`, its `state`, the `tasks` it holds back, the date it was first seen (`opened`) and,
once closed, the date (`resolved`) and what lifted it or why it was dropped (`resolution`). An
observation proposes two kinds of change on it.

**A new blocker**: the session hit a problem that no blocker of the task describes.

```yaml
  - blocker: new
    field: blocker
    after:
      text: Pas d'accès en lecture aux statistiques d'usage de l'instance du client
      type: access             # see the list below
      tasks: [CSM-T6.19]       # the tasks it holds back; the first one names the file
      owner: CSM-R6            # optional: the role that can lift it
    basis: observed
    evidence: The usage export was refused for lack of rights; the figures were taken from the previous month.
```

`after` takes `text`, `type` and `tasks` (required), and optionally `state` (`open` by default),
`owner`, `source`, `evidence` and `notes`. At the merge, `build_rpt.py --apply-observation` gives
it the next free id, `opened` = `meta.date`, and `source: observation`. If the same problem is
already open on the same tasks in the register, the change is closed without a duplicate.

`type`: `connector` (no connector to the tool), `method` (method not written), `tool` (tool to
build or broken), `decision` (decision awaited), `data` (data missing or unusable), `licence`,
`access` (access refused or not granted), `security`, `budget`, `organization` (who does what is
not settled), `provider` (an outside provider), `other`.

**A known blocker that moves**: one change per field, `blocker` gives its id, the file is named
after it.

```yaml
  - blocker: BLK-12
    field: state
    before: open
    after: resolved          # open, in_progress, resolved or dropped
    basis: observed
    evidence: The monthly report was produced by the scheduled skill, with no preparation by hand.
  - blocker: BLK-12
    field: resolution
    before: null
    after: skill planifié écrit et lancé chaque lundi
    basis: declared
    evidence: The person says the scheduled skill has run every Monday since this week.
```

The fields a change can touch: `state`, `resolution`, `text`, `type`, `tasks`, `owner`.

| `state` after | When | Also propose |
|---|---|---|
| `in_progress` | Someone works on lifting it (access requested, ticket opened, decision on the agenda) | — |
| `resolved` | It no longer holds the task back | `resolution`: what lifted it (connector enabled, access granted, decision taken, skill written) |
| `dropped` | It no longer matters (the task changed, the need went away) | `resolution`: why |
| `open` | A resolved or dropped blocker is back | — |

At the merge, `resolved` or `dropped` writes the date of the observation as the blocker's
`resolved`; back to `open` or `in_progress` removes it.

**Never delete.** No change removes a blocker from the register, or a task from its `tasks`
because it was lifted: a blocker that no longer applies is `resolved` or `dropped`, and the
register keeps it with its dates.

**Only the work problem.** `text` and `evidence` say what blocks, not what was said: no content
of a message, an e-mail or a document, no client name, no name of the person who refused or did
not answer. « Pas d'accès aux exports du CRM » [No access to the CRM exports], not who said it.
A problem the person reports without the session seeing it is `declared`; a problem only
supposed is not written unless the person confirms it (then `declared`).

## The status

- **M → S**: the task was done with Claude, and the person says they will do it that way from
  now on. A single assisted execution is not enough without this answer.
- **S → A**: a skill, an agent or a tool does it end to end without a person redoing it; the
  tool is in `tools`.
- A judgment task (J) never becomes A.

## What the file never contains

- A name of a client, prospect, candidate or partner: in a pattern, `[Client]`.
- The content of the deliverable, of an e-mail, of a document, an amount.
- Personal data, except a person's name in `by` and in `meta.observer`.
- A fact inferred without evidence: an observation only has `observed` or `declared`.
- For a blocker: the content of the message that reported it, the name of who refused an access
  or did not answer.

`evidence` fits in one sentence of at most 300 characters: the fact, not the content.

## Check

- In the repository: `python3 <referential.tools_path>build_rpt.py --observation <file>`. It
  also checks that the task exists and that `before` is indeed the current value; otherwise the
  script reports the observation as stale: read the entry again and fix `before`.
- With the skill installed in claude.ai: `python3 scripts/build_rpt.py --observation <file>`
  checks the form only.

The script prints its messages in the organization's language. Frequent errors and their fix:

| The script reports | Fix |
|---|---|
| an unknown field | An unquoted comma inside `{…}`: put the text in quotes |
| a `field` value outside the expected list | The field cannot be observed: use a field from the table above |
| an `evidence` that is too long | Keep the fact, remove the content |
| more than one target in the file | Two tasks in the same file, or a change on a known blocker next to a task's changes: one file per target |
| a new blocker written another way | `blocker: new`, `field: blocker`, and `after` with at least `text`, `type`, `tasks` |
| a blocker that is not in the register | Read `blockers.yaml` again: the id is wrong, or the blocker is new (`blocker: new`) |
| a `field` outside the list, on a blocker | `opened` and `resolved` are not proposed: change `state`, the merge writes the dates |
| an unexpected file name | Rename the file as the message says |
