---
title: Catálogos del portafolio
description: Los catálogos que estructuran los datos del portafolio de aplicaciones.
---

## Catálogos núcleo

El sistema se organiza alrededor de tres catálogos principales:

### 1. Aplicaciones

Registro maestro de las aplicaciones del portafolio. Campos orientativos:

- Datos generales: nombre, descripción, propietario de negocio, arquitecto responsable, equipo.
- Clasificación: capacidad de negocio que soporta, criticidad, estado del ciclo de vida.
- Estrategia: mantener / invertir / contener / retirar (matriz de racionalización).
- Stack: tecnología usada, integraciones, usuarios, locaciones, KPIs.
- Artefactos: arquitecturas y diagramas asociados.

### 2. Integraciones

Flujos de datos entre aplicaciones y sistemas externos:

- Extremos origen/destino, protocolo (REST, SOAP, mensajería, ficheros), autenticación.
- Volumen y tipo de datos intercambiados, dueño técnico, SLA, criticidad del flujo.
- Contrato y versión de API, estado operativo, sensibilidad de los datos.

### 3. Tecnologías y componentes

Inventario de productos tecnológicos (lenguajes, frameworks, librerías, bases de datos, middleware, nube):

- Versiones instaladas y su distribución entre aplicaciones.
- Fechas de fin de vida (EOL) y fin de soporte (EOS).
- Licencias y su estado.
- Vulnerabilidades relacionadas (CVEs).

Este catálogo habilita la [gestión de vulnerabilidades y obsolescencia](../ia-agentes/).

## Catálogos extendidos (por fases)

Se recomienda incorporarlos progresivamente:

- **Proveedores, contratos y licencias**: vendors, costos, fechas de renovación, términos y uso.
- **Capacidades de negocio**: mapa de capacidades y cobertura por aplicación (detección de solapamientos y vacíos).
- **Datos**: dominios y activos de datos, ciclo de vida y responsabilidad.
- **Iniciativas y proyectos**: hoja de ruta del portafolio, fases y estado (alimenta las presentaciones de avance).
- **Arquitecturas y artefactos**: repositorio versionado de diagramas (ArchiMate/C4/SVG/PDF) vinculados a aplicaciones — conecta directamente con este portal de documentación.

## Filtros complejos y activos críticos

Sobre estos catálogos se construyen vistas analíticas: activos críticos, cobertura por capacidad, riesgo agregado por negocio, dependencias hacia tecnologías obsoletas o vulnerables, y consultas en lenguaje natural. La definición de "activo crítico" se modela como regla configurable (criticidad de negocio × impacto × dependencias), no como campo fijo.