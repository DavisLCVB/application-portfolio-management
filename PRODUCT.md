# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: course evaluators (instructors or jury) reviewing an academic case. They need to grasp the proposal, the architecture, and the current progress quickly, typically while or after the author presents the idea.

## Product Purpose

A static documentation portal for a future Application Portfolio Management (APM) system for an IT Architecture team, with agentic AI as its focus. It publishes the system's architecture (ArchiMate 3.2 diagrams as code), supporting documents (PDF), and presentations (PPTX). The APM itself is not implemented yet; success means evaluators understand the proposal and its credibility from the portal alone.

## Positioning

Architecture as code: every ArchiMate view is a versioned PlantUML source with CI-verified generated SVGs, and agentic AI applied to portfolio discovery is the core proposal.

## Operating Context

- Content lives in `docs/` (Markdown/MDX, PDF, PPTX, `.puml` diagrams) and is rendered by `website/` (Astro + Starlight).
- Sections: architecture (solution, catalogs, data model, data governance, AI agents, interface, roadmap, similar solutions), guides, documents, presentations.
- Presentations embed the Office Online viewer, which works only on the public production domain.
- Deployment target: Vercel (not configured yet).

## Capabilities and Constraints

- All content and UI are in Spanish.
- Academic case: no real organization, no real data. MEF or other institutions may appear only as illustrative examples, never as the client.
- Very limited university budget: own build with free/open sources and free tiers; no paid APM/EA vendors.
- Everything under `docs/` is public once deployed.
- Sidebar is hand-maintained in `website/astro.config.mjs`.

## Evidence on Hand

- ArchiMate views and SVGs: `docs/arquitectura/diagramas/`.
- Presentation: `docs/presentaciones/apm-agents.pptx`.
- MVP prototype code: `mvp/` (synthetic fixtures only).
- No real users, testimonials, metrics, or deployments exist; do not fabricate them.

## Product Principles

1. Clarity for a first-time evaluator beats exhaustiveness.
2. Honest status: state what is proposed versus built.
3. Architecture is the evidence; diagrams must stay legible and current.
4. Zero-cost, open tooling.
