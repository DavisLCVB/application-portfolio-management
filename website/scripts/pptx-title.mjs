import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { inflateRawSync } from 'node:zlib';

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };

/** Reads one entry from a ZIP buffer using its central directory. Returns null if absent. */
function readZipEntry(buffer, wanted) {
  // End of central directory: last 22 bytes plus an optional comment of up to 64 KiB.
  const min = Math.max(0, buffer.length - 22 - 0xffff);
  let eocd = -1;
  for (let i = buffer.length - 22; i >= min; i--) {
    if (buffer.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) return null;
  const count = buffer.readUInt16LE(eocd + 10);
  let pointer = buffer.readUInt32LE(eocd + 16);
  for (let n = 0; n < count; n++) {
    if (buffer.readUInt32LE(pointer) !== 0x02014b50) return null;
    const method = buffer.readUInt16LE(pointer + 10);
    const compressedSize = buffer.readUInt32LE(pointer + 20);
    const nameLength = buffer.readUInt16LE(pointer + 28);
    const extraLength = buffer.readUInt16LE(pointer + 30);
    const commentLength = buffer.readUInt16LE(pointer + 32);
    const localOffset = buffer.readUInt32LE(pointer + 42);
    const name = buffer.toString('utf8', pointer + 46, pointer + 46 + nameLength);
    if (name === wanted) {
      if (buffer.readUInt32LE(localOffset) !== 0x04034b50) return null;
      const start = localOffset + 30 + buffer.readUInt16LE(localOffset + 26) + buffer.readUInt16LE(localOffset + 28);
      const data = buffer.subarray(start, start + compressedSize);
      if (method === 0) return data;
      if (method === 8) return inflateRawSync(data);
      return null;
    }
    pointer += 46 + nameLength + extraLength + commentLength;
  }
  return null;
}

/** Returns the `dc:title` embedded in a .pptx file, or null on any failure. */
export async function readPptxTitle(file) {
  try {
    const xml = readZipEntry(await readFile(file), 'docProps/core.xml')?.toString('utf8');
    const match = xml?.match(/<dc:title(?:\s[^>]*)?>([\s\S]*?)<\/dc:title>/);
    if (!match) return null;
    const title = match[1]
      .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
      .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(Number(dec)))
      .replace(/&(amp|lt|gt|quot|apos);/g, (_, name) => ENTITIES[name])
      .replace(/\s+/g, ' ')
      .trim();
    return title || null;
  } catch {
    return null;
  }
}

/** Turns a file name into a readable title: `pitch-apm_ia.pptx` → `Pitch apm ia`. */
export function titleFromFileName(name) {
  const base = path.basename(name, path.extname(name)).replace(/[-_]+/g, ' ').replace(/\s+/g, ' ').trim();
  return base.charAt(0).toUpperCase() + base.slice(1);
}

/** Title hook for publishFiles: embedded title first, prettified file name as fallback. */
export async function presentationTitle(fullPath, relativeName) {
  return (await readPptxTitle(fullPath)) ?? titleFromFileName(relativeName);
}
