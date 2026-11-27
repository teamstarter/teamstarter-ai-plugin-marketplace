# The marks of a generated interface: catalog and review checklist

Each entry gives the mark, why a reader takes it for generated, the fix, and when it is fine.
Two levels:

- Remove: almost always a reflex. Report every occurrence, unless the organization's design
  system specifies it.
- Earn it: fine when the element carries information here, a mark when it decorates. Name the
  element, ask what it tells the user, and report only the decorative use.

The `[id]` after a title is the rule id of `scripts/check_ui.py` when the script can see it.

## U1. Text on the page

The words of a page follow `ts-general-deslop-writing` when it is installed. The marks that
matter most on a page:

- Remove: em dash in headings, buttons and labels `[em-dash]`; « · » strings of metadata
  (« Paris · 12 mars · 3 places ») `[separator]`; bold label followed by a colon `[bold-label]`.
- Remove: the headline formula of two imperative fragments (« Ship faster. Build smarter. »,
  « Simple. Rapide. Efficace. »), more than once per page.
- Remove: sales vocabulary in place of what the product does (seamless, supercharge, « en toute
  fluidité », « boostez »). Say what happens, with a number.
- Remove: a page that describes itself. A subtitle that says what the section is or how to read
  it (« Une ligne par objet », "Here's an overview of…"), a kicker that repeats the title, a
  header paragraph that lists what the page contains. The title names the section; the content
  starts below it. A legend that decodes a color or a glyph is content and stays.
- Remove: process text left on the page (« Option A », "generated from", « à remplir »,
  "Lorem ipsum", `[Nom du client]`, 2025-XX-XX, example.com).
- Earn it: an arrow in a call to action. Fine on the one primary action, a mark when every
  button has one `[unicode-icon]`.
- A button says what happens (« Enregistrer », « Publier le projet »), and the same action keeps
  the same name from the button to the confirmation message. Generic labels (« En savoir plus »,
  « Découvrir », "Get started", "Learn more") are a mark when every button has one
  `[generic-cta]`.
- A label, its sublabel, its helper text and its placeholder do not repeat each other.
- An empty state says what to do next, without marketing copy. An error says how to recover; a
  success message confirms what happened. Not every message ends with « ! ».
- Casing: one convention (sentence case unless the design system says otherwise), held from
  headings to buttons.

## U2. Color and background

- Remove: purple, violet or indigo gradient, purple on dark, cyan on dark `[purple-gradient]`.
  The default palette of generated pages. Fix: the organization's palette.
- Remove: gradient text on a headline `[gradient-text]`. One solid color; size and weight carry
  the impact.
- Remove: blurred color blobs, a spotlight glow from the top of the hero, a glowing orb used as a
  mascot `[blur-blob]`.
- Remove: colored glow under a button or a card `[glow]`.
- Remove: Claude's own house palette (cream background, serif display, terracotta accent) on a
  page that is not Anthropic's `[claude-palette]`. A model drifts back to it when nothing else is
  decided.
- Earn it: dark theme. Fine when the product calls for it; a mark when chosen by reflex with
  frosted glass everywhere `[glass]`.
- Earn it: dot-grid or line-grid backgrounds `[dot-grid]`, only when they belong to the brand.
- Earn it: one accent color per view; a second accent competes with the first.
- The palette test: if these colors would look the same on any other company's page, nothing was
  decided. Start from the organization's tokens.

## U3. Type

- Remove: spaced capitals as the default label style (eyebrows above every heading, table
  headers, badges) `[uppercase]` `[letter-spacing]`. Fine when the organization's type scale
  specifies them; then pass `--allow uppercase`.
- Remove: one word of the headline in another color, in italics or in another font.
- Earn it: Inter, Roboto, Poppins, Space Grotesk, Geist, Fraunces, Instrument Serif or an italic
  serif display on the hero `[font]`. Fine when it is the organization's font; a mark when it is
  the default.
- Earn it: monospace for small data labels. Fine for code and ids; a mark as a costume.
- Quality floor (rendered page): heading at least 1.25 times the size of the level below, body
  line height at least 1.3, text at least 12 px, lines under about 80 characters, no last line of
  one word on a heading.

## U4. Shapes and surfaces

- Remove: a colored bar on one side of a card, a callout, a quote or a list row `[side-bar]`.
  Tint the surface, or say the state with a label.
- Remove: cards nested in cards. Group with space and type; two levels of container at most.
- Remove: the same large radius on every surface, pills for buttons and sections `[pill]`
  `[radius]`. One radius per level (section, block, small element); pills for tags, chips,
  counters and progress bars only.
- Remove: a thin border on every surface plus a wide shadow, the untouched component-kit look
  (gray palette, gray secondary text, library font). Make the decisions the kit left open.
- One card style, one button pair (primary, secondary), one link look across the page.

## U5. Icons and emoji

- Remove: emoji in place of icons (🚀 🎯 💡 ✅ on feature cards, in headings, in the navigation)
  `[emoji]`.
- Remove: sparkles as the sign of AI `[sparkles]`. Name the capability.
- Remove: the trio lightning = fast, shield = secure, sparkles = AI on three equal cards.
- Remove: text symbols used as icons (▸ ▾ ↗ ✕) `[unicode-icon]`. Use the icon set of the design
  system.
- Earn it: an icon beside a navigation item (when it encodes a category), a chevron on a row (when
  the row opens), a check mark in a comparison (when there is something to compare).
- Earn it: an icon tile above every heading. Fine for a real category system; a mark as filler.

## U6. Layout and page assembly

The mark is the assembly. Report the pattern once, with its pieces, when three or more appear:

- a badge pill above the hero headline (« ✨ Nouveau : v2.0 → ») with nothing to announce;
- a centered hero: headline, gray subtitle, two buttons side by side;
- every section built the same way: eyebrow, big centered heading, gray subheading, grid;
- three equal cards with an icon, a title and two lines;
- numbered steps 01, 02, 03 with circles and a line, on content that is not a sequence
  `[numbered-marker]`;
- a band of statistics (« 99,9 % de disponibilité », « +10 000 équipes »);
- a pricing table with « Le plus populaire » on the middle column;
- a logo marquee, stacked avatars, five stars, three polished testimonials `[marquee]`;
- a bento grid where every tile weighs the same;
- an FAQ accordion and a four-column footer of links as filler.

Fix: build the page around what the reader must understand or do. Vary the weight of blocks by
importance; ship only sections that have content behind them; at most two actions in the hero.
Density follows the use: dense where people work, airy where they decide; not the same padding
everywhere.

## U6b. Dashboards and admin screens

- Remove: the default shell (a sidebar, four stat cards with green deltas, a line chart, a recent
  activity feed) whatever the job of the screen. Start from the decision the screen serves: what
  the person must see, compare or do.
- Remove: invented deltas (« +12 % ce mois-ci »), filler activity feeds, John Doe rows.
- A chart's title is the question it answers (« Quels sites ont le plus de projets en retard ? »),
  not its type (« Graphique »).
- Table columns are chosen from that decision, numbers aligned right in tabular figures.
- The empty state, the filtered-to-nothing state and the access-denied state are three different
  screens; a loading skeleton has the shape of the final layout.
- No dead control: every button, link and menu item does something, or is not there.

## U7. Motion

- Remove: fade-in and slide-up on every section as it scrolls in `[scroll-reveal]`. Static by
  default; animate the one moment that needs it.
- Remove: `transition: all` `[transition-all]`. Transition the properties that change.
- Earn it: a pulsing status dot `[pulse]`. Fine for a real-time state; a mark as decoration.
- Earn it: hover lift or scale on cards `[hover-scale]`. Fine on cards that open something, the
  same on all of them.
- Earn it: count-up animation on numbers `[count-up]`. Show the number; it must be real.
- Interaction feedback under 200 ms; no blinking cursor in the hero, no marquee.

## U8. Numbers, proof and images

These are honesty rules before style rules. Never present invented data, people or endorsements
as real.

- Remove: invented statistics, customer logos, testimonials with names and job titles, ratings,
  « Batch n° 047 » details, default names (Acme, Northwind, Priya, Jean Dupont) presented as
  real. Use the organization's real figures with their source, or nothing.
- Remove: charts, sparklines, gauges and percentages that measure nothing.
- Remove: stock photography or a generated image where the product, the team or the real output
  should be; an illustration drawn from basic shapes standing in for a product screenshot.
- Earn it: a progress ring, a meter, a green delta. Fine when it shows a real measure the user
  needs.

## U9. Generated documents and pages (artifacts, reports, dashboards)

Pages generated from a template by an AI tool (a report, a dashboard, a project page) add their
own marks:

- the kicker or eyebrow that repeats the title, or a « · » string of metadata above it;
- a sentence under each title explaining the section instead of starting it;
- a header that counts what the page contains (« 12 sections, 4 tables »);
- the same block anatomy for every section, whatever its content;
- pills, chips and badges on every value;
- emoji as section icons;
- a closing « Prochaines étapes » or « En résumé » block that repeats the page.

Keep in the header what the reader needs to act (status, owner, date, the decision asked); fold
the rest.

## Over-correction

Removing marks breeds new ones. Check the replacements too:

- the gradient removed, then the page in the gray component-kit look: make the palette
  decision instead;
- the purple replaced by another default: emerald, cream and terracotta, near-black with one
  acid green accent, the editorial look (serif greeting, serif numbers, cream) on a product
  dashboard;
- every radius set to zero, every border removed until nothing groups the content;
- the eyebrow in capitals replaced by an eyebrow in small gray text above every heading: the
  eyebrow itself was the reflex.

## The final question

Shown this page and told « une IA l'a fait », would someone believe it at once? If yes, find
which decisions were left to the default and make them.
