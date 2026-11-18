---
name: ts-general-rpt-context
description: "Generate, from an organization's rpt-config.yaml, its RPT context skill: a packaged skill (.skill and .zip) that carries what the organization's instructions give the RPT skills in Claude, for an AI tool that has no organization instructions, such as ChatGPT. It holds the text of global_context, where the configuration, the referential, the task index and the intake folder are, the teams and their codes, the owners, what is never sent nor filed, and a copy of rpt-config.yaml, so that the mapping, the data map, the observation and the filing know where to drop and where to read. Builds it with the shipped script, shows it, gives it after approval. Use when an organization uses the RPT skills in ChatGPT or in another tool without global instructions, when its maps do not know where to go, after a change of its rpt-config.yaml, or when someone says 'make our RPT context skill', « génère le skill de contexte RPT », « la carto ne sait pas où déposer »."
metadata:
  version: "1.0 (2026-11-18)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-rpt-context; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Generate an organization's RPT context skill

Speak and write to the person in their language; this file is in English.

The RPT skills (`ts-general-check-process-cartography`, `ts-general-data-crawl`,
`ts-general-rpt-observe`, `ts-general-rpt-file`, `ts-general-os-place`) carry no value of any
organization. In Claude, they find the organization's configuration through its instructions,
the global context Claude receives in every conversation: its `Config RPT` line gives the
address of `rpt-config.yaml`, and the rest of the text says when to propose each skill. An AI
tool without organization instructions (ChatGPT, for example) gives them nothing: the mapping
does not know where to drop a map, the filing does not know where the referential is, and none
of them knows what the organization never sends.

This skill turns the organization's `rpt-config.yaml` into a skill of its own, the **RPT context
skill**, named `<organization>-rpt-context` (`make-the-grade-rpt-context`). The organization
installs it next to the RPT skills; it holds:

- the text of `global_context`, to follow as the organization's instructions;
- where the configuration, the referential, the task index, the explorer, the merged maps and the
  intake folder are, with the intake folder's link, who can read it and who merges the maps;
- how to read the configuration and where to drop or file each thing;
- the teams with their codes, scope, headcount and lead, and the owners;
- `privacy` (`excluded`, `allowed_personal_data`, `not_filed`);
- a copy of `rpt-config.yaml`, in its folder references, used when the address cannot be
  read.

The skill carries the configuration of one date: a change of `rpt-config.yaml` (a folder, a
team, the global context) needs a new generation. In Claude, where the organization's
instructions exist, the context skill is not needed; installing it there does no harm.

## Skill files

| File | When to read it |
|---|---|
| `scripts/build_context_skill.py` | At step 2: `python3 scripts/build_context_skill.py rpt-config.yaml --out-dir <folder>` writes the skill folder and its package. |
| `assets/exemple-rpt-config.yaml` | When the person has no configuration yet: the form of a filled-in file (fictitious organization). Never generate a skill from it. |

## Step 1 — The configuration

Take the organization's `rpt-config.yaml` by the first means that works: the file the person
adds to the conversation; the address on the `Config RPT` line of the organization's
instructions, read with the Google Drive connector (the file whose id is in the link; for a
folder link, the file named `rpt-config.yaml` in that folder) or the GitHub connector; a search
of Drive for `rpt-config.yaml`, which the person confirms is their organization's. Never write a
configuration here: without one, the organization runs `ts-general-rpt-setup` first.

Save it as `rpt-config.yaml` in your working folder. When the file has a `referential.config_url`
that does not lead to the folder where you found it, say so in one line: the context skill
carries that address, and the RPT skills will look there first.

## Step 2 — Build the skill

```bash
python3 scripts/build_context_skill.py rpt-config.yaml --out-dir out
```

The script refuses a configuration without `organization.name`, without a place for the
referential (`config_url`, `drive_folder` or `repository_path`), without an intake destination
(`drive_folder`, `drive_folder_id` or `email`) or without `global_context`: name what is missing
and stop; the organization completes its file (with `ts-general-rpt-setup`, or by hand) and
runs this skill again. The name is `<organization slug>-rpt-context`; `--name` gives another one
(lowercase letters, digits and hyphens, 64 characters at most).

It writes `out/<name>/` (`SKILL.md` and the copy of the configuration), `out/<name>.skill` for
claude.ai and `out/<name>.zip` for ChatGPT: the same zip.

## Step 3 — Show, then give

Show the person the generated `SKILL.md` in full: it is what every RPT skill will read as the
organization's instructions. It holds no value the configuration does not hold; check with them
that the intake folder, its audience (`intake.visibility`) and the teams are right. A wrong value
is corrected in `rpt-config.yaml`, never in the generated file, and the skill is built again.

After their approval, give the package: as a file of the conversation, or, with their approval,
in the folder of the configuration (next to `rpt-config.yaml`). Then tell them how to install it:

- **ChatGPT**: upload `<name>.zip` as a skill (workspace skills for the whole organization when
  the plan allows it), next to the RPT skills.
- **Claude**: not needed when the organization's instructions hold `global_context`; otherwise
  upload `<name>.skill` (Settings, Capabilities, Skills).

Each time `rpt-config.yaml` changes, run this skill again and replace the installed skill.

## What the skill does not do

- It does not write nor change `rpt-config.yaml`: that is `ts-general-rpt-setup`.
- It does not map, observe, file nor place: the RPT skills do, reading the context skill.
- It reads nothing but the configuration, and the package holds nothing else.
- It installs nothing and drops nothing without the person's approval.
