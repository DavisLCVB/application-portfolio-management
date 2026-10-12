---
title: IA agéntica y funcionalidades
description: Capacidades de IA agéntica del APM, pipeline multi-agente de descubrimiento continuo upstream y gobernanza OCDE.
---

## De "bombero downstream" a motor de descubrimiento upstream

Tradicionalmente, la inteligencia artificial en la gestión de portafolio de aplicaciones se ha concebido como un consumidor pasivo o "bombero downstream": asume que el catálogo ya existe, está limpio y actualizado, limitándose a responder consultas de chat, correlacionar CVEs o calcular obsolescencia sobre datos preexistentes.

En organizaciones de alta complejidad y sector público (como el MEF), la realidad es que el catálogo manual falla por fatiga burocrática, falta de incentivos y dispersión de información. El verdadero cuello de botella es la captura y unificación de datos. La arquitectura del APM evoluciona hacia un **motor proactivo de descubrimiento continuo upstream**, donde un sistema multi-agente escanea activamente la realidad técnica y contractual para construir y mantener al día los Fact Sheets con mínima intervención humana.

![Pipeline multi-agente de descubrimiento y reconciliación](./diagramas/ia-descubrimiento.svg)

---

## Topología del pipeline multi-agente de descubrimiento

El pipeline opera mediante cuatro agentes especializados que colaboran para pasar de datos crudos fragmentados a Fact Sheets gobernados y verificados:

```text
[ Fuentes Técnicas: Git / CI-CD / K8s ]       [ Dark Data: Contratos / TDRs (PDF/Word) ]
                 │                                                  │
                 ▼                                                  ▼
     ┌───────────────────────┐                          ┌───────────────────────┐
     │ Agente 1:             │                          │ Agente 2:             │
     │ Code-to-Catalog       │                          │ Dark Data Miner       │
     └───────────┬───────────┘                          └───────────┬───────────┘
                 │                                                  │
         [Evidencia Técnica]                            [Evidencia Contractual]
                 │                                                  │
                 └───────────────────┐      ┌───────────────────────┘
                                     ▼      ▼
                          ┌───────────────────────────┐
                          │ Agente 3:                 │
                          │ Reconciliador Semántico   │
                          └─────────────┬─────────────┘
                                        │
                            [Hipótesis Conciliada +
                             Scoring de Confianza]
                                        │
                         ¿Confianza < umbral o vacíos?
                                  ┌─────┴─────┐
                             Sí   │           │   No (Confianza alta)
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

### Agente 1: Code-to-Catalog (Pilar técnico)

Este agente inspecciona de manera continua los artefactos generados en el ciclo de vida del desarrollo de software:
- **Fuentes analizadas**: Repositorios Git (GitHub/GitLab), Dockerfiles, manifiestos de Kubernetes, Helm charts, archivos de dependencias de empaquetado (`pom.xml`, `package.json`, `requirements.txt`, `go.mod`, `build.gradle`), y especificaciones OpenAPI/Swagger.
- **Capacidades de extracción**:
  - Identificación del stack tecnológico real y versiones de frameworks/runtimes en uso.
  - Mapeo de dependencias de librerías y componentes de infraestructura subyacente.
  - Detección de puertos, endpoints expuestos, variables de entorno y servicios de base de datos consumidos.
  - Detección de actividad reciente (commits, PRs) para sugerir potenciales responsables técnicos.
- **Resultado**: Genera un objeto estructurado de **Evidencia Técnica** con hashes de commit y rutas exactas de archivos como soporte.

### Agente 2: Dark Data Miner (Pilar contractual y documental)

Gran parte de la información crítica de una aplicación en organizaciones públicas o corporativas reside en lo que se denomina *Dark Data*: documentos no estructurados que nunca llegan al repositorio de código ni a la CMDB.
- **Fuentes analizadas**: Términos de Referencia (TDRs), contratos de desarrollo o mantenimiento, adendas, órdenes de compra y actas de conformidad técnica (archivos PDF, Word o digitalizaciones escaneadas).
- **Capacidades de extracción**:
  - Procesamiento multimodal (OCR para digitalizaciones y NLP / LLMs con extracción guiada por esquemas).
  - Extracción de proveedores adjudicados, razón social, consorcios y montos asociados.
  - Identificación de vigencia contractual, fechas límite de garantía, renovación y calendarios de soporte contratado.
  - Detección de Acuerdos de Nivel de Servicio (SLAs) contractuales (disponibilidad comprometida, tiempos de respuesta ante incidentes).
  - Identificación de licencias adquiridas y restricciones legales de uso.
- **Resultado**: Genera un objeto estructurado de **Evidencia Contractual y Licenciamiento**, indexando el documento de origen, número de página y cláusula contractual.

### Agente 3: Reconciliador Semántico (Entity Resolution)

El desafío principal en organizaciones reales es que el código y los contratos utilizan nomenclaturas diferentes: un repositorio puede llamarse `svc-mef-pagos-v2`, mientras que el contrato lo denomina *"Servicio de Implementación de la Pasarela de Recaudación Digital para Entidades Públicas"*, y la CMDB lo etiqueta como `VM-PRD-PAGOS01`.

- **Mecanismo de resolución**:
  - Emplea técnicas de resolución de entidades (*Entity Resolution*), combinando similitud léxica difusa (fuzzy matching), embeddings vectoriales semánticos sobre descripciones funcionales y análisis de grafos de co-ocurrencia.
  - Cruza la evidencia técnica del Agente 1 con la evidencia contractual del Agente 2 y los CIs de infraestructura.
- **Scoring de confianza multivariable**:
  - Calcula un puntaje de confianza probabilístico ($0.0$ a $1.0$) para cada atributo y para la correlación global de la entidad.
  - Factores evaluados: concordancia de nombres/alias, congruencia tecnológica (si el TDR pedía Java/Spring y el repo contiene Java 17), alineación de fechas y coincidencia de equipos/autores.
- **Resultado**: Produce una **Hipótesis Conciliada**, vinculando código, contrato e infraestructura bajo una entidad candidata a Fact Sheet.

### Agente 4: Micro-Nudge y Entrevista Proactiva

El mayor error de los portafolios de arquitectura tradicionales es exigir a los desarrolladores y líderes de producto que completen cuestionarios de decenas de campos en una herramienta externa, lo que genera resistencia inmediata y datos ficticios.

- **Filosofía de mínima fricción**: El agente interactúa en los canales cotidianos del equipo (canales de chat como Slack o Microsoft Teams, o comentarios automatizados en Pull Requests).
- **Micro-solicitudes en 1 clic**: Formula preguntas puntuales, contextuales y de respuesta binaria o de selección rápida.
  - *Ejemplo*: *"Hola @carlos.detectamos que el repositorio `svc-mef-pagos-v2` se despliega en producción en K8s. Según los últimos commits, tú eres el principal contribuyente. ¿Confirmas que eres el Dueño Técnico de esta aplicación? [Confirmar] [No, indicar responsable]"*.
  - *Ejemplo 2*: *"El contrato MEF-2024-089 especifica una criticidad de negocio 'Misión Crítica' para este módulo. ¿Sigue vigente esa clasificación? [Sí, confirmar] [No, ajustar]"*.
- **Enriquecimiento progresivo**: Resuelve ambigüedades, llena vacíos de información donde la confianza del reconciliador era insuficiente y actualiza la hipótesis sin fatiga operativa.

---

## Alineación con los Principios de Gobernanza de IA de la OCDE

La arquitectura de descubrimiento y gestión agéntica del APM se diseña bajo estricto apego a las directrices de la **Organización para la Cooperación y el Desarrollo Económicos (OCDE)** sobre inteligencia artificial confiable:

### 1. Supervisión humana y valores centrados en las personas (Principio 1.2)
- **"La IA propone con evidencia, la persona dispone"**: Ningún agente tiene privilegios de escritura directa o publicación desatendida en el catálogo de producción.
- **Doble escalón de validación humana**:
  1. *Validación técnica/operativa*: El desarrollador o dueño de producto valida los micro-nudges de atributos operativos.
  2. *Aprobación de arquitectura*: El comité de **Gobierno de Arquitectura** o el Arquitecto TI revisa formalmente el Fact Sheet consolidado y autoriza su paso a estado `Aprobado` (publicado).

### 2. Transparencia y Explicabilidad con citas de evidencia primaria (Principio 1.3)
- Cada atributo propuesto por el sistema multi-agente está respaldado por **citas de evidencia primaria verificables**:
  - Para datos técnicos: enlace directo al archivo de configuración, línea de código o manifiesto (`deployment.yaml#L45`, `pom.xml#L12-L28`), junto con el hash del commit escaneado.
  - Para datos contractuales: referencia exacta al documento, número de página y párrafo de la cláusula (`Contrato-MEF-2024-012.pdf`, Pág. 8, Cláusula 4.2).
- Si un arquitecto audita un Fact Sheet, la plataforma permite inspeccionar el fragmento original de texto o código que originó la sugerencia, erradicando las alucinaciones sin sustento.

### 3. Robustez, Seguridad y Calidad de Datos (Principio 1.4)
- **Erradicación del Shadow IT**: La combinación del escaneo continuo de repositorios/despliegues y la minería de contratos saca a la luz aplicaciones huérfanas o componentes que operan fuera de la visibilidad formal de TI.
- **Control por umbrales de confianza**: Las correlaciones con puntaje de confianza inferior al umbral configurable (por ejemplo, $< 0.80$) se marcan como `Requiere Verificación` y no pueden publicarse sin aclaración explícita mediante micro-nudge o intervención de un arquitecto.

---

## Capacidades analíticas y downstream

Una vez que el catálogo está poblado y sincronizado de forma continua mediante el descubrimiento upstream, se habilitan las capacidades analíticas downstream:

### Edición asistida y control de cambios
Agentes que asisten a los usuarios durante la navegación y actualización cotidiana del catálogo, verificando consistencia y sugiriendo mejoras sobre Fact Sheets existentes.

### Generación de arquitecturas base
A partir de los datos reconciliados y plantillas estandarizadas, los agentes sintetizan vistas preliminares de arquitectura en notación ArchiMate o C4 (contexto de sistema, topología de contenedores, integraciones). El arquitecto responsable las valida y las incorpora a los artefactos oficiales.

### Gestión de vulnerabilidades (CVEs)
- Ingesta automatizada de feeds públicos y privados (NVD, OSV, GitHub Advisory).
- Correlación automática con las dependencias detectadas por el Agente Code-to-Catalog.
- Priorización calculada mediante la combinación de métricas CVSS + EPSS ponderadas por la criticidad de negocio del Fact Sheet.
- Propuestas de remediación y generación automática de incidencias en ITSM.

### Obsolescencia tecnológica y de licenciamiento
- Vigilancia de hitos de fin de soporte (EOL/EOS) mediante feeds como `endoflife.date` y catálogos de proveedores.
- Cruce con los plazos contractuales y garantías detectados por el Agente Dark Data Miner.
- Notificaciones predictivas con 6 a 12 meses de anticipación para planificar refactorizaciones o renovaciones de contratos.

### Consulta y analítica avanzada sobre el portafolio
- Consultas en lenguaje natural sobre el grafo del portafolio (*"¿Qué aplicaciones dependen de Oracle 12c y tienen contrato vencido este año?"*).
- Matriz de racionalización (TIME: Tolerante, Invertir, Mantener, Eliminar).
- Detección de redundancias funcionales y análisis de impacto en cascada ante cambios.

---

## Requisitos transversales de seguridad y operación

- **Seguridad**: Integración con IAM corporativo (OIDC/SAML, RBAC/ABAC granular). Las credenciales de acceso a repositorios y repositorios documentales se administran en almacenes secretos (Key Vaults/Secrets Managers) y nunca se almacenan en texto plano en el APM.
- **Ambiente de ejecución seguro (Sandbox)**: Los agentes operan en contenedores aislados y de solo lectura sobre las fuentes inspeccionadas.
- **Evaluación y evals**: Monitoreo continuo de precisión y exhaustividad (*precision/recall*) en la extracción documental y la resolución de identidades.
- **Trazabilidad y pista de auditoría**: Registro inmutable de cada inferencia, modelo LLM utilizado, tokens consumidos, versión del prompt y fecha/hora de validación humana.