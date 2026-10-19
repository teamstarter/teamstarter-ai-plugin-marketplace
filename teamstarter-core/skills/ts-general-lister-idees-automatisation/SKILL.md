---
name: ts-general-lister-idees-automatisation
description: >-
  Liste les idées d'automatisation déposées dans Teamstarter via le connecteur MCP Teamstarter :
  les idées de la boîte à idées et des ateliers dont le type est « Automatisation de processus
  avec l'IA » ou « AI Skill », celles à prendre et celles déjà lancées en projet, avec leur
  auteur, leurs réactions et le projet lancé. Propose ensuite de créer le skill d'une idée avec
  ts-general-creer-skill. Lecture seule. Déclenche SYSTÉMATIQUEMENT dès que l'utilisateur
  mentionne "idées d'automatisation", "idées de skill", "idées d'agent IA", "quelles tâches
  automatiser", "qu'est-ce que les collègues veulent automatiser", "idées IA de la boîte à
  idées", "trouver une idée de skill", "une idée à automatiser". Ne pas déclencher pour créer un
  skill (ts-general-creer-skill) ni pour lister ses projets (ts-general-lister-projets).
---

# Lister les idées d'automatisation de Teamstarter

## Quand utiliser ce skill

Un collaborateur cherche une tâche à automatiser, veut savoir ce que ses collègues aimeraient
voir automatisé, ou vérifier qu'une idée n'est pas déjà portée par un projet. Dans Teamstarter,
une idée déposée dans la boîte à idées ou pendant un atelier peut porter un type de projet : les
idées d'automatisation sont celles dont le type est « Automatisation de processus avec l'IA »
(`PROCESS_AUTOMATION_WITH_AI`) ou « AI Skill » (`AI_SKILL`). Le skill les lit sur la plateforme,
sépare celles à prendre de celles déjà lancées en projet, et propose de créer le skill de l'une
d'elles.

Ne pas utiliser pour créer le skill (`ts-general-creer-skill`) ni pour voir ses propres projets
(`ts-general-lister-projets`).

## Sortie attendue

1. Les idées **à prendre** (pas encore lancées), les plus récentes d'abord.
2. Les idées **déjà lancées**, avec le projet qui les porte.
3. Sur demande, les idées **sans type** qui parlent d'automatisation, à confirmer.

Pour chaque idée : titre, `#id`, auteur (ou « anonyme »), date, réactions et commentaires, une
ligne de description. Puis une question : créer le skill d'une idée, ou rien.

## Vue d'ensemble du workflow

```
[0] Connecteur (lecture suffit)
[1] Les types d'automatisation de l'organisation
[2] Les idées de ces types : à prendre, déjà lancées
[3] Sur demande : les idées sans type qui parlent d'automatisation
[4] Présenter
[5] Créer le skill d'une idée → ts-general-creer-skill
```

Lire `references/regles-api.md` avant le premier appel.

---

## Étape 0 — Connecteur

Trouver le connecteur Teamstarter (plusieurs : demander lequel). `list-schema` suffit à vérifier
que `idea`, `ideaCount` et `projectType` sont lisibles. Un accès multi-organisations (staff) :
demander l'organisation et passer son `organizationTag`.

## Étape 1 — Les types d'automatisation

```graphql
query($where: SequelizeJSON) { projectType(where: $where) { id tag isDisabled titleWordings { value } } }
```
variables : `{"where": {"tag": {"in": ["PROCESS_AUTOMATION_WITH_AI", "AI_SKILL"]}}}`

Garder les ids. Les ids changent d'une organisation à l'autre : ne jamais les coder en dur. Un type
`isDisabled` : lister quand même ses idées, en disant que le type n'est plus proposé pour créer un
projet. Aucun des deux types : le dire, et passer à l'étape 3.

## Étape 2 — Les idées de ces types

```graphql
query($where: SequelizeJSON) {
  toTakeCount: ideaCount(where: $where, isLaunched: false)
  launchedCount: ideaCount(where: $where, isLaunched: true)
  toTake: idea(where: $where, isLaunched: false, limit: 50) {
    id projectTypeId createdAt isAnonymized d_likesCount d_commentsCount workshopId
    titleWordings { value language } descriptionWordings { value language }
    author { fullname }
  }
  launched: idea(where: $where, isLaunched: true, limit: 50) {
    id projectTypeId createdAt isAnonymized d_lastProjectId
    titleWordings { value language }
    author { fullname }
  }
}
```
variables : `{"where": {"projectTypeId": {"in": [<ids de l'étape 1>]}}}`

- **`isLaunched` est un argument de la liste**, à côté de `where`, pas une clé de `where` : dans
  `where`, l'appel échoue avec l'erreur générique « Désolé, une erreur est apparue ». Une idée est
  lancée quand un projet de l'organisation a été créé depuis elle et n'est ni supprimé ni annulé.
- **50 lignes au plus par appel**, sans erreur : les totaux viennent de `ideaCount`. Au-delà de
  50, paginer avec `offset`, et dire combien il en reste.
- **L'ordre** : le serveur ignore `order`, sauf `"id"`, `"reverse:id"` et `"author.fullname"`.
  Trier soi-même par `createdAt`, la plus récente d'abord.
- **Le texte** est dans `titleWordings[].value.value` et `descriptionWordings[].value.value`, une
  entrée par langue : prendre celle de la langue de l'utilisateur (`language`), sinon la
  première.
- **Une idée anonyme** (`isAnonymized: true`) n'a pas d'auteur : écrire « anonyme », ne pas le
  chercher.
- `d_lastProjectId` donne le projet lancé depuis l'idée ; le lire si l'utilisateur veut son statut :
  `project(where: {"id": <id>}) { id title status }`.
- Filtres possibles, sur demande : `workshopId` (les idées d'un atelier), et sur l'auteur
  `departmentId`, `locationId`, `groupId`. Un filtre sur l'auteur écarte les idées anonymes : le
  dire.

## Étape 3 — Les idées sans type (sur demande)

Une idée déposée sans type, ou avant que le type existe, n'a pas de `projectTypeId` : elle
n'apparaît pas à l'étape 2. Quand l'utilisateur veut tout voir, ou quand l'étape 2 est vide :

```graphql
query($where: SequelizeJSON, $offset: Int) {
  count: ideaCount(where: $where, isLaunched: false)
  idea(where: $where, isLaunched: false, limit: 50, offset: $offset) {
    id createdAt isAnonymized d_likesCount titleWordings { value language } descriptionWordings { value language } author { fullname }
  }
}
```
variables : `{"where": {"projectTypeId": null}, "offset": 0}` ; tant que `offset` + 50 < `count`,
relire avec `offset` augmenté de 50. Les idées sans type peuvent être bien plus nombreuses que
celles de l'étape 2.

Garder celles dont le titre ou la description parle d'automatiser une tâche (automatiser, IA,
agent, assistant, skill, GPT, Copilot, Claude, « gagner du temps sur »). Les présenter à part,
comme « sans type, à confirmer » : c'est une lecture du texte, pas une donnée de Teamstarter.

## Étape 4 — Présenter

Deux tableaux, dans cet ordre, puis le troisième s'il a été demandé :

| Tableau | Colonnes |
|---|---|
| Idées à prendre (`toTakeCount`) | idée (titre), `#id`, type, auteur, déposée le, 👍 `d_likesCount`, 💬 `d_commentsCount`, description en une ligne (120 caractères) |
| Idées déjà lancées (`launchedCount`) | idée, `#id`, auteur, projet lancé `#d_lastProjectId` |
| Sans type, à confirmer | idée, `#id`, auteur, déposée le, description en une ligne |

- Donner les totaux, et dire quand une liste est tronquée.
- Une liste vide ne veut pas dire que personne n'a d'idée d'automatisation : les idées sans type
  n'y sont pas (étape 3).
- Lien vers la boîte à idées quand l'adresse de l'app est connue :
  `<adresse de l'app>/<tag de l'organisation>/projects-ideas-box`.

## Étape 5 — Créer le skill d'une idée

Proposer de créer le skill d'une idée à prendre (« Je crée le skill de laquelle ? »). Sur choix de
l'utilisateur, passer la main à `ts-general-creer-skill` avec l'id de l'idée : il crée le projet
de création de skill depuis l'idée, qui affiche ensuite le projet lancé.

Une idée déjà lancée : ne pas en créer un second projet ; proposer de rejoindre le projet existant
(`d_lastProjectId`), ou de le reprendre avec `ts-general-creer-skill` si l'utilisateur en est
porteur.

## Garde-fous

- **Lecture seule** : ce skill n'appelle jamais `run-mutation`.
- **Ne pas présenter une liste partielle comme complète** : liste plafonnée à 50, idées sans type,
  filtre sur l'auteur qui écarte les idées anonymes — le dire.
- **Ne pas chercher l'auteur d'une idée anonyme.**
- Une idée « sans type, à confirmer » n'est pas une idée d'automatisation tant que l'utilisateur
  ne l'a pas dit.

## Tags de sécurité

aucun : lecture seule, pas de fichier produit.

## Fallback

- **Pas de connecteur** : dire que le connecteur Teamstarter n'est pas connecté. Il se connecte
  depuis l'onglet Connecteurs du plugin Teamstarter (ou les paramètres des connecteurs de l'outil
  IA), avec le compte Teamstarter de l'utilisateur. En attendant, renvoyer vers la boîte à idées
  de l'app.
- **`projectTypeId` refusé par le serveur** (version ancienne) : lire les 50 idées les plus
  récentes et faire l'étape 3 sur toutes.
- **`isLaunched` refusé** : lire les idées sans cet argument, et séparer soi-même avec
  `d_lastProjectId` (vide = à prendre), en disant qu'un projet annulé compte alors comme lancé.

## Ressources

- `references/regles-api.md` — règles du connecteur, identité de l'utilisateur, liens vers l'app
  (même fichier que dans `ts-general-creer-projet`).
- Skills voisins : `ts-general-creer-skill` (créer le skill d'une idée),
  `ts-general-lister-projets` (voir ses projets).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-lister-idees-automatisation` — domaine
`general`, verbe `lister`, objet `idees-automatisation`.
