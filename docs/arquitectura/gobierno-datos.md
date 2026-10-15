---
title: Gobierno y procedencia de datos
description: Fuentes autoritativas, procedencia por atributo y flujo de registro descentralizado con aprobación de Gobierno de Arquitectura.
---

## Enfoque

El APM sigue un modelo **híbrido**: es registro maestro propio para los datos de arquitectura y estrategia, e **ingiere** el resto desde sus fuentes autoritativas. El registro es **descentralizado** — los equipos de aplicación mantienen sus propios Fact Sheets — pero los cambios a atributos con impacto estratégico pasan por la aprobación de **Gobierno de Arquitectura**. Esta página complementa [Modelo de datos (metamodelo)](../modelo-datos/): allí se definen las entidades y atributos; aquí, quién es dueño de cada dato y cómo se aprueba un cambio.

## Fuentes y autoridad

| Fuente | Qué gobierna | Mecanismo |
|---|---|---|
| **APM (registro maestro)** | Aplicaciones, integraciones, capacidades de negocio, relaciones entre Fact Sheets, decisiones de arquitectura (criticidad, TIME, ciclo de vida) | Registro directo por los equipos de aplicación, sujeto a aprobación de Gobierno de Arquitectura para atributos gobernados (ver [flujo de registro](#flujo-de-registro-descentralizado)) |
| **Repositorios Git / CI-CD / K8s** | Código fuente, dependencias empaquetadas, stacks, contenedores, manifiestos de despliegue y endpoints | Descubrimiento continuo upstream mediante el **Agente 1 (Code-to-Catalog)**; genera evidencia técnica primaria |
| **Contratos y TDRs (PDF/Word)** | Proveedores adjudicados, licencias, costos, vigencia contractual, garantías y SLAs | Descubrimiento continuo upstream mediante el **Agente 2 (Dark Data Miner)**; extrae Dark Data no estructurado |
| **CMDB** | Infraestructura (servidores, contenedores, CIs y su topología) | Conector / ingesta periódica; el APM nunca edita estos atributos, solo los muestra y los referencia (ver [Identidad y reconciliación](#identidad-y-reconciliación-con-cmdb)) |
| **Feeds CVE / EOL** | Vulnerabilidades (CVE) y fechas de fin de vida (EOL) / fin de soporte (EOS) de componentes tecnológicos | Ingesta automática — **propuesta a validar**: NVD para CVE, endoflife.date para EOL/EOS |
| **Excel** | Catálogos actuales de aplicaciones, integraciones y tecnologías | **Solo importación inicial única** (ver [Migración del Excel](#migración-del-excel)); después de la migración deja de ser fuente y se retira |

**Regla de autoridad única:** cada atributo tiene exactamente una fuente autoritativa en un momento dado. Ningún atributo se edita simultáneamente desde dos sistemas: los atributos de infraestructura solo se editan en la CMDB (el APM los ingiere de solo lectura), los atributos de CVE/EOL solo se editan en el feed de origen, y todo lo demás se edita en el APM una vez completada la migración del Excel o la reconciliación del descubrimiento continuo.

## Procedencia por atributo

Cada valor almacenado en el APM registra su procedencia, para poder auditar y confiar en el dato:

| Campo de procedencia | Descripción |
|---|---|
| Fuente | Sistema, conector o agente descubridor (`APM manual`, `Excel migrado`, `CMDB`, `Feeds CVE/EOL`, `Agente Code-to-Catalog`, `Agente Dark Data Miner`, `Reconciliador Semántico`) |
| Método | `manual` (escrito por persona), `importación` (carga inicial Excel), `ingesta` (sincronización CMDB/feeds), `descubrimiento técnico`, `minería contractual`, `hipótesis reconciliada` |
| Evidencia primaria | Cita directa auditable: archivo, hash de commit y línea de código (`repo:path#L10-25`), o documento, página y cláusula contractual (`TDR-2024.pdf, pág. 12, cl. 5`) |
| Fecha | Momento exacto en que se registró o actualizó el valor |
| Autor | Persona, conector o agente que generó el valor |
| Confianza | *Score* heurístico ($0.0$ a $1.0$) calculado por el Reconciliador Semántico; no es una probabilidad hasta calibrarse contra un conjunto verificado (ver [IA agéntica y funcionalidades](../ia-agentes/)) |
| Estado de validación | `Publicado automáticamente (determinista)`, `Pendiente (micro-nudge)`, `Validado por dueño técnico`, `En revisión de gobierno`, `Aprobado por Gobierno de Arquitectura`, `Ingerido (solo lectura)` |

Esto conecta directamente con el ciclo de datos con IA agéntica descrito en [Arquitectura del sistema](../#ciclo-de-datos-con-ia-agéntica) y en [IA agéntica y funcionalidades](../ia-agentes/): un agente puede **proponer** un valor (por ejemplo, al descubrir o reconciliar una aplicación), pero ese valor queda como **borrador auditado con origen, evidencia primaria y confianza**, y no se publica hasta que una persona lo valida — *"la IA propone, la persona dispone"*. La única excepción son los atributos técnicos obtenidos por parsing determinista, que se publican automáticamente con su procedencia (ver la regla siguiente). El campo de procedencia es el mecanismo con el que ese principio se registra dato a dato.

### Descubrimiento continuo y precedencia

Los agentes descubridores vuelven a escanear las fuentes de forma continua. Para que un escaneo nuevo no destruya trabajo humano, la autoridad se decide por la procedencia del valor vigente:

| Valor vigente | Llega evidencia nueva que lo contradice | Resultado |
|---|---|---|
| Validado por una persona (dueño técnico o Gobierno de Arquitectura) | Sí | **No se sobrescribe**: se crea una propuesta de discrepancia con ambos valores y su evidencia, que decide el responsable |
| Publicado automáticamente (parsing determinista) | Sí | Se actualiza con la nueva procedencia, salvo que una persona lo haya corregido antes |
| Pendiente o sin valor | — | La nueva evidencia actualiza la propuesta en curso |

**Aprobación por nivel de riesgo:**

- **Publicación automática con procedencia**: atributos técnicos extraídos de forma determinista (stack, versiones, dependencias, endpoints). Son trazables a su evidencia y reversibles por el responsable.
- **Aprobación de Gobierno de Arquitectura**: atributos críticos para el negocio (dueño, criticidad, costo, datos contractuales) y la vinculación de candidatos huérfanos, aunque provengan de una hipótesis de alta confianza.

## Flujo de registro descentralizado

![Flujo de registro descentralizado](./diagramas/gobierno-datos.svg)

### Estados

Un Fact Sheet nuevo, o una propuesta de cambio sobre uno existente, recorre estos estados:

`Borrador` → `En revisión` → `Aprobado` (publicado) / `Rechazado` (con motivo) / `Devuelto` (con observaciones, vuelve a `Borrador`)

### Reglas por clase de atributo

Las tres clases de atributo definidas en [Modelo de datos › Atributos](../modelo-datos/#clasificación-de-gobierno-de-los-atributos-propuesta) determinan cómo se aplica un cambio:

- **Gobernado**: un cambio sobre un atributo gobernado de un Fact Sheet **ya publicado** genera una **solicitud de cambio**. El Fact Sheet publicado sigue vigente y visible tal cual está hasta que Gobierno de Arquitectura aprueba la solicitud; solo entonces se actualiza la versión publicada. El alta y la baja de Fact Sheets también son cambios gobernados y siguen el mismo flujo de aprobación.
- **Operativo**: el responsable del Fact Sheet lo edita directamente, sin pasar por revisión previa. El cambio queda auditado (quién, cuándo, valor anterior) para trazabilidad, pero no bloquea la publicación.
- **Ingerido**: de solo lectura para cualquier persona en el APM; solo cambia cuando la fuente autoritativa (CMDB o feed externo) lo actualiza en la siguiente sincronización.

### Roles

- **Equipo de aplicación**: registra y mantiene sus Fact Sheets (rol Responsible); envía a revisión los borradores y las solicitudes de cambio.
- **Gobierno de Arquitectura**: revisa y decide (Accountable del proceso de aprobación); puede aprobar, rechazar con motivo o devolver con observaciones.
- **Arquitecto/a responsable**: puede coincidir con Gobierno de Arquitectura o actuar como enlace entre el equipo de aplicación y el comité de gobierno, según cómo se organice el equipo.

### Relación con el Quality Seal de LeanIX

LeanIX v4 tiene un mecanismo **verificado** llamado *Quality Seal*: un sello que otorga el rol Responsible/Accountable de un Fact Sheet, y que se **rompe automáticamente** si otra persona lo edita después. Es una marca de calidad retrospectiva, no bloquea la edición ni la visibilidad del Fact Sheet.

El flujo de aprobación de esta página es distinto y complementario: la aprobación de Gobierno de Arquitectura es un **gate previo a la publicación** de un cambio gobernado — mientras la solicitud está pendiente, el dato publicado no cambia. Se puede adoptar el Quality Seal como indicador adicional de calidad sobre un Fact Sheet ya publicado, sin que reemplace este gate de gobierno.

### SLA de revisión y carga de revisión

:::caution[Propuesta inicial, a calibrar en el piloto]
Los plazos y métricas de esta sección son una **propuesta inicial**. Se ajustan con los datos medidos en el piloto de calibración y se acuerdan con el equipo de Gobierno de Arquitectura.
:::

| Elemento en cola | Plazo propuesto para decidir | Al vencer |
|---|---|---|
| Solicitud de cambio sobre un atributo gobernado | 5 días hábiles | Se escala al arquitecto responsable, igual que un micro-nudge vencido (riesgo 14 en [Riesgos de la IA](../arquitectura-solucion/#riesgos-de-la-ia-y-contramedidas)) |
| Candidato huérfano o conflicto de reconciliación | 5 días hábiles | Se escala al arquitecto responsable, que decide o reasigna |
| Lote de migración del Excel | Por tanda priorizada, no por elemento | Se replanifica la tanda en la siguiente sesión de gobierno |

Para que la revisión no se convierta en el nuevo cuello de botella, se miden desde el inicio estas métricas de carga:

| Métrica | Qué indica |
|---|---|
| Tamaño de la cola (por tipo: solicitudes, huérfanos, conflictos, migración) | Si entra más trabajo del que se resuelve |
| Antigüedad de los elementos en cola (p50 y p95) | Si el SLA se cumple para la mayoría y para los casos lentos |
| Elementos resueltos por revisor y semana | Capacidad real del equipo y reparto de la carga |
| Tasa de aprobación y de rechazo (y de devolución) | Calidad de las propuestas; una aprobación cercana al 100 % sin ediciones puede indicar sesgo de automatización |
| Escalamientos por SLA vencido | Puntos donde el plazo o la capacidad no alcanzan |

Si la cola crece de forma sostenida, se ajustan primero los umbrales de publicación automática y la priorización de lotes, antes que el número de revisores.

### Pendiente de definir

- **Notificaciones**: canales y eventos exactos (¿correo?, ¿en la app?, ¿ambos?) para avisar de una solicitud pendiente, una decisión o un cambio ingerido relevante (ver también el componente "Notificaciones y Aprobaciones" en [Composición de la plataforma](../#composición-de-la-plataforma)).

## Migración del Excel

Pasos propuestos para la migración única del Excel al APM:

1. **Perfilado y limpieza**: revisar los archivos Excel actuales de aplicaciones, integraciones y tecnologías; detectar columnas vacías, formatos inconsistentes y valores fuera de catálogo.
2. **Mapeo columna → atributo del metamodelo**: cada columna del Excel se mapea a un atributo del modelo de datos, usando las tablas de [Modelo de datos › Atributos específicos por tipo](../modelo-datos/#atributos-específicos-por-tipo) como referencia (esas tablas ya indican, para cada atributo, el campo orientativo de [Catálogos del portafolio](../catalogos/) del que proviene).
3. **Reconciliación de duplicados e identidad**: antes de cargar, agrupar filas que representen el mismo Fact Sheet en distintas fuentes o pestañas, usando alias y códigos existentes (ver [Identidad y reconciliación](#identidad-y-reconciliación-con-cmdb)).
4. **Carga inicial**: dos opciones, con distinto costo y riesgo:

   | Opción | Ventaja | Riesgo |
   |---|---|---|
   | Cargar todo como `Borrador` | Simple, un solo tipo de estado inicial | Genera un volumen grande de borradores pendientes de revisión, puede saturar a Gobierno de Arquitectura |
   | Cargar como `Aprobado por migración` | El portafolio queda utilizable de inmediato, sin cola de revisión | Publica datos del Excel sin que nadie los haya validado contra el metamodelo nuevo; riesgo de arrastrar errores previos como si fueran datos gobernados |

   **Recomendación**: cargar por lotes como `Borrador`, agrupados por dominio o equipo, y que Gobierno de Arquitectura los revise en tandas priorizadas (por ejemplo, aplicaciones críticas primero) en vez de una revisión masiva simultánea. Esto conserva el control de calidad del flujo de aprobación sin bloquear la disponibilidad del resto del portafolio, que puede consultarse igual mientras está en borrador.
5. **Congelar y retirar el Excel**: una vez migrados y revisados los datos, el Excel pasa a solo lectura como archivo histórico y se retira como fuente operativa; no vuelve a sincronizarse con el APM.

## Identidad y reconciliación con CMDB

- Cada Fact Sheet tiene un **identificador estable propio del APM** (UUID, ver [Modelo de datos › Atributos base](../modelo-datos/#atributos-base-comunes-a-todo-fact-sheet)), que no depende de ningún sistema externo.
- Además, guarda **claves externas** hacia los sistemas de origen: alias/códigos de reconciliación (para el Excel migrado) y el **CI de CMDB** (para IT Components de infraestructura).
- **Reglas de matching** (propuesta, a validar con el equipo de CMDB): cruce por CI de CMDB cuando existe; si no, por alias/código normalizado; si no, por nombre normalizado + tipo de Fact Sheet como último recurso, siempre marcado de menor confianza.
- **Conflictos** (por ejemplo, dos CIs de CMDB que podrían corresponder a la misma aplicación, o un alias que matchea más de un Fact Sheet) no se resuelven automáticamente: se envían a una **cola de revisión humana** para que un arquitecto decida la reconciliación correcta.

Páginas relacionadas: [Modelo de datos (metamodelo)](../modelo-datos/), [Catálogos del portafolio](../catalogos/), [IA agéntica y funcionalidades](../ia-agentes/).
