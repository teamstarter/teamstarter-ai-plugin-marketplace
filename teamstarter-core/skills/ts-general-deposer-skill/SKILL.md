---
name: ts-general-deposer-skill
description: >-
  Dépose automatiquement dans Teamstarter chaque nouvelle version d'un skill rattaché à un projet
  Teamstarter : dès qu'un SKILL.md qui porte la métadonnée teamstarter-project-id est écrit ou
  modifié (par ts-general-creer-skill, par skill-creator ou à la main), appelle le tool
  upload-project-skill du connecteur MCP Teamstarter avec l'id du projet et le contenu du
  fichier, pour que le projet montre la dernière version de son skill. Déclencher
  automatiquement, sans le demander à l'utilisateur, à la fin de chaque écriture ou modification
  d'un tel SKILL.md, ou quand l'utilisateur dit "dépose mon skill", "mets à jour mon skill dans
  Teamstarter", "envoie la nouvelle version de mon skill". Ne rien déposer pour un SKILL.md sans
  cette métadonnée, pour un fichier inchangé depuis son dernier dépôt, quand le skill est
  seulement exécuté ou lu, ni sans connecteur en écriture.
---

# Déposer automatiquement chaque version d'un skill dans Teamstarter

## Quand utiliser ce skill

Un skill créé par un projet Teamstarter (skill `ts-general-creer-skill`) porte l'id de son projet
dans ses métadonnées. Le projet garde le fichier du skill : sa page `/manage` montre le dernier
déposé, le propose au partage avec toute l'organisation, et `project.skillFileId` le nomme. Pour
que le projet montre toujours la version en cours, **chaque version est déposée dès qu'elle est
écrite**, sans le demander : c'est ce que fait ce skill, par un appel au tool
`upload-project-skill`, au nom de la personne qui a branché le connecteur.

Ne pas utiliser pour autre chose : ce skill n'écrit rien d'autre dans Teamstarter. Déclarer une
exécution du skill, c'est `ts-general-declarer-execution-skill`.

## Sortie attendue

Un appel `upload-project-skill` par version, et une ligne dans la réponse :
« Version déposée sur le projet Teamstarter <id> (20/10 à 14 h 20). » ou la raison pour laquelle
elle ne l'est pas.

## Quand déclencher

À la fin de chaque écriture ou modification d'un `SKILL.md` dont l'en-tête porte l'id d'un
projet :

```markdown
---
name: <nom-du-skill>
description: <…>
metadata:
  teamstarter-project-id: "<id du projet>"
---
```

- Lire aussi l'ancienne forme, à la racine de l'en-tête : `teamstarter_project_id: <id>`.
- **Une modification = un dépôt**, une fois la modification terminée : plusieurs retouches du
  fichier dans la même réponse font un seul dépôt, avant la réponse finale. Trois corrections
  demandées l'une après l'autre font trois dépôts.
- **La première version aussi** : dès que le `SKILL.md` est écrit pour la première fois, avant de
  le montrer à l'utilisateur.
- **Sans le demander à l'utilisateur** : le dépôt fait partie de l'écriture du skill. Le dire
  après coup, en une ligne.
- Une modification d'un autre fichier du skill (`references/`, `scripts/`) sans modification du
  `SKILL.md` : ne rien déposer. Seul le `SKILL.md` est déposé.

## Quand ne pas déclencher

- Le `SKILL.md` n'a pas d'id de projet : ce n'est pas un skill de projet Teamstarter. Ne rien
  faire, ne rien dire.
- L'id n'est pas un entier : ne rien déposer, et le signaler (l'en-tête est à corriger).
- **Le contenu n'a pas changé** depuis le dernier dépôt fait dans la conversation : ne rien
  déposer. Chaque dépôt crée pour les admins de l'organisation une tâche « partager ce fichier » ;
  un fichier identique en créerait une de plus pour rien.
- **Le skill est seulement exécuté, lu, résumé ou discuté** : pas de dépôt. Une exécution se
  déclare avec `ts-general-declarer-execution-skill`.
- L'en-tête est illisible (YAML cassé) : le corriger d'abord, puis déposer.
- Jamais « pour essayer le tool ».
- **Pas de connecteur Teamstarter, ou un connecteur sans le tool `upload-project-skill`** (accès
  en lecture seule, ou plateforme qui ne l'expose pas encore) : ne pas passer par `run-mutation`,
  et le dire une fois dans la conversation : « Version non déposée : le connecteur Teamstarter ne
  permet pas de déposer un skill. Dépose le `SKILL.md` dans la section Fichiers de la page
  `/manage` du projet. » Plusieurs connecteurs : celui de l'organisation du projet.

## L'appel

1. Lire le `SKILL.md` tel qu'il est enregistré, après la modification.
2. L'encoder en base64 : le tool ne prend pas de chemin. Avec un outil d'exécution de code,
   `base64 -w0 SKILL.md` ou
   `python3 -c "import base64,sys;print(base64.b64encode(open(sys.argv[1],'rb').read()).decode())" SKILL.md` ;
   sans, encoder soi-même le contenu exact du fichier (UTF-8).
3. Appeler :

```
upload-project-skill {
  "projectId": <id du projet, entier>,
  "fileName": "SKILL.md",
  "contentBase64": "<contenu du SKILL.md en base64>"
}
```

| Argument | Valeur |
|---|---|
| `projectId` | l'id lu dans l'en-tête du `SKILL.md` déposé, jamais un autre |
| `fileName` | `SKILL.md` |
| `contentBase64` | le fichier entier, 1 Mo au plus une fois décodé |

## Ce que répond Teamstarter

- **Succès** : la réponse donne `project.skillFileId`, égal à l'id du `projectFile` créé ; c'est
  désormais le skill du projet. Les dépôts précédents restent dans les fichiers du projet.
- **« Only the organizers of the project can manage its files. »** : le compte du connecteur
  n'est pas porteur du projet (un admin non porteur est refusé aussi). Le dire, et proposer de
  demander à un porteur de déposer, ou de se faire ajouter comme porteur.
- **Fichier trop gros** (plus de 1 Mo) : le dire ; le `SKILL.md` est à raccourcir, le détail
  déplacé dans `references/`.
- **Autre refus** (projet d'une autre organisation, projet qui n'est pas un projet
  d'automatisation avec l'IA, accès qui ne peut pas écrire) : ne pas réessayer, ne pas
  contourner ; rapporter la raison en une ligne : « Version non déposée : <raison>. »

## Garde-fous

- N'écrit que le dépôt du `SKILL.md`, jamais par `run-mutation`.
- Ne modifie pas le skill.
- Ne dépose jamais sur un autre projet que celui de l'en-tête, ni un fichier inchangé.

## Tags de sécurité

`écriture` : un dépôt de fichier par version du skill, sans validation à chaque fois (le dépôt
fait partie de l'écriture du skill), annoncé à l'utilisateur.

## Exemple

L'utilisateur demande d'ajouter une étape à son skill `cr-reunion-client`, dont l'en-tête porte
`metadata: { teamstarter-project-id: "41207" }`. Le `SKILL.md` est modifié et enregistré, puis :

```
upload-project-skill {
  "projectId": 41207,
  "fileName": "SKILL.md",
  "contentBase64": "LS0tCm5hbWU6IGNyLXJldW5pb24tY2xpZW50Ci4uLg=="
}
```

Ligne finale : « Version déposée sur le projet Teamstarter 41207 (20/10 à 14 h 20). »

## Ressources

- Skills voisins : `ts-general-creer-skill` (créer le skill et suivre son projet),
  `ts-general-declarer-execution-skill` (déclarer chaque exécution du skill).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-deposer-skill` — domaine `general`,
verbe `deposer`, objet `skill`.
