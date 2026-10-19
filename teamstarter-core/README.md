# Teamstarter

Créez et suivez vos projets Teamstarter depuis votre conversation avec Claude. Le plugin
s'adresse à tout collaborateur d'une organisation qui utilise
[Teamstarter](https://teamstarter.co), la plateforme d'innovation collaborative : projets,
objectifs, idées, ateliers.

Teamstarter reste la source de vérité. Statuts, réponses et fiches sont écrits dans
Teamstarter, jamais seulement dans la conversation : un brouillon commencé dans l'app se reprend
avec Claude, et inversement.

## Ce que fait le plugin

| Skill | Pour | Exemples de demandes |
|---|---|---|
| `ts-general-creer-projet` | Créer un projet de n'importe quel type (événement, automatisation avec l'IA, autre) jusqu'à sa proposition, ou reprendre un brouillon là où il s'est arrêté | « J'ai une idée de projet », « Reprends mon brouillon », « Soumets mon projet » |
| `ts-general-lister-projets` | Voir ses projets regroupés par statut, avec l'étape suivante de chacun | « Où en sont mes projets ? », « Mes brouillons » |
| `ts-general-creer-skill` | Créer un skill (un agent IA) par un projet « Automatisation de processus avec l'IA » : projet, validation, écriture du skill, dépôt de chaque version, test, points de blocage | « Je veux créer un skill », « Reprends mon skill », « Mon skill est bloqué » |
| `ts-general-declarer-execution-skill` | Déclarer à Teamstarter chaque utilisation d'un skill rattaché à un projet | se déclenche seul, à la fin de l'exécution d'un tel skill |
| `ts-general-lister-idees-automatisation` | Voir les idées d'automatisation de la boîte à idées : à prendre, déjà lancées ; créer le skill de l'une d'elles | « Quelles idées d'automatisation ont été proposées ? », « Trouve-moi une idée de skill » |

**Créer un projet** suit le parcours de l'app : choix du type et de l'objectif, recherche des
projets et idées proches, création du brouillon, questions de structuration, fiche du projet
(générée par Teamstarter ou rédigée dans la conversation), audit du cadre quand l'organisation
l'a activé, puis proposition du projet. Vous pouvez vous arrêter à chaque étape et reprendre plus
tard.

**Créer un skill** passe par un projet de création de skill, dont le titre est la tâche à
automatiser et dont les questions sont posées avec leur libellé exact : il est créé et proposé,
puis, une fois validé par
l'organisation, Claude écrit le skill à partir du prompt de création généré par Teamstarter (avec
le skill `skill-creator` d'Anthropic), le dépose sur le projet, coche les étapes « Créer mon agent
IA » et « Tester l'agent en conditions réelles » avec votre accord, et déclare les points de
blocage. Le skill porte l'id de son projet dans ses métadonnées ; chacune de ses utilisations est
ensuite déclarée à Teamstarter ; les statistiques sont dans la carte « Utilisation du skill » de
la page de gestion du projet.

**Lister les idées d'automatisation** montre celles de la boîte à idées et des ateliers, à prendre
ou déjà lancées, et propose de créer le skill de l'une d'elles.

**Lister ses projets** les regroupe comme la page « Mes projets » de l'app, et propose de
reprendre un brouillon.

## Ce dont vous avez besoin

- Un compte Teamstarter dans une organisation hébergée sur `app.teamstarter.co`.
- Connecter le connecteur Teamstarter une fois, avec ce compte : la page de consentement fait
  choisir l'organisation et l'accès (lecture, ou lecture et écriture).
- Pour créer un projet, l'accès en écriture, que l'administrateur de votre organisation doit
  avoir ouvert. En lecture seule, la liste des projets fonctionne, et la création produit une
  fiche en Markdown à recopier dans l'app.

## Ce que le plugin lit, écrit et exécute

- **Un seul service contacté** : le serveur MCP Teamstarter, `https://app.teamstarter.co/mcp`
  (HTTP, authentification OAuth avec votre compte Teamstarter). Le plugin n'envoie de données à
  aucun autre service.
- **Lecture** dans votre organisation Teamstarter : types de projet, objectifs, projets, idées,
  questions et sections de vos projets, et les noms des collaborateurs, pour retrouver un
  co-porteur ou vous identifier.
- **Écriture**, seulement après votre validation dans la conversation : création et mise à jour
  de vos projets, réponses aux questions de structuration, lignes de dépense, co-porteurs (qui
  reçoivent une notification de Teamstarter), statut du projet, dépôt du fichier d'un skill sur
  son projet, validation des étapes « Créer mon agent IA » et « Tester l'agent en conditions
  réelles », points de blocage. La proposition d'un projet demande une confirmation explicite.
  Lister ses projets n'écrit rien.
- **Déclaration d'utilisation**, sans validation à chaque fois : à la fin de chaque exécution d'un
  skill qui porte l'id d'un projet Teamstarter, `ts-general-declarer-execution-skill` envoie à
  Teamstarter l'id du projet, l'heure, la durée, les tokens (estimés quand l'outil ne les affiche
  pas) et le résultat ; la personne enregistrée est celle du connecteur. La déclaration est
  annoncée dans la réponse. Rien n'est déclaré pour un autre skill.
- **Script local** : `skills/ts-general-creer-projet/scripts/tiptap.py` convertit du Markdown
  simple en document tiptap, le format des sections de fiche de Teamstarter. Il tourne sur la
  machine, sans accès réseau. Sans Python, Claude construit ce document lui-même.
- **Fichiers locaux** : sans connecteur ou en lecture seule, la création livre un fichier
  `fiche-projet-<titre>.md` dans la conversation ; la création d'un skill livre le dossier du
  skill et son zip, prêts à installer.
- Le plugin ne stocke rien en dehors de Teamstarter : aucune mémoire, aucun cache.

## Garde-fous

- Rien n'est écrit dans Teamstarter sans votre accord, sauf la déclaration d'utilisation d'un
  skill de projet, annoncée à chaque fois.
- Aucune version d'un skill n'est déposée sans que vous l'ayez validée.
- Rien n'est inventé : date, lieu, montant, prestataire, co-porteur sont demandés, ou notés « à
  préciser ».
- Une réponse ou une section n'est jamais réécrite sans vous le dire.
- Pas de donnée personnelle ni de nom de client dans la fiche d'un projet d'automatisation.

## Support

Teamstarter, [product@teamstarter.co](mailto:product@teamstarter.co).

## Licence

Voir [LICENSE](LICENSE).
