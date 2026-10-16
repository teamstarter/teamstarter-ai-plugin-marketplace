# Plugins Teamstarter pour les outils IA

Ce dépôt est un marketplace de plugins pour les outils IA. Il contient le plugin
**`teamstarter-core`**, qui permet à tout collaborateur d'une organisation Teamstarter de créer
un projet, de le mener jusqu'à sa proposition et de suivre où en sont ses projets, sans quitter
sa conversation avec Claude ou ChatGPT.

Le plugin est au format des plugins Claude, que ChatGPT sait aussi lire. Il réunit :

- des **skills** : la méthode, écrite en Markdown, que l'outil IA suit étape par étape ;
- le **connecteur MCP Teamstarter** : l'accès à vos données Teamstarter, avec votre propre compte.

**Teamstarter reste la source de vérité.** Statuts, réponses et fiches sont écrits dans
Teamstarter, jamais seulement dans la mémoire de l'outil IA. Un brouillon commencé dans l'app se
reprend dans une conversation, et inversement ; la liste de vos projets est la même dans Claude,
dans ChatGPT et dans l'app.

## Ce que fait `teamstarter-core`

| Skill | Pour | Exemples de demandes |
|---|---|---|
| `ts-general-creer-projet` | Créer un projet de n'importe quel type, de l'idée jusqu'à sa proposition ; reprendre un brouillon là où il s'est arrêté | « J'ai une idée de projet », « Monte un projet pour notre séminaire de juin », « Reprends mon brouillon », « Génère la fiche de mon projet », « Soumets mon projet » |
| `ts-general-lister-projets` | Voir ses projets regroupés par statut, avec l'étape suivante de chacun, et choisir lequel reprendre | « Où en sont mes projets ? », « Mes brouillons », « Qu'est-ce qu'il me reste à faire sur Teamstarter ? » |
| `ts-general-creer-skill` | Créer un skill (un agent IA) par un projet « Automatisation de processus avec l'IA » : projet, validation, écriture du skill, dépôt de chaque version, test, points de blocage | « Je veux créer un skill », « Crée-moi un agent qui… », « Reprends mon skill », « Dépose la nouvelle version de mon skill », « Mon skill est bloqué » |
| `ts-general-declarer-execution-skill` | Déclarer à Teamstarter chaque utilisation d'un skill rattaché à un projet, pour ses statistiques | se déclenche seul, à la fin de l'exécution d'un tel skill |

Inutile de nommer le skill : l'outil IA le choisit d'après la demande.

### Créer un projet

Le skill suit le même parcours que l'app, en conversation :

1. **Nouveau projet ou reprise.** Si vous avez des brouillons, l'IA propose d'en reprendre un.
   Un brouillon repris repart de la première étape non faite, d'après son état dans Teamstarter.
2. **Type et objectif.** L'IA propose les types de projet de votre organisation (Événement,
   Automatisation de processus avec l'IA, etc.) et ses objectifs ouverts. Le mode de décision du
   projet (modération, vote, financement participatif) découle de l'objectif choisi.
3. **Titre, description, doublons.** Avant de créer quoi que ce soit, l'IA cherche les projets et
   les idées proches et vous les montre : vous pouvez rejoindre l'existant. Un projet peut aussi
   partir d'une idée de la boîte à idées ou d'un atelier ; il lui est alors relié.
   → **Validation**, puis création du brouillon. L'IA vous donne son numéro : c'est avec lui que
   vous le retrouverez.
4. **Questions de structuration.** Vous répondez vous-même, ou l'IA propose des réponses à partir
   de ce que vous avez déjà dit. → **Validation section par section** avant chaque écriture.
   Selon le projet : co-porteurs (ils reçoivent une notification, l'IA vous prévient avant),
   lignes de dépense et budget.
5. **Fiche du projet.** Générée par l'IA de Teamstarter quand votre accès le permet, sinon
   rédigée dans la conversation (→ **validation**). Chaque section peut être modifiée ensuite.
6. **Audit du cadre**, quand votre accès le permet : le projet est confronté aux règles définies
   par votre organisation, et l'IA vous restitue les points d'attention et les améliorations
   suggérées. Vous corrigez puis relancez l'audit, ou vous passez outre.
7. **Proposer le projet.** L'IA vérifie que rien ne manque (questions obligatoires, sections de
   la fiche, budget), affiche un récapitulatif et ce qui va se passer : relecture par les
   animateurs, ou publication directe si votre organisation ne relit pas les projets.
   → **Confirmation explicite** obligatoire.

Vous pouvez vous arrêter à n'importe quelle étape : le brouillon reste cohérent dans
Teamstarter, et « reprends mon projet <numéro> » repart de là, dans la même conversation ou
dans une autre.

Deux types ont des consignes propres : **Événement** (date, horaires et lieu demandés, jamais
inventés ; dépenses et budget) et **Automatisation de processus avec l'IA** (la tâche, ses étapes,
le temps qu'elle prend, et aucune donnée sensible dans la fiche). Les autres types suivent le
parcours commun, avec les questions que votre organisation a définies.

### Créer un skill

`ts-general-creer-skill` passe avant le skill `skill-creator` d'Anthropic : un skill de
l'organisation naît d'un projet Teamstarter.

1. **Projet.** L'IA crée et propose un projet « Automatisation de processus avec l'IA » avec
   `ts-general-creer-projet`, en reprenant ce que vous avez dit de la tâche.
2. **Validation.** Si votre organisation relit les projets, le projet attend la validation des
   animateurs : revenez quand il est validé, l'IA reprend là. Sans relecture, le projet passe
   directement en réalisation.
3. **Écriture.** Le projet en réalisation, l'IA récupère le prompt de création du skill généré par
   Teamstarter et confie l'écriture à `skill-creator`. Le skill porte l'id du projet dans ses
   métadonnées (`teamstarter-project-id`). → **Validation** du skill, puis livraison en zip prêt
   à installer.
4. **Dépôt.** Le skill est déposé sur le projet, puis chaque nouvelle version que vous validez.
5. **Étapes de réalisation.** L'IA coche avec votre accord « Créer mon agent IA », puis « Tester
   l'agent en conditions réelles » une fois le test concluant.
6. **Utilisation.** Chaque exécution du skill est déclarée à Teamstarter par
   `ts-general-declarer-execution-skill` : heure, durée, tokens (estimés quand l'outil ne les
   affiche pas) et personne qui l'utilise, pour les statistiques d'utilisation du projet.
7. **Blocage.** Un problème qui empêche de créer ou d'utiliser le skill devient, avec votre accord,
   un point de blocage sur le projet.

Le prompt de création, le dépôt du skill, la validation des étapes et la déclaration des
utilisations demandent des outils du connecteur que votre accès n'a peut-être pas encore. Sans
eux, l'IA vous dit quoi faire dans l'app : copier le prompt, déposer le fichier, cocher l'étape.
Sans eux, les utilisations ne sont pas comptées.

### Lister ses projets

Les projets sont regroupés comme dans la page « Mes projets » de l'app : structuration, en cours
de rédaction, en attente de modération, soumis au vote, en cours de financement, recherche de
participants, campagne échouée, en cours de réalisation, mis en place, terminé. Pour chacun :
titre, numéro, type, date de dernière mise à jour, étape suivante, et le lien vers l'app quand
son adresse est connue. L'IA propose ensuite de reprendre un brouillon.

Vos projets déjà proposés ou publiés sont visibles par toute l'organisation : pour ne garder que
les vôtres, l'IA vous demande de confirmer votre identité. Sans cette confirmation, elle n'affiche
que vos brouillons et vos projets en attente de modération, et dit ce qu'elle n'a pas pu lire.

Ce skill est en lecture seule : il ne modifie rien.

### Garde-fous

- **Rien n'est écrit sans votre accord** : chaque écriture suit une validation, et la proposition
  du projet demande une confirmation explicite. Seule exception : la déclaration d'utilisation
  d'un skill de projet, faite à la fin de chaque exécution et annoncée dans la réponse.
- **Rien n'est inventé** : date, lieu, montant, prestataire, co-porteur. L'IA vous les demande,
  ou écrit « à préciser » en vous le disant.
- Une réponse ou une section n'est jamais réécrite sans vous le dire, et seulement celle que vous
  avez demandée.
- Un projet proposé n'est jamais repassé en brouillon sans votre demande.

### Ce qui se fait dans l'app

Pour un projet autre qu'un skill, le plugin s'arrête à la proposition. Le suivi d'un projet déjà
proposé (vote, financement, réalisation, mise en place) et le dépôt d'idées se font dans l'app
Teamstarter.

## Installer

### Avant de commencer

- Il faut un compte Teamstarter dans l'organisation.
- Le connecteur s'autorise une fois, avec ce compte : la page de consentement fait choisir
  l'organisation et le niveau d'accès (lecture, ou lecture et écriture).
- **Créer un projet demande l'accès en écriture**, que l'administrateur de votre organisation
  doit avoir ouvert. En lecture seule, la liste des projets fonctionne, et la création produit une
  fiche Markdown à recopier dans l'app.

### Selon l'outil

| Outil | Comment |
|---|---|
| Claude Code | `/plugin marketplace add teamstarter/teamstarter-ai-plugin-marketplace`, puis `/plugin install teamstarter-core@teamstarter`. Depuis une copie locale du dépôt : `/plugin marketplace add <chemin du dépôt>`. Puis `/mcp` pour autoriser le connecteur. |
| claude.ai, Cowork (compte individuel) | Personnaliser → Plugins → Ajouter → téléverser `teamstarter-core.zip` (voir [Empaqueter](#empaqueter)), puis connecter le connecteur depuis l'onglet Connecteurs du plugin. |
| claude.ai (Team, Enterprise) | Paramètres de l'organisation → Plugins et skills : le propriétaire téléverse le zip, ou synchronise un dépôt GitHub qu'il contrôle (une copie de celui-ci), et choisit qui a le plugin (disponible, installé par défaut, obligatoire). |
| ChatGPT | Un administrateur du workspace importe le marketplace depuis un dépôt GitHub (le fichier `.claude-plugin/marketplace.json` est lu tel quel) ; le connecteur s'ajoute comme serveur MCP personnalisé (`https://app.teamstarter.co/mcp`, OAuth). Un plugin importé avec un `.mcp.json` ne fonctionne que dans l'app de bureau ; pour le web, enregistrer le connecteur comme app du workspace. Les skills seuls se téléversent depuis `dist/skills/`. |

### Adresse du connecteur

`https://app.teamstarter.co/mcp` vaut pour les organisations hébergées sur
`app.teamstarter.co`. Une instance Teamstarter sur une autre adresse a son propre connecteur :
remplacer l'adresse dans `teamstarter-core/.mcp.json` avant d'installer ou d'empaqueter le plugin.

### Si vous aviez déjà le skill `ts-general-creer-projet`

Une organisation qui a déjà installé un skill `ts-general-creer-projet` séparément doit le retirer
en installant le plugin : deux skills au même nom et aux mêmes déclencheurs se concurrencent.

## En cas de souci

| Situation | Ce que fait l'IA |
|---|---|
| Connecteur pas connecté | Le dit et explique comment le connecter. Pour un projet, prépare quand même les réponses et la fiche dans un fichier à recopier dans l'app. |
| Accès en lecture seule | Liste vos projets. Pour un projet, livre la fiche dans un fichier `fiche-projet-<titre>.md`. Pour écrire : l'administrateur ouvre l'accès en écriture, puis vous reconnectez le connecteur en choisissant lecture et écriture. |
| Génération de fiche ou audit absents de votre accès | Rédige la fiche elle-même, et passe l'audit en vous le disant. |
| Génération ou audit qui dépasse 5 minutes | Arrête d'attendre, dit où en est le projet ; reprenez plus tard avec « reprends mon projet <numéro> ». |
| Plusieurs connecteurs Teamstarter, ou un accès à plusieurs organisations | Vous demande lequel ou laquelle utiliser. |

## Pour les mainteneurs

### Contenu du dépôt

```
.
├── .claude-plugin/marketplace.json     # le marketplace « teamstarter » et la liste de ses plugins
├── teamstarter-core/                   # le plugin pour tous les collaborateurs
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json                       # connecteur Teamstarter : https://app.teamstarter.co/mcp
│   ├── README.md                       # description du plugin, affichée par le répertoire de Claude
│   ├── LICENSE                         # MIT
│   └── skills/
│       ├── ts-general-creer-projet/    # créer un projet jusqu'à sa proposition ; reprendre un brouillon
│       ├── ts-general-lister-projets/  # mes projets par statut ; choisir lequel reprendre
│       ├── ts-general-creer-skill/     # créer un skill par un projet : écrire, déposer, tester, blocages
│       └── ts-general-declarer-execution-skill/  # déclarer chaque utilisation d'un skill de projet
└── scripts/check_plugins.py            # vérifier, synchroniser les fichiers partagés, empaqueter
```

### Empaqueter

```bash
python3 scripts/check_plugins.py --package
```

Écrit `dist/teamstarter-core.zip` (le plugin, pour claude.ai et Cowork) et
`dist/skills/<skill>.zip` (chaque skill seul, pour claude.ai ou ChatGPT). `dist/` n'est pas
versionné.

### Modifier un skill

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

Pas de hook ni de dossier `bin/` : le chat claude.ai et ChatGPT ne les exécutent pas, et
claude.ai refuse un plugin qui a un `bin/` à sa racine. Le script le vérifie.
