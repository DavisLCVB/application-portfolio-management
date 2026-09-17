---
title: Editar y regenerar diagramas
description: Cómo mantener al día los diagramas ArchiMate de la arquitectura del APM.
---

## Fuente de los diagramas

La arquitectura se modela en **ArchiMate 3.2** como código: los archivos `*.puml` en `docs/arquitectura/diagramas/` son la fuente de verdad. Los **SVG** generados se versionan y son los que muestra el portal.

## Regenerar localmente

Requisitos: Java 17+ y `plantuml.jar`. Usa la **misma versión que el CI** (definida en `.github/workflows/docs.yml`).

```sh
# Descargar PlantUML (una vez)
curl -L -o /tmp/opencode/plantuml/plantuml.jar \
  https://github.com/plantuml/plantuml/releases/download/v1.2026.8/plantuml.jar

# Regenerar diagramas + manifest.json
cd website
PLANTUML_JAR=/tmp/opencode/plantuml/plantuml.jar npm run diagrams

# Comprobar (sin Java) que todo está al día
npm run diagrams:check
```

Se generan SVG (publicados) y PNG (solo revisión local). Si java no está en el `PATH`, define `JAVA_HOME`.

## Por qué se valida con hashes y no con los SVG

PlantUML calcula el tamaño y la posición del texto con las **fuentes instaladas en el sistema**, así que los SVG pueden diferir unos píxeles entre máquinas (tu equipo frente al runner de GitHub). Comparar los bytes del SVG daría **falsos negativos** en CI aunque la fuente `.puml` sea idéntica.

Por eso el script escribe `docs/arquitectura/diagramas/manifest.json` con el **hash SHA-256 de cada `.puml`** y la versión de PlantUML usada. El CI compara esos hashes: si editas un diagrama y olvidas regenerarlo, el hash no coincide y el pipeline falla. **El `manifest.json` también se versiona.**

## Flujo de trabajo

1. Edita o crea `docs/arquitectura/diagramas/*.puml`.
2. Ejecuta `npm run diagrams`.
3. Revisa el resultado y haz commit de **los `.puml`, los `.svg` y `manifest.json`** (los `.png` están en `.gitignore`).
4. El CI comprueba con `npm run diagrams:check` que no haya fuentes modificadas sin regenerar y, además, **compila los `.puml`** con una versión fija de PlantUML para detectar errores de sintaxis.

## Modelado en Archi (opcional)

Si tu equipo prefiere modelar en la herramienta **Archi** (archimatetool.com), puedes mantener un modelo `.archimate` con coArchi y exportar diagramas a SVG. Por ahora el repositorio usa PlantUML como fuente canónica para que todo sea revisable y regenerable en CI/CD; una migración al flujo Archi+coArchi puede incorporarse más adelante.

## Notación utilizada

- Elementos: `Business_Actor`, `Business_Process`, `Application_Component`, `Application_Function`, `Application_DataObject`, `Technology_Node`, `Motivation_Goal`, `Implementation_WorkPackage`, entre otras.
- Relaciones: `Rel_Serving_*`, `Rel_Access_*`, `Rel_Flow_*`, `Rel_Triggering_*`, `Rel_Assignment_*`, `Rel_Realization_*`, `Rel_Composition_*`, `Rel_Aggregation_*`... con dirección `Up/Down/Left/Right`.
- Tema: `!theme archimate-standard from <archimate/themes>` (colores del estándar ArchiMate).