---
title: Interfaz de usuario (UI/UX)
description: Pantallas, navegación y patrones de interacción propuestos para el APM.
---

## Principios de la interfaz

- **Orientada a catálogos**: cada catálogo es un espacio con listado, filtros, detalle y vista gráfica.
- **IA visible pero gobernada**: todo contenido generado por agentes se muestra como **propuesta** con origen, confianza y estado de aprobación (*"la IA propone, la humana dispone"*).
- **Menos clics para decisiones**: dashboards y vistas analíticas listas para presentar (activos críticos, riesgo, obsolescencia).
- **Responsive y accesible**: uso en sala de juntas y en escritorio; tema claro/oscuro, atajos de teclado, navegación por foco.

## Estructura de navegación (sitemap propuesto)

```
APM
├── Inicio · Dashboard
│   ├── KPIs del portafolio (apps, integraciones, tecnologías, alertas)
│   ├── Alertas críticas (vulnerabilidades, EOL, aprobaciones pendientes)
│   └── Accesos rápidos a catálogos y análisis
├── Catálogos
│   ├── Aplicaciones            → lista / detalle / grafo
│   ├── Integraciones           → lista / detalle / grafo
│   ├── Tecnologías             → lista / detalle (versiones, EOL, CVEs)
│   ├── Proveedores y licencias → lista / detalle
│   └── Capacidades de negocio  → mapa de cobertura
├── Análisis
│   ├── Activos críticos
│   ├── Cobertura por capacidad
│   ├── Dependencias e impacto
│   ├── Vulnerabilidades        (ranking, priorización, remediación)
│   ├── Obsolescencia           (EOL/EOS, licencias por vencer)
│   └── Solapamientos y duplicados
├── IA agéntica
│   ├── Propuestas pendientes   (bandeja de aprobación)
│   ├── Historial de agentes    (acciones, origen, trazabilidad)
│   ├── Generador de arquitecturas
│   └── Chat del portafolio
├── Gobernanza
│   ├── Aprobaciones
│   ├── Auditoría y cambios
│   └── Informes (incl. exportar PDF)
└── Configuración
    ├── Usuarios y roles (RBAC)
    ├── Reglas de criticidad
    ├── Fuentes de ingesta (CMDB, nube, SBOM, repos)
    └── Conexiones (ITSM, notificaciones, SSO)
```

## Pantallas clave

| Pantalla | Contenido |
| --- | --- |
| **Dashboard** | Resumen ejecutivo del portafolio en tarjetas y gráficas; ideal para reuniones de avance. |
| **Listado de catálogo** | Tabla con columnas configurables, búsqueda, filtros combinables y **vistas guardadas** (p. ej. "activos críticos"). |
| **Detalle de aplicación** | Pestañas: General, Tecnología, Integraciones, Vulnerabilidades, Arquitectura, Historial. |
| **Vista grafo** | Grafo de dependencias apps ↔ integraciones ↔ tecnologías ↔ capacidades, con pan/zoom y filtrado por riesgo. |
| **Centro de vulnerabilidades** | Ranking CVE por severidad × criticidad de la aplicación, con propuestas de remediación y tickets. |
| **Bandeja de propuestas IA** | Lista de cambios propuestos por agentes con comparativa (*diff*), origen y acción Aprobar / Rechazar / Editar. |
| **Chat del portafolio** | Consultas en lenguaje natural con respuestas citando fuentes del catálogo. |

## Patrones de interacción con la IA agéntica

- **Tarjeta de propuesta**: muestra qué cambió (antes → después), quién/qué lo generó (modelo, prompt, versión), confianza y estado (`Borrador` → `En revisión` → `Aprobada` / `Rechazada`).
- **Aprobaciones**: un solo clic desde la bandeja, con registro obligatorio opcional de comentario; los cambios se publican solo tras aprobación.
- **Chat con fuentes**: cada respuesta enlaza los registros del catálogo citados (permitir verificación).
- **Notificaciones**: avisos de CVEs nuevos, EOL próximas, propuestas pendientes y contratos por vencer (por correo y en la app).

## Roles y vistas por rol

- **Arquitecto/a TI**: acceso completo a catálogos, análisis e IA; aprueba propuestas.
- **Analista de seguridad**: prioriza vulnerabilidades y obsolescencia.
- **Dirección**: dashboard y análisis en modo lectura, informes exportables.
- **Equipos de aplicación**: editan sus aplicaciones; ven notificaciones que les afectan.

## Relación con el portal de documentación

El APM enlaza y abre los **artefactos publicados** en el portal de documentación (diagramas ArchiMate, PDF de avance) desde la vista de Arquitectura de cada aplicación, reutilizando el contenido ya publicado por CI/CD.