# Presentaciones con visor de Office

## Objective
Add a "Presentaciones" section to the website that embeds PowerPoint files from `docs/` using the Office Online viewer.

## Problem / Why
`docs/` is the official knowledge source; course decks should be published from it instead of living as loose files. Browsers cannot render `.pptx`; the site is deployed on Vercel (public URL), so the Office Online embed viewer can render them.

## Scope
- Copy every `.pptx` under `docs/` (skip hidden entries and symlinks) to `website/public/presentaciones/` and write `website/src/generated/presentaciones.json` before `dev`/`build`, reusing the PDF pipeline logic (shared helper, no duplication).
- New page `/presentaciones/` that embeds each deck via `https://view.officeapps.live.com/op/embed.aspx?src=<absolute url>`; absolute URL built client-side from `location.origin`. On localhost/127.0.0.1 show a notice instead of the iframe. Always offer download.
- Sidebar entry "Presentaciones"; guide and CLAUDE.md updated.

## Constraints
- Generated outputs are gitignored and never committed.
- Office viewer needs a publicly reachable URL (production domain; Vercel-protected previews will not work) and has file size limits.
- Commits directly on `main` (TBD), Conventional Commits, no AI attribution.

## Delivery
Forecast ~200 authored lines, one work unit. Strategy: ask-on-risk. RDD: off (global) → ordinary checks only.

## Tasks
- [x] T1 — Pipeline + page + sidebar + docs for presentations. Route: delegated, writer trigger (2+ non-trivial files).
- [x] T2 — Human-readable presentation titles: embedded `dc:title` from `docProps/core.xml`, fallback to prettified basename; PDFs unchanged. Route: delegated, writer trigger (2+ non-trivial files).

## Acceptance criteria
- `npm test` and `npm run build` pass; `dist/presentaciones/index.html` exists.
- With a sample `.pptx` in `docs/`, it is copied to `public/presentaciones/` and listed in the manifest (covered by test).
- Removing a `.pptx` from `docs/` removes its generated copy on next run.

## Progress / Evidence
- T1: shared helper `website/scripts/publish-files.mjs` used by `prepare-pdfs.mjs` and new `prepare-presentations.mjs`; page `website/src/pages/presentaciones.astro`; sidebar, `.gitignore`, guide `docs/guias/publicacion.md` and `CLAUDE.md` updated (CLAUDE.md is untracked in git, edited but not committed).
- RED: `npm test` failed with ENOENT copying `prepare-presentations.mjs` (script missing) in new test `prepare-presentations.test.mjs`.
- GREEN: `cd website && npm test` → 2 pass, 0 fail.
- `cd website && npm run build` → 14 pages built; `website/dist/presentaciones/index.html` exists.
- `git status --short` → no generated outputs or `.pptx` files listed.
- RDD off (global): ordinary checks only.
- Commit: `922bcee` feat(website): sección de presentaciones con visor de Office.
- T2: new `website/scripts/pptx-title.mjs` (ZIP central directory + `zlib.inflateRawSync`, Node built-ins only, any failure → fallback); optional `title(fullPath, relativeName)` hook in `publish-files.mjs` (default = relative path, so PDFs keep their titles); `prepare-presentations.mjs` passes `presentationTitle`. Page unchanged (renders `title`).
- T2 RED: `npm test` failed with ENOENT copying `pptx-title.mjs` after adding assertions for `Mi & deck` (deflated test ZIP) and `Otro archivo final` (garbage `.pptx`).
- T2 GREEN: `cd website && npm test` → 2 pass, 0 fail.
- T2 build: `npm run build` → 15 pages; `src/generated/presentaciones.json` title `APM con IA agéntica`.
- T2 commit: pending (GPG-signed, by user).

## Next step
Manual check of the Office viewer on the production domain after deployment with a real `.pptx`.
