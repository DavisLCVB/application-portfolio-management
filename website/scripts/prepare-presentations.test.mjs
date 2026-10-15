import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, copyFile, writeFile, readFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

test('publica presentaciones PPTX anidadas, codifica URLs y retira archivos eliminados', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'apm-pptx-'));
  try {
    const scripts = path.join(root, 'website/scripts');
    await mkdir(scripts, { recursive: true });
    for (const file of ['prepare-presentations.mjs', 'publish-files.mjs']) {
      await copyFile(new URL(`./${file}`, import.meta.url), path.join(scripts, file));
    }
    const script = path.join(scripts, 'prepare-presentations.mjs');
    await mkdir(path.join(root, 'docs/presentaciones'), { recursive: true });
    await mkdir(path.join(root, 'docs/.interno'));
    const deck = Buffer.from('PK\u0003\u0004 Fixture de presentación sin transformar');
    await writeFile(path.join(root, 'docs/presentaciones/Avance #1.PPTX'), deck);
    await writeFile(path.join(root, 'docs/presentaciones/Cierre.pptx'), deck);
    await writeFile(path.join(root, 'docs/.interno/privado.pptx'), deck);
    await writeFile(path.join(root, 'docs/presentaciones/.borrador.pptx'), deck);
    await writeFile(path.join(root, 'docs/informe.pdf'), '%PDF-1.4');
    await symlink(path.join(root, 'docs/presentaciones'), path.join(root, 'docs/enlace'));
    const run = () => execFileSync(process.execPath, [script]);
    run();
    const manifest = path.join(root, 'website/src/generated/presentaciones.json');
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')), [
      { title: 'presentaciones/Avance #1.PPTX', url: '/presentaciones/presentaciones/Avance%20%231.PPTX' },
      { title: 'presentaciones/Cierre.pptx', url: '/presentaciones/presentaciones/Cierre.pptx' },
    ]);
    const output = path.join(root, 'website/public/presentaciones/presentaciones/Avance #1.PPTX');
    assert.deepEqual(await readFile(output), deck);
    await assert.rejects(readFile(path.join(root, 'website/public/presentaciones/informe.pdf')), { code: 'ENOENT' });
    await rm(path.join(root, 'docs/presentaciones/Avance #1.PPTX'));
    run();
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')), [
      { title: 'presentaciones/Cierre.pptx', url: '/presentaciones/presentaciones/Cierre.pptx' },
    ]);
    await assert.rejects(readFile(output), { code: 'ENOENT' });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
