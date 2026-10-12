# Pipeline Multi-Agente de Descubrimiento y Reconciliación (IA Agéntica Upstream)

## Objetivo
Evolucionar la arquitectura de IA agéntica del APM desde un enfoque de consumo pasivo ("bombero downstream") hacia un sistema multi-agente proactivo de descubrimiento continuo, unificación y reconciliación de datos ("upstream"), con foco bimodal en extracción desde código/despliegues y minería de contratos/TDRs.

## Problema / por qué
El modelo previo asumía datos preexistentes y limpios (vía migración única de Excel o CMDB), limitando la IA a consultas downstream (chat, CVEs, obsolescencia). En organizaciones reales (como el sector público / MEF), el problema raíz es la fragmentación extrema, falta de inventarios actualizados y "Shadow IT". La IA agéntica debe resolver la captura y unificación donde fallan las ETL tradicionales.

## Decisiones aceptadas
1. **Topología Multi-Agente de 4 etapas**:
   - **Agente 1 (Code-to-Catalog / Extracción Técnica)**: Análisis estático de repositorios Git, Dockerfiles, manifiestos K8s, dependencias y endpoints.
   - **Agente 2 (Dark Data Miner / Minería Contractual y Documental)**: Extracción de información de licenciamiento, proveedores, costos, vigencia y SLAs desde contratos y TDRs (PDF/Word).
   - **Agente 3 (Reconciliador Semántico / Entity Resolution)**: Fusión de evidencias heterogéneas, resolución de identidades y cálculo de puntaje de confianza.
   - **Agente 4 (Micro-Nudge / Entrevista Proactiva)**: Interacciones asíncronas de mínima fricción con dueños/desarrolladores para validación en 1 clic.
2. **Notación y estándares**: ArchiMate 3.2 en PlantUML (`docs/arquitectura/diagramas/ia-descubrimiento.puml`), compilado a SVG con verificación en `manifest.json`.
3. **Alineación con Gobernanza OCDE**:
   - Transparencia y Explicabilidad (1.3): Toda propuesta cita evidencia primaria (archivo, línea, cláusula de contrato).
   - Supervisión humana (1.2): "La IA propone con evidencia, la persona dispone".
   - Robustez y Calidad de Datos (1.4): Erradicación proactiva del Shadow IT y datos desactualizados.
4. **Revisión crítica (2026-10-11)** — la idea se mantiene, pero se corrige su planteamiento:
   - La resolución de entidades es N:M (aplicación ↔ repos ↔ contratos ↔ CIs) y se ancla primero en el catálogo existente (Excel/CMDB); "sin coincidencia" es un resultado válido (candidato huérfano / Shadow IT).
   - El puntaje es un *score* heurístico, no una probabilidad, hasta calibrarse contra un conjunto verificado; umbral único configurable.
   - "Reducción" (no "erradicación") del Shadow IT; el dueño técnico inferido de commits es solo una sugerencia.
   - Agentes 1 y 3 son procesos deterministas; el LLM solo se usa en el Agente 2 (texto no estructurado) y el Agente 4 (redacción de nudges).
   - Operación continua: precedencia de valores validados por humanos, tiempo límite y escalamiento de nudges, límite de frecuencia, aprobación por niveles de riesgo.
   - OCDE 2024: 1.2 incluye privacidad (Ley 29733 para correos de commits y firmantes de contratos); se agrega 1.5 (rendición de cuentas). Fuente: https://oecd.ai/en/ai-principles

## Alcance autorizado
- `odd/tasks/ia-descubrimiento-multiagente.md` (este archivo).
- `docs/arquitectura/diagramas/ia-descubrimiento.puml`, `ia-descubrimiento.svg`, `manifest.json`.
- `docs/arquitectura/ia-agentes.md` (actualización de arquitectura, casos de uso y diagrama).
- `docs/arquitectura/gobierno-datos.md` (alineación de procedencia de datos con los nuevos agentes).
- Revisión crítica (T5–T10): `docs/arquitectura/ia-agentes.md`, `gobierno-datos.md`, `arquitectura-solucion.md`, `roadmap.md`, `index.md`, `interfaz.md`, `diagramas/ia-descubrimiento.puml` (+ `.svg`, `manifest.json`).
- Sin código de aplicación. Todo el contenido y UI en español neutral/profesional.

## TDD
Desactivado (portal documental). Checks funcionales:
- `cd website && npm test`
- `cd website && npm run diagrams`
- `cd website && npm run diagrams:check`
- `cd website && npm run build`

## Estrategia de entrega
ask-on-risk. Commits con Trunk-Based Development directamente en `main` (decisión del usuario 2026-10-11); push a cargo del usuario.

## Tareas
- [x] T1 — Crear diagrama ArchiMate `ia-descubrimiento.puml` y compilar SVG/manifest con `npm run diagrams`.
- [x] T2 — Actualizar `docs/arquitectura/ia-agentes.md` estructurando el nuevo paradigma, los 4 agentes y el detalle bimodal (Código + Contratos).
- [x] T3 — Actualizar `docs/arquitectura/gobierno-datos.md` incorporando la trazabilidad de evidencia y procedencia de los agentes descubridores.
- [x] T4 — Ejecutar validaciones (`npm test`, `diagrams:check`, `build`) y verificar consistencia de enlaces y visualización.
- [x] T5 — Reformular la resolución de entidades como N:M anclada en el catálogo existente (Excel/CMDB), con resultado "sin coincidencia" → candidato huérfano; actualizar `ia-agentes.md` y el diagrama `ia-descubrimiento.puml` (render + manifest).
- [ ] T6 — Corregir afirmaciones en `ia-agentes.md`: *score* heurístico (no probabilidad) con calibración contra conjunto verificado, umbral único configurable, "reducción" del Shadow IT, dueño técnico inferido como sugerencia; indicar qué agentes son deterministas y cuáles usan LLM.
- [ ] T7 — Diseñar la operación continua en `ia-agentes.md` y `gobierno-datos.md`: precedencia frente a valores validados por humanos, tiempo límite y escalamiento de nudges, límite de frecuencia, aprobación por niveles de riesgo.
- [ ] T8 — Privacidad y rendición de cuentas: OCDE 1.2 (privacidad, Ley 29733) y 1.5 en `ia-agentes.md`; riesgos propios del descubrimiento en la tabla de riesgos de `arquitectura-solucion.md`.
- [ ] T9 — Alinear `roadmap.md`, `arquitectura/index.md` e `interfaz.md` (canal de micro-nudges) con el paradigma de descubrimiento.
- [ ] T10 — Validar (`npm test`, `diagrams:check`, `build`) y cerrar la idea.

## Progreso
- Creado y renderizado `docs/arquitectura/diagramas/ia-descubrimiento.puml` a SVG y PNG (15 diagramas al día en manifest).
- Documentación actualizada en `docs/arquitectura/ia-agentes.md` con topología multi-agente, foco dual (código + contratos) y gobernanza OCDE.
- Tablas de fuentes y procedencia por atributo actualizadas en `docs/arquitectura/gobierno-datos.md`.
- Verificaciones pasadas con éxito: `npm test` (1/1), `diagrams:check` (15/15 OK), `npm run build` (13 páginas generadas sin errores).

- Commit `7f68565` (T1–T4) en `main`, publicado en `origin/main`.
- Revisión crítica 2026-10-11: hallazgos convertidos en T5–T10 (documentación) y en tareas T8–T10 de `odd/tasks/mvp-descubrimiento.md` (código).
- T5: resolución N:M anclada en el catálogo y candidatos huérfanos en `ia-agentes.md` y `ia-descubrimiento.puml` (15 diagramas al día). Ruta: delegado.

## Siguiente paso
T5–T10 (ruta: delegado, un escritor; disparador: 6+ archivos de documentación no triviales).
