---
title: Arquitectura de solución y despliegue
description: Propuesta de despliegue del APM en Azure, capa de IA agéntica, recuperación de contexto, ingesta y operación segura.
---

:::note[Propuesta]
Esta página describe una **arquitectura propuesta**, no una implementación existente. Los servicios y modelos nombrados son candidatos sujetos a validación (marcados "por validar") y a las decisiones de la fase correspondiente del [roadmap](./roadmap/).
:::

## Vista rápida

Resumen a muy alto nivel de cómo se usa el APM, cómo actúa la IA y de dónde llegan los datos. El detalle está en las secciones siguientes.

```text
 USO
 ┌────────────────────────────┐
 │ Arquitectos y equipos      │   portal web · chat · Teams (opcional)
 └─────────────┬──────────────┘
               │ inicio de sesión (Entra ID)
               ▼
 ┌────────────────────────────┐   herramientas   ┌──────────────────────┐
 │ API del APM (App Service)  │◄─────────────────┤ Agentes de IA        │
 │ única puerta de entrada    │                  │ (Azure OpenAI)       │
 │ para personas y agentes    ├─────────────────►│ responden con citas  │
 └──────┬──────────────▲──────┘     contexto     └──────────────────────┘
        │              │         (con permisos)
        ▼              │
 ┌──────────────┐   ┌──┴───────────┐
 │ Azure SQL    ├──►│ AI Search    │   índice sin datos Restringidos
 │ registro     │   │ búsqueda con │
 │ maestro      │   │ permisos     │
 └──────▲───────┘   └──────────────┘
        │ cada dato llega con su procedencia
 ┌──────┴─────────────────────────────┐
 │ INGESTA (Azure Functions)          │
 │ Excel · CMDB · CVE · EOL · SBOM    │
 └────────────────────────────────────┘
```

- **Uso:** las personas entran con su cuenta corporativa y trabajan siempre a través de la API del APM.
- **IA:** los agentes no tocan la base de datos. Piden contexto a la API, que solo les entrega lo que la persona puede ver, y responden citando los registros usados.
- **Ingesta:** los datos externos entran por funciones programadas y cada valor guarda su procedencia (fuente, método, fecha).

Cuando un agente sugiere un cambio, este nunca se publica directamente:

```text
Agente sugiere ──► Borrador ──► Gobierno de Arquitectura aprueba ──► Publicado
                                      │
                                      └──► Rechaza o devuelve
```

## Funcionalidades

Cómo responde el sistema en las funcionalidades principales. Cada flujo pasa por la API del APM y respeta los permisos de quien consulta. La lista completa está en [IA agéntica y funcionalidades](./ia-agentes/).

### Chat del portafolio

```text
"¿Qué aplicaciones críticas usan PostgreSQL 11?"

 Persona ──► Chat ──► Agente ──► API: búsqueda + filtros (con permisos)
                                   │
                                   ▼
 Persona ◄── Lista de aplicaciones, gráfico y cita a cada Fact Sheet
             (si no hay datos, el chat lo dice; no inventa)
```

### Edición asistida y enriquecimiento

```text
"Registra la aplicación Portal de Clientes"

 Persona ──► Formulario ──► Agente detecta stack, dueños y contacto
                                   │
                                   ▼
                   Borrador con origen y confianza por campo
                                   │
                                   ▼
             Gobierno de Arquitectura ──► Aprueba ──► Publicado
                                      └─► Rechaza o devuelve
```

### Análisis de impacto

```text
"Si retiro el servicio de autenticación, ¿qué se ve afectado?"

 Persona ──► Agente ──► API: recorrido del grafo de dependencias
                                   │
                                   ▼
 Persona ◄── Aplicaciones e integraciones afectadas, por criticidad,
             con la ruta de dependencia de cada una
```

### Vulnerabilidades

```text
 Feed NVD/OSV ──► Ingesta ──► Correlación con la versión del
 (programado)                 IT Component (CPE/purl)
                                   │
                                   ▼
                  Prioridad = CVSS + EPSS + criticidad de la aplicación
                                   │
                                   ▼
 Seguridad ◄── Alerta y ticket sugerido ──► se crea solo si se aprueba
```

### Obsolescencia y alertas

```text
 Feed endoflife.date ──► Ingesta ──► Fechas EOL/EOS por componente
                                   │
                                   ▼
 Equipos ◄── Digest programado: EOL próximas, licencias por vencer,
             cambios pendientes de aprobación
```

### Arquitecturas base y revisión

```text
"Genera la vista de contexto de la aplicación Pagos"

 Persona ──► Agente ──► API: Fact Sheet, relaciones e integraciones
                                   │
                                   ▼
 Persona ◄── Vista ArchiMate/C4 preliminar + hallazgos contra los
             estándares del equipo (consultivo; el arquitecto valida)
```

## Vista de despliegue

![Arquitectura de solución y despliegue](./diagramas/despliegue.svg)

## Componentes

| Capa | Componente | Responsabilidad |
|---|---|---|
| Aplicación | **Azure App Service** | Web y API del APM (OpenAPI). Única vía de lectura/escritura para personas, agentes e ingesta |
| Datos | **Azure SQL Database** | Registro maestro: Fact Sheets, relaciones, procedencia por atributo, estados del flujo de aprobación y bitácora de auditoría (ver [Modelo de datos](./modelo-datos/) y [Gobierno de datos](./gobierno-datos/)) |
| Identidad | **Entra ID** | OIDC/SSO, RBAC/ABAC; identidades administradas (*managed identity* o *service principal*) por agente |
| Secretos | **Key Vault** | Secretos y claves; sin credenciales en el catálogo |
| Red | *Private endpoints* / integración con VNet | Los servicios de datos e IA no se exponen a Internet |
| Observabilidad | **Application Insights / Azure Monitor** | Trazas, métricas y alertas |
| IA | **Azure OpenAI** | Servicio de modelos |
| IA | **Azure AI Foundry Agent Service** (o equivalente, por validar) | Orquestación de agentes |
| IA | **Azure AI Search** | Índice para recuperación de contexto (RAG) |
| Ingesta | **Azure Functions** (temporizador/cola) o Data Factory | Migración, sincronización y feeds |
| Canal opcional | Copilot Studio / Teams (por validar) | Acceso al chat desde herramientas corporativas |

## Capa de IA

### Reglas de actuación de los agentes

- Los agentes **solo actúan a través de la API del APM** (herramientas OpenAPI); nunca escriben directo en la base de datos.
- Cada agente tiene **identidad propia** y **mínimo privilegio**: solo las herramientas y los alcances que su función requiere.
- Toda escritura crea un **Borrador** con procedencia y confianza, que entra a la bandeja de aprobación (estados y roles en [Gobierno de datos](./gobierno-datos/#flujo-de-registro-descentralizado)). Ningún agente publica por sí mismo.
- Un agente opera con los permisos del usuario que lo invoca o con su propia identidad de menor alcance, nunca con la unión de ambos.

### Modelos por rol

| Rol | Uso | Modelo |
|---|---|---|
| Razonamiento / chat | Agentes y chat del portafolio | Modelo de chat/razonamiento de Azure OpenAI (versión por validar) |
| Pequeño | Clasificación y extracción | Modelo pequeño de Azure OpenAI (versión por validar) |
| Embeddings | Indexación y búsqueda semántica | Familia `text-embedding-3` (small/large), listada en el catálogo de Microsoft |

El catálogo de modelos cambia con frecuencia ([Microsoft Learn: modelos de Azure](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure)), por lo que las versiones concretas se eligen con **evals** del propio APM. Reglas: **versión fijada** (*pinning*) por entorno y **compuerta de evals** antes de cualquier actualización de modelo.

### Recuperación de contexto (RAG)

1. Azure AI Search se alimenta desde Azure SQL (indexador con seguimiento de cambios) y genera embeddings.
2. **Recorte de seguridad** (*security trimming*): cada consulta hereda los permisos del usuario y solo recupera lo que ese usuario puede ver.
3. **Filtro por clasificación**: `Restringido` nunca se indexa; `Confidencial` solo se recupera para roles autorizados.
4. La búsqueda se combina con **consultas estructuradas a la API** (por ejemplo, el grafo de dependencias), que la búsqueda semántica no resuelve bien.

## Ingesta

| Fuente | Mecanismo | Fase |
|---|---|---|
| Excel (migración única) | Carga por lotes como `Borrador`; ver [Migración del Excel](./gobierno-datos/#migración-del-excel) | F1 |
| CMDB | Sincronización de solo lectura, por clave de CI | F3 |
| NVD / OSV (CVE) y endoflife.date (EOL) | Función programada; propuesta por validar | F2 |
| SBOM y repositorios | Descubrimiento continuo | F3 |

Toda ingesta registra **procedencia** (fuente, método, fecha, autor). El contenido externo se trata como **no confiable** (defensa contra *prompt injection*): se sanea, nunca se ejecutan instrucciones halladas en los datos y los agentes solo pueden invocar herramientas de una lista permitida.

## Flujos de comportamiento

**1. Pregunta en el chat**

1. La persona se autentica (Entra ID).
2. El agente recupera contexto con recorte de permisos y consultas a la API.
3. Responde con **citas** a los Fact Sheets o fuentes usadas.
4. Se registran pregunta, herramientas invocadas y respuesta.

**2. Sugerencia de cambio a un Fact Sheet**

1. El agente propone el cambio mediante la API.
2. Se crea un Borrador con procedencia y puntaje de confianza.
3. Gobierno de Arquitectura aprueba, rechaza o devuelve.
4. Si se aprueba, se publica; todo el recorrido queda en la auditoría.

**3. Ingesta de CVE**

1. La función programada obtiene el CVE y lo guarda con su procedencia.
2. Se correlaciona con la versión del IT Component (CPE/purl).
3. Se prioriza combinando CVSS, EPSS y criticidad de la aplicación.
4. El ticket sugerido en la herramienta de ITSM **requiere aprobación** antes de crearse.

## Clases de datos

| Clase | Azure SQL | Índice de búsqueda | Prompt del modelo | Registros (logs) |
|---|---|---|---|---|
| Público | Sí | Sí | Sí | Sí |
| Interno | Sí | Sí | Sí, para usuarios autorizados | Sí |
| Confidencial | Sí | Solo con filtro por rol | Solo para roles autorizados | Enmascarado |
| Restringido | **No se carga** (secretos, datos de clientes, datos personales sensibles) | **Nunca** | **Nunca** | Omitido; la ingesta lo descarta |

La clasificación es una propuesta; los valores exactos se confirman con Seguridad de la información (por validar).

## Operación y seguridad

| Tema | Propuesta |
|---|---|
| Registro | Prompts, salidas y llamadas a herramientas; historial de conversaciones con retención de **90 días** (propuesta) |
| Filtros y límites | Filtros de contenido del servicio de modelos, límites de tasa por usuario/agente y alertas de presupuesto |
| Entornos | `dev`, `test` y `prod`, con recursos y datos separados |
| CI/CD | Infraestructura como código y *pipeline* por entorno; despliegue a `prod` tras pruebas y evals |
| Evals | Conjunto de casos del APM ejecutado ante cambios de modelo, *prompts* o herramientas |

### Mecanismo de detención

| Nivel | Efecto | Interruptor concreto |
|---|---|---|
| 1. Agente | Se detiene un agente | Deshabilitar la identidad del agente o revocar sus herramientas |
| 2. Solo lectura | Ningún agente puede escribir | Bandera de solo lectura para agentes en la API |
| 3. Sin IA | Se desactiva la capa de IA | La interfaz usa búsqueda simple y filtros; el APM sigue operando |

## Relación con el roadmap

| Fase | Elementos de esta arquitectura |
|---|---|
| F0 | Esta propuesta; infraestructura como código y entornos base |
| F1 | App Service, Azure SQL, Entra ID, Key Vault, observabilidad; migración del Excel |
| F2 | Ingesta de CVE y EOL |
| F3 | Conectores CMDB, SBOM y repositorios |
| F4 | Azure OpenAI, agentes, Azure AI Search, evals, mecanismo de detención |
| F5 | Analítica avanzada e informes sobre la misma base |
