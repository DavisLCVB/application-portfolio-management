# Soluciones similares y evaluación crítica

## Objective
Add a docs page that surveys existing solutions to the same problem (with and without AI) and critically compares the proposed idea's strengths and weaknesses against them.

## Problem / Why
The pitch needs positioning against the market and an honest assessment; `docs/` is the official source.

## Scope
- New page `docs/arquitectura/soluciones-similares.md` (Spanish), sidebar entry in `website/astro.config.mjs`.
- Section A: solutions without AI (EA/APM tools, CMDB, spreadsheets/manual, open source).
- Section B: solutions with AI (vendor AI features, discovery/agentic approaches, research).
- Section C: strengths/weaknesses of the proposal vs. those solutions (judge stance).

## Constraints
- Primary sources with URLs; mark unverified claims and freshness (as of 2026-10).
- No real client organization; public page.
- Runs concurrently with the pitch-deck writer: do not commit; parent commits after both finish.

## Tasks
- [x] T1 — Research + write page + sidebar. Route: delegated, user-requested agent + research trigger.

## Acceptance criteria
- Page builds (`npm run build`) and appears in sidebar.
- Each product claim cites a source URL.
- Comparison table + strengths/weaknesses grounded in `docs/` with path references.

## Progress / Evidence
- T1 done 2026-10-15: `docs/arquitectura/soluciones-similares.md` (26 cited sources, 7 non-AI + 7 AI entries, strengths/weaknesses, matrix, take/avoid) and sidebar entry after 'Roadmap' in `website/astro.config.mjs`.
- `npm run build`: OK, 15 pages; `dist/arquitectura/soluciones-similares/index.html` exists; 12/12 in-page anchor links to sibling pages resolve.
- `npm test`: 2 pass, 0 fail.
- Unverified: Orbus/Bizzdesign AI details, Now Assist specific to APM, LeanIX July 2026 update, all pricing (no public prices). ServiceNow and Essential pages returned 403 to fetch.
- Commit: pending, made by parent (concurrent writer on main).

## Next step
- Parent commits (`docs(arquitectura): soluciones similares y evaluación crítica`).
