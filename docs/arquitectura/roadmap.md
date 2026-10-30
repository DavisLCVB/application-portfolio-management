---
title: Roadmap de implementación
description: Fases de construcción del APM, de los cimientos al gobierno avanzado.
---

## Fases

<ol class="apm-fases" aria-label="Fases del roadmap">
<li class="apm-fase apm-fase--f0 apm-fase--actual" style="--i: 0"><div class="apm-fase__cab"><span class="apm-fase__codigo">F0</span><strong class="apm-fase__nombre">Cimientos</strong><span class="apm-fase__estado">En curso</span></div><dl><dt>Alcance</dt><dd>Portal de documentación y arquitectura (este sitio), modelo de datos inicial, CI/CD de publicación; decisión de construir con fuentes abiertas (ver <a href="#decisión-construir-con-fuentes-abiertas">abajo</a>) y piloto de calibración del <em>score</em> y de los micro-nudges.</dd><dt>Criterio de salida</dt><dd>El portal se despliega automáticamente y la arquitectura ArchiMate está versionada y publicada; la decisión de construcción queda registrada antes de F1.</dd></dl></li>
<li class="apm-fase apm-fase--f1" style="--i: 1"><div class="apm-fase__cab"><span class="apm-fase__codigo">F1</span><strong class="apm-fase__nombre">Catálogo núcleo</strong><span class="apm-fase__estado">Planificada</span></div><dl><dt>Alcance</dt><dd>Catálogos de Aplicaciones e Integraciones, IAM, UI base, motor de grafo de dependencias.</dd><dt>Criterio de salida</dt><dd>Alta/baja/modificación de aplicaciones e integraciones con auditoría.</dd></dl></li>
<li class="apm-fase apm-fase--f2" style="--i: 2"><div class="apm-fase__cab"><span class="apm-fase__codigo">F2</span><strong class="apm-fase__nombre">Tecnologías y seguridad</strong><span class="apm-fase__estado">Planificada</span></div><dl><dt>Alcance</dt><dd>Catálogo de Tecnologías, gestión de vulnerabilidades y obsolescencia, alertas y aprobaciones.</dd><dt>Criterio de salida</dt><dd>CVEs y EOL correlacionados con aplicaciones; primeros informes de riesgo.</dd></dl></li>
<li class="apm-fase apm-fase--f3" style="--i: 3"><div class="apm-fase__cab"><span class="apm-fase__codigo">F3</span><strong class="apm-fase__nombre">Ingesta continua</strong><span class="apm-fase__estado">Planificada</span></div><dl><dt>Alcance</dt><dd>Conectores deterministas CMDB/nube/SBOM/repos; descubrimiento técnico (Agente 1, Code-to-Catalog) y reconciliación anclada en el catálogo existente (Agente 3), con candidatos huérfanos a revisión humana.</dd><dt>Criterio de salida</dt><dd>El catálogo se actualiza desde fuentes reales con intervención mínima; <em>score</em> de confianza calibrado contra un conjunto verificado de aplicaciones (umbrales tomados del piloto de calibración).</dd></dl></li>
<li class="apm-fase apm-fase--f4" style="--i: 4"><div class="apm-fase__cab"><span class="apm-fase__codigo">F4</span><strong class="apm-fase__nombre">IA agéntica</strong><span class="apm-fase__estado">Planificada</span></div><dl><dt>Alcance</dt><dd>Minería de contratos y TDRs (Agente 2), micro-nudges con escalamiento (Agente 4); asistentes downstream: edición asistida, generación de arquitecturas base y consulta del catálogo vía servidor MCP; humano en el bucle.</dd><dt>Criterio de salida</dt><dd>Propuestas de IA auditadas y aprobadas por arquitectos; evidencia contractual citada por cláusula; blueprints generados y validados; tasa de respuesta a micro-nudges y carga de revisión dentro de las metas fijadas en el piloto.</dd></dl></li>
<li class="apm-fase apm-fase--f5" style="--i: 5"><div class="apm-fase__cab"><span class="apm-fase__codigo">F5</span><strong class="apm-fase__nombre">Analítica avanzada</strong><span class="apm-fase__estado">Planificada</span></div><dl><dt>Alcance</dt><dd>Scoring, impacto, solapamientos, what-if, informes ejecutivos PDF y gobierno; chat del portafolio en lenguaje natural (opcional).</dd><dt>Criterio de salida</dt><dd>Dashboard completo y reportes ejecutivos desde el portal.</dd></dl></li>
</ol>

Los criterios de salida de F3 y F4 dependen del **piloto de calibración**: los umbrales del *score*, las metas de respuesta a micro-nudges y el SLA de revisión son propuestas hasta que el piloto los mida sobre un conjunto verificado de aplicaciones.

## Decisión: construir con fuentes abiertas

Decisión tomada antes de F1, con presupuesto limitado:

- **No se adquieren herramientas comerciales de APM/EA.** Los productos revisados en [Soluciones similares](../soluciones-similares/) se usan como referencia de diseño, no como plataforma.
- **Construcción propia sobre fuentes y formatos abiertos:** `endoflife.date` (EOL), NVD y OSV (vulnerabilidades), SBOM en CycloneDX o SPDX, metadatos en el repositorio al estilo Backstage (`catalog-info.yaml`) y modelado ArchiMate con Archi y PlantUML.
- **Azure sigue siendo la arquitectura objetivo empresarial**, pero el diseño es portable: el MVP puede ejecutarse en la capa gratuita de Azure o de GCP y el proveedor de LLM es intercambiable (ver [Portabilidad y costo](../arquitectura-solucion/#portabilidad-y-costo)).
- **Primero la captura de datos, después la conversación:** el valor está en el descubrimiento y la reconciliación. La consulta del catálogo se expone primero mediante un servidor MCP, más ligero que un chat propio; el chat del portafolio queda como capacidad opcional posterior.

## Principios de arquitectura

- **Arquitectura y documentación como código**: todo lo visible se genera desde fuentes versionadas (detección de cambios por CI/CD).
- **APIs primero y trazabilidad total**: todas las operaciones son auditables.
- **La IA propone, la humana dispone**: cambios de IA siempre con aprobación.
- **Datos gobernados**: el catálogo es un activo con propietario, calidad y confianza.

## Relación con el portal de documentación

Desde la fase 0, cada despliegue exitoso publica la última versión de documentos, diagramas y PDF, aunque el sistema APM siga en construcción. Los diagramas ArchiMate se regeneran con `npm run diagrams` y el CI valida que siempre estén al día antes de fusionar.