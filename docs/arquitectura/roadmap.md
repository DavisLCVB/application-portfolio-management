---
title: Roadmap de implementación
description: Fases de construcción del APM, de los cimientos al gobierno avanzado.
---

## Fases

| Fase | Alcance | Criterio de salida |
| --- | --- | --- |
| **F0 · Cimientos** | Portal de documentación y arquitectura (este sitio), modelo de datos inicial, CI/CD de publicación. | El portal se despliega automáticamente y la arquitectura ArchiMate está versionada y publicada. |
| **F1 · Catálogo núcleo** | Catálogos de Aplicaciones e Integraciones, IAM, UI base, motor de grafo de dependencias. | Alta/baja/modificación de aplicaciones e integraciones con auditoría. |
| **F2 · Tecnologías y seguridad** | Catálogo de Tecnologías, gestión de vulnerabilidades y obsolescencia, alertas y aprobaciones. | CVEs y EOL correlacionados con aplicaciones; primeros informes de riesgo. |
| **F3 · Ingesta continua** | Conectores deterministas CMDB/nube/SBOM/repos; descubrimiento técnico (Agente 1, Code-to-Catalog) y reconciliación anclada en el catálogo existente (Agente 3), con candidatos huérfanos a revisión humana. | El catálogo se actualiza desde fuentes reales con intervención mínima; *score* de confianza calibrado contra un conjunto verificado de aplicaciones. |
| **F4 · IA agéntica** | Minería de contratos y TDRs (Agente 2), micro-nudges con escalamiento (Agente 4); asistentes downstream: edición asistida, generación de arquitecturas base, consulta en lenguaje natural, humano en el bucle. | Propuestas de IA auditadas y aprobadas por arquitectos; evidencia contractual citada por cláusula; blueprints generados y validados. |
| **F5 · Analítica avanzada** | Scoring, impacto, solapamientos, what-if, informes ejecutivos PDF y gobierno. | Dashboard completo y reportes ejecutivos desde el portal. |

## Principios de arquitectura

- **Arquitectura y documentación como código**: todo lo visible se genera desde fuentes versionadas (detección de cambios por CI/CD).
- **APIs primero y trazabilidad total**: todas las operaciones son auditables.
- **La IA propone, la humana dispone**: cambios de IA siempre con aprobación.
- **Datos gobernados**: el catálogo es un activo con propietario, calidad y confianza.

## Relación con el portal de documentación

Desde la fase 0, cada despliegue exitoso publica la última versión de documentos, diagramas y PDF, aunque el sistema APM siga en construcción. Los diagramas ArchiMate se regeneran con `npm run diagrams` y el CI valida que siempre estén al día antes de fusionar.