# Lignes de dépense d'un projet

À lire quand la réponse `resources` vaut `"true"` : l'app exige alors au moins une ligne de
dépense avant la soumission.

## Vérifier que l'accès les expose

`list-schema` doit lister `spendingCreate` et `spending`. Sinon : le dire, expliquer que l'app
marquera « dépenses obligatoires », laisser `planned-spendings` vide, et proposer d'ajouter les
lignes depuis la fiche du projet dans l'app. Dans ce cas seulement, poser `estimate` (centimes)
par `projectUpdate`, en prévenant que la liste des dépenses restera vide dans l'app.

## Ce qu'il faut demander pour chaque ligne

Intitulé, montant, type, prestataire (optionnel), description (optionnelle). Ne jamais inventer
un montant ni un prestataire.

Types valides : `REGISTRATION`, `FOOD`, `EQUIPMENT`, `TRANSPORT`, `SOFTWARE`, `TRAINING`,
`EXTERNAL_SPEAKER`, `DONATION`, `MAN_HOURS`, `OTHER`. La note de `describe-type spending` donne la
liste à jour.

Prestataire : `provider(where: {"name": {"iLike": "%<nom>%"}}) { id name }`. Absent : proposer
`providerCreate` (après accord), ou omettre `providerId`.

## Écrire

```graphql
mutation($s1: spendingInput!, $s2: spendingInput!) {
  s1: spendingCreate(spending: $s1) { id title moneySpent type status }
  s2: spendingCreate(spending: $s2) { id title moneySpent type status }
}
```
variables : `{"s1": {"projectId": <id>, "title": "…", "moneySpent": 25000, "type": "EXTERNAL_SPEAKER", "providerId": <id>, "description": "…"}}`

- `moneySpent` en **centimes** (25000 = 250 €).
- Ne pas passer `status` : le serveur pose `PLANNED` sur un brouillon.
- Ne pas poser `estimate` à la main : le serveur le recalcule comme la somme des lignes `PLANNED`.

## Relire

```graphql
query($where: SequelizeJSON, $pw: SequelizeJSON) {
  spending(where: $where) { id title moneySpent type status }
  project(where: $pw) { id estimate spendingsCount budgetId }
}
```
variables : `{"where": {"projectId": <id>}, "pw": {"id": <id>}}`

Puis écrire la réponse `budget` (voir `questions-structuration.md`).
