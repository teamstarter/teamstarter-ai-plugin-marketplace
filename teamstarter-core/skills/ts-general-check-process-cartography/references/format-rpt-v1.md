# Format rpt/v1 — the map in one YAML file

Complete reference of the file delivered at step 5. A complete and valid example:
`assets/exemple.rpt.yaml`. The same format is used by the organization's referential; a file
that passes `scripts/validate_rpt.py` can be merged into it.

The keys and the enum values below are English and never translated. The texts (names,
missions, inputs, outputs, notes, gaps, sources) are written in the person's language.

## Contents

1. Structure of the file
2. Ids
3. Fields of a role
4. Fields of a process
5. Fields of a task
6. Fields of a tool and of a data source
7. Allowed values
8. Modelling rules the file must follow
9. YAML pitfalls
10. Script messages and fixes
11. Blockers

## 1. Structure of the file

```yaml
format: rpt/v1
meta:
  title: "RPT map of <job or team>"     # in the person's language: « Carte RPT de … »
  organization: "<organization.name of rpt-config.yaml>"
  team: "csm"                          # the code, in lower case
  authors: ["Camille Durand", "Claude"]   # the person mapped (first and last name), then the assistant
  updated: 2026-09-24                  # today's date
  detector: "ts-general-check-process-cartography@2.10"   # the skill and its version (metadata.version)
  sources: ["Claude's memory", "calendar (recurrences, last 3 months)", "answers of 2026-09-24"]
  notes: "Full mode. Sources set aside: messaging (refused)."
tools: [...]      # the tools cited that are not in catalogues/tools.yaml (without it: every tool cited)
data_sources: [...]   # the data sources cited that are not in catalogues/data-sources.yaml (or references/)
roles: [...]
processes: [...]
tasks: [...]
blockers: [...]   # what keeps tasks from reaching their target (§11)
people: [...]     # the person mapped, in their first map only (§12)
agents: [...]     # their recurring agents, in their first map only (§12)
```

`detector` says which version of the skill produced the map: the merge compares what each
version proposes with what the referential keeps (deltas, README_operations.md §4.2).

No other top-level key, no other key in `meta`. `people` and `agents` (§12) are written once, in
the first map of the person. The order of the lists is free; this one is the
order of the referential, which `validate_rpt.py --format` restores.

An update (`SKILL.md`, "Updating a map already sent") keeps the ids of the starting map;
`meta.sources` starts with the name of its file (`"csm-alex-2026-09-24.rpt.yaml"`), and
`meta.notes` with "Update of the map of 2026-09-24" (in the person's language: « Mise à jour de
la carte du 2026-09-24 »). The merge finds the elements already merged through this name and
these ids.

## 2. Ids

| Element | Form | Example |
|---|---|---|
| Role | `<CODE>-R<n>` | `CSM-R2` |
| Process | `<CODE>-P<n>` | `CSM-P3` |
| Task | `<CODE>-T<n>.<m>`, n = number of the role that holds it | `CSM-T2.4` |
| Tool | `<type>:<name>`, lower case, digits, `.`, `_`, `-`, no space or accent | `saas:hubspot`, `skill:compte-rendu-rdv` |
| Data source | `data:<name>`, lower case, digits, `-` | `data:pipe-prospects`, `data:candidatures` |

`<CODE>`: the code of the hat (list in `SKILL.md`, "One map per hat"); capitals and digits,
starts with a letter, no hyphen. A file carries a single code: a person with several hats writes
one file per hat.
One id per element, never the same twice. Numbers follow each other (R1, R2, R3; T1.1, T1.2…); a
gap is not an error.

## 3. Fields of a role

| Field | Required | Content |
|---|---|---|
| `id` | yes | `<CODE>-R<n>` |
| `name` | yes | Verb + object: "Support clients after signature". |
| `team` | yes | The code in lower case, like `meta.team`. |
| `departments` | yes | List of department ids; the first is the main one. |
| `mission` | yes | One sentence: what the role achieves. |
| `holders` | | Who holds the role today: first and last name, or role. One of the three fields where a name is allowed. |
| `fallback` | | The person who decides the cases outside the rules: first and last name, or role (text, or empty). |
| `entries` | | List of `{what, from, trigger, volume}`: what arrives, from where, trigger, volume. |
| `routing` | | List of `{case, to, status}`: incoming case → what handles it (id of a process or a task of the file, or free text for a person) and `status`, the status of what handles it today: for a task, its status; for a process, A if it is `end-to-end` or `once-launched`, otherwise S if at least one of its steps is A or S, otherwise J if its J steps are at least as many as its M steps, otherwise M; for a person, J if they decide, M if they execute; `-` for another role. |
| `gates` | | Human gates: the mandatory validations. |
| `supervision` | | What is measured and who reads it (text, or empty). |
| `criteria` | | The five conditions: `{entry, routing, key_tasks, fallback, supervision}`, each `"yes"` (true for all cases), `"partial"` (true for some cases only) or `"no"`. `routing` is `"yes"` when the list "case → what handles it" is written somewhere others can read it (procedure, Notion page, instructions of an agent); the map in progress does not count. If you do not know, put `"no"` and write the question in `gaps`. |
| `level` | | `"01"` (automated tasks), `"02"` (processes that run once launched), `"03"` (the role runs with its agents). Omit if no task is automated. |
| `verdict` | | One or two sentences: where the automation of the role stands, and why. |
| `gaps` | | List: what is missing or remains to be confirmed, as questions. |
| `basis` | | Where each fact comes from: `{holders: declared, routing: inferred}`, a field of the element and its origin (§7). Also applies to a process, a task and a data source. |
| `notes` | | Free text. |
| `sources` | | List: where this information comes from. |

## 4. Fields of a process

| Field | Required | Content |
|---|---|---|
| `id` | yes | `<CODE>-P<n>` |
| `name` | yes | Verb + object: "Prepare the monthly follow-up meeting". |
| `role` | yes | Id of the role that holds it. |
| `state` | yes | `active` if it runs today; `proposed` if it is desired but does not exist; `retired`, in an update, if it no longer runs. |
| `replaced_by` | | In an update, the id of what replaces a `retired` element. Also applies to a role and a task. |
| `steps` | yes | Task ids, in order; at least two. |
| `trigger` | | `{what, type, volume}`: what launches it, `type` among `auto`, `event`, `schedule`, `manual`, and `volume`, how much enters the process **a month**: `{count, kind, unit}` with `kind` among `document` (an e-mail, an invoice, a letter received) and `event` (a meeting, a signature, a ticket opened), and `unit`, optional, the name of what is counted (`{count: 200, kind: document, unit: e-mails}`). The volume is written on the first process of a chain; it says how much work arrives, and the human time of each task is weighed against it. |
| `gates` | | Who validates what along the way. |
| `exit` | | The exit proof: "minutes sent to the client". |
| `fixed_path` | | `true` if the order never changes, `false` otherwise. |
| `blockers` | | What prevents automating it end to end. |
| `automation` | | See §7. |
| `tools` | | What orchestrates the process (tool ids). |
| `next` | | Ids of the processes that start when this one ends: the order of the chain of production. A process triggered by a task of another one says so in `trigger.by` instead. |
| `handoffs` | | When the process ends with someone else: list of `{to, what, via, issues}`. `to`: who takes over the work, the id of a role or a process of the file, otherwise the role or the team in words ("the CSM team", "support"); `what`: what is passed on; `via`: the tool or the data source it goes through (id); `issues`: what gets lost or delayed at this handoff, without the name of a person, of a client, or an amount. |
| `departments` | | Only if they differ from the role's. |
| `basis`, `notes`, `sources` | | As for a role. |

## 5. Fields of a task

| Field | Required | Content |
|---|---|---|
| `id` | yes | `<CODE>-T<n>.<m>` |
| `name` | yes | Verb + object: "Write the reminder to an inactive admin". |
| `role` | yes | Id of the role that holds it. |
| `state` | yes | `active`, or `proposed` for a desired task that does not exist yet, or `retired`, in an update, for a task that is no longer done. |
| `status` | yes | A, S, C, M or J: what happens **today** (S skilled: the AI runs a skill; C conversational: the AI only talks, in a chat or a bot). |
| `input` | | What it takes. |
| `output` | | What it produces (checkable). |
| `job` | | What the task is for: `{when, so_that}`, read as « When <when>, I want to <name>, so that <so_that>. » `when`: the situation or the trigger that starts it; `so_that`: the result for someone, never the deliverable. Each part without its leading words. |
| `tools` | | Ids of the tools used. |
| `data` | | Ids of the data sources the task reads or writes (§6): `[data:pipe-prospects, data:emails]`. Expected for an M, C or S task; absent for a task that touches no business data. |
| `okrs` | | At most two ids of key results of `catalogues/okrs.yaml` that the deliverable of the task moves directly: `[O1.3.KR1]` (`SKILL.md`, step 3, point 7). Absent for a task without a direct link, that is most of them. With `basis: {okrs: inferred}` or `declared`. |
| `method` | | Where the method of the task is written: the URL of a procedure (Notion page, Drive document) the person can open, or the id of the skill or of the written rule that carries it (`skill:compte-rendu-rdv`). Only a link found in a source or given by the person, never guessed. |
| `by` | | Who does it today: first and last name or role, "Claude", or a tool, by its name as declared ("HubSpot") or its id (`saas:hubspot`). Expected for M and J. |
| `target` | | The status aimed at, when an automation is conceivable. |
| `blocker` | | What is missing to reach `target`, as one text. Still read in an older map; a map writes its blockers in the `blockers` list (§11), and the script warns when a task still writes `blocker`. |
| `output_files`, `templates` | | Where the deliverable goes (a fixed file updated each time, or the folder and the name pattern of the file of each execution) and the template it starts from. Only when a source shows them; do not ask for them: the skill `ts-general-rpt-file` notes them at the end of a task. Form: `README_operations.md` §1.12 of the referential. |
| `blocker_type` | | The type of what is missing (§7), with `blocker`. Same rule as `blocker`: in a map, the `type` of an entry of `blockers`. |
| `build` | | The work to reach `target`: `{size: S, kind: skill}` (§7). When you know how to estimate it; otherwise the merge estimates it. |
| `frequency` | | "every Monday", "10 per week", "for each new client". |
| `measure` | | For an M, C or S task: `{minutes: 20, runs: 8, basis: observed}`, the duration of one execution in minutes, the number of executions per month for one person, and their origin (`observed`: counted in a source; `declared`: given by the person). Numbers without quotes. The gain of the task is computed with them rather than with the ratings. |
| `queue` | | The stock waiting at the input of the task on a date, when a source shows it (a board column, a status, an inbox): `{count: 198, unit: tickets, at: '2026-10-17', basis: observed, source: 'JIRA, statut « Merged in prod »'}`. `count` a number ≥ 0, `at` the date of the count, quoted. A count, not a rate: the explorer divides it by the runs a month of the task to give the days it waits. |
| `stakes` | | For an M, C or S task: what happens when it is done late or badly, `{level: 2, text: "the client waits for their proposal"}` (§7). The sentence describes the consequence, without a client name or an amount. |
| `relevance` | | The relevance: `{reach: 2, frequency: 3, effort: 1, describability: 3, payback: 2}`, each axis rated 1, 2, 3 or `null` (scales in `SKILL.md`, "The model"). Expected for each task, with its five axes; `null` for an axis neither you nor the person can estimate. `relevance.frequency` rates what the text field `frequency` describes. |
| `departments` | | Only if they differ from the role's. |
| `basis`, `notes`, `sources` | | As for a role: `{status: observed, data: inferred, relevance.effort: inferred, frequency: declared}`. |

## 6. Fields of a tool and of a data source

Declare in `tools` of the file each tool cited that is not in `catalogues/tools.yaml`.

```yaml
tools:
  - {id: "saas:hubspot", name: "HubSpot", type: saas, status: external, description: "CRM: deals, contacts, sequences."}
  - {id: "skill:compte-rendu-rdv", name: "Meeting minutes prompt", type: skill, status: live, description: "Prompt saved in a Claude project."}
```

| Field | Required | Content |
|---|---|---|
| `id` | yes | `<type>:<name>`; the prefix is the `type`. |
| `name` | yes | Readable name. |
| `type` | yes | `skill` (skill or saved prompt of an AI assistant), `agent` (configured AI agent), `script`, `bot` (an automaton that reacts to an event: a Zap, a Make scenario, a Slack bot), `saas` (software or service), `reference` (procedure or written rule), `routine` (scheduled task), `ci`, `hook`, `command`. |
| `status` | yes | `external` for software or a service of a vendor; `live` for what the team built and uses; `deprecated`, `removed`. |
| `description` | | One sentence. |
| `shared` | | For a `bot` that people talk to in the team's chat tool and whose AI reads the company's data (a shared assistant): `{channel: slack, audience: all, reaches: os, state: works, checked: '2026-10-20', basis: declared, evidence: …}`. `audience` is `all` or a list of team codes; `reaches: os` when its AI reads the OS; `state` `works`, `not_found` or `unchecked`. The people of its audience count as reaching the OS (README_operations.md §1.18). |

Declare in `data_sources` each data source cited that is not in `catalogues/data-sources.yaml` (without it, `references/data-sources.yaml`),
and declare again, complete, a source of the catalogue when what you observed differs from it
(one more tool, a different AI access). The first tool of the list is the reference tool of the
source: a task that cites the source without citing any of its tools in `tools` counts for it.

```yaml
data_sources:
  - id: data:candidatures
    name: Candidatures
    description: Offres publiées, candidatures reçues et leur avancement.
    sensitivity: [personal, hr]
    tools:
      - tool: saas:welcome-to-the-jungle
        where: offres et candidatures
        connector: none
      - tool: saas:gmail
        where: candidatures spontanées reçues par e-mail
        connector: native
    basis: {sensitivity: declared}
    sources: [réponses du 2026-09-24]
```

(The texts of this example are in French, the language of the person mapped in
`assets/exemple.rpt.yaml`.)

| Field | Required | Content |
|---|---|---|
| `id` | yes | `data:<name>`. |
| `name` | yes | The type of business data, in a few words: "Pipeline and prospects", "Applications". |
| `description` | | One sentence: what this data contains. |
| `sensitivity` | | What this data contains, among the categories of §7: `[personal, client]`; `[]` for internal working data only. The AI policy rule of each category is in `catalogues/ai-policy.yaml`. |
| `tools` | | The tools where this data is found, the reference tool first; for each, `tool` (tool id, declared or present in `catalogues/tools.yaml`), `where` (where in the tool: "client records"), `connector` (how the AI reaches it, §7) and `notes`. |
| `basis`, `notes`, `sources` | | As for a role. |

## 7. Allowed values

| Field | Values |
|---|---|
| `status`, `target` | `A`, `S`, `C`, `M`, `J` |
| `routing.status` | `A`, `S`, `C`, `M`, `J`, `-` (the case goes to another role) |
| `trigger.type`, `entries.trigger` | `event` (something arrives from outside: form filled, e-mail received, status changed); `auto` (a tool launches the work by itself, without an outside event: a rule that detects, an agent that watches); `schedule` (a date, a recurrence); `manual` (a person launches, including at a date they must remember) |
| `state` | `active`, `proposed`; `retired` for an element of a starting map that is no longer done (update) |
| `automation` | `end-to-end` (runs alone, trigger included); `once-launched` (automated once launched by hand); `one-change-away` (a single change would be enough: a trigger, a written rule); `assisted` (some steps need a human by nature); `manual` (a human does most of it); `routing` (the next step depends on the case: it is a routing, not a process). The choice follows the rule written under this table. |
| `criteria.*` | `"yes"`, `"partial"`, `"no"` |
| `level` | `"01"`, `"02"`, `"03"` |
| `relevance.reach`, `relevance.frequency`, `relevance.effort`, `relevance.describability`, `relevance.payback` | `1`, `2`, `3` or `null`, without quotes |
| `measure.minutes`, `measure.runs` | a number above 0, without quotes |
| `measure.basis` | `observed` (counted in a source: calendar, tickets, inbox, launches of a skill); `declared` (given by the person) |
| `queue.count`, `queue.at` | a number ≥ 0; a date `'YYYY-MM-DD'`, quoted |
| `stakes.level` | `1` (internal nuisance, caught up without visible cost); `2` (visible cost: someone waits, work is redone); `3` (loss: a client, revenue, a compliance risk); or `null` |
| `blocker_type` | `connector` (the AI does not reach the data); `method` (the method is not written); `tool` (a skill, an agent or a script to build); `decision` (someone must decide or validate); `data` (data missing or of poor quality); `licence`; `other` |
| `blockers.type` | the values of `blocker_type`, and `access` (a person or the AI lacks a right), `security` (a security or compliance rule), `budget`, `organization` (nobody in charge, priorities), `provider` (a vendor or a provider does not deliver) |
| `blockers.state` | `open` (nothing moves); `in_progress` (someone works on it); `resolved` (lifted); `dropped` (given up) |
| `blockers.source` | `map` (said during the mapping); `slack`; `email`; `ticket`; `meeting`; `other`. (`observation` and `merge` are written by the referential, not by a map.) |
| `blockers.basis` | one value: `observed`, `declared` or `inferred` (below) |
| `blockers.opened`, `blockers.resolved` | a date `YYYY-MM-DD`, between quotes in the example (`'2026-10-08'`) |
| `build.size` | `S` (less than a day); `M` (a few days); `L` (more than a week) |
| `build.kind` | `prompt` (a saved prompt); `skill`; `agent` (does it alone); `workflow` (Zapier, Make, n8n); `script`; `feature` (a feature to develop); `connector` (a connector to activate or configure) |
| `data_sources.tools.connector` | `native` (connector of Claude's directory, enabled for the organization: native MCP); `mcp` (MCP server the company added, custom connector); `api` (a skill or a script calls the tool's API); `export` (someone exports or copies the data for the AI); `none` (the AI has no access to it); `null` (to be specified) |
| `departments` | the 14 ids of `catalogues/departments.yaml` (without it, `references/departments.yaml`) |
| `sensitivity` | `public` (already published or meant to be); `personal` (what identifies a person: name, e-mail, phone, behaviour); `client` (data and documents of a client); `hr` (headcount, arrivals and departures, organization, positions); `internal_confidential` (non-public finances, strategy, intellectual property, code included); `regulated` (sensitive personal data: health, opinions, biometrics; individual files and named salaries; trade secrets; regulatory or contractual obligation); `credentials` (logins, passwords, API keys); `[]` for internal data only |
| `basis.*` | `observed` (found in an authorized source: calendar, tool, inbox, repository); `declared` (said by the person); `inferred` (deduced by you, without the person having confirmed it) |

**Choosing `automation`.** A process whose next step depends on the case takes `routing` (§8,
rule 3), whatever the statuses of its steps. For the others, the value is read from these
statuses: the first rule that applies gives it. The launch task (a short action that triggers
what follows, not real work: §8, rule 4) counts in none of them.

1. All steps are A, and the trigger is not `manual` → `end-to-end`.
2. All steps are A, and the trigger is `manual`, with or without a launch task →
   `once-launched`.
3. A single step prevents one of the two, and its `blocker` is written → `one-change-away`.
4. The M steps outnumber the A steps, and are at least as many as the S, C and J steps
   together → `manual`.
5. In all other cases → `assisted`.

Rule 4 counts the A steps: when they are at least as many as the M steps, a human does not do
most of the work. A sequence that sends each e-mail on its own (A), and whose replies a person
reads (M, without `blocker`), is `assisted`, not `manual`. The script warns when `end-to-end` or
`once-launched` does not match the statuses, and when `manual` is declared while the rule gives
another value. The referential applies the same rule.

## 8. Modelling rules the file must follow

1. A process step is a task of the file, cited by its id.
2. A task belongs to a single role (`role`). It can be the step of several processes, or of
   none.
3. A process has a trigger, at least two steps and an exit proof. A "process" of a single task
   is a task. If the next step depends on the case, write it anyway with `automation: routing`
   and `fixed_path: false`.
4. When the launch is a separate action (opening a tool to launch a skill, triggering a check),
   it is a task (M), first step. When it merges with the first task (the person starts writing
   with the AI themselves), no launch task: `trigger.type: manual` is enough. A process
   triggered by an event or a date has no launch task.
5. An `active` process chains only `active` tasks. A `proposed` process can reuse active tasks
   and add proposed ones.
6. A `proposed` task carries in `status` what is done today (often M or J) and in `target` what
   is aimed at.
7. Each element cites its `sources`. What is not proven goes into `gaps` or `notes`, as a
   question.
8. A first name or a name appears only in `holders`, `by`, `fallback` and `meta.authors`, for a
   person of the organization who holds the role, does the task or acts as a fallback;
   everywhere else, write their role. Never a client or a third party. No other personal data
   (address, phone, e-mail, age, gender, health, pay, absence), and nothing confidential for the
   company (internal reviews, HR discussions, cash, fundraising): `SKILL.md`, Privacy section.

## 9. YAML pitfalls

- **In a list between brackets `[…]` or between braces `{…}`, put between double quotes any
  text that is not a single word or an id.** Reasons:
  - a comma cuts the value: `{what: "Quote request", from: form, e-mail}` creates an unknown
    field `e-mail` (the script flags it as an "unknown field");
  - the space French puts before "?" and ":" breaks the reading of the file:
    `gaps: [Qui valide quand le manager est absent ?]` gives "unreadable YAML". Write
    `gaps: ["Qui valide quand le manager est absent ?"]`;
  - between brackets, ":" breaks nothing but changes the meaning: `[Sources set aside: messaging]`
    becomes a key-value pair; the script flags it ("which is not a text").
- `"yes"`, `"no"`, `"01"`, `"02"`, `"03"` are written between quotes (otherwise YAML reads a
  boolean or the number 1).
- A text that contains `: ` (colon followed by a space), starts with `[`, `{`, `*`, `&`, `!`,
  `%`, `@` or `` ` ``, or contains ` #`, goes between double quotes.
- An apostrophe inside double quotes is not a problem: `"l'équipe"`. A double quote inside is
  written `\"`.
- `fixed_path` is written `true` or `false`, without quotes.
- `validate_rpt.py --format` then rewrites the quotes its own way (single, and only where they
  are needed): it has no effect on the content.
- A date is written `2026-09-24`.
- Indentation: two spaces, never a tab.

## 10. Script messages and fixes

The script prints its messages in the organization's language (`--lang` to choose another); they
are quoted here in English, the same message in every language. An error line starts with
`ERROR`, a warning line with `warning`.

| Message | Cause | Fix |
|---|---|---|
| `unreadable YAML (…)` | The file cannot be read: unprotected text between brackets or braces ("?", ":", comma), indentation, tab. The message gives the line and the column. | Double quotes around the text (§9), two-space indentation. |
| `` unknown field `x` (unquoted comma in a list between braces?) `` | An unprotected comma between braces, or a misspelled field name. | Quotes around the text, or a field name of §3 to §6. |
| `` `x` contains {…}, which is not a text `` | An unprotected ":" in a list between brackets made a text into a key-value pair. | Double quotes around the text (§9). |
| `` required field `x` missing `` | A required field is missing. | Add it. |
| `malformed … id` | Code in lower case, with a hyphen, or form `T1-2`. | Form of §2. |
| `id already used in …` | Two elements have the same id. | Renumber one of them. |
| `` `x` points to X, which is not in the referential `` | `role`, `steps` or `routing.to` cites an id that does not exist. | Create the element, or correct the id; for a person, write free text ("the sales management"). |
| `` unknown tool `x` `` | The tool is declared neither in the file nor in `catalogues/tools.yaml`. | Declare it in `tools` (§6). |
| `` `data` points to data:x, which is not in the referential `` | The data source is declared neither in `data_sources` nor in `catalogues/data-sources.yaml` (or `references/data-sources.yaml`). | Declare it in `data_sources` (§6), or take the id of the catalogue. |
| `` `tools.connector (saas:x)` = …, expected […] `` | An AI access outside the list. | A value of §7, `null` if you do not know. |
| `` tool `x` cited twice `` | The same tool appears twice in a data source. | One line per tool; join the two `where`. |
| `` warning … M, C or S task(s) without `data` `` | A manual, conversational or skilled task does not say which data it reads or writes. | Write its data sources (`SKILL.md`, step 3, point 6). |
| `` unknown KR `O…KRn` (okrs.yaml) `` | `okrs` cites a key result absent from `catalogues/okrs.yaml`. | Take the id of a KR of the file, or remove the link. |
| `` `okrs` = …, expected a KR id (`O1.2.KR1`) `` | `okrs` cites an objective (`O1.3`) or a text. | The id of a KR: `O1.3.KR1`. |
| `` warning … N KRs in `okrs`: is the link direct? `` | A task names more than two KRs. | Keep the two whose measure moves directly with the deliverable (`SKILL.md`, step 3, point 7). |
| `` unknown department `x` `` | A department outside the list. | One of the 14 ids; the original word in `notes`. |
| `` `x` = …, expected […] `` | A value outside the list. | A value of §7. |
| `active process, step X not active` | An `active` process cites a `proposed` task. | Set the process to `proposed`, or the task to `active` if it is practised. |
| `warning … 1 step(s) — a process has at least two tasks` | A process of a single task. | Make it a task, or find the missing step. |
| `` warning … M task without `by` (who does it?) `` | Nobody knows who does it. | Ask the person. |
| `` `relevance.reach` = 4, expected 1, 2, 3 or null `` | A rating outside the scale, between quotes (`"2"`) or written `yes`. | A rating from 1 to 3 without quotes, or `null`. |
| `` `relevance.simplicity` no longer exists: … `` | A map rated before 2026-09-30: describability replaced simplicity, and it measures something else. | Remove `simplicity` and rate `describability` (`SKILL.md`, "The model"); do not carry over the simplicity rating. |
| `` warning … task(s) without a complete `relevance` `` | The relevance is not written, or one of the five axes is missing (a map rated before `payback` was added on 2026-09-29, or before `describability` replaced `simplicity` on 2026-09-30). | Rate the axes that can be estimated, ask the person for the others; `null` only if they do not know. |
| `` `measure.minutes` = 0, expected a number above 0 `` | A measure that is zero, negative or between quotes (`"20"`). | The number, without quotes; remove `measure` if nobody knows it. |
| `` warning … `measure.minutes` = 10 gives an effort of 1, `relevance.effort` is 3: correct the effort rating `` | The measured duration and the effort rating do not say the same thing. | The measure decides: correct the effort rating (up to 30 min: 1; up to 2 h: 2; beyond: 3). |
| `` warning … M, C or S task(s) without `measure` `` or `` without `stakes` `` | The minutes, the number of times per month or the stakes of a manual or assisted task are not written. | Ask the person for them in a single table (`SKILL.md`, step 4). |
| `` `sensitivity` = …, expected a list among […], or [] for internal data `` | The sensitivity of a source is not a list, or a category is outside the list. | `[personal, client]`, categories of §7; `[]` for internal data only. |
| `` warning … sensitivity not stated `` | A source declared in the file does not say what it contains. | Write `sensitivity` from the type of data, never by reading its content, and have it confirmed at step 4. |
| `` `basis` cites `x`, which is not a field to source `` | A key of `basis` is not a field of the element (or `relevance.<axis>`, `measure.<field>`…). | The name of the field: `status`, `data`, `frequency`, `relevance.effort`… |
| `` a handoff (`handoffs`) has no `to` `` (or `what`) | A handoff without a recipient or without what is passed on. | Write who takes over the work (`to`) and what is passed on (`what`). |
| `` `handoffs.via` = … is not an id `` | `via` is written as text. | The id of a tool or of a data source (`saas:hubspot`, `data:emails`), or remove `via`. |
| `` `method` = …, expected a URL (https://…) or the id of a tool of the catalogue `` | The link of the method is a document name or a path. | The full URL the person can open, or the id of the skill or of the written rule; otherwise remove `method`. |
| `warning N element(s) of the starting map missing from this one…` (with `--since`) | An update lost an element of the starting map, or renumbered it. | Put it back with its id; `state: retired` if it no longer exists. |
| `warning … end-to-end, but…`, `once-launched, but…` or `manual, but…` | The declared automation does not follow the statuses of the steps: `end-to-end` or `once-launched` while a step is not A; `manual` while the rule gives another value, most often because the A steps are at least as many as the M steps. | Choose `automation` according to the rule of §7. |
| `` warning codes X in the map `y`… `` | An id carries another code than that of `meta.team`: two hats in the same file. | File the element in the file of its hat, or correct its code (`SKILL.md`, "One map per hat"). |
| `` `tasks` must list the ids of the tasks the blocker holds back `` | A blocker without `tasks`, or `tasks` written as a text. | `tasks: [CSM-T2.4, CSM-T2.5]`, ids of tasks of the file. |
| `` `tasks` points to X, which is not in the referential `` (on a blocker) | A blocker cites a task that is not in the file (another hat, a typo, a task of the register). | The id of a task of the file; a task of another hat goes in the blocker of that map. |
| `` a blocker in state `resolved` gives the date it was closed (`resolved`) `` | `state: resolved` or `dropped` without the date. | `resolved: '2026-10-08'`, and `resolution`. |
| `` `resolved` is only written once the blocker is resolved or dropped `` | A date of resolution on an open blocker. | Remove `resolved`, or change `state`. |
| `` `resolved` comes before `opened` `` | The two dates are swapped. | Correct them. |
| `` `evidence` too long `` | More than 300 characters: a content, not a trace. | Where and when only: "Slack #csm, 2026-10-08". |
| `warning … same problem as BLK-n…` | Two entries say the same problem. | One entry, with all its tasks in `tasks`. |
| `` warning … closed without `resolution` `` | A resolved or dropped blocker does not say how. | Write what lifted it, or why it was dropped. |
| `warning … still open while all its tasks are automated or retired` | The tasks moved, the blocker did not. | Ask the person: `resolved` with its date, or correct the status of the task. |
| `` warning … inferred blocker without `source` `` | A blocker deduced from a source does not say which one. | `source: slack`, `email`, `ticket` or `meeting`. |
| `` warning … blocker found in a source (…) without `evidence` `` | Nothing says where and when it was seen. | `evidence: 'Slack #channel, 2026-10-08'`, `'ticket DP-6301'`; never the message. |
| `` warning … task(s) still write their own `blocker` `` | The map writes what is missing on the task. | Move each problem to `blockers` (§11), one entry per problem, and remove `blocker` and `blocker_type` from the task. |
| `warning data: …` | A text looks like personal or confidential data: e-mail, phone, address, amount, a word about health, HR or finances (French and English words), a common first name or the name of a holder written outside `holders`, `by`, `fallback` and `meta.authors`. The check does not see a family name alone, a rare first name, or a private subject described without a keyword. | Remove the data or write the role; if it is an activity that reveals nothing, tell the person at step 7. |

## 11. Blockers

A blocker is a problem that keeps one or several tasks from moving towards their `target` (an
access missing, a method not written, a decision awaited), with the state of its resolution.
The map writes each one once, in the `blockers` list, after `tasks`; the merge adds it to the
organization's register (`blockers.yaml`) without duplicates. `SKILL.md`, section "Blockers",
says where to find them and how to have them confirmed.

```yaml
blockers:
  - id: BLK-1
    text: "No admin access to the recruiting software to set the automatic replies"
    type: access
    state: open
    tasks: [RH-T1.3, RH-T1.8]
    opened: '2026-09-18'
    source: slack
    basis: inferred
    evidence: 'Slack #recruiting, 2026-09-18'
    notes: "Confirmed by the person on 2026-09-24."
    sources: ["Slack (recruiting channel, last 3 months)"]
  - id: BLK-2
    text: "Applications from the careers site did not reach the recruiting software"
    type: connector
    state: resolved
    tasks: [RH-T1.9]
    opened: '2026-08-20'
    resolved: '2026-09-15'
    resolution: "Careers site form connected to the recruiting software."
    source: map
    basis: declared
```

(`assets/exemple.rpt.yaml` carries the same entries in French, with six others.)

| Field | Required | Content |
|---|---|---|
| `id` | yes | `BLK-<n>`, local to the map: `BLK-1`, `BLK-2`… The merge gives each new blocker the next free number of the register; never reuse an id within the map. |
| `text` | yes | The problem, in one sentence, in the person's language. The work problem, never the content of a message, never the name of a colleague, a client or a provider. |
| `type` | yes | Its nature (§7, `blockers.type`). |
| `state` | yes | Where its resolution stands (§7, `blockers.state`). |
| `tasks` | yes | The ids of the tasks it holds back, all tasks of the file. The same problem on several tasks is one entry. |
| `opened` | yes | The date it was first seen: the date of the message, of the ticket, of the meeting or, failing that, of the interview. |
| `resolved` | if `resolved` or `dropped` | The date it was lifted or dropped. Required for these two states, forbidden for the others. |
| `resolution` | | What lifted it ("connector enabled", "criteria written") or why it was dropped. Expected when `resolved` is written. |
| `owner` | | The id of the role of the file that can lift it. A person or a team outside the map goes in `notes`, as a role. |
| `source` | | Where it was found (§7, `blockers.source`). |
| `basis` | | How the problem is known: `inferred` when you deduced it from a source (a Slack message, an e-mail, a ticket, a meeting note) and the person confirmed it; `declared` when the person raised it. `observed` is accepted, for a blocker a tool reports by itself; a map writes `inferred` or `declared`. One value, not a mapping. |
| `evidence` | | Where and when it was seen, 300 characters at most, without personal content: "Slack #csm, 2026-10-08", "ticket DP-6301", "e-mail, 2026-09-30", "team meeting of 2026-10-02". Expected for a blocker whose `source` is `slack`, `email`, `ticket` or `meeting`, or whose `basis` is `inferred`. |
| `notes`, `sources` | | As for a role. An update writes in `sources` the id of an entry of the register it takes over (`"blockers.yaml BLK-12"`): the merge updates that entry. |

Rules:

1. One problem, one entry; one entry can list several tasks. Two problems on one task are two
   entries.
2. `resolved` is written if and only if `state` is `resolved` or `dropped`; it does not come
   before `opened`.
3. A blocker is never deleted from a map: a lifted blocker becomes `resolved`, a blocker given up
   `dropped`, each with its date and its `resolution`. It says why a task changed status.
4. An inferred blocker goes into the map only after the person confirms it (`SKILL.md`,
   section "Blockers"); a rejected one leaves no trace.
5. `text`, `evidence`, `resolution` and `notes` follow the privacy rules (§8, rule 8): the scripts
   check them like every other text.
6. A task of an older map may still write `blocker` and `blocker_type`: the file stays valid,
   the script warns, and an update moves them to this list.

## 12. Access to the OS and recurring agents

Two lists, written once, at the top level of the person's first map (`people`, `agents`). The
merge adds them to the organization's `people.yaml` and `agents.yaml`.

`people`, one entry: the person who is mapped.

| Field | Required | Content |
|---|---|---|
| `id` | yes | `person:<first name>`, lower case, without accents: `person:helene`; `-2` when a person with the same first name already has the id. |
| `name` | yes | The first and last name (two people can share a first name). Never an e-mail or a phone number. |
| `aliases` | | Other ways the name is written in the maps (`Houlé`). |
| `os_access` | | One entry per way the person's AI reaches the OS: `mode` (`connector`, `local`, `repository`, `none`), `tool` (the tool id: `saas:google-drive`), `state` (`works`, `not_found`, `unchecked`; required unless `mode: none`), `checked` (the date the AI read the folder), `basis`, `evidence` (300 characters at most), `notes`. |
| `ai_plan` | | The AI licence the person uses for work: `tool` (the tool id: `saas:claude`), `plan` (as the vendor names it: Pro, Max, Team, Enterprise), `tier` (`free`, `standard`, `premium`), `modes` (a list among `thinking`: the AI reasons before it answers, and `work`: it works on files and tools, as in Cowork, Claude Code, artifacts, generation of assets), `checked`, `basis`, `evidence`, `notes`. |
| `notes`, `sources` | | As for a role. |

`agents`, one entry per recurring agent the person set up or keeps.

| Field | Required | Content |
|---|---|---|
| `id` | yes | `ag:<slug>`, local to the map. |
| `name` | yes | What it does, in one line. |
| `kind` | yes | `scheduled-task` (a scheduled task of their Claude), `routine` (a Claude Code Routine), `managed-agent` (Claude Managed Agents), `worker` (a pipeline that processes what arrives in a folder). |
| `state` | yes | `live`, `construction`, `paused`, `retired`. |
| `platform` | | The tool id where it runs (`saas:claude`, `saas:claude-routines`, `saas:claude-managed-agents`). |
| `schedule` | | When it runs, in words: "every Monday", "every 2 hours". |
| `owner` | | The id of the role it works for. |
| `people` | | The `person:` ids of who set it up or keeps it. |
| `tasks` | | The ids of the tasks of the map it does. |
| `skills` | | The ids of the skills, routines and scripts it runs (tool ids). |
| `data` | | The data sources it reads. |
| `stage` | | The stage it reached: `{level, checked, basis, evidence}`, `level` among `functional` (it does the work: running, tasks of the referential, last three runs without repair), `efficient` (measured cost, versioned configuration, run journal) and `refined` (Slack message, mail recap, failure alert). A stage needs the ones before it; `evidence` says what proves it. Omit when not yet functional. |
| `config`, `log` | | Where its configuration is versioned and where its runs are journaled: a path in the organization's repository or an https:// link. |
| `notify` | | Who it tells: a list of `{channel, to, when}`, `channel` `slack` or `email`, `to` a channel or a `person:` id, `when` `run`, `result`, `failure`, `daily`, `weekly` or `monthly`. |
| `basis`, `notes`, `sources` | | As for a role. Never the prompt of the task, nor what it produced. |

