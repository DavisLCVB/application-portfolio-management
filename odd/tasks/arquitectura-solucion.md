# Arquitectura de solución y despliegue de la IA (Azure)

## Objetivo
Publicar en el portal la arquitectura de solución propuesta: despliegue en Azure (App Service + Azure SQL), capa de IA agéntica, recuperación de contexto (RAG), modelos por rol, ingesta de datos y operación segura.

## Problema / por qué
El portal describe capacidades, datos y gobierno, pero no cómo se despliega el sistema ni cómo la IA interactúa técnicamente con la API y los datos. Era el pendiente "arquitectura de solución" para salir de F0.

## Decisiones aceptadas
- App Service (web + API) con Azure SQL como registro maestro (usuario, 2026-10-01).
- Capa de IA en el ecosistema Microsoft: Azure OpenAI; agentes orquestados; canal opcional Copilot Studio/Teams (supuesto del proyecto).
- Los agentes solo actúan vía la API del APM, con mínimo privilegio; toda escritura es un borrador sujeto a aprobación.
- Es una propuesta de arquitectura; no describe una implementación existente.

## Alcance autorizado
`docs/arquitectura/` (página nueva + diagrama `.puml`/`.svg` + `manifest.json`), sidebar en `website/astro.config.mjs`, enlace en `docs/arquitectura/index.md`. Sin código de aplicación. Sin mencionar organizaciones reales.

## TDD
Desactivado (repo documental). Checks: `npm test`, `npm run diagrams:check`, `npm run build` (en `website/`), y compilación PlantUML vía `npm run diagrams`.

## Estrategia de entrega
ask-on-risk. Rama: `docs/arquitectura-solucion`.

## Tareas
- [x] T1 — Página `arquitectura-solucion.md` + diagrama ArchiMate de despliegue + sidebar + enlace en índice. Ruta: delegado (writer, 2+ archivos no triviales).

## Progreso
- T1 (delegado; revisado por el orquestador 2026-10-01): corregida la fila Restringido (no se carga en Azure SQL, coherente con la clasificación del informe). Checks: `npm run diagrams` 8 regenerados, `diagrams:check` 8 al día, `npm test` 1/1, `npm run build` 13 páginas, sin menciones a organizaciones reales. Modelos: solo `text-embedding-3` nombrado (verificado en Microsoft Learn); chat y pequeño genéricos.

## Siguiente paso
Revisión del usuario; push/merge a su decisión.
