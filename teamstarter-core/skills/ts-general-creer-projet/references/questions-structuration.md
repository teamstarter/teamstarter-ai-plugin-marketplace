# Questions de structuration : lire, répondre, écrire

À lire avant l'étape 5 du skill. Ce qui est propre à un type de projet est dans
`type-evenement.md` et `type-automatisation-ia.md` ; ce fichier vaut pour tous les types.

## Lire les questions du projet

`projectCreate` génère les questions et les sections du projet, avec des **ids propres à ce
projet** : ne jamais réutiliser les ids d'un autre projet.

```graphql
query($where: SequelizeJSON) {
  AIprojectQuestion(where: $where, order: "id") {
    id tag isRequired isEnabled responseFormat options stepsOrder
    questionWordings { value }
    section { id titleWordings { value } }
    answer { id answer idontknow }
  }
}
```
variables : `{"where": {"projectId": <id>}}`

- Regrouper par section, dans l'ordre des sections puis de `stepsOrder`.
- Ignorer `isEnabled: false`.
- Sauter les questions déjà répondues (pré-remplies à la création : objectif, « nécessite des
  participants », étapes de mise en œuvre selon le type).
- `options` donne les valeurs d'un choix (`single-select`, `multi-select`) : afficher le libellé,
  écrire la `value`.

## Poser les questions

Demander d'abord à l'utilisateur :

1. **Obligatoires seulement**, ou toutes ?
2. **Il répond** lui-même, ou **Claude propose** des réponses à partir de ce qu'il a déjà dit
   (description du projet, idée de départ, conversation) ?

Puis :

- Projet de création de skill (`PROCESS_AUTOMATION_WITH_AI`, `AI_SKILL`) : poser chaque question
  avec son libellé exact, sans reformulation (`type-automatisation-ia.md`, règle 3).
- Une question ouverte à la fois. Grouper dans une même demande les questions courtes (durée,
  nombre, score, oui/non, date).
- Quand Claude propose : afficher toute la proposition d'une section, attendre la validation ou
  les corrections, puis passer à la section suivante. Une proposition non validée ne s'écrit pas.
- **Ne jamais inventer une donnée factuelle** : date, lieu, montant, nom d'un intervenant ou d'un
  prestataire. La demander, ou écrire « à préciser » en le disant.
- « Je ne sais pas » : écrire la réponse avec `idontknow: true` et sans `answer`.
- Optionnelle sans réponse : ne rien envoyer.

## Formats de `answer` (toujours une chaîne)

| `responseFormat` | Valeur écrite | Exemple |
|---|---|---|
| `text`, `short-text` | texte libre | `"2 heures"` |
| `number` | nombre en chaîne | `"8"` |
| `score` | entier de 1 à 5 en chaîne | `"4"` |
| `boolean` | `"true"` / `"false"`, sauf `team` (voir plus bas) | `"true"` |
| `single-select` | la `value` de l'option choisie | `"pause-dejeuner"` |
| `multi-select` | tableau JSON sérialisé des `value` | `"[\"pause-dejeuner\"]"` |
| `objective` | id de l'objectif en chaîne | `"42"` |
| `date` | ISO datetime : minuit heure de Paris converti en UTC | `"2026-11-04T23:00:00.000Z"` pour le 5 novembre |

Pour une date : heure d'été (CEST, UTC+2) → la veille à `22:00:00.000Z` ; heure d'hiver (CET,
UTC+1) → la veille à `23:00:00.000Z`. Un simple `"YYYY-MM-DD"` laisse le sélecteur de date vide
dans l'app.

**`responseFormat` ne dit pas tout.** Pour une question affichée dans l'app en cartes, en menu ou
en sélecteur de date, et absente des tableaux de ce fichier, lire la valeur enregistrée sur un
projet saisi à la main avant d'inventer un codage :
`AIprojectQuestion(where: {"tag": "<tag>", "projectId": {"gt": <id récent>}}) { answer { answer } }`.

## Tags à valeur codée, communs à tous les types

Une valeur hors codage est acceptée par l'API mais laisse le champ vide dans l'app.

| Tag | Question | Valeur |
|---|---|---|
| `team` | Seul(e) ou en équipe ? (`boolean`) | `"0"` = seul(e), `"1"` = avec des co-porteurs. **Pas `"true"`.** Défaut `"0"` ; les co-porteurs s'ajoutent ensuite par `projectOrganizerCreate`. |
| `organization-participant` | Le projet a-t-il besoin de participants ? | `"true"` / `"false"` (souvent pré-rempli) |
| `resources` | Besoin de ressources / d'un budget ? (format `text`) | `"true"` / `"false"`. À `"true"`, le serveur crée lui-même les réponses `planned-spendings` et `budget`, vides et obligatoires. |
| `planned-spendings` | Lignes de dépense | **Ne rien écrire** : `spendingCreate` la met à jour avec le nombre de lignes. Une écriture fait doublon et part en erreur. |
| `budget` | Enveloppe budgétaire | id de l'enveloppe, en chaîne. Lire `budget { id targetAmount startAt endAt titleWordings { value } }` et prendre celle dont la période couvre aujourd'hui. Écrire par `AIprojectQuestionAnswerUpdate` sur la réponse créée par le serveur (ou `Create` si elle manque). Le serveur pose `project.budgetId`. Un id inexistant donne l'erreur générique. |
| `campaign` | Période de collecte (format `text`) | nombre de jours en chaîne (`"30"`). Relire ensuite `project.daysToAutoAssignFundingEndedAt` et le corriger par `projectUpdate` s'il diffère. |
| `impacts-objectives` | Objectif du projet | id de l'objectif en chaîne ; pré-rempli à la création quand la question existe. Si le modèle de l'organisation ne contient pas cette question, l'objectif ne s'affiche pas dans « Impact recherché » même avec `project.objectiveId` posé : le signaler, rien à faire par l'API. |

## Écrire les réponses : 7 au plus par appel

```graphql
mutation($a1: AIprojectQuestionAnswerInput!, $a2: AIprojectQuestionAnswerInput!) {
  r1: AIprojectQuestionAnswerCreate(AIprojectQuestionAnswer: $a1) { id questionId answer }
  r2: AIprojectQuestionAnswerCreate(AIprojectQuestionAnswer: $a2) { id questionId answer }
}
```
variables : `{"a1": {"projectId": <id>, "questionId": <id de la question>, "answer": "…"}, …}`

Corriger une réponse : `AIprojectQuestionAnswerUpdate` avec l'`id` de la **réponse** (pas de la
question).

Ordre quand le projet a un budget : réponses (dont `resources`) → lignes de dépense
(`depenses.md`) → relire `planned-spendings` et `budget`, écrire `budget` → champs du projet
dérivés des réponses (fichier du type).

## Contrôle de fin de structuration

```graphql
query($where: SequelizeJSON, $q: SequelizeJSON) {
  project(where: $where) { id d_factoryCompletionRate d_draftCompletionRate }
  AIprojectQuestion(where: $q) { id tag answer { id } }
}
```
variables : `{"where": {"id": <id>}, "q": {"projectId": <id>, "isRequired": true}}`

Terminé quand `d_factoryCompletionRate` vaut `1` et qu'aucune question obligatoire n'est sans
`answer`. Ne pas passer à la fiche avant, sauf demande explicite de l'utilisateur.
