# English: the marks of generated text

The words, phrases and constructions that make an English text read as generated. They are bad
writing before they are a sign of origin: they inflate, announce, or stage instead of saying. The
checker (`scripts/check_writing.py`) reads every section tagged `[fail]` or `[warn]`: `[fail]` is
a mark to remove, `[warn]` a mark to check in context (several words are fine in their literal
sense: a "robust" statistical estimator, a "crucial" step that the text then explains).

Pattern syntax: a phrase in backticks matches case-insensitively, on whole words, with `…` for a
few words and a leading `^` for "at the start of a sentence or a line"; `re:` starts a Python
regular expression. The text after the pattern says why it reads as generated and what to write.

## Correct English, never a mark

- Contractions, "and" or "but" at the start of a sentence, a one-sentence paragraph.
- Semicolons and colons; they show how two ideas relate.
- Conventional documentation headings: Prerequisites, Installation, Configuration,
  Troubleshooting, API reference.
- "Just" and "simply" when the writer's established voice uses them.

## Patterns the checker reads

### Staged constructions [fail]

- `re:\bit'?s not (?:just |only |simply |merely )?(?:about )?[^.!?\n]{1,60}[.,;:] ?it'?s\b` : "It's not X, it's Y" corrects a claim nobody made. Say what it is.
- `re:\bnot (?:just|only|merely) [^.!?\n]{1,40}, but\b` : same staging. State the claim.
- `re:\bmore than (?:just )?an? \w+,\s(?:it'?s|a|an)\b` : "More than a tool, a partner". Say what it does.
- `Whether you're … or` : addresses an imaginary audience. Name the reader.
- `re:\bin today'?s (?:fast-paced|ever-changing|rapidly evolving|digital|modern|competitive)\b` : opening windup. Start with the news.
- `re:\bin an (?:era|age|world) (?:of|where)\b` : opening windup. Start with the news.
- `re:\b(?:the result|the catch|the secret|the answer|the kicker|the twist|the best part|the bottom line|the verdict|the problem)\?` : question answered right after. State the point.
- `re:\bbut (?:that'?s|it'?s) not all\b` : announces more instead of giving it.
- `re:\bhere'?s (?:the thing|the deal|the kicker|the catch|why|what)\b` : teaser. Give the point.
- `re:\b(?:what|the part) (?:nobody|no one|most people|everyone) (?:tells you|talks about|gets wrong|misses|skips|sleeps on)\b` : teaser. Give the point.
- `re:\b(?:let'?s|let us) (?:dive|delve|dig|unpack|break (?:it|this) down|explore)\b` : announces what comes next. Write it.
- `re:\bready to [^.!?\n]{1,50}\?` : engagement bait. End on the last concrete point.
- `re:\b(?:what'?s your take|curious (?:what|to hear) (?:others|your thoughts)|let me know in the comments|drop a comment|thoughts\?)` : engagement bait. Cut it.
- `re:\blet that sink in\b|\bread that again\b|\bfull stop\.` : emphasis by command. Cut it.
- `re:\bthis is where [^.!?\n]{1,40} comes in\b` : staging. Say what it does.
- `re:\bthe (?:best|worst|hard|tricky|real|key|surprising) (?:part|thing|news|bit):` : colon reveal, a teaser in one line. State the point.
- `re:\b(?:to be clear|to be fair|let me be (?:clear|direct)|I'?ll be honest)\b` : arguing with no one, or announced candor. Say the thing.
- `re:\bone (?:might|could) (?:be tempted to|think|argue|assume)\b` : rebuts an objection nobody raised. Cut it.

### Writing about the text [warn]

- `re:\b(?:the|this) (?:table|list|section|chart|document|article|guide) below\b` : writes about the document instead of its subject. Give the content.
- `re:\bas you can see\b|\bas shown (?:above|below)\b|\bas mentioned (?:above|earlier)\b` : same.
- `re:\bthis (?:distinction|point|nuance|detail) (?:matters|is (?:important|key|crucial))\b|\bthis matters because\b|\bhere'?s why (?:this|that|it) matters\b` : announces significance. Give the reason itself.
- `re:\bthis is (?:deliberate|intentional|by design)\b|\bthat'?s by design\b` : same. Give the reason.
- `re:(?:^|(?<=[.!?]\s))what (?:makes|sets|matters|really matters|stands out)\b[^.?!\n]{0,60}\bis\b` : cleft opener that delays the subject. Start with it.
- `re:\b(?:substrate|flywheel|north star|wedge|scaffolding|throughline|through-line)\b` : abstract metaphor noun. Name the thing.

### Openers and formulas [fail]

- `re:(?:^|(?<=[.!?]\s))(?:great|excellent|good) (?:question|point|catch)\b` : validation opener. Answer.
- `re:\byou'?re (?:absolutely|completely|totally|exactly) right\b` : validation opener. Answer.
- `re:(?:^|(?<=[.!?]\s))(?:certainly|absolutely|of course|sure)!` : opener. Start with the answer.
- `re:\bI(?:'d| would) be (?:happy|glad|delighted) to\b` : assistant formula in a text written for someone else.
- `re:\bI hope (?:this|my) (?:email|message|note) finds you\b` : the most recognized email opener. Cut it.
- `re:\bit'?s (?:worth noting|important to (?:note|remember|understand)|crucial to (?:note|understand))\b` : announces that something matters instead of saying it.
- `re:\bplays? an? (?:crucial|pivotal|vital|key|central|critical|significant) role\b` : says something matters without saying how. Name what it does.
- `re:\b(?:serves|stands) as an? (?:testament|reminder|example|beacon)\b|\ba testament to\b` : pseudo-significance. State the fact.
- `re:\bmarks? an? (?:pivotal|significant|major|key) (?:moment|milestone|shift|step)\b` : pseudo-significance. Say what changed.
- `re:,\s(?:highlighting|underscoring|emphasizing|showcasing|reflecting|demonstrating|illustrating) (?:the|its|their|a)\b` : trailing participle that pretends to explain. Write the consequence or cut.
- `re:\bunlock(?:s|ing)? (?:the )?(?:full |true )?(?:potential|power|value)\b|\btake (?:\w+ ){0,2}\w+ to the next level\b` : promotional. Say what changes, with a number.
- `re:\b(?:studies|research|experts|data) (?:show|shows|suggest|suggests|agree)\b` : unnamed authority. Name the source or cut the claim.
- `re:\bas an (?:AI|expert|experienced)\b` : announces a role. Say the thing.

### Connectors and closers [warn]

- `^Moreover,` : filler connector at the start of a paragraph; usually removable.
- `^Furthermore,` : same.
- `^Additionally,` : same.
- `^Notably,` : same.
- `^Importantly,` : same; show why it matters instead.
- `^Ultimately,` : summary opener. End on the last concrete point.
- `^Overall,` : same.
- `^In conclusion,` : same; a conclusion that repeats the text can go.
- `^In summary,` : same.
- `^That said,` : seesaw transition; pick a side.
- `^Honestly,` : announced candor; just be direct.
- `re:\bthink of it (?:as|like)\b` : analogy on reflex; keep only if it explains an unusual mechanism.
- `re:\bfeel free to (?:reach out|contact)|\bdon'?t hesitate to (?:reach out|contact)` : reflex closer.

### Inflated vocabulary [warn]

Correct in their literal sense; marks when they inflate. Replace with the concrete thing (the
number, the name, the action), never with a synonym.

- `re:\bdelv(?:e|es|ed|ing)\b` : say "look at", or just look.
- `re:\btapestry\b|\brealm\b|\btestament\b` : stock images.
- `re:\blandscape\b|\becosystem\b|\bjourney\b|\bnavigat(?:e|es|ing)\b` : figurative outside their literal sense.
- `re:\b(?:pivotal|crucial|vital|paramount|critical)\b` : importance claimed instead of shown.
- `re:\b(?:seamless(?:ly)?|effortless(?:ly)?|frictionless)\b` : promises ease without showing it. Count the steps.
- `re:\b(?:robust|cutting-edge|state-of-the-art|best-in-class|world-class|next-generation|innovative|powerful)\b` : sales vocabulary. Name the property.
- `re:\b(?:leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|empower(?:s|ed|ing)?|elevat(?:e|es|ed|ing)|supercharg(?:e|es|ed|ing)|unleash(?:es|ed|ing)?|streamlin(?:e|es|ed|ing)|revolutioniz(?:e|es|ed|ing))\b` : promotional verbs. Say "use", or what happens.
- `re:\b(?:foster(?:s|ed|ing)?|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|bolster(?:s|ed|ing)?|garner(?:s|ed|ing)?)\b` : inflated verbs. Say "shows", "builds", "gets".
- `re:\b(?:holistic|synergy|synergies|paradigm|multifaceted|nuanced|intricate|meticulous(?:ly)?|vibrant|transformative|game-?changer)\b` : abstract or promotional. Be specific.
- `re:\b(?:ever-evolving|fast-paced|rapidly evolving|ever-changing)\b` : says nothing. Cut it.
- `re:\bgenuinely\b|\bquietly\b|\bunder the hood\b|\bheavy lifting\b` : intensifiers a model reaches for. Cut or say what it does.
