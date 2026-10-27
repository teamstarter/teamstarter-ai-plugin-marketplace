---
name: ts-general-data-crawl
description: "Describe where an organization's data is kept and how it is laid out, tool by tool (Google Drive, Notion, HubSpot, Slack, Gmail, Linear, Jira), from the connectors of the person who runs it: the folders, files, sheets, databases, CRM objects and pipelines, channels, labels and projects, nested as in the tool, with their size, the date of their last change and their column names. Never reads or sends a value of the data: no document content, no message, no record, no client name, no amount. Shows a preview of what will be sent, then, after the person's approval, drops the data map (rpt/v1 file with containers) in the organization's intake folder, where it is merged into the data tree of the RPT referential. Use when someone wants to know or map where the company's data is, which tool holds what, or whether it is up to date. Triggers: 'map our data', 'where is our data', 'crawl my Drive structure', « cartographie nos données », « où est notre donnée », « fais la carte des données »."
metadata:
  version: "1.3 (2026-10-26)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-data-crawl; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Map where the data is

Speak and write to the person in their language; this file is in English. The content of the
file (names of places, what they hold, notes) is written in the person's language; the keys and
the enum values stay as in the format (`references/format-datamap-v1.md`).

The organization keeps a referential of its roles, processes and tasks (RPT), and, next to it, a
**data map**: for each type of data (client accounts, offers and quotes, tickets…), the tools
where it is, and in each tool the places that hold it (a Drive folder, a sheet, a Notion
database, a HubSpot object, a Slack channel, a Gmail label, a Linear team, a Jira project). The
data map answers questions such as "Where are the client quotes, and who creates and updates
them?": the place comes from this skill; who keeps it comes from the referential (the roles of
the tasks that write it), at the merge.

This skill describes the places of the tools the person reaches with their connectors. It reads
**metadata only**: names of folders and files, kinds, counts, dates of last change, column or
property names. It never opens a document, a message or a record, and never sends a value.
It writes one file in the rpt/v1 format, checks it with a script, shows the person a preview of
everything that will be sent, then, after their approval, drops it in the organization's intake
folder. The person who maintains the referential merges it (skill `ts-general-data-merge`).

Count 15 to 30 minutes, depending on the number of tools.

## The organization's configuration

The skill carries no data of any organization. The organization's instructions (the global
context Claude receives in every conversation) give the address of its configuration, on a line
such as `Config RPT (rpt-config.yaml) : <link>`. Read it before your first message:

1. **The configuration.** A `drive.google.com` link: with the Google Drive connector, the file
   whose id is in the link, or, for a folder link, the file named `rpt-config.yaml` in that
   folder. A `github.com` link: with the GitHub connector, or in Claude Code the file of a clone.
   Otherwise, fetch the link (a public file only). Without an address, search Drive for a file
   named `rpt-config.yaml` and have the person confirm it is their organization's. If none
   works, ask the person to add the file to the conversation. Never guess a value. Save it as
   `rpt-config.yaml` in your working folder.
2. **The catalogues.** `catalogues` of the configuration names the catalogue files; this skill
   uses the tool catalogue (`tools`) and the data sources (`data_sources`) when it names them,
   relative to the referential (`referential.repository_path` in
   `referential.repository`, or the Drive folder `referential.drive_folder`). Read them by the
   same means and save them in the folder `catalogues/` of your working folder. A catalogue you
   cannot read is missing, which is normal for an organization that has no referential yet: the
   common data types of `references/data-sources.yaml` take its place, and the file declares the
   tools it describes. Say nothing to the person about a missing catalogue.
3. Pass both to the script: `--config rpt-config.yaml --catalogues catalogues`.

In this text, "the intake folder" is `intake.drive_folder` (Drive id `intake.drive_folder_id`),
"the intake address" is `intake.email`, `intake.merged_by` is who merges, and `privacy` lists
what is never sent, in addition to the rules below.

## What is never read, never written

The data map describes the **container**, never the **content**. This rule has no exception, and
the person's approval does not lift it.

- **Never open** a document, a page body, a message, an e-mail, a record of a CRM or a ticket.
  The only reading allowed beyond metadata: the **first row** of a spreadsheet (its column
  names), and the **schema** of a database or a CRM object (its property names), when the person
  allowed it at step 1. A tool that can only return a whole file is not used for that: leave
  `fields` empty.
- **Never write a value**: no client, prospect or partner name, no person's name, no amount, no
  e-mail address, no phone number, no title of a deal, a ticket or a message, no subject of an
  e-mail. A folder named after a client becomes a placeholder: `Clients/[Client]/`, with
  `items.count` the number of such folders. A channel `#client-acme` becomes `#client-[client]`.
  A file name with a date becomes a pattern: `Proposition [Client] [YYYY-MM-DD].pdf`
  (`[AAAA-MM-JJ]` in French).
- **Never a person**: not in a path (`Drive de [First name]`), not as an editor. Activity is a
  count (`activity.editors_90d: 4`), never a list of names.
- **Placeholders** for whatever varies or identifies: `[Client]`, `[Projet]`, `[Numéro]` (a file
  or project number such as `2024-017`), `[Ville]`, `[Fournisseur]`, `[Prénom]`, `[AAAA-MM-JJ]`
  (in English `[Client]`, `[Project]`, `[Number]`, `[Town]`, `[Supplier]`, `[First name]`,
  `[YYYY-MM-DD]`). `Projets/2024-017 Dupont Maison Arcachon/` becomes
  `Projets/[Numéro] [Client] [Ville]/`.
- **Private and confidential places are left out entirely**: a person's private folder, HR
  folders and channels (recruitment, reviews, payroll, health), the board's and the
  shareholders' spaces, and the subjects of `privacy` in the configuration. Do not describe them,
  not even as a placeholder, and do not name them anywhere in the file: `meta.notes` says only
  "3 places left out (private or confidential)". The summary, which is not sent, says which ones
  and why. The `items.count` of the folder that holds them counts what the person sees in it, as
  the tool gives it, without naming them.
- Places that hold no business data (a personal "Untitled" folder, a test channel, a social
  channel) are not described.

The script refuses e-mail addresses, phone numbers and amounts in every text field of the file
(meta, declared tools and data types, containers), and warns on first names, postal addresses,
file numbers, amounts before HT or TTC and words of private subjects. It does not see a client's,
a family's, a town's or a supplier's name: you do, by replacing it with a placeholder before
writing. The preview shows the whole file, so that the person can see what the script cannot.

## Asking a question

Every question that waits for an answer goes through the question tool (`AskUserQuestion` in
Claude Code and Cowork; in claude.ai, the answer input tool): at most four questions per call,
closed answers, the recommended answer first with "(Recommended)" in the person's language. A
question written at the end of a message reads as a polite formula. Without a question tool,
end the message with the question alone on its last line, in bold.

## Step 1 — Frame

Look at the connectors available in your tools among Google Drive, Notion, HubSpot, Slack, Gmail,
Linear and Jira (Atlassian). Then, in a single call:

1. "Which tools shall I describe?" (several answers): the connected tools, each named. A tool
   without a connector is not offered; say in the message which ones are missing.
2. "How far in Drive?" (only with Google Drive): "Shared drives and folders shared with the team
   (Recommended)", "Also my own My Drive folders".
3. "May I read the column names of the spreadsheets and the properties of the databases (first
   row and schema only, never the content)?": "Yes (Recommended)", "No".
4. "Is there a place I must leave out?": "No (Recommended)"; the person writes the place
   otherwise.

Say what you will read before reading it: "I will list the folders and files of <tools>, with
their size and the date of their last change, without opening any of them."

**One place only.** When the skill `ts-general-os-place` sends you to describe the folder where
a content was just stored, skip the questions: describe that folder alone, and its parent when
the data map does not have it either (one or two containers, with `parent` set to the id of the
data map's container when it has one). Count five minutes. Steps 3 to 5 do not change.

## Step 2 — Describe each tool

For each tool chosen, follow its procedure. Write each container as you go, in the form of
`references/format-datamap-v1.md`; give it the type of data it holds (`data`, an id of
`catalogues/data-sources.yaml`, else of `references/data-sources.yaml`; a type that is in
neither is declared in `data_sources` of the file, with its name, description and sensitivity).
A container that holds several types of data takes the main one and says the others in `holds`.

Keep the map readable: **30 to 80 containers per tool at most**. Describe the levels that hold
business data, aggregate the repeated ones (one placeholder container for the 46 client
folders), and stop at the level below which every folder looks the same. For each container,
take what the tool gives without opening anything:

- `items`: the number of files, pages, records, channels or threads (`approx: true` when the
  tool gives an estimate or a page of results);
- `freshness.last_modified`: the date of the most recent change among its items, and
  `freshness.modified_90d`: how many changed in the last 90 days, when the tool gives dates;
  `freshness.checked`: today;
- `activity.editors_90d` / `viewers_90d`: counts only, when the tool gives them;
- `url`: the link of the container (folder, database, object list), never of an item;
- `access`: the connector used and whether it worked (`works`).

**Google Drive.** List the shared drives (or the folders shared with the team), then their
folders, level by level, with the search and metadata tools of the connector (name, kind,
modification date of the files, number of children). Never read a file's content. A folder
whose children are named after clients, people or dates becomes one placeholder container.
For a spreadsheet, with the person's approval, read only the first row (column names) when the
tool can read a range; otherwise leave `fields` empty. Kinds: `folder`, `spreadsheet`,
`document`, `presentation`, `file`.

**Notion.** Search the teamspaces and their top pages; for each database, fetch its schema
(property names and types) without querying its rows, and take the number of pages when the
tool gives it. Kinds: `page`, `database`, `view`.

**HubSpot.** For each object (contacts, companies, deals, quotes, tickets, custom objects): its
number of records (the total of a search with one result), the date of the most recent change
(a search sorted by last modification, one result, keeping only its date), and, with the
person's approval, its property names (only the ones the team created or fills, at most 20).
For each pipeline: its stages as `fields`, and the number of open deals. Kinds: `object`,
`pipeline`, `list`.

**Slack.** List the public channels (and the private ones the person is a member of, only with
their approval), with the date of their last activity when the channel list gives it; never
read a message to get a date (leave `freshness` empty instead). The number of members goes in
`notes` ("12 membres"): members are not editors. Group the channels that follow a pattern
(`#client-[client]`, `#proj-[project]`) into one container whose `items.count` is the number of
channels. Kind: `channel`; type of data: the internal messages (`data:messages-internes`), what
they are about in `holds`.

**Gmail.** List the labels the person created (not the system labels), with their number of
threads and the date of the most recent one, taken from the counts and dates of a search on the
label, without opening a message and without writing a subject or a sender. Kind: `label`; type
of data: the e-mails (`data:emails`), what they are about in `holds` ("the returns of signed
quotes"). A personal mailbox is described only through its labels, and only those that hold
business data.

**Jira.** For each project: its key, its issue types (`fields`), its statuses (in `notes`), its
number of issues (the total of a JQL search with one result) and the date of the last update
(a search sorted by `updated`, one result, keeping only its date). Kinds: `project`, `board`.

**Linear.** For each team: its key (in `path`), its statuses with their type (`triage`,
`backlog`, `unstarted`, `started`, `completed`, `canceled`) in `notes`, its label groups and
labels as `fields` (names only), whether it runs cycles (in `notes`), its number of issues (the
issues listed with the largest page the tool allows; `approx: true` when there is a next page)
and the date of the last update (a list sorted by update, one result, keeping only its date).
Kind: `project`, as a Jira project: a Linear team holds the issues, their key and their
statuses. For each project of the team that is not canceled or completed: its name, its status,
its number of issues and the date of its last update; kind `project`, `parent` = the team.
A saved view is a `view`. Never write the title or the description of an issue.
An organization may run Jira and Linear side by side, or keep Jira as a read-only history after
moving to Linear: describe both, and say in `notes` which one is the history.

When a tool refuses (rights, timeout), write the containers you could describe, and say in the
summary which ones are missing and why.

## Step 3 — Write and check the file

1. Read `references/format-datamap-v1.md` and start from the structure of
   `assets/exemple.datamap.yaml`.
2. Tools: reuse the ids of `catalogues/tools.yaml` (`saas:google-drive`, `saas:hubspot`…).
   Without that catalogue, declare in `tools` every tool you describe, with an id `saas:<name>`,
   as in the example.
3. Leave `written_by`, `read_by` and `owner` empty: the merge links the places to the tasks and
   roles of the referential. What you learned about who uses a place goes in `notes` as a role,
   never as a person ("the sales team fills it").
4. Name the file `datamap-<first name in lower case without accents>-<YYYY-MM-DD>.yaml`, with
   `meta.authors` = the person (first and last name) then Claude, `meta.detector` =
   `ts-general-data-crawl@` followed by the number of `metadata.version` of this skill, and
   `meta.sources` = the tools read with their scope. Write it where your environment puts the
   files to deliver (in claude.ai: `/mnt/user-data/outputs/`).
5. Check it:

   ```bash
   python3 <skill folder>/scripts/check_datamap.py <file> --config rpt-config.yaml --catalogues catalogues
   ```

   The script prints its messages in the organization's language (`--lang` to choose). Fix every
   error and run it again until 0 errors. Handle each warning: replace a name or a number with a
   placeholder, leave out a place that turns out to be private, or keep a word that is the
   ordinary vocabulary of the trade (a « commission de sécurité ») and say so in the summary. If PyYAML is
   missing, run `pip install pyyaml`. Without Python: check by hand that each `tool` and `data`
   is declared or in the catalogues, that each `parent` is a container of the file in the same
   tool, and reread every text with the rules above.

## Step 4 — Summary and sending preview

**Choose the destination first**, the first that exists: the intake folder (by
`intake.drive_folder_id`, or by its name in the folder of the configuration and its parent), the
intake address, the folder of the configuration, otherwise the person drops the file and sends it
to `intake.merged_by`. At the first run of an organization, the intake folder often does not
exist yet: say so in one line.

**A. The summary**, in the conversation (not sent): the script's figures (containers by tool and
by type of data, freshness), the three to five places that answer the questions the person
asked, the places left out (how many, why, in one line), the tools that could not be read, and
what surprised you (a type of data in three places, a folder untouched for two years).

**B. The preview**, in an artifact:

```bash
python3 <skill folder>/scripts/check_datamap.py <file> --config rpt-config.yaml --catalogues catalogues --preview > apercu.md
```

When the file will not go to the intake folder or address of the configuration, add
`--destination "<where it will go>"`, so that the preview does not name a folder that does not
exist. Create an artifact (Markdown document)
whose content is **exactly** `apercu.md`, without rewriting or adding anything. Without
artifacts, paste its content in your answer.

## Step 5 — Have the preview reviewed, then send

**Always ask for a review of the preview before sending**, in the person's language:

> "The artifact shows everything that will be sent, and nothing else: places, sizes and dates,
> no content. Check in particular that no name of a client or a person remains. The file will go
> to <destination>; <intake.merged_by> will merge it into the data map."

then the question tool asks "Shall I send it as is?", answers "Send as is" and "Change something".
Send only after an explicit approval given after this preview; an approval given earlier does
not count. After a correction, run the script and the preview again, replace the artifact and
ask again.

After the approval, give the file to download, then send it like a map of the skill
`ts-general-check-process-cartography`: create it in the intake folder with the Google Drive
connector (content type `text/plain`, conversion to Google Docs disabled; check the created file
is not a Google Doc), else e-mail it to the intake address (subject
`Data map — <first name> — <YYYY-MM-DD>`, in French `Carte des données — <prénom> — <AAAA-MM-JJ>`;
body: one sentence, then the YAML content), else the folder of the configuration, else the person
drops it. Send nothing else: neither the preview nor the summary. Say what was done.

## Files of the skill

| File | When to read it |
|---|---|
| `references/format-datamap-v1.md` | At step 2, before writing the first container: fields, kinds, placeholders, what is refused. |
| `assets/exemple.datamap.yaml` | At step 3: a complete and valid data map whose structure to copy. |
| `references/data-sources.yaml` | At step 2, without the organization's catalogue: the common types of data. |
| `scripts/check_datamap.py` | To run at step 3 (check) and at step 4 (`--preview`). |
| `scripts/build_rpt.py`, `scripts/rpt_i18n.py`, `scripts/preview_rpt.py` | The referential's tool, the messages in each language and the detectors of personal data, called by `check_datamap.py`; no need to read them. |
