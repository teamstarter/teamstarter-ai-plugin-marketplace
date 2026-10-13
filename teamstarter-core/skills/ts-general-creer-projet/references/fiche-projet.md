# Fiche projet : générer, relire, modifier une section

À lire à l'étape 6 du skill. La fiche, ce sont les sections du projet (`project.sections`), chacune
avec une réponse (`answer`) dont le texte est un wording traduit.

## Lire la fiche

```graphql
query($where: SequelizeJSON) {
  project(where: $where) {
    id title shortDescription d_draftCompletionRate
    aiMetadata { generationJob { id status } }
    sections {
      id isContentOptional titleWordings { value } descriptionWordings { value }
      answer { id wordingTranslatedUuid isAIPowered wordings { id language type value } }
    }
  }
}
```
variables : `{"where": {"id": <id>}}`

- `isContentOptional: true` : la section peut rester vide.
- `descriptionWordings` : la consigne de rédaction de la section (document Draft.js, lire
  `blocks[].text`).
- Le texte d'une section est un document tiptap (ProseMirror) : pour le résumer, extraire les
  nœuds `text`.

## A. Génération par la plateforme (si `projectGenerateSheet` est dans `list-schema`)

```graphql
mutation($id: Int!) { projectGenerateSheet(projectId: $id) { jobId } }
```

- Poller la fiche toutes les 60 à 90 secondes, 5 minutes au plus. **Fin = les sections non
  optionnelles ont un `wordings` non vide.** `aiMetadata.generationJob` peut rester `null`, ou y
  revenir dès la fin : ne pas s'y fier.
- Durée observée : 1 à 3 minutes.
- Le job **réécrit le titre** (raccourci) et parfois la description : relire, et remettre le
  titre voulu par l'utilisateur via `projectUpdate` s'il a changé.
- Après toute modification d'une réponse de structuration, la fiche n'est plus à jour : proposer
  de la régénérer.

Résumer la fiche à l'utilisateur, une ligne par section, et proposer des retouches.

## B. Rédaction par Claude (si la génération n'est pas exposée, ou pour retoucher une section)

1. Le dire, puis rédiger chaque section à partir des réponses de structuration et de la consigne
   de la section. Suivre le ton des fiches existantes de l'organisation (les lire si besoin) et
   les indications du fichier du type.
2. **Montrer le texte de toutes les sections et attendre la validation** avant d'écrire.
3. Convertir chaque section en document tiptap : `python3 scripts/tiptap.py section.md` (markdown
   simple : paragraphes, puces `- `, listes `1. `, `**gras**`). Sans Python, construire le JSON à la
   main d'après l'exemple plus bas.
4. Écrire. Le `wordings` imbriqué dans `projectSectionAnswerUpdate` est ignoré : créer le wording
   sur l'uuid de la réponse, puis marquer la réponse.

```graphql
mutation($w: wordingTranslatedInput!, $a: projectSectionAnswerInput!) {
  w: wordingTranslatedCreate(wordingTranslated: $w) { id wordingTranslatedUuid language type }
  a: projectSectionAnswerUpdate(projectSectionAnswer: $a) { id isAIPowered }
}
```
variables : `{"w": {"wordingTranslatedUuid": "<answer.wordingTranslatedUuid>", "language": "fr", "type": "tiptap", "organizationId": <id de l'organisation>, "value": <document tiptap>}, "a": {"id": <answer.id>, "isAIPowered": true}}`

- `type: "tiptap"` et `organizationId` sont obligatoires. `organizationId` se lit sur le projet
  (`project { organizationId }`) : la requête `organization` n'existe pas sur un accès
  collaborateur.
- Un wording par langue et par uuid. **Modifier un texte existant** : `wordingTranslatedUpdate`
  avec l'`id` du wording (lu dans `answer.wordings`), jamais un second `Create`.
- Ne jamais réécrire une section que l'utilisateur n'a pas demandé de changer, et dire laquelle
  on modifie avant de le faire.

## Format tiptap

```json
{"type": "doc", "content": [
  {"type": "paragraph", "attrs": {"textAlign": "left"}, "content": [
    {"type": "text", "text": "Cette tâche me prend environ "},
    {"type": "text", "marks": [{"type": "bold"}], "text": "30 minutes"},
    {"type": "text", "text": ", 5 fois par mois."}
  ]},
  {"type": "bulletList", "content": [
    {"type": "listItem", "attrs": {"color": null}, "content": [
      {"type": "paragraph", "attrs": {"textAlign": "left"}, "content": [{"type": "text", "text": "Étape 1"}]}
    ]}
  ]},
  {"type": "orderedList", "attrs": {"start": 1}, "content": []}
]}
```

Les `attrs` sont ceux que pose l'app ; la plateforme accepte aussi le document sans eux.

## Contrôle

`project { sections { isContentOptional answer { isAIPowered wordings { id language type } } } d_draftCompletionRate }` :
un wording `fr` / `tiptap` par section non optionnelle.
