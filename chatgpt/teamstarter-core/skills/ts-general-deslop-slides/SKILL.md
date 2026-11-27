---
name: ts-general-deslop-slides
description: "Removes the marks of generated decks from a presentation (PowerPoint, Google Slides, an HTML deck, a markdown outline), in French or English: topic titles in Title Case instead of the point of the slide, an agenda in a short deck, the same title-and-bullets layout on every slide, bullets opening with a bold label, emoji bullets, icon-in-a-circle trios, pillars and pyramids without data, stock photos and gradient backgrounds, invented numbers and logos, a recap slide and a closing « Merci ! Des questions ? ». The organization's template wins. Two modes: build (outline of assertion titles, layout chosen per slide) and review (slide by slide, the mark and the fix). Runs a checker script on .pptx, HTML or markdown decks, which also applies the writing rules to the text of each slide. Use when building or reviewing any deck, and when someone says deslop, « enlève le slop », « ça fait IA », « ce deck fait template », or asks to clean up a presentation."
license: MIT
metadata:
  version: "1.0 (2026-11-18)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-deslop-slides; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Deslop slides

Speak and write to the person in their language; this file is in English.

A generated deck is recognized from its first slides: « Agenda », then « Notre Solution
Innovante 🚀 » over three bullets that each start with a bold word, three icons in circles,
« +300 % d'engagement » without a source, and « Merci ! Des questions ? » to close. Each slide
follows the same template whatever it has to say. The audience stops reading after the third
slide.

A deck exists to make an audience understand something or decide something. Each slide has one
point; its title says that point; its body shows the evidence (a number with its source, a
chart, a screen, a quote). This skill removes what stands between the audience and those
points.

## What wins over this skill

1. The organization's slide template and brand guide (fonts, colors, title position, logo).
2. The person's own deck and voice, when they are fixing an existing deck.
3. This skill.

## Build mode

1. Write the outline first, as a list of slide titles. Each title is a full sentence that states
   the point (« Les fiches arrivent remplies deux jours avant l'atelier »). Read the titles alone:
   they must tell the whole story. A deck of ten slides or fewer has no agenda.
2. For each slide, choose the layout from its evidence: one big number with its source, a
   comparison, a chart that highlights the series that matters, a screenshot, a photo of the real
   thing, a short quote. Title and bullets is one layout among others, not the default.
3. End on what the audience must do or decide, never on « Merci ».
4. Never invent a number, a logo, a customer or a quote. A missing figure is asked for, or marked
   « à préciser » and said to the person.
5. Review the result in review mode, then run the checker.

## Review mode

Slide by slide: the slide number, the mark, the fix. Marks of the whole deck (the same layout
everywhere, titles that only name topics, no visual at all) are reported once. "Remove" marks of
`references/catalog.md` are reported at each occurrence; "earn it" marks only when they decorate.
Content honesty (invented numbers, logos, testimonials) is always reported.

## The checker

`python3 scripts/check_slides.py <deck.pptx | deck.html | outline.md> [--lang fr|en]` reads the
title and body of each slide (not the speaker notes) and prints the marks slide by slide, then
the marks of the deck. It runs the writing checker (`scripts/check_writing.py`, with
`references/fr.md` and `references/en.md`) on the text of each slide. A markdown outline has one
slide per `---`, or per heading; an HTML deck has one slide per `<section>`. Fix the FAIL marks
and run it again; read each WARN.

The script cannot see the visuals: colors, photos, icon trios, diagrams, alignment. Render the
slides to images when the tool allows it (a PDF export, a thumbnail per slide) and review them
against S4 and S6 of the catalog.

## The catalog

`references/catalog.md`: S1 titles, S2 structure of the deck, S3 bullets and text, S4 visuals,
S5 numbers and proof, S6 layout and type, and the final question: shown this deck and told « une
IA l'a fait », would someone believe it at once?

## Related skills

`ts-general-deslop-writing` holds the rules for the text; `ts-general-deslop-ui` for an HTML deck's
styles (gradients, glows, radii, fonts): run `check_ui.py` on it too when it is installed.
