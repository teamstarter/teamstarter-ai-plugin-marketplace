---
name: ts-general-declarer-execution-skill
description: >-
  Déclare à Teamstarter chaque exécution d'un skill rattaché à un projet Teamstarter, pour les
  statistiques d'utilisation du projet : à la fin de toute exécution d'un
  skill dont le SKILL.md porte la métadonnée teamstarter-project-id, que l'exécution ait réussi
  ou échoué, appelle le tool report-skill-execution du connecteur MCP Teamstarter avec l'id du
  projet, l'heure, la durée, les tokens et le résultat ; la personne déclarée est celle du
  connecteur. Déclencher automatiquement, sans le demander à l'utilisateur, à la fin de
  l'exécution d'un tel skill, ou quand un skill demande de déclarer son exécution à Teamstarter.
  Ne rien déclarer pour un skill sans cette métadonnée, pour une exécution qui n'a pas eu lieu,
  ni sans connecteur en écriture. Une exécution bloquée par un problème qui empêche d'utiliser
  le skill : proposer de déclarer un point de blocage avec ts-general-creer-skill.
---

# Déclarer l'exécution d'un skill à Teamstarter

## Quand utiliser ce skill

Un skill créé par un projet Teamstarter (skill `ts-general-creer-skill`) porte l'id de son projet
dans ses métadonnées. Teamstarter enregistre chacune de ses exécutions et en tire les
statistiques du projet, affichées dans la carte « Utilisation du skill » de sa page `/manage` :
nombre d'exécutions, échecs, personnes distinctes, tokens, durée moyenne, dernière utilisation.
Teamstarter ne les connaît que si **l'agent qui exécute le skill les déclare** : c'est ce que
fait ce skill, par un appel au tool `report-skill-execution` à la fin de chaque exécution, au nom
de la personne qui a branché le connecteur.

Ne pas utiliser pour autre chose : ce skill n'écrit rien d'autre dans Teamstarter.

## Sortie attendue

Un appel `report-skill-execution` par exécution, et une ligne dans la réponse finale :
« Exécution déclarée à Teamstarter (projet <id>). » ou la raison pour laquelle elle ne l'est pas.

## Quand déclencher

À la fin de chaque exécution d'un skill dont l'en-tête du `SKILL.md` porte l'id d'un projet :

```markdown
---
name: <nom-du-skill>
description: <…>
metadata:
  teamstarter-project-id: "<id du projet>"
---
```

- Lire aussi l'ancienne forme, à la racine de l'en-tête : `teamstarter_project_id: <id>`.
- **Une exécution = un appel**, que le skill ait réussi ou échoué. Trois exécutions dans une
  conversation font trois appels, chacun avec son `executionId`.
- **Sans le demander à l'utilisateur** : la déclaration fait partie de l'exécution du skill. La
  dire après coup, en une ligne.

## Quand ne pas déclencher

- Le `SKILL.md` n'a pas d'id de projet : ce n'est pas un skill de projet Teamstarter. Ne rien
  faire, ne rien dire.
- L'id n'est pas un entier : ne rien déclarer, et le signaler (l'en-tête est à corriger).
- **L'exécution n'a pas eu lieu** : l'utilisateur a lu, résumé, modifié ou discuté le skill, ou
  l'a interrompu avant sa première étape. Une exécution commencée puis arrêtée a eu lieu : elle se
  déclare avec `outcome: "failure"`.
- Jamais « pour essayer le tool ».
- **Pas de connecteur Teamstarter, ou un connecteur sans le tool `report-skill-execution`** (accès
  en lecture seule, ou plateforme qui ne l'expose pas encore) : ne rien déclarer, ne pas passer par
  `run-mutation`, et le dire une fois dans la conversation : « Exécution non déclarée à
  Teamstarter : le connecteur Teamstarter ne permet pas de la déclarer. » Plusieurs connecteurs :
  celui de l'organisation du projet.

## L'appel

Avant la première étape du skill : générer un `executionId` (UUID v4) et noter l'heure de début.
Après la dernière étape, avant la réponse finale :

```
report-skill-execution {
  "projectId": <id du projet, entier>,
  "inputTokens": <entier ≥ 0>,
  "outputTokens": <entier ≥ 0>,
  "durationMs": <entier ≥ 0>,
  "executedAt": "<début de l'exécution, ISO 8601 UTC>",
  "outcome": "success" | "failure",
  "executionId": "<UUID de cette exécution>"
}
```

| Argument | Valeur |
|---|---|
| `projectId` | l'id lu dans l'en-tête du `SKILL.md` exécuté, jamais un autre |
| `inputTokens`, `outputTokens` | les tokens de l'exécution quand l'outil les affiche ; sinon une estimation : nombre de caractères lus par l'exécution (skill, messages, résultats d'outils) divisé par 4 pour l'entrée, caractères produits divisés par 4 pour la sortie. Dire dans la ligne finale qu'ils sont estimés |
| `durationMs` | de la première étape à la dernière, d'après l'heure notée au début ; `0` sans horloge, en le disant |
| `executedAt` | l'heure de début ; omise, Teamstarter prend l'heure de réception |
| `outcome` | `success` si le skill a livré ce qu'il devait ; `failure` sur une erreur, une interruption, un résultat non livré |
| `executionId` | le même pour toute nouvelle tentative de la même déclaration : Teamstarter n'écrit rien de plus et répond `created: false`. 255 caractères au plus : un UUID convient |

## Ce que répond Teamstarter

- `created: true` : l'exécution est enregistrée au nom de la personne du connecteur, et comptée
  dans la carte « Utilisation du skill » du projet. Aucune notification n'est envoyée.
- `created: false` : cette exécution était déjà déclarée. Ne pas rappeler avec un autre id.
- **Refus** (projet d'une autre organisation, projet d'un type qui ne compte pas les
  exécutions, accès qui ne peut pas écrire) : ne pas réessayer, ne pas contourner ; rapporter la
  raison en une ligne : « Exécution non déclarée : <raison>. »

## Après la déclaration

Si l'exécution a échoué sur un problème que l'utilisateur ne peut pas lever seul (accès refusé,
outil indisponible, donnée manquante, règle de sécurité) : proposer de le déclarer comme point de
blocage du projet avec `ts-general-creer-skill` (étape B). Ne pas le déclarer sans accord.

## Garde-fous

- N'écrit que la déclaration d'exécution, jamais par `run-mutation`.
- Ne modifie pas le skill exécuté.
- Ne déclare jamais une exécution qui n'a pas eu lieu, ni sur un autre projet que celui de
  l'en-tête.

## Tags de sécurité

`écriture` : une déclaration d'exécution par exécution, sans validation à chaque fois (la
déclaration fait partie de l'exécution du skill), annoncée à l'utilisateur.

## Exemple

`SKILL.md` avec `metadata: { teamstarter-project-id: "41207" }`. Début à 10:15:00 UTC, fin à
10:16:30 UTC, résultat livré, tokens estimés.

```
report-skill-execution {
  "projectId": 41207,
  "inputTokens": 18400,
  "outputTokens": 2300,
  "durationMs": 90000,
  "executedAt": "2026-10-16T10:15:00Z",
  "outcome": "success",
  "executionId": "6f1c2a3e-9b7d-4e2a-8c1f-2d5b7a9e4c11"
}
```

Ligne finale : « Exécution déclarée à Teamstarter (projet 41207, tokens estimés). »

## Ressources

- Skill voisin : `ts-general-creer-skill` (créer le skill, déposer ses versions, déclarer un
  blocage).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-declarer-execution-skill` — domaine
`general`, verbe `declarer`, objet `execution-skill`.
