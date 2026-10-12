# MVP 1: Pipeline de Descubrimiento Continuo y Reconciliación Semántica

Este módulo implementa el prototipo ejecutable (**MVP 1**) del sistema multi-agente de descubrimiento continuo para la plataforma de Gestión de Portafolio de Aplicaciones (**APM**), diseñado para organizaciones complejas y entidades del sector público (como el Ministerio de Economía y Finanzas - MEF).

---

## 1. El cambio de paradigma: De "bombero downstream" a motor upstream

Tradicionalmente, la IA en Enterprise Architecture y APM se concibe de manera reactiva: asume que el inventario de software ya está completo, limpio y actualizado en una base de datos central, limitándose a responder consultas de chat, correlacionar vulnerabilidades CVE o calcular métricas de obsolescencia.

En la realidad operativa:
- El levantamiento manual de inventarios falla sistemáticamente por **fatiga burocrática**.
- Los desarrolladores rechazan llenar formularios extensos de 40+ campos en herramientas ajenas a su flujo.
- Existe una proliferación invisible de **Shadow IT** y dispersión de información crítica en documentos aislados (*Dark Data*).

**La solución del APM**: Transformar la IA en un **motor proactivo de descubrimiento upstream**, donde agentes especializados inspeccionan continuamente la realidad técnica (repositorios, Dockerfiles, dependencias) y documental (TDRs, contratos de soporte, órdenes de compra), unificando ambas verdades en **Fact Sheets preliminares** con trazabilidad estricta hacia fuentes primarias.

```
[ Fuentes Técnicas: Git / CI-CD / Docker ]        [ Dark Data: Contratos / TDRs ]
                 │                                               │
                 ▼                                               ▼
     ┌───────────────────────┐                       ┌───────────────────────┐
     │ Agente 1:             │                       │ Agente 2:             │
     │ Code-to-Catalog       │                       │ Dark Data Miner       │
     └───────────┬───────────┘                       └───────────┬───────────┘
                 │                                               │
         [Evidencia Técnica]                         [Evidencia Contractual]
                 │                                               │
                 └───────────────────┐   ┌───────────────────────┘
                                     ▼   ▼
                          ┌───────────────────────────┐
                          │ Agente 3:                 │
                          │ Reconciliador Semántico   │
                          └─────────────┬─────────────┘
                                        │
                            [Hipótesis Conciliada +
                             Score heurístico]
                                        │
                     ¿Score < umbral de revisión o vacíos?
                                  ┌─────┴─────┐
                             Sí   │           │   No (score ≥ umbral)
                                  ▼           │
                    ┌───────────────────┐     │
                    │ Agente 4:         │     │
                    │ Micro-Nudge       │     │
                    └─────────┬─────────┘     │
                              │               │
                     [Micro-solicitud]        │
                              ▼               │
                    (Dueño técnico / Dev)     │
                              │ (1 clic)      │
                              └───────┬───────┘
                                      ▼
                        [Fact Sheet Enriquecido]
                         (con citas primarias)
                                      │
                                      ▼
                        (Arquitecto TI / Gobierno)
                                      │ (Aprobación)
                                      ▼
                             [Catálogo APM]
```

---

## 2. Los cuatro agentes del pipeline

### Agente 1: Code-to-Catalog (`src/code_to_catalog.py`)
- **Responsabilidad**: Inspecciona repositorios locales o remotos, detectando artefactos de construcción (`pom.xml`, `package.json`, `Dockerfile`), rutas de endpoints REST y metadatos de Git.
- **Salida**: Objeto `EvidenciaTecnica` con stack de runtime, dependencias de librerías, endpoints detectados y citas primarias de tipo `archivo:línea` (`pom.xml#L18`, `Dockerfile#L1`).

### Agente 2: Dark Data Miner (`src/contract_miner.py`)
- **Responsabilidad**: Procesa documentos no estructurados y contractuales (TDRs, contratos de mantenimiento, bases técnicas) usando expresiones regulares estructuradas y análisis de cláusulas.
- **Salida**: Objeto `EvidenciaContractual` que captura el proveedor adjudicado, vigencia contractual, SLA de uptime mensual y licenciamiento homologado, con citas primarias de tipo `documento#cláusula (línea)`.

### Agente 3: Reconciliador Semántico (`src/reconciliator.py`)
- **Responsabilidad**: Realiza *Entity Resolution* entre la jerga técnica (`recaudacion-digital-service`) y la terminología legal/administrativa (*"Pasarela de Recaudación Digital de Ingresos Públicos"*).
- **Ancla en el catálogo existente**: primero carga el catálogo de aplicaciones (`fixtures/catalogs/catalogo_aplicaciones.csv`, columnas de código, nombre y alias) y adjunta a cada aplicación los repositorios y contratos que la referencian. Una hipótesis es *aplicación del catálogo + repositorios vinculados + contratos vinculados*.
- **Relación N:M**: un contrato puede cubrir varios repositorios y un repositorio varios contratos; se vincula todo par con score ≥ `MIN_LINK_SCORE` (`src/config.py`, 0.5). Cada evidencia se ancla a la aplicación del catálogo con mayor score (si supera el mínimo); un contrato también se vincula a la aplicación a través de un repositorio ya anclado.
- **Conflicto**: si el mejor y el segundo mejor score de una evidencia contra aplicaciones del catálogo superan `MIN_LINK_SCORE` y difieren menos que `AMBIGUITY_MARGIN` (`src/config.py`, 0.05, configurable con `--margen-conflicto`), la evidencia no discrimina entre ellas: no se adjunta a ninguna hipótesis ni se reporta como huérfana. Se registra como `ConflictoReconciliacion` en la **cola de revisión humana** con las aplicaciones candidatas y sus scores, y un arquitecto decide (nunca se resuelve automáticamente ni genera micro-nudges al equipo técnico). Un contrato no se ancla a través de un repositorio en conflicto.
- **"Sin coincidencia" es un resultado válido**: la evidencia que no alcanza el score mínimo con ninguna aplicación del catálogo se reporta como **candidato huérfano** (posible Shadow IT) para revisión humana, junto con las otras evidencias huérfanas con las que se relaciona. Nunca se fuerza una vinculación.
- **Score heurístico de confianza** (no está calibrado contra un conjunto verificado, por lo que no debe leerse como certeza estadística):
  $$\text{Score} = (0.50 \times \text{Similitud Nominal}) + (0.35 \times \text{Congruencia Técnica}) + (0.15 \times \text{Consistencia de Dominio})$$
  - *Similitud nominal*: Fusión de Jaccard sobre bolsa de tokens significativos y `difflib.SequenceMatcher`.
  - *Congruencia técnica*: Grado de coincidencia entre tecnologías requeridas por contrato y dependencias reales del código.
  - *Consistencia de dominio*: Alineación de rutas de endpoints y nombres funcionales.
- **Umbral único de revisión**: `REVIEW_THRESHOLD` en `src/config.py` (por defecto $0.85$, configurable con `--umbral`) lo comparten el reconciliador y el generador de micro-nudges; no hay valores duplicados.
- **Salida**: `HipotesisFactSheet` con estado (`Draft` si score $\ge$ umbral, de lo contrario `Requires_Verification`).

### Agente 4: Micro-Nudge Generator (`src/nudge_generator.py`)
- **Responsabilidad**: Si el score es menor al umbral único de revisión, faltan atributos mandatarios (como el *Dueño de Negocio*) o el *Dueño Técnico* solo fue inferido de los commits, genera solicitudes contextuales en formato **Microsoft Adaptive Card v1.4** para Teams o Slack.
- **Interacción**: Diseñado para resolverse en 1 clic ("Confirmar asociación", "Confirmar rol técnico"), eliminando la resistencia humana.

---

## 3. Alineación con el Meta-modelo LeanIX v4

Los objetos generados mapean directamente a los tipos fundamentales de LeanIX v4:
- **Application**: Entidad de negocio central (`entity_name`, ej. *"Pasarela de Recaudación Digital de Ingresos Públicos"*).
- **ITComponent / Tech Stack**: Runtimes y bibliotecas detectadas (`Java 17`, `Spring Boot`, `Node.js 20`, `PostgreSQL`).
- **Provider**: Empresa contratista adjudicada vinculada al Fact Sheet (`Indra Soluciones`, `Stefanini IT`).
- **Service Level Agreements**: Disponibilidad contractual comprometida (`sla_uptime`: `99.9%`, `99.5%`).
- **Ownership**: el dueño técnico registrado en el catálogo prevalece; el inferido de los commits se marca como sugerencia (`technical_owner_suggested`) y siempre genera un micro-nudge de confirmación. Se solicita además el dueño funcional.

---

## 4. Alineación con los Principios de Gobernanza de IA de la OCDE

1. **Principio 1.2 — Supervisión humana y valores centrados en las personas**:
   - *La IA propone con evidencia, la persona dispone*: Ningún agente publica directamente en el catálogo de producción.
   - El desarrollador valida o ajusta en 1 clic mediante Micro-Nudges.
   - El arquitecto de gobierno autoriza el Fact Sheet final consolidado.
2. **Principio 1.3 — Transparencia y Explicabilidad**:
   - Cada dato propuesto incluye citas primarias directas: `pom.xml#L18`, `tdr-recaudacion-digital.md#Cláusula 4 (L18)`.
   - Cero alucinaciones: Si un dato no tiene evidencia textual o técnica, se marca como vacío y se solicita aclaración.
3. **Principio 1.4 — Robustez y Seguridad**:
   - Ejecución autónoma en entorno cerrado (Sandbox) utilizando únicamente la biblioteca estándar de Python 3.
   - Un umbral único de revisión sobre el score heurístico impide la incorporación desatendida de datos ambiguos.

---

## 5. Estructura del proyecto

```text
mvp/
├── README.md                           # Documentación técnica y conceptual
├── run_discovery.py                   # Orquestador y runner CLI end-to-end
├── src/
│   ├── __init__.py
│   ├── config.py                      # Umbral único de revisión y score mínimo de vínculo
│   ├── models.py                      # Dataclasses canónicas (Evidencias, Hipótesis, Nudges)
│   ├── code_to_catalog.py             # Agente 1: Extractor de código y repositorios
│   ├── contract_miner.py              # Agente 2: Minero de TDRs y contratos
│   ├── reconciliator.py               # Agente 3: Reconciliador semántico y scoring
│   └── nudge_generator.py             # Agente 4: Generador de Adaptive Cards interactivas
├── fixtures/                          # Casos de prueba reales
│   ├── repo-recaudacion/              # Proyecto Java 17 + Spring Boot + Postgres
│   │   ├── pom.xml
│   │   ├── Dockerfile
│   │   └── src/main/java/.../RecaudacionController.java
│   ├── repo-portal-atencion/          # Proyecto Node.js 20 + Express + Next.js
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   └── src/routes/atencion.js
│   ├── catalogs/
│   │   └── catalogo_aplicaciones.csv  # Catálogo existente (ancla de identidad, con alias)
│   └── contracts/
│       ├── tdr-recaudacion-digital.md # TDR Indra Soluciones, SLA 99.9%
│       └── tdr-portal-ciudadano.md    # TDR Stefanini IT, SLA 99.5% (sin app en el catálogo: huérfano)
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py               # Suite completa de pruebas unitarias
│   └── test_reconciliation.py         # Reconciliación N:M, anclaje en catálogo y umbral único
└── output/
    └── fact_sheets_draft.json         # Artefacto consolidado exportado
```

---

---

## 6. Capa de Conectores Federados Multimodales (`src/connectors/`)

Para extender la cobertura más allá del código Git y los TDRs Markdown, el sistema implementa una **Capa Federada Multimodal** que ingesta artefactos de arquitectura dispersos (*Dark Data* organizacional) sin dependencias externas:

```
                          ┌───────────────────────────┐
                          │     ConnectorRegistry     │
                          └─────────────┬─────────────┘
                                        │
     ┌──────────────────┬───────────────┼───────────────┬──────────────────┐
     ▼                  ▼               ▼               ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────┐ ┌───────────────────┐
│ Spreadsheet  │ │ Presentation │ │  Diagram  │ │CodeToCatalog │ │   ContractMiner   │
│  Connector   │ │  Connector   │ │ Connector │ │  Connector   │ │     Connector     │
└──────┬───────┘ └──────┬───────┘ └─────┬─────┘ └──────┬───────┘ └─────────┬─────────┘
       │                │               │              │                   │
   .csv/.xlsx         .pptx       .puml/.drawio/   Git / Docker       .md / .txt (TDR)
                                  .archimate/.xml
       │                │               │              │                   │
       └────────────────┴───────────────┼──────────────┴───────────────────┘
                                        ▼
                   [EvidenciaTecnica | EvidenciaContractual | EvidenciaDiagrama]
```

### Conectores Disponibles:
1. **`SpreadsheetConnector`**:
   - Ingesta inventarios y catálogos en `.csv` y `.xlsx` (OpenXML nativo mediante `zipfile` y `xml.etree.ElementTree`).
   - Normaliza encabezados para identificar columnas de aplicación, stack, responsable, SLA y proveedor.
   - Genera citas canónicas de celda/fila (ej. `catalogo.xlsx#Sheet1!R12`).
2. **`PresentationConnector`**:
   - Ingesta presentaciones ejecutivas y diapositivas de arquitectura en `.pptx`.
   - Inspecciona `ppt/slides/slide*.xml` extrayendo bloques de texto, nombres de componentes y notas de orador.
   - Genera citas canónicas de forma (ej. `presentacion.pptx#Slide3!Shape4`).
3. **`DiagramConnector`**:
   - Ingesta diagramas en 3 formatos estándar:
     - **PlantUML (`.puml`)**: Macros ArchiMate 3.2 (`Application_Component`, `Rel_Flow`, `Rel_Serving`), C4 y componentes estándar con numeración de línea.
     - **Archi XML / Open Exchange (`.archimate`, `.xml`)**: Modelos ArchiMate oficiales de The Open Group, resolviendo componentes y topología de relaciones.
     - **draw.io XML (`.drawio`, `.xml`)**: Esquemas `mxGraphModel`, decodificando celdas `mxCell`, resolviendo aristas y conectores origen-destino.
   - Genera instancias estructuradas de `EvidenciaDiagrama`.
4. **`ConnectorRegistry`**:
   - Registro federado central que auto-detecta el conector adecuado para cualquier archivo o recorre recursivamente directorios completos (`scan_directory`), aislando repositorios enteros y agrupando evidencias (`partition_evidences`).

---

## 7. Ejecución del pipeline y pruebas

### Requisitos
- Python 3.10 o superior (Solo requiere biblioteca estándar: `zipfile`, `xml.etree.ElementTree`, `json`, `re`, `pathlib`, `difflib`, `dataclasses`, `unittest`).
- Cero dependencias externas (`pip install` no requerido).

### Ejecución con uv (Recomendado para reproducibilidad hermética)
```bash
cd mvp
# Flujo estándar de descubrimiento (fixtures canónicos)
uv run python run_discovery.py

# Mismo flujo con otro umbral único de revisión
uv run python run_discovery.py --umbral 0.75

# Margen de conflicto más amplio (más evidencia va a la cola de revisión)
uv run python run_discovery.py --margen-conflicto 0.10

# Escaneo multimodal federado sobre un directorio completo
uv run python run_discovery.py --dir fixtures/

# Escaneo federado cruzando fuentes reales y sintéticas, anclado en un catálogo
uv run python run_discovery.py \
  --repos /home/davis/Dev \
  --contracts contratos_generados \
  --diagrams fixtures/diagrams \
  --catalog fixtures/catalogs/catalogo_aplicaciones.csv

# Pruebas unitarias completas (100% biblioteca estándar)
uv run python -m unittest discover -s tests -v
```

### Ejecución alternativa con Python estándar (sin uv)
```bash
python3 mvp/run_discovery.py
python3 mvp/run_discovery.py --dir mvp/fixtures/
python3 -m unittest discover -s mvp/tests -v
```

---

## 8. Formato de salida (`output/`)

El pipeline genera dos artefactos principales de gobernanza:

1. **`output/fact_sheets_draft.json`**:
   Contiene las hipótesis ancladas en el catálogo (con trazabilidad estricta y micro-nudges), los candidatos huérfanos, los conflictos para revisión humana y las aplicaciones del catálogo sin evidencia nueva:
```json
{
  "hypotheses": [
  {
    "fact_sheet": {
      "entity_name": "Sistema Integrado de Tesorería",
      "catalog_id": "APP-001",
      "linked_repos": ["recaudacion-digital-service"],
      "linked_contracts": ["TDR-2024-MEF-0089"],
      "candidate_type": "Application",
      "technical_stack": "Java (Java 17)",
      "provider": "Indra Soluciones Tecnologías de la Información S.L.U.",
      "sla_uptime": "99.9%",
      "confidence_score": 0.753,
      "status": "Requires_Verification",
      "primary_citations": [
        {
          "source": "repository_code",
          "entity": "recaudacion-digital-service",
          "commit": "c4b3a1f9e201",
          "attribute": "runtime_version",
          "citation": "pom.xml#L17"
        },
        {
          "source": "contract_dark_data",
          "doc_id": "TDR-2024-MEF-0089",
          "attribute": "sla_uptime",
          "citation": "tdr-recaudacion-digital.md#Cláusula 4 (L18)"
        }
      ]
    },
    "micro_nudges": [ ... ]
  }
  ],
  "orphan_candidates": [
    {
      "evidence_type": "repositorio",
      "name": "portal-atencion-ciudadano",
      "best_score": 0.306,
      "reason": "Sin coincidencia con ninguna aplicación del catálogo (posible Shadow IT).",
      "related": ["TDR-2023-MEF-0145"]
    }
  ],
  "conflicts": [],
  "catalog_without_evidence": ["APP-002", "APP-003"]
}
```

2. **`output/diagram_evidences.json`**:
   Contiene las evidencias arquitectónicas extraídas de diagramas y modelos técnicos:
```json
[
  {
    "source_file": "arquitectura_drawio.xml",
    "format_type": "draw.io",
    "components": [
      "Base de Datos de Transacciones",
      "Pasarela de Pagos Digitales",
      "Portal del Contribuyente",
      "Servicio de Autenticación Central"
    ],
    "relations": [
      {
        "source": "Portal del Contribuyente",
        "target": "Pasarela de Pagos Digitales",
        "relation_type": "Inicia transacción de pago"
      }
    ],
    "citations": {
      "arquitectura_drawio.xml#cell/node-portal": "Componente: Portal del Contribuyente"
    }
  }
]
```
