import { readdir, mkdir, copyFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const source = fileURLToPath(new URL('../../docs/', import.meta.url));
const destination = fileURLToPath(new URL('../public/documentos/', import.meta.url));
const manifest = new URL('../src/generated/pdfs.json', import.meta.url);
const documents = [];

async function collect(directory, relative = '') {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    // No seguir enlaces simbólicos ni publicar carpetas ocultas.
    if (entry.name.startsWith('.') || entry.isSymbolicLink()) continue;
    const name = path.join(relative, entry.name);
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) await collect(fullPath, name);
    else if (entry.isFile() && /\.pdf$/i.test(entry.name)) {
      const target = path.join(destination, name);
      await mkdir(path.dirname(target), { recursive: true });
      await copyFile(fullPath, target);
      const segments = name.split(path.sep);
      documents.push({
        title: segments.join('/'),
        url: '/documentos/' + segments.map(encodeURIComponent).join('/'),
      });
    }
  }
}

// Eliminar únicamente las copias generadas, incluidos PDF retirados de docs/.
await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });
await collect(source);
documents.sort((a, b) => a.title.localeCompare(b.title, 'es'));
await mkdir(new URL('../src/generated/', import.meta.url), { recursive: true });
await writeFile(manifest, JSON.stringify(documents, null, 2) + '\n');
console.log(`PDF preparados: ${documents.length}`);
