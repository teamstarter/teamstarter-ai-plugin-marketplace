---
name: ts-general-creer-skill
description: >-
  Point d'entrée quand l'utilisateur veut créer un skill, un agent IA, ou automatiser une tâche
  avec Claude : porte la création dans un projet Teamstarter « Automatisation de processus avec
  l'IA » via le connecteur MCP Teamstarter. Crée et propose le projet (ts-general-creer-projet),
  attend sa validation, puis, une fois le projet en réalisation, récupère automatiquement le
  prompt de création, fait écrire le skill par skill-creator avec l'id du projet dans ses
  métadonnées, le dépose automatiquement dans Teamstarter à chaque version, valide l'étape
  « Créer mon agent IA », fait tester le skill, déclare les blocages et lit son usage. Déclenche
  SYSTÉMATIQUEMENT, avant skill-creator, dès que l'utilisateur mentionne "créer un skill",
  "nouveau skill", "créer un agent", "automatiser une tâche avec Claude", "crée le skill de mon
  projet", "reprendre mon skill", "modifier mon skill", "nouvelle version de mon skill", "mon
  skill est bloqué", "usage de mon skill". Pour seulement lister ses projets :
  ts-general-lister-projets.
---

# Créer un skill par un projet Teamstarter

## Quand utiliser ce skill

Un collaborateur veut un skill (un agent, un assistant) qui fait une tâche de son travail. Dans
son organisation, un skill est porté par un projet Teamstarter de type « Automatisation de
processus avec l'IA » (`PROCESS_AUTOMATION_WITH_AI`) : le projet décrit la tâche, passe par la
validation de l'organisation, puis la page de gestion du projet (`/manage`) suit la construction
de l'agent, son test, son usage et ses blocages.

Ce skill est le **point d'entrée** : il passe avant `skill-creator` et lui confie l'écriture du
skill une fois le projet validé. Il sert aussi à reprendre un skill commencé, à en déposer une
nouvelle version, ou à déclarer un blocage.

Ne pas utiliser pour un projet d'un autre type (`ts-general-creer-projet`), ni pour seulement
voir ses projets (`ts-general-lister-projets`).

## Sortie attendue

- un projet `PROCESS_AUTOMATION_WITH_AI` proposé, puis en réalisation (`CASHEDOUT`) ;
- un skill dont le `SKILL.md` porte l'id du projet dans ses métadonnées, déposé dans Teamstarter
  à chaque version sans validation, et livré à l'utilisateur en zip prêt à installer ;
- les étapes « Créer mon agent IA » et « Tester l'agent en conditions réelles » validées ;
- un point de blocage sur le projet pour chaque problème qui empêche de créer ou d'utiliser le
  skill.

## Vue d'ensemble

```
[0] Connecteur et capacités
[1] Nouveau skill ou reprise ─────────── reprise : aller à l'étape indiquée par l'état du projet
[2] Créer et proposer le projet           ←── validations de ts-general-creer-projet
[3] Attendre la validation : le projet doit être en CASHEDOUT
[4] Prompt de création du skill          ←── automatique, dès que le projet est en CASHEDOUT
[5] Écrire le skill (skill-creator)
[6] Déposer le skill dans Teamstarter      ←── automatique, à chaque version (ts-general-deposer-skill)
[7] Valider l'étape « Créer mon agent IA »
[8] Tester, valider « Tester l'agent en conditions réelles »
[U] Utilisation du skill, à tout moment après [6]
[B] Point de blocage, à tout moment après [3]   ←── validation
```

Chaque étape peut être la dernière de la conversation : l'état est dans Teamstarter, et le skill
repart de là (« reprends mon skill », « où en est mon skill »).

Lire `references/regles-api.md` avant le premier appel.

---

## Étape 0 — Connecteur et capacités

1. Trouver le connecteur Teamstarter (plusieurs : demander lequel). `list-schema` ; sans
   `run-mutation`, l'accès est en lecture seule → Fallback.
2. Noter ce que l'accès expose. Les trois tools de skill sont des tools du connecteur, listés à
   côté de `list-schema` ; la mutation est dans la réponse de `list-schema`.

| Capacité | Sert à | Absente |
|---|---|---|
| tool `get-skill-creation-instructions` | lire le prompt de création, sans demander (étape 4) | l'utilisateur copie le prompt depuis `/manage` |
| tool `upload-project-skill` | déposer chaque version, sans demander (étape 6, `ts-general-deposer-skill`) | l'utilisateur dépose le fichier dans `/manage` |
| tool `report-skill-execution` | déclarer chaque utilisation (skill `ts-general-declarer-execution-skill`) | les utilisations ne sont pas comptées |
| mutation `setProjectWorkflowActionStatus` | valider une étape de `/manage` (étapes 7 et 8) | l'utilisateur coche l'étape dans `/manage` |
| mutation `projectBlockerCreate` | déclarer un blocage | l'utilisateur le déclare dans `/manage` |
| query `projectSkillUsage` | lire l'utilisation du skill (étape U) | l'utilisateur ouvre la carte « Utilisation du skill » de `/manage` |

Dire en une phrase ce qui se fera dans l'app faute de capacité, une seule fois. Ne jamais
contourner un tool absent par `run-mutation` sur une mutation que `list-schema` ne montre pas.

## Étape 1 — Nouveau skill ou reprise

- **Le skill existe déjà** (l'utilisateur ouvre un `SKILL.md`, ou parle de « mon skill ») : lire
  `metadata.teamstarter-project-id` dans l'en-tête du `SKILL.md` ; c'est le projet.
- **Sinon**, retrouver ses projets d'automatisation : identité confirmée comme le dit
  `references/regles-api.md`, puis

```graphql
query($where: SequelizeJSON) {
  project(where: $where, order: "reverse:updatedAt", limit: 20) {
    id title status decisionMode updatedAt
    projectType { tag }
    skillFileId
    projectDeliveryActions { id type doneAt skippedAt }
  }
}
```
variables : `{"where": {"d_organizerIds": {"contains": [<moi>]}}}`, garder `projectType.tag` =
`PROCESS_AUTOMATION_WITH_AI`, ou `AI_SKILL` (l'autre type de projet d'agent IA, que les tools de
skill acceptent aussi). `skillFileId` nomme le dernier skill déposé ; vide, aucun ne l'est.
Un projet de création de skill pas encore proposé, sans identité confirmée : `scopeForMe: true` avec
`{"statusGroup": {"in": ["structuration", "writing"]}}`.

Proposer de reprendre un projet ou d'en créer un. L'utilisateur a nommé le projet (« crée le
skill de mon projet X »), ou un seul projet est en `CASHEDOUT` sans skill déposé : le reprendre
sans poser la question. L'utilisateur part d'une idée de la boîte à idées (skill
`ts-general-lister-idees-automatisation`) : garder son id pour l'étape 2. Pour reprendre, aller
à la première étape non faite :

| État relu | Reprendre à |
|---|---|
| `EMPTY` ou `DRAFT` | étape 2 (`ts-general-creer-projet` reprend le projet de création de skill) |
| `UNDER_REVIEW`, ou `PUBLISHED` (vote, financement) | étape 3 : en attente |
| `CASHEDOUT`, `skillFileId` vide | étape 4, aussitôt |
| `CASHEDOUT`, `skillFileId` renseigné, `create-my-agent` sans `doneAt` | étape 7 |
| `CASHEDOUT`, `create-my-agent` fait, `test-agent` sans `doneAt` | étape 8 |
| `CASHEDOUT` ou `DELIVERED`, tout fait | nouvelle version (étapes 5 et 6), utilisation (U) ou blocage (B), selon la demande |
| `CAMPAIGN_FAILED`, `CANCELLED`, `ENDED` | le dire ; un nouveau skill passe par un nouveau projet |

Dire en une phrase où en est le skill avant de continuer (« Ton projet *X* est validé et le skill
est déposé ; il reste à le tester. »).

## Étape 2 — Créer et proposer le projet

Suivre le skill `ts-general-creer-projet`, étapes 0 à 7, avec ces différences :

- **Type imposé** : `PROCESS_AUTOMATION_WITH_AI`. Ne pas proposer d'autre type. Absent ou
  `isDisabled` dans l'organisation : le dire, et proposer de créer le skill sans projet
  (Fallback).
- Lire la référence du type « Automatisation de processus avec l'IA » de `ts-general-creer-projet`
  pour les questions et la fiche.
- **Vocabulaire** : le projet est « ton projet de création de skill », jamais un « brouillon » ;
  son titre est « la tâche » à automatiser (un verbe à l'infinitif et son objet, 3 à 8 mots),
  demandée par « Quelle tâche veux-tu automatiser ? » et affichée sous l'étiquette « Tâche ».
- **Questions mot pour mot** : chaque question de structuration est posée avec son libellé exact
  dans Teamstarter, entre guillemets, sans reformulation. Ce que l'utilisateur a déjà dit de la
  tâche (étapes, outils, livrable, durée, fréquence) se montre sous la question
  (« Proposition : … ») ; il répond ou valide, et sa réponse s'écrit telle qu'il l'a donnée.
- **Depuis une idée** : passer son id à `ts-general-creer-projet` (sa création depuis une idée,
  `sourceIdeaId`) ; le projet est relié à l'idée, qui affiche alors le projet lancé.
- Les validations restent celles de `ts-general-creer-projet` ; la proposition (son étape 7)
  demande une confirmation explicite.

`ts-general-creer-projet` absent de la conversation : le dire (il fait partie du même plugin) et
s'arrêter.

## Étape 3 — Attendre la validation du projet

```graphql
query($where: SequelizeJSON) { project(where: $where) { id title status decisionMode underReviewAt cashedoutAt } }
```
variables : `{"where": {"id": <id>}}`

| `status` | Ce qui se passe | À dire |
|---|---|---|
| `UNDER_REVIEW` | l'organisation relit les projets : un animateur doit le valider | « Ton projet attend la validation des animateurs. Reviens me voir quand il est validé : je reprendrai à la création du skill. » Ne pas écrire le skill avant. |
| `CASHEDOUT` | le projet est validé et en réalisation (sans relecture, il y passe dès la proposition) | « Ton projet est validé : je récupère le prompt de création et j'écris le skill. » puis l'étape 4, sans attendre de réponse |
| `PUBLISHED` | le projet est soumis au vote ou en financement | attendre la fin de la campagne, comme pour `UNDER_REVIEW` |
| `DRAFT` après une proposition | les animateurs l'ont renvoyé avec un retour | lire les commentaires du projet, et reprendre avec `ts-general-creer-projet` pour en tenir compte |

Rien ne prévient Claude quand le statut change : c'est quand l'utilisateur revient que le statut
est relu.

## Étape 4 — Prompt de création du skill

Le prompt de création est généré par Teamstarter depuis le projet : le contexte IA de
l'organisation, la tâche, les réponses de structuration, la fiche. C'est la spécification du
skill.

**Automatique** : dès que le projet est relu en `CASHEDOUT` sans skill déposé (étape 1 ou 3), ou
que l'utilisateur demande le skill d'un projet ou une nouvelle version écrite depuis le prompt,
appeler le tool sans demander « je récupère le prompt ? ». C'est une lecture : elle n'écrit rien
dans Teamstarter. Dire en une ligne que le prompt est récupéré, puis enchaîner sur l'étape 5.

- **Tool `get-skill-creation-instructions`** : `{"projectId": <id>}`. La réponse est le prompt
  lui-même, en markdown ; il demande déjà au skill la métadonnée `teamstarter-project-id`.
  - Un refus « structuration incomplète » liste les questions obligatoires sans réponse : y
    répondre avec `ts-general-creer-projet` (étape 4), puis rappeler le tool.
  - Le prompt est réservé à l'auteur, aux porteurs et aux admins du projet : un autre compte
    reçoit un refus. Le dire, et demander à un porteur de reprendre.
- **Sans le tool** : demander à l'utilisateur d'ouvrir `<adresse de l'app>/<tag de
  l'organisation>/project/<id>/manage`, l'étape « Créer mon agent IA », bouton « Copier le
  prompt », et de le coller dans la conversation.

Ne pas résumer le prompt à l'utilisateur à la place de s'en servir : il se suit.

## Étape 5 — Écrire le skill

Passer la main à `skill-creator` (skill d'Anthropic) avec le prompt de l'étape 4 comme
spécification, et ces règles en plus :

1. **En-tête du `SKILL.md`**, au format de la spécification Agent Skills : `name` (minuscules,
   chiffres, tirets, 64 caractères au plus, égal au nom du dossier), `description` (1024
   caractères au plus, avec les phrases qui déclenchent le skill), et l'id du projet dans
   `metadata` :

```markdown
---
name: <nom-du-skill>
description: <ce que fait le skill et quand le déclencher>
metadata:
  teamstarter-project-id: "<id du projet>"
---
```

   La valeur est une chaîne. C'est elle qui relie le skill à son projet : le dépôt, la
   déclaration des utilisations et les blocages s'en servent.
2. **Deux dernières sections du `SKILL.md`**, à recopier telles quelles :

```markdown
## Après chaque exécution

Déclarer l'exécution à Teamstarter avec le skill `ts-general-declarer-execution-skill` du plugin
Teamstarter. S'il n'est pas disponible, ne rien faire.

## Après chaque modification de ce fichier

Quand ce `SKILL.md` est modifié (pas quand le skill s'exécute), déposer la nouvelle version sur
le projet Teamstarter avec le skill `ts-general-deposer-skill` du plugin Teamstarter. S'il n'est
pas disponible, ne rien faire.
```

   Les deux skills se déclenchent aussi sur la métadonnée, mais ces lignes garantissent qu'ils
   sont appelés quand le skill tourne chez un collègue, ou quand il est modifié dans une autre
   conversation, avec `skill-creator` ou à la main.
3. **Rien de confidentiel** dans le skill : ni donnée personnelle, ni nom de client, ni clé
   d'API ou mot de passe. Un accès à un service passe par un connecteur.
4. `skill-creator` absent : écrire le skill directement, au même format.

Enregistrer le `SKILL.md`, le déposer aussitôt (étape 6), puis le montrer en entier et demander
s'il convient. Chaque correction demandée fait une nouvelle version, déposée de même.

Livrer aussi le skill prêt à installer : un zip dont le dossier du skill est la racine
(`<nom-du-skill>.zip` contenant `<nom-du-skill>/SKILL.md`), à téléverser dans claude.ai ou Cowork
(Personnaliser → Skills), ou le dossier à copier dans `~/.claude/skills/` pour Claude Code.

## Étape 6 — Déposer le skill dans Teamstarter

**Automatique**, sans validation : à la première écriture du `SKILL.md`, puis à chaque
modification, suivre le skill `ts-general-deposer-skill` : un appel au tool
`upload-project-skill`, `{"projectId": <id>, "fileName": "SKILL.md", "contentBase64": "<le
SKILL.md en base64>"}`, le fichier encodé soi-même (le tool ne prend pas de chemin), 1 Mo au plus
une fois décodé. Le dépôt fait partie de
l'écriture du skill ; il s'annonce en une ligne (« Version déposée sur le projet Teamstarter
41207 (20/10 à 14 h 20). »).

- Un fichier par appel : le `SKILL.md`, celui qui porte la métadonnée. Un nouveau dépôt s'ajoute
  aux précédents ; le projet montre le dernier comme son skill (`project.skillFileId`).
- Pas de dépôt d'un fichier inchangé : chaque dépôt crée une tâche « partager ce fichier » pour
  les admins.
- Seuls les porteurs du projet déposent : un autre compte, admin compris, reçoit « Only the
  organizers of the project can manage its files. ». Le dire, et demander à un porteur de
  déposer, ou de se faire ajouter comme porteur.
- `ts-general-deposer-skill` absent de la conversation : faire le même appel directement.
- **Sans le tool** : demander à l'utilisateur de déposer le `SKILL.md` dans la section Fichiers
  de la page `/manage` du projet.

## Étape 7 — Valider l'étape « Créer mon agent IA »

Le skill est écrit et déposé : proposer de cocher l'étape, et attendre l'accord.

```graphql
query($where: SequelizeJSON) { project(where: $where) { id projectDeliveryActions { id type doneAt skippedAt } } }
```
variables : `{"where": {"id": <id>}}` → l'action de `type` `create-my-agent`.

```graphql
mutation($actionId: Int!, $status: String!) { setProjectWorkflowActionStatus(actionId: $actionId, status: $status) { id doneAt skippedAt } }
```
variables : `{"actionId": <id de l'action>, "status": "done"}`

Seuls l'auteur et les porteurs du projet cochent une étape ; un admin qui n'est pas porteur reçoit
un refus. Sans la mutation : demander à l'utilisateur de cocher « Créer mon agent IA » dans
`/manage`.

## Étape 8 — Tester le skill

1. Faire tester le skill sur un cas réel, dans la conversation ou après installation (étape 5).
   Chaque exécution est déclarée par `ts-general-declarer-execution-skill`.
2. Demander à l'utilisateur si le résultat est bon.
   - **Oui** : proposer de cocher « Tester l'agent en conditions réelles » (action `test-agent`),
     comme à l'étape 7.
   - **Non, à corriger** : revenir à l'étape 5 ; la nouvelle version est déposée
     automatiquement (étape 6).
   - **Non, et ça bloque** (accès, outil, sécurité, données) : étape B.

Les étapes suivantes de `/manage` (« Faire valider mon agent par mon ambassadeur », « Partager mon
agent au collectif », « Déclarer mis en place ») se font dans l'app : les nommer, donner le lien.

## Étape U — Utilisation du skill

Quand l'utilisateur demande comment son skill est utilisé (« combien de fois », « qui s'en sert »,
« combien de tokens ») :

```graphql
query($projectId: Int!) {
  projectSkillUsage(projectId: $projectId) {
    executionsCount failuresCount distinctUsersCount tokensCount averageDurationMs lastExecutionAt
    topUsers { executionsCount lastExecutionAt user { fullname } }
  }
}
```
variables : `{"projectId": <id>}`

- Réservé à l'auteur, aux porteurs et aux admins du projet ; un autre compte reçoit un refus.
- Les chiffres sont ceux que le skill a déclarés (`ts-general-declarer-execution-skill`) : une
  exécution non déclarée n'est pas comptée, et `tokensCount` à 0 veut dire « tokens non
  déclarés », pas « aucun token ».
- Les mêmes chiffres sont dans la carte « Utilisation du skill » de la page `/manage` du projet.

## Étape B — Point de blocage

Dès qu'un problème empêche de créer ou d'utiliser le skill, et que l'utilisateur ne peut pas le
lever seul : proposer de le déclarer sur le projet.

- Le projet doit être en `CASHEDOUT` ou `DELIVERED` ; avant, le dire : un blocage ne se déclare
  qu'en réalisation.
- Lire d'abord les blocages ouverts du projet, pour ne pas déclarer deux fois le même :
  `projectBlocker(where: {"projectId": <id>}) { id title category isResolved description }`.
- Préparer le titre (120 caractères au plus), la catégorie (`tool`, `access`, `security`,
  `budget`, `organization`, `participation`, `provider`, `other`) et une description qui dit ce
  qui bloque, ce qui a été essayé, et le contournement en attendant. **Valider** avec
  l'utilisateur, puis :

```graphql
mutation($b: projectBlockerInput!) { projectBlockerCreate(projectBlocker: $b) { id title category createdAt } }
```
variables : `{"b": {"projectId": <id>, "title": "…", "category": "tool", "description": "…"}}`

- Dire que personne n'est prévenu tout de suite : le blocage devient une tâche des admins de
  l'organisation, visible dans leurs actions et leur récapitulatif hebdomadaire.
- Le blocage levé : `projectBlockerUpdate` avec `{"id": <id>, "isResolved": true}`, sur demande.

## Garde-fous

- **Jamais `run-mutation` sans demande de l'utilisateur dans la conversation**, et jamais
  d'écriture sans la validation de l'étape. Deux exceptions, faites sans validation et annoncées
  en une ligne : le dépôt de chaque version du skill (étape 6) et la déclaration de ses
  exécutions (`ts-general-declarer-execution-skill`).
- **Ne pas écrire le skill avant que le projet soit en `CASHEDOUT`**, sauf si l'utilisateur
  choisit de le faire sans projet (Fallback).
- **Déposer chaque version écrite, et seulement elle** : pas de fichier inchangé, pas d'autre
  fichier que le `SKILL.md`. Ne jamais cocher une étape sans l'accord de l'utilisateur.
- **Une seule source pour l'id du projet** : la métadonnée `teamstarter-project-id`. Ne jamais
  déposer ni déclarer sur un autre projet.
- Ne rien inventer de la tâche : demander.

## Tags de sécurité

`écriture` : crée et propose un projet, dépose des fichiers, valide des étapes, déclare des
blocages. Chaque écriture suit une validation de l'utilisateur, sauf le dépôt de chaque version
du skill, automatique et annoncé. Produit un fichier local (le zip du skill).

## Fallback

- **Pas de connecteur, ou accès en lecture seule** : dire que le skill ne pourra pas être rattaché
  à un projet Teamstarter, et comment ouvrir l'écriture (l'administrateur de l'organisation ouvre
  l'accès en écriture, puis l'utilisateur reconnecte le connecteur en choisissant lecture et
  écriture). Si l'utilisateur veut continuer quand même, passer la main à `skill-creator` sans
  métadonnée.
- **Type `PROCESS_AUTOMATION_WITH_AI` absent de l'organisation** : même chose.
- **Tools de skill absents** : les gestes manuels de l'étape 0, une fois annoncés.

## Ressources

- `references/regles-api.md` — règles du connecteur, statuts, identité de l'utilisateur.
- Skills voisins : `ts-general-creer-projet` (créer et proposer le projet),
  `ts-general-deposer-skill` (déposer chaque version du skill),
  `ts-general-declarer-execution-skill` (déclarer chaque utilisation du skill),
  `ts-general-lister-projets` (voir ses projets).
- Skill d'Anthropic : `skill-creator` (écrire et évaluer le skill).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-creer-skill` — domaine `general`, verbe
`creer`, objet `skill`.
