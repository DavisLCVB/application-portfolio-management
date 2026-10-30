---
name: APM · Arquitectura TI
description: Documentation portal for an agentic-AI Application Portfolio Management proposal.
colors:
  accent: "#387bd6"
  accent-low: "#172b46"
  accent-high: "#b9d7ff"
  ink-black: "hsl(224, 10%, 10%)"
  slate-panel: "hsl(224, 14%, 16%)"
  slate-line: "hsl(224, 10%, 23%)"
  slate-muted: "hsl(224, 7%, 36%)"
  slate-dim: "hsl(224, 6%, 56%)"
  slate-text: "hsl(224, 6%, 77%)"
  paper-white: "hsl(0, 0%, 100%)"
  logo-sky: "#38bdf8"
  logo-indigo: "#818cf8"
  logo-pink: "#f472b6"
  logo-emerald: "#34d399"
  logo-tile: "#1e293b"
  aurora-blue: "oklch(0.55 0.19 255 / 0.4)"
  aurora-indigo: "oklch(0.5 0.21 280 / 0.38)"
  aurora-violet: "oklch(0.52 0.22 305 / 0.32)"
  glass: "color-mix(in oklab, hsl(224, 10%, 10%) 62%, transparent)"
  tile: "color-mix(in oklab, hsl(224, 14%, 16%) 62%, transparent)"
typography:
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "2.1875rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.75
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    fontSize: "0.875rem"
rounded:
  sm: "0.5rem"
  md: "0.625rem"
  lg: "0.75rem"
  tile: "1rem"
  logo: "12px"
spacing:
  control-y: "0.35rem"
  control-x: "0.9rem"
  block: "2rem"
  content-pad-x: "1rem"
components:
  button-primary:
    backgroundColor: "{colors.accent-high}"
    textColor: "{colors.ink-black}"
    rounded: "{rounded.md}"
    padding: "0.6rem 1rem 0.6rem 0.875rem"
  button-secondary:
    backgroundColor: "{colors.tile}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.md}"
    padding: "0.6rem 1rem 0.6rem 0.875rem"
  bento-tile:
    backgroundColor: "{colors.tile}"
    rounded: "{rounded.tile}"
    padding: "1.25rem"
  embed-frame:
    rounded: "{rounded.sm}"
    width: "100%"
    height: "75vh"
  nav-bar:
    backgroundColor: "{colors.glass}"
    height: "3.5rem"
  sidebar:
    backgroundColor: "{colors.glass}"
    width: "18.75rem"
---

# Design System: APM · Arquitectura TI

## Overview

**Creative North Star: "El Cuaderno bajo la Aurora"**

The portal is still an honest lab notebook for a proposal under construction, but it no longer looks like stock documentation. Starlight remains the engine; on top of it sits a modern landing world: a soft blurred aurora of blue, indigo and violet light, glass chrome that lets the aurora show through, bento grids on the entry surfaces, one authored icon set, and short purposeful motion. Long reading pages keep a single 45rem column so the architecture stays readable.

Personality comes from: the aurora behind the home hero, the GSAP collection animation that shows the agents working, bento tiles with hue chips, the four-block logo, the click-to-zoom lightbox for diagrams, and plain Spanish copy that marks status explicitly.

The custom accent overrides Starlight in both themes (Starlight styles live in cascade layers, so unlayered `:root` wins). Light theme redefines the trio with inverted roles (pale `#dbe8fa` low, `#2a64b8` accent at 5.8:1 on white, dark `#13325e` high) and switches the aurora to pastel.

**Key Characteristics:**
- Starlight shell with system UI fonts and cool slate neutrals (hue 224), dark theme first.
- Aurora background: vivid and drifting on the home page, faint and static at the top of every other page.
- Glass chrome: header, sidebar and table of contents are translucent with `backdrop-filter`.
- Bento grids only on entry and navigation surfaces (home, Arquitectura overview, Presentaciones).
- One authored 24px stroke icon set (1.5 stroke), painted with `currentColor`.
- Explicit status language ("propuesto", "aún no implementado") over persuasion.

## Colors

Cool slate neutrals carry the text; Cuaderno Blue marks interaction; the aurora and hue chips add atmosphere and identity.

### Primary
- **Cuaderno Blue** (accent): links, active sidebar item, primary button, focus.
- **Deep Ink Navy** (accent-low): dark-mode accent backgrounds and text selection.
- **Pale Sky Ink** (accent-high): accent text and primary button fill on dark backgrounds.

### Atmosphere
- **Aurora** (aurora-blue, aurora-indigo, aurora-violet): large radial blobs on a fixed layer behind everything. Dark alphas are capped so gray-2 body text stays at least 4.5:1 even where all three blobs overlap (measured 4.75:1). Light theme uses pastel versions (L 0.85–0.88, chroma ≤ 0.1).
- **Glass** (glass): 62% ink over the aurora with `blur(16px) saturate(1.6)`; 88% for the full-screen mobile menu. Solid Starlight backgrounds remain when `backdrop-filter` is unsupported.
- **Tile** (tile): 62% slate panel (64% white in light theme). Tiles are translucent but never blurred.

### Tertiary
- **Logo Tiles** (logo-sky, logo-indigo, logo-pink, logo-emerald on logo-tile): used only inside the logo mark.

### Neutral
- **Ink Black** (ink-black): dark-mode page background.
- **Slate Panel** (slate-panel): base for tile and console surfaces.
- **Slate Line** (slate-line): inline-code backgrounds and cycle-step borders.
- **Slate Muted** (slate-muted), **Slate Dim** (slate-dim): secondary text and metadata.
- **Slate Text** (slate-text): body text in dark mode.
- **Paper White** (paper-white): light-mode background and the plate behind diagrams.

### Named Rules
**The Single Ink Rule.** Cuaderno Blue is the only interactive color. Logo tile colors never leave the logo.

**The Phase Hue Exception.** The roadmap timeline gives each phase its own hue (oklch, equal lightness: L 0.8 dark / 0.5 light, chroma 0.16; hues 230, 275, 310, 355, 65, 160). Color there encodes sequence, never interaction. Bento tiles reuse the same recipe (`--apm-tono-l`, chroma 0.16, one hue per tile) for their icon chip and corner glow: color encodes identity, never rank or state.

**The White Plate Rule.** Diagrams always render on a white plate, in both themes, because PlantUML SVGs are drawn for light backgrounds. Tile thumbnails follow the same rule.

**The Contrast-over-Aurora Rule.** Any change to aurora colors must keep body text ≥4.5:1 over the brightest overlap of blobs.

## Typography

**Display Font:** System UI stack (-apple-system, Segoe UI, Roboto, Helvetica Neue)
**Body Font:** System UI stack
**Label/Mono Font:** ui-monospace stack for code, file paths and the agent log

**Character:** Neutral and native, so attention goes to the content and the motion.

### Hierarchy
- **Headline** (600, 2.1875rem; home hero clamps to 3.25rem, -0.02em): page H1 titles.
- **Title** (600, 1.5rem to 1.8125rem, -0.015em): H2/H3. H2 gets 2.75rem above, H3 2rem.
- **Tile title** (600, 1.125rem): bento tile headings.
- **Body** (400, 1rem, 1.75): prose, capped by the 45rem content column.
- **Label** (400, 0.8125rem): sidebar, table of contents, tile descriptions, tables.
- **Code** (0.875rem monospace).

### Named Rules
**The Status-in-Words Rule.** Status (proposed, in progress, built) is written in text, not implied by color or badges.

## Layout

Starlight's three-region layout: glass top nav (3.5rem), glass left sidebar (18.75rem), centered content column (45rem; 67.5rem on the splash home) and a glass right-hand table of contents on wide screens. Narrow viewports collapse the sidebar behind the menu button.

**Bento grids** live inside a `.apm-bento-marco` container (container queries, not viewport queries):
- Home: 12 columns from 60rem (cycle tile 8, status tile 4, four path tiles 3 each), 2 columns from 36rem, 1 column below.
- Arquitectura overview: 6 columns from 36rem with spans 2/3/4 in reading order, 1 column below.
- Presentaciones: one hero tile holding title, actions and the viewer.

Reading pages never use bento; they keep the single column.

## Elevation & Depth

Depth comes from the aurora behind, glass in the middle and translucent tiles on top. Tiles and secondary buttons declare elevation once, as a 1px ring shadow (`oklch(1 0 0 / 0.08)` dark, `oklch(0 0 0 / 0.07)` light); there are no border-plus-shadow ghost cards.

### Shadow Vocabulary
- **Ring** (`--apm-ring`): resting tiles, tables, secondary buttons, embeds.
- **Lift** (`--apm-lift`: `0 1px 2px` + `0 12px 32px -12px`): hover on link tiles and buttons, combined with a hue-tinted ring on tiles.
- **Lightbox lift** (`0 12px 48px rgba(0, 0, 0, 0.5)`): the zoomed diagram.

## Shapes

Tiles 1rem; tables, asides and diagram plates 0.75rem; buttons and hue chips 0.625rem; thumbnails, iframes and sidebar items 0.5rem. Nested radii are concentric: a thumbnail inset 0.5rem from its tile edge uses 0.5rem inside the 1rem tile. Pills are reserved for small status labels.

## Components

### Icons
One authored 24px set, 1.5 stroke, round caps and joins, defined once in `custom.css` as mask data URIs (`--apm-i-*`) and painted with `background-color: currentColor`, so states come from color. Use `<span class="apm-ico apm-ico--NAME">` in pages and raw Markdown HTML; the sidebar maps icons by `href` with `::before`. Names: inicio, arquitectura, catalogos, datos, gobierno, ia, solucion, interfaz, roadmap, similares, documentos, presentaciones, guias, descargar, flecha, externo, pantalla, estado, ciclo. Starlight's own caret and aside icons remain the only exceptions.

### Buttons
`.apm-btn` plus `--primario` or `--secundario`; Starlight `.sl-link-button` shares the same rules.
- **Primary:** accent fill, ink text (white in light theme), inset top highlight.
- **Secondary:** translucent tile fill with ring.
- **Icon:** leading, 1.25em; icon-side padding is 2px less than the text side.
- **States:** hover lifts 1px with the lift shadow; press scales to 0.96; focus-visible shows a 2px accent ring. Transitions name their properties (never `all`), 150ms ease-out.

### Bento Tiles
Translucent tile surface with a hue-tinted radial glow in the top-right corner, hue chip (2.25rem, 0.625rem radius) with the section icon, title, one-line description and, where a diagram belongs to the section, a thumbnail on a white plate. Link tiles add a trailing arrow that shifts 2px on hover; tiles lift 2px and press to 0.98.

### Content Blocks
- **Tables:** rounded container with ring, accent-tinted header row, row hover tint.
- **Asides:** 1px tinted border and 10% tinted fill, 0.75rem radius, no thick side stripe.
- **Diagrams:** white plate with 0.75rem padding, 1px neutral outline, zoom-in cursor.
- **Links:** faint 40% underline at rest that fills to full color left-to-right on hover.

### Navigation
Glass sidebar with an icon on every link and group; the current page keeps Starlight's accent pill; hover tints the row.

### Diagram Lightbox (signature)
Clicking a content image opens it centered at up to 95vw × 95vh on a white plate over an `rgba(10, 15, 25, 0.9)` scrim; closes on click or Escape. Tile thumbnails are excluded because the tile is a link.

### Home Hero
Copy on the left, the GSAP collection animation on the right. Below 36rem viewport the SVG is hidden because its labels would render near 7px; the agent console log (the existing text alternative) shows instead, as it does under reduced motion or without JavaScript.

## Motion

Tokens follow the transitions.dev scale: `--duration-stagger` 40ms, `--duration-quick` 150ms, `--duration-fast` 250ms, `--ease-smooth-out`, `--distance-base` 8px.
- **Page transitions:** cross-document View Transitions (`@view-transition { navigation: auto; }`). Only `main` (`view-transition-name: apm-main`) animates: old content fades out in 150ms, new content fades in and rises 8px in 250ms. Header and sidebar swap instantly so the chrome reads as stable. Browsers without support navigate normally.
- **Bento entrance:** tiles rise 8px once, staggered 40ms (capped at five steps, about 410ms total). Home tiles start when the grid first scrolls into view.
- **Aurora drift:** home only, transform-only loops of 28s and 36s.
- **Micro-interactions:** hover and press per Buttons and Bento Tiles.
- **Reduced motion:** view transitions, drift, entrances, the hero reveal and the GSAP animation are all off; content is fully visible statically.

## Do's and Don'ts

### Do:
- **Do** use Starlight's `--sl-color-*` tokens and the `--apm-*` surface tokens instead of literal colors.
- **Do** keep diagrams on a white plate and make them zoomable.
- **Do** use the shared icon set and `.apm-btn` for every new action.
- **Do** keep bento grids to entry and navigation surfaces.
- **Do** state project status in plain Spanish text.

### Don't:
- **Don't** use the logo tile colors outside the logo mark.
- **Don't** blur tiles or content; glass is for chrome over the aurora only.
- **Don't** raise aurora alpha without re-measuring text contrast.
- **Don't** use `transition: all` or animations without a reduced-motion guard.
- **Don't** add paid fonts or assets; the project runs on a zero budget.
