# Integración de puntos de la evaluación crítica

## Objective
Integrate the improvement points from `docs/arquitectura/soluciones-similares.md` into the idea (docs, MVP, pitch deck), low-effort points first.

## Problem / Why
The judge evaluation found weaknesses (build vs buy, uncalibrated assumptions, review load, chat focus, personal data, MEF residue). The pitch must answer them.

## Decisions (user, 2026-10-15)
- No third-party APM/EA vendors are bought; own build with open/free sources.
- Limited university budget. Azure stays as the enterprise target architecture; the solution must be cloud-portable without friction.
- MVP may use dependencies and the free tier of Azure or GCP; the LLM provider is pluggable (Google, OpenAI, Anthropic Claude), not locked to Azure OpenAI.
- No MEF or real organizations anywhere (academic case focused on agentic AI).

## Ranking by impact (effort / cost)
1 Calibration pilot (M/free) · 2 Build-with-OSS decision (S/free) · 3 Pseudonymize + remove MEF (S/free) · 4 SBOM CycloneDX (S–M/free) · 5 Review load metrics + SLA (S/free) · 6 Deprioritize chat (S/saves) · 7 endoflife.date + OSV/NVD only (S/free) · 8 catalog-info.yaml (S/free) · 9 Cost estimate (M/free) · 10 MCP server (M/free) · 11 SaaS discovery (M–L/out of MVP).

## Tasks
- [x] T1 — Docs: decisions (build+OSS, cloud-portable, pluggable LLM, free-tier MVP), chat deprioritized, EOL free sources only, review load metrics + proposed SLA, remove MEF from docs, rewrite build-vs-buy in soluciones-similares. Route: delegated (writer trigger, 2+ non-trivial files).
- [ ] T2 — MVP: pseudonymize git authors, remove MEF from code/fixtures/tests/README. Route: delegated (writer trigger). DEFERRED 2026-10-15: user prioritized docs + deck for the idea presentation; writer stopped before any edit (mvp/ untouched).
- [x] T3 — Pitch deck: reflect T1/T2 (build with OSS, chat secondary, calibration as challenge, review load, privacy, cloud-portable/free-tier MVP). Route: delegated (after T1).
- [ ] T4 — (next, M) SBOM CycloneDX + catalog-info.yaml connectors.
- [ ] T5 — (next, M) Calibration C1–C4 (`odd/tasks/mvp-calibracion.md`).
- [ ] T6 — (next, M) Cost estimate (free tier vs Azure target) and MCP server design.

## Constraints
- Commits are GPG-signed: agents do not commit; the user commits per task.
- Writers T1 and T2 run in parallel on disjoint surfaces.

## Progress / Evidence
- T1 (route: delegated, writer trigger — 6 non-trivial doc files). Edited `soluciones-similares.md` (build-with-OSS stance, matrix Costo/Asistente rows, open EOL sources + curated EOL table), `roadmap.md` (new section `#decisión-construir-con-fuentes-abiertas`, MCP before chat, chat optional in F5, F3/F4 exit depends on calibration pilot), `arquitectura-solucion.md` (new `#portabilidad-y-costo` with pluggable LLM layer and Azure target vs free-tier MVP mapping; chat marked secondary), `gobierno-datos.md` (new `#sla-de-revisión-y-carga-de-revisión`: proposed 5-business-day SLA + review-load metrics; `#pendiente-de-definir` kept for notifications), `interfaz.md` (comment mandatory to reject/return, optional to approve; Approve shown after evidence/diff; chat secondary), `ia-agentes.md` (MEF removed, TIME fixed, pluggable provider note, EOL free sources).
  - Evidence: `grep -rniw mef docs` → 0; `npm run build` → 15 pages, Complete; built HTML contains ids `decisión-construir-con-fuentes-abiertas`, `portabilidad-y-costo`, `sla-de-revisión-y-carga-de-revisión`, `pendiente-de-definir`, `modelos-por-rol`; `git diff --stat -- docs` → 5 tracked files, 87+/25− (plus untracked `soluciones-similares.md`).
  - Commit: pending by user (GPG-signed).
- T3 (route: delegated, after T1). Regenerated `docs/presentaciones/pitch-apm-ia-agentica.pptx` from the pptxgenjs generator (session scratchpad `pitch/build.js`), same 8 slides/titles/palette. Slide 4: "Chat con RAG" replaced by "Minería de contratos"; metamodel card adds consulta vía API/MCP (chat opcional, después); "Fuentes abiertas" (CycloneDX, endoflife.date, NVD/OSV); "Plataforma portable" (Azure objetivo, MVP capa gratuita Azure/GCP, IA Gemini/OpenAI/Claude/Azure OpenAI); "¿Por qué no comprar?" band. Slide 5: chip "Consulta API/MCP". Slide 6: chat ≥90 % stat replaced by "0 en licencias"; differentiator (contract/TDR mining not documented by reviewed tools) + per-attribute provenance; calibration caveat kept. Slide 7: calibration pilot, review load (SLA 5 business days + metrics), automation bias, personal data, build vs mature products; 3-level stop line kept. Cover graph chat icon swapped for plug. Speaker notes updated.
  - Evidence: `validate.py` → All validations PASSED; titles in order (8); case-sensitive word grep MEF/Credicorp/lorem/TODO → 0 (only Spanish "todo"); size 245,043 bytes; OnlyOffice x2t + Ghostscript render, one fix round (slide 4 title wrap, platform card text); `npm run build` → 15 pages, Complete; `presentaciones.json` lists the deck.
  - Commit: pending by user (GPG-signed); git index untouched (older deck version still staged).
