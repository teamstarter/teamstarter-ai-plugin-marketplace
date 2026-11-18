---
name: ts-general-deslop-ui
description: "Removes the marks of generated interfaces from any page, screen or HTML artifact (landing page, dashboard, report, project page, component): purple gradients, gradient text, blurred blobs and glows, an accent bar on one side of a card, spaced capitals, pills and large radii everywhere, nested cards, emoji and sparkles as icons, the templated landing page (badge pill, centered hero, three icon cards, stats band), fade-in on scroll, invented logos, numbers and testimonials, Claude's own cream and terracotta palette. The organization's design system always wins. Two modes: build (decide palette, type, radius and density before writing code) and review (file:line or screen region, the mark, the fix). Runs a checker script on HTML, CSS and component files. Use when building or reviewing an interface or artifact, and when someone says deslop, « enlève le slop », « ça fait IA », « ça fait template », looks AI-generated."
license: MIT
metadata:
  version: "1.0 (2026-11-18)"
  owner: "Teamstarter product team"
  source: "teamstarter repository, teamstarter-os/skills/ts-general-deslop-ui; packaged by teamstarter-os/tools/package_rpt_skill.py"
---

# Deslop UI

Speak and write to the person in their language; this file is in English.

A generated interface is recognized in one look: a violet gradient on the headline, a pill
announcing « ✨ Nouveau », three identical cards with an emoji on top, a colored bar on the left
of every block. None of these elements is wrong in itself. The mark is the element used by
reflex, because it looks like a dashboard or a landing page, without telling the user anything.

The test for each element on the screen: does it carry information or serve the person here? If
yes, it stays. If it is there because "that is what this kind of page looks like", remove it or
replace it with a decision taken from the context. Removing meaningful elements in the name of
this skill (a status tag that maps to a real state, a chevron on a row that opens) is a failure
too.

## What wins over this skill

1. The organization's design system: its tokens (colors, fonts, radii, spacing), its components,
   its brand guide, a `DESIGN.md`, a design system attached to the design tool. A mark this skill
   lists is fine when the design system specifies it (capitals in its type scale, its own
   gradient). Pass those rules to the checker with `--allow`.
2. A design brief or a validated mockup for this screen.
3. This skill.

Without a design system, say so to the person and make the decisions in step 1 below rather
than falling back on a default.

## Build mode

1. Before writing code, write a short plan: the palette (four to six named colors, one accent),
   the fonts, the radius of each level, the density, the one element that gives the page its
   character. Take each value from the design system, or from the context of the product and its
   users.
2. Compare the plan with what a generic prompt would produce ("a modern landing page for X"). Any
   choice that matches the generic answer is a default: change it or justify it.
3. Build. Use the components and icons of the design system; no emoji or text symbols as icons.
4. Review the result in review mode below, then run the checker.

## Review mode

Works on code and on screenshots.

- On code: one finding per line, `file:line`, the mark, the fix.
- On a screenshot or a published page: the region or element, the mark, the fix.
- "Remove" marks: report each occurrence (`references/catalog.md`).
- "Earn it" marks: name the element and say what it should tell the user; report it only when it
  decorates ("status pill on every row: does it map to a real state?").
- A templated page: report the pattern once when three or more of its pieces appear, with the
  list of pieces, not ten separate findings.
- Order findings by what the reader notices first: the hero and the headings, then the
  components, then the details. Keep findings that a person can check; drop a weak one rather
  than pad the list.

Never report a finding about content honesty lightly, and never let one pass: invented figures,
logos, testimonials or people presented as real are removed, whatever the style.

## The checker

`python3 scripts/check_ui.py <files or folders> [--allow rule,rule]` reads HTML, CSS and
component files (`.html .css .scss .jsx .tsx .js .ts .vue .svelte`), skips comments, `<code>`
and `<pre>`, and prints each mark with `file:line`. `--list-rules` gives the rule ids. FAIL marks
are removed unless the design system specifies them; WARN marks are checked by hand. Run it again
until there is no FAIL.

The script reads the source, not the rendered page: nested cards, the assembly of a templated
page, density, invented numbers and the quality floor of `references/catalog.md` (sizes, line
length, contrast) are checked by looking at the page. When a browser is available, open the page,
take a screenshot at desktop and phone widths, and review it too.

## The catalog

`references/catalog.md` holds the full list, by family:

| Family | Examples |
|---|---|
| U1 Text on the page | em dash, « · » strings, bold labels, two-fragment slogans, a page that describes itself, process text left visible |
| U2 Color and background | purple gradients, gradient text, blobs, glows, Claude's cream and terracotta, dark by reflex |
| U3 Type | spaced capitals, one word in another color, default fonts, the quality floor |
| U4 Shapes and surfaces | side bars, nested cards, pills and large radii everywhere, the untouched component kit |
| U5 Icons and emoji | emoji as icons, sparkles, the fast/secure/AI icon trio, text symbols as icons |
| U6 Layout and page assembly | the templated landing page, uniform sections, uniform density |
| U6b Dashboards and admin screens | the default shell, invented deltas, charts titled by their type, missing empty states, dead controls |
| U7 Motion | fade-in on scroll, `transition: all`, pulsing dots, count-up numbers |
| U8 Numbers, proof and images | invented figures, logos and testimonials, decorative charts, stock images |
| U9 Generated documents and pages | kickers repeating titles, sections that explain themselves, pills on every value |

It ends with the over-corrections to avoid (replacing one default with another) and the final
question: shown this page and told « une IA l'a fait », would someone believe it at once?

## Related skills

The text of the page follows `ts-general-deslop-writing` when it is installed; run its checker
on the visible text when the page has long passages. A deck follows `ts-general-deslop-slides`.
