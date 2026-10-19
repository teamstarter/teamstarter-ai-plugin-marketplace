# The data map — rpt/v1 format, `containers` list

A data map is a YAML file of the rpt/v1 format whose main list is `containers`. The same list
lives in the referential, in `OS/Operations/data-map.yaml` (README_operations.md §1.20): a data
map sent by a person is merged into it.

```yaml
format: rpt/v1
meta:
  title: Carte des données — Alex Martin
  organization: Acme Conseil
  authors: [Alex Martin, Claude]
  updated: '2026-10-19'
  detector: ts-general-data-crawl@1.0
  sources: [Google Drive (Drive partagé « Commercial »), HubSpot]
  notes: 'Espace personnel du Drive non lu (refusé).'
tools: [...]          # only the tools absent from the organization's catalogue
data_sources: [...]   # only the types of data absent from the catalogue
containers: [...]
```

`meta` accepts `title`, `organization`, `team`, `authors`, `updated`, `detector`, `sources` and
`notes`, nothing else.

## 1. A container

A container is a place of a tool where data is kept: what an organization would point to when
asked "where is it?".

| Field | Required | What it holds |
|---|---|---|
| `id` | yes | `DC-<n>`, unique in the file (`DC-1`, `DC-2`…). The merge gives the referential's ids. |
| `name` | yes | The name of the place as the team says it ("Propositions", "Devis", "Base Clients"). |
| `tool` | yes | Id of the tool: `catalogues/tools.yaml`, else declared in `tools` of the file. |
| `kind` | yes | One of the kinds of §2. |
| `data` | yes | Id of the type of data: `catalogues/data-sources.yaml`, else `references/data-sources.yaml`, else declared in `data_sources`. |
| `parent` | no | Id of the container it sits in, in the same tool (a sheet in a folder, a pipeline under an object). |
| `path` | no | Where it is in the tool, with placeholders: `Commercial/Propositions/[Client]/`, `CRM › Devis`, `#client-[client]`, the key of a Jira project. |
| `url` | no | `https://` link of the container (never of an item inside it). |
| `holds` | no | One sentence: what it holds, described as a type ("one folder per client, with its proposals"). |
| `items` | no | `{count, unit, approx}`: how many items (`count` a whole number), of what (`unit`: "fichiers", "devis", "pages"), `approx: true` for an estimate. |
| `formats` | no | List of file formats (`[pdf, slides]`). |
| `naming` | no | The naming pattern of its items, with placeholders: `Proposition [Client] [AAAA-MM-JJ].pdf`. |
| `fields` | no | Column names of a sheet, property names of a database or an object, stages of a pipeline, issue types of a project. Names, never values. |
| `freshness` | no | `{last_modified, modified_90d, checked}`: date `YYYY-MM-DD` of the most recent change of its items, number of items changed in the last 90 days, date it was read. |
| `activity` | no | `{editors_90d, viewers_90d}`: counts of distinct people, never names. |
| `access` | no | `{connector, state}`: connector used (`native`, `mcp`, `api`, `export`, `none`) and whether it worked (`works`, `not_found`, `unchecked`). |
| `sensitivity` | no | Categories of the AI policy (`client`, `personal`, `hr`, `internal_confidential`, `regulated`, `public`, `credentials`) when the place holds more sensitive data than its type says. |
| `state` | no | `active` (default), `archived`, `duplicate` (with `duplicate_of: DC-n`), `unused`. |
| `basis` | no | `observed` (read in the tool), `declared` (said by a person), `inferred`. |
| `notes` | no | What the fields do not say: statuses of a project, who fills it (a role or a team, never a person). |
| `sources` | no | Where the description comes from. |
| `written_by`, `read_by`, `owner` | **empty in a data map sent** | Filled at the merge: the tasks (`SALES-T2.9`) that write or read the place, and the role in charge (`SALES-R2`). |

The freshness of a container is computed from the age of its last change: 7 days or less, 8 to
30, 31 to 90, 91 to 180, more than 180, unknown without `last_modified`.

## 2. Kinds

`folder`, `file`, `document`, `spreadsheet`, `presentation` (Drive); `database`, `page`, `view`
(Notion); `object`, `pipeline`, `list` (HubSpot); `channel` (Slack); `label` (Gmail); `project`,
`board` (Jira); `other`.

## 3. Placeholders

A part of a name that varies from one item to the next, or that would name a client, a person
or a date, is written between brackets, in the person's language: `[Client]`, `[Projet]`,
`[Prénom]`, `[Numéro]` (a file or project number), `[Ville]`, `[Fournisseur]`, `[AAAA-MM-JJ]`,
`[Montant]` (`[Client]`, `[Project]`, `[First name]`, `[Number]`, `[Town]`, `[Supplier]`,
`[YYYY-MM-DD]`, `[Amount]` in English). The merge matches two places whatever their placeholders.

## 4. What the check refuses

- an e-mail address, a phone number or an amount in any text of the file: the containers
  (`name`, `path`, `holds`, `naming`, `fields`, `formats`, `items.unit`, `notes`, `sources`),
  `meta`, and the declared tools and types of data (error);
- `written_by`, `read_by` or `owner` filled in a data map sent for merging (error);
- a `tool`, a `data` or a `parent` that exists nowhere, a `parent` in another tool, a loop of
  parents, a count that is not a whole number, a date that is not `YYYY-MM-DD`, a `url` that is
  not `https://` (error);
- a first name, a postal address, an age, a file or project number, an amount before HT or TTC,
  a word of an HR or health subject (warning: replace, leave the place out, or keep an ordinary
  word of the trade).

A declared type of data needs no task and no `tools` list in a data map: its tools are those of
its containers.

## 5. YAML pitfalls

Quote a text that starts with `#`, `[`, `*`, `&`, `!`, `%`, `@` or contains `: ` (a Slack channel
`'#client-[client]'`, a note `'fields : les étapes'`); write dates between quotes
(`'2026-10-19'`). In a list written on one line (`fields: [A, B]`), a comma separates two items:
`[Facturé 4.800,00]` becomes two fields; write such a list one item per line, or quote each item.
