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
- [ ] T10 — Renombrar "probabilidad" a *score*, umbral único configurable compartido por reconciliador y generador de nudges; dueño técnico inferido marcado como sugerencia.

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

## Siguiente paso
Pipeline multimodal MVP 1 listo para integración continua y pruebas en staging.
