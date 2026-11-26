# Marketplace Teamstarter pour ChatGPT

Ce dossier est le marketplace à importer dans un workspace ChatGPT. Il contient le plugin
`teamstarter-core` du dépôt, sans son fichier `.mcp.json`.

ChatGPT marque « Desktop only » un plugin importé qui déclare un serveur MCP (`.mcp.json` ou
`mcp.json`), même quand ce serveur a une adresse HTTPS distante comme
`https://app.teamstarter.co/mcp` (aide OpenAI « Importing and syncing plugin marketplaces from
GitHub », section « Understand the Desktop only label »). Un plugin « Desktop only » ne tourne que
dans l'app de bureau de ChatGPT : ni sur le web, ni dans l'app mobile. Claude a besoin de ce
`.mcp.json` pour trouver le connecteur : le plugin de la racine du dépôt le garde, cette copie le
laisse de côté.

## Installer dans ChatGPT

Dans un workspace ChatGPT Business, Enterprise ou Edu, un administrateur :

1. ajoute le connecteur Teamstarter comme app du workspace : un serveur MCP personnalisé, adresse
   `https://app.teamstarter.co/mcp`, authentification OAuth, publié pour les membres (aide OpenAI
   « Connecting custom MCP servers in ChatGPT ») ;
2. importe le marketplace : Admin Console → Plugins → Add → Import marketplace, Source
   `https://github.com/teamstarter/teamstarter-ai-plugin-marketplace`, Path `chatgpt`, branche
   vide (la branche par défaut, que la synchronisation quotidienne suit) ;
3. règle l'installation du plugin `teamstarter-core` (« Available » ou « Installed ») pour les rôles
   qui en ont besoin.

Puis chaque membre connecte l'app Teamstarter une fois, avec son compte Teamstarter : la page de
consentement fait choisir l'organisation et le niveau d'accès (lecture, ou lecture et écriture).

Un workspace qui a déjà importé le dépôt avec le chemin vide supprime d'abord cet import : son
plugin est « Desktop only », et deux plugins au même nom et aux mêmes skills se concurrencent.
Supprimer un marketplace dans ChatGPT supprime ses plugins : leurs réglages d'installation sont à
refaire après le nouvel import.

Sans import GitHub, un administrateur téléverse `dist/chatgpt/teamstarter-core.zip` (Admin
Console → Plugins → Add), écrit par `python3 scripts/check_plugins.py --package`.

## Ne pas modifier ce dossier à la main

Tout ce dossier, sauf ce README, est écrit par `python3 scripts/check_plugins.py --sync` à partir
du marketplace de la racine (`.claude-plugin/marketplace.json` et `teamstarter-core/`).
`python3 scripts/check_plugins.py` refuse une copie qui en diffère. Pour changer un skill, un
manifeste ou la version : modifier la source à la racine, puis lancer `--sync`.
