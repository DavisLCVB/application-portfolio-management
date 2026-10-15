# Pitch deck del APM con IA agéntica

## Objective
Build a modern pitch deck (.pptx, Spanish) about the APM idea, sourced from `docs/`, published through the "Presentaciones" section.

## Problem / Why
The user needs to present the idea as a pitch. `docs/` is the official source; the deck must not reintroduce MEF/Credicorp framing (academic case focused on agentic AI for APM).

## Scope
Slides: 1 Carátula · 2 Problema actual · 3 Diagrama del problema · 4 Herramientas de solución · 5 Diagrama de la solución · 6 Beneficios · 7 Retos y riesgos · 8 Agradecimiento/cierre.
Output: `docs/presentaciones/pitch-apm-ia-agentica.pptx`. Style reference: `~/Documents/GobIA_TF/GobIA_TF_Arquitectura_IA_propuesta.pptx` (outside repo, read-only).

## Constraints
- Content only from `docs/`; no real organizations or data; public once deployed.
- Office viewer limit ~10 MB.
- Commit on `main` (TBD), Conventional Commits, no AI attribution.

## Delivery
One work unit (binary deck). RDD off (global).

## Tasks
- [x] T1 — Build deck, validate, publish under docs/presentaciones. Route: delegated, preparation trigger (broad reading of docs + reference deck before writing).

## Acceptance criteria
- 8 slides in the order above, each with a visual element; diagrams on slides 3 and 5.
- `validate.py` passes; text extraction shows no placeholders/typos.
- `npm run build` lists the deck in `website/src/generated/presentaciones.json`.

## Progress / Evidence
- T1 done: 8-slide deck generated with pptxgenjs (structured: theme, 2 layouts, sections, speaker notes), palette from the reference deck (deep teal 0B3C49, teal 127C86, amber F2A900, terracotta C4533A, green 3F8F6B), Calibri throughout, motif = icons in solid circles + portfolio-graph hub on cover/closing.
- Slide 3 and slide 5 are native-shape diagrams (editable); slide 5 simplifies the ArchiMate `ia-descubrimiento` pipeline (the SVG at 4014x581 is unreadable at slide size).
- `validate.py`: All validations PASSED. Text extraction: 8 titles in order; 0 matches for MEF/Credicorp/lorem/TODO (word match). Size 259,709 bytes.
- Visual QA: rendered with OnlyOffice x2t + Ghostscript; one fix round (Cambria not installed locally -> switched headings to Calibri; cover title/graph overlap; slide 5 chip wrap; bullet indent).
- `npm run build`: OK; `presentaciones.json` lists `presentaciones/pitch-apm-ia-agentica.pptx`.
- Commit: pending — `feat(docs): presentación pitch del APM con IA agéntica` staged; GPG signing timed out (pinentry needs the user).

## Next step
User review of the deck in the Presentaciones section; push remains a user decision.
