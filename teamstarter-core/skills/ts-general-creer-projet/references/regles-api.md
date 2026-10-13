# Règles du connecteur Teamstarter

À lire avant le premier appel. Règles vérifiées sur des projets réels, ou lues dans le code de la
plateforme quand c'est précisé.

## Les quatre tools

| Tool | Rôle |
|---|---|
| `list-schema` | Ce que cet accès peut appeler : requêtes, mutations, et la liste des types qui ont une note. |
| `describe-type` | Les champs d'un type, et sa note quand elle existe. Toujours le lancer avant d'interroger un type dont la note est signalée par `list-schema`. |
| `run-query` | Lire. |
| `run-mutation` | Écrire. Absent d'un accès en lecture seule. **Jamais sans une demande de l'utilisateur dans la conversation.** |

Un accès multi-organisations (staff Teamstarter) demande `organizationTag` à chaque appel, et
`api: "organization"` pour les requêtes d'une organisation. Un accès collaborateur porte déjà son
organisation : ne rien passer.

## Écrire une requête

- `where`, `order`, `limit`, `offset` et les inputs passent **toujours** dans `variables`, jamais
  en dur dans le document. `where` est de type `SequelizeJSON`.
- Les listes plafonnent à **50 lignes**. Compter avec `<nom>Count` (même `where`), paginer avec
  `offset`.
- Lire un projet par `{"id": N}`. Un filtre `id: [a, b]` sur `project` peut ne renvoyer qu'une
  partie des lignes.
- Une liste vide ne prouve pas l'absence : la liste `project` d'un collaborateur ne contient que
  ses projets, ceux où il est invité et ceux que leur statut rend visibles à tous.

## Écrire une mutation

- **7 mutations au plus par appel** (alias `r1:`, `r2:`…). Au-delà : « Internal server error » et
  **rien** n'est écrit.
- L'erreur générique « Désolé, une erreur est apparue » / « Sorry, an error happened » vient d'un
  resolver ou d'un hook. **Relire** avant de réécrire : l'écriture a pu réussir, ou être
  enregistrée vide.
- Les objets imbriqués dans un input (`spendings`, `wordings` dans `projectInput` ou
  `projectSectionAnswerInput`) sont **ignorés sans erreur**. N'écrire que par les mutations
  dédiées.
- `projectUpdate` répond `projectAndItsEventsAndCurrentAccount` : lire le projet sous
  `project { … }`.
- Montants en **centimes** (`estimate`, `moneySpent`).
- `shortDescription` : **120 caractères au plus** (au-delà : erreur générique).
- Chaque écriture est relue avec les champs retournés, et rapportée à l'utilisateur avec les
  valeurs lues, pas avec celles envoyées.

## Statuts d'un projet

`status` est une chaîne. Valeurs : `EMPTY`, `DRAFT`, `UNDER_REVIEW`, `PUBLISHED`,
`CAMPAIGN_FAILED`, `FROZEN`, `CASHEDOUT`, `DELIVERED`, `ENDED`, `CANCELLED`, `DELETED`, `TEMPLATE`.

Le libellé que l'utilisateur voit dans « Mes projets » est plus fin que `status`. La liste
`project` accepte un filtre `statusGroup` qui n'est pas une colonne et que le schéma ne montre pas :

| `statusGroup` | Libellé dans l'app | Condition |
|---|---|---|
| `structuration` | Structuration | `DRAFT` et `isBeingStructured: true` |
| `writing` | En cours de rédaction | `EMPTY`, ou `DRAFT` hors structuration |
| `moderation` | En attente de modération | `UNDER_REVIEW` |
| `vote` | Soumis au vote | `PUBLISHED`, mode vote |
| `funding` | En cours de financement | `PUBLISHED`, autres cas (financement, modération simple, en attente de sélection) |
| `participantSearch` | Recherche de participants | `PUBLISHED`, financé et ouvert aux participants |
| `campaignFailed` | Campagne échouée | `CAMPAIGN_FAILED` |
| `realization` | En cours de réalisation | `CASHEDOUT` (et `FROZEN`, « Temporairement gelé ») |
| `delivered` | Mis en place | `DELIVERED` |
| `ended` | Terminé | `ENDED` |

Source : `server/services/project/getMyProjectsStatusGroupWhere.ts` (plateforme). Une
organisation peut renommer un libellé dans son interface : citer aussi le statut technique quand
un doute est possible.

Syntaxe : `"where": {"statusGroup": {"in": ["structuration", "writing"]}}`.

## Qui est l'utilisateur du connecteur

Le connecteur agit au nom de la personne qui l'a autorisé, mais aucune requête ne renvoie son
identifiant. Le retrouver dans cet ordre, une fois par conversation, et le garder :

1. `userIdea(limit: 1) { userId }` : cette liste est forcée sur la personne du connecteur. Vide
   si l'IA ne lui a jamais suggéré d'idée.
2. Sinon, demander son adresse email Teamstarter, puis
   `user(where: {"email": "<email>"}) { id fullname organizationId }` (filtre sur l'email lu
   dans le code, pas encore joué sur un accès collaborateur : s'il ne répond rien, chercher par
   `fullname` avec `{"iLike": "%<nom>%"}`).
3. **Faire confirmer** : « Je travaille pour <fullname> (#<id>), c'est bien toi ? ». Sans
   confirmation, ne rien filtrer sur cet id.

Utile pour `authorId` et `d_organizerIds`, qui s'interrogent ainsi :
`"where": {"d_organizerIds": {"contains": [<id>]}}`.

## Jobs IA

`projectGenerateSheet(projectId)` et `projectEvaluateLimits(projectId)` répondent dès que le job
est mis en file : une réponse sans erreur veut dire « lancé », pas « terminé ». Poller toutes les
60 à 90 secondes, 5 minutes au plus, puis proposer de revenir plus tard. Une commande `sleep` d'un
shell est plafonnée à 2 minutes : poller par tranches.

Leur absence de `list-schema` est une limite de **l'accès** du connecteur, pas une fonctionnalité
qui manque à l'organisation. Le dire ainsi.

## Liens vers l'app

Un projet s'ouvre à `<adresse de l'app>/<tag de l'organisation>/project/<id>` et se modifie à
`…/project/<id>/edit`. L'adresse change d'une instance à l'autre
(`https://demo-internal-test.teamstarter.co/demo-internal-test/project/8891`) : la reprendre de
l'URL que l'utilisateur utilise. Si elle n'est pas connue, donner seulement l'id et le titre du
projet.
