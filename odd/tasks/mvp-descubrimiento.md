# MVP 1: Pipeline de Descubrimiento Continuo y Reconciliación

## Objetivo
Implementar una versión mínima viable (MVP 1) funcional y ejecutable en Python del sistema multi-agente de descubrimiento continuo, demostrando de punta a punta la extracción técnica (código), minería documental (contratos/TDRs), reconciliación semántica y generación de micro-nudges.

## Alcance del MVP 1
1. **Módulo 1: Code-to-Catalog (`code_to_catalog.py`)**
   - Escaneo estático de repositorios locales o carpetas de proyecto.
   - Detección de stacks y dependencias desde `pom.xml`, `package.json`, `Dockerfile`.
   - Extracción de autor/equipo principal vía `git log`.
   - Salida: `EvidenciaTecnica` estructurada con citas primarias (`archivo:linea` y hash de commit).

2. **Módulo 2: Dark Data Miner (`contract_miner.py`)**
   - Procesamiento de especificaciones contractuales y TDRs (archivos de texto/Markdown/PDF estructurados).
   - Extracción guiada de: proveedor adjudicado, vigencia contractual, SLAs comprometidos y licencias.
   - Salida: `EvidenciaContractual` estructurada con citas primarias (`documento:clausula`).

3. **Módulo 3: Reconciliador Semántico (`reconciliator.py`)**
   - Cruce y desambiguación léxico-semántica entre nombres técnicos y descripciones contractuales (usando `difflib.SequenceMatcher` / similitud difusa).
   - Cálculo de puntaje de confianza ponderado ($0.0$ a $1.0$).
   - Salida: `HipotesisFactSheet` candidata al metamodelo LeanIX v4.

4. **Módulo 4: Micro-Nudge Generator (`nudge_generator.py`)**
   - Evaluación contra umbral de gobernanza (ej. confianza $< 0.85$ o campos vacíos).
   - Generación de solicitud contextual interactiva (formato Adaptive Card / Markdown para Teams/Slack) con opciones de validación en 1 clic.

5. **Fixtures y Runner CLI (`run_discovery.py`)**
   - Casos de prueba reales: 2 repositorios de muestra (`repo-recaudacion`, `repo-portal-ciudadano`) y 2 contratos TDR.
   - Ejecución completa sin dependencias externas obligatorias (Python 3.10+ estándar).
   - Pruebas unitarias automatizadas (`python3 -m unittest`).

## Tareas
- [x] T1 — Diseñar modelos de datos canónicos (`models.py`) para evidencias, hipótesis y Fact Sheets.
- [x] T2 — Implementar el extractor técnico `code_to_catalog.py` con soporte para Java (Maven), Node.js (npm) y Docker.
- [x] T3 — Implementar el extractor documental `contract_miner.py` con reglas de extracción estructurada de TDRs.
- [x] T4 — Implementar el motor de reconciliación semántica y scoring `reconciliator.py`.
- [x] T5 — Implementar el generador de micro-nudges `nudge_generator.py`.
- [x] T6 — Crear fixtures de prueba y script orquestador `run_discovery.py` con pruebas unitarias (`test_pipeline.py`).
- [x] T7 — Implementar la Capa de Conectores Federados Multimodales (`src/connectors/`), modelo `EvidenciaDiagrama`, conectores (.csv, .xlsx, .pptx, .puml, .archimate, .drawio), registro federado (`ConnectorRegistry`) y pruebas unitarias (`test_connectors.py`).
- [x] T8 — Reconciliación N:M con resultado "sin coincidencia": reemplazar el emparejamiento codicioso de `SemanticReconciliator.match_all` (siempre asigna un contrato) por emparejamiento con umbral mínimo y reporte de huérfanos.
- [x] T9 — Anclar la reconciliación en el catálogo existente (`fixtures/catalogs/catalogo_aplicaciones.csv`) antes de cruzar código y contratos.
- [x] T10 — Renombrar "probabilidad" a *score*, umbral único configurable compartido por reconciliador y generador de nudges; dueño técnico inferido marcado como sugerencia.
- [x] T11 — Resultado "Conflicto": evidencia cuyo mejor y segundo mejor *score* contra apps del catálogo superan el mínimo de vinculación y difieren menos que un margen configurable no se asigna a ninguna hipótesis; se reporta en una cola de revisión humana con las apps candidatas y sus *scores* (alineado con `ia-agentes.md` y `gobierno-datos.md`).
- [x] T12 — Contratos multi-aplicación: un contrato se vincula a todas las apps del catálogo con *score* ≥ mínimo (un TDR de mantenimiento puede cubrir varias) y se marca como multi-aplicación; la regla de conflicto aplica solo a repos. Las apps candidatas de un conflicto no se listan como "sin evidencia".

## Progreso
- **Completado T1**: Implementadas dataclasses canónicas `EvidenciaTecnica`, `EvidenciaContractual`, `HipotesisFactSheet` y `MicroNudge` con serialización `to_dict()` y soporte para LeanIX v4 y principios OCDE 1.2 y 1.3.
- **Completado T2**: Implementado `CodeToCatalogExtractor` con soporte para `pom.xml` (Maven, dependencias, versión Java), `package.json` (Node.js/TypeScript), `Dockerfile` (imágenes base), escaneo de endpoints REST (Spring y Express) y metadatos de Git con citas de archivo:línea.
- **Completado T3**: Implementado `ContractMiner` con regex estructurado para extracción de identificadores TDR, proveedores adjudicados, SLAs de uptime, vigencia contractual y licencias, asociando citas primarias por cláusula.
- **Completado T4**: Implementado `SemanticReconciliator` con algoritmo probabilístico de scoring (50% similitud nominal difusa con `difflib.SequenceMatcher` y Jaccard, 35% congruencia técnica, 15% dominio) y generación de `HipotesisFactSheet`.
- **Completado T5**: Implementado `NudgeGenerator` con evaluación de umbral (< 0.85) y atributos faltantes, generando micro-solicitudes en formato Microsoft Adaptive Card v1.4 con acciones en 1 clic.
- **Completado T6**: Creados fixtures completos (`repo-recaudacion`, `repo-portal-atencion`, `tdr-recaudacion-digital.md`, `tdr-portal-ciudadano.md`), script orquestador CLI `run_discovery.py` y suite completa de pruebas unitarias (`test_pipeline.py`).
- **Completado T7**: Implementada Capa de Conectores Federados Multimodales en `mvp/src/connectors/`:
  - `BaseConnector` (`base.py`) con interfaz estándar `can_handle` y `extract`.
  - Dataclass `EvidenciaDiagrama` en `models.py` para representación canónica de componentes, relaciones y citas.
  - `SpreadsheetConnector` (`spreadsheet_connector.py`) para `.csv` y `.xlsx` (OpenXML con `zipfile` + `ElementTree`).
  - `PresentationConnector` (`presentation_connector.py`) para `.pptx` (extracción de sistemas, stacks y notas por slide/shape).
  - `DiagramConnector` (`diagram_connector.py`) para PlantUML (.puml), Archi XML (.archimate, .xml) y draw.io (.drawio, .xml).
  - `ConnectorRegistry` (`registry.py`) con soporte de auto-detección y `scan_directory` recursivo.
  - Fixtures multimodales en `mvp/fixtures/diagrams/` y `mvp/fixtures/catalogs/`.
  - Pruebas unitarias exhaustivas en `mvp/tests/test_connectors.py` (100% biblioteca estándar).
  - Orquestador `run_discovery.py` actualizado con soporte `--dir`, particionamiento de evidencias y tabla resumen de diagramas.
- Creado y actualizado `mvp/README.md` documentando la arquitectura multimodal, conectores, principios de gobernanza OCDE y guía de ejecución.
- **Completado T8** (ruta: delegado): `SemanticReconciliator.match_all` vincula N:M todo par con score ≥ `config.MIN_LINK_SCORE` (0.5, menor que el umbral de revisión) y devuelve `ResultadoReconciliacion` con `links` y `orphans` (`CandidatoHuerfano`); ya no fuerza la mejor coincidencia. RED: `tests/test_reconciliation.py` (6 pruebas, p. ej. `test_unrelated_repo_is_orphan_not_forced`). Se actualizó `test_match_all_pairs_correctly` (asumía la lista de tuplas del emparejamiento forzado). Checks: `uv run python -m unittest discover -s tests` → 35 OK; `run_discovery.py --dir fixtures/` → 2 vínculos, 3 huérfanos.
- **Completado T9** (ruta: delegado): `load_catalog` (reutiliza los lectores del `SpreadsheetConnector`) y `SemanticReconciliator.reconcile_with_catalog` anclan la evidencia en el catálogo: hipótesis = aplicación del catálogo + repos + contratos vinculados (N:M, contratos también vía repo anclado, score = vínculo más débil); lo que no coincide con el catálogo es `CandidatoHuerfano` con evidencias relacionadas. Se agregó la columna `Alias` al CSV (APP-001 ↔ recaudación); el portal queda huérfano. `run_discovery.py` muestra hipótesis ancladas, huérfanos y apps sin evidencia; acepta `--catalog`; en `--dir` los catálogos tabulares ya no se tratan como evidencia técnica. RED: `TestCatalogAnchoring` (falla en `setUpClass`, sin `load_catalog`). Se actualizó `test_full_pipeline_execution` (asumía 2 hipótesis forzadas y JSON en lista). Checks: unittest → 41 OK; `run_discovery.py --dir fixtures/` → 1 hipótesis anclada (APP-001), 2 huérfanos.
- **Completado T10** (ruta: delegado): `config.REVIEW_THRESHOLD` (0.85) es el umbral único que comparten `SemanticReconciliator` y `NudgeGenerator` (parámetro `review_threshold`, sin literales duplicados; `run_discovery.py --umbral`). Se reemplazó "probabilístico" por *score* heurístico en código, CLI y README. `HipotesisFactSheet.technical_owner_suggested` marca el dueño inferido de commits (el del catálogo prevalece) y siempre genera un nudge de confirmación "(sugerido)". RED: `TestScoreTerminologyAndThreshold` (5 pruebas, p. ej. `test_no_probability_terminology`, `test_commit_inferred_owner_is_a_suggestion_with_confirmation_nudge`). Se cambió el kwarg `confidence_threshold` → `review_threshold` en `test_pipeline.py`. Checks: unittest → 46 OK; `run_discovery.py --dir fixtures/` → exit 0, 1 hipótesis anclada, 2 huérfanos. Commit `f41d177`.
- **Completado T11** (ruta: delegado): `config.AMBIGUITY_MARGIN` (0.05, `run_discovery.py --margen-conflicto`). En `reconcile_with_catalog`, cada repositorio y contrato se puntúa contra todas las apps; si el mejor y el segundo score superan `MIN_LINK_SCORE` y difieren menos que el margen, se registra un `ConflictoReconciliacion` (tipo, identidad, apps candidatas con código/nombre/score en orden descendente, citas, motivo): no se adjunta a ninguna hipótesis ni es huérfano. Un contrato no se ancla a través de un repositorio en conflicto. Con ganador claro, la evidencia se ancla solo a la app de mayor score (antes se vinculaba a toda app ≥ mínimo). `ResultadoReconciliacion.conflicts`, JSON `conflicts` y sección "Cola de revisión (conflictos)" en la CLI; sin micro-nudges al equipo técnico (decide un arquitecto). Los fixtures no producen conflictos. RED: `TestConflictResult` (6 pruebas: `test_ambiguous_evidence_is_conflict_not_hypothesis_nor_orphan`, `test_clear_winner_beyond_margin_is_anchored`, `test_ambiguity_margin_is_configurable`, `test_contract_is_not_anchored_through_conflicted_repo`, `test_pipeline_reports_conflicts_without_developer_nudges`, `test_fixtures_have_no_conflicts`; 3 FAIL + 3 ERROR). Checks: unittest → 52 OK; `run_discovery.py --dir fixtures/` → exit 0, 1 hipótesis anclada, 2 huérfanos, 0 conflictos. Commit: `0d36f28`.
- **Completado T12** (ruta: delegado): decisión del usuario. Los repositorios mantienen el anclaje a la app de mayor *score* y la regla de conflicto. Los contratos ya no pasan por la regla de conflicto: se vinculan a toda app del catálogo con *score* ≥ `MIN_LINK_SCORE` (directo o a través de un repositorio anclado, nunca uno en conflicto); si cubren 2+ apps, `HipotesisFactSheet.multi_application_contracts` (contrato → códigos de apps) lo señala en `to_dict()`/JSON y la CLI muestra un aviso "Contrato multi-aplicación". `catalog_without_evidence` excluye las apps candidatas de un conflicto. Ninguna prueba de T11 afirmaba conflictos de contrato, así que no se modificó ninguna. RED: `TestMultiApplicationContract.test_contract_links_to_every_matching_application_without_conflict` (FAIL), `TestMultiApplicationContract.test_single_application_contract_is_not_flagged` (ERROR), `TestConflictResult.test_conflict_candidates_are_not_catalog_without_evidence` (FAIL). Checks: unittest → 55 OK; `run_discovery.py --dir fixtures/` → exit 0, 1 hipótesis anclada, 2 huérfanos, 0 conflictos.

## Siguiente paso
T8–T12 completas. Siguiente: definir con el usuario la próxima tarea (p. ej. flujo de resolución de conflictos por el arquitecto).
