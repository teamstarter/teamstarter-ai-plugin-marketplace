---
name: ts-general-rpt-file
description: "Store the deliverable of a task of the organization's RPT referential at the end of the task, where its entry says: update the fixed file the task maintains, or put the new file in the right folder (Google Drive, OneDrive, SharePoint, Notion, repository) under the name given by the entry's pattern, and start from the task's template when it cites one. Proposes the location and the name, and moves, renames or creates nothing without the person's approval. When the entry does not say where the deliverable goes, proposes the folder of the organization's data tree that the referential proposes for the task, else asks once, then passes the answer to the skill ts-general-rpt-observe to complete the entry and the data tree. Use when the deliverable of a work task done with Claude is ready, when the organization's global context asks for it, or when someone asks 'where do I store this?', 'file this in the right place', « où je range ça ? » or « range ce fichier au bon endroit »."
metadata:
  version: "1.7 (2026-10-28)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-rpt-file; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Store the deliverable of a task

Speak and write to the person in their language; this file is in English.

Each task of the organization's RPT referential can say where its deliverable goes
(`output_files`), where the files it reads are (`input_files`, same form) and which template it
starts from (`templates`):

- **a fixed file** (`kind: file`), which each execution updates: the account tracking sheet, the
  Notion page of the roadmap;
- **a folder** (`kind: folder`), where each execution puts a new file, named according to a
  pattern: `Clients/[Client]/2. Support/meeting-[YYYY-MM-DD].pptx`;
- **a template** (`templates`): the file to start from;
- **no file** (`kind: none`, alone): a person said the task keeps no file on this side;
- **not disclosed** (`kind: private`, alone): the task keeps files on this side, but where is
  confidential (a board reporting, payroll): the referential describes the task, not the place.

This skill stores the deliverable at that location at the end of the task. When the entry says
nothing, it first proposes the folder of the organization's data tree that the referential
proposes for the task (`places` of the index), else asks; the answer completes the entry through
an observation, and the folder of the data tree gets the task: the location is asked only once
per task.

## When

- The deliverable of a work task done with Claude is ready, and the organization's global context
  asks for it (`global_context` of the organization's configuration, below) or the task's prompt says so.
- Someone asks where to store a file, or to store it in the right place.

Not for a conversation that is not a work task, nor for a deliverable that is not a file: a sent
message or a created ticket is already in its place. Not either in a session where nobody can
answer (autonomous worker, routine): storing requires a person's approval.

## Step 1 — Find the task

Like the skill `ts-general-rpt-observe`: the given id (the prompt copied from the explorer
contains it), otherwise the skill used in the session (`skills` list of the index), otherwise the
tasks of the person's team in the index, and the question "Which one is it?". The index is the
file `index-taches.json` of the referential; the organization's configuration says where it is.
The skill carries no data of any organization. The organization's
instructions (the global context Claude receives in every conversation) give the address of its
configuration, on a line such as `Config RPT (rpt-config.yaml) : <link>`: the Drive link of
the file, or of the folder at whose root it is (or its link in a repository).
To read it: a `drive.google.com` link, with the Google Drive connector (the file whose id is
in the link; for a folder link, the file named `rpt-config.yaml` in that folder); a `github.com`
link, with the GitHub connector, or in Claude Code the file of a clone of that repository;
otherwise, fetch the link (a public file only). Without an address in the instructions, search
Drive for a file named `rpt-config.yaml` and have the person confirm it is their
organization's. If none works, ask the person to add the file to the conversation; it is in the
folder the organization's instructions link to. Never guess a value. The configuration gives:

- in the organization's repository: in `referential.repository_path`;
- in claude.ai, with the Google Drive connector: in the folder `referential.drive_folder`;
- without either: ask for the id; the explorer shows it (`referential.explorer`).

Then read the task's entry in its role file (`roles.<role>.file` of the index), and, in the
index, its line of `places` when it has one: `{"out": [status, [container ids]], "in": …}`, where
the status says what the data tree knows when the entry says nothing (`tree`: the data map
already names the task in these folders; `proposed`: the folder of the tree that fits it best;
`to_choose`: folders that hold this data, none of which clearly fits; `missing`: the tree has no folder for this data).
Each id is described in `containers` of the index: `[name, tool, path, link]`.

**Without a referential** (no `index-taches.json` yet: the organization has not merged its first
maps, or has no OS): there is no entry. Go to step 3 as if the entry said nothing, without looking
for pending observations, and skip step 5; when the deliverable is stored, propose the mapping
(`ts-general-check-process-cartography`) once, so that the task gets an entry.

## Step 2 — At the start, the template

When you come in before the deliverable exists and the entry cites a template (`templates`):
propose to start from this template (a copy, never the original). If the deliverable is already
done without it, say so at step 4 without redoing it.

When the entry says where the files the task reads are (`input_files`), or the index places them
(`places`, side `in`): look for them there first, and name the folder before reading it. When
`input_files` is `kind: private`, do not look for them: ask the person for the files.

## Step 3 — Propose the location and the name

For each entry of `output_files`:

- **Fixed file**: "This deliverable updates <link> (<what>). Shall I put the result in this
  file?" If the work was already done in this file, only check that it is saved.
- **Folder**: fill in the pattern. `[YYYY-MM-DD]` (or `[AAAA-MM-JJ]`) is today's date,
  `[Client]` the client of the session, `[First name]` (or `[Prénom]`) the person; ask for what
  the session does not say. Propose the full path and the file name, with the folder's link.

Ask with the question tool "Shall I store it there?", with the answers "Yes", "Somewhere else"
(the person says where) and "Not now".

- **Not disclosed** (`kind: private`): propose no place, ask for none and read no folder to find
  one. Say in one sentence that the referential does not give this place and that the person
  stores the deliverable; skip steps 4 and 5 for this side.

**The entry says nothing** (`output_files` missing): first check whether a pending observation
already says it (step 2 of the skill `ts-general-rpt-observe`: the files whose name ends with the
task, in the intake folder `intake.drive_folder` and in `observations/`). If so, propose that
location as above, saying it comes from an observation not yet merged. Otherwise, read the task's
`places` (step 1), side `out`:

- `tree` or `proposed`: "The data tree of <organization> has <folder> (<path>, <link>) for this
  data. Shall I store it there?", with the answers "Yes", "Somewhere else" and "Not now". With
  several folders, the first one, and the others as answers.
- `to_choose`: "Which of these folders?", with the folders and "Somewhere else" as answers.
- `missing`, or no line: ask "Where does this deliverable usually go?", with as answers the
  plausible locations seen in the session and "Somewhere else". The tree has no folder for this
  data: say it in one sentence ("this folder is not described in the data tree yet").

Each of these questions also has the answer "Not disclosed": the place is confidential. Then
store nothing; step 5 writes `kind: private`, never the place.

It is the only question in this case.

## Step 4 — Store, after the approval

With a tool that can write at that location, and only after the "Yes":

- **Google Drive**: create or copy the file in the folder (parent folder id taken from the link),
  under the proposed name;
- **OneDrive, SharePoint** (Microsoft 365 connector): upload or move the file into the folder;
- **Claude Code**: write the file at the repository path given by the pattern.

Without a write tool, give the path, the name and the folder's link: the person stores the file
themselves. In every case:

- never replace an existing file without saying so and without approval;
- create a missing subfolder (the client's folder, for example) only with an approval given for
  that subfolder;
- delete nothing.

Then say what was done: the link of the stored file, or what is left for the person to do.

## Step 5 — Complete the entry

What the entry did not say becomes an observation, with the skill `ts-general-rpt-observe`:

- the location given at step 3 when `output_files` was missing, or the actual location when it
  differs from the entry; with `container: <DC-n>` when the location is a folder of the data
  tree (the one proposed by `places`, or a folder of `containers` with the same link): the merge
  then also writes the task into that folder of the data map;
- where the files it read were (`input_files`), when the session read them from a folder the
  entry does not give;
- `kind: none` when the person says the task keeps no file on this side;
- `kind: private` when the person answers "Not disclosed": neither link, pattern nor
  container, and nothing of the place in the evidence;
- the template used when the entry cites none.

A location that is in no container of the index is written with its link only: the referential
lists it among the folders to describe in the data map (page « Files to place » of the explorer),
and the skill `ts-general-data-crawl` describes it at the next crawl.

Unless the same value is already pending in an observation: the person stored the file where the
pending observation said, there is nothing new to write.

In the observation, the pattern keeps the brackets: `Clients/[Client]/…`, never the client's
name. The observation skill shows the diff and asks for approval; do not send it yourself.

## Confidentiality

A client's name, the content of the deliverable and personal data stay in the session: they are
used to store the file, never in the observation. Read only the folders needed to check the
location, and name each folder before reading it.
