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

## Alcance autorizado
- `odd/tasks/ia-descubrimiento-multiagente.md` (este archivo).
- `docs/arquitectura/diagramas/ia-descubrimiento.puml`, `ia-descubrimiento.svg`, `manifest.json`.
- `docs/arquitectura/ia-agentes.md` (actualización de arquitectura, casos de uso y diagrama).
- `docs/arquitectura/gobierno-datos.md` (alineación de procedencia de datos con los nuevos agentes).
- Sin código de aplicación. Todo el contenido y UI en español neutral/profesional.

## TDD
Desactivado (portal documental). Checks funcionales:
- `cd website && npm test`
- `cd website && npm run diagrams`
- `cd website && npm run diagrams:check`
- `cd website && npm run build`

## Estrategia de entrega
ask-on-risk.

## Tareas
- [x] T1 — Crear diagrama ArchiMate `ia-descubrimiento.puml` y compilar SVG/manifest con `npm run diagrams`.
- [x] T2 — Actualizar `docs/arquitectura/ia-agentes.md` estructurando el nuevo paradigma, los 4 agentes y el detalle bimodal (Código + Contratos).
- [x] T3 — Actualizar `docs/arquitectura/gobierno-datos.md` incorporando la trazabilidad de evidencia y procedencia de los agentes descubridores.
- [x] T4 — Ejecutar validaciones (`npm test`, `diagrams:check`, `build`) y verificar consistencia de enlaces y visualización.

## Progreso
- Creado y renderizado `docs/arquitectura/diagramas/ia-descubrimiento.puml` a SVG y PNG (15 diagramas al día en manifest).
- Documentación actualizada en `docs/arquitectura/ia-agentes.md` con topología multi-agente, foco dual (código + contratos) y gobernanza OCDE.
- Tablas de fuentes y procedencia por atributo actualizadas en `docs/arquitectura/gobierno-datos.md`.
- Verificaciones pasadas con éxito: `npm test` (1/1), `diagrams:check` (15/15 OK), `npm run build` (13 páginas generadas sin errores).

## Siguiente paso
Presentar propuesta consolidada al usuario para su sustentación.
