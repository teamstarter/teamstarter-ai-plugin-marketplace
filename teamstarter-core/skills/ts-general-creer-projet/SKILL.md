---
name: ts-general-creer-projet
description: >-
  Crée un projet Teamstarter de bout en bout via le connecteur MCP Teamstarter, quel que soit son
  type (événement, automatisation avec l'IA, don, achat d'équipement, autre) : type, objectif,
  brouillon, questions de structuration, fiche générée ou rédigée, audit du cadre, puis
  proposition du projet. Reprend aussi un brouillon là où il s'est arrêté, en relisant son état
  sur la plateforme. Validation de l'utilisateur avant chaque écriture. Déclenche
  SYSTÉMATIQUEMENT dès que l'utilisateur mentionne "créer un projet", "lancer un projet",
  "nouveau projet Teamstarter", "j'ai une idée de projet", "proposer un projet", "monter un
  événement", "déclarer un projet d'automatisation", "reprendre mon brouillon", "continuer mon
  projet", "finir la structuration", "générer la fiche de mon projet", "soumettre mon projet".
  Déclencher même sans le mot "projet" si l'utilisateur veut porter une initiative dans
  Teamstarter. Pour voir ses projets : ts-general-lister-projets ; pour créer un skill :
  ts-general-creer-skill.
---

# Créer un projet Teamstarter, de la création à la proposition

## Quand utiliser ce skill

Un collaborateur veut porter un projet dans Teamstarter sans quitter sa conversation : il décrit
son idée, le skill crée le brouillon, pose les questions de structuration du type de projet,
fait générer la fiche, lance l'audit du cadre et propose le projet. Le même skill reprend un
brouillon commencé dans l'app ou dans une autre conversation : l'état du projet est sur la
plateforme, pas dans la mémoire de l'outil IA.

Ne pas utiliser pour lister ses projets ou voir leur statut (`ts-general-lister-projets`), ni pour
un projet déjà proposé ou en réalisation.

L'utilisateur veut créer un skill, un agent ou un assistant IA : c'est `ts-general-creer-skill`
qui mène, et qui suit ce skill pour créer et proposer le projet `PROCESS_AUTOMATION_WITH_AI`.
Après la proposition (étape 7), lui rendre la main.

## Sortie attendue

Un projet dans l'organisation du connecteur, structuré, avec sa fiche, et :

- soit **proposé** (`UNDER_REVIEW`, ou `PUBLISHED` quand l'organisation ne relit pas les
  projets) si l'utilisateur l'a demandé ;
- soit laissé en brouillon (`DRAFT`) à une étape nommée, que l'utilisateur pourra reprendre.

Le récapitulatif final donne l'id, le titre, le statut, la complétion, et le lien vers l'app
quand l'adresse est connue.

## Vue d'ensemble du workflow

```
[0] Connecteur et capacités
[1] Nouveau projet ou reprise d'un brouillon ──── reprise : aller à l'étape indiquée par l'état
[2] Type et objectif
[3] Titre, description, doublons             ←── validation 1, puis création du brouillon
[4] Questions de structuration               ←── validation 2, section par section
    (+ dépenses, budget, champs dérivés selon le type)
[5] Fiche : générée, ou rédigée              ←── validation 3 si rédigée ou modifiée
[6] Audit du cadre, si exposé
[7] Proposer le projet                       ←── validation 4, explicite
```

Chaque étape peut être la dernière de la conversation : le brouillon reste cohérent et le skill
saura le reprendre.

Lire `references/regles-api.md` avant le premier appel.

---

## Étape 0 — Connecteur et capacités

1. Trouver le connecteur Teamstarter de la conversation. S'il y en a plusieurs, demander lequel
   (ou le déduire de l'organisation que cite l'utilisateur). Aucun : aller au Fallback.
2. `list-schema`. Noter :
   - `run-mutation` : sans lui, l'accès est en lecture seule → Fallback ;
   - `projectCreate`, `projectUpdate`, `AIprojectQuestionAnswerCreate` : indispensables ;
   - `projectGenerateSheet`, `projectEvaluateLimits`, `spendingCreate` : optionnels, le parcours
     s'adapte à leur absence.
3. Un accès multi-organisations (staff) : demander l'organisation, passer son `organizationTag`
   à chaque appel.

## Étape 1 — Nouveau projet ou reprise

Si l'utilisateur parle d'un projet existant (« reprends mon projet X », « continue le brouillon »),
ou s'il a des brouillons en cours :

```graphql
query($where: SequelizeJSON) {
  project(where: $where, scopeForMe: true, order: "reverse:updatedAt", limit: 20) {
    id title status isBeingStructured updatedAt d_factoryCompletionRate d_draftCompletionRate
    projectType { tag titleWordings { value } }
  }
}
```
variables : `{"where": {"statusGroup": {"in": ["structuration", "writing"]}}}`

`scopeForMe: true` limite les brouillons à ceux de l'utilisateur (auteur, porteur ou invité).
Proposer de reprendre l'un d'eux ou d'en créer un nouveau. Pour reprendre, lire l'état et
**aller à la première étape non faite** :

| État relu | Reprendre à |
|---|---|
| `status` = `EMPTY` (créé dans l'app, rien d'écrit) | étape 4 ; si le projet n'a aucune question, étape 5 |
| une question obligatoire sans réponse (`d_factoryCompletionRate` < 1) | étape 4 |
| une section non optionnelle de la fiche vide | étape 5 |
| fiche remplie, `projectEvaluateLimits` exposé, pas d'audit ou audit périmé (`aiMetadata.isEvaluationOutdated`) | étape 6 |
| tout est fait | étape 7 |
| `UNDER_REVIEW`, `PUBLISHED` ou au-delà | déjà proposé : le dire, et orienter vers `ts-general-lister-projets` |

Dire en une phrase où en est le projet avant de continuer (« Ton projet *X* a ses réponses ;
il reste la fiche et l'audit. »).

## Étape 2 — Type et objectif

**Type.**
```graphql
query { projectType { id tag isDisabled titleWordings { value } d_useCaseTags } }
```
Écarter `isDisabled: true`. Proposer 3 ou 4 types, avec leur titre en français, d'après ce que
l'utilisateur a décrit. Puis lire le fichier du type s'il existe :

| Type | Référence |
|---|---|
| `EVENT` (cohésion, afterwork, séminaire…) | `references/type-evenement.md` |
| `PROCESS_AUTOMATION_WITH_AI`, `AI_SKILL` | `references/type-automatisation-ia.md` |
| autres | aucune : le parcours commun suffit, les questions se lisent sur le projet créé |

**Objectif.**
```graphql
query { objectiveCount objective(limit: 50, order: "reverse:id") { id status mode titleWordings { value } projectTypes { id tag } projectsCount } }
```
- `where.status` est ignoré par le serveur : garder côté client les objectifs `OPEN`. Paginer
  avec `offset` si `objectiveCount` dépasse 50.
- `projectTypes` non vide = objectif réservé à ces types.
- Un seul objectif possible : le prendre en le disant. Des titres en double : citer l'id.

**Mode de décision.** Le `decisionMode` du projet découle du mode de l'objectif. Ne jamais le
choisir soi-même :

| `objective.mode` | `decisionMode` à écrire | À dire à l'utilisateur |
|---|---|---|
| `SIMPLE_MODERATION` | `MODERATION` | modération |
| `CALLFORPROJECTS` | `VOTE` | appel à projets, vote |
| `CROWDSOURCING` | `VOTE` | vote |
| `CROWDFUNDING` | `CONTRIBUTE` | financement participatif |

La mutation accepte n'importe quelle valeur sans erreur. En cas de doute, relire
`decisionMode` sur quelques projets récents du même objectif.

## Étape 3 — Titre, description, doublons, création

1. **Doublons.** Chercher les projets proches dans tout le texte des projets :
   `omnisearch(where: {"search": "<2 ou 3 mots clés>", "isApproximate": true}, limit: 20) { type projectId searchA }`
   (garder `type: "project"`), puis lire ceux qui ressemblent :
   `project(where: {"id": <projectId>}) { id title status }`. Les idées ne sont pas dans cette
   recherche : lire les plus récentes, `idea(order: "reverse:createdAt", limit: 50) { id titleWordings { value } }`,
   et comparer les titres. Un projet ou une idée proche : le montrer et proposer de le rejoindre
   plutôt que d'en créer un. Un résultat vide ne prouve pas l'absence de doublon
   (`regles-api.md`).
2. **Depuis une idée** de la boîte à idées ou d'un atelier : la lire
   (`idea(where: {"id": <id>}) { id titleWordings { value } descriptionWordings { value } }`),
   s'en servir pour préparer le titre, la description et les réponses, et passer
   `sourceIdeaId: <id>` à `projectCreate`. Le serveur relie alors l'idée au projet (l'idée
   affiche le projet lancé), copie l'image de couverture de l'idée et range le projet dans le
   cycle de l'idée.
3. Proposer un **titre court** (3 à 8 mots) et une **description de 120 caractères au plus**.
   Pour un Événement, demander aussi la date, les horaires et le lieu (`type-evenement.md`).
4. **Validation 1** : afficher organisation, type, objectif et son mode, titre, description.
   Attendre le OK.
5. Créer avec le minimum, puis compléter :

```graphql
mutation($project: projectInput!) { projectCreate(project: $project) { id title status projectTypeId objectiveId organizationId authorId } }
```
variables : `{"project": {"title": "…", "projectTypeId": <id>, "objectiveId": <id>, "language": "fr", "status": "DRAFT", "isParticipatingEnabled": true}}`
(+ `locationId` pour un Événement sur un site de l'organisation : seulement ici, refusé ensuite.)

```graphql
mutation($project: projectInput!) { projectUpdate(project: $project) { project { id shortDescription decisionMode isBeingStructured } } }
```
variables : `{"project": {"id": <id>, "shortDescription": "…", "decisionMode": "<étape 2>", "isBeingStructured": true}}`

`projectCreate` ignore `decisionMode` et `isBeingStructured`, et échoue sur une description trop
longue : d'où les deux appels. Il génère les questions et les sections du projet.
`isBeingStructured: true` met le projet en phase « Structuration ».

Dire à l'utilisateur l'id du projet créé : c'est avec lui qu'il le retrouvera.

## Étape 4 — Questions de structuration

Suivre `references/questions-structuration.md` : lire les questions du projet, demander à
l'utilisateur s'il répond lui-même ou si Claude propose, **valider section par section** avant
d'écrire, écrire par lots de 7.

- `team` = `"1"` (co-porteurs) : demander leurs noms, retrouver chacun par
  `user(where: {"fullname": {"iLike": "%<nom>%"}}) { id fullname }`, faire confirmer, puis
  `projectOrganizerCreate` (lancer `describe-type projectOrganizer` avant). Un co-porteur ajouté
  reçoit une notification : le dire avant d'écrire. Le serveur recalcule la réponse `team` à
  chaque ajout ou retrait de porteur : ne pas la réécrire ensuite.
- `resources` = `"true"` : lignes de dépense (`references/depenses.md`), puis la réponse `budget`.
- Champs dérivés propres au type : fichier du type.
- Contrôle de fin (fin de `questions-structuration.md`) avant de passer à l'étape 5.

## Étape 5 — Fiche du projet

Suivre `references/fiche-projet.md` :

- `projectGenerateSheet` exposé : lancer, poller, résumer la fiche une ligne par section, puis
  remettre le titre de l'utilisateur si le job l'a changé ;
- sinon : rédiger, **valider**, écrire en tiptap ;
- l'utilisateur veut modifier une section : montrer la nouvelle version, valider, écrire par
  `wordingTranslatedUpdate`.

Quand les sections non optionnelles sont remplies, terminer la structuration :

```graphql
mutation($project: projectInput!) { projectUpdate(project: $project) { project { id isBeingStructured structuredAt d_draftCompletionRate } } }
```
variables : `{"project": {"id": <id>, "isBeingStructured": false, "structuredAt": "<maintenant, ISO>"}}`

C'est l'état des projets structurés dans l'app (le projet passe en « En cours de rédaction »).

## Étape 6 — Audit du cadre (si `projectEvaluateLimits` est exposé)

```graphql
mutation($id: Int!) { projectEvaluateLimits(projectId: $id) { jobId } }
```
Poller toutes les 60 à 90 secondes (1,5 à 3,5 minutes observées) :

```graphql
query($where: SequelizeJSON, $pw: SequelizeJSON) {
  projectLimitEvaluation(where: $where) { limitId status confidence explanation improvements impacts evaluatedAt }
  project(where: $pw) { id aiMetadata { statusEvaluation isEvaluationOutdated } }
}
```
variables : `{"where": {"projectId": <id>, "aiJobId": <jobId>}, "pw": {"id": <id>}}`

- Filtrer sur `aiJobId` : les lignes des audits précédents restent.
- Terminé quand `statusEvaluation` vaut `successful`. Aucune ligne = aucune limite de
  l'organisation ne s'applique.
- Restituer : nombre de points `ok`, `warning`, `not_applicable` ; puis chaque warning avec sa
  confiance, son explication et l'amélioration suggérée.
- Proposer : corriger (réponses, dépenses, champs) → régénérer la fiche → relancer l'audit ; ou
  proposer le projet tel quel. L'utilisateur décide.

Absent du schéma : le dire comme une limite de l'accès, sans audit fait par Claude.

## Étape 7 — Proposer le projet

**L'API n'a aucun garde-fou** : elle accepte la proposition d'un projet vide. Vérifier :

1. aucune question obligatoire sans réponse (`d_factoryCompletionRate` = 1) ;
2. sections non optionnelles remplies ;
3. si `resources` = `"true"` : au moins une ligne de dépense, `estimate` > 0, `budgetId` posé ;
4. `decisionMode` cohérent avec le mode de l'objectif, champs dérivés du type posés ;
5. audit lu et traité, ou écarté par l'utilisateur en le disant.

Un point manque : le dire et proposer de le compléter. L'utilisateur peut choisir de proposer
quand même.

**Statut à écrire.** Dans l'app, « Proposer » envoie le projet en relecture (`UNDER_REVIEW`)
quand l'organisation relit les projets avant publication, et le publie directement
(`PUBLISHED`) sinon. Le réglage n'est pas lisible par un accès collaborateur. Le déduire :

```graphql
query($where: SequelizeJSON) { project(where: $where, limit: 1) { id } }
```
variables : `{"where": {"underReviewAt": {"ne": null}}}`

Une ligne : l'organisation relit les projets → `UNDER_REVIEW`. Aucune : demander à
l'utilisateur si son bouton dans l'app dit « Soumettre le projet » (relecture) ou « Publier le
projet » (publication directe), et écrire `UNDER_REVIEW` dans le doute.

**Validation 4.** Afficher le récapitulatif (titre, type, objectif et mode, description, date et
lieu le cas échéant, budget et lignes, complétion, audit) et **ce qui va se passer** (« Le
projet part en relecture chez les animateurs » ou « Le projet sera visible par toute
l'organisation »). Attendre une confirmation explicite.

```graphql
mutation($project: projectInput!) { projectUpdate(project: $project) { project { id title status underReviewAt publishedAt isBeingStructured } } }
```
variables : `{"project": {"id": <id>, "status": "UNDER_REVIEW", "isBeingStructured": false}}`

Confirmer avec l'id, le statut relu et la date. Retour en arrière, sur demande seulement :
`status: "DRAFT"`, `isBeingStructured: true`.

## Garde-fous

- **Jamais `run-mutation` sans demande de l'utilisateur dans la conversation**, et jamais
  d'écriture sans la validation de l'étape.
- **Ne pas inventer** : date, lieu, montant, prestataire, co-porteur, réponse factuelle. Demander,
  ou écrire « à préciser » en le disant.
- **Ne pas coder en dur** les ids de type, d'objectif, de question, de section : ils changent
  d'une organisation et d'un projet à l'autre. Les relire à chaque fois.
- **Ne jamais proposer un projet sans la validation 4**, ni le repasser en brouillon sans demande.
- **Ne jamais réécrire une réponse ou une section sans le dire**, et seulement celle demandée.
- **7 mutations au plus par appel** ; relire après toute erreur générique avant de réécrire.
- Pas de donnée personnelle ni de nom de client dans la fiche d'un projet d'automatisation.

## Tags de sécurité

`écriture` : crée et modifie un projet, des réponses, des lignes de dépense, des co-porteurs, et
change le statut du projet. Chaque écriture suit une validation de l'utilisateur.

## Fallback

- **Pas de connecteur, ou accès en lecture seule** : poser quand même les questions du type,
  rédiger la fiche, et livrer un fichier `fiche-projet-<titre>.md` (titre, description, réponses,
  sections) à recopier dans l'app. Expliquer comment autoriser l'écriture : l'administrateur de
  l'organisation ouvre l'accès en écriture, puis l'utilisateur reconnecte le connecteur en
  choisissant la lecture et l'écriture.
- **`projectGenerateSheet` absent** : rédiger la fiche (étape 5 B).
- **`projectEvaluateLimits` absent** : passer l'étape 6 en le disant.
- **`spendingCreate` absent** : voir `references/depenses.md`.
- **Job IA qui ne se termine pas en 5 minutes** : arrêter de poller, dire où en est le projet, et
  proposer de reprendre plus tard (« reprends mon projet <id> »).
- **Pas de Python** : construire le JSON tiptap à la main (`references/fiche-projet.md`).

## Ressources

- `references/regles-api.md` — règles du connecteur, statuts, identité de l'utilisateur.
- `references/questions-structuration.md` — lire, poser, coder et écrire les réponses.
- `references/depenses.md` — lignes de dépense et budget.
- `references/fiche-projet.md` — générer, rédiger, modifier une section.
- `references/type-evenement.md`, `references/type-automatisation-ia.md` — particularités par type.
- `scripts/tiptap.py` — markdown simple vers document tiptap.
- Skill voisin : `ts-general-lister-projets` (voir ses projets et leur statut, choisir lequel
  reprendre).
- Parcours Teamstarter : étape `PMG-A-22`, qui fait par le connecteur les étapes `PMG-A-6` à
  `PMG-A-18` de l'app.

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-creer-projet` — domaine `general`,
verbe `creer`, objet `projet`.
