---
title: Modelo de datos (metamodelo)
description: Metamodelo conceptual del APM, basado en SAP LeanIX Meta Model v4 y expresado en ArchiMate 3.2.
---

## Enfoque

El modelo de datos del APM toma como base el **SAP LeanIX Meta Model v4** (tipos de *Fact Sheet* y sus relaciones) y lo expresa en notación **ArchiMate 3.2**, consistente con el resto de diagramas de este portal.

El APM es un **registro maestro híbrido**: es dueño y fuente de verdad de la estrategia (mantener/invertir/contener/retirar), la criticidad, las capacidades de negocio, las relaciones entre elementos y las decisiones de arquitectura. El resto de los datos (inventario técnico, versiones, vulnerabilidades, etc.) se **ingiere de fuentes externas** con un proceso de reconciliación y procedencia por atributo (ver [Atributos](#atributos) más abajo y [Gobierno y procedencia de datos](./gobierno-datos/)).

> **Nota importante:** SAP LeanIX **no publica un mapeo oficial** de tipos de Fact Sheet a elementos ArchiMate. La correspondencia presentada en esta página es una **propuesta de este proyecto**, construida a partir de la semántica de cada tipo de Fact Sheet y las definiciones del estándar ArchiMate 3.2. Debe validarse contra un workspace real de LeanIX o su documentación oficial antes de tomarse como definitiva.

## Diagrama

![Metamodelo del APM](./diagramas/metamodelo.svg)

El diagrama muestra un subconjunto ilustrativo de tipos y relaciones; la tabla completa de tipos y la tabla completa de relaciones están más abajo.

## Tabla de tipos: Fact Sheet → ArchiMate

| Fact Sheet (LeanIX v4) | Elemento ArchiMate | Capa | Catálogo actual que lo cubre | Subtipos |
|---|---|---|---|---|
| Application | Application Component | Aplicación | Aplicaciones | por confirmar |
| Interface | Application Interface (+ relación *Flow* entre aplicaciones) | Aplicación | Integraciones | por confirmar |
| Data Object | Data Object | Aplicación | Integraciones / Datos (extendido) | por confirmar |
| IT Component | Software → System Software; Hardware → Device/Node; Service (SaaS/PaaS/IaaS) → Technology Service | Tecnología | Tecnologías y componentes | Software, Hardware, Service (SaaS/PaaS/IaaS) — probable, por confirmar |
| Tech Category | Grouping | Compuesto | Tecnologías | por confirmar |
| Provider | Business Actor | Negocio | Proveedores (extendido) | por confirmar |
| Business Capability | Capability | Estrategia | Capacidades (extendido) | por confirmar |
| Business Context | Process → Business Process; Value Stream → Value Stream; Business Product → Product; Customer Journey → Value Stream | Negocio/Estrategia | — | Business Product, Customer Journey, Process, Value Stream |
| Organization | Business Actor | Negocio | Datos generales (propietario, equipo) | por confirmar |
| Objective | Goal | Motivación | — | por confirmar |
| Initiative | Work Package | Implementación y migración | Iniciativas (extendido) | Idea, Program, Project, Epic |
| Platform | Grouping | Compuesto | — | por confirmar |

Notas sobre la tabla:

- **IT Component** e **Interface** no tienen una correspondencia 1 a 1: el elemento ArchiMate depende del subtipo (IT Component) o se acompaña de una relación adicional (Interface, con *Flow* entre las aplicaciones proveedora y consumidora).
- **Business Context** agrupa cuatro subtipos de LeanIX (Business Product, Customer Journey, Process, Value Stream) que se reparten entre tres tipos de elemento ArchiMate distintos (Business Process, Value Stream, Product), porque representan conceptos de capas diferentes (proceso operativo vs. propuesta de valor vs. producto).
- Los subtipos marcados "por confirmar" no se pudieron verificar contra fuentes primarias de LeanIX (ver [Fuentes y límites](#fuentes-y-límites)).

## Tabla de relaciones: LeanIX → ArchiMate

| Relación LeanIX | Relación ArchiMate | Atributos de la relación |
|---|---|---|
| Application → Business Capability | Realization | functional fit |
| Application → Business Context | Serving | — |
| Application compone su Interface proveedora | Composition | — |
| Interface → aplicación consumidora | Serving (y *Flow* proveedora→consumidora — **por validar**) | — |
| Application / Interface → Data Object | Access | — |
| IT Component → Application | Serving | technical fit, costo |
| Tech Category → IT Component | Aggregation | — |
| Provider → IT Component | Association | — |
| Application → Organization (uso) | Serving | — |
| Application → Organization (propiedad/responsabilidad) | Association | — |
| Initiative → elementos afectados | Association | — |
| Initiative → Objective | Influence | — |
| Business Capability → Objective | Influence | — |
| Platform → Application / IT Component / Business Capability | Aggregation | — |
| Jerarquías padre/hijo (Business Capability, Application, Organization, Business Context, IT Component) | Composition | — |
| Business Capability → Value Stream | Serving | — |
| Business Product → Application | Aggregation (**por validar**) | — |

Estas parejas se contrastaron contra las reglas de derivación de ArchiMate 3.2: Realization e Influence son las relaciones designadas por el estándar para cruzar hacia las capas de Estrategia, Motivación e Implementación (por eso Application → Business Capability usa Realization, e Initiative/Business Capability → Objective usan Influence), Association es válida entre cualquier par de elementos, y Grouping puede agregar elementos de cualquier capa. Business Capability → Value Stream usa Serving porque una capacidad (Estrategia) sirve/habilita el flujo de valor (Estrategia); ambas están en la capa de Estrategia y Serving es la relación de dependencia que ArchiMate usa para expresar que un elemento presta servicio a otro. Las parejas marcadas **por validar** son:

- *Interface → aplicación consumidora (Flow)*: el Flow entre dos elementos estructurales (Application Interface y Application Component) es una práctica común en herramientas de modelado, pero no se pudo confirmar contra la tabla normativa del Apéndice B de la especificación (bloqueada por autenticación al momento de esta investigación).
- *Business Product → Application (Aggregation)*: se modela así porque un producto de negocio (Business Context / Business Product, capa de Estrategia) suele agregar las aplicaciones que lo materializan, pero LeanIX no documenta esta relación de forma explícita en su Meta Model v4 público; es una propuesta de este proyecto para no dejar sin relaciones a Business Product en el diagrama.

Si una revisión posterior encuentra una pareja incompatible, se debe corregir aquí y regenerar el diagrama en vez de forzar una relación no soportada por el estándar.

## Atributos estándar verificados

Estos aspectos transversales de LeanIX se confirmaron contra documentación oficial de SAP y del modelo TIME de Gartner:

- **Ciclo de vida**: fases `plan` → `phaseIn` → `active` → `phaseOut` → `endOfLife`, cada una con su propia fecha de inicio.
- **TIME** (Tolerate / Invest / Migrate / Eliminate): se deriva de cruzar *functional fit* × *technical fit* de una aplicación (matriz de racionalización del portafolio).
- **Quality Seal**: sello de aprobación otorgado por el rol Responsible/Accountable de un Fact Sheet; se rompe automáticamente si otra persona edita el Fact Sheet después del sello.
- **Completion score**: porcentaje de completitud de un Fact Sheet, configurable por tipo y por campo.

El conjunto completo de atributos por entidad, sus escalas y su clasificación de gobierno se definen en [Atributos](#atributos), más abajo. El modelo de procedencia y fuente autoritativa por atributo se define en [Gobierno y procedencia de datos](./gobierno-datos/).

## Extensiones propias del APM

Estas capacidades están fuera del metamodelo estándar de LeanIX:

- Vulnerabilidades (CVE) vinculadas a la versión específica de un IT Component (atributos en [Atributos › IT Component](#it-component); procedencia en [Gobierno y procedencia de datos](./gobierno-datos/)).
- Calendario de fin de vida (EOL) y fin de soporte (EOS).
- Licencias y su estado.
- Procedencia y fuente autoritativa por atributo (qué sistema es dueño de cada dato y cómo se reconcilia) — ver [Gobierno y procedencia de datos](./gobierno-datos/).

## Atributos

Esta sección detalla los atributos de cada tipo de Fact Sheet, sus escalas y su clasificación de gobierno. Es un modelo propuesto por este proyecto a partir de la semántica pública de LeanIX v4; los puntos no verificados están marcados explícitamente.

### Clasificación de gobierno de los atributos (propuesta)

Cada atributo se clasifica en una de tres categorías, para saber quién puede cambiarlo y bajo qué control. **Esta clasificación es una propuesta a confirmar con Gobierno de Arquitectura** antes de implementarse; las tablas de esta página ya la aplican como punto de partida.

| Clase | Quién edita | Control | Ejemplos |
|---|---|---|---|
| **Gobernado** | Equipo de aplicación propone el cambio | Requiere aprobación de Gobierno de Arquitectura antes de publicarse (ver [flujo de registro](./gobierno-datos/#flujo-de-registro-descentralizado)) | Criticidad de negocio, TIME, ciclo de vida, relaciones con capacidades de negocio, responsable Accountable, alta/baja de Fact Sheets |
| **Operativo** | Responsable del Fact Sheet | Se edita directamente, sin aprobación previa; queda auditado (quién, cuándo, valor anterior) | Descripción, datos de contacto, URL, etiquetas, campos de detalle técnico sin impacto estratégico |
| **Ingerido** | Nadie en el APM (solo lectura) | Se sincroniza desde la fuente autoritativa (CMDB o feeds externos); un usuario no puede editarlo a mano | Inventario de infraestructura desde CMDB, CVE y fechas EOL/EOS desde feeds externos |

Dos matices sobre "ingerido":

- Algunos campos son de solo lectura porque los **calcula la propia plataforma** (p. ej. TIME derivado, completitud, fechas de creación/actualización), no porque vengan de un sistema externo. Se marcan igual como ingerido/calculado en las tablas siguientes, con la aclaración "(calculado)".
- Si en el futuro se activa el descubrimiento automático de inventario técnico (ver "Descubrimiento continuo" en [IA agéntica y funcionalidades](../ia-agentes/)), algunos atributos hoy operativos (p. ej. versión de un IT Component) podrían pasar a ingeridos; se marca esa posibilidad donde aplica.

### Atributos base (comunes a todo Fact Sheet)

| Atributo | Descripción | Clase |
|---|---|---|
| ID estable (UUID) | Identificador único del Fact Sheet, asignado por el APM al crearlo; nunca cambia y es la clave de reconciliación con Excel/CMDB | Gobernado (se asigna al dar de alta) |
| Nombre | Nombre visible del Fact Sheet | Operativo |
| Descripción | Texto libre descriptivo | Operativo |
| Subtipo | Subtipo dentro del tipo de Fact Sheet (p. ej. Business Product dentro de Business Context) | Gobernado |
| Padre (jerarquía) | Fact Sheet padre en la jerarquía del tipo (p. ej. capacidad padre) | Gobernado |
| Ciclo de vida | Fase actual (`plan`/`phaseIn`/`active`/`phaseOut`/`endOfLife`) y fecha de cada fase | Gobernado |
| Responsable (Responsible) | Persona/equipo que mantiene el Fact Sheet al día | Operativo |
| Responsable último (Accountable) | Persona que responde por el Fact Sheet ante Gobierno de Arquitectura | Gobernado |
| Observadores | Personas que solo reciben notificaciones | Operativo |
| Etiquetas | Etiquetas libres de clasificación | Operativo |
| Estado de gobierno | `Borrador` / `En revisión` / `Aprobado` / `Rechazado` / `Devuelto` (ver [flujo de registro](./gobierno-datos/#flujo-de-registro-descentralizado)) | Ingerido (calculado por el flujo de aprobación) |
| Completitud | Porcentaje de campos obligatorios completos (Completion score) | Ingerido (calculado) |
| Fecha de creación / actualización | Metadatos de auditoría | Ingerido (calculado) |

### Atributos específicos por tipo

Cada tabla incluye, cuando aplica, el campo orientativo de [Catálogos del portafolio](./catalogos/) donde hoy vive ese dato en Excel/CMDB.

#### Application

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Criticidad de negocio | Gobernado | Catálogo Aplicaciones → Clasificación: criticidad |
| Functional fit | Gobernado | — (nuevo; insumo de TIME) |
| Technical fit | Gobernado | — (nuevo; insumo de TIME) |
| TIME (derivado) | Ingerido (calculado de functional × technical fit) | Catálogo Aplicaciones → Estrategia (mantener/invertir/contener/retirar) |
| Alias / códigos de reconciliación | Operativo (clave para identidad, ver [Identidad y reconciliación](./gobierno-datos/#identidad-y-reconciliación-con-cmdb)) | — (nuevo; no existe en Excel hoy) |
| URL | Operativo | — (nuevo) |
| Usuarios estimados | Operativo | Catálogo Aplicaciones → Stack: usuarios |
| Capacidad de negocio soportada (relación) | Gobernado | Catálogo Aplicaciones → Clasificación: capacidad de negocio |
| Equipo / propietario de negocio / arquitecto responsable | Operativo (Responsible) / Gobernado (Accountable) | Catálogo Aplicaciones → Datos generales |

#### Interface

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Proveedor (aplicación origen) | Operativo | Catálogo Integraciones → extremos origen/destino |
| Consumidores (aplicaciones destino) | Operativo | Catálogo Integraciones → extremos origen/destino |
| Protocolo (REST, SOAP, mensajería, ficheros) | Operativo | Catálogo Integraciones → protocolo |
| Frecuencia | Operativo | — (nuevo) |
| Dirección (unidireccional/bidireccional) | Operativo | — (nuevo) |
| Sensibilidad de los datos intercambiados | Gobernado (impacto de cumplimiento) | Catálogo Integraciones → sensibilidad de los datos |
| SLA | Operativo (propuesta: revisar si debe ser gobernado) | Catálogo Integraciones → SLA |

#### IT Component

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Fabricante / Provider | Operativo (pasaría a ingerido si se activa descubrimiento automático) | Catálogo Tecnologías → (implícito en inventario) |
| Versión | Operativo (ídem) | Catálogo Tecnologías → versiones instaladas |
| Fecha EOL / EOS | Ingerido (feed externo — propuesta: endoflife.date, a confirmar) | Catálogo Tecnologías → fechas EOL/EOS |
| Licencia y su estado | Operativo | Catálogo Tecnologías → licencias y su estado |
| Identificador CPE / purl (para cruzar CVEs) | Operativo | — (nuevo; necesario para correlación de vulnerabilidades) |
| CI de CMDB (clave externa) | Ingerido (solo lectura, viene de CMDB) | — (nuevo; ver [Identidad y reconciliación](./gobierno-datos/#identidad-y-reconciliación-con-cmdb)) |

#### Data Object

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Clasificación de sensibilidad | Gobernado (impacto de cumplimiento) | — (extensión de Datos en catálogos extendidos) |
| Dominio de datos | Operativo | — (extensión de Datos en catálogos extendidos) |

#### Business Capability

Nivel, madurez (actual/objetivo) e importancia estratégica son campos **verificados** del Meta Model v4 público de LeanIX.

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Nivel (posición en el mapa de capacidades) | Gobernado | Catálogo Capacidades de negocio (extendido) |
| Madurez actual | Gobernado | Catálogo Capacidades de negocio (extendido) |
| Madurez objetivo | Gobernado | Catálogo Capacidades de negocio (extendido) |
| Importancia estratégica | Gobernado | Catálogo Capacidades de negocio (extendido) |

#### Initiative

| Atributo | Clase | Campo orientativo en catálogos |
|---|---|---|
| Estado (Idea/Program/Project/Epic y su avance) | Operativo | Catálogo Iniciativas y proyectos (extendido) |
| Fechas (inicio/fin planificadas y reales) | Operativo | Catálogo Iniciativas y proyectos (extendido) |
| Presupuesto | Operativo (propuesta: revisar si debe ser gobernado por su impacto financiero) | Catálogo Iniciativas y proyectos (extendido) |

#### Provider, Organization, Objective, Platform

Estos cuatro tipos reutilizan los atributos base y agregan, como mínimo:

| Tipo | Atributos específicos | Clase |
|---|---|---|
| Provider | Contacto comercial; servicios/tecnologías que provee (relación) | Operativo |
| Organization | Tipo (unidad de negocio, equipo, área) | Operativo |
| Objective | Indicador de éxito asociado; horizonte temporal | Gobernado (define dirección estratégica) |
| Platform | Dominio tecnológico; componentes agregados (relación) | Gobernado (agrupa activos gobernados) |

### Escalas

| Escala | Valores | Estado |
|---|---|---|
| Ciclo de vida | `plan` → `phaseIn` → `active` → `phaseOut` → `endOfLife` | Verificado (SAP LeanIX docs) |
| TIME | Tolerate / Invest / Migrate / Eliminate, derivado de functional fit × technical fit | Verificado (SAP LeanIX docs, modelo TIME de Gartner) |
| Criticidad de negocio | `missionCritical`, `businessCritical`, `businessOperational`, `administrativeService` | **No verificado — valores habituales de LeanIX, a confirmar contra un workspace real** |
| Functional fit | `unreasonable`, `insufficient`, `appropriate`, `perfect` | **No verificado — a confirmar** |
| Technical fit | `inappropriate`, `unreasonable`, `adequate`, `fullyAppropriate` | **No verificado — a confirmar** |

**Recomendación:** modelar estas escalas como datos configurables (tabla de valores permitidos por atributo, con orden y color), no como enumeraciones fijas en código. Esto permite ajustar las tres escalas no verificadas sin una migración cuando se confirmen contra la fuente primaria, y permite a Gobierno de Arquitectura adaptar los valores a la organización.

## Fuentes y límites

- [TIME model — SAP LeanIX docs](https://help.sap.com/docs/leanix/ea/time)
- [Quality Seal — SAP LeanIX docs](https://help.sap.com/docs/leanix/ea/quality-seal)
- [Gartner TIME model — LeanIX wiki](https://www.leanix.net/en/wiki/apm/gartner-time-model)
- [ArchiMate 3.2 Specification — The Open Group](https://pubs.opengroup.org/architecture/archimate32-doc/)

**Límite de la investigación:** la lista completa de tipos y subtipos del Meta Model v4, así como las escalas exactas de criticidad y de *fit* (functional/technical), no pudieron verificarse contra fuentes primarias porque la documentación de LeanIX se renderiza con JavaScript y no fue accesible para extracción automática en esta iteración. Estos puntos deben confirmarse contra un workspace real de LeanIX o su documentación oficial antes de considerarse definitivos.

Páginas relacionadas: [Catálogos del portafolio](./catalogos/), [Gobierno y procedencia de datos](./gobierno-datos/).
