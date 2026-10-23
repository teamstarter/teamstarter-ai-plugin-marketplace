# Plugins Teamstarter pour les outils IA

Ce dépôt est un marketplace de plugins pour les outils IA. Il contient le plugin
**`teamstarter-core`**, qui permet à tout collaborateur d'une organisation Teamstarter de créer
un projet, de le mener jusqu'à sa proposition et de suivre où en sont ses projets, sans quitter
sa conversation avec Claude ou ChatGPT. Il contient aussi les skills RPT côté utilisateur, qui
décrivent les rôles, processus et tâches de l'organisation et ce qui peut en être confié à l'IA.

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
| `ts-general-creer-skill` | Créer un skill (un agent IA) par un projet « Automatisation de processus avec l'IA » : projet, validation, prompt de création récupéré automatiquement, écriture du skill, test, points de blocage | « Je veux créer un skill », « Crée-moi un agent qui… », « Crée le skill de mon projet », « Reprends mon skill », « Modifie mon skill », « Mon skill est bloqué » |
| `ts-general-deposer-skill` | Déposer sur son projet Teamstarter chaque version d'un skill rattaché à un projet | se déclenche seul, à chaque écriture ou modification du `SKILL.md` d'un tel skill |
| `ts-general-declarer-execution-skill` | Déclarer à Teamstarter chaque utilisation d'un skill rattaché à un projet, pour ses statistiques | se déclenche seul, à la fin de l'exécution d'un tel skill |
| `ts-general-declarer-blocage` | Remonter les blocages d'un projet en réalisation : proposé dès qu'un problème bloque (par exemple l'échec d'un skill de projet), rédigé, validé, déclaré ; lister, commenter, résoudre | « Je suis bloqué sur mon projet », « Déclare un blocage », « Le blocage est levé », « Quels sont les blocages de mon projet ? » ; proposé seul quand un skill de projet échoue |
| `ts-general-lister-idees-automatisation` | Voir les idées d'automatisation déposées dans la boîte à idées et les ateliers : celles à prendre, celles déjà lancées en projet ; créer le skill de l'une d'elles | « Quelles idées d'automatisation ont été proposées ? », « Trouve-moi une idée de skill », « Qu'est-ce que les collègues veulent automatiser ? » |

Les skills RPT (voir [Cartographier ses rôles, processus et tâches](#cartographier-ses-rôles-processus-et-tâches-rpt)) :

| Skill | Pour | Exemples de demandes |
|---|---|---|
| `ts-general-rpt-setup` | Mettre en place RPT dans l'organisation : écrire son fichier `rpt-config.yaml` et le texte à coller dans les instructions de Claude. Une fois par organisation | « Configure RPT pour ma boîte », « Mets en place RPT » |
| `ts-general-check-process-cartography` | Cartographier ses rôles, processus et tâches, ou ceux de son équipe, avec le niveau d'automatisation de chaque tâche, puis déposer la carte dans le dossier de réception de l'organisation | « Fais la carte de mes rôles », « Cartographie mon équipe », « Qu'est-ce que je pourrais automatiser ? » |
| `ts-general-data-crawl` | Décrire où sont les données de l'organisation, outil par outil (Drive, Notion, HubSpot, Slack, Gmail, Linear, Jira), sans lire leur contenu | « Cartographie nos données », « Où est notre donnée ? » |
| `ts-general-rpt-observe` | À la fin d'une tâche faite avec Claude, proposer la mise à jour de sa fiche (durée, outils, méthode, blocage) | « Mets à jour la fiche de cette tâche », « Ce bloqueur est levé » |
| `ts-general-rpt-file` | Ranger le livrable d'une tâche là où sa fiche le dit, sous le bon nom | « Où je range ça ? », « Range ce fichier au bon endroit » |

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

1. **Projet de création de skill.** L'IA crée et propose un projet « Automatisation de processus
   avec l'IA » avec `ts-general-creer-projet`, depuis une idée de la boîte à idées si vous en
   choisissez une. Elle vous demande la **tâche** à automatiser, qui devient le titre du projet,
   puis pose chaque question de structuration **avec son libellé exact dans Teamstarter**, sans la
   reformuler ; ce que vous avez déjà dit de la tâche apparaît comme proposition sous la question.
2. **Validation.** Si votre organisation relit les projets, le projet attend la validation des
   animateurs : revenez quand il est validé, l'IA reprend là. Sans relecture, le projet passe
   directement en réalisation.
3. **Écriture.** Dès que le projet est en réalisation, l'IA récupère d'elle-même le prompt de
   création du skill généré par Teamstarter, sans vous le demander, et confie l'écriture à
   `skill-creator`. Le skill porte l'id du projet dans ses métadonnées
   (`teamstarter-project-id`). Vous relisez le skill, demandez des corrections, puis le recevez en
   zip prêt à installer.
4. **Dépôt automatique.** Chaque version du skill est déposée sur le projet dès qu'elle est
   écrite, sans validation : la première, puis chaque correction, y compris celles faites plus
   tard avec `skill-creator` ou à la main (`ts-general-deposer-skill`). L'IA l'annonce en une
   ligne. Un fichier inchangé n'est pas redéposé : chaque dépôt crée pour les admins une tâche
   « partager ce fichier ».
5. **Étapes de réalisation.** L'IA coche avec votre accord « Créer mon agent IA », puis « Tester
   l'agent en conditions réelles » une fois le test concluant.
6. **Utilisation.** Chaque exécution du skill est déclarée à Teamstarter par
   `ts-general-declarer-execution-skill` : heure, durée, tokens (estimés quand l'outil ne les
   affiche pas) et personne qui l'utilise. Les statistiques sont dans la carte « Utilisation du
   skill » de la page `/manage` du projet, réservée aux porteurs et aux admins, et l'IA les lit
   sur demande (« combien de fois mon skill a été utilisé ? »).
7. **Blocage.** Un problème qui empêche de créer ou d'utiliser le skill devient, avec votre accord,
   un point de blocage sur le projet (`ts-general-declarer-blocage`, ci-dessous).

Le prompt de création, le dépôt du skill, la validation des étapes et la déclaration des
utilisations demandent des outils du connecteur que votre accès n'a peut-être pas encore. Sans
eux, l'IA vous dit quoi faire dans l'app : copier le prompt, déposer le fichier, cocher l'étape.
Sans eux, les utilisations ne sont pas comptées.

Pour que ces appels se fassent sans clic, autorisez une fois pour toutes les outils
`get-skill-creation-instructions` et `upload-project-skill` du connecteur : « Toujours autoriser »
quand l'outil IA le demande (claude.ai, Cowork), ou une règle d'autorisation dans `/permissions`
(Claude Code).

### Remonter les blocages d'un projet

Une fois un projet validé et en réalisation (`CASHEDOUT`) ou mis en place (`DELIVERED`), ses
problèmes se déclarent comme **blocages** du projet, quel que soit son type :
`ts-general-declarer-blocage`.

1. **Proposition.** Dès qu'un problème que vous ne pouvez pas lever seul empêche d'avancer
   (accès refusé, outil indisponible, donnée manquante, règle de sécurité, budget, prestataire,
   décision ou participation qui manque), l'IA propose de le déclarer, une fois par problème.
   Elle le fait d'elle-même quand l'exécution d'un skill de projet échoue sur un tel problème.
   Une erreur corrigée dans la conversation, ou qu'un nouvel essai règle, n'est pas un blocage.
2. **Pas de doublon.** L'IA lit les blocages du projet : si le même problème est déjà ouvert,
   elle propose d'y ajouter un commentaire ; s'il a été résolu et revient, de le rouvrir.
3. **Rédaction.** Un titre (120 caractères au plus), une catégorie (outil, accès, sécurité,
   budget, organisation, participation des collègues, prestataire, autre) et une description :
   ce qui bloque, ce qui a été essayé, le contournement en attendant, qui peut débloquer. Rien de
   confidentiel. → **Validation**, puis déclaration.
4. **Suite.** Personne n'est prévenu tout de suite : le blocage apparaît dans la section
   « Blocages » de la page `/manage` du projet et dans la page « Blocages » des admins, et devient
   une tâche des admins de l'organisation. L'IA liste ensuite les blocages d'un projet, lit
   l'échange avec les admins, commente, marque un blocage résolu ou le rouvre, chaque fois avec
   votre accord.

Seuls les porteurs du projet et les admins de l'organisation lisent et déclarent ses blocages.
`ts-general-lister-projets` affiche le nombre de blocages ouverts des projets en réalisation.

### Lister les idées d'automatisation

`ts-general-lister-idees-automatisation` lit les idées de la boîte à idées et des ateliers dont le
type est « Automatisation de processus avec l'IA » ou « AI Skill » : celles à prendre, les plus
récentes d'abord, avec leur auteur, leurs réactions et leurs commentaires, puis celles déjà
lancées, avec le projet qui les porte. Sur demande, il cherche aussi parmi les idées déposées sans
type celles qui parlent d'automatisation, à confirmer. Il propose ensuite de créer le skill d'une
idée avec `ts-general-creer-skill`. Lecture seule.

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

### Cartographier ses rôles, processus et tâches (RPT)

Le référentiel RPT d'une organisation décrit ses **rôles**, ses **processus** et ses **tâches**.
Pour chaque tâche, il dit si elle est automatisée, assistée par une IA, faite à la main ou
décidée par une personne, quelles données elle utilise et ce qui la bloque. Il sert à choisir ce
qui peut être confié ensuite à un agent IA, et les connecteurs à activer pour qu'il ait ces
données.

Les skills RPT ne passent pas par le connecteur Teamstarter. Ils ne contiennent aucune donnée
d'une organisation : ils lisent son fichier `rpt-config.yaml` (nom, langue, dossiers du
référentiel et de réception, équipes, responsables, ce qui n'est jamais envoyé), dont l'adresse
est dans les instructions de Claude de l'organisation.

1. **Mise en place, une fois** : `ts-general-rpt-setup` écrit `rpt-config.yaml` avec la personne
   qui met RPT en place, le dépose à la racine du dossier de l'OS de l'organisation, et donne le
   texte à coller dans les instructions de Claude (le contexte global de l'organisation).
2. **Cartographie** : `ts-general-check-process-cartography` lit, avec votre accord, ce que vos
   connecteurs montrent de votre travail (agenda, e-mails envoyés, documents, tickets), vous
   interroge, vous fait valider la carte, la vérifie avec un script, vous montre un aperçu de tout
   ce qui sera envoyé, puis, après votre accord, la dépose dans le dossier de réception (Google
   Drive) ou l'envoie à l'adresse de réception. `ts-general-data-crawl` fait de même pour la
   carte des données : noms de dossiers, fichiers, tables, canaux, leur taille et leur date de
   mise à jour, jamais leur contenu.
3. **Au fil du travail** : à la fin d'une tâche faite avec Claude, `ts-general-rpt-file` range le
   livrable à l'endroit que dit la fiche de la tâche, et `ts-general-rpt-observe` propose la mise
   à jour de la fiche quand la session a appris ce qu'elle ne dit pas.

La personne ou l'équipe qui tient le référentiel fusionne ensuite les cartes et les observations
reçues ; cette fusion ne se fait pas avec le plugin. Les consignes des skills RPT sont écrites en
anglais ; l'IA vous parle dans votre langue, et la carte est écrite dans la langue de
l'organisation.

### Garde-fous

- **Rien n'est écrit sans votre accord** : chaque écriture suit une validation, et la proposition
  du projet demande une confirmation explicite. Deux exceptions, annoncées dans la réponse : le
  dépôt de chaque version d'un skill de projet sur son projet, et la déclaration de chacune de
  ses utilisations.
- **Rien n'est inventé** : date, lieu, montant, prestataire, co-porteur. L'IA vous les demande,
  ou écrit « à préciser » en vous le disant.
- Une réponse ou une section n'est jamais réécrite sans vous le dire, et seulement celle que vous
  avez demandée.
- Un projet proposé n'est jamais repassé en brouillon sans votre demande.
- **RPT : rien ne part sans aperçu ni accord.** Une carte, une observation ou un fichier rangé
  n'est envoyé, créé ou déplacé qu'après votre validation de ce qui sera envoyé. La carte des
  données ne lit que des noms et des métadonnées : aucun contenu de document, aucun message, aucun
  nom de client, aucun montant.

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
- **Les skills RPT** demandent que RPT soit mis en place dans l'organisation
  (`ts-general-rpt-setup`, puis le texte qu'il donne collé dans les instructions de Claude), les
  connecteurs des outils où vous travaillez (Google Drive pour déposer la carte ; Gmail, Slack,
  Notion, HubSpot, Jira selon les cas), et l'exécution de code avec Python 3 et PyYAML pour leurs
  scripts de vérification. Sans connecteur Google Drive ni outil d'envoi d'e-mail, la carte vous
  est donnée en fichier, à déposer vous-même.

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
| Skill RPT sans adresse de `rpt-config.yaml` dans les instructions de Claude | Cherche le fichier dans Google Drive et vous le fait confirmer ; sinon vous demande de l'ajouter à la conversation. Sans ce fichier nulle part, RPT n'est pas encore mis en place : `ts-general-rpt-setup`. |

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
│       ├── ts-general-creer-skill/     # créer un skill par un projet : prompt, écriture, test, blocages
│       ├── ts-general-deposer-skill/   # déposer chaque version d'un skill de projet, automatiquement
│       ├── ts-general-declarer-execution-skill/  # déclarer chaque utilisation d'un skill de projet
│       ├── ts-general-declarer-blocage/  # blocages d'un projet en réalisation : déclarer, suivre, résoudre
│       ├── ts-general-lister-idees-automatisation/  # idées d'automatisation : à prendre, lancées
│       ├── ts-general-rpt-setup/                    # RPT : écrire le rpt-config.yaml de l'organisation
│       ├── ts-general-check-process-cartography/   # RPT : carte des rôles, processus et tâches
│       ├── ts-general-data-crawl/                   # RPT : carte des données, outil par outil
│       ├── ts-general-rpt-observe/                  # RPT : proposer la mise à jour d'une fiche de tâche
│       └── ts-general-rpt-file/                     # RPT : ranger le livrable d'une tâche
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

1. Écrire dans le dossier du skill. Règles de forme : frontmatter limité aux clés du format
   agentskills.io (`name`, `description`, et au besoin `metadata`, `license`, `compatibility`,
   `allowed-tools` ; l'import claude.ai refuse les autres), `name` = nom du dossier, format
   `ts-<domaine>-<verbe>-<objet>`, description de 1024 caractères au plus, sans chevrons, avec les
   phrases qui déclenchent le skill. Corps adressé au modèle, à l'infinitif.
2. Un fichier utile à plusieurs skills est copié dans chacun (un skill doit pouvoir être téléversé
   seul). La source et ses copies sont listées dans `SHARED` du script ; modifier la source, puis
   `python3 scripts/check_plugins.py --sync`. Aujourd'hui : `regles-api.md`, dont la source est
   dans `ts-general-creer-projet`.
3. `python3 scripts/check_plugins.py` doit répondre `OK`.
4. Monter la version dans `plugin.json` et dans `marketplace.json`.

### Mettre à jour les skills RPT

Les cinq skills RPT ne s'écrivent pas ici. Leur source est dans le dépôt `teamstarter`,
`teamstarter-os/skills/<skill>/`, et `teamstarter-os/tools/package_rpt_skill.py` y ajoute leurs
scripts et catalogues génériques ; leur version et leur source sont dans le `metadata` de leur
frontmatter. Une modification faite ici serait écrasée à la copie suivante. Pour les mettre à
jour :

1. Dans le dépôt `teamstarter` :
   `python3 teamstarter-os/tools/package_rpt_skill.py --marketplace <clone de ce dépôt>`
   remplace chaque `teamstarter-core/skills/<skill>/` déjà présent ici par le dossier empaqueté,
   et laisse de côté un skill RPT que le plugin ne déclare pas encore (l'ajouter est une
   décision prise ici, avec le tableau des skills de ce README).
2. `python3 scripts/check_plugins.py`, puis monter la version du plugin (dernier chiffre pour de
   nouvelles versions de skills déjà déclarés) dans `plugin.json` et `marketplace.json`.

Une PR qui ne fait que cela (nouvelles versions de skills déjà déclarés, version du plugin) est
mergée par la session qui l'ouvre, sans validation (Vincent, 2026-10-19). Un skill ajouté ou
retiré, ou un changement de la description du plugin, passe par une revue.

Pas de hook ni de dossier `bin/` : le chat claude.ai et ChatGPT ne les exécutent pas, et
claude.ai refuse un plugin qui a un `bin/` à sa racine. Le script le vérifie.
