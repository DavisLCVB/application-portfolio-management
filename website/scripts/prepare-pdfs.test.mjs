import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, copyFile, writeFile, readFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

test('publica PDF anidados, codifica URLs y retira archivos eliminados', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'apm-pdfs-'));
  try {
    const script = path.join(root, 'website/scripts/prepare-pdfs.mjs');
    await mkdir(path.dirname(script), { recursive: true });
    await copyFile(new URL('./prepare-pdfs.mjs', import.meta.url), script);
    await mkdir(path.join(root, 'docs/entregables'), { recursive: true });
    await mkdir(path.join(root, 'docs/.interno'));
    const pdf = Buffer.from('%PDF-1.4\n% Fixture para comprobar copia sin transformar\n%%EOF\n');
    await writeFile(path.join(root, 'docs/entregables/Visión #1.PDF'), pdf);
    await writeFile(path.join(root, 'docs/.interno/privado.pdf'), pdf);
    await writeFile(path.join(root, 'docs/notas.txt'), 'No publicar');
    await symlink(path.join(root, 'docs/entregables'), path.join(root, 'docs/enlace'));
    const run = () => execFileSync(process.execPath, [script]);
    run();
    const manifest = path.join(root, 'website/src/generated/pdfs.json');
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')), [{
      title: 'entregables/Visión #1.PDF',
      url: '/documentos/entregables/Visi%C3%B3n%20%231.PDF',
    }]);
    const output = path.join(root, 'website/public/documentos/entregables/Visión #1.PDF');
    assert.deepEqual(await readFile(output), pdf);
    await rm(path.join(root, 'docs/entregables/Visión #1.PDF'));
    run();
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')), []);
    await assert.rejects(readFile(output), { code: 'ENOENT' });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
