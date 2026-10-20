---
name: ts-general-declarer-blocage
description: >-
  Remonte les blocages d'un projet Teamstarter en cours de réalisation (CASHEDOUT) ou mis en
  place (DELIVERED), via le connecteur MCP Teamstarter : dès qu'un problème empêche d'avancer
  sur un tel projet et que l'utilisateur ne peut pas le lever seul (exécution d'un skill de
  projet qui échoue sur un accès refusé, un outil indisponible, une donnée manquante ou une
  règle de sécurité ; budget, prestataire, décision ou participation qui manque), propose
  d'enregistrer un blocage, le rédige (titre, catégorie, ce qui bloque, ce qui a été essayé,
  contournement, qui peut débloquer), le fait valider puis le déclare sur le projet. Lit aussi
  les blocages d'un projet, les commente, les marque résolus. Déclenche dès que l'utilisateur
  dit "je suis bloqué", "mon projet est bloqué", "déclarer un blocage", "remonter un problème",
  "le blocage est levé", "quels sont les blocages de mon projet", ou quand l'exécution d'un
  skill qui porte teamstarter-project-id échoue sur un tel problème. Jamais sans accord.
---

# Remonter les blocages d'un projet en réalisation

## Quand utiliser ce skill

Une fois un projet validé et en réalisation, ses porteurs rencontrent des problèmes qu'ils ne
peuvent pas lever seuls : un accès refusé, un outil qui ne marche pas, un budget bloqué, un
prestataire en retard, des collègues qui ne participent pas. Teamstarter les enregistre comme
**blocages** du projet : chacun est visible par les porteurs et les admins de l'organisation
(section « Blocages » de la page `/manage` du projet, page « Blocages » des admins), devient une
tâche des admins, et sert à repérer ce qui freine les projets.

Ce skill fait remonter ces problèmes au moment où ils arrivent, dans la conversation où ils
arrivent, au lieu de les laisser se perdre. Il sert pour tout type de projet, pas seulement les
projets de création de skill.

## Sortie attendue

- un blocage déclaré sur le bon projet, avec un titre, une catégorie et une description qui
  disent ce qui bloque, ce qui a été essayé, le contournement en attendant et qui peut
  débloquer ;
- ou un commentaire sur un blocage déjà ouvert pour le même problème ;
- ou un blocage marqué résolu.

Chaque écriture suit une validation de l'utilisateur.

## Vue d'ensemble

```
[0] Repérer le problème et le projet
[1] Proposer de déclarer un blocage        ←── accord de l'utilisateur
[2] Connecteur et droits
[3] Statut du projet : CASHEDOUT ou DELIVERED
[4] Blocages déjà ouverts : commenter plutôt que doublonner
[5] Rédiger le blocage                      ←── validation du texte
[6] Déclarer, relire, dire la suite
[S] Suivre : lister, commenter, résoudre, rouvrir   ←── validation
```

Lire `references/regles-api.md` avant le premier appel.

---

## Étape 0 — Repérer le problème et le projet

**Un problème qui bloque** : l'utilisateur ne peut pas le lever seul, dans la conversation, et il
empêche le projet d'avancer ou le skill de servir.

| Bloque (proposer) | Ne bloque pas (ne pas proposer) |
|---|---|
| accès refusé à un outil ou à des données, compte manquant | une erreur du skill que l'on corrige dans la conversation : la corriger |
| outil ou connecteur indisponible, fonction absente | une erreur réseau ponctuelle qu'un nouvel essai règle |
| donnée nécessaire absente ou inaccessible | une question à laquelle l'utilisateur sait répondre |
| règle de sécurité ou de conformité qui interdit l'usage | un choix que l'utilisateur doit faire lui-même |
| budget, achat ou validation attendue | |
| prestataire, collègue ou décision qui ne vient pas | |

**Le projet**, dans cet ordre :

1. L'exécution d'un skill de projet a échoué : l'id est dans l'en-tête de son `SKILL.md`,
   `metadata.teamstarter-project-id` (ou l'ancienne forme `teamstarter_project_id`). C'est le
   projet, et aucun autre.
2. L'utilisateur nomme le projet ou en donne l'id.
3. Sinon, ses projets en réalisation : identité confirmée comme le dit
   `references/regles-api.md` (« Qui est l'utilisateur du connecteur »), puis

```graphql
query($where: SequelizeJSON) {
  project(where: $where, order: "reverse:updatedAt", limit: 20) { id title status openBlockersCount }
}
```
variables : `{"where": {"d_organizerIds": {"contains": [<moi>]}, "status": {"in": ["CASHEDOUT", "DELIVERED"]}}}`

   Un seul projet : le proposer. Plusieurs : demander lequel.

## Étape 1 — Proposer de déclarer un blocage

Le problème vient d'arriver (un skill a échoué, l'utilisateur dit qu'il est bloqué) : le dire en
une phrase, puis proposer, une seule fois par problème :

> « L'accès au dossier Drive *Comptes rendus* est refusé : le skill ne peut pas tourner tant que
> ce n'est pas réglé. Je le déclare comme blocage sur ton projet *Rédiger les comptes rendus de
> réunion client* (#41207) ? »

- L'utilisateur demande lui-même à déclarer un blocage : passer directement à l'étape 2.
- Il refuse : ne pas reproposer pour le même problème dans la conversation.
- Il préfère d'abord essayer autre chose : l'aider, et reproposer seulement si le problème reste.

## Étape 2 — Connecteur et droits

1. Trouver le connecteur Teamstarter (plusieurs : celui de l'organisation du projet). Lancer
   `list-schema`.
2. Déclarer demande `run-mutation` et la mutation `projectBlockerCreate` ; commenter,
   `projectBlockerCommentCreate` ; résoudre, `projectBlockerUpdate`.
3. Seuls les **porteurs du projet et les admins** de l'organisation lisent et écrivent ses
   blocages. Un autre compte reçoit « Only the organizers of the project and the admins can
   manage its blockers. » : le dire, et proposer de transmettre le texte rédigé à un porteur.

Sans `run-mutation` (accès en lecture seule) ou sans ces mutations : rédiger quand même le
blocage (étape 5) et donner le geste dans l'app : page `/manage` du projet, section
« Blocages », bouton « Déclarer un blocage ». Ne jamais contourner par une autre mutation.

## Étape 3 — Statut du projet

```graphql
query($where: SequelizeJSON) { project(where: $where) { id title status openBlockersCount } }
```
variables : `{"where": {"id": <id>}}`

| `status` | Ce qui se passe |
|---|---|
| `CASHEDOUT` (en cours de réalisation) ou `DELIVERED` (mis en place) | continuer |
| `FROZEN` (temporairement gelé), `DRAFT`, `UNDER_REVIEW`, `PUBLISHED` | un blocage ne se déclare qu'en réalisation : le dire. Avant la validation, le problème se règle avec les animateurs (commentaire sur le projet) ; un projet gelé, avec les admins |
| `ENDED`, `CANCELLED` | les blocages du projet sont en lecture seule : le dire |

## Étape 4 — Blocages déjà ouverts

Lire les blocages du projet avant d'en déclarer un :

```graphql
query($where: SequelizeJSON) {
  projectBlocker(where: $where, order: "reverse:createdAt", limit: 50) {
    id title category description source isResolved resolvedAt commentsCount createdAt
    author { fullname }
  }
}
```
variables : `{"where": {"projectId": <id>}}` (`projectId` est obligatoire, sauf pour un admin).

- **Le même problème est déjà ouvert** : ne pas le déclarer une seconde fois. Proposer d'y
  ajouter un commentaire (ce qui est nouveau, l'erreur du jour, ce qui a été essayé) :

```graphql
mutation($c: projectBlockerCommentInput!) { projectBlockerCommentCreate(projectBlockerComment: $c) { id createdAt } }
```
variables : `{"c": {"projectBlockerId": <id du blocage>, "content": "<texte simple>"}}`

- **Le même problème a été résolu** et revient : proposer de le rouvrir (étape S) plutôt que
  d'en déclarer un nouveau.
- Un blocage `source` `cancellation` ou `cancellation-request` est un motif d'annulation, pas un
  blocage à commenter.

## Étape 5 — Rédiger le blocage

| Champ | Règle |
|---|---|
| `title` | ce qui bloque, en une phrase, **120 caractères au plus** (« Accès refusé au dossier Drive des comptes rendus clients ») |
| `category` | une des huit valeurs ci-dessous ; la nommer à l'utilisateur par son libellé |
| `description` | ce qui bloque ; ce qui a été essayé ; le contournement en place en attendant (ou « aucun ») ; qui peut débloquer. Pour l'échec d'un skill : le nom du skill, l'étape, l'outil et le message d'erreur |

| `category` | Libellé dans l'app | Exemples |
|---|---|---|
| `tool` | Outil ou technique | connecteur indisponible, fonction absente, outil en panne |
| `access` | Accès et droits | accès refusé, compte ou licence manquant, partage non fait |
| `security` | Sécurité ou conformité | donnée sensible interdite à l'IA, validation DSI ou RGPD attendue |
| `budget` | Budget ou achat | achat à valider, budget épuisé, abonnement à payer |
| `organization` | Organisation ou temps | pas de temps dégagé, décision attendue, priorité changée |
| `participation` | Participation des collègues | collègues qui ne testent pas, ne répondent pas |
| `provider` | Prestataire | prestataire en retard, devis attendu |
| `other` | Autre | le reste |

- **Rien de confidentiel** dans le texte : ni clé d'API, ni mot de passe, ni jeton, ni donnée
  personnelle ou nom de client lus pendant l'exécution. Le blocage est lu par les porteurs et
  les admins.
- Ne rien inventer : ce qui a été essayé et qui peut débloquer viennent de la conversation ou
  de l'utilisateur ; sinon « à préciser ».
- Montrer le blocage tel qu'il sera enregistré, et **attendre la validation**. L'utilisateur
  peut corriger chaque champ.

## Étape 6 — Déclarer, relire, dire la suite

```graphql
mutation($b: projectBlockerInput!) {
  projectBlockerCreate(projectBlocker: $b) { id title category description createdAt }
}
```
variables : `{"b": {"projectId": <id>, "title": "…", "category": "access", "description": "…"}}`

- Ne passer que ces quatre champs : `resolvedAt`, `resolvedById`, `source` et les autres sont
  posés par le serveur, qui refuse l'appel s'ils sont envoyés.
- Rapporter le blocage avec les valeurs relues dans la réponse.
- Dire ce qui se passe ensuite : **personne n'est prévenu tout de suite**. Le blocage apparaît
  dans la section « Blocages » de la page `/manage` du projet et dans la page « Blocages » des
  admins ; il devient une tâche non assignée des admins de l'organisation, dans leurs actions et
  leur récapitulatif hebdomadaire, jusqu'à ce que l'un d'eux la prenne.
- Donner le lien du projet quand l'adresse de l'app est connue :
  `<adresse de l'app>/<tag de l'organisation>/project/<id>/manage`.

Refus possibles :

| Message | À dire |
|---|---|
| « A blocker can only be declared on a project in realization or delivered. » | le projet n'est pas en réalisation (étape 3) |
| « This project is closed: its blockers are read-only. » | projet terminé ou annulé |
| « Only the organizers of the project and the admins can manage its blockers. » | le compte du connecteur n'est ni porteur ni admin |
| « A blocker needs a title. » / « A blocker needs a category from the list. » | corriger le champ, revalider |

## Étape S — Suivre les blocages

Sur demande (« quels sont les blocages de mon projet », « le blocage est levé ») :

- **Lister** : la requête de l'étape 4. Présenter les ouverts d'abord : titre, catégorie
  (libellé), déclaré par, le, nombre de commentaires ; puis le nombre de résolus.
  `project.openBlockersCount` donne le nombre d'ouverts.
- **Lire l'échange** avec les admins avant de dire qu'un blocage est sans réponse :
  `projectBlockerComment(where: {"projectBlockerId": <id>}) { content authorScope createdAt author { fullname } }`.
- **Commenter** : `projectBlockerCommentCreate` (étape 4), texte validé par l'utilisateur.
- **Résoudre** : après accord,

```graphql
mutation($b: projectBlockerInput!) { projectBlockerUpdate(projectBlocker: $b) { id isResolved resolvedAt } }
```
variables : `{"b": {"id": <id du blocage>, "isResolved": true}}` ; `false` le rouvre.

- **Modifier** le titre, la catégorie ou la description : même mutation, avec ces champs.
- La suppression ne se fait que dans l'app.

## Garde-fous

- **Jamais de déclaration, de commentaire ni de résolution sans l'accord de l'utilisateur** sur
  le texte exact.
- **Un seul projet** : celui de la métadonnée du skill, ou celui que l'utilisateur a confirmé.
- **Pas de doublon** : lire les blocages ouverts avant de déclarer.
- **Rien de confidentiel** dans un blocage ou un commentaire.
- Proposer une fois par problème ; un refus vaut pour la conversation.

## Tags de sécurité

`écriture` : déclare, commente, modifie et résout des blocages de projet, chaque fois après
validation de l'utilisateur. Aucune notification n'est envoyée au moment de l'écriture.

## Fallback

- **Pas de connecteur, ou accès en lecture seule** : rédiger le blocage et donner le geste dans
  l'app (page `/manage` du projet, « Déclarer un blocage »). Pour écrire depuis l'outil IA :
  l'administrateur de l'organisation ouvre l'accès en écriture, puis l'utilisateur reconnecte le
  connecteur en choisissant lecture et écriture.
- **`projectBlocker` absent de `list-schema`** (version ancienne de la plateforme) : même chose.

## Exemple

Le skill `cr-reunion-client` (`teamstarter-project-id: "41207"`) échoue : le connecteur Google
Drive répond « accès refusé » sur le dossier des comptes rendus. L'exécution est déclarée en
échec (`ts-general-declarer-execution-skill`), puis :

> « Le dossier Drive *Comptes rendus clients* n'est pas partagé avec toi : le skill ne peut pas
> l'écrire. Je le déclare comme blocage sur ton projet *Rédiger les comptes rendus de réunion
> client* (#41207) ? »

Après accord, aucun blocage ouvert sur le même problème, texte validé :

```json
{"b": {"projectId": 41207,
       "title": "Accès refusé au dossier Drive des comptes rendus clients",
       "category": "access",
       "description": "Le skill cr-reunion-client ne peut pas écrire dans le dossier Drive « Comptes rendus clients » (étape 3, connecteur Google Drive : « accès refusé »). Essayé : reconnecter le connecteur, même erreur. Contournement : le compte rendu est copié à la main dans le dossier. Qui peut débloquer : le propriétaire du dossier (équipe Sales Ops)."}}
```

## Ressources

- `references/regles-api.md` — règles du connecteur, statuts, identité de l'utilisateur (même
  fichier que dans `ts-general-creer-projet`).
- Skills voisins : `ts-general-declarer-execution-skill` (déclarer chaque exécution d'un skill
  de projet, qui passe la main ici sur un échec), `ts-general-creer-skill` (créer et tester un
  skill de projet), `ts-general-lister-projets` (voir ses projets).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-declarer-blocage` — domaine `general`,
verbe `declarer`, objet `blocage`.
