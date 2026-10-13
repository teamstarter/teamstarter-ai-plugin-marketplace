---
name: ts-general-lister-projets
description: >-
  Liste les projets Teamstarter de l'utilisateur via le connecteur MCP Teamstarter, regroupés
  comme dans la page Mes projets de l'app : en structuration, en cours de rédaction, en attente
  de modération, soumis au vote, en cours de financement, en réalisation, mis en place. Donne
  pour chacun l'étape suivante, et propose de reprendre un brouillon avec ts-general-creer-projet.
  Lecture seule. Déclenche SYSTÉMATIQUEMENT dès que l'utilisateur mentionne "mes projets", "où
  en sont mes projets", "liste mes projets", "mes brouillons", "quels projets j'ai proposés",
  "mes projets en cours de financement", "mes projets en attente de modération", "qu'est-ce qu'il
  me reste à faire sur Teamstarter", "reprendre un projet", "retrouver mon projet". Déclencher
  même sans le mot "projet" si l'utilisateur demande l'état de ses initiatives Teamstarter. Ne
  pas déclencher pour créer un projet (ts-general-creer-projet).
---

# Lister ses projets Teamstarter et choisir lequel reprendre

## Quand utiliser ce skill

Un collaborateur veut savoir où en sont ses projets Teamstarter, ou retrouver un brouillon pour
le terminer. Le skill lit ses projets sur la plateforme, les regroupe par statut avec les
libellés de l'app, et dit pour chacun ce qui reste à faire. La plateforme garde tout l'état des
projets : rien n'est stocké dans la mémoire de l'outil IA, et la liste est la même dans Claude,
ChatGPT ou l'app.

Ne pas utiliser pour créer, modifier ou proposer un projet : `ts-general-creer-projet`.

## Sortie attendue

Un tableau par groupe de statut, dans l'ordre de la page « Mes projets », avec pour chaque
projet : titre, id, type, dernière mise à jour, et l'étape suivante. Puis une question : quel
projet reprendre, ou rien.

## Vue d'ensemble du workflow

```
[0] Connecteur (lecture suffit)
[1] Brouillons de l'utilisateur (scopeForMe)
[2] Identité de l'utilisateur, si les autres statuts sont demandés   ←── confirmation
[3] Projets proposés, publiés, en réalisation, mis en place
[4] Présenter par groupe, avec l'étape suivante
[5] Proposer de reprendre un brouillon → ts-general-creer-projet
```

Lire `references/regles-api.md` avant le premier appel.

---

## Étape 0 — Connecteur

Trouver le connecteur Teamstarter (plusieurs : demander lequel). `list-schema` suffit à vérifier
que `project` et `projectCount` sont lisibles. Un accès multi-organisations (staff) : demander
l'organisation et passer son `organizationTag`.

## Étape 1 — Les brouillons de l'utilisateur

```graphql
query($where: SequelizeJSON) {
  project(where: $where, scopeForMe: true, order: "reverse:updatedAt", limit: 50) {
    id title status isBeingStructured projectTypeId updatedAt
    d_factoryCompletionRate d_draftCompletionRate
  }
}
```
variables : `{"where": {"statusGroup": {"in": ["structuration", "writing"]}}}`

`scopeForMe: true` garde les brouillons dont l'utilisateur est l'auteur, le porteur ou un invité.
Sans lui, la liste contiendrait les brouillons de toute l'organisation.

Si l'utilisateur ne demandait que ses brouillons, passer à l'étape 4.

## Étape 2 — Identité de l'utilisateur

Les projets proposés ou publiés sont visibles par toute l'organisation : pour ne garder que
ceux de l'utilisateur, il faut son id. Le retrouver comme le dit `references/regles-api.md`
(« Qui est l'utilisateur du connecteur »), et **le faire confirmer** avant de filtrer.

Sans confirmation : n'afficher que les brouillons (étape 1) et les projets en attente de
modération, que la liste ne montre qu'à leurs auteurs et porteurs (sauf pour un accès
administrateur).

## Étape 3 — Les autres projets

Une seule requête, avec un alias par groupe :

```graphql
query($moderation: SequelizeJSON, $published: SequelizeJSON, $realization: SequelizeJSON, $done: SequelizeJSON) {
  moderation: project(where: $moderation, order: "reverse:updatedAt", limit: 50) { id title status projectTypeId underReviewAt updatedAt }
  published: project(where: $published, order: "reverse:updatedAt", limit: 50) { id title status decisionMode projectTypeId publishedAt fundingEndedAt estimate d_credit d_backersCount updatedAt }
  realization: project(where: $realization, order: "reverse:updatedAt", limit: 50) { id title status projectTypeId committedDeliveredAt updatedAt }
  done: project(where: $done, order: "reverse:updatedAt", limit: 50) { id title status projectTypeId deliveredAt updatedAt }
}
```
variables, avec `<moi>` l'id confirmé :
```json
{
  "moderation":  {"d_organizerIds": {"contains": [<moi>]}, "statusGroup": {"in": ["moderation"]}},
  "published":   {"d_organizerIds": {"contains": [<moi>]}, "statusGroup": {"in": ["vote", "funding", "participantSearch", "campaignFailed"]}},
  "realization": {"d_organizerIds": {"contains": [<moi>]}, "statusGroup": {"in": ["realization"]}},
  "done":        {"d_organizerIds": {"contains": [<moi>]}, "statusGroup": {"in": ["delivered", "ended"]}}
}
```

- `d_organizerIds` contient l'auteur et les co-porteurs : c'est le filtre de la page « Mes
  projets » de l'app.
- Pour départager vote, financement et recherche de participants dans `published`, refaire
  une requête par `statusGroup` si l'utilisateur veut ce détail ; sinon, se fier à
  `decisionMode` (`VOTE` = soumis au vote, `CONTRIBUTE` = financement).
- Une liste plafonne à 50 lignes : au-delà, `projectCount` avec le même `where`, et le dire.
- Type : lire une fois `projectType { id tag titleWordings { value } }` et afficher le titre.

## Étape 4 — Présenter

Un tableau par groupe non vide, dans cet ordre, avec le libellé de l'app :

| Groupe | Libellé | Étape suivante à afficher |
|---|---|---|
| `structuration` | Structuration | questions restantes (`d_factoryCompletionRate` < 1) ou fiche à générer |
| `writing` | En cours de rédaction | fiche à compléter (`d_draftCompletionRate` < 100), audit, puis proposer |
| `moderation` | En attente de modération | en relecture depuis `underReviewAt` ; rien à faire, sauf répondre à un retour |
| `vote` | Soumis au vote | fin du vote (`fundingEndedAt`) |
| `funding` | En cours de financement | financé à `d_credit` / `estimate` (montants en centimes), `d_backersCount` contributeurs, fin `fundingEndedAt` |
| `participantSearch` | Recherche de participants | inscriptions en cours |
| `campaignFailed` | Campagne échouée | peut être proposé à nouveau |
| `realization` | En cours de réalisation | date de mise en place prévue (`committedDeliveredAt`) |
| `delivered` | Mis en place | mis en place le `deliveredAt` |
| `ended` | Terminé | — |

Colonnes : titre, `#id`, type, mis à jour le (date seule), étape suivante. Une organisation peut
renommer un libellé dans son app : en cas de doute, ajouter le statut technique entre
parenthèses. Ne jamais écrire « tu n'as aucun projet » d'après une liste vide quand l'identité
n'a pas été confirmée : dire ce qui n'a pas pu être lu.

Donner le lien de chaque projet quand l'adresse de l'app est connue
(`<adresse de l'app>/<tag de l'organisation>/project/<id>`).

## Étape 5 — Reprendre un projet

Proposer de reprendre un brouillon (« Je reprends lequel ? »). Sur choix de l'utilisateur, passer
la main à `ts-general-creer-projet` avec l'id du projet : il relit l'état et repart de la
première étape non faite. Un projet en campagne échouée se propose à nouveau par le même skill.

## Garde-fous

- **Lecture seule** : ce skill n'appelle jamais `run-mutation`.
- **Ne pas filtrer sur un id non confirmé** par l'utilisateur.
- **Ne pas présenter une liste partielle comme complète** : liste plafonnée, identité inconnue,
  accès sans le droit de voir un statut — le dire.

## Tags de sécurité

aucun : lecture seule, pas de fichier produit.

## Fallback

- **Pas de connecteur** : dire que le connecteur Teamstarter n'est pas connecté. Il se connecte
  depuis l'onglet Connecteurs du plugin Teamstarter (ou les paramètres des connecteurs de l'outil
  IA), avec le compte Teamstarter de l'utilisateur. En attendant, renvoyer vers la page « Mes
  projets » de l'app.
- **Filtre `statusGroup` refusé par le serveur** (version ancienne) : filtrer sur `status`
  (`DRAFT`, `UNDER_REVIEW`, `PUBLISHED`, `CASHEDOUT`, `DELIVERED`) et regrouper soi-même avec le
  tableau de `references/regles-api.md`.

## Ressources

- `references/regles-api.md` — règles du connecteur, table des statuts, identité de
  l'utilisateur (même fichier que dans `ts-general-creer-projet`).
- Skill voisin : `ts-general-creer-projet` (créer, reprendre, proposer un projet).
- Parcours Teamstarter : étape `PMG-B-15`, l'équivalent de la page « Mes projets » (`/myspace`).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-lister-projets` — domaine `general`,
verbe `lister`, objet `projets`.
