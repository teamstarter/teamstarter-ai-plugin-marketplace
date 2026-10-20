---
name: ts-general-check-process-cartography
description: "Map the roles, processes and tasks (RPT) of a person or of a team of their organization, with the automation level of each task (automated, skilled, conversational, manual, human judgment), the data it uses and what blocks it, have the person review a preview of what will be sent, then drop the map (one rpt/v1 file per job held) in the organization's intake folder, or send it to its intake address (read from the organization's rpt-config.yaml). Use whenever someone wants to map their work or their team's, list their roles, processes or recurring tasks, know what they could automate or hand over to AI or which connectors to activate, answer the product team's request to map their RPT, update an RPT map, or turn a procedure or a job description into an RPT map, even without saying role, process or mapping. Triggers: 'map my roles', 'process mapping', 'which tasks could I automate', « fais la carte de mes rôles », « cartographie mon équipe », « qu'est-ce que je pourrais automatiser »."
metadata:
  version: "2.17 (2026-10-20)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-check-process-cartography; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Map your roles, processes and tasks

Speak and write to the person in their language; this file is in English. The content of the map
(names, missions, inputs, outputs, notes, gaps) is written in the person's language too; the keys
and the enum values stay as in the format (`references/format-rpt-v1.md`).

The organization keeps a shared referential of the **roles**, **processes** and **tasks** (RPT)
of each team. For each task, it says whether it is already automated, run by the AI with a skill, helped by a chat, done by
hand, or a human decision, and which data it uses. It is used to choose what to hand over next to
AI agents, and the connectors to activate so that they have this data.

This skill produces the map of a person or of a team, and one map per job when the person holds
several (section "One map per hat"). It reads what you can read about their work (with their
approval), interviews them, has them validate the map, writes a file in the rpt/v1 format,
checks it with a script, shows them in a preview everything that will be sent, then, after their
approval, drops it in the organization's intake folder. The person or team that maintains the
referential then merges it; the person has nothing else to do.

**The organization's configuration.** The skill carries no data of any organization. The organization's
instructions (the global context Claude receives in every conversation) give the address of its
configuration, on a line such as `Config RPT (rpt-config.yaml) : <link>`: the Drive link of
the file, or of the folder at whose root it is (or its link in a repository). This file holds everything
specific to the organization; read it before your first message, with the catalogues it names
(section "Reading the configuration"). In this text:

- "the organization" is `organization.name`; never ask for the company's name;
- "the team codes" are those of `teams` (`code`, `name`, `scope`);
- "the intake folder" is `intake.drive_folder`, with Drive id `intake.drive_folder_id`; "the
  intake address" is `intake.email`; `intake.visibility` says who can read what is dropped
  there, `intake.merged_by` who merges it;
- "the folder of merged maps" is `referential.archive_drive_folder` (in a repository,
  `referential.archive_repository_path`);
- `privacy` lists what is never sent, in addition to the rules of the section "Privacy and
  personal data".

If the person adds to the conversation their organization's `rpt-config.yaml`, it replaces the one
at the address. A missing value is not a reason to stop: the maps go to the first destination
that exists (step 7).

**An organization without an OS.** Mapping needs nothing but `rpt-config.yaml`: neither an OS,
nor a referential, nor catalogues, nor maps already merged (Vincent, 2026-10-18). At the first
run, the folder of the configuration often holds this file alone, and the folders it names (the
referential, the intake folder, the folder of merged maps) do not exist yet. Then:

- the catalogues are the generic ones of `references/` (departments, common data types), and the
  map declares every tool and data source it cites (section "Reading the configuration");
- it is a first map: there is no starting map to look for (section "Updating a map already
  sent"), nor a blocker register;
- the access to the OS is not checked and the person is not told what it costs (section "Access
  to the OS and recurring agents");
- the maps go to the first destination that exists (step 7): the intake folder, the intake
  address, the folder of the configuration, or the person drops them.

Never present the OS as a prerequisite, and never ask the person to create one.

### Reading the configuration

1. **The configuration.** Take its address from the organization's instructions, then read
   `rpt-config.yaml` by the first means that works:
   - a `drive.google.com` link, with the Google Drive connector: the file whose id is in the
     link; for a folder link, the file named `rpt-config.yaml` in that folder;
   - a `github.com` link, with the GitHub connector: owner, repository, branch and path taken
     from the link; in Claude Code, in a clone of that repository, the file at its path;
   - otherwise, fetch the link (a public file only).

   Without an address in the instructions, search Drive for a file named `rpt-config.yaml` and
   have the person confirm it is their organization's. If none works, ask the person to add the
   file to the conversation; it is in the folder the organization's instructions link to. Never
   guess a value. Save it
   as `rpt-config.yaml` in your working folder.
2. **The catalogues.** `catalogues` of the configuration names the catalogue files (departments,
   tools, data sources, AI policy, OKR), relative to the referential: `referential.repository_path`
   in `referential.repository`, or the Drive folder `referential.drive_folder`. Read each one by
   the same means and save it under the same name in the folder `catalogues/` of your working
   folder. A catalogue you cannot read is missing, which is normal at the first run: the generic
   ones of `references/` take its place (`references/departments.yaml`,
   `references/data-sources.yaml`: common data types), and the map declares every tool and data
   source it cites; without `okrs.yaml`, tasks link to no key result; without `ai-policy.yaml`,
   the rules of the section "Privacy and personal data" apply. Say nothing to the person about a
   missing catalogue.
3. Pass both to the scripts: `--config rpt-config.yaml --catalogues catalogues`.

In this text, `catalogues/tools.yaml` (and the other catalogues) means the organization's
catalogue saved in that folder.

The person does not need to know the model. Talk to them about their weeks, the requests they
receive and their tools; the model's vocabulary is for the file. Work in their language; the
field names of the file stay those of the format. Count 30 to 40 minutes in full mode, 15 in
quick mode.

## The course

1. Frame: a single series of questions (section "Asking a question").
2. Read the authorized sources (full mode only), blocker signals included.
3. Write a first draft, with the blockers of its tasks.
4. Have it validated: three rounds at most.
5. Write the map, one per hat, and check it with the script.
6. Give the summary, and show in an artifact everything that will be sent.
7. Have this preview reviewed, then send the maps, only after an explicit approval.

Two variants:

- The person has **already sent a map**: it is an update (section "Updating a map already
  sent"); you start from their map and ask only for what is missing or has changed.
- They bring a **document** (procedure, job description, export of a ticketing tool, Notion
  page): it is the conversion mode. The document replaces step 2; statuses are deduced from the
  tools it cites; what the document does not say becomes a question.

## Asking a question

**Every question that waits for an answer from the person goes through the question tool**: the
one that shows the question apart, with answers to choose from (`AskUserQuestion` in Claude Code
and Cowork; in claude.ai, the answer input tool, `ask_user_input`). A question written at the end
of a message ("Is that OK for you?") reads as a polite formula: the person does not see that an
answer is expected, the conversation stops there, and the map is never sent.

- Your message first shows what the question is about (the first draft, a table, the summary,
  the sending preview); the tool asks the question last, and nothing follows. Do not repeat the
  question in the text of the message.
- The answers offered are the most likely ones, your estimate first. An open question (a typical
  week, the members of a team, a correction) also goes through the tool: it offers what you
  already know, if anything, and the person answers in free text. Do not invent answers to fill
  the list.
- Several questions at once: in the same call, as many as the tool accepts, the most important
  first; the others in a second call, after the answers.
- Without a question tool in your list of tools: end the message with the question, alone on its
  last line, in bold, and nothing after.
- The list of questions left open in the summary (step 6) is not a question asked: it is
  information for the person, which stays in the summary.

## One map per hat

A map covers one hat: a job the person holds, which matches a team of the referential. Someone
who does HR, finance and CSM at the same time has three hats, hence three maps, each with its
code (`RH-R1`, `FIN-R1`, `CSM-R1`). Each map then joins its team's map in the referential; a
single code would mix three teams. The maps are made in the same conversation: one framing, one
reading of the sources, one validation where each role is filed under its hat, one preview and
one approval for sending.

Take the code from the team codes (`teams` of the configuration, in capitals in the
ids: `csm` gives `CSM-R1`); `scope` says which hat each team covers. A code outside the list
creates one more team, which will have to be reconciled at the merge.

If none fits, propose a new code (capitals and digits, no hyphen) and tell the person that it
creates a team.

Each map is complete in itself: its processes chain only its own tasks, and a task is only in
the map of the hat that holds it. To send a case to a role of another of their maps, write in
`routing.to` the name of that role as text, with its hat in brackets ("Recruit for an open
position (HR map)"), and the status `-`.

## Updating a map already sent

A person who has already sent a map does not redo the whole interview: you start from that map,
you do not ask again what it already says, and you ask only for what is missing (often the
relevance of the tasks, added to the model after the first maps) and what has changed since its
date.

**Finding the map.** Question 2 of step 1 asks the person whether they have already sent a map.
If so, they give it to you in one of these ways:

| The person… | What you do |
|---|---|
| kept the file sent | They add it to the conversation. |
| has the organization's OS on their computer: the Drive folder synchronized by Google Drive for desktop, or the repository | The maps already merged are in the folder of merged maps. In Cowork or Claude Code, they point you to this folder and you read only their maps there; in claude.ai, they add their maps to the conversation. |
| cannot find the file, and you have the Google Drive connector | With their approval, search for the file by its name: in the folder of merged maps if it was merged, in the intake folder otherwise. |

Their maps are recognized by their name, `<code>-<first name>-<YYYY-MM-DD>.rpt.yaml`
(`csm-alex-2026-09-24.rpt.yaml`), one per hat; for the same code, take the most recent (the
date, then the suffix `-v2`). Read nothing else in the OS: neither the maps of others nor the
source documents; the blocker register is the one exception (point 4). The role files of the
referential (`OS/Operations/<code>-r<n>-….rpt.yaml`) are not a starting point: they mix the maps
of several people and point to roles of other files. If the person has never sent a map, or
cannot find theirs, it is a first map: normal course.

**Updating.** These points replace steps 2 and 3. Your first message after the framing shows what
the map contains (point 1) and asks the questions of points 2 to 4 with the question tool: it is
the first round of step 4, which has three at most. Steps 5 to 7 follow, with point 6.
No typical week to tell: it would serve to redo the map. The codes are those of the starting
maps; with several hats, one starting map and one updated map per hat.

1. Check the starting map with `validate_rpt.py` (step 5) and show the person what it contains:
   their roles, the number of tasks by status, the tasks without relevance, the questions left
   open (`gaps`).
2. Ask what has changed since its date (`meta.updated`): a new activity, a task or a process
   stopped, a status that changed (a tool, a skill or an automation put in place), a holder; and
   an activity the person already did but that the map does not show. In full mode, read the
   authorized sources over this period to find these changes, not to redo the map.
3. Complete what is missing: the relevance of each task, including the axes an older map does
   not have (`payback`, added on 2026-09-29, and `describability`, which replaces `simplicity`
   on 2026-09-30: remove `simplicity`, its rating does not carry over); rate what you can
   estimate and ask for the rest (section "The model"); the data sources of each task (`data`,
   added on 2026-09-30: step 3, point 6); `by` of an M or J task; the `gaps` left open; and,
   added on 2026-10-02, the handoffs of each process (`handoffs`), the link to the written
   method when you find it (`method`), the sensitivity of the sources the map declares and the
   origin of the facts (`basis`). The facts the starting map marks `inferred` and that matter (a
   status, a data source) are confirmed with the person, in the same questions; a confirmed fact
   becomes `declared`.
4. Review the blockers still open. Take those of the starting map (its `blockers` list, or the
   `blocker` texts of its tasks for an older map) and those of the organization's register:
   `blockers.yaml`, in the referential's folder (`referential.drive_folder` of the
   configuration; in a repository, `referential.repository_path`), only the entries in state
   `open` or `in_progress` whose `tasks` cite an id of the starting map. The person adds the
   register to the conversation or points you to it; with the Google Drive connector and their
   approval, search it by its name in that folder; if it cannot be found, review the starting
   map alone. Ask with the question tool whether each one is still open, in progress, resolved
   (when, and what lifted it) or dropped (when, and why); a table and a single question beyond
   four. Write each in the `blockers` list of the updated map with its new state, keeping its
   text, type, `opened`, `source`, `basis` and `evidence`; for an entry of the register, keep in
   `tasks` only the tasks of this map and write its id in `sources` (`blockers.yaml BLK-12`): the
   merge updates this entry instead of opening a new one. Then look for the blockers that
   appeared since the date of the starting map, as for a first map (section "Blockers").
5. Keep every role, process and task id of the starting map: the merge uses them to find the
   elements already merged. A task whose tool or status alone changes keeps its id, and its
   status changes (M → A); replace it with a new task only if its input or its deliverable
   changes. An element that no longer exists becomes `state: retired` (with `replaced_by` if it
   is replaced); it does not disappear from the file. A new element takes the next number of the
   map (`CSM-T2.5` after `CSM-T2.4`). A role the person no longer holds, a task they no longer do
   but that someone else does: keep the element and write it in `notes` ("no longer holds this
   role since 2026-10", in the person's language).
6. Write the updated map as a new map (step 5, named with today's date). `meta.sources` starts
   with the name of the starting file, keeps the sources of the starting map and adds those of
   the update ("answers of <YYYY-MM-DD>", in the person's language: « réponses du
   <AAAA-MM-JJ> »); `meta.notes` starts with "Update of the map of <YYYY-MM-DD>" (« Mise à jour
   de la carte du <AAAA-MM-JJ> »). Check it by giving the starting map, last on the command
   line:

   ```bash
   python3 <skill folder>/scripts/validate_rpt.py <updated map> [--format] \
     --config rpt-config.yaml --catalogues catalogues --since <starting map>
   ```

   (`--depuis` is accepted in place of `--since`.) The script flags each element of the starting
   map that disappeared (to put back, or to set `retired`) and sums up what changed; reuse this
   summary at step 6.

## Privacy and personal data

The map goes into a Drive folder readable by the whole company, then into a referential read by
all employees and by agents. It describes only the work. These rules apply from beginning to
end, to what you read as well as to what you write:

1. **Out of the map, even if an authorized source mentions it**:
   - what is private or unrelated to work (health, personal life, personal appointments, a skill
     or a conversation unrelated to the job);
   - what is confidential and could harm the company: internal reviews and individual
     evaluations, HR discussions (a specific person, their pay, a conflict, a departure), the
     health of the company (cash, fundraising, difficulties, unpublished internal figures).

   An activity may appear, never its content: "Prepare the annual reviews" yes, what is said in
   them no. An activity you know only through a confidential case (a departure under way, a
   dispute) stays out of the map, `gaps` and questions included: even written in general terms,
   it points to the case for whoever reads the map. Mention it only in the summary, which is not
   sent; the person decides whether it is recurring and must appear.
2. **Systematically filter out personal data**: no address, no sex or gender, no age or date of
   birth, no phone number, no e-mail address, no family situation, no health, no pay (fixed,
   variable, commission target), no absence. The only personal data allowed is the first name
   and the name of a person **where they hold a role, do a task or act as a fallback**
   (`holders`, `by`, `fallback`) and in `meta.authors`. Everywhere else (`notes`, `sources`,
   `gaps`, `supervision`, free texts), write their role, with no word that would say their
   gender: without an article ("to be validated by: CEO", "reviewed by Head of CS") or with a
   phrasing that does not depend on the person ("the management", "the CEO position", "the person
   who holds this role"; in French, without a gendered article). Even in those fields, prefer the
   role when it is enough: as little personal data as possible. A replacement (absence, leave)
   may appear through the new holder or the fallback, never through its cause.
3. **No name of a client, prospect, candidate, partner or other third party**, nor their contact
   details.
4. Before reading a source, name it and wait for the person's approval, source by source.
5. Note **activities**, not contents: "answer quote requests" yes; the text of an e-mail or an
   amount, no.
6. What you deduce without any clue is written as a question (`gaps` or `notes`), never as a
   fact. What you deduce from clues (the tools of a task, its input and its deliverable, the
   description of a skill) is written as a fact marked `inferred` in `basis` (section "The
   model").

The two scripts of the skill flag what looks like personal or confidential data (e-mail, phone,
address, amount, words about health, HR or finances in French or English, a common first name or
the name of a holder written outside the allowed fields). Each alert is fixed before sending; if
it is a false positive (an activity that reveals nothing), tell the person. They do not see
everything: a family name alone, a rare first name, a private subject described without a
keyword pass without an alert. Filtering is up to you, by applying these rules to every text you
write.

## The model

Three levels, each recognizable by a question:

- **Task**: one action, one result, done in one go by a person, an AI agent or a tool.
  Question: *can you tell when it is finished?* Example: "Write the minutes of a client
  meeting". What a tool does internally to produce its result is not a separate task.
- **Process**: at least two tasks, always in the same order, launched by the same trigger, up to
  an exit proof. Question: *does the order change from one time to the next?* If so, it is not a
  process but a routing. Example: "Prepare and hold the monthly follow-up meeting of a client".
- **Operational role**: receives different cases and chooses what to do with them (launch a
  process, do a task alone, hand over to someone). Question: *do you have to choose what to
  launch?* Example: "Support clients after signature". A role is not a position: a person often
  holds 3 to 8 roles.

The status of each task, **today**:

| Status | Meaning |
|---|---|
| **A** automated | An agent, a script or a tool does it; a human steps in only if it fails. |
| **S** skilled | The AI runs the method of the task through a skill or an agent (cited in `tools`) and produces the result; a human validates or triggers before what follows. |
| **C** conversational | The AI only helps through a conversation: a chat (Claude, ChatGPT…) or a bot that answers. The person asks, copies, adapts and does the work; no skill carries the method. |
| **M** manual | A human does it; no tool carries it. |
| **J** judgment | A human decision on value, priority, risk or the relationship, or a live exchange that depends on the person (running a client meeting, a webinar, negotiating). It will stay human. |

Four cases that cause confusion:

- A task done with Claude by writing or pasting a prompt each time is **C**; when its method is
  written in a skill (or an agent) that Claude runs, it is **S**, and that skill is in `tools`.
  Ask: "When you use the AI for it, does it follow a skill, or do you explain what to do in the
  chat?"

- A decision that applies simple and stable criteria (company size, sector, amount) is **M**,
  not J: it would become A if its criteria were written, and that is its blocker (section
  "Blockers").
- What a tool does on its own, at a date or on an event, and whose result can be checked (a
  scheduled newsletter that goes out, a reminder sent to registrants), is an **A** task;
  scheduling it in the tool is an M task.
- Classify according to what happens today, not to what would be possible: a task the AI could
  do but that nobody hands over to it is M. The referential compares teams with each other; an
  optimistic status distorts the comparison. What is possible goes into `target`, and what is
  missing to get there into a blocker (section "Blockers").

A role can be handed over to agents when five conditions are met: the work arrives without a
human launching it (**automatic entry**), the list "case → what handles it" is written
(**routing**), the key tasks are automated, a person is named for the cases outside the rules
(**human fallback**), and someone reads a few measures (**supervision**).

Each task also carries its **relevance** (`relevance`): five ratings from 1 to 3 used to estimate
quickly whether it is worth working on (automating it, tooling it).

| Axis | 1 | 2 | 3 |
|---|---|---|---|
| `reach`: how many people of the company the task affects (those who do it and those who wait for its result) | one or two people | a whole department | potentially all employees |
| `frequency`: how often it comes back for the company | once a year or less | at least once a month | potentially every day |
| `effort`: how long one execution done by hand takes | less than 30 minutes | between 30 minutes and 2 h | more than 2 h |
| `describability`: how well the task is mastered from end to end, that is whether its input, its deliverable and its method are structured | only one of these three elements is structured, or none | two of the three are structured | the input, the deliverable and the method are structured |
| `payback`: how long until the time saved pays back the time spent automating it | more than three months | between one week and three months | less than one week |

Between two levels, the rating is the highest whose condition is met: a weekly task is worth 2 in
frequency, a quarterly task 1; three people of a department of six are worth 1 in reach. Effort
counts one execution of the task as its name describes it: "Run the prospecting call" = one
call, not a session of calls.

An element is structured when it has a written and stable form that can be given as is to an AI:
an input that always arrives in the same form (a ticket and its fields, a form, an export), a
deliverable that follows a template, a written method (a procedure, a checklist, a skill). An
oral request, a free message, a deliverable redone differently each time or a know-how nobody
wrote down are not. The map helps rate it: `input`, `output` and `tools` say what exists; an A
task is worth 3, because the tool that does it has a written input, deliverable and method; the
method of a J task is a judgment, it is not structured. The payback is computed: the time to
automate the task, divided by the time it saves each week (the duration of one execution × the
number of executions per week, all people included). Count about 30 minutes to automate a task
whose input, deliverable and method are structured and that a prompt or a skill can carry, half a
day or more when two of these elements must first be written or when the task links several
tools. Examples: a 30-minute task done once a year, fully structured, pays back in one year (1);
a 10-minute task that 10 people do every week, whose deliverable alone is structured (half a
day), pays back in 2.4 weeks (2). A J task that no tool can prepare has no payback:
`payback: null`.

Rate yourself each axis that what you read or heard, or the nature of the task, lets you
estimate: a frequency mentioned, the volume of an input, the number of people waiting for the
deliverable, a duration; validating an appointment in a tool takes less than 30 minutes. For the
others, ask the person (step 4). If they do not know, keep your estimate when you have one;
otherwise the axis is `null`. The score is (reach + frequency + effort + describability) ×
payback, out of 36: in the sum, a `null` axis counts 0; a `null` payback counts 1; "?" when no
axis of the sum is estimated.

Every task carries its **job** (`references/format-rpt-v1.md`):

- `job`: what the task is for, in two parts that read as one sentence, « When <when>, I want to
  <name>, so that <so_that>. »: `when`, the situation or the trigger that starts the task (not
  its frequency); `so_that`, the result for someone (the client, a team, the next decision),
  never the deliverable restated. Each part is one short sentence, written without its leading
  words, which the views add. Example: `{when: "a new client's organization is created",
  so_that: "the kick-off workshop starts on a ready platform"}`. Write it for every task, with
  `basis: {job: inferred}` when you deduced it from the map rather than heard it.

The ratings rank tasks against each other; for **M and S** tasks, the map also carries figures,
which make the action plan of the referential:

- `measure`: the duration of one execution in minutes (`minutes`) and the number of executions
  per month for one person (`runs`), with their origin (`basis`): `observed` when you counted
  them in a source (36 meetings per month in the calendar, 120 tickets per month, a skill
  launched 11 times in three months), `declared` when the person gives them. The duration sets
  the effort rating (up to 30 minutes: 1; up to 2 h: 2; beyond: 3): the script flags a gap;
- `stakes`: what happens when the task is done late or badly, a rating (`level`) and a sentence
  (`text`): 1, an internal nuisance, caught up without visible cost; 2, a visible cost (someone
  waits, work is redone); 3, a loss (a client, revenue, a compliance risk). The sentence
  describes the consequence, without a client name or an amount;
- the **blockers** of the task: what keeps it from reaching `target`, each with its type and the
  state of its resolution, in the `blockers` list of the map (section "Blockers");
- `build`, when a target is written and you know how to estimate it: the work to reach it, its
  size (`size`: `S`, less than a day; `M`, a few days; `L`, more than a week) and its form
  (`kind`: `prompt`, `skill`, `agent`, `workflow`, `script`, `feature`, `connector`). Otherwise
  the merge estimates it.

Each task also cites its **data sources** (`data`): the business data it reads or writes
("Pipeline and prospects", "E-mails", "Development tickets"). A data source says in which tools
of the company this data is found and, for each tool, how the AI reaches it (`connector`):

| `connector` | Meaning |
|---|---|
| `native` | a connector of Claude's directory, enabled for the organization (native MCP) |
| `mcp` | an MCP server the company added (custom connector) |
| `api` | a skill or a script calls the tool's API |
| `export` | someone exports or copies the data for the AI |
| `none` | the AI has no access to it |
| `null` | to be specified |

The referential uses it to rank the connectors to activate first: those that give the AI the
data of the largest number of manual, conversational or skilled tasks. The organization's data sources are in
`catalogues/data-sources.yaml`. The first tool of a source is its reference tool: a task that
cites a source without citing any of its tools in `tools` counts for it.

**Data sensitivity.** Each data source says what it contains (`sensitivity`): `public`,
`personal` (what identifies a person), `client` (data and documents of a client), `hr`
(headcount, arrivals and departures, positions), `internal_confidential` (non-public finances,
strategy, intellectual property, code included), `regulated` (sensitive personal data,
individual files and named salaries, trade secrets, regulatory or contractual obligation),
`credentials` (logins, passwords, API keys); `[]` for internal working data only. The AI policy
of `catalogues/ai-policy.yaml` (when the organization has one; without it, the rules of the
section "Privacy and personal data") gives a rule to each category, and the referential deduces from it what an AI
may receive for each task. A source of the catalogue already has its sensitivity: declare it
again only if the person says it contains something else (an HR spreadsheet that also holds
salaries). A source of `references/data-sources.yaml` that you declare to say where the
organization keeps it (no catalogue of its own) copies its `sensitivity` from that file. A source you declare is classified from the type of data, never by reading its
content, with `basis: {sensitivity: inferred}`, and is confirmed at step 4.

**Handoffs.** When a process ends with someone else (another person, another team), write it in
`handoffs`: who takes over the work (`to`: the id of a role or a process of the map, otherwise
the role or the team in words, "the CSM team"), what is passed on (`what`), the tool or the data
source it goes through (`via`), and what gets lost or delayed at that moment (`issues`), without
the name of a person, of a client, or an amount. Delays and errors often sit at these handoffs;
the referential gathers them from one team to another.

**Written method.** When an authorized source shows that the method of a task is written (a
Notion procedure, a Drive document, a skill), keep its link in `method`: the URL, or the id of
the skill. Never a guessed link, nor a document the person cannot open. For describability, a
written method is one of the three structured elements (with the input and the deliverable).

**Where each fact comes from.** Each element says in `basis` how its facts are known:
`observed` when you found them in an authorized source (a recurring meeting in the calendar, a
skill launched in the conversations), `declared` when the person said them (framing, typical
week, answers of step 4), `inferred` when you deduced them from clues without confirmation (a
relevance axis estimated, a data source drawn from the tools of the task, a status read in the
description of a skill). Write it for the facts that matter: `status`, `frequency`, `data`,
`relevance` (or one axis: `relevance.effort`), `stakes`, `build`, `method`, `handoffs`, and
`sensitivity` of a source you declare; `measure` keeps its own `basis`. An inferred fact is
visible as such in the referential, and the person confirms it at the next update of their map.

Each role, process and task is filed in one or more **departments** (the first is the main one),
by id: `strategy-management` (strategy and management), `product-design` (product design),
`software-development` (software development), `it-operations` (infrastructure and operations),
`data-analytics` (data and measurement), `customer-support` (customer support),
`customer-success` (customer success and onboarding), `sales` (sales), `marketing` (marketing and
communication), `people-hr` (HR and recruiting), `finance-admin` (finance, administration and
legal), `security-compliance` (security and compliance), `knowledge-ai-tooling` (knowledge and
AI tooling), `operations-supply` (production, logistics and supplies of a physical activity). If you hesitate, read the examples and aliases of `catalogues/departments.yaml`. If
none fits, take the closest and write the original word in `notes`.

## Blockers

That a task exists is half of what the referential needs; the other half is what keeps it from
moving towards its `target`, since when, and whether it is solved. A **blocker** is one work
problem ("the recruiting software gives no API access", "the sorting criteria are not written"),
with the tasks it holds back and the state of its resolution. The map writes its blockers in the
`blockers` list (`references/format-rpt-v1.md` §11), one entry per problem; the organization
keeps them in a register, which the merge feeds from the maps.

**What to look for.** For each task, the M and S tasks and those with a `target` first: what
keeps it from going one step further (M to S, S to A)? A connector or an access that is missing,
a method that is not written, a decision awaited, a tool to build, data missing or of poor
quality, a licence, a security rule, a budget, the organization (nobody in charge, a team busy
elsewhere), a provider who does not deliver. A J task can be blocked too (the decision cannot be
taken without data).

**Where to find it.** Ask the person (step 4). In full mode, also look for signals in the
sources they authorized (step 1, question 4), with the same reading as step 2 (the last three
months, wide and shallow):

| Source | Signals | What you keep |
|---|---|---|
| Messaging (Slack, Teams) | « je n'ai pas accès », « bloqué », « en attente de », « ça ne marche pas », « toujours pas »; "no access", "blocked", "waiting for", "doesn't work", "still not" | the problem, the channel and the date |
| E-mails | access requests, follow-ups left without an answer, refusals | the problem and the date |
| Tickets (Jira…) | a ticket in a blocked status, an "is blocked by" link, « en attente » | the problem and the key of the ticket |
| Meeting notes and transcripts | « on n'a pas pu », « il faut une décision de »; "we could not", "we need a decision from" | the problem and the date of the meeting |

Example: on Slack, "Je n'ai pas accès aux données pour faire mes slides" gives a blocker of type
`access` on the task that produces the slides.

**What you keep.** The section "Privacy and personal data" applies in full. Keep the work
problem only, in a sentence of yours: never the content of the message, never the name of a
colleague, a client or a provider, no personal data. A problem you know only through a
confidential case (an HR case, the company's finances) stays out of the map. `evidence` says
where and when the problem was seen, in 300 characters at most: « Slack #csm, 2026-10-08 »,
« ticket DP-6301 », « e-mail, 2026-09-30 », « réunion d'équipe du 2026-10-02 »; no quote, no
name, no link to a private message.

**Confirm before writing.** A blocker you found in a source is inferred: `basis: inferred`, with
its `source` (`slack`, `email`, `ticket`, `meeting`) and its `evidence`. It goes into the map only
after the person confirms it, with the question tool (section "Asking a question"): your message
shows a table of the inferred blockers (the problem, the tasks, the type, where and when you saw
it), and the tool asks, for each one, "Still a problem", "Resolved" or "Not a blocker"; beyond
four, a single question where the person writes their corrections. A rejected blocker leaves the
map. A confirmed blocker keeps `basis: inferred`, `source` and `evidence`: the merge reads there
that it was found in a source. A blocker the person raises themselves is `basis: declared`,
`source: map`.

**How to write it.**

- One problem, one entry: the same problem on several tasks ("the accounting software is not
  connected") is one blocker that lists all of them in `tasks`; two problems on one task are two
  blockers. `tasks` cites tasks of the map only.
- `state`: `open` (nothing moves), `in_progress` (someone works on it: an access requested, a
  method being written), `resolved` (lifted), `dropped` (given up: the task changed, the target
  was abandoned). Ask since when: `opened` is the date it was first seen (the date of the
  message, of the ticket or, failing that, of the interview); `resolved` is the date it was
  lifted or dropped, written only for these two states, with `resolution`: what lifted it
  ("connector enabled", "criteria written") or why it was dropped.
- `type`: `connector` (the AI does not reach the data), `method` (the method is not written),
  `tool` (a skill, an agent or a script to build), `decision` (someone must decide or validate),
  `data` (data missing or of poor quality), `licence`, `access` (a person or the AI lacks a
  right), `security` (a security or compliance rule), `budget`, `organization` (nobody in charge,
  priorities), `provider` (a vendor or a provider), `other`.
- `owner`: the id of the role of the map that can lift it, when there is one; a person or a team
  outside the map goes into `notes`, as a role ("the IT administrator").
- Ids are local to the map: `BLK-1`, `BLK-2`…; the merge renumbers them in the register.
- Write blockers in the list, never as a `blocker` text on the task. A starting map that still
  has `blocker` and `blocker_type` on its tasks remains readable: in the update, move each text
  to the list.
- A resolved blocker stays in the map, with its date and its resolution: it says why a task
  moved (a status that went from M to A).

## Access to the OS and recurring agents

The map also says how far the AI of the organization reaches the person's work: whether their
AI reads the organization's OS, and which agents run tasks for them without being launched by
hand. The map writes both at the top level of the person's first map (`references/format-rpt-v1.md`
§12): one `people` entry for the person, and one `agents` entry per recurring agent they set up.
The organization adds them up into its coverage of the OS and its list of recurring agents.

**Access to the OS.** The OS is the folder that holds the referential: the parent of
`referential.drive_folder` in the configuration (for example
`<Organization>/<Organization>-OS/`). Having an OS is not required to map. When the organization
has none yet (the referential folder does not exist, the folder of the configuration holds
`rpt-config.yaml` alone, or the person says so), do not check the access: the `people` entry has
no `os_access`, its `notes` say "no OS yet" (in the person's language), and you tell the person
nothing about what it costs. Otherwise, check each way, without reading the content of the folder:

- **Connector** (`mode: connector`): with the Drive tool, search for the OS folder by its title.
  Found: `state: works`, `checked` = today, `basis: observed`. The connector works but the folder
  is not found while others in the organization reach it (not shared with the person, other
  account): `state: not_found`; tell the person who can share it (the person who maintains the
  referential, in the configuration). No Drive
  tool in this conversation: ask whether the connector is enabled; `state: unchecked`,
  `basis: declared`.
- **Local folder** (`mode: local`): ask whether the OS folder is synchronised on their computer
  (Google Drive for desktop, OneDrive) and shared with Claude (Cowork folder, Claude project,
  Claude Code). If you can list the folder in this conversation, `state: works`.
- **Repository** (`mode: repository`): in Claude Code, the repository that holds the OS
  (`repository_path` of the configuration) is open: `state: works`.
- No way: one entry `mode: none`. Say what it costs: their tasks cannot draw on the OS (offers,
  objections, client records), and what enables it (the connector, the shared folder).

The `id` of the person is `person:<first name in lower case, without accents>` (`person:helene`);
`name` is the first and last name (`Hélène Martin`): two people of an organization can share a
first name, and a first name alone merges them.

**AI licence.** Ask which AI the person uses for work and with which plan (`ai_plan`): the tool
(`saas:claude`, `saas:chatgpt`…), the plan as the vendor names it (Free, Pro, Max, Team,
Enterprise), its `tier` (`free`, `standard`, `premium`: premium is the plan with the most use,
such as Claude Max or a premium seat of Claude Team or Enterprise), and its `modes`: `thinking`
if the AI can reason before it answers (extended thinking), `work` if it can work on files and
tools (Cowork, Claude Code, artifacts, generation of images or documents). In a Claude
conversation you can read the plan and the modes from the settings when the person shows them;
otherwise `basis: declared`. No AI for work: no `ai_plan`, and say so in `notes`. The
organization counts, per team, how many people have each access (README_operations.md §1.18).

**Recurring agents.** List what runs for the person without being launched by hand: the
scheduled tasks of their Claude (list them with the tool when it exists; otherwise ask), their
Claude Code Routines, the agents they keep (Claude Managed Agents, a worker, an automation in
Zapier or Make that calls an AI). For each one, write an `agents` entry: what it does (`name`),
its `kind` (`scheduled-task`, `routine`, `managed-agent`, `worker`), when it runs (`schedule`),
its `state` (`live`, `construction`, `paused`), the tasks of the map it does (`tasks`, usually A
or S), the skills it runs (`skills`) and the data it reads (`data`). Its `people` is the person.
Ask who it tells and how (`notify`: a Slack message, a mail recap, an alert when it fails), and
whether its last runs gave the expected result without repair: when they did, write `stage`
(`level: functional`, with that answer as `evidence`); the referential takes it from there
(`references/format-rpt-v1.md` §12). Never the prompt of the task, nor what it produced: its
purpose and its schedule only. Ids are local to the map: `ag:<slug>`.

## Step 1 — Frame

Ask these questions with the question tool (section "Asking a question"), in a single call if
the tool accepts five questions, otherwise the first three then, after the answers, the other
two, question 5 (the mode) first: in quick mode, question 4 is not asked. Wait for the answers. Question 4 is multiple choice: one answer per source. Do not ask again
a question the request already answers ("I am a CSM"): reuse the answer and ask only to correct
it.

1. Your first and last name, and your hats: the job or jobs you hold (for example HR, finance and CSM)?
2. Have you already sent a map (a `.rpt.yaml` file)? If so, add it to the conversation; if you
   have the OS of <the organization> on your computer, it is in <the folder of merged maps>. I
   start from what is written and ask you only for what is missing or has changed. (In Cowork or
   Claude Code, also offer that they point you to this folder: you then read only their maps
   there.) When the organization has no OS yet (section "An organization without an OS"), leave
   out the sentence about the OS: "No, it is my first map" is the first answer offered.
3. Does the map cover you alone or your team? (If it is the team: who belongs to it, with the
   first and last name and the role of each.)
4. Which sources may I read? Offer the list of what you really have access to in this
   conversation (see step 2), their skills included, and the person ticks. **The mailbox always
   comes first, marked "recommended"**: sent e-mails are the most direct trace of what the person
   delivers (minutes, a proposal, a report, a reminder), received e-mails of what is asked of
   them. Say what you will read there: over three months, the subjects, the dates, the type of
   recipient and of attachment; never the text of an e-mail. Without a mail tool in your list of
   tools (Gmail, Outlook), offer it anyway, with what lets you read it: enable the Gmail or
   Outlook connector in Claude's settings, Connectors section (if the organization allows it),
   then tell you. If the person cannot or does not want to, ask them at step 4 for the list of
   e-mails they send each week or each month. Also offer the messaging (Slack, Teams), the
   ticketing tool and the meeting notes or transcripts when you can read them: they show what
   blocks the tasks (section "Blockers").
5. **Full** mode (I read the authorized sources, then interview you: 30 to 40 minutes) or
   **quick** mode (I only interview you: 15 minutes)? In quick mode, for a first map, also tell
   me about a typical week: what comes to you (requests, meetings, deadlines), what you do with
   it, with which tools, how often, and how long each thing takes you.

In conversion mode, replace questions 4 and 5 with: who holds each role described in the
document, and what the document does not say (frequencies, durations, tools, who validates).

If a question stays unanswered, take the most cautious assumption and say it: it is a first map,
it covers the person alone, and no source is read without approval (quick mode).

For a first map, if the request already names the hats ("I do HR and finance"), propose in this
message a code for each, taken from the list of the section "One map per hat"; otherwise, propose
them at the start of your next message (the reading of the sources or the first draft), saying
how many maps that will make. The person can group or split hats, or change a code, until the end
of the validation. Do not ask for the company: it is the organization of the configuration.
Finally, check whether you have a tool to create a file in Google Drive or send an e-mail: if
there is none, say so in this message, the person will drop their maps themselves at the end.

## Step 2 — Read the authorized sources

Offer only the sources your tools really let you read; a source promised then unreadable wastes
time and trust. The mailbox is the exception: without a connector, offer to enable it (step 1,
question 4). Limit yourself to the last three months. Read wide and shallow: titles, subjects,
senders by type, recurrences; not the body of messages. Leave aside, without noting it,
everything the Privacy section excludes. For each activity signal, note where it comes from (the
source, a date, an anonymized example): it will be used in `sources`. For each blocker signal,
note the task it concerns, the source, the place (channel, ticket key) and the date, not the
message: it will be used in `evidence`.

| Source | What to look for |
|---|---|
| Your memory about the person, their instructions, their Claude projects | Their job, their responsibilities, their tools, what they often hand over to you. |
| Their skills: those they created or installed, those of the organization they launch (the list of available skills you see; in claude.ai, the skill folders mounted under `/mnt/skills/`) | Each skill they use carries at least one task, often S (the skill produces, they validate); its description gives the input and the deliverable. Past conversations say which ones they really launch, and how often. A personal or business skill installed but never launched is not a task: ask. A generic skill (docx, xlsx, pptx…) is a task only through the activity it serves (a client review in pptx). A skill unrelated to their work stays out of the map. |
| Past conversations (history search tool, if it exists) | Requests that come back are tasks; those you do alone are A or S. Look for "every week", "every month", "as usual", "reminder", "report", "minutes", "validate", "prepare" (and their equivalents in the person's language: « chaque semaine », « tous les mois », « comme d'habitude », « relance », « rapport », « compte rendu », « valider », « préparer »). |
| Attached files, project files, Drive | Procedures, templates, checklists, minutes, tracking sheets. |
| Calendar | Recurring meetings (often processes or judgments), typical appointments, and their frequency. Not personal appointments. |
| Mailbox: sent e-mails (Gmail: `in:sent newer_than:3m`; Outlook: sent items) | What the person delivers. Each kind of e-mail that comes back (minutes, proposal, report, reminder, invitation, standard answer) is the deliverable of a task; their number over three months, divided by three, gives `measure.runs` (`basis: observed`). Note the typical subject, the type of recipient (client, prospect, internal, partner) and of attachment (presentation, quote, spreadsheet). A sending done by a tool (sequence, automatic reply) is an A or S task. Never the text, nor the name or address of a recipient. |
| Mailbox: received e-mails; messaging (Slack, Teams) | What is asked of the person: types of requests (the entries of a role), where they come from by type, their volume; reminders. The signals of a blocker (section "Blockers"): access requests, follow-ups without an answer, refusals, « je n'ai pas accès », « en attente de », "still not". Never the content. |
| Ticketing tool, CRM, tracking spreadsheet (Jira, HubSpot, Notion…) | The statuses of a ticket or a deal (they are the steps of a process), who moves what, the volumes. The blocked tickets and the "is blocked by" links: blockers. |
| Meeting notes and transcripts | Recurring meetings and what they decide; the signals of a blocker: « on n'a pas pu », « il faut une décision de ». Never what a person said. |
| Existing automations (Zapier, Make, scripts, agents, saved prompts) | What they do: they are the A or S tasks. |
| Scheduled tasks and Routines of their Claude, the OS folder | The recurring agents and the access to the OS (section "Access to the OS and recurring agents"): the title and the schedule of each scheduled task, never its prompt; whether the OS folder is found. |

In Claude Code, in a repository: the instruction files (`CLAUDE.md`, `AGENTS.md`), the skills
(those of the repository, their personal skills in `~/.claude/skills/`, those of their plugins),
agents, hooks, CI workflows and scripts, and `git log` of the last three months; with the
person's explicit approval, their past sessions (their messages and the skills they launch
there, not the tool outputs).

In quick mode, skip this step and start from the answers of step 1, typical week included.

## Step 3 — Write a first draft

1. **List the entries**: what comes to the person (a request, a status that changes, a date, an
   event), from where, how often.
2. **Group into roles**: a role = a set of entries handled with the same choice logic. Name
   "verb + object", mission in one sentence. File each role under its hat. A "role" that
   receives only one kind of entry is often a process of another role: keep it only if the
   person confirms it.
3. **For each role, write the routing**: for each type of incoming case, what handles it (a
   process, a task, another person).
4. **Write the processes**: trigger, tasks in order, exit proof ("quote sent and reminder
   scheduled"), human gates (who validates what). When the launch is a short separate action
   (opening a tool to launch a skill, scheduling a sequence, triggering a check), it is the
   first task (M); when it merges with the first task (the person starts writing with the AI
   themselves), there is no launch task and `trigger.type: manual` is enough. Real work at the
   head (choosing prospects, writing) is not a launch: it is a step like the others. A process
   that a tool triggers, on an event or at a date, has no launch task; a date the person must
   remember (an end-of-quarter review) is a `manual` trigger, and the launch follows the rule
   above. Write the order of the processes: `next` (the processes that start when this one
   ends), and on the first process of a chain how many documents or events enter it a month
   (`trigger.volume`: `{count: 200, kind: document, unit: e-mails}`, `kind` `document` or
   `event`; ask it when the sources do not give it). When a source shows what waits at the input
   of a task (a board column, a status, an unread folder), write the count and its date on the
   task (`queue: {count: 198, unit: tickets, at: '2026-10-17', basis: observed, source: …}`); a
   large stock is the sign of a process that does not keep up. Choose
   `automation` from the statuses of the steps (`references/format-rpt-v1.md`
   §7). The A steps count: a process is `manual` only if its M steps outnumber its A steps. A
   sequence that sends each e-mail on its own (A), and whose replies the person reads (M,
   without a blocker), is `assisted`. When the process ends with someone else, write `handoffs`
   (section "The model").
5. **Write the tasks**: name "verb + object", input → deliverable, tools (including the skill
   they launch for this task), data sources (`data`, point 6), who does it today (`by`), status
   A/S/C/M/J, and its relevance (`relevance`: rate the axes you can estimate, keep the others for
   step 4). A task belongs to a single role, the one that holds it; it can be the step of
   several processes, or of none. Put `target` when an automation is conceivable, and write in
   the `blockers` list what is missing to get there (written rules, a trigger, an access, a
   tool), with the signals of step 2 (section "Blockers"); `build` when you know how to estimate
   the work. For each M, C or S task, write `measure` with
   what the sources give (`basis: observed`) and `stakes` when the consequence of a delay is
   clear; the rest is asked at step 4. Write `method` when a source shows where the method is
   written.
6. **Note the data sources**, in every mode. For each task, the business data it reads or writes
   (`data`): writing the minutes of a meeting reads "Meetings and minutes" and writes "Pipeline
   and prospects". Take the ids of `catalogues/data-sources.yaml`; data that is not there is
   declared in the `data_sources` list of the file, with its tools ("Candidatures" in the
   example). For each tool of a declared source, write where the data is (`where`: "client
   records", "Drive folder of proposals") and how the AI reaches it (`connector`), from the
   tools you have in this conversation: a connector of Claude's directory present in your list
   of tools (Gmail, Google Drive, Slack, Notion, HubSpot, Jira…) gives `native`; a connector the
   company added (an internal MCP server) gives `mcp`. A tool without a connector in your list:
   `export` if the person copies or exports their data for you, `none` if they do not give this
   data to the AI; otherwise the question goes to step 4. When what you observe differs from
   `catalogues/data-sources.yaml` (a connector present for a tool the catalogue says "to be
   specified", data kept in another tool, a spreadsheet instead of the CRM), declare the source
   again in `data_sources`, complete, with what you observed: the merge updates the catalogue. A
   task that touches no business data (running a workshop, negotiating) has no `data`. A source
   you declare carries its sensitivity (`sensitivity`, section "The model").
7. **Link each task to the key results it serves** (`okrs`), when the organization has
   `catalogues/okrs.yaml`; without it, no task has `okrs` and step 4 asks no question about them.
   This catalogue gives the organization's objectives and their key results (KR), each with what
   it measures (`metric`).
   A task names a KR when its deliverable directly changes the measure of this KR: the task
   done, or done better, moves the figure. Preparing the second meeting with a prospect serves
   "50% of first meetings lead to a second"; keeping the CRM up to date does not serve it, even
   if the figure is read there. Link to the KR, never to the whole objective, at most two KRs per
   task, and write `basis: {okrs: inferred}`. A task without a direct link has no `okrs`: most
   tasks have none, and it is not a gap. A link you doubt goes into the question of step 4 about
   the OKRs.
8. **Write what is missing**: a desired activity that does not exist yet (a process the person
   would like to have) is written with `state: proposed`.
9. **Note your confidence**: each element has its `sources`, and the origin of its facts that
   matter in `basis`; a deduction without a clue goes into the list of questions. Also compare
   the volumes from one source to another (a skill launched 11 times in three months for 36
   monthly meetings): a gap is a question for the first round. Likewise match each kind of sent
   e-mail that comes back with the tasks of the draft: an e-mail delivered without a matching
   task is a forgotten task, to confirm in the first round.

## Step 4 — Have it validated (three rounds at most)

Show the first draft in summary: one table per role (tasks, statuses and relevance), the roles
filed by hat, then the list of processes. Then ask, with the question tool, **3 or 4 questions
at a time**, the most important first: a missing role, a process whose order is doubtful, an
uncertain status or relevance, an unknown human fallback, a frequency or a duration, a tool for
which you do not know whether the AI reaches it (a single question for all these tools). The
relevance axes you could not estimate make a single question: your message shows a table of the
tasks concerned, with the missing axis and your estimate when you have one, and the tool asks
whether these estimates are right ("yes, keep them", or the person writes their corrections).
The measures and the stakes of the M and S tasks likewise make a single question: a table with,
for each task, the minutes per execution, the number of times per month and what happens when it
is done late or badly (1, 2 or 3, with a sentence), your figures when you have them, and the tool
asks to correct or complete; a figure given by the person is written `basis: declared`. The
handoffs also make a single question: a table of the processes that end with someone else, with
who takes over the work, through which tool, and what gets lost or delayed at this handoff; the
person corrects or completes. The links to the OKRs make a single question: a table of the tasks
linked to a KR, with the KR and the deliverable that moves it, and of the tasks whose link is
doubtful; the person removes, adds or confirms (a confirmed link becomes `declared`). A person
who does not know the OKRs answers "I don't know": the links stay `inferred`, the merge will
reread them. The blockers make a single question: a table of the blockers of the draft, the
inferred ones first with where and when you saw them, then the M and S tasks that have a
`target` and no blocker; the person confirms or rejects each inferred blocker, corrects the
state and gives the date (section "Blockers"). The sensitivity of the sources you declare is
confirmed in the question about tools. If the mailbox was not read, a question asks for the
kinds of e-mails the person sends each week or each month (minutes, proposals, reports,
reminders), by type of recipient, without names: each is a task, to match with the draft. A fact the person confirms goes from `inferred`
to `declared`. Correct after each round. A question left unanswered is asked once more in the
next round, with the assumption you will keep if it stays unanswered; "I don't know" is an
answer, which is not asked again. Stop when the person says it is right, even if questions remain
unanswered, when there is nothing left to ask, or after three rounds; what remains uncertain goes
into `gaps` or `notes`, with the assumption kept. Beyond three rounds, the person drops out and
the map is never sent.

## Step 5 — Write the maps and check them

1. Read `references/format-rpt-v1.md` (the fields, the allowed values, the YAML pitfalls) and
   start from the structure of `assets/exemple.rpt.yaml`.
2. For the software and skills already known to the referential (Claude, Slack, Google Drive,
   Notion, Jira, HubSpot, the organization's skills…), reuse their id as it appears in
   `catalogues/tools.yaml`. Declare in the `tools` list of the file any other tool cited: a tool
   the catalogue lists (Gmail, when it is there) is not declared again; a Zap, a personal skill
   or a saved prompt is. Without `catalogues/tools.yaml` (an organization without an OS, a first
   run), declare every tool cited, Claude and Gmail included, with an id `saas:<name>` as in
   `assets/exemple.rpt.yaml`. Same for the data sources: the ids of
   `catalogues/data-sources.yaml` (or `references/data-sources.yaml`), and `data_sources` for
   the others (step 3, point 6).
3. Write one file per hat, named
   `<code in lower case>-<first name in lower case without accents>-<YYYY-MM-DD>.rpt.yaml`
   (`rh-alex-2026-09-24.rpt.yaml`, `fin-alex-2026-09-24.rpt.yaml`); `meta.team` and the
   `team` of each role are the code of the hat, in lower case. For a team map:
   `<code>-team-<YYYY-MM-DD>.rpt.yaml` (`<code>-equipe-<YYYY-MM-DD>.rpt.yaml` is accepted too),
   `meta.authors` = the person who launched the mapping (first and last name) then Claude, and the
   first and last names of the members in `holders` and `by`. In each file, `meta.detector` is
   `ts-general-check-process-cartography@` followed by the number of `metadata.version` of this
   skill (`@2.10`): the merge measures what each version proposes and what the referential keeps
   of it. Write the files where your environment puts the files to deliver (in claude.ai:
   `/mnt/user-data/outputs/`).
4. Check them, all at once:

   ```bash
   python3 <skill folder>/scripts/validate_rpt.py <file> [<other file> …] \
     --config rpt-config.yaml --catalogues catalogues
   ```

   The script prints its messages in the organization's language (`--lang en` or `--lang fr` to
   choose). For each file, it lists the errors (the file cannot be merged as long as some
   remain), the warnings (a code that is not the map's, the personal data alerts, the declared
   automations that the step statuses contradict, the tasks without relevance, the M, C or S tasks
   without `data`, without `measure` or without `stakes`, a measured duration that the effort
   rating contradicts, a blocker found in a source without `evidence`, a task that still writes
   its own `blocker`), then the figures of each role and the "Relevance", "Blockers" and
   "Connectors" lines.
   Fix the form yourself (quotes, ids, undeclared tool, value outside the list) and run it again
   until 0 errors. Handle each warning: file the element in the map of its hat, remove the data
   flagged, correct the automation, rate the missing relevance or ask for it (`null` if the
   person does not know), write the data sources of an M, C or S task, ask for its measures and its
   stakes, correct the effort rating a measure contradicts, ask who does an M or J task
   without `by`, write where and when a blocker was seen (`evidence`), or move the `blocker` of
   a task to the `blockers` list. If PyYAML is missing, run `pip install pyyaml`. Add `--format`
   to rewrite the files in the referential's style, and `--since <starting map>` last for an
   update.
5. Without Python: check by hand that each id carries the code of its map, that each `role`,
   `steps` and `routing.to` that looks like an id exists in the file, that each tool cited is
   declared or present in `catalogues/tools.yaml`, that each `data` is declared or present in
   `catalogues/data-sources.yaml`, that no id appears twice, that the values are in the lists of
   `references/format-rpt-v1.md` (the axes of `relevance`: 1, 2, 3 or `null`), that the `tasks`
   of each blocker are tasks of the file and that `resolved` is written exactly when its state
   is `resolved` or `dropped`, and reread each text, those of the blockers and their `evidence`
   included, with the rules of the Privacy section.

## Step 6 — Give the summary and the sending preview

**A. The summary**, in the conversation. It is for the person and is not sent:

- the roles, filed by hat, with for each the number of tasks by status and the coverage (A
  tasks / (tasks − J tasks)); reuse the script's figures rather than computing them again;
- for an update, what has changed since the starting map (the script's "Since the starting map"
  line);
- the processes that already run on their own;
- the five tasks to automate first: the most relevant (highest score) among the M and S tasks,
  with their score and what is missing for each; reuse the script's "Relevance" line;
- the blockers that still hold tasks back, with their tasks and since when, and, for an update,
  those resolved or dropped since the starting map: the script's "Blockers" line;
- the connectors to activate first, and those the AI already reaches: the script's "Connectors"
  line;
- the questions left open;
- the sources read (in conversion mode, the document) and those set aside (refused by the person
  or inaccessible);
- what was left out of the map for privacy, described without repeating it ("an external
  contact and their phone", not the name or the number).

**B. The sending preview**, in an artifact. It shows everything that will be sent, and only that;
with several maps, a single preview shows them all, one after the other:

```bash
python3 <skill folder>/scripts/preview_rpt.py <file> [<other file> …] --config rpt-config.yaml > apercu.md
```

When the maps will not go to the intake folder or address of the configuration (it does not
exist yet: step 7), add `--destination "<where they will go>"`; choose it before this run.

The preview's labels are in the organization's language (`--lang` to choose another); the
content of the maps stays as written. Create an artifact (Markdown document) whose content is
**exactly** this `apercu.md` file, without rewriting, summarizing or adding anything: it is the
only way for the person to see what will be sent. It starts with the people and roles named, and
with the alerts of the automatic check. Without artifacts, present the `apercu.md` file and paste
its content in your answer. Do not give the `.rpt.yaml` files to download yet: they are given at
step 7, after the approval, in the version the preview showed.

## Step 7 — Have the preview reviewed, then send

**Choose the destination first**, the first that exists in this list: the intake folder (found
by its id `intake.drive_folder_id`, or, without an id, by its name, the last part of
`intake.drive_folder` (`to-process` for `Acme/OS/to-process/`), searched in the folder of the
configuration and in its parent); the intake address `intake.email`;
the folder of the configuration (the folder of the link in the organization's instructions, when
the Drive tool can create a file there); otherwise the person drops the files themselves and
sends them to <intake.merged_by>. At the first run of an organization, the intake folder often
does not exist yet: say so in one line, without asking the person to create it.

Pass the destination chosen to the preview when it is not the intake folder or address of the
configuration: `--destination "<the folder of the configuration, link>"` (step 6), so that the
preview does not name a folder that does not exist.

**Always ask for a review of the preview before sending**, in the same message as the summary or
right after. The message says, in the person's language, with the destination chosen (for the
folder of the configuration, leave out `intake.visibility`, which describes the intake folder):

> "The artifact shows everything that will be sent, and nothing else. Review it, in particular
> the people named and the alerts. The file will go to <the intake folder>, <intake.visibility>;
> <intake.merged_by> will merge it into the referential."

then the question tool asks "Shall I send it as is?", with two answers: "Send as is" and "Change
something" (the person writes what). Neither is recommended. With several maps, say it in the
plural and name the files. If you have no sending tool, do not promise the sending: "… After
your approval, I give you the file to drop yourself in <the intake folder>.", and the tool asks
"Shall I give you the file as is?", with the answers "Yes, as is" and "Change something".

- Send only after an explicit approval given **after** this preview: "Send as is" (or "Yes, as
  is") chosen in the tool, or "yes", "send it" written. An ambiguous answer or a question is not
  an approval; an approval given earlier in the conversation does not count.
- If an alert remains, say what it flags before asking for the approval.
- If the person asks for a correction: correct the map, run `validate_rpt.py` and
  `preview_rpt.py` again on all the files, replace the artifact, and ask again. Send only the
  files as the last preview showed them.

After the approval, give the `.rpt.yaml` files to download, in the version the preview showed
(if you cannot create a file, their content in YAML code blocks). Then try in this order and stop
at the first that works:

1. **Google Drive.** With the file creation tool of the Google Drive connector, create each file
   in the intake folder: parent folder id `intake.drive_folder_id` (or the id of the folder found
   above), title = the name of the file, content = the YAML text in the text field of the tool (for example `textContent`; not a
   base64 field nor a field marked deprecated), content type `text/plain` (field
   `contentMimeType` or its equivalent), **conversion to Google Docs disabled** (the option
   `disableConversionToGoogleType` or its equivalent). Check in the tool's answer that the file
   created is of type `text/plain`: a Google Doc (`application/vnd.google-apps.document`) no
   longer reads as a YAML file and cannot be merged. If it is a Google Doc, tell the person, move
   on to e-mail and mention in the message the Google Doc to delete. Otherwise, give the link of
   the file created.
2. **E-mail**, if the Drive connector is absent or refuses (rights, folder not found, conversion
   option absent, file converted, no `intake.drive_folder_id`) and the configuration gives an
   intake address. Send to the intake address one message per file:
   - subject: `RPT map — <CODE> — <first name> — <YYYY-MM-DD>`, the code in capitals
     (`RPT map — CSM — Camille — 2026-09-24`), in the organization's language (in French:
     `Carte RPT — CSM — Camille — 2026-09-24`); for a team map, `team` (`équipe`) in place of
     the first name;
   - plain-text body: one sentence ("RPT map produced with the skill
     ts-general-check-process-cartography, to merge into the referential."; for an update,
     "Update of <starting file>, produced with the skill ts-general-check-process-cartography."),
     in the organization's language, then the complete YAML content, as is;
   - the file as an attachment if the tool allows it.

   If the tool can only create a draft, create it and ask the person to click Send.
3. **The folder of the configuration**, if the intake folder does not exist and there is no
   intake address: create each file there as in point 1 (the folder of the link in the
   organization's instructions), and tell the person that <intake.merged_by> will find it next to
   `rpt-config.yaml`.
4. **By hand**, if none is possible: tell the person to download the files you just gave them
   (those, not a previous version) and drop them in the intake folder (link:
   `https://drive.google.com/drive/folders/` followed by `intake.drive_folder_id`, when there is
   one), or send them to the intake address, one message per file, with the subject and the
   sentence of point 2; without either, give them to <intake.merged_by>.

Send nothing but the maps: neither the preview, nor the sources read, nor the summary. Tell the
person what was done for each file (Drive link, e-mail sent, draft created, or drop to be done by
them). If they correct a map after sending, redo the preview, ask for the approval again and send
the new version of this file with the suffix `-v2` before `.rpt.yaml`.

## Files of the skill

| File | When to read it |
|---|---|
| `references/format-rpt-v1.md` | At step 3 to choose `automation` (§7), at step 5 before writing the file: fields, allowed values, YAML pitfalls, script messages, the `blockers` list (§11). |
| `assets/exemple.rpt.yaml` | At step 5: a complete and valid map whose structure to copy. |
| `rpt-config.yaml` (address in the organization's instructions) | Before your first message: the organization, its team codes, the intake folder and address, what is never sent, where its catalogues are. |
| `catalogues/departments.yaml` | When an element hesitates between two departments: examples and aliases of each (without the organization's catalogue: `references/departments.yaml`). |
| `catalogues/tools.yaml` | At step 5: ids of the tools and skills already known to the referential. |
| `catalogues/data-sources.yaml` | At step 3 (point 6): the organization's data sources, their tools, the AI's access to each and their sensitivity (without the organization's catalogue: the common data types of `references/data-sources.yaml`). |
| `catalogues/okrs.yaml` | At step 3 (point 7), if the organization has one: its objectives and their key results, to link to the tasks. |
| `catalogues/ai-policy.yaml` | When the person asks what an AI may receive: the rule of each data category. |
| `scripts/validate_rpt.py` | To run at step 5; with `--since <starting map>` for an update. |
| `scripts/preview_rpt.py` | To run at step 6: the sending preview. |
| `scripts/build_rpt.py`, `scripts/rpt_i18n.py` | The referential's tool, called by `validate_rpt.py`, and the messages of the scripts in each language; no need to read them. |
