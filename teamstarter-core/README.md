# Teamstarter

Créez et suivez vos projets Teamstarter depuis votre conversation avec Claude. Le plugin
s'adresse à tout collaborateur d'une organisation qui utilise
[Teamstarter](https://teamstarter.co), la plateforme d'innovation collaborative : projets,
objectifs, idées, ateliers.

Teamstarter reste la source de vérité. Statuts, réponses et fiches sont écrits dans
Teamstarter, jamais seulement dans la conversation : un brouillon commencé dans l'app se reprend
avec Claude, et inversement.

Le plugin contient aussi les skills RPT côté utilisateur : ils décrivent les rôles, processus et
tâches de votre organisation, avec ce qui en est automatisé ou peut être confié à l'IA.

## Ce que fait le plugin

| Skill | Pour | Exemples de demandes |
|---|---|---|
| `ts-general-creer-projet` | Créer un projet de n'importe quel type (événement, automatisation avec l'IA, autre) jusqu'à sa proposition, ou reprendre un brouillon là où il s'est arrêté | « J'ai une idée de projet », « Reprends mon brouillon », « Soumets mon projet » |
| `ts-general-lister-projets` | Voir ses projets regroupés par statut, avec l'étape suivante de chacun | « Où en sont mes projets ? », « Mes brouillons » |
| `ts-general-creer-skill` | Créer un skill (un agent IA) avec Teamstarter : comprendre la tâche, la structurer (une réponse proposée à chaque question, validée une à une), fiche et audit, validation, construction et tests selon le prompt de Teamstarter, présentation, première exécution | « Je veux créer un skill », « Crée le skill de mon projet », « Reprends mon skill », « Mon skill est bloqué » |
| `ts-general-deposer-skill` | Enregistrer dans Teamstarter chaque version d'un skill, en fichier `.skill` | se déclenche seul, à chaque écriture ou modification du `SKILL.md` d'un tel skill |
| `ts-general-declarer-execution-skill` | Déclarer à Teamstarter chaque utilisation d'un skill rattaché à un projet | se déclenche seul, à la fin de l'exécution d'un tel skill |
| `ts-general-declarer-blocage` | Remonter les blocages d'un projet en réalisation : proposé dès qu'un problème bloque (par exemple l'échec d'un skill de projet), validé, déclaré ; lister, commenter, résoudre | « Je suis bloqué sur mon projet », « Le blocage est levé » ; proposé seul quand un skill de projet échoue |
| `ts-general-lister-idees-automatisation` | Voir les idées d'automatisation de la boîte à idées : à prendre, déjà lancées ; créer le skill de l'une d'elles | « Quelles idées d'automatisation ont été proposées ? », « Trouve-moi une idée de skill » |
| `ts-general-rpt-setup` | RPT : mettre en place le référentiel dans l'organisation (son `rpt-config.yaml`), une fois | « Configure RPT pour ma boîte » |
| `ts-general-check-process-cartography` | RPT : cartographier ses rôles, processus et tâches, ou ceux de son équipe, et déposer la carte | « Fais la carte de mes rôles », « Qu'est-ce que je pourrais automatiser ? » |
| `ts-general-data-crawl` | RPT : décrire où sont les données de l'organisation, outil par outil, sans lire leur contenu | « Cartographie nos données », « Où est notre donnée ? » |
| `ts-general-rpt-observe` | RPT : à la fin d'une tâche faite avec Claude, proposer la mise à jour de sa fiche | « Mets à jour la fiche de cette tâche », « Ce bloqueur est levé » |
| `ts-general-rpt-file` | RPT : ranger le livrable d'une tâche là où sa fiche le dit | « Où je range ça ? » |

**Créer un projet** suit le parcours de l'app : choix du type et de l'objectif, recherche des
projets et idées proches, création du brouillon, questions de structuration, fiche du projet
(générée par Teamstarter ou rédigée dans la conversation), audit du cadre quand l'organisation
l'a activé, puis proposition du projet. Vous pouvez vous arrêter à chaque étape et reprendre plus
tard.

**Créer un skill** se fait en conversation, en parlant toujours de votre skill : Claude regarde
si une idée ou un skill proche existe déjà, présente les étapes, comprend la tâche (étapes,
sources de données, découpage en plusieurs skills), crée le skill dans Teamstarter, vous soumet
une à une ses réponses proposées aux questions de structuration, fait la fiche et l'audit,
l'envoie en validation ou passe directement à la création quand votre organisation ne modère
pas, construit et teste le skill en suivant le prompt de création de Teamstarter, l'enregistre
dans Teamstarter, vous le présente dans un schéma SVG (entrées, étapes, sorties) et propose une
première exécution. Il ne vous demande jamais de confirmer votre identité, et applique vos
corrections sans compte rendu. Chaque utilisation du skill est ensuite déclarée à Teamstarter ; les
statistiques sont dans la carte « Utilisation du skill » de sa page.

**Remonter les blocages** : sur un projet en réalisation ou mis en place, de n'importe quel type,
dès qu'un problème que vous ne pouvez pas lever seul empêche d'avancer, Claude propose de le
déclarer comme blocage du projet ; il le fait de lui-même quand l'exécution d'un skill de projet
échoue sur un tel problème. Il vérifie que le même blocage n'est pas déjà ouvert, rédige le
titre, la catégorie et la description, et ne déclare qu'après votre validation. Le blocage est
visible par les porteurs et les admins, et devient une tâche des admins ; personne n'est prévenu
au moment de la déclaration.

**Lister les idées d'automatisation** montre celles de la boîte à idées et des ateliers, à prendre
ou déjà lancées, et propose de créer le skill de l'une d'elles.

**Lister ses projets** les regroupe comme la page « Mes projets » de l'app, et propose de
reprendre un brouillon.

**Les skills RPT** tiennent à jour le référentiel des rôles, processus et tâches (RPT) de
l'organisation : pour chaque tâche, ce qui est automatisé, assisté par une IA, fait à la main ou
décidé par une personne, les données qu'elle utilise et ce qui la bloque. Ils ne passent pas par
le connecteur Teamstarter et ne contiennent aucune donnée d'une organisation : ils lisent son
`rpt-config.yaml`, dont l'adresse est dans les instructions de Claude de l'organisation.
`ts-general-rpt-setup` écrit ce fichier une fois. La cartographie lit, avec votre accord, ce que
vos connecteurs montrent de votre travail, vous interroge, vous montre un aperçu de ce qui sera
envoyé, puis dépose la carte dans le dossier de réception de l'organisation ; la personne qui
tient le référentiel la fusionne ensuite, hors du plugin.

## Ce dont vous avez besoin

- Un compte Teamstarter dans une organisation hébergée sur `app.teamstarter.co`.
- Connecter le connecteur Teamstarter une fois, avec ce compte : la page de consentement fait
  choisir l'organisation et l'accès (lecture, ou lecture et écriture).
- Pour créer un projet, l'accès en écriture, que l'administrateur de votre organisation doit
  avoir ouvert. En lecture seule, la liste des projets fonctionne, et la création produit une
  fiche en Markdown à recopier dans l'app.
- Pour que la création d'un skill se fasse sans clic : « Toujours autoriser » les outils
  `run-query`, `run-mutation`, `get-skill-creation-instructions` et `upload-project-skill` du
  connecteur quand l'outil IA le demande (claude.ai, Cowork), ou une règle dans `/permissions`
  (Claude Code).
- Pour les skills RPT : RPT mis en place dans l'organisation (`ts-general-rpt-setup`, puis le
  texte qu'il donne collé dans les instructions de Claude), les connecteurs des outils où vous
  travaillez (Google Drive pour déposer la carte), et l'exécution de code avec Python 3 et PyYAML.

## Ce que le plugin lit, écrit et exécute

- **Un seul serveur déclaré** : le serveur MCP Teamstarter, `https://app.teamstarter.co/mcp`
  (HTTP, authentification OAuth avec votre compte Teamstarter). Les skills de projet n'envoient
  de données à aucun autre service.
- **Skills RPT : vos autres connecteurs.** Ils n'utilisent pas le connecteur Teamstarter, mais
  ceux que vous avez déjà activés dans l'outil IA, avec votre compte et votre accord :
  - lecture, pour la cartographie : agenda, e-mails envoyés, documents, tickets, canaux, en
    n'en retenant que les types, les fréquences et les volumes, jamais le texte d'un message ni
    le nom ou l'adresse d'un destinataire ; pour la carte des données
    (`ts-general-data-crawl`), seulement des noms et des métadonnées (dossiers, fichiers, tables,
    canaux, taille, date de mise à jour), jamais le contenu ;
  - lecture du fichier `rpt-config.yaml` de l'organisation et des catalogues qu'il nomme ;
  - écriture, après un aperçu de tout ce qui sera envoyé et votre accord : la carte déposée dans
    le dossier de réception de l'organisation (Google Drive) ou envoyée par e-mail à son adresse
    de réception, une observation de fiche de tâche, un livrable rangé ou renommé,
    `rpt-config.yaml` déposé dans le dossier de l'OS.
- **Lecture** dans votre organisation Teamstarter : types de projet, objectifs, projets, idées,
  questions et sections de vos projets, blocages de vos projets et leurs commentaires, et les noms
  des collaborateurs, pour retrouver un co-porteur ou vous identifier.
- **Écriture**, après votre validation dans la conversation : création et mise à jour de vos
  projets, réponses aux questions de structuration, lignes de dépense, co-porteurs (qui
  reçoivent une notification de Teamstarter), statut du projet, blocages (déclaration,
  commentaire, résolution). La proposition d'un projet demande une confirmation explicite.
  Lister ses projets n'écrit rien.
- **Création d'un skill**, sans validation à chaque fois, parce que ces écritures font partie de
  la création : le skill est créé dans Teamstarter, chaque réponse que vous avez validée est
  écrite, la fiche et l'audit sont faits, le skill est envoyé en validation (ou passe
  directement en réalisation quand l'organisation ne modère pas), et les étapes « Créer mon
  agent IA » et « Tester l'agent en conditions réelles » sont cochées.
- **Enregistrement du skill**, sans validation à chaque fois : à chaque écriture ou modification
  d'un skill qui porte son id Teamstarter, `ts-general-deposer-skill` l'empaquette en
  `<nom-du-skill>.skill` (archive zip du dossier du skill) et le dépose, au nom de la personne du
  connecteur, qui doit être porteuse du skill. Chaque dépôt est une nouvelle version et crée pour
  les admins de l'organisation une tâche « partager ce fichier » ; un skill inchangé n'est pas
  redéposé.
- **Déclaration d'utilisation**, sans validation à chaque fois : à la fin de chaque exécution d'un
  skill qui porte l'id d'un projet Teamstarter, `ts-general-declarer-execution-skill` envoie à
  Teamstarter l'id du projet, l'heure, la durée, les tokens (estimés quand l'outil ne les affiche
  pas) et le résultat ; la personne enregistrée est celle du connecteur. La déclaration est
  annoncée dans la réponse. Rien n'est déclaré pour un autre skill.
- **Scripts locaux**, sans accès réseau :
  - `scripts/tiptap.py` (dans `ts-general-creer-projet` et `ts-general-creer-skill`) convertit
    du Markdown simple en document tiptap, le format des sections de fiche de Teamstarter. Sans
    Python, Claude construit ce document lui-même ;
  - `ts-general-deposer-skill` empaquette le skill en `.skill` avec un court script Python
    (bibliothèque standard) ;
  - `ts-general-creer-skill/scripts/schema_svg.py` dessine le schéma SVG du skill (entrées,
    étapes, sorties) à partir d'un fichier JSON (bibliothèque standard) ;
  - dans les skills RPT, `scripts/build_rpt.py` et `validate_rpt.py` vérifient une carte, une
    observation ou un `rpt-config.yaml`, `preview_rpt.py` produit l'aperçu de ce qui sera envoyé
    et signale les données personnelles, `check_datamap.py` vérifie la carte des données,
    `rpt_i18n.py` porte leurs messages. Ils demandent Python 3 et PyYAML.
- **Fichiers locaux** : sans connecteur ou en lecture seule, la création livre un fichier
  `fiche-projet-<titre>.md` dans la conversation ; la création d'un skill livre le dossier du
  skill et son fichier `.skill`, prêts à installer.
- Le plugin ne garde rien de son côté : aucune mémoire, aucun cache. Les skills de projet
  écrivent dans Teamstarter ; les skills RPT, dans les dossiers de l'organisation que nomme son
  `rpt-config.yaml`.

## Garde-fous

- Rien n'est écrit dans Teamstarter sans votre accord, sauf ce qui fait partie de la création
  d'un skill (création, fiche, audit, envoi en validation, enregistrement de chaque version,
  étapes cochées) et la déclaration de ses utilisations. Aucune réponse de structuration n'est
  écrite sans votre validation.
- Rien n'est inventé : date, lieu, montant, prestataire, co-porteur sont demandés, ou notés « à
  préciser ».
- Une réponse ou une section n'est jamais réécrite sans vous le dire.
- Pas de donnée personnelle ni de nom de client dans la fiche d'un projet d'automatisation.
- RPT : aucune carte, observation ou fichier n'est envoyé, créé ou déplacé sans un aperçu de ce
  qui part et votre accord.

## Support

Teamstarter, [product@teamstarter.co](mailto:product@teamstarter.co).

## Licence

Voir [LICENSE](LICENSE).
