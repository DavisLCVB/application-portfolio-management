# Application Portfolio Management

Portal documental independiente del futuro sistema APM para Arquitectura TI, con arquitectura del sistema modelada en ArchiMate.

## Estructura

- `docs/`: contenido compartido (Markdown, MDX, PDF y diagramas).
  - `arquitectura/`: documentación y **modelo ArchiMate** del APM (fuente `.puml` + diagramas `.svg`).
  - `guias/`: guías de publicación y de edición de diagramas.
- `website/`: portal estático Astro/Starlight en español.
- `.github/workflows/docs.yml`: CI que valida el build y que los diagramas estén al día.

## Desarrollo

Requiere Node.js 22.12 o superior (recomendado: Node.js 24) y npm.

```sh
cd website
npm ci
npm run dev
```

Para validar producción: `npm run build`. Para verla localmente: `npm run preview`.

## Arquitectura del sistema (ArchiMate)

La arquitectura del APM se modela en **ArchiMate 3.2** como código (PlantUML) en `docs/arquitectura/diagramas/`. Cinco vistas: contexto de negocio, capas, composición de la plataforma, ciclo de IA agéntica y roadmap.

Para regenerar los diagramas necesitas **Java 17+** y `plantuml.jar`:

```sh
curl -L -o /tmp/opencode/plantuml/plantuml.jar \
  https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar
cd website
PLANTUML_JAR=/tmp/opencode/plantuml/plantuml.jar npm run diagrams
```

Haz commit de los `.puml` y los `.svg` (los `.png` son solo para revisión local y están en `.gitignore`). El CI regenera los diagramas y **falla si los SVG no coinciden** con los fuentes.

## PDF

Coloca archivos `.pdf` en `docs/` o sus subcarpetas. El build genera automáticamente `/documentos/`, con visor integrado y enlaces de apertura/descarga. No se utilizan servicios externos para visualizar PDF. Reinicia el servidor de desarrollo después de cambiar PDF.

Los archivos de `website/public/documentos/` y el catálogo de `website/src/generated/` son generados: no los edites ni los subas a Git.

**Todo lo incluido en `docs/` debe considerarse público.** Conserva documentos internos fuera de esta carpeta. Los despliegues anteriores de Vercel pueden seguir accesibles: eliminar un archivo del nuevo build no revoca las copias previamente compartidas.

## Despliegue continuo en Vercel

1. Crea un repositorio remoto y sube este proyecto.
2. Impórtalo en Vercel y selecciona el preset **Astro**.
3. Usa `website` como **Root Directory** y activa **Include source files outside of the Root Directory in the Build Step** para leer `docs/`.
4. Configura Node.js **24.x**, instalación `npm ci`, build `npm run build` y salida `dist`.
5. Selecciona `main` como rama de producción y habilita previews para pull requests.
6. No configures reglas de omisión que ignoren cambios en `docs/`. Verifica un despliegue cambiando solo un documento.

La integración Git de Vercel despliega cada actualización; GitHub Actions valida el build de forma independiente. Configura protección de `main` con el check de CI obligatorio si quieres exigir validación antes de fusionar.

Aún no hay remoto ni proyecto Vercel configurado desde este entorno. No se incluyen enlaces de despliegue ficticios.