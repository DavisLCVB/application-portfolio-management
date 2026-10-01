# Modelo de datos del APM (LeanIX Meta Model v4 + ArchiMate)

## Objetivo
Definir el esquema de datos del APM inspirado en el SAP LeanIX Meta Model v4 y expresado en ArchiMate 3.2, publicado en el portal.

## Problema / por qué
`docs/arquitectura/catalogos.md` lista catálogos y campos orientativos, pero no hay un modelo de entidades, relaciones ni aspectos transversales (procedencia por atributo, fuente autoritativa, ciclo de vida). Los catálogos viven en sistemas externos: el APM es registro maestro híbrido + integrador.

## Decisiones aceptadas
- Metamodelo base: LeanIX Meta Model v4 (elegido por el usuario, 2026-09-24).
- Notación: ArchiMate 3.2 (PlantUML `<archimate/Archimate>`), consistente con los diagramas existentes.
- Estrategia de datos: híbrida — registro maestro propio + ingesta/reconciliación con fuente autoritativa y procedencia por atributo.
- Artefactos en español (convención del proyecto).

## Fuentes actuales (usuario, 2026-09-24)
- Catálogos (aplicaciones, integraciones, tecnologías): Excel.
- Infraestructura: CMDB (producto por confirmar).

## Decisiones de gobierno (usuario, 2026-09-24)
- El APM reemplaza al Excel: importación inicial única con reconciliación; luego el APM es registro maestro.
- Registro descentralizado (los equipos registran/editan) con aprobación de Gobierno de Arquitectura.

## Alcance autorizado
Documentación en `docs/arquitectura/`, diagramas `.puml`/`.svg`/`manifest.json`, sidebar en `website/astro.config.mjs`. Sin código de aplicación.

## TDD
Desactivado (repo documental, sin configuración TDD). Checks funcionales: `npm test`, `npm run diagrams:check`, `npm run build` (en `website/`).

## Estrategia de entrega
ask-on-risk. Rama: `docs/modelo-datos`.

## Tareas
- [x] T1 — Metamodelo conceptual: página `modelo-datos.md`, diagrama ArchiMate `metamodelo.puml` (tipos de Fact Sheet → elementos ArchiMate, relaciones), sidebar, regenerar SVG + manifest. Ruta: delegado (writer, 2+ archivos no triviales).
- [x] T2 — Atributos por entidad (en `modelo-datos.md`): atributos base comunes, atributos por tipo, escalas (criticidad, fit, TIME, ciclo de vida), clasificación de atributos (gobernado / operativo / ingerido); conectar Value Stream y Business Product en el diagrama. Ruta: delegado (writer).
- [x] T3 — Gobierno y procedencia de datos (`gobierno-datos.md` + diagrama ArchiMate del flujo): fuentes y autoridad (APM, CMDB, feeds), procedencia por atributo, flujo de registro descentralizado con aprobación de Gobierno de Arquitectura, migración única del Excel, identidad y reconciliación. Ruta: delegado (mismo writer).
- [ ] T4 — Modelo lógico/físico (almacenamiento relacional/grafo/híbrido). Pendiente de decisión del usuario.

## Progreso
- Investigación LeanIX v4: parcial (docs SAP renderizadas con JS). Verificado: ciclo de vida, TIME, Quality Seal, completion score, subtipos de Business Context e Initiative. Sin mapeo oficial LeanIX→ArchiMate (mapeo propio). Pendiente: lista completa de tipos/subtipos y escalas de criticidad/fit.
- T1 (delegado): checks `npm run diagrams` OK (6), `diagrams:check` OK, `npm test` 1/1, `npm run build` 11 páginas. Relación Flow interfaz→consumidora marcada "por validar". Value Stream y Business Product aún sin relaciones en el diagrama.

- T2 y T3 (delegado, revisado por el orquestador 2026-10-01): corregida la justificación de Serving (relación de dependencia, no estructural) y el lema "la persona dispone". Checks: `npm test` 1/1, `diagrams:check` 7 al día, `npm run build` 12 páginas. Commits: ver git log (`docs: atributos…`, `docs: gobierno…`).

## Siguiente paso
T4 — modelo lógico/físico: requiere decisión del usuario sobre almacenamiento (relacional / grafo / híbrido).
