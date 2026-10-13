# Type Événement (`EVENT`)

Ce qui s'ajoute au parcours commun pour un projet Événement. Parcours joué de bout en bout en
production et en staging (création, réponses, dépenses, fiche générée, audit, soumission).

## Choisir le type

« Cohésion », « teambuilding », « afterwork », « séminaire », « conférence » : ce sont des cas
d'usage du type Événement, pas des types. Proposer Événement.

## Avant de créer le brouillon

Demander, dans cet ordre :

1. un **titre court** : c'est aussi la réponse à `event-name`, qui écrase le titre du projet ;
2. une description de 120 caractères au plus (en proposer une) ;
3. **la date de l'événement et ses horaires** — ne jamais les inventer ;
4. le **lieu** :
   - mode : `SUR_SITE`, `EN_LIGNE` ou `HYBRIDE` ;
   - sur site : la ville, `city(where: {"name": {"iLike": "%paris%"}}) { id name }`. Ce
     référentiel est global et contient des doublons : reprendre de préférence l'id utilisé par les
     projets récents de l'organisation ;
   - `SINGLE` (un lieu) ou `MULTIPLE` (plusieurs).

Lire les projets récents du type pour reprendre les valeurs de l'organisation :
`project(where: {"projectTypeId": <id>}, order: "reverse:createdAt", limit: 10) { locationId cityId decisionMode }`.

- **`locationId` (le site de l'organisation) ne peut être posé qu'à `projectCreate`** : refusé
  ensuite. L'omettre si l'organisation n'en utilise pas.
- Après la création, poser par `projectUpdate` : `projectLocationMode`, `projectLocationCount`,
  `cityId`.

## Questions propres au type

| Tag | Valeur |
|---|---|
| `event-name` | Le titre court. Il écrase le titre du projet, tronqué à 120 caractères. |
| `event-date` | Format `date` : minuit heure de Paris en UTC (`questions-structuration.md`). La date vient de l'utilisateur. |
| `event-funding-tiers` | Jamais renseigné par l'app dans les données observées : `"false"`, ou ne rien envoyer. |

Selon le modèle de l'organisation, un Événement compte 31 à 34 questions en 7 sections
(événement, impact, public, déroulé, ressources, préparation, campagne).

## Champs du projet dérivés des réponses

L'app les dérive des réponses ; l'API ne le fait pas. Les poser après les réponses et les
dépenses :

```graphql
mutation($project: projectInput!) {
  projectUpdate(project: $project) {
    project { id committedDeliveredAt committedDeliveredStartTime committedDeliveredEndTime
      minParticipants maxParticipants daysToAutoAssignFundingEndedAt estimate budgetId
      d_draftCompletionRate }
  }
}
```
variables : `{"project": {"id": <id>, "committedDeliveredAt": "YYYY-MM-DD", "committedDeliveredStartTime": "12:30", "committedDeliveredEndTime": "13:15", "minParticipants": 5, "maxParticipants": 20, "daysToAutoAssignFundingEndedAt": 30}}`

Avec `budgetId` et `daysToAutoAssignFundingEndedAt` posés, `d_draftCompletionRate` atteint 100 %
(l'image de couverture n'est pas comptée).

## Fiche

Sections habituelles : « Pourquoi cet événement ? », « Comment ça va se passer ? »,
« Infos pratiques », « Le coup de main recherché » (cette dernière peut rester vide). Ton des
fiches existantes : tutoiement, concret, listes pour le déroulé et les infos pratiques.

## Audit

Les avertissements à confiance inférieure à 80 % sur des sujets d'appréciation reviennent souvent
même après correction (un intervenant bien-être lu comme « paramédical », un jeu ou du yoga doux
lu comme « sport sur site », un trophée lu comme « cadeau »). Le dire à l'utilisateur et le
laisser décider.
