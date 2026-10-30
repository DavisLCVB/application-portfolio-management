# Landing de la portada y detalles globales

**Locator:** `odd/tasks/landing-portada.md` · Engram `odd/landing-portada/tasks`

## Objective

Turn the home page into a landing that shows the agentic-AI proposal in action, and polish interaction details across the site, so the portal stops reading as a stock documentation site.

## Problem / Why

The user reported the site "looks like just a documentation website". The 2026-10-29 critique scored the home 22/40: generic Starlight look, no evidence of the core idea in the first viewport. Primary readers are course evaluators with limited time (PRODUCT.md).

## Scope (authorized: "Landing + detalles globales")

- Home becomes `website/src/pages/index.astro` (Starlight `splash` template via `StarlightPage`), replacing `docs/index.md`. Components cannot be imported from `docs/` (it lives outside the Vite root).
- Home sections: hero with staggered text reveal; live "agent console" showing the discovery pipeline reasoning over a synthetic example app; status block; data cycle revealed on scroll; suggested path.
- Site-wide detail polish (make-interfaces-feel-better): text wrapping, diagram outlines, consistent hover/focus/press states, motion tokens.
- Out of scope: docs page content, `.puml` sources, new fonts/palette (DESIGN.md world stays), lightbox keyboard a11y (separate accessibility front).

## Constraints

- Spanish UI copy; synthetic/illustrative data labeled as such; no invented metrics, clients or testimonials.
- Zero budget, no new runtime dependency unless CSS cannot do it (GSAP only as fallback).
- Every animation honors `prefers-reduced-motion`; motion never the only channel.
- Starlight tokens (`--sl-color-*`) only; works in light and dark themes and at 390px.
- Do not edit `website/src/generated/` or `website/public/documentos|presentaciones/`.

## Tasks

- [x] T1 · Landing: create `website/src/pages/index.astro` (splash), move home content, delete `docs/index.md`, hero with texts reveal, agent console (reasoning stream + thinking states), cycle with scroll reveal, status + suggested path. Route: delegated (writer, 2+ non-trivial files).
- [x] T2 · Global details in `website/src/styles/custom.css`: text-wrap, diagram image outline, link/button hover-focus-press, motion tokens, reduced motion. Route: delegated with T1 (same writer, shared CSS).
- [x] T3 · Verify: build, tests, impeccable detect, browser check desktop/narrow, light/dark, reduced motion. Route: inline (parent spot check).

- [x] T4 · GSAP collection animation replaces the console in the hero: SVG of sources → evidence fragments travelling along paths (MotionPathPlugin) → Agents 1/2 → Agent 3 score → Agent 4 nudge → Fact Sheet assembled → architect approval → catalog; looping per example app. Console kept as the reduced-motion / no-JS / screen-reader alternative. Adds dependency `gsap@3.15.0` (user-approved 2026-10-29, free standard license). Route: delegated (writer).

- [x] T5 · Roadmap phases table → colored vertical timeline (`docs/arquitectura/roadmap.md` raw HTML + `.apm-fases` CSS in custom.css): one oklch hue per phase at equal lightness, F0 marked "En curso" with pulsing node, scroll reveal, reduced-motion guard. Requested by user 2026-10-29 ("más vivo"). Route: inline (one content file mechanical conversion + one CSS block). Checked: dark/light screenshots; colored text ≥5.2:1 in both themes.

- [x] T6 · Site-wide shell redesign so pages stop reading as stock docs (user request 2026-10-29: "botones con íconos, transparencias, transiciones", all pages): translucent blurred header and sidebar, icons on sidebar groups/links and on buttons/actions (inline SVG, one stroke set), styled content blocks (tables, asides, diagram figures, headings with anchors), hover/press transitions, cross-document View Transitions between pages, reduced-motion guards. Bento grids (user request 2026-10-29) on entry/navigation surfaces only: home below the hero (cycle large, status medium, suggested-path tiles with icon + phase-style hue), Arquitectura overview opening with a bento of its 8 subpages (icon, one-line description, diagram thumbnail where one exists), Presentaciones hero tile; long reading pages keep a single reading column. Blurred gradient "aurora" backgrounds (user reference image 2026-10-29: dark base with large blurred blue/indigo/violet blobs): vivid and slowly drifting behind the home hero; faint and static at the top of every other page so the translucent header/sidebar have something to blur; pastel variant in light theme; pure CSS (blurred radial gradients, transform-only motion), static under reduced motion, text contrast verified over the brightest blob. Starlight component overrides allowed only where CSS cannot do it. Route: delegated writer, after T4 writer finishes (single writer at a time).

## Acceptance criteria

- First viewport of `/` states the proposal and shows the agents working, without scrolling.
- No horizontal overflow at 390px; both themes legible (text ≥4.5:1).
- With reduced motion, all content is visible statically.
- `npm run build` and `npm test` pass; detector has no unexplained findings.

## Checks

`cd website && npm run build && npm test`; `impeccable detect --json website/src/pages`; browser visual check.

## Progress

- 2026-10-29: feature document created; scope confirmed by user.
- 2026-10-29: T1+T2 written by delegated writer (not committed). `/` is now `website/src/pages/index.astro` using Starlight's hero (console in `hero.image.html`); `docs/index.md` removed. Pending: sidebar entry `{ label: 'Inicio', slug: 'index' }` in `website/astro.config.mjs` must become `{ label: 'Inicio', link: '/' }` (outside writer surface); build passes in a scratch copy with that change. Detector: one `gradient-text` warning, the thinking-states shimmer on the console status line (intentional, not a heading).
- 2026-10-29: parent applied sidebar `{ label: 'Inicio', link: '/' }`. Fixed console loop: CSS minifier rewrites `2800ms` as `2.8s`, script parsed it as 2.8 ms; `ms()` now honors units. Cycle widened to hero width; suggested-path descriptions capitalized.
- Verification: `npm run build` 15 pages OK; `npm test` 2/2 pass; detector 1 finding `gradient-text` (index.astro thinking-state shimmer, intentional, not a heading). Browser: desktop dark + light checked, console status and log animate correctly. Not verified: real 390px viewport (window cannot resize), reduced-motion rendering (code-guarded only), scroll reveal visually.
- Next: user review; commit when approved (no commit made).
- 2026-10-29: T4 written by delegated writer (not committed). Hero console replaced by an inline SVG (`aria-hidden`) animated with `gsap@3.15.0` + MotionPathPlugin (bundled, ~92 kB hashed asset); console kept as static text alternative (visually hidden under `prefers-reduced-motion: no-preference` and `scripting: enabled`, shown otherwise); old console loop script and shimmer removed. Checks: build 15 pages OK, `npm test` 2/2, detector `[]`; browser: full loop seen in dark + light, no page errors. Not verified: 390px rendering (text scales to ~66%), reduced-motion fallback visually.
- 2026-10-29: T6 written by delegated writer (not committed). Aurora (fixed CSS radial blobs: vivid + 28s/36s drift on home, faint static elsewhere, pastel in light), glass header/sidebar/TOC with `@supports` fallback, authored 1.5-stroke icon set as CSS mask tokens (`--apm-i-*`, sidebar mapped by href), `.apm-btn` primary/secondary shared with `.sl-link-button`, bento on home / Arquitectura overview (8 tiles, diagram thumbnails via Markdown images) / Presentaciones hero tile, styled tables/asides/diagram plates/link underline, cross-document View Transitions on `main` only, hero SVG hidden below 36rem (console log shown). DESIGN.md rewritten ("El Cuaderno bajo la Aurora"). Checks: build 15 pages OK, `npm test` 2/2, detector `[]`; browser (built preview): dark/light home, /arquitectura/, /arquitectura/modelo-datos/, /presentaciones/; view transition fired on tile click; worst-case aurora overlap contrast 4.75:1 (dark), 7.8:1 (light); no page console errors. Not verified: real 390px render, reduced-motion visually, `.impeccable/design.json` not regenerated (outside surface). Dev server on :4321 does not pick up `docs/` edits until restarted.
- 2026-10-29: parent spot check after dev-server restart: home hero + bento and /arquitectura/ 8-tile bento render correctly (an apparent gap was the entrance animation mid-flight). T6 ticked. Aurora is subtle in dark theme (alphas lowered for 4.75:1 contrast); offered user a more vivid variant. Nothing committed.
