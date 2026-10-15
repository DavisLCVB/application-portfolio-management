import { readdir, mkdir, copyFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

/**
 * Copia los archivos de docs/ con la extensión indicada a una carpeta pública
 * y escribe un manifiesto JSON con `{ title, url }` ordenado por título.
 * `title(fullPath, relativeName)` es opcional; por defecto usa la ruta relativa a docs/.
 */
const defaultTitle = (_fullPath, relativeName) => relativeName;

export async function publishFiles({ source, destination, manifest, extension, urlPrefix, title = defaultTitle }) {
  const pattern = new RegExp(`\\.${extension}$`, 'i');
  const files = [];

  async function collect(directory, relative = '') {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      // No seguir enlaces simbólicos ni publicar carpetas ocultas.
      if (entry.name.startsWith('.') || entry.isSymbolicLink()) continue;
      const name = path.join(relative, entry.name);
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) await collect(fullPath, name);
      else if (entry.isFile() && pattern.test(entry.name)) {
        const target = path.join(destination, name);
        await mkdir(path.dirname(target), { recursive: true });
        await copyFile(fullPath, target);
        const segments = name.split(path.sep);
        files.push({
          title: await title(fullPath, segments.join('/')),
          url: urlPrefix + segments.map(encodeURIComponent).join('/'),
        });
      }
    }
  }

  // Eliminar únicamente las copias generadas, incluidos archivos retirados de docs/.
  await rm(destination, { recursive: true, force: true });
  await mkdir(destination, { recursive: true });
  await collect(source);
  files.sort((a, b) => a.title.localeCompare(b.title, 'es'));
  await mkdir(path.dirname(manifest), { recursive: true });
  await writeFile(manifest, JSON.stringify(files, null, 2) + '\n');
  return files;
}
