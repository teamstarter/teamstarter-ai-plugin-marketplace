# Plugins Teamstarter pour les outils IA

Ce dossier est un marketplace de plugins, au format des plugins Claude, que ChatGPT sait aussi
lire. Un plugin regroupe des skills (la méthode, en Markdown) et le connecteur MCP Teamstarter
(l'accès aux données). Le collaborateur fait avancer ses projets Teamstarter depuis sa
conversation ; l'app reste la source de vérité : statuts, réponses et fiches sont écrits dans
Teamstarter, jamais seulement dans la mémoire de l'outil IA.

Contexte : atelier « outil IA + app recentrée », board Miro
[parcours de A à Z](https://miro.com/app/board/uXjVEdqfWjI=/) (post-its bleus = maintenant,
roses = ensuite).


> Source : dossier [`plugin-ts/`](https://github.com/teamstarter/teamstarter/tree/develop/plugin-ts) du dépôt `teamstarter/teamstarter`, recopié à la racine de [`teamstarter/teamstarter-plugin-ia`](https://github.com/teamstarter/teamstarter-plugin-ia). Modifier les fichiers dans `plugin-ts/`, jamais directement dans `teamstarter-plugin-ia`.
## Contenu

```
plugin-ts/
├── .claude-plugin/marketplace.json     # le marketplace « teamstarter » et la liste des plugins
├── teamstarter-core/                   # plugin pour tous les collaborateurs
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json                       # connecteur Teamstarter : https://app.teamstarter.co/mcp
│   └── skills/
│       ├── ts-general-creer-projet/    # créer un projet, tout type, jusqu'à « Proposer » ; reprendre un brouillon
│       └── ts-general-lister-projets/  # mes projets par statut, choisir lequel reprendre
└── scripts/check_plugins.py            # vérifier, synchroniser les fichiers partagés, empaqueter
```

Prévus, pas encore commencés : `teamstarter-admin` (ambassadeurs, chefs de projet) et
`teamstarter-platform-admin` (staff Teamstarter).

## Ce que couvre `teamstarter-core`

| Post-it du board | Couleur | Skill | État |
|---|---|---|---|
| Initier un projet (depuis une idée ou pas) | bleu | `ts-general-creer-projet`, étapes 2-3 (`sourceIdeaId`) | écrit |
| Vérifier si mon idée existe déjà | rose | `ts-general-creer-projet`, étape 3 (doublons : projets et idées) | écrit |
| Répondre aux questions de structuration | bleu | `ts-general-creer-projet`, étape 4 | écrit |
| Faire générer la fiche par l'IA | bleu | `ts-general-creer-projet`, étape 5 | écrit |
| Modifier les sections | bleu | `ts-general-creer-projet`, étape 5 | écrit |
| Voir l'audit du cadre | bleu | `ts-general-creer-projet`, étape 6 | écrit |
| Proposer le projet | bleu | `ts-general-creer-projet`, étape 7 | écrit |
| Reprendre un brouillon | jaune | `ts-general-creer-projet`, étape 1 ; `ts-general-lister-projets` | écrit |
| Récupérer le prompt, créer mon agent, tester, date de mise en place, signaler un blocage, partager, déclarer mis en place | bleu | — | à faire (phase réalisation) |
| Poster une idée, classer l'idée dans un process, uploader le skill, mettre à jour et republier, donner un retour | rose | — | à faire |
| Prioriser, désigner des porteurs (ambassadeur) | rose | — | plugin `teamstarter-admin` |

Étapes de parcours : `PMG-A-22` et `PMG-B-15` dans
[la fiche du porteur de projet](https://github.com/teamstarter/teamstarter/blob/develop/teamstarter-os/OS/Product/specifications/journeys/pmg-porteur-de-projet.md),
avec les écarts trouvés en écrivant les skills (`PMG-A-G24`, `PMG-A-G25`, `PMG-B-G10`).

### D'où viennent les skills

- **`ts-general-creer-projet`** reprend le skill d'organisation claude.ai du même nom (validé
  sur des projets Événement, en production et en staging) et le skill
  `ts-general-create-project-skill` du plugin POC `teamstarter-skill-factory` 0.4.0 (type
  « Automatisation de processus avec l'IA »). Il les généralise à tous les types et ajoute la
  reprise d'un brouillon. Les noms et identifiants des organisations clientes ont été retirés :
  le plugin est distribué à tous les clients.
- Les deux autres skills du POC (`ts-general-generer-skill`, `ts-general-declarer-execution-skill`)
  fabriquent des skills Claude et déclarent leurs exécutions : hors du sujet de ce plugin. Ils
  restent dans le POC et dans l'historique git (commit `eae294cb`).
- Une organisation qui a déjà le skill d'organisation `ts-general-creer-projet` doit le retirer en
  installant le plugin : deux skills au même nom et aux mêmes déclencheurs se concurrencent.

## Installer

Le connecteur s'autorise une fois, avec son compte Teamstarter : la page de consentement fait
choisir l'organisation et l'accès (lecture, ou lecture et écriture). **Créer un projet demande
l'écriture** ; l'administrateur de l'organisation doit l'avoir ouverte.

| Outil | Comment |
|---|---|
| Claude Code | `/plugin marketplace add teamstarter/teamstarter-plugin-ia` puis `/plugin install teamstarter-core@teamstarter`. En local, depuis ce dépôt : `/plugin marketplace add ./plugin-ts`. Puis `/mcp` pour autoriser le connecteur. |
| claude.ai, Cowork (compte individuel) | Personnaliser → Plugins → Ajouter → téléverser `dist/teamstarter-core.zip` (produit par `--package`), puis connecter le connecteur depuis l'onglet Connecteurs du plugin. |
| claude.ai (Team, Enterprise) | Paramètres de l'organisation → Plugins et skills : le propriétaire téléverse le zip, ou synchronise un repo GitHub qu'il contrôle, et choisit qui l'a (disponible, installé par défaut, obligatoire). |
| ChatGPT | Un admin de workspace importe le marketplace depuis un repo GitHub (le fichier `.claude-plugin/marketplace.json` est lu tel quel) ; le connecteur s'ajoute comme serveur MCP personnalisé (`…/mcp`, OAuth). Un plugin importé avec un `.mcp.json` ne fonctionne que dans l'app de bureau ; pour le web, il faudra enregistrer le connecteur comme app du workspace. Les skills seuls se téléversent depuis `dist/skills/`. |

### Distribution : le dépôt `teamstarter/teamstarter-plugin-ia`

Les plugins sont distribués depuis le dépôt
[`teamstarter/teamstarter-plugin-ia`](https://github.com/teamstarter/teamstarter-plugin-ia), dont la
racine est le contenu de ce dossier : `/plugin marketplace add`, l'import ChatGPT et la
synchronisation d'une organisation claude.ai ne lisent que `.claude-plugin/marketplace.json` **à la
racine** d'un dépôt, et un client n'a pas accès à ce dépôt-ci. Ce dossier reste la source : un
skill se modifie ici, dans la même PR que l'endpoint qu'il appelle, puis le contenu est recopié
dans `teamstarter-plugin-ia`.

L'adresse du connecteur (`https://app.teamstarter.co/mcp`, sans tag d'organisation, décision D17 du
[plan MCP](https://github.com/teamstarter/teamstarter/blob/develop/teamstarter-os/OS/Product/process/opportunities/2026-08-13-connecteur-mcp-cowork-plan.md))
vaut pour les organisations hébergées sur `app.teamstarter.co`. Une instance sur une autre adresse
a besoin de sa propre adresse de connecteur.

## Modifier un skill

1. Écrire dans le dossier du skill. Règles de forme : frontmatter limité à `name` et
   `description` (l'import claude.ai refuse d'autres clés), `name` = nom du dossier, format
   `ts-<domaine>-<verbe>-<objet>`, description de 1024 caractères au plus, sans chevrons, avec les
   phrases qui déclenchent le skill. Corps adressé au modèle, à l'infinitif.
2. Un fichier utile à plusieurs skills est copié dans chacun (un skill doit pouvoir être téléversé
   seul). La source et ses copies sont listées dans `SHARED` du script ; modifier la source, puis
   `python3 scripts/check_plugins.py --sync`. Aujourd'hui : `regles-api.md`, dont la source est
   dans `ts-general-creer-projet`.
3. `python3 scripts/check_plugins.py` doit répondre `OK`.
4. Monter la version dans `plugin.json` et dans `marketplace.json`.

Pas de hook ni de dossier `bin/` pour l'instant : le chat claude.ai et ChatGPT ne les exécutent
pas, et claude.ai refuse un plugin qui a un `bin/` à sa racine. Le script le vérifie.

## Empaqueter

```bash
cd plugin-ts
python3 scripts/check_plugins.py --package
```

Écrit `dist/teamstarter-core.zip` (le plugin) et `dist/skills/<skill>.zip` (chaque skill seul).
`dist/` n'est pas versionné.
