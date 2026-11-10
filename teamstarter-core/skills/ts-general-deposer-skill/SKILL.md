---
name: ts-general-deposer-skill
description: >-
  Enregistre automatiquement dans Teamstarter chaque nouvelle version d'un skill rattaché à
  Teamstarter : dès qu'un skill dont le SKILL.md porte la métadonnée teamstarter-project-id est
  écrit ou modifié (par ts-general-creer-skill, par skill-creator ou à la main), l'empaquette en
  fichier .skill (archive zip du dossier du skill) et appelle le tool upload-project-skill du
  connecteur MCP Teamstarter, pour que Teamstarter montre la dernière version du skill.
  Déclencher automatiquement, sans le demander à l'utilisateur, à la fin de chaque écriture ou
  modification d'un tel skill, ou quand l'utilisateur dit "enregistre mon skill dans
  Teamstarter", "dépose mon skill", "envoie la nouvelle version de mon skill". Ne rien
  enregistrer pour un skill sans cette métadonnée, pour un skill inchangé depuis son dernier
  dépôt, quand le skill est seulement exécuté ou lu, ni sans connecteur en écriture.
---

# Enregistrer chaque version d'un skill dans Teamstarter

## Quand utiliser ce skill

Un skill créé avec Teamstarter (skill `ts-general-creer-skill`) porte son id Teamstarter dans
ses métadonnées. Teamstarter garde le fichier du skill : la page du skill le montre, le propose
au partage avec toute l'organisation, et en garde les versions. Pour que Teamstarter montre
toujours la version en cours, **chaque version est enregistrée dès qu'elle est écrite**, sans le
demander : c'est ce que fait ce skill, par un appel au tool `upload-project-skill`, au nom de la
personne qui a branché le connecteur.

Ne pas utiliser pour autre chose : ce skill n'écrit rien d'autre dans Teamstarter. Déclarer une
exécution du skill, c'est `ts-general-declarer-execution-skill`.

## Ce que l'utilisateur lit

- **Première version, ou dépôt demandé par l'utilisateur** : une ligne, « Skill enregistré dans
  Teamstarter. »
- **Version qui suit une correction demandée par l'utilisateur** : rien. La correction se voit
  dans le skill ; l'enregistrement ne s'annonce pas.
- **Échec** : une ligne avec la raison (« Skill non enregistré dans Teamstarter : <raison>. »).
- Jamais le mot « projet » ni l'id : pour l'utilisateur, c'est son skill.

## Quand déclencher

À la fin de chaque écriture ou modification d'un skill dont l'en-tête du `SKILL.md` porte l'id :

```markdown
---
name: <nom-du-skill>
description: <…>
metadata:
  teamstarter-project-id: "<id>"
---
```

- Lire aussi l'ancienne forme, à la racine de l'en-tête : `teamstarter_project_id: <id>`.
- **Une modification = un dépôt**, une fois la modification terminée : plusieurs retouches dans
  la même réponse font un seul dépôt, avant la réponse finale. Trois corrections demandées l'une
  après l'autre font trois dépôts.
- **La première version aussi**, dès qu'elle est écrite et testée.
- **Tout le dossier du skill** est déposé : une modification de `references/`, `scripts/` ou
  `assets/` fait aussi une nouvelle version.
- **Sans le demander à l'utilisateur** : le dépôt fait partie de l'écriture du skill.

## Quand ne pas déclencher

- Le `SKILL.md` n'a pas d'id : ce n'est pas un skill Teamstarter. Ne rien faire, ne rien dire.
- L'id n'est pas un entier : ne rien déposer, et le signaler (l'en-tête est à corriger).
- **Rien n'a changé** depuis le dernier dépôt fait dans la conversation : ne rien déposer.
  Chaque dépôt crée une version de plus et, pour les admins de l'organisation, une tâche
  « partager ce fichier ».
- **Le skill est seulement exécuté, lu, résumé ou discuté** : pas de dépôt.
- L'en-tête est illisible (YAML cassé) : le corriger d'abord, puis déposer.
- Jamais « pour essayer le tool ».
- **Pas de connecteur Teamstarter, ou un connecteur sans le tool `upload-project-skill`** (accès
  en lecture seule) : ne pas passer par `run-mutation`, et le dire une fois : « Skill non
  enregistré dans Teamstarter : le connecteur ne le permet pas. Dépose le fichier
  `<nom-du-skill>.skill` sur la page de ton skill dans Teamstarter. » Plusieurs connecteurs :
  celui de l'organisation du skill.

## L'appel

1. **Empaqueter** le dossier du skill en `<nom-du-skill>.skill` : une archive zip qui contient
   `<nom-du-skill>/SKILL.md` et les autres fichiers du skill, `<nom-du-skill>` étant le `name`
   de l'en-tête. Depuis le dossier qui contient le dossier du skill :

```bash
python3 - <nom-du-skill> <<'EOF'
import base64, pathlib, sys, zipfile
name = sys.argv[1]
out = pathlib.Path(f"{name}.skill")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(pathlib.Path(name).rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.name != ".DS_Store":
            archive.write(path, path.as_posix())
print(base64.b64encode(out.read_bytes()).decode())
EOF
```

   Le script écrit le fichier `.skill` et affiche son contenu en base64 : le tool ne prend pas
   de chemin. Sans outil d'exécution de code, le skill ne peut pas être empaqueté : donner le
   dossier à l'utilisateur et le geste manuel (« Quand ne pas déclencher », dernier point).
2. **Appeler** :

```
upload-project-skill {
  "projectId": <id, entier>,
  "fileName": "<nom-du-skill>.skill",
  "contentBase64": "<le .skill en base64>"
}
```

| Argument | Valeur |
|---|---|
| `projectId` | l'id lu dans l'en-tête du `SKILL.md`, jamais un autre |
| `fileName` | `<nom-du-skill>.skill`, **le même à chaque dépôt** : chaque dépôt sous ce nom est la version suivante ; un autre nom ferait un second skill |
| `contentBase64` | l'archive entière, 1 Mo au plus une fois décodée |
| `version` | à omettre : Teamstarter prend la dernière plus un |

## Ce que répond Teamstarter

- **Succès** : `project.skillFileId` nomme la version déposée ; la précédente est gardée, mais
  n'est plus listée sur la page du skill.
- **« Only the organizers of the project can manage its files. »** : le compte du connecteur
  n'est pas porteur du skill (un admin non porteur est refusé aussi). Le dire, et proposer de
  demander à un porteur de déposer, ou de se faire ajouter comme porteur.
- **Nom de fichier, archive ou `name` refusés** (le fichier ne s'appelle pas
  `<nom-du-skill>.skill`, l'archive n'est pas un zip, ou son `SKILL.md` a un autre `name`) :
  refaire l'archive comme au point 1 et redéposer une fois.
- **Fichier trop gros** (plus de 1 Mo) : le dire ; les fichiers lourds du skill sont à réduire.
- **Autre refus** (autre organisation, type qui n'est pas un skill, accès qui ne peut pas
  écrire) : ne pas réessayer, ne pas contourner ; le dire en une ligne.

## Garde-fous

- N'écrit que le dépôt du skill, jamais par `run-mutation`.
- Ne modifie pas le skill.
- Ne dépose jamais sur un autre id que celui de l'en-tête, ni un skill inchangé.

## Tags de sécurité

`écriture` : un dépôt de fichier par version du skill, sans validation à chaque fois (le dépôt
fait partie de l'écriture du skill). Produit un fichier local (le `.skill`).

## Exemple

L'utilisateur demande d'ajouter une étape à son skill `cr-reunion-client`, dont l'en-tête porte
`metadata: { teamstarter-project-id: "41207" }`. Le `SKILL.md` est modifié et enregistré, le
dossier empaqueté en `cr-reunion-client.skill`, puis :

```
upload-project-skill {
  "projectId": 41207,
  "fileName": "cr-reunion-client.skill",
  "contentBase64": "UEsDBBQAAAAIAA…"
}
```

La réponse montre le skill modifié, sans ligne sur l'enregistrement : la modification suivait
une demande de l'utilisateur.

## Ressources

- Skills voisins : `ts-general-creer-skill` (créer le skill), `ts-general-declarer-execution-skill`
  (déclarer chaque exécution du skill).

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-deposer-skill` — domaine `general`,
verbe `deposer`, objet `skill`.
