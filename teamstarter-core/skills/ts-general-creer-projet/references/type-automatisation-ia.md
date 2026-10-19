# Type « Automatisation de processus avec l'IA » (`PROCESS_AUTOMATION_WITH_AI`)

Ce qui s'ajoute au parcours commun pour un projet qui automatise une tâche avec l'IA (un skill,
un agent, un assistant). Parcours joué en production en septembre 2026 (création, 14 réponses,
fiche rédigée et écrite, sans audit ni soumission).

Le type `AI_SKILL` (« AI Skill ») a la même structure de sections (`AI_SKILL_TASK`, `MY_TEAM`,
`AI_SKILL_IMPACT`, `AI_SKILL_EXPERTISE`, `AI_SKILL_ORGANIZATION`) ; ses tags de questions
commencent par `AI_SKILL_` au lieu de `AI_TASK_`. Il n'a pas encore été joué par le connecteur :
lire ses questions sur le projet créé, comme pour tout type.

## Règles du projet de création de skill

Un projet de l'un de ces deux types crée un skill. Ces règles valent pour tout le parcours, de
la création à la proposition, dans ce que Claude dit et demande à l'utilisateur :

1. **« Projet de création de skill », jamais « brouillon ».** Le projet tant qu'il n'est pas
   proposé (`EMPTY`, `DRAFT`) se nomme « ton projet de création de skill ». Les statuts
   techniques restent dans les requêtes.
2. **« Tâche », jamais « titre ».** Le titre du projet est la tâche à automatiser : un verbe à
   l'infinitif et son objet, 3 à 8 mots (« Rédiger les comptes rendus de réunion client »).
   Demander « Quelle tâche veux-tu automatiser ? », et l'afficher sous l'étiquette « Tâche » dans
   les récapitulatifs. La question `AI_TASK_DESCRIPTION` la détaille ensuite.
3. **Les questions telles qu'elles sont écrites dans Teamstarter.** Poser chaque question de
   structuration avec son libellé exact (`questionWordings.value` du projet), entre guillemets,
   sans la reformuler, la résumer ni la fusionner avec une autre. Une question par message ; les
   questions courtes (durée, fréquence, score, date) peuvent être envoyées ensemble, chacune sur
   sa ligne avec son libellé exact. Ce que Claude sait déjà de la tâche se montre sous la question
   (« Proposition : … ») : l'utilisateur répond, ou valide la proposition. Sa réponse s'écrit
   telle qu'il l'a donnée ; une correction (faute, donnée sensible) se montre avant d'écrire.

## Choisir le type et l'objectif

- `projectType(where: {"tag": "PROCESS_AUTOMATION_WITH_AI"}) { id tag isDisabled titleWordings { value } aiGlobalContextWordings { value } }`.
  `aiGlobalContextWordings` (FR) est le cahier des charges de construction de l'agent IA défini
  par l'organisation : le garder pour l'utilisateur, il en aura besoin pour construire l'agent
  une fois le projet validé.
- Objectif : celui dont `projectTypes` contient ce type, en statut `OPEN` (souvent « skills IA »
  ou « efficience »). Un seul : le prendre en le disant.
- Doublons : `project(where: {"objectiveId": <id>, "projectTypeId": <id>}, order: "reverse:createdAt", limit: 50) { id title status }`.
  Une tâche proche déjà portée par un projet : le montrer et proposer de rejoindre ce projet
  plutôt que d'en créer un.

## Les 16 questions

| Section | Tag | Question | Format | Obligatoire |
|---|---|---|---|---|
| Ma tâche métier | `AI_TASK_DESCRIPTION` | Quelle tâche souhaites-tu automatiser avec l'IA ? | text | oui |
| Ma tâche métier | `AI_TASK_STEPS` | Quelles sont les étapes précises à suivre pour réaliser cette tâche ? (3 à 6 étapes) | text | oui |
| Ma tâche métier | `AI_TASK_TRIGGER` | Qu'est-ce qui déclenche précisément la réalisation de cette tâche ? | text | oui |
| Ma tâche métier | `AI_TASK_TOOLS` | Quel(s) outil(s) utilises-tu actuellement pour accomplir cette tâche ? | text | oui |
| Ma tâche métier | `AI_TASK_DELIVERABLE` | Une fois la tâche terminée, quel est le livrable exact obtenu ? Dans quel outil et sous quel format ? | text | oui |
| Impact de l'IA | `AI_TASK_DURATION` | Combien de temps prend la tâche actuellement ? | short-text | oui |
| Impact de l'IA | `AI_TASK_MONTHLY_FREQUENCY` | Combien de fois la réalises-tu par mois (environ) ? | short-text | oui |
| Impact de l'IA | `impacts-objectives` | Dans quel objectif s'inscrit ton projet ? | objective | oui, pré-rempli |
| Impact de l'IA | `AI_TASK_BENEFICIARIES` | Qui d'autre dans l'entreprise réalise cette tâche et pourra bénéficier de cette automatisation ? | short-text | oui |
| Impact de l'IA | `AI_TASK_QUALITY_GAINS` | Sur quels aspects l'IA pourrait-elle faire gagner en qualité ? | text | oui |
| Expertise métier | `AI_TASK_EXPLAINABILITY_SCORE` | À quel point sais-tu expliquer comment réaliser cette tâche et évaluer son résultat ? (1 à 5) | score | oui |
| Expertise métier | `AI_TASK_BEST_PRACTICES` | As-tu déjà en tête des bonnes pratiques à suivre ou écueils à éviter ? | text | non |
| Expertise métier | `AI_TASK_EXPERT_CONTRIBUTION` | Certaines personnes ont-elles une expertise à apporter pour mieux la réaliser ? | text | non |
| Mon équipe | `team` | Est-ce que ce projet est organisé seul(e) ou en équipe ? | boolean | oui (`"0"` / `"1"`) |
| Organisation du projet IA | `AI_TASK_IMPLEMENTATION_DATE` | Quelle est la date prévisionnelle de réalisation de ton projet ? | date | oui |
| Organisation du projet IA | `AI_TASK_IMPLEMENTATION_STEPS` | Quelles sont les étapes de mise en œuvre de ton projet ? | text | oui, pré-rempli |

Les questions et leur libellé peuvent varier selon l'organisation : lire celles du projet créé,
ce tableau sert à préparer les réponses.

- Si l'utilisateur vient de faire la tâche avec l'IA dans la conversation : en tirer une
  proposition sous chaque question (règle 3), sans sauter la question.
- **Aucune donnée réelle sensible** dans les réponses (noms de clients, montants, données
  personnelles) : proposer un terme générique à la place, en le disant ; la fiche sera lue par
  d'autres.
- Pas de dépenses ni de campagne pour ce type.

## Fiche : correspondance réponses → sections

| Section | Obligatoire | Contenu | Réponses sources |
|---|---|---|---|
| La tâche à automatiser | oui | ce que la tâche produit et pour qui, ce qui la déclenche, le temps qu'elle prend (durée × fréquence, **en gras**) | DESCRIPTION, TRIGGER, DURATION, MONTHLY_FREQUENCY |
| Comment la tâche se déroule | oui | les étapes dans l'ordre (liste), les outils, le livrable exact | STEPS, TOOLS, DELIVERABLE |
| Ce que ça pourrait changer, et pour qui | oui | ce qui se prête à l'IA, les gains de qualité, qui d'autre fait la tâche | QUALITY_GAINS, BENEFICIARIES, EXPLAINABILITY_SCORE |
| L'expertise recherchée | non | l'expertise ou le métier recherché, en quoi la personne aiderait | BEST_PRACTICES, EXPERT_CONTRIBUTION ; vide si rien |

Style observé sur les fiches existantes : 2 à 4 paragraphes courts, première personne (« Cette
tâche me prend… »), chiffres en gras, liste à puces pour les étapes, pas de titre dans le contenu.

## Mode de décision

Les objectifs de ce type sont souvent en `SIMPLE_MODERATION` : écrire
`decisionMode: "MODERATION"` (voir la table du skill, étape 2).
