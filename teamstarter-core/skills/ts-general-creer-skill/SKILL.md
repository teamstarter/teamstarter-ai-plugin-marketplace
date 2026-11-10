---
name: ts-general-creer-skill
description: >-
  Point d'entrée quand l'utilisateur veut créer un skill, un agent IA ou automatiser une tâche
  avec Claude, via le connecteur MCP Teamstarter. Regarde si une idée ou un skill proche existe
  déjà dans Teamstarter, présente les étapes, comprend la tâche (étapes, sources de données,
  découpage en plusieurs skills), crée le skill dans Teamstarter sans le demander, propose une
  réponse à chaque question de structuration que l'étape 1 n'a pas couverte et la fait valider,
  fait la fiche et
  l'audit, l'envoie en validation ou le publie sans demander quand l'organisation
  ne modère pas, construit et teste le skill en suivant le prompt de création de Teamstarter,
  l'enregistre dans Teamstarter, le présente (entrées, sorties, étapes) et propose une première
  exécution. Déclenche SYSTÉMATIQUEMENT, avant skill-creator, dès que l'utilisateur mentionne
  "créer un skill", "nouveau skill", "créer un agent", "automatiser une tâche avec Claude",
  "crée le skill de", "reprendre mon skill", "modifier mon skill", "usage de mon skill".
---

# Créer un skill avec Teamstarter

## Quand utiliser ce skill

Un collaborateur veut un skill (un agent, un assistant) qui fait une tâche de son travail. Dans
son organisation, chaque skill est enregistré dans Teamstarter : sa tâche y est structurée, il
y est validé, son fichier y est déposé, ses exécutions y sont comptées. Techniquement, c'est un
projet Teamstarter de type « Automatisation de processus avec l'IA » ; pour l'utilisateur, c'est
**son skill**.

Ce skill mène toute la création, de la première question à la première exécution, en demandant
le moins possible : l'utilisateur décrit sa tâche, valide les réponses de structuration une à
une, puis regarde le skill créé et l'essaie. Il sert aussi à reprendre un skill commencé, à
modifier un skill existant, à lire son utilisation ou à déclarer un blocage.

Il passe avant `skill-creator` : `skill-creator` ne sert qu'à l'étape 5, pour ce que le prompt
de Teamstarter ne dit pas.

## Règles de la conversation (obligatoires)

1. **Ne jamais demander à l'utilisateur de confirmer son identité.** Le retrouver sans rien lui
   demander (« Qui est l'utilisateur du connecteur », `references/regles-api.md`) ; sans
   résultat, travailler sans son id.
2. **Parler de skill, jamais de projet.** Dans tout ce que l'utilisateur lit, y compris le
   libellé des questions de structuration :

   | Dans Teamstarter | À dire |
   |---|---|
   | le projet, ton projet, le projet de création de skill, le brouillon | ton skill |
   | le titre du projet | la tâche |
   | la fiche du projet | la fiche de ton skill |
   | projet en relecture, validé, en réalisation | skill en attente de validation, validé |
   | la page `/manage` du projet | la page de ton skill dans Teamstarter |

   Un libellé de Teamstarter qui contient « projet » se montre avec « skill » à la place, et
   n'est pas modifié autrement.
3. **Les étapes de la structuration, jamais les « sections ».** Les questions de structuration
   sont regroupées par Teamstarter en sections : chacune est une **étape de la structuration**
   (« Étape 2/5 de la structuration : Impact de l'IA »). Le mot « section » n'apparaît jamais.
4. **Les mises à jour sont silencieuses.** Après un retour de l'utilisateur, appliquer la
   correction et continuer, sans dire « j'ai mis à jour », « j'ai corrigé », « nouvelle
   version », ni annoncer un nouveau dépôt. Montrer le résultat quand il faut le revoir, sans
   commentaire sur ce qui a changé.
5. **Suivre le prompt de création de Teamstarter** pour la construction et pour les tests du
   skill (étape 5). Il passe avant `skill-creator` et avant les habitudes de Claude.
6. **Les étapes s'enchaînent en silence.** Ne jamais annoncer « je passe à l'étape suivante »,
   ni demander la permission de continuer, de créer le skill dans Teamstarter, de lancer la
   fiche ou l'audit, de l'envoyer en validation, de le **publier**, de récupérer le prompt ou
   d'enregistrer le skill. Questions interdites, même avec l'outil de question : « Je le
   publie ? », « Je l'envoie en validation ? », « Je le crée dans Teamstarter ? », « Je
   récupère le prompt ? », « Je l'enregistre ? », « Ce nom te va ? », et toute question sur un
   choix de construction (étape 5). **La demande de l'utilisateur de créer un
   skill est la demande explicite qui couvre toutes les écritures de la création** :
   création, réponses validées, fiche, audit, envoi en validation, publication, enregistrement
   des versions, étapes cochées. Elle satisfait la règle du connecteur « jamais `run-mutation`
   sans une demande de l'utilisateur », et la confirmation explicite que
   `ts-general-creer-projet` demande avant de proposer un projet ne s'applique pas ici. Les
   seules questions sont : le choix proposé au préambule quand une idée ou un skill
   proche existe, celles de l'étape 1, la validation de chaque réponse de structuration (et les
   noms des co-porteurs), le choix de l'objectif s'il y en a plusieurs, ce que l'audit ne
   permet pas de trancher seul, et les propositions des étapes 6 et 7.
7. **Toute question passe par l'outil de question** de l'outil IA (`ask_user`,
   `AskUserQuestion` dans Claude Code et Cowork), à toutes les étapes, l'étape 1 comprise :
   **jamais une question, ni une liste de questions, écrite dans le texte de la réponse**.
   Chaque question a des réponses proposées (2 à 4), la plus probable en premier ; la réponse
   libre reste toujours possible. Ce qu'une question ouverte demande (les étapes du processus,
   un exemple) se propose : écrire la proposition dans la conversation, puis l'outil de
   question pour la valider ou la corriger. Sans cet outil : une seule question par message,
   avec ses réponses proposées numérotées.

## Vue d'ensemble

```
[P] Préambule : idée ou skill existant ? Présenter les étapes     (rien trouvé : en silence)
[1] Comprendre la tâche                ←── questions à l'utilisateur
[2] Structurer le skill dans Teamstarter  ←── création sans demander ; chaque réponse validée
[3] Fiche et audit                     ←── sans rien demander
[4] Validation, puis prompt de création   ←── sans modération : directement le prompt
[5] Construire, tester, enregistrer le skill   ←── en suivant le prompt
[6] Présenter le skill : entrées, sorties, étapes   ←── changements possibles
[7] Proposer une première exécution
[U] Utilisation du skill · [B] Blocage · [R] Reprise
```

Lire `references/regles-api.md` avant le premier appel.

---

## Préambule

1. **Connecteur, en silence.** Trouver le connecteur Teamstarter (plusieurs : celui de
   l'organisation de l'utilisateur ; doute réel : demander lequel). `list-schema`. Sans
   `run-mutation`, l'accès est en lecture seule → Fallback. Noter les capacités :

| Capacité | Sert à | Absente |
|---|---|---|
| `projectCreate`, `projectUpdate`, `AIprojectQuestionAnswerCreate` | créer et structurer le skill | Fallback |
| `projectGenerateSheet`, `projectEvaluateLimits` | fiche et audit (étape 3) | fiche rédigée par Claude ; pas d'audit |
| tool `get-skill-creation-instructions` | prompt de création (étape 4) | l'utilisateur copie le prompt depuis la page de son skill (« Copier le prompt ») |
| tool `upload-project-skill` | enregistrer le skill (étape 5) | l'utilisateur dépose le fichier `.skill` sur la page de son skill |
| tool `report-skill-execution` | compter les exécutions | les exécutions ne sont pas comptées |
| mutation `setProjectWorkflowActionStatus` | cocher « Créer mon agent IA » et « Tester l'agent » | l'utilisateur les coche sur la page de son skill |

   Une capacité absente : le dire une seule fois, en une phrase, au moment où elle manque.

2. **Une reprise ou une modification ?** L'utilisateur ouvre un `SKILL.md` qui porte
   `metadata.teamstarter-project-id`, nomme un skill existant, ou demande de le modifier :
   aller à « Reprise » (R). Une **modification** d'un skill existant ne présente pas les étapes
   et ne dit rien de plus : faire la modification (étape 5, puis 6).

3. **Une idée ou un skill existe-t-il déjà ?** Dès que la tâche est connue (dans la demande,
   sinon pendant l'étape 1, avant de créer quoi que ce soit) :

```graphql
query($t: SequelizeJSON) { projectType(where: $t) { id tag isDisabled } }
```
variables : `{"t": {"tag": {"in": ["PROCESS_AUTOMATION_WITH_AI", "AI_SKILL"]}}}`

```graphql
query($i: SequelizeJSON, $p: SequelizeJSON) {
  idea(where: $i, isLaunched: false, limit: 50) {
    id createdAt isAnonymized titleWordings { value language } descriptionWordings { value language } author { fullname }
  }
  skills: project(where: $p, order: "reverse:updatedAt", limit: 50) { id title status skillFileId d_organizerIds }
  mine: project(where: $p, scopeForMe: true, order: "reverse:updatedAt", limit: 20) { id title status }
}
```
variables : `{"i": {"projectTypeId": {"in": [<ids>]}}, "p": {"projectTypeId": {"in": [<ids>]}}}`

   Comparer les titres et descriptions à la tâche (même action, même livrable). Écarter les
   statuts `CANCELLED`, `ENDED`, `DELETED`.

   | Trouvé | Question (outil de question) |
   |---|---|
   | rien | aucune : continuer en silence |
   | une idée proche | « L'idée *X* (de <auteur>) décrit cette tâche. » → « Partir de cette idée » / « Créer un nouveau skill » |
   | un skill de l'utilisateur (dans `mine`, ou `d_organizerIds` contient son id) | « Tu as déjà commencé le skill *X*. » → « Reprendre ce skill » / « Créer un nouveau skill » |
   | le skill d'un collègue, déjà créé (`skillFileId` renseigné) | « <Porteur> a déjà un skill *X* pour cette tâche. » → « Créer quand même » / « Voir ce skill » (lien de sa page) |
   | le skill d'un collègue en cours | même question, sans « Voir ce skill » |

   Partir d'une idée : garder son id (`sourceIdeaId`, étape 2) et son texte pour l'étape 1.
   Reprendre : aller à « Reprise ».

4. **Présenter les étapes**, pour une nouvelle création seulement :

> Voici comment on va créer ton skill :
> 1. Comprendre ta tâche : ses étapes, ses données, comment tu la fais aujourd'hui.
> 2. La structurer dans Teamstarter : je te propose une réponse à chaque question, tu valides.
> 3. Préparer la fiche de ton skill et son audit : je m'en occupe.
> 4. La validation par les animateurs, si ton organisation la demande.
> 5. Construire le skill, le tester et l'enregistrer dans Teamstarter.
> 6. Te le présenter : ce qu'il prend, ce qu'il produit, ses étapes. Tu peux tout changer.
> 7. Le lancer une première fois.

   Puis enchaîner sur l'étape 1, dans le même message.

## Étape 1 — Comprendre la tâche

Comprendre la tâche assez pour répondre à toutes les questions de structuration et pour
construire le skill, en partant de ce que l'utilisateur a déjà dit (et de l'idée de départ, le
cas échéant).

**Comment poser les questions** (règle 7) :

- **Toujours avec l'outil de question**, jamais en liste dans le texte. Une question par appel ;
  des questions courtes à choix sur le même sujet (« Pour qui ? », « À quelle fréquence ? »)
  peuvent partir dans le même appel quand l'outil en accepte plusieurs, quatre au plus.
- **Ne demander que ce qui manque** : ce que la demande, l'idée de départ ou les connecteurs
  disent déjà ne se redemande pas.
- **Toujours des réponses proposées**, tirées du contexte, la plus probable en premier :
  « Pour qui est le résultat ? » → « Pour moi » / « Pour mon équipe » / « Pour la direction » ;
  « À quelle fréquence ? » → « Chaque semaine » / « Chaque mois » / « À la demande » ; « D'où
  viennent les données ? » → les outils dont un connecteur est branché, puis « Ailleurs ».
- **Une question ouverte devient une proposition à valider** : écrire dans la conversation ce
  que Claude comprend (les étapes du processus, les mesures d'un rapport, le livrable), puis
  l'outil de question : « C'est bien ça ? » → « Oui » / « À corriger » (la réponse libre dit
  quoi).
- Une réponse qui ouvre une nouvelle question : la poser de la même façon, à la suite.

**Ce qu'il faut savoir** — de quoi répondre aux questions de structuration du type
(`references/type-automatisation-ia.md`, « Les 16 questions ») : ce que l'utilisateur dit ou
valide ici n'est plus demandé à l'étape 2.

- **La tâche** : ce qu'elle produit, pour qui, ce qui la déclenche, combien de temps elle prend
  et combien de fois par mois.
- **Les étapes du processus**, dans l'ordre, telles qu'il les fait aujourd'hui ; demander un
  exemple récent quand c'est flou.
- **Les sources de données** : d'où viennent les informations à chaque étape (outil, fichier,
  boîte mail, CRM, dossier partagé), sous quelle forme, et où va le livrable. Vérifier quels
  connecteurs de l'outil IA y donnent accès ; une source inaccessible est notée pour l'étape 5.
- **Le savoir-faire** : les règles, bonnes pratiques et pièges ; qui d'autre fait la tâche ou
  s'y connaît.
- **Le découpage** : si le processus enchaîne des tâches distinctes (déclencheurs, livrables ou
  personnes différents), proposer de les séparer, avec l'outil de question : « Un skill pour
  tout le processus » / « Un skill par tâche » (en nommant les tâches). Un skill par tâche :
  créer d'abord celui que l'utilisateur choisit, et garder la liste des autres pour la fin
  (étape 7).

Pas de donnée sensible gardée pour la suite : un nom de client, un montant, une donnée
personnelle deviennent un terme générique dans les réponses.

Quand ces points sont couverts, passer à l'étape 2 sans l'annoncer.

## Étape 2 — Structurer le skill dans Teamstarter

**Créer, sans le demander.** Les mutations sont celles de `references/questions-structuration.md`
et de `references/type-automatisation-ia.md` ; ce qui suit remplace leurs validations.

1. **Type** : `PROCESS_AUTOMATION_WITH_AI` (sinon `AI_SKILL`), non `isDisabled`. Aucun des deux
   → Fallback.
2. **Objectif** : `objective(limit: 50) { id status mode titleWordings { value } projectTypes { id } }`,
   garder les `OPEN`. D'abord ceux dont `projectTypes` contient le type ; sinon ceux sans
   `projectTypes`. Un seul : le prendre. Plusieurs : outil de question « Dans quel objectif
   s'inscrit ton skill ? », leurs titres en choix. `decisionMode` : `SIMPLE_MODERATION` →
   `MODERATION`, `CALLFORPROJECTS` et `CROWDSOURCING` → `VOTE`, `CROWDFUNDING` → `CONTRIBUTE`.
3. **Tâche** (le titre) : un verbe à l'infinitif et son objet, 3 à 8 mots ; **description** de
   120 caractères au plus. Tirées de l'étape 1.
4. Créer, puis compléter (`projectCreate` ignore `decisionMode` et `isBeingStructured`, et
   échoue sur une description trop longue) :

```graphql
mutation($project: projectInput!) { projectCreate(project: $project) { id title status organizationId authorId } }
```
variables : `{"project": {"title": "<tâche>", "projectTypeId": <id>, "objectiveId": <id>, "language": "fr", "status": "DRAFT", "isParticipatingEnabled": true}}`
(+ `"sourceIdeaId": <id>` si l'on part d'une idée)

```graphql
mutation($project: projectInput!) { projectUpdate(project: $project) { project { id shortDescription decisionMode isBeingStructured } } }
```
variables : `{"project": {"id": <id>, "shortDescription": "…", "decisionMode": "<mode>", "isBeingStructured": true}}`

   Garder l'id et `authorId` : c'est l'id de l'utilisateur.
5. Ne rien annoncer : le message suivant est la première question.

**Les questions.** Lire les questions du projet (`references/questions-structuration.md`), les
grouper par section dans l'ordre : chaque section est une étape de la structuration. Ignorer
`isEnabled: false` et les questions déjà répondues (pré-remplies à la création). Préparer une
proposition de réponse pour **toutes** les questions restantes, obligatoires et facultatives, à
partir de l'étape 1, sans demander à l'utilisateur s'il veut répondre lui-même.

**Ce qui est déjà dit ne se repose pas.** Pour chaque question, regarder si l'utilisateur y a
déjà répondu : dans sa demande, à l'étape 1, ou en validant une proposition (« C'est bien ça ? »
→ « Oui »). Si oui, **écrire la réponse directement**, sans reposer la question, sans la faire
valider et sans le dire : la durée et la fréquence demandées à l'étape 1, les étapes du
processus qu'il a validées, le livrable qu'il a décrit. Seule une réponse qui ajoute ce que
l'utilisateur n'a ni dit ni validé passe par l'outil de question. Une étape de la structuration
dont toutes les réponses sont déjà connues s'écrit en silence, sans être nommée.

Puis, pour les questions qui restent, **une à la fois**, avec l'outil de question :

- en-tête : `Étape 2/5` (l'étape de la structuration) ;
- question : le libellé exact de Teamstarter (`questionWordings.value`), avec « skill » à la
  place de « projet » ;
- premier choix : « Valider », la proposition en description ; d'autres choix seulement quand la
  question en a (options d'un choix, score de 1 à 5, seul ou en équipe), la proposition en
  premier ; la réponse libre reste possible ;
- **proposition trop longue** pour un choix (plusieurs lignes, une liste d'étapes) : l'écrire
  dans la conversation juste avant, puis l'outil de question avec « Valider la proposition
  ci-dessus » en premier choix.

À la première question d'une nouvelle étape de la structuration, la nommer en une ligne avant
l'outil de question (« Étape 2/5 de la structuration : Impact de l'IA »).

Après chaque réponse :

- **Écrire la réponse aussitôt**, sans le dire (`AIprojectQuestionAnswerCreate`, ou `Update`
  avec l'id de la réponse ; formats et codages de `references/questions-structuration.md`). Une
  réponse libre s'écrit telle que l'utilisateur l'a donnée.
- Une réponse libre qui contient une donnée sensible : reposer la question avec la version
  générique en premier choix.
- `team` = « En équipe » : demander les noms des co-porteurs, les retrouver
  (`user(where: {"fullname": {"iLike": "%<nom>%"}})`), les ajouter (`projectOrganizerCreate`), et
  dire une fois qu'ils reçoivent une notification de Teamstarter.
- Le type n'a ni dépenses ni campagne.

Quand toutes les questions ont leur réponse (contrôle de fin de
`references/questions-structuration.md`), passer à l'étape 3 sans l'annoncer.

## Étape 3 — Fiche et audit, sans rien demander

1. **Fiche.** `projectGenerateSheet`, poller (`references/fiche-projet.md`, partie A) ; remettre
   la tâche comme titre si le job l'a changée. Sans le job : rédiger la fiche
   (`references/fiche-projet.md`, partie B, et la correspondance réponses → sections de
   `references/type-automatisation-ia.md`) et l'écrire **sans la faire valider**.
2. **Fin de la structuration** : `projectUpdate` avec `isBeingStructured: false` et
   `structuredAt`.
3. **Audit** (si `projectEvaluateLimits` est exposé) : lancer, puis poller toutes les 60 à 90
   secondes (`references/regles-api.md`, « Jobs IA ») :

```graphql
mutation($id: Int!) { projectEvaluateLimits(projectId: $id) { jobId } }
```

```graphql
query($where: SequelizeJSON, $pw: SequelizeJSON) {
  projectLimitEvaluation(where: $where) { limitId status confidence explanation improvements }
  project(where: $pw) { id aiMetadata { statusEvaluation isEvaluationOutdated } }
}
```
variables : `{"where": {"projectId": <id>, "aiJobId": <jobId>}, "pw": {"id": <id>}}` ; terminé
quand `statusEvaluation` vaut `successful` (aucune ligne : aucune règle de l'organisation ne
s'applique). Pour chaque point `warning` :
   - ce qui se corrige avec ce que l'on sait déjà : corriger la réponse en silence ;
   - ce qui demande une information de l'utilisateur : une question avec l'outil de question,
     l'amélioration suggérée en proposition.

   Après une correction : régénérer la fiche, relancer l'audit une fois. Deux audits au plus ;
   ensuite, continuer.

Ne rien présenter de la fiche ni de l'audit : passer à l'étape 4.

## Étape 4 — Validation, puis prompt de création

**Envoyer le skill en validation, ou le publier**, sans le demander ni l'annoncer avant : la
fiche est faite et les réponses validées. Ne jamais poser « Je le publie ? » : la publication
fait partie de la création demandée (règle 6).

```graphql
mutation($project: projectInput!) { projectUpdate(project: $project) { project { id status underReviewAt } } }
```
variables : `{"project": {"id": <id>, "status": "UNDER_REVIEW", "isBeingStructured": false}}`

| Réponse | Ce que ça veut dire | Suite |
|---|---|---|
| `status: UNDER_REVIEW` | l'organisation fait valider les skills par ses animateurs | « Ton skill est envoyé aux animateurs pour validation. Reviens me voir quand il sera validé : je le construirai. » Fin de la conversation sur ce skill. |
| refus « You must publish this project directly. » | l'organisation ne modère pas | refaire aussitôt l'appel avec `"status": "PUBLISHED"`, sans rien demander ni dire |
| refus « The project audit is outdated… » | l'audit date d'avant la dernière modification | relancer l'audit (étape 3), puis réessayer |
| autre refus | | dire en une phrase ce qui manque, sans parler de projet, et le compléter |

Après `PUBLISHED`, relire `status` :

- `CASHEDOUT` : le skill est validé (un objectif en modération passe directement en
  réalisation). **Récupérer aussitôt le prompt**, sans rien dire.
- `PUBLISHED` : l'objectif est un vote ou un financement : « Ton skill est soumis au vote de ton
  organisation. Reviens me voir quand il sera retenu : je le construirai. »

**Le prompt de création** : tool `get-skill-creation-instructions`, `{"projectId": <id>}`. La
réponse est le prompt, en markdown : la spécification du skill.

- Refus « structuration incomplète » : il liste les questions obligatoires sans réponse ; les
  poser comme à l'étape 2, puis rappeler le tool.
- Refus d'accès : le prompt est réservé à l'auteur, aux porteurs et aux admins.
- Sans le tool : demander à l'utilisateur de copier le prompt depuis la page de son skill dans
  Teamstarter (« Créer mon agent IA », « Copier le prompt »).

Ne pas résumer le prompt à l'utilisateur : il se suit, à l'étape 5.

## Étape 5 — Construire, tester, enregistrer le skill

**Suivre le prompt de Teamstarter**, dans cet ordre :

1. Sa section « Instructions IA » d'abord : elle dit ce qu'est un agent IA dans l'organisation
   et comment le construire et le tester. Chacune de ses instructions s'applique.
2. Le contexte de l'organisation et les informations sur la tâche, avec la règle de priorité
   des sources du prompt.
3. Sa checklist finale, point par point, avant l'enregistrement.

`skill-creator` (skill d'Anthropic) sert pour ce que le prompt ne dit pas ; ses tests et
évaluations seulement si le prompt n'en définit pas. Sans `skill-creator` : écrire le skill
directement.

**Aucune question pendant la construction.** Chaque choix se fait seul, sans le proposer à
l'utilisateur : le nom du skill, sa description, le découpage en fichiers, le format de ce qu'il
produit, la langue, les sources qu'il lit. D'abord ce que dit le prompt, puis ce que
l'utilisateur a dit aux étapes 1 et 2, puis les habitudes de l'organisation. L'utilisateur voit
ces choix à l'étape 6 et peut les changer. `skill-creator` propose de valider un nom, une
structure ou un plan : ne pas lui transmettre ces questions. Seule exception : une information
que seul l'utilisateur a et sans laquelle le skill ne peut pas être construit (un accès, une
donnée introuvable), demandée avec l'outil de question.

**Le nom** : la convention de l'organisation quand le prompt ou les skills qu'elle a déjà la
montrent (`ts-tech-suivre-tickets-linear` → `ts-<domaine>-<verbe>-<objet>`), sinon
`<verbe>-<objet>` tiré de la tâche, en minuscules et tirets, sans accent.

En plus du prompt :

- **En-tête du `SKILL.md`** : `name` (minuscules, chiffres, tirets, 64 caractères au plus, égal
  au nom du dossier), `description` (1024 caractères au plus, avec les phrases qui le
  déclenchent), et l'id dans `metadata`, en chaîne :

```markdown
---
name: <nom-du-skill>
description: <ce que fait le skill et quand le déclencher>
metadata:
  teamstarter-project-id: "<id>"
---
```

- **Deux dernières sections du `SKILL.md`**, telles quelles :

```markdown
## Après chaque exécution

Déclarer l'exécution à Teamstarter avec le skill `ts-general-declarer-execution-skill` du plugin
Teamstarter. Si l'exécution a échoué sur un problème que l'utilisateur ne peut pas lever seul
(accès refusé, outil indisponible, donnée manquante, règle de sécurité), proposer de le déclarer
comme blocage avec le skill `ts-general-declarer-blocage`. Si ces skills ne sont pas
disponibles, ne rien faire.

## Après chaque modification de ce fichier

Quand ce skill est modifié (pas quand il s'exécute), enregistrer la nouvelle version dans
Teamstarter avec le skill `ts-general-deposer-skill` du plugin Teamstarter. S'il n'est pas
disponible, ne rien faire.
```

- **Rien de confidentiel** : ni donnée personnelle, ni nom de client, ni clé d'API ou mot de
  passe. Un accès à un service passe par un connecteur.

**Tester** comme le prompt le demande, avant de présenter le skill : les tests que Claude peut
faire seul (sur un exemple de l'étape 1, à blanc) maintenant ; ceux qui demandent l'utilisateur
ou ses vraies données, à l'étape 7. Un test qui échoue : corriger et retester, sans le dire.

**Enregistrer dans Teamstarter**, sans le demander, comme le dit `ts-general-deposer-skill` :
empaqueter le dossier en `<nom-du-skill>.skill` (une archive zip qui contient
`<nom-du-skill>/SKILL.md` et les autres fichiers), l'encoder en base64, puis

```
upload-project-skill { "projectId": <id>, "fileName": "<nom-du-skill>.skill", "contentBase64": "<…>" }
```

- Toujours le même nom de fichier : chaque dépôt est la version suivante du skill.
- Seuls les porteurs déposent : un refus « Only the organizers… » se dit à l'utilisateur.
- **Vérifier le dépôt** : relire `project(where: {"id": <id>}) { skillFileId skillName }`. Le
  skill est enregistré quand `skillName` est le `name` du skill. Sinon, il ne l'est pas, quoi
  qu'ait répondu l'appel.
- **Un dépôt impossible ou refusé se dit tout de suite**, en une phrase avec la raison, avant la
  présentation de l'étape 6 et pas à la fin d'un récapitulatif ; puis donner le fichier
  `<nom-du-skill>.skill` et le geste (page du skill dans Teamstarter, section Fichiers, déposer
  le fichier). Les cas sont dans `ts-general-deposer-skill` (archive trop grosse pour être
  recopiée sans risque, outil absent, refus).
- **Cocher « Créer mon agent IA » seulement quand le skill est enregistré** (`skillName`
  renseigné), sans le demander ni le dire : l'action `create-my-agent` de
  `project { projectDeliveryActions { id type doneAt } }`, avec
  `setProjectWorkflowActionStatus(actionId: <id>, status: "done")`. Dépôt fait à la main par
  l'utilisateur : relire `skillName` quand il dit l'avoir fait, puis cocher. Ne jamais écrire
  que le skill est enregistré ou validé dans Teamstarter tant que `skillName` est vide.

## Étape 6 — Présenter le skill

Présenter le skill par **un schéma SVG** de ce qu'il prend, de ses étapes et de ce qu'il
produit, pour que l'utilisateur puisse le reprendre :

1. Écrire `<nom-du-skill>-schema.json`, à côté du dossier du skill (pas dedans : il n'est pas
   déposé), d'après ce que le `SKILL.md` construit fait vraiment, au format de
   `assets/exemple-schema.json` :
   - `name` (le `name` de l'en-tête), `title` (la tâche), `description` (ce que fait le skill,
     en une phrase) ;
   - `inputs`, ce qu'il prend : `label` (quoi), `detail` (d'où et sous quelle forme : outil,
     connecteur, fichier, message de l'utilisateur), `step` (le numéro de l'étape qui le lit) ;
   - `steps`, ses étapes dans l'ordre : `label` (ce qu'elle fait, un verbe à l'infinitif),
     `detail` (ce qu'elle lit ou produit, une ligne) ;
   - `outputs`, ce qu'il produit : `label`, `detail` (où, sous quelle forme), `step` (l'étape
     qui le produit).

   Des libellés de 5 mots au plus, des détails d'une ligne, 8 étapes au plus (regrouper
   au-delà). Pas de donnée réelle : un client, un montant, une personne restent génériques.
2. `python3 scripts/schema_svg.py <nom-du-skill>-schema.json --out <nom-du-skill>-schema.svg`.
   Sans Python : écrire le SVG à la main sur le même modèle (fond blanc, trois colonnes
   « Entrées », « Étapes » numérotées et « Sorties », une flèche de chaque entrée vers son étape
   et de chaque étape vers ses sorties).
3. **Afficher le schéma dans la conversation**, dans la réponse elle-même, pas seulement en
   fichier à ouvrir. Dans cet ordre :
   - l'outil de l'outil IA qui affiche un visuel dans la réponse (dans claude.ai et Cowork,
     l'outil de visualisation, par exemple `show_widget`) : lui passer le contenu du fichier
     `<nom-du-skill>-schema.svg`, tel quel ;
   - sinon, une image dans la réponse, si l'outil IA affiche les images markdown :
     `![Schéma du skill](data:image/svg+xml;base64,<le SVG en base64>)` ;
   - sinon seulement, le fichier (artifact SVG ou fichier joint), en disant de l'ouvrir.

   Au-dessus, une phrase : le nom du skill et ce qu'il fait. Pas de tableau en plus : le
   schéma porte les entrées, les étapes et les sorties. Le fichier `.svg` peut être joint en
   plus, jamais à la place quand le schéma peut s'afficher dans la réponse.
4. Donner le fichier `<nom-du-skill>.skill` pour l'installer (claude.ai et Cowork :
   Personnaliser → Skills ; Claude Code : décompresser dans `~/.claude/skills/`).

Puis l'outil de question : « Ce skill te convient ? » → « Oui, on l'essaie » / « Changer les
entrées ou les sorties » / « Changer les étapes ». Un changement : le faire (étape 5 : modifier,
retester, empaqueter, enregistrer), refaire le schéma sous les mêmes noms de fichier, puis le
montrer de nouveau, sans dire ce qui a changé.

## Étape 7 — Première exécution

L'outil de question : « On le lance une première fois sur un cas réel ? » → « Oui, maintenant »
/ « Plus tard ».

- **Oui** : demander l'entrée réelle si elle manque, exécuter le skill en suivant son
  `SKILL.md` (pas besoin de l'installer pour cette première fois), avec les tests du prompt qui
  demandent l'utilisateur. L'exécution est déclarée par `ts-general-declarer-execution-skill`. Un
  échec sur un problème que l'utilisateur ne peut pas lever seul : `ts-general-declarer-blocage`.
- Puis : « Le résultat te convient ? » → « Oui » / « Non, à corriger ».
  - **Oui** : cocher « Tester l'agent en conditions réelles » (action `test-agent`), sans le
    dire. Seulement après ce « Oui », jamais en même temps que « Créer mon agent IA ». Donner le lien de la page du skill
    (`<adresse de l'app>/<tag de l'organisation>/project/<id>/manage`) et la suite qui se fait
    dans Teamstarter : le faire valider par son ambassadeur, le partager à ses collègues.
  - **Non** : demander ce qui ne va pas, corriger (étape 5) en silence, proposer de relancer.
- **Plus tard** : donner le lien de la page du skill.

Un découpage en plusieurs skills (étape 1) : proposer de créer le suivant.

## Reprise (R)

Retrouver le skill : `metadata.teamstarter-project-id` du `SKILL.md` ouvert ; sinon la tâche que
l'utilisateur nomme, parmi `mine` et `skills` du préambule (`d_organizerIds` contient son id,
retrouvé sans le lui demander). Lire :

```graphql
query($where: SequelizeJSON) {
  project(where: $where) {
    id title status isBeingStructured underReviewAt d_factoryCompletionRate d_draftCompletionRate skillFileId
    projectDeliveryActions { id type doneAt skippedAt }
  }
}
```
variables : `{"where": {"id": <id>}}`

| État | Reprendre à |
|---|---|
| `EMPTY`, ou `DRAFT` avec une question obligatoire sans réponse | étape 2 (questions sans réponse seulement) |
| `DRAFT`, réponses complètes, fiche incomplète ou sans audit | étape 3 |
| `DRAFT`, tout fait | étape 4 |
| `DRAFT` après un envoi en validation (`underReviewAt` renseigné) | les animateurs l'ont renvoyé : lire leurs commentaires (`comment(where: {"projectId": <id>})`), les montrer, y répondre par l'étape 2 ou 3, puis étape 4 |
| `UNDER_REVIEW` | « Ton skill attend encore la validation des animateurs. » |
| `PUBLISHED` | « Ton skill est encore soumis au vote. » |
| `CASHEDOUT`, `skillFileId` vide | étape 4, prompt de création, puis étape 5 |
| `CASHEDOUT` ou `DELIVERED`, skill enregistré | ce que l'utilisateur demande : modification (étapes 5 et 6), exécution (7), utilisation (U), blocage (B) |
| `CANCELLED`, `ENDED`, `CAMPAIGN_FAILED` | le dire ; un nouveau skill repart du préambule |

Une reprise de création : dire en une phrase où en est le skill, sans présenter les étapes. Une
modification : ne rien dire avant de montrer le résultat.

## Étape U — Utilisation du skill

« Combien de fois mon skill a été utilisé ? », « qui s'en sert ? » :

```graphql
query($projectId: Int!) {
  projectSkillUsage(projectId: $projectId) {
    executionsCount failuresCount distinctUsersCount tokensCount averageDurationMs lastExecutionAt
    topUsers { executionsCount lastExecutionAt user { fullname } }
  }
}
```
variables : `{"projectId": <id>}`

Réservé à l'auteur, aux porteurs et aux admins. Seules les exécutions déclarées sont comptées ;
`tokensCount` à 0 veut dire « tokens non déclarés ». Les mêmes chiffres sont sur la page du
skill (« Utilisation du skill »).

## Étape B — Blocage

Un problème qui empêche de créer ou d'utiliser le skill et que l'utilisateur ne peut pas lever
seul : suivre `ts-general-declarer-blocage` (le skill doit être validé ; proposition,
rédaction, validation, déclaration). Sans lui : lire les blocages ouverts
(`projectBlocker(where: {"projectId": <id>})`), rédiger titre (120 caractères), catégorie et
description, faire valider, puis `projectBlockerCreate(projectBlocker: {projectId, title,
category, description})`.

## Garde-fous

- **Écritures faites sans demander**, parce qu'elles font partie de la création que
  l'utilisateur a demandée : création du skill dans Teamstarter, réponses validées, fiche,
  audit et ses corrections, envoi en validation ou publication, enregistrement de chaque
  version, étapes « Créer mon agent IA » et « Tester l'agent » cochées. Toute autre écriture (co-porteurs, blocage) suit l'accord de
  l'utilisateur.
- **Aucune réponse de structuration écrite que l'utilisateur n'a ni donnée ni validée**, et
  aucune question reposée quand il y a déjà répondu.
- **Ne rien inventer** : date, montant, nom, outil viennent de l'utilisateur ou d'une
  proposition qu'il a validée.
- **Ne pas construire le skill avant `CASHEDOUT`.**
- **Une seule source pour l'id** : `metadata.teamstarter-project-id`. Ne jamais enregistrer ni
  déclarer sur un autre skill.
- **Rien de confidentiel** dans les réponses, la fiche ou le skill.
- Pas d'enregistrement d'un fichier inchangé.

## Tags de sécurité

`écriture` : crée et structure un skill dans Teamstarter, l'envoie en validation, enregistre ses
versions, coche ses étapes de réalisation ; chaque réponse de structuration est validée par
l'utilisateur ; co-porteurs et blocages après accord. Produit des fichiers locaux (le `.skill`,
le schéma `-schema.svg` et son `-schema.json`).

## Fallback

- **Pas de connecteur, ou accès en lecture seule** : dire que le skill ne pourra pas être
  enregistré dans Teamstarter, et comment ouvrir l'écriture (l'administrateur de l'organisation
  ouvre l'accès en écriture, puis l'utilisateur reconnecte le connecteur en choisissant lecture
  et écriture). S'il veut continuer : étape 1, puis `skill-creator` sans métadonnée.
- **Type d'automatisation absent ou désactivé** : même chose.
- **Job IA qui ne se termine pas en 5 minutes** : continuer sans lui (fiche rédigée, pas
  d'audit).

## Ressources

- `references/regles-api.md` — règles du connecteur, statuts, utilisateur du connecteur.
- `references/questions-structuration.md` — lire, coder et écrire les réponses.
- `references/type-automatisation-ia.md` — les questions du type, la correspondance réponses →
  fiche.
- `references/fiche-projet.md` et `scripts/tiptap.py` — générer ou rédiger la fiche.
- `scripts/schema_svg.py` et `assets/exemple-schema.json` — le schéma SVG du skill (étape 6).
- Skills voisins : `ts-general-deposer-skill` (enregistrer chaque version),
  `ts-general-declarer-execution-skill` (compter les exécutions), `ts-general-declarer-blocage`
  (blocages), `ts-general-lister-idees-automatisation` (partir d'une idée),
  `ts-general-creer-projet` (le même parcours pour les autres types).
- Skill d'Anthropic : `skill-creator`.

## Convention de nommage

Skill nommé selon la convention Teamstarter : `ts-general-creer-skill` — domaine `general`, verbe
`creer`, objet `skill`.
