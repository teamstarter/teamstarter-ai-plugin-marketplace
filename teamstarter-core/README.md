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
| `ts-general-creer-skill` | Créer un skill (un agent IA) par un projet « Automatisation de processus avec l'IA » : projet, validation, prompt de création récupéré automatiquement, écriture du skill, test, points de blocage | « Je veux créer un skill », « Crée le skill de mon projet », « Reprends mon skill », « Mon skill est bloqué » |
| `ts-general-deposer-skill` | Déposer sur son projet chaque version d'un skill rattaché à un projet | se déclenche seul, à chaque écriture ou modification du `SKILL.md` d'un tel skill |
| `ts-general-declarer-execution-skill` | Déclarer à Teamstarter chaque utilisation d'un skill rattaché à un projet | se déclenche seul, à la fin de l'exécution d'un tel skill |
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

**Créer un skill** passe par un projet de création de skill, dont le titre est la tâche à
automatiser et dont les questions sont posées avec leur libellé exact : il est créé et proposé,
puis, une fois validé par
l'organisation, Claude récupère de lui-même le prompt de création généré par Teamstarter, écrit le
skill (avec le skill `skill-creator` d'Anthropic), dépose automatiquement chaque version sur le
projet, coche les étapes « Créer mon agent IA » et « Tester l'agent en conditions réelles » avec
votre accord, et déclare les points de blocage. Le skill porte l'id de son projet dans ses métadonnées ; chacune de ses utilisations est
ensuite déclarée à Teamstarter ; les statistiques sont dans la carte « Utilisation du skill » de
la page de gestion du projet.

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
- Pour que le prompt de création et le dépôt du skill se fassent sans clic : « Toujours
  autoriser » les outils `get-skill-creation-instructions` et `upload-project-skill` du
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
  questions et sections de vos projets, et les noms des collaborateurs, pour retrouver un
  co-porteur ou vous identifier.
- **Écriture**, seulement après votre validation dans la conversation : création et mise à jour
  de vos projets, réponses aux questions de structuration, lignes de dépense, co-porteurs (qui
  reçoivent une notification de Teamstarter), statut du projet, validation des étapes « Créer mon
  agent IA » et « Tester l'agent en conditions réelles », points de blocage. La proposition d'un projet demande une confirmation explicite.
  Lister ses projets n'écrit rien.
- **Dépôt du skill**, sans validation à chaque fois : à chaque écriture ou modification du
  `SKILL.md` d'un skill qui porte l'id d'un projet Teamstarter, `ts-general-deposer-skill` dépose
  ce fichier sur le projet, au nom de la personne du connecteur, qui doit être porteuse du
  projet. Chaque dépôt crée pour les admins de l'organisation une tâche « partager ce fichier » ;
  un fichier inchangé n'est pas redéposé. Le dépôt est annoncé dans la réponse.
- **Déclaration d'utilisation**, sans validation à chaque fois : à la fin de chaque exécution d'un
  skill qui porte l'id d'un projet Teamstarter, `ts-general-declarer-execution-skill` envoie à
  Teamstarter l'id du projet, l'heure, la durée, les tokens (estimés quand l'outil ne les affiche
  pas) et le résultat ; la personne enregistrée est celle du connecteur. La déclaration est
  annoncée dans la réponse. Rien n'est déclaré pour un autre skill.
- **Scripts locaux**, sans accès réseau :
  - `skills/ts-general-creer-projet/scripts/tiptap.py` convertit du Markdown simple en document
    tiptap, le format des sections de fiche de Teamstarter. Sans Python, Claude construit ce
    document lui-même ;
  - dans les skills RPT, `scripts/build_rpt.py` et `validate_rpt.py` vérifient une carte, une
    observation ou un `rpt-config.yaml`, `preview_rpt.py` produit l'aperçu de ce qui sera envoyé
    et signale les données personnelles, `check_datamap.py` vérifie la carte des données,
    `rpt_i18n.py` porte leurs messages. Ils demandent Python 3 et PyYAML.
- **Fichiers locaux** : sans connecteur ou en lecture seule, la création livre un fichier
  `fiche-projet-<titre>.md` dans la conversation ; la création d'un skill livre le dossier du
  skill et son zip, prêts à installer.
- Le plugin ne garde rien de son côté : aucune mémoire, aucun cache. Les skills de projet
  écrivent dans Teamstarter ; les skills RPT, dans les dossiers de l'organisation que nomme son
  `rpt-config.yaml`.

## Garde-fous

- Rien n'est écrit dans Teamstarter sans votre accord, sauf le dépôt de chaque version d'un skill
  de projet et la déclaration de ses utilisations, annoncés à chaque fois.
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
