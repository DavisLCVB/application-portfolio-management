import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, copyFile, writeFile, readFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { deflateRawSync, crc32 } from 'node:zlib';

// Minimal ZIP writer (deflate) with local headers and central directory.
function zip(entries) {
  const locals = [];
  const centrals = [];
  let offset = 0;
  for (const [name, text] of Object.entries(entries)) {
    const nameBytes = Buffer.from(name);
    const raw = Buffer.from(text);
    const data = deflateRawSync(raw);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(8, 8);
    local.writeUInt32LE(crc32(raw), 14);
    local.writeUInt32LE(data.length, 18);
    local.writeUInt32LE(raw.length, 22);
    local.writeUInt16LE(nameBytes.length, 26);
    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(8, 10);
    central.writeUInt32LE(crc32(raw), 16);
    central.writeUInt32LE(data.length, 20);
    central.writeUInt32LE(raw.length, 24);
    central.writeUInt16LE(nameBytes.length, 28);
    central.writeUInt32LE(offset, 42);
    locals.push(local, nameBytes, data);
    centrals.push(central, nameBytes);
    offset += local.length + nameBytes.length + data.length;
  }
  const directory = Buffer.concat(centrals);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(centrals.length / 2, 8);
  end.writeUInt16LE(centrals.length / 2, 10);
  end.writeUInt32LE(directory.length, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, directory, end]);
}

test('publica presentaciones PPTX anidadas, codifica URLs y retira archivos eliminados', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'apm-pptx-'));
  try {
    const scripts = path.join(root, 'website/scripts');
    await mkdir(scripts, { recursive: true });
    for (const file of ['prepare-presentations.mjs', 'publish-files.mjs', 'pptx-title.mjs']) {
      await copyFile(new URL(`./${file}`, import.meta.url), path.join(scripts, file));
    }
    const script = path.join(scripts, 'prepare-presentations.mjs');
    await mkdir(path.join(root, 'docs/presentaciones'), { recursive: true });
    await mkdir(path.join(root, 'docs/.interno'));
    const deck = Buffer.from('PK\u0003\u0004 Fixture de presentación sin transformar');
    await writeFile(path.join(root, 'docs/presentaciones/Avance #1.PPTX'), deck);
    await writeFile(path.join(root, 'docs/presentaciones/Cierre.pptx'), deck);
    await writeFile(path.join(root, 'docs/presentaciones/otro_archivo--final.pptx'), 'not a zip');
    await writeFile(path.join(root, 'docs/presentaciones/z-deck.pptx'), zip({
      '[Content_Types].xml': '<Types/>',
      'docProps/core.xml': '<cp:coreProperties xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title> Mi &amp; deck </dc:title></cp:coreProperties>',
    }));
    await writeFile(path.join(root, 'docs/.interno/privado.pptx'), deck);
    await writeFile(path.join(root, 'docs/presentaciones/.borrador.pptx'), deck);
    await writeFile(path.join(root, 'docs/informe.pdf'), '%PDF-1.4');
    await symlink(path.join(root, 'docs/presentaciones'), path.join(root, 'docs/enlace'));
    const run = () => execFileSync(process.execPath, [script]);
    run();
    const manifest = path.join(root, 'website/src/generated/presentaciones.json');
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')), [
      { title: 'Avance #1', url: '/presentaciones/presentaciones/Avance%20%231.PPTX' },
      { title: 'Cierre', url: '/presentaciones/presentaciones/Cierre.pptx' },
      { title: 'Mi & deck', url: '/presentaciones/presentaciones/z-deck.pptx' },
      { title: 'Otro archivo final', url: '/presentaciones/presentaciones/otro_archivo--final.pptx' },
    ]);
    const output = path.join(root, 'website/public/presentaciones/presentaciones/Avance #1.PPTX');
    assert.deepEqual(await readFile(output), deck);
    await assert.rejects(readFile(path.join(root, 'website/public/presentaciones/informe.pdf')), { code: 'ENOENT' });
    await rm(path.join(root, 'docs/presentaciones/Avance #1.PPTX'));
    run();
    assert.deepEqual(JSON.parse(await readFile(manifest, 'utf8')).map((item) => item.title), [
      'Cierre', 'Mi & deck', 'Otro archivo final',
    ]);
    await assert.rejects(readFile(output), { code: 'ENOENT' });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
