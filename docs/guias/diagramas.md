---
title: Editar y regenerar diagramas
description: Cómo mantener al día los diagramas ArchiMate de la arquitectura del APM.
---

## Fuente de los diagramas

La arquitectura se modela en **ArchiMate 3.2** como código: los archivos `*.puml` en `docs/arquitectura/diagramas/` son la fuente de verdad. Los **SVG** generados se versionan y son los que muestra el portal.

## Regenerar localmente

Requisitos: Java 17+ y `plantuml.jar`.

```sh
# Descargar PlantUML (una vez)
curl -L -o /tmp/opencode/plantuml/plantuml.jar \
  https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar

# Regenerar diagramas
cd website
PLANTUML_JAR=/tmp/opencode/plantuml/plantuml.jar npm run diagrams
```

Se generan SVG (publicados) y PNG (solo revisión local). Si java no está en el `PATH`, define `JAVA_HOME`.

## Flujo de trabajo

1. Edita o crea `docs/arquitectura/diagramas/*.puml`.
2. Ejecuta `npm run diagrams`.
3. Revisa el resultado y haz commit de **los `.puml` y los `.svg`** (los `.png` están en `.gitignore`).
4. El CI regenera los diagramas y **falla si los SVG no coinciden** con los fuentes.

## Modelado en Archi (opcional)

Si tu equipo prefiere modelar en la herramienta **Archi** (archimatetool.com), puedes mantener un modelo `.archimate` con coArchi y exportar diagramas a SVG. Por ahora el repositorio usa PlantUML como fuente canónica para que todo sea revisable y regenerable en CI/CD; una migración al flujo Archi+coArchi puede incorporarse más adelante.

## Notación utilizada

- Elementos: `Business_Actor`, `Business_Process`, `Application_Component`, `Application_Function`, `Application_DataObject`, `Technology_Node`, `Motivation_Goal`, `Implementation_WorkPackage`, entre otras.
- Relaciones: `Rel_Serving_*`, `Rel_Access_*`, `Rel_Flow_*`, `Rel_Triggering_*`, `Rel_Assignment_*`, `Rel_Realization_*`, `Rel_Composition_*`, `Rel_Aggregation_*`... con dirección `Up/Down/Left/Right`.
- Tema: `!theme archimate-standard from <archimate/themes>` (colores del estándar ArchiMate).