#!/usr/bin/env python3
"""
Vérifie et empaquette les plugins du marketplace Teamstarter.

Usage, depuis la racine du dépôt :
    python3 scripts/check_plugins.py              # vérifie tout, code retour 1 si erreur
    python3 scripts/check_plugins.py --sync       # recopie les fichiers partagés, puis vérifie
    python3 scripts/check_plugins.py --package    # vérifie, puis écrit les zips dans dist/

Vérifie :
  - .claude-plugin/marketplace.json : name, owner.name, plugins[].name et source ;
  - chaque plugin : .claude-plugin/plugin.json (name = nom du marketplace), .mcp.json (serveur
    http avec url), ni dossier bin/ (refusé par claude.ai) ni hooks/ (pas de hook pour l'instant) ;
  - chaque skill : frontmatter limité aux clés du format agentskills.io, name = dossier, format
    ts-domaine-verbe-objet, 64 caractères au plus, description de 1024 caractères au plus et sans
    chevron, fichiers references/ et scripts/ cités qui existent ;
  - les copies des fichiers partagés (SHARED) identiques à leur source.

--package écrit dans dist/ :
  - <plugin>.zip : le plugin, à téléverser dans claude.ai (Personnaliser > Plugins > Ajouter) ;
  - skills/<skill>.zip : chaque skill seul, dossier du skill à la racine du zip, à téléverser
    comme skill dans claude.ai ou ChatGPT.

Stdlib uniquement.
"""

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Source -> copies. Un skill doit rester autonome (téléversé seul dans claude.ai ou ChatGPT) :
# un fichier utile à plusieurs skills est copié dans chacun, et modifié seulement à la source.
SHARED = {
    "teamstarter-core/skills/ts-general-creer-projet/references/regles-api.md": [
        "teamstarter-core/skills/ts-general-lister-projets/references/regles-api.md",
        "teamstarter-core/skills/ts-general-creer-skill/references/regles-api.md",
        "teamstarter-core/skills/ts-general-lister-idees-automatisation/references/regles-api.md",
    ],
}

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
SKILL_NAME_RE = re.compile(r"^ts-[a-z0-9]+(-[a-z0-9]+){2,}$")
LOCAL_FILE_RE = re.compile(r"`((?:references|scripts|assets)/[A-Za-z0-9_./-]+)`")
EXCLUDED_FROM_ZIP = {"__pycache__", ".DS_Store"}


def parse_frontmatter(text):
    """Renvoie (dict, corps) d'un SKILL.md ; valeurs repliées (>-, |) jointes par des espaces."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    block, body = text[4:end], text[end + 4 :]
    data, key = {}, None
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match and not line.startswith(" "):
            key, value = match.group(1), match.group(2).strip()
            data[key] = "" if value in (">-", ">", "|", "|-") else value.strip("\"'")
        elif key and line.strip():
            data[key] = (data[key] + " " + line.strip()).strip()
    return data, body


def check_skill(skill_dir, errors):
    skill_md = skill_dir / "SKILL.md"
    where = skill_dir.relative_to(ROOT)
    if not skill_md.is_file():
        errors.append(f"{where} : SKILL.md manquant")
        return
    data, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if data is None:
        errors.append(f"{where} : frontmatter absent ou mal fermé")
        return
    unknown = set(data) - ALLOWED_FRONTMATTER_KEYS
    if unknown:
        errors.append(f"{where} : clés de frontmatter refusées à l'import : {sorted(unknown)}")
    name, description = data.get("name", ""), data.get("description", "")
    if name != skill_dir.name:
        errors.append(f"{where} : name « {name} » différent du nom du dossier")
    if not SKILL_NAME_RE.match(name) or len(name) > 64:
        errors.append(f"{where} : name hors convention ts-domaine-verbe-objet (64 car. max)")
    if not description:
        errors.append(f"{where} : description vide")
    if len(description) > 1024:
        errors.append(f"{where} : description de {len(description)} caractères (1024 max)")
    if "<" in description or ">" in description:
        errors.append(f"{where} : chevron dans la description (refusé à l'import)")
    for cited in sorted(set(LOCAL_FILE_RE.findall(body))):
        if not (skill_dir / cited).exists():
            errors.append(f"{where} : fichier cité introuvable : {cited}")


def check_plugin(entry, marketplace_dir, errors):
    name, source = entry.get("name"), entry.get("source")
    if not name or not isinstance(source, str):
        errors.append(f"marketplace.json : entrée sans name ou source : {entry}")
        return None
    plugin_dir = (marketplace_dir / source).resolve()
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        errors.append(f"{source} : .claude-plugin/plugin.json manquant")
        return None
    plugin = json.loads(manifest.read_text(encoding="utf-8"))
    if plugin.get("name") != name:
        errors.append(f"{source} : plugin.json name « {plugin.get('name')} » ≠ « {name} »")
    for forbidden in ("bin", "hooks"):
        if (plugin_dir / forbidden).exists():
            errors.append(f"{source} : dossier {forbidden}/ présent")
    mcp = plugin_dir / ".mcp.json"
    if mcp.is_file():
        servers = json.loads(mcp.read_text(encoding="utf-8")).get("mcpServers", {})
        for server_name, server in servers.items():
            if server.get("type") != "http" or not server.get("url"):
                errors.append(f"{source} : serveur MCP {server_name} sans type http ni url")
    skills_dir = plugin_dir / "skills"
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        check_skill(skill_dir, errors)
    return plugin_dir


def check_shared(errors, sync):
    for source, copies in SHARED.items():
        source_path = ROOT / source
        if not source_path.is_file():
            errors.append(f"fichier partagé introuvable : {source}")
            continue
        for copy in copies:
            copy_path = ROOT / copy
            if sync:
                copy_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_path, copy_path)
            elif not copy_path.is_file() or copy_path.read_bytes() != source_path.read_bytes():
                errors.append(f"{copy} diffère de {source} : lancer avec --sync")


def zip_dir(directory, target, prefix):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not EXCLUDED_FROM_ZIP & set(path.parts):
                archive.write(path, Path(prefix) / path.relative_to(directory))


def package(plugin_dirs):
    dist = ROOT / "dist"
    shutil.rmtree(dist, ignore_errors=True)
    (dist / "skills").mkdir(parents=True)
    for plugin_dir in plugin_dirs:
        zip_dir(plugin_dir, dist / f"{plugin_dir.name}.zip", "")
        for skill_dir in sorted(p for p in (plugin_dir / "skills").iterdir() if p.is_dir()):
            zip_dir(skill_dir, dist / "skills" / f"{skill_dir.name}.zip", skill_dir.name)
    for built in sorted(dist.rglob("*.zip")):
        print(f"écrit : {built.relative_to(ROOT)}")


def main(argv):
    sync, do_package = "--sync" in argv, "--package" in argv
    errors = []
    check_shared(errors, sync)
    marketplace_file = ROOT / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_file.read_text(encoding="utf-8"))
    if not marketplace.get("name") or not marketplace.get("owner", {}).get("name"):
        errors.append("marketplace.json : name ou owner.name manquant")
    plugin_dirs = [
        plugin_dir
        for entry in marketplace.get("plugins", [])
        if (plugin_dir := check_plugin(entry, ROOT, errors)) is not None
    ]
    if errors:
        print("\n".join(f"ERREUR {error}" for error in errors))
        return 1
    print(f"OK : {len(plugin_dirs)} plugin(s) vérifié(s)")
    if do_package:
        package(plugin_dirs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
