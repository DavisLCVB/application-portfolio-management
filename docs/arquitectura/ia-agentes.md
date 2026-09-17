---
title: IA agéntica y funcionalidades
description: Capacidades de IA agéntica del APM y funcionalidades adicionales propuestas.
---

## Capacidades principales

### Edición de información asistida

Agentes que proponen creaciones o correcciones sobre los catálogos. Toda propuesta queda como **borrador auditado** con origen (humano o IA) y confianza, y requiere **aprobación humana** antes de publicarse. Cumple el principio *"la IA propone, la humana dispone"*.

### Generación de arquitecturas base

A partir de los datos del catálogo y plantillas, los agentes generan **vistas de arquitectura preliminares** (ArchiMate/C4) por aplicación o integración: diagramas de contexto, composición, datos e integraciones. El arquitecto las valida y las incorpora como artefactos del portafolio.

### Gestión de vulnerabilidades

- Ingesta de CVEs desde fuentes públicas (NVD/OSV) y feeds de proveedores.
- Correlación automática con el **catálogo de tecnologías** y las aplicaciones afectadas.
- Priorización combinando CVSS + EPSS con la criticidad de las aplicaciones.
- Propuestas de remediación y generación de tickets en la herramienta de ITSM.

### Obsolescencia de componentes

- Seguimiento de EOL/EOS (endeoflife.date y fuentes de proveedores) y fechas de cumplimiento de licencias.
- Alertas anticipadas y recomendaciones de actualización por aplicación afectada.

### Consulta y analítica sobre el portafolio

Filtros complejos, **activos críticos**, scoring y matriz de racionalización (mantener/invertir/contener/retirar), cobertura por capacidad, detección de solapamientos, análisis de impacto de cambios y costos estimados.

## Funcionalidades adicionales propuestas

1. **Chat del portafolio**: respuestas y gráficas en lenguaje natural sobre los catálogos.
2. **Enriquecimiento automático** al incorporar una aplicación (stack detectado, dueños estimados, datos de contacto).
3. **Descubrimiento continuo**: agentes que escanean CMDB, nube, monitoreo, SBOM y repositorios de código para mantener el catálogo fresco.
4. **Alertas y digest programados**: CVEs nuevos, EOL próximas, contratos por vencer, cambios pendientes de aprobación.
5. **Análisis de impacto**: "si cambia X, ¿qué se ve afectado?" sobre el grafo de dependencias.
6. **Detección de duplicados funcionales** entre aplicaciones.
7. **Escenarios "what-if"** de modernización y migración (con costos y riesgo estimados).
8. **Informes ejecutivos** generados por IA (PDF) — conecta con la sección [Documentos PDF](../../documentos/).
9. **Verificación de cumplimiento y salud**: políticas, estándares y puntaje de salud por aplicación.
10. **Revisor de arquitectura**: agentes que contrastan arquitecturas propuestas contra los estándares del equipo.
11. **Gobierno y trazabilidad**: bitácora completa de cambios (origen, prompt, versión de modelo, aprobaciones).

## Requisitos transversales

- **Seguridad**: IAM (OIDC/SSO, RBAC/ABAC), sandbox para ejecución de agentes, sin credenciales en el catálogo.
- **Calidad**: evaluación de los agentes (evals) y umbrales de confianza; los agentes no publican por sí mismos.
- **Trazabilidad**: cada cambio registra origen, herramienta, versión de modelo y aprobador.