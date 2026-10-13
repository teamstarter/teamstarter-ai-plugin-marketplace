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

**Créer un projet** suit le parcours de l'app : choix du type et de l'objectif, recherche des
projets et idées proches, création du brouillon, questions de structuration, fiche du projet
(générée par Teamstarter ou rédigée dans la conversation), audit du cadre quand l'organisation
l'a activé, puis proposition du projet. Vous pouvez vous arrêter à chaque étape et reprendre plus
tard.

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
  reçoivent une notification de Teamstarter), statut du projet. La proposition d'un projet
  demande une confirmation explicite. Lister ses projets n'écrit rien.
- **Script local** : `skills/ts-general-creer-projet/scripts/tiptap.py` convertit du Markdown
  simple en document tiptap, le format des sections de fiche de Teamstarter. Il tourne sur la
  machine, sans accès réseau. Sans Python, Claude construit ce document lui-même.
- **Fichier local** : sans connecteur ou en lecture seule, la création livre un fichier
  `fiche-projet-<titre>.md` dans la conversation.
- Le plugin ne stocke rien en dehors de Teamstarter : aucune mémoire, aucun cache.

## Garde-fous

- Rien n'est écrit dans Teamstarter sans votre accord.
- Rien n'est inventé : date, lieu, montant, prestataire, co-porteur sont demandés, ou notés « à
  préciser ».
- Une réponse ou une section n'est jamais réécrite sans vous le dire.
- Pas de donnée personnelle ni de nom de client dans la fiche d'un projet d'automatisation.

## Support

Teamstarter, [product@teamstarter.co](mailto:product@teamstarter.co).

## Licence

Voir [LICENSE](LICENSE).
