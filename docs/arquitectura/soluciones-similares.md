---
title: Soluciones similares y evaluación crítica
description: Panorama de herramientas de APM y arquitectura empresarial, con y sin IA, y evaluación crítica de la propuesta frente a ellas.
---

> **Fecha de la investigación:** 2026-10-15. Las capacidades de IA de los fabricantes cambian cada trimestre; toda afirmación lleva su fuente y lo que no pudo confirmarse se marca como **(no verificado)**. Las cifras de ROI o de automatización publicadas por los propios fabricantes son material de marketing, no mediciones independientes.

## Problema común

Todas las soluciones revisadas atacan el mismo problema que el APM de este portal: **mantener un inventario de aplicaciones exacto y vigente** y usarlo para decidir. Las decisiones típicas son racionalizar con el modelo TIME (*Tolerate, Invest, Migrate, Eliminate*), analizar el impacto de un cambio o retiro, anticipar la obsolescencia (EOL/EOS) y relacionar vulnerabilidades con aplicaciones.

La diferencia está en **cómo se llena y se mantiene al día el inventario**:

- encuestas y carga manual;
- conectores hacia CMDB, SSO o nube;
- descubrimiento técnico (SBOM, repositorios, agentes de red);
- y, más recientemente, asistentes y agentes de IA.

## Soluciones sin IA (o con la IA como añadido opcional)

| Solución | Qué hace | Cómo se alimenta y actualiza | Licenciamiento | Limitaciones principales |
|---|---|---|---|---|
| **SAP LeanIX APM** | Inventario de aplicaciones, dependencias, TIME, informes de TCO y *fit*, riesgo de obsolescencia [1] | Integraciones nativas, API abierta, importación Excel, encuestas, *Quality Seal* y descubrimiento de SaaS/SAP [1][3]; SBOM y catálogo de ciclo de vida en el módulo de riesgo tecnológico [4][5][6] | SaaS; precio por número de aplicaciones, usuarios ilimitados; sin precios públicos [1] | El dato de negocio (dueño, criticidad, costo) sigue dependiendo de personas; el descubrimiento cubre SaaS/SAP mejor que el software propio sin SBOM |
| **ServiceNow APM + CMDB** | Inventario de aplicaciones de negocio sobre la CMDB, mapa de capacidades y racionalización [7][8] | CMDB alimentada por Discovery y Service Graph Connectors, que importan datos de terceros de forma programada [9] | Suscripción; sin precios públicos (no verificado) | Depende de la calidad de la CMDB y del modelo CSDM; implantación y licencias pesadas para un equipo pequeño (no verificado) |
| **Bizzdesign (Horizzon, HOPEX, Alfabet)** | Repositorio de arquitectura y gestión de portafolio, modelado ArchiMate [12][13] | Modelado y carga por arquitectos, integraciones; fusión de Bizzdesign, MEGA y Alfabet en 2025, con hojas de ruta de producto mantenidas al menos 5–7 años [14] | Comercial; sin precios públicos | Curva de aprendizaje alta según revisores [12]; tres productos en convergencia hacia una plataforma nueva [14] |
| **Orbus iServer365** | EA y gestión de portafolio sobre Microsoft 365, informes en Power BI [17] | Integraciones con ServiceNow, Azure DevOps, Jira, Flexera y M365 [17] | SaaS comercial; ROI de 394 % en un estudio encargado por el propio fabricante [17] | Capacidades de IA no confirmadas en fuentes públicas (no verificado) |
| **Archi** (código abierto) | Editor de modelos ArchiMate 3.2, multiplataforma [18][19] | 100 % manual; colaboración vía *plug-in* coArchi sobre Git [19] | Gratuito, licencia MIT [19] | No es un APM: sin flujo de aprobación, sin descubrimiento; usuarios señalan ausencia de informes y tableros [21] |
| **Essential** (Open Source / Cloud) | Herramienta de EA usada para APM y racionalización tecnológica [20] | Carga manual sobre un metamodelo propio; la edición abierta exige formación en ese metamodelo según usuarios [21] | Edición abierta gratuita; Essential Cloud comercial [20] | Entrada de datos costosa; comunidad pequeña |
| **Hoja de cálculo / CMDB manual** | Práctica habitual de partida (es el punto de partida asumido por este proyecto, ver [Migración del Excel](../gobierno-datos/#migración-del-excel)) | Encuestas y actualización periódica a mano | Sin costo de licencia | Se desactualiza, no tiene procedencia ni control de cambios; es el problema que motiva el APM |

**Notas:**

- **LeanIX** es la referencia directa de este proyecto: su *Meta Model v4* es la base del [modelo de datos](../modelo-datos/) y su *Quality Seal* se analiza en [Gobierno de datos](../gobierno-datos/#relación-con-el-quality-seal-de-leanix). Ya ofrece descubrimiento de SaaS mediante conectores con Okta, Entra ID, Netskope o Zscaler [3], y extrae versiones desde SBOM para cruzarlas con fechas de fin de soporte [4].
- **ServiceNow** separa el inventario (CMDB) del análisis (APM); su fortaleza es el ecosistema ITSM/ITOM, no el modelado de arquitectura.
- **Backstage** (CNCF, código abierto) no es un APM, pero resuelve el mismo problema de vigencia desde los equipos de desarrollo: el catálogo se alimenta de archivos YAML de metadatos versionados en los repositorios y se actualiza con cada *merge* [22]. Es el antecedente más cercano al Agente 1, con una diferencia: Backstage exige que el equipo escriba el YAML, y el Agente 1 lo infiere.

## Soluciones con IA

| Solución | Qué hace la IA | Descubrimiento / actualización | Estado | Limitaciones |
|---|---|---|---|---|
| **SAP LeanIX AI** | Documentación generativa, resumen de dependencias, IA agéntica conversacional, servidor MCP, *AI Agent Hub* para inventariar agentes de IA [1][2] | Integraciones con repositorios de agentes de SAP, Google y Microsoft; API con protocolo Agent2Agent [2]; búsqueda semántica y configuración en lenguaje natural (actualización de julio de 2026, no verificado en fuente primaria) | Parte en *Early Adopter* según terceros (no verificado) | La IA se apoya en el inventario existente; no se documenta minería de contratos ni reconciliación con repositorios propios |
| **Ardoq AI** | Asistente conversacional con respuestas trazables a la fuente; *AI Import Builder* que lee la documentación de un sistema externo y configura la importación; agentes personalizados [10][11] | Grafo de arquitectura actualizado por importaciones; *Data Ingestion Agent* en vista previa técnica [10] | Asistente e *Import Builder* GA; agentes personalizados en beta abierta (mayo 2026) [10] | Afirma que el arquitecto puede cuestionar o anular cada propuesta [10]; el 40 % de automatización es estimación del fabricante |
| **ServiceNow Now Assist (CMDB y SPM)** | Calidad de la CMDB: búsqueda de CIs, resúmenes, detección de duplicados, problemas de importación de conectores, asesoría agéntica de gobierno [15]; en SPM, resúmenes de demanda e informes de estado [16] | Sobre Discovery y Service Graph Connectors existentes [9][15] | GA desde la versión Zurich; modelos seleccionables (Now LLM, Azure OpenAI, Gemini, Claude) [15][16] | El propio fabricante exige supervisión humana y evaluación de exactitud [16]; no se halló documentación de Now Assist específica para APM (no verificado) |
| **Bizzdesign AI** | Capacidades de IA para modelado, captura de contenido y calidad de datos según Gartner [12]; servidor MCP de Horizzon en beta [13] | Sin descubrimiento automático documentado | Beta (2026) [13] | Funciones de IA poco documentadas en fuentes públicas |
| **Flexera One (SaaS Management + Technopedia)** | Descubrimiento y normalización de SaaS y software; biblioteca de referencia con datos de fin de vida y soporte [23][24] | Múltiples fuentes combinadas: extensiones de navegador, SSO, CASB, conectores API, agentes y datos financieros [23] | Comercial; sin precios públicos | Orientado a activos y licencias (ITAM), no a arquitectura ni a capacidades de negocio |
| **Investigación: LLM para modelado empresarial** | Reitemeyer y Fill (2025): los LLM rinden en tareas acotadas, la fiabilidad cae con la complejidad y la supervisión experta es esencial [25] | — | Académico | Experimentos y encuesta pequeños; sin despliegue en producción |
| **Investigación: ArchAgent** | Agentes que combinan análisis estático y síntesis con LLM para recuperar la arquitectura de varios repositorios heredados [26] | Desde el código fuente | Académico (enero 2026) | Evaluado en proyectos de código abierto, no en portafolios corporativos |

**Notas:**

- Los fabricantes convergen en **tres patrones**: un asistente conversacional sobre el grafo existente, conectores asistidos por IA y servidores MCP para que agentes externos lean el repositorio de arquitectura. Ninguna fuente revisada documenta **minería de contratos o TDRs** para poblar el portafolio, ni **micro-solicitudes** a responsables en Teams o Slack como mecanismo central.
- La investigación coincide con el principio del proyecto: los LLM sirven para tareas acotadas con supervisión humana [25], y la recuperación desde código funciona mejor cuando se combina con análisis estático determinista [26].

## Evaluación crítica de la propuesta

Juicio de la propuesta frente a las soluciones anteriores, con referencia a la página de este portal que sostiene cada punto.

### Puntos fuertes

1. **Descubrimiento upstream desde fuentes que los incumbentes no cubren.** Los contratos y TDRs como fuente de proveedor, vigencia, SLA y licencias ([Agente 2](../ia-agentes/#agente-2-dark-data-miner-pilar-contractual-y-documental)) no aparecen en ninguna herramienta revisada, cuyo descubrimiento es de SaaS, SSO o CMDB [3][9][23]. Es relevante en el sector público, donde mucho software se adquiere por contrato.
2. **Reconciliación anclada en el catálogo y N:M.** El [Agente 3](../ia-agentes/#agente-3-reconciliador-semántico-entity-resolution) adjunta evidencia a aplicaciones conocidas y envía a revisión los huérfanos y conflictos, en lugar de crear entidades desde cero. ServiceNow resuelve duplicados de CIs [15], pero no vincula repositorios y contratos con aplicaciones de negocio.
3. **Procedencia por atributo y citas primarias.** Cada valor guarda fuente, método, versión del agente y cita a línea de código o cláusula ([Gobierno de datos](../gobierno-datos/#procedencia-por-atributo), [IA agéntica](../ia-agentes/#2-transparencia-y-explicabilidad-principio-13)). Ardoq promete trazabilidad a la fuente [10]; la propuesta la baja al nivel de atributo y la hace auditable.
4. **IA acotada y controles de riesgo explícitos.** El LLM solo extrae texto libre y redacta; el resto es determinista ([tabla de agentes](../ia-agentes/#qué-es-determinista-y-qué-usa-llm)). Hay 14 riesgos con prevención y detección y un mecanismo de detención en tres niveles ([Riesgos de la IA](../arquitectura-solucion/#riesgos-de-la-ia-y-contramedidas)). Es coherente con la evidencia académica [25][26].
5. **Arquitectura como código y estándar abierto.** ArchiMate 3.2 en PlantUML versionado y validado en CI ([Visión general](../)) evita el bloqueo del formato propietario, igual que Archi [19], pero con publicación automática.

### Puntos débiles

1. **Construcción propia frente a productos maduros.** LeanIX, ServiceNow y Ardoq ya ofrecen inventario, TIME, informes, integraciones y asistentes de IA en producción [1][10][15]. La decisión tomada es **no adquirir herramientas comerciales de APM/EA** y construir con fuentes y formatos abiertos ([Roadmap](../roadmap/#decisión-construir-con-fuentes-abiertas)), usando a los incumbentes como referencia de diseño. El riesgo que queda es el de toda construcción propia: la propuesta parte de cero (seis fases, F0 a F5) y necesita equipo para mantener conectores, agentes, evals y seguridad. El costo de operación aún no está estimado; se acota con un MVP en capa gratuita de nube ([Portabilidad y costo](../arquitectura-solucion/#portabilidad-y-costo)).
2. **Madurez e integraciones.** Un incumbente trae cientos de conectores, catálogos de referencia (Technopedia supera los 5 millones de productos [24]) y soporte del fabricante. La propuesta depende de fuentes abiertas (`endoflife.date`, NVD y OSV), cuya cobertura de productos es menor, y su ingesta está "por validar" ([Ingesta](../arquitectura-solucion/#ingesta)). La mitigación prevista es una tabla propia de EOL curada para los productos que esas fuentes no cubren.
3. **Supuestos sin evidencia propia.** El *score* de confianza no está calibrado, el umbral de 0,85 es un ejemplo y la tasa de respuesta a micro-nudges es una hipótesis ([Agente 3](../ia-agentes/#agente-3-reconciliador-semántico-entity-resolution), riesgo 14 en [Riesgos de la IA](../arquitectura-solucion/#riesgos-de-la-ia-y-contramedidas)). Sin un piloto medido, el valor diferencial no está demostrado.
4. **Carga de gobierno humano.** El doble escalón de aprobación, las colas de huérfanos y conflictos y la migración en `Borrador` ([Gobierno de datos](../gobierno-datos/#flujo-de-registro-descentralizado)) pueden saturar a un equipo pequeño. Es el mismo cuello de botella que la propuesta quiere eliminar, ahora desplazado a la revisión.
5. **Dependencia de plataforma y sensibilidad de datos.** La arquitectura objetivo descansa sobre Azure, con varios componentes "por validar" ([Componentes](../arquitectura-solucion/#componentes)); para no quedar atada, el proveedor de LLM se abstrae y el diseño se mantiene portable entre nubes ([Portabilidad y costo](../arquitectura-solucion/#portabilidad-y-costo)), lo que exige disciplina adicional en las evals por proveedor. Los contratos y autores de commits son datos personales (Ley N.° 29733), lo que encarece la operación frente a herramientas que no los procesan.

### Matriz comparativa

| Criterio | Propuesta | Incumbentes (LeanIX, ServiceNow, Ardoq, Bizzdesign) |
|---|---|---|
| Madurez y soporte | Diseño, sin implementación | Productos en producción con soporte comercial |
| Integraciones listas | Pocas, por construir | Amplias (SSO, CMDB, nube, ITSM) [1][9][17] |
| Descubrimiento de SaaS | No previsto | Sí: LeanIX, Flexera [3][23] |
| Descubrimiento desde código propio | Agente 1 (manifiestos, K8s, OpenAPI) | Parcial: SBOM en LeanIX [4]; Backstage requiere YAML manual [22] |
| Minería de contratos y TDRs | Sí (Agente 2) | No documentado |
| Reconciliación con catálogo existente | N:M con colas de revisión | Deduplicación de CIs en CMDB [15] |
| Procedencia por atributo | Sí, con cita primaria | Parcial (trazabilidad a la fuente en Ardoq [10]) |
| Asistente en lenguaje natural | Secundario y posterior; consulta vía MCP primero | Disponible (Ardoq GA [10], LeanIX [1]) |
| Notación abierta y como código | ArchiMate en PlantUML versionado | Bizzdesign y Archi modelan ArchiMate; repositorios propietarios |
| Costo | Sin licencia: construcción propia con fuentes abiertas y MVP en capa gratuita; costo de equipo y operación aún no estimado | Suscripción; precios no públicos |

### Qué tomar / qué evitar

**Qué tomar**

- **Construir con fuentes abiertas y usar a los incumbentes como referencia de diseño.** No se adquieren herramientas comerciales de APM/EA: el metamodelo sigue a LeanIX, el catálogo en repositorio sigue a Backstage y el modelado usa Archi, pero la implementación es propia sobre fuentes y formatos abiertos. El esfuerzo diferencial se concentra en los Agentes 2 y 3 y en la procedencia; lo genérico (inventario, TIME, informes) se mantiene simple. La decisión queda registrada antes de F1 ([Roadmap](../roadmap/#decisión-construir-con-fuentes-abiertas)).
- **Reusar formatos estándar de descubrimiento.** Ingerir SBOM en CycloneDX o SPDX (como hace LeanIX con SBOM [4]) y admitir un archivo de metadatos en el repositorio al estilo Backstage [22] como evidencia de máxima confianza, antes de inferir con el Agente 1.
- **Datos de ciclo de vida de fuentes abiertas.** Usar `endoflife.date` para EOL y NVD/OSV para vulnerabilidades. Su cobertura es menor que la de un catálogo comercial como Technopedia [24]; se compensa con una tabla propia de EOL curada por el equipo para los productos no cubiertos, con su procedencia.
- **Exponer el catálogo vía MCP**, como LeanIX, Ardoq y Bizzdesign [1][10][13], para que otros agentes consulten el APM sin construir otro chat.

**Qué evitar**

- **Presentar el *score* o los micro-nudges como probados** antes de calibrarlos en un piloto con un conjunto verificado ([Agente 3](../ia-agentes/#agente-3-reconciliador-semántico-entity-resolution)).
- **Competir en el asistente de chat**, donde los incumbentes ya tienen productos GA [10][15]; el valor de la propuesta está en la captura de datos, no en la conversación.
- **Ampliar la cola de revisión sin medir su costo**: fijar desde el inicio métricas de carga de revisión y un SLA propuesto ([Gobierno de datos](../gobierno-datos/#sla-de-revisión-y-carga-de-revisión)).
- **Usar cifras de ROI de fabricantes** como argumento comparativo; no son independientes [10][17].

## Fuentes

Todas consultadas el 2026-10-15.

1. SAP LeanIX — Application Portfolio Management: <https://www.leanix.net/en/products/application-portfolio-management>
2. SAP LeanIX — AI Agent Hub: <https://www.leanix.net/en/blog/sap-leanix-announces-launch-of-ai-agent-hub-and-key-industry-partnerships>
3. Okta Integration Network — LeanIX SaaS Discovery: <https://www.okta.com/integrations/leanix-saas-discovery/>
4. SAP LeanIX — Actualización de producto (SBOM y fin de soporte): <https://updates.leanix.net/announcements/ann_bWQnrdHiEVRa0>
5. SAP LeanIX docs — Obsolescence Risk Management: <https://docs-eam.leanix.net/docs/obsolescence-risk-management>
6. SAP LeanIX — Technology Risk and Compliance: <https://www.leanix.net/en/products/technology-risk-and-compliance>
7. ServiceNow — Application Portfolio Management: <https://www.servicenow.com/products/application-portfolio-management.html>
8. ServiceNow — Hoja de datos APM: <https://www.servicenow.com/standard/resource-center/data-sheet/ds-application-portfolio-management.html>
9. Surety Systems — Guía de Service Graph Connectors (fuente secundaria): <https://www.suretysystems.com/insights/servicenow-service-graph-connectors-guide-surety-systems/>
10. Ardoq — AI-First Enterprise Architecture Platform (28-05-2026): <https://www.ardoq.com/news/ai-first-enterprise-architecture-platform>
11. Ardoq — Q1 2026 AI Roundup: <https://www.ardoq.com/blog/q1-2026-ardoq-ai-roundup>
12. Gartner Peer Insights — Bizzdesign Horizzon: <https://www.gartner.com/reviews/market/enterprise-architecture-tools/vendor/bizzdesign/product/bizzdesign-horizzon>
13. Bizzdesign — Product roadmaps 2026: <https://mega.com/customer/bizzdesign-product-roadmaps-2026>
14. Forrester — The EA Tool Market Starts 2025 With A Notable Merger: <https://www.forrester.com/blogs/the-enterprise-architecture-tool-market-starts-2025-with-a-notable-merger/>
15. ServiceNow docs — Now Assist for CMDB release notes (Zurich): <https://www.servicenow.com/docs/r/zurich/release-notes/now-assist-cmdb-rn.html>
16. ServiceNow docs — Now Assist for SPM release notes: <https://www.servicenow.com/docs/r/release-notes/now-assist-for-spm-rn.html>
17. SoftwareReviews — iServer and SPM aligned to Microsoft: <https://www.softwarereviews.com/vendor-technology-notes/iserver-enterprise-architecture-and-strategic-portfolio-management-tightly-aligned-to-your-microsoft-suite>; Fintech Times — estudio Forrester TEI encargado por Orbus: <https://thefintechtimes.com/study-shows-that-iserver365-users-can-sunset-20-of-applications-driving-394-roi/>
18. Archi — sitio oficial: <https://www.archimatetool.com/>
19. Archi — repositorio GitHub: <https://github.com/archimatetool/archi>; coArchi: <https://github.com/archimatetool/archi-modelrepository-plugin>
20. The Essential Project — Essential Cloud: <https://enterprise-architecture.org/essential_cloud.php>; FAQ: <https://forums.enterprise-architecture.org/viewtopic.php?p=6>
21. Gartner Peer Community — alternativas abiertas a herramientas de EA (opiniones de usuarios): <https://www.gartner.com/peer-community/post/whilst-high-quality-paid-enterprise-architecture-applications-market-increasing-move-to-saas-dangers-vendor-lock-it-s-prudent>
22. Backstage — Software Catalog: <https://backstage.io/docs/features/software-catalog/>
23. Flexera — Hoja de datos Flexera One SaaS Management: <https://www.flexera.com/sites/default/files/datasheet-flexera-one-saas-management.pdf>
24. Flexera — Technopedia: <https://www.flexera.com/enterprise/products/data-platform/technopedia/>
25. Reitemeyer, B. y Fill, H.-G. (2025). *Applying Large Language Models in Knowledge Graph-based Enterprise Modeling: Challenges and Opportunities*. arXiv:2501.03566: <https://arxiv.org/abs/2501.03566>
26. Pan, R. et al. (2026). *ArchAgent: Scalable Legacy Software Architecture Recovery with LLMs*. arXiv:2601.13007: <https://arxiv.org/abs/2601.13007>

**Límites de esta investigación:** varias páginas de fabricantes (ServiceNow, Essential) devolvieron error 403 a la extracción automática y se usaron resúmenes de búsqueda o fuentes secundarias. No se encontraron precios públicos para ningún producto comercial salvo una referencia antigua de Essential Cloud. Las capacidades de IA de Orbus y Bizzdesign, y la existencia de Now Assist específico para APM, quedan **(no verificado)**.
