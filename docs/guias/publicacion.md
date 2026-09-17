---
title: Publicar documentación
description: Cómo actualizar el contenido compartido.
---

## Markdown

Agrega archivos `.md` o `.mdx` en `docs/`. Incluye al menos el título en el encabezado:

```yaml
---
title: Avance del proyecto
---
```

Los documentos dentro de `docs/guias/` aparecen automáticamente en la navegación de Guías. Para otras secciones, agrega un grupo en `website/astro.config.mjs`.

## PDF

Copia tus PDF en cualquier subcarpeta de `docs/`, por ejemplo `docs/entregables/avance.pdf`. No requieren encabezado ni registro manual.

Durante el build se copian los PDF al sitio y se actualiza el [catálogo de documentos](/documentos/). El catálogo ofrece vista integrada con el visor PDF del navegador, apertura en otra pestaña y descarga. La visualización integrada depende del soporte del navegador, especialmente en móviles.

Se conservan los nombres y las subcarpetas. También se acepta la extensión `.PDF`. Al retirar un archivo y desplegar nuevamente, su copia deja de formar parte de la nueva versión.

En desarrollo local, reinicia `npm run dev` después de agregar, modificar o retirar PDF. En producción, cada build vuelve a preparar el catálogo.

## Qué se comparte

Trata `docs/` como contenido público. Guarda borradores y documentación confidencial **fuera de esta carpeta**. No se siguen enlaces simbólicos ni se copian PDF de carpetas ocultas. No agregues credenciales ni datos sensibles.

El texto dentro de los PDF no se incorpora al buscador de Starlight. El portal no convierte documentos de Office a PDF ni proporciona autenticación.

## Actualizaciones

Una vez conectado el repositorio a Vercel, los cambios en la rama de producción generan un nuevo despliegue y las solicitudes de cambio generan vistas previas, según la configuración del proyecto. Un build fallido no reemplaza la última versión publicada.
