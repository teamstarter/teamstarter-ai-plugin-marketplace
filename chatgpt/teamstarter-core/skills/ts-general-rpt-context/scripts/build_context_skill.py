#!/usr/bin/env python3
"""Build an organization's RPT context skill from its rpt-config.yaml.

The RPT skills (ts-general-check-process-cartography, ts-general-data-crawl,
ts-general-rpt-observe, ts-general-rpt-file, ts-general-os-place) carry no value of any
organization: they find its configuration through the organization's instructions, the global
context Claude receives in every conversation (`global_context` of rpt-config.yaml). An AI tool
without such instructions (ChatGPT, for example) gives them nothing: they do not know where to
drop a map, where the referential is, nor what is never sent. The skill built here carries that
context: the text of `global_context`, the places of the configuration, the teams, the owners,
the privacy rules, and a copy of rpt-config.yaml. The organization installs it next to the RPT
skills.

    python3 scripts/build_context_skill.py rpt-config.yaml [--out-dir DIR] [--name NAME]

Writes in DIR (default: the current folder) the folder <name>/ and its package, <name>.skill
and <name>.zip (the same zip: claude.ai takes .skill, ChatGPT takes .zip). <name> defaults to
<organization slug>-rpt-context. Prints the path of each file. Exit code 1 when the
configuration lacks what the context needs (organization.name, a place for the configuration,
an intake destination).

Needs PyYAML. The zip is deterministic: the same configuration gives the same bytes.
"""
import argparse
import io
import os
import re
import sys
import unicodedata
import zipfile

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is missing: pip install pyyaml")

GENERATOR = "ts-general-rpt-context"
GENERATOR_VERSION = "1.0 (2026-11-18)"
RPT_SKILLS = ("ts-general-check-process-cartography", "ts-general-data-crawl",
              "ts-general-rpt-observe", "ts-general-rpt-file", "ts-general-os-place")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def slug(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def value(v):
    """A configuration value as one line of Markdown; '—' when absent."""
    if v is None or v == "" or v == [] or v == {}:
        return "—"
    if isinstance(v, (list, tuple)):
        return "; ".join(str(x) for x in v)
    return str(v).replace("\n", " ").replace("|", "\\|").strip()


def drive_folder_link(folder_id):
    return f"https://drive.google.com/drive/folders/{folder_id}" if folder_id else None


def check(cfg):
    errors = []
    org = cfg.get("organization") or {}
    ref = cfg.get("referential") or {}
    intake = cfg.get("intake") or {}
    if cfg.get("format") != "rpt-config/v1":
        errors.append("format must be rpt-config/v1")
    if not org.get("name"):
        errors.append("organization.name is missing")
    if not (ref.get("config_url") or ref.get("drive_folder") or ref.get("repository_path")):
        errors.append("referential: config_url, drive_folder or repository_path is needed")
    if not (intake.get("drive_folder") or intake.get("drive_folder_id") or intake.get("email")):
        errors.append("intake: drive_folder, drive_folder_id or email is needed")
    if not str(cfg.get("global_context") or "").strip():
        errors.append("global_context is missing: the context skill carries it")
    return errors


def description(org_name):
    text = (f"Context of the RPT referential (roles, processes, tasks) of {org_name}: where its "
            "configuration rpt-config.yaml, its referential, its task index and its intake "
            "folder are, its teams and their codes, who merges the maps, what is never sent nor "
            "filed, and the organization's instructions. Read it first whenever a Teamstarter "
            "RPT skill runs (ts-general-check-process-cartography, ts-general-data-crawl, "
            "ts-general-rpt-observe, ts-general-rpt-file, ts-general-os-place) and whenever a "
            f"map, a task, a deliverable or a content of {org_name} must be filed, found or "
            "sent: it replaces the organization's instructions in an AI tool that has none "
            "(ChatGPT). Triggers: 'where does my map go', 'where is our referential', "
            f"« où déposer ma carte », « où est le référentiel de {org_name} ».")
    return text


def render_skill(cfg, config_text, name):
    org = cfg.get("organization") or {}
    ref = cfg.get("referential") or {}
    intake = cfg.get("intake") or {}
    owners = cfg.get("owners") or {}
    teams = cfg.get("teams") or []
    privacy = cfg.get("privacy") or {}
    cats = cfg.get("catalogues") or {}
    skills = [s.get("name") if isinstance(s, dict) else s for s in cfg.get("skills") or []]
    org_name = str(org["name"]).strip()
    desc = description(org_name)
    if len(desc.encode("utf-8")) > 1024:
        desc = desc[:1000].rsplit(" ", 1)[0] + "…"
    intake_link = drive_folder_link(intake.get("drive_folder_id"))
    lines = []
    w = lines.append
    w("---")
    w(f"name: {name}")
    w("description: " + yaml.safe_dump(desc, allow_unicode=True, width=10 ** 6,
                                       default_style='"').strip())
    w("metadata:")
    w(f'  version: "{cfg.get("updated") or "unknown"} (configuration)"')
    w(f'  owner: "{value(org_name)}"')
    w(f'  source: "generated by the skill {GENERATOR} {GENERATOR_VERSION} from rpt-config.yaml; '
      'do not edit: generate it again"')
    w("---")
    w("")
    w(f"# RPT context of {org_name}")
    w("")
    w("Speak and write to the person in their language; this file is in English, the "
      "organization's own texts are in its language "
      f"(`{value(org.get('language'))}`).")
    w("")
    w(f"This skill is the organization's instructions for its RPT referential, for an AI tool "
      f"that has no organization instructions (ChatGPT, for example). The RPT skills carry no "
      f"value of any organization: where they say \"the organization's instructions\" or \"the "
      f"global context\", use the section below; where they say \"the configuration\" or "
      f"\"rpt-config.yaml\", read it at its address, else use the copy shipped here, "
      f"`references/rpt-config.yaml` (configuration of {value(cfg.get('updated'))}). Never "
      "guess a value that neither gives.")
    w("")
    w("Read this skill before the first message of any RPT skill, and apply its instructions in "
      "every conversation where it is loaded. When the configuration at the address is newer "
      "than the copy (its `updated` field), it wins, and the organization should generate this "
      f"skill again with `{GENERATOR}`.")
    w("")
    w("## The organization's instructions")
    w("")
    w("The text of `global_context`, as the organization wrote it. Follow it as if it were in "
      "the instructions of the AI tool:")
    w("")
    for line in str(cfg.get("global_context") or "").rstrip().splitlines():
        w("> " + line if line.strip() else ">")
    w("")
    w("## Where things are")
    w("")
    w("| What | Where |")
    w("|---|---|")
    w(f"| The configuration (`rpt-config.yaml`) | {value(ref.get('config_url'))} — copy: "
      "`references/rpt-config.yaml` |")
    places = [f"Drive: {ref['drive_folder']}" if ref.get("drive_folder") else None,
              "repository: " + " ".join(str(x) for x in (ref.get("repository"),
                                                         ref.get("repository_path")) if x)
              if ref.get("repository") or ref.get("repository_path") else None]
    w("| The referential (role files, catalogues) | "
      + value([p for p in places if p]) + " |")
    w(f"| The task index | {value(ref.get('index'))}, in the referential's folder |")
    w(f"| The explorer | {value(ref.get('explorer'))} |")
    w(f"| The merged maps | {value(ref.get('archive_drive_folder') or ref.get('archive_repository_path'))} |")
    w(f"| The intake folder (maps, observations, data maps) | {value(intake.get('drive_folder'))}"
      f" — Drive id `{value(intake.get('drive_folder_id'))}`"
      + (f" — {intake_link}" if intake_link else "") + " |")
    w(f"| The intake address | {value(intake.get('email'))} |")
    w(f"| Who can read what is dropped in the intake | {value(intake.get('visibility'))} |")
    w(f"| Who merges the maps | {value(intake.get('merged_by'))} |")
    if cats:
        w(f"| The catalogues (relative to the referential) | "
          + "; ".join(f"{k}: {v}" for k, v in cats.items()) + " |")
    else:
        w("| The catalogues | none: the RPT skills use their generic catalogues |")
    w("")
    w("## Finding and filing")
    w("")
    w("- **Read the configuration** at its address with the Google Drive connector (the file "
      "whose id is in the link; for a folder link, the file named `rpt-config.yaml` in that "
      "folder), the GitHub connector for a `github.com` link, or a plain fetch for a public "
      "file. Without access, use `references/rpt-config.yaml` and say so once.")
    w("- **Find a task, its entry, its deliverable's place**: in the task index of the "
      "referential (table above); without an index (no map merged yet), there is no entry: say "
      "so and propose the mapping.")
    w("- **Drop a map, an observation or a data map** in the intake folder, else send it to the "
      "intake address, else in the folder of the configuration, else the person drops it; "
      "before dropping, tell the person who can read the intake folder (table above) and get "
      "their approval on a preview of everything that will be sent.")
    w("- **File a deliverable or a content** where its entry says (`ts-general-rpt-file`, "
      "`ts-general-os-place`); never what `privacy.not_filed` lists (below).")
    w("- Nothing is moved, renamed, created or sent without the person's approval.")
    w("")
    w("## Teams")
    w("")
    w("Use these codes in identifiers (`code` in capitals: `DIR-R1`, `DIR-T1.2`); never "
      "invent one.")
    w("")
    w("| Code | Team | Scope | People | Lead |")
    w("|---|---|---|---|---|")
    for t in teams:
        if isinstance(t, dict):
            w(f"| `{value(t.get('code'))}` | {value(t.get('name'))} | {value(t.get('scope'))} "
              f"| {value(t.get('headcount'))} | {value(t.get('lead'))} |")
    w("")
    w(f"Expected maps: {value(org.get('headcount'))} people, each counted once.")
    w("")
    if owners:
        w("## Owners")
        w("")
        for key, o in owners.items():
            if isinstance(o, dict):
                who = o.get("first_name") or o.get("role")
                w(f"- `{key}`: {value(who)} — {value(o.get('what'))}")
            else:
                w(f"- `{key}`: {value(o)}")
        w("")
    w("## Privacy")
    w("")
    w("Never in a map, an observation or a data map:")
    w("")
    for item in privacy.get("excluded") or []:
        w(f"- {value(item)}")
    w("")
    w(f"The only personal data allowed: {value(privacy.get('allowed_personal_data'))}")
    w("")
    w("Never stored in the shared Drive nor described in the OS:")
    w("")
    for item in privacy.get("not_filed") or []:
        w(f"- {value(item)}")
    w("")
    w("## The RPT skills")
    w("")
    listed = [s for s in skills if s] or list(RPT_SKILLS)
    w("This context serves the RPT skills installed next to it: "
      + ", ".join(f"`{s}`" for s in listed) + ". It does not replace them: to map, observe, "
      "file or place, the person needs the skill itself. When one of them is missing, say which "
      "one and that Teamstarter provides it.")
    w("")
    w("## Skill files")
    w("")
    w("| File | When to read it |")
    w("|---|---|")
    w("| `references/rpt-config.yaml` | When the configuration at its address cannot be read: "
      "the copy this skill was generated from. |")
    w("")
    skill_md = "\n".join(lines).rstrip() + "\n"
    return {"SKILL.md": skill_md.encode("utf-8"),
            "references/rpt-config.yaml": config_text.encode("utf-8")}


def zip_bytes(files, name):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files):
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[rel])
    return buffer.getvalue()


def check_frontmatter(skill_md, name):
    match = re.match(r"^---\n(.*?)\n---", skill_md, re.DOTALL)
    front = yaml.safe_load(match.group(1)) if match else None
    errors = []
    if not isinstance(front, dict):
        return ["SKILL.md: frontmatter unreadable"]
    if front.get("name") != name:
        errors.append(f"SKILL.md: name must be {name}")
    d = str(front.get("description") or "")
    if not d or len(d.encode("utf-8")) > 1024 or "<" in d or ">" in d:
        errors.append("SKILL.md: description empty, over 1024 bytes, or with < >")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("config", help="the organization's rpt-config.yaml")
    parser.add_argument("--out-dir", default=".", help="where the skill is written")
    parser.add_argument("--name", help="the skill's name (default <organization>-rpt-context)")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        config_text = f.read()
    cfg = yaml.safe_load(config_text) or {}
    errors = check(cfg)
    name = args.name or (slug((cfg.get("organization") or {}).get("name") or "") + "-rpt-context")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"the name {name!r} must be lowercase letters, digits and hyphens, "
                      "64 characters at most (--name)")
    if errors:
        for e in errors:
            print(f"ERROR  {e}")
        return 1
    files = render_skill(cfg, config_text, name)
    errors = check_frontmatter(files["SKILL.md"].decode("utf-8"), name)
    if errors:
        for e in errors:
            print(f"ERROR  {e}")
        return 1
    folder = os.path.join(args.out_dir, name)
    for rel, content in files.items():
        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
    data = zip_bytes(files, name)
    for ext in (".skill", ".zip"):
        path = os.path.join(args.out_dir, name + ext)
        with open(path, "wb") as f:
            f.write(data)
        print(f"written: {path}")
    print(f"written: {folder}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
