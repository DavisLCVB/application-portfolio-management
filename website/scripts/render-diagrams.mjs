// Regenera los diagramas ArchiMate (PlantUML) de /docs/arquitectura/diagramas.
//
// Requisitos: Java 17+ y plantuml.jar (solo para regenerar).
//   - PLANTUML_JAR: ruta al jar (opcional).
//   - JAVA_HOME:     ruta al JDK/JRE (opcional; también busca `java` en PATH).
//   - Caché por defecto: /tmp/opencode/plantuml/plantuml.jar y jdk-*/bin/java.
//
// Uso:
//   npm run diagrams         Regenera SVG (publicados en el portal) y PNG (solo local).
//   npm run diagrams:check   Verifica que los SVG están al día (no necesita Java).
//
// Por qué la verificación usa hashes y no los bytes del SVG:
// PlantUML calcula el tamaño y la posición del texto con las fuentes instaladas en el
// sistema. Así, los SVG pueden diferir unos píxeles entre máquinas (p. ej. macOS vs.
// el runner de GitHub) aunque la fuente .puml sea idéntica. Comparar bytes daría falsos
// negativos en CI. Por eso se registra en `manifest.json` el hash SHA-256 de cada .puml:
// si editas un diagrama y olvidas regenerarlo, el hash no coincide y el CI falla.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..', '..');
const diagramsDir = path.join(repoRoot, 'docs', 'arquitectura', 'diagramas');
const manifestPath = path.join(diagramsDir, 'manifest.json');

function findJava() {
  if (process.env.JAVA_HOME) {
    const bin = path.join(process.env.JAVA_HOME, 'bin', 'java');
    if (existsSync(bin)) return bin;
  }
  const cached = [
    '/tmp/opencode/plantuml',
    path.join(process.env.HOME ?? '', '.local', 'share', 'plantuml'),
  ];
  for (const dir of cached) {
    if (!existsSync(dir)) continue;
    const jdk = readdirSync(dir).find((n) => n.startsWith('jdk-'));
    if (jdk && existsSync(path.join(dir, jdk, 'bin', 'java'))) {
      return path.join(dir, jdk, 'bin', 'java');
    }
    const jre = readdirSync(dir).find((n) => n.startsWith('jre'));
    if (jre && existsSync(path.join(dir, jre, 'bin', 'java'))) {
      return path.join(dir, jre, 'bin', 'java');
    }
  }
  return 'java'; // confía en el PATH
}

function findJar() {
  if (process.env.PLANTUML_JAR) return process.env.PLANTUML_JAR;
  const candidates = [
    '/tmp/opencode/plantuml/plantuml.jar',
    path.join(process.env.HOME ?? '', '.local', 'share', 'plantuml', 'plantuml.jar'),
    path.join(process.env.HOME ?? '', '.cache', 'apm', 'plantuml.jar'),
  ];
  for (const c of candidates) if (existsSync(c)) return c;
  return null;
}

function sha256(file) {
  return createHash('sha256').update(readFileSync(file)).digest('hex');
}

if (!existsSync(diagramsDir)) {
  console.error(`No existe el directorio de diagramas: ${diagramsDir}`);
  process.exit(1);
}

const pumls = readdirSync(diagramsDir).filter((f) => f.endsWith('.puml')).sort();
if (pumls.length === 0) {
  console.error('No hay archivos .puml en ' + diagramsDir);
  process.exit(1);
}

const sources = Object.fromEntries(
  pumls.map((f) => [f, sha256(path.join(diagramsDir, f))])
);

// ---------------------------------------------------------------------------
// Modo verificación: ¿los SVG publicados corresponden a los .puml actuales?
// No requiere Java y no compara bytes (ver nota de cabecera).
// ---------------------------------------------------------------------------
if (process.argv.includes('--check')) {
  if (!existsSync(manifestPath)) {
    console.error(
      'Falta docs/arquitectura/diagramas/manifest.json. Ejecuta "npm run diagrams" y haz commit.'
    );
    process.exit(1);
  }
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch {
    console.error('manifest.json no es JSON válido. Ejecuta "npm run diagrams" de nuevo.');
    process.exit(1);
  }
  const previous = manifest.sources ?? {};
  const problems = [];
  for (const [file, hash] of Object.entries(sources)) {
    if (previous[file] !== hash) problems.push(`Fuente modificada sin regenerar: ${file}`);
    const svg = path.join(diagramsDir, file.replace(/\.puml$/, '.svg'));
    if (!existsSync(svg) || readFileSync(svg).length === 0) {
      problems.push(`Falta el SVG de: ${file}`);
    }
  }
  for (const file of Object.keys(previous)) {
    if (!(file in sources)) problems.push(`Fuente eliminada pero sigue en manifest.json: ${file}`);
  }
  if (problems.length) {
    console.error('Los diagramas no están al día:');
    for (const p of problems) console.error(`  - ${p}`);
    console.error('Ejecuta "npm run diagrams" y haz commit de los SVG y manifest.json.');
    process.exit(1);
  }
  console.log(`Diagramas al día: ${pumls.length} (verificado por hash de las fuentes)`);
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Modo regeneración
// ---------------------------------------------------------------------------
const java = findJava();
const jar = findJar();
if (!jar) {
  console.error(
    'No se encontró plantuml.jar. Descárgalo y define PLANTUML_JAR, por ejemplo:\n' +
      '  curl -L -o /tmp/opencode/plantuml/plantuml.jar https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar\n' +
      '  PLANTUML_JAR=/tmp/opencode/plantuml/plantuml.jar npm run diagrams'
  );
  process.exit(1);
}

const result = spawnSync(java, ['-jar', jar, '-tsvg', ...pumls], {
  cwd: diagramsDir,
  encoding: 'utf8',
});
if (result.status !== 0) {
  console.error(result.stdout || result.stderr || 'Fallo al renderizar diagramas (SVG).');
  process.exit(result.status ?? 1);
}
// PNG: solo para revisión local/PR; no se suben al repositorio.
const png = spawnSync(java, ['-jar', jar, '-tpng', ...pumls], {
  cwd: diagramsDir,
  encoding: 'utf8',
});
if (png.status !== 0) {
  console.error(png.stdout || png.stderr || 'Fallo al renderizar diagramas (PNG).');
  process.exit(png.status ?? 1);
}

let ok = 0;
for (const puml of pumls) {
  const name = puml.replace(/\.puml$/, '');
  for (const ext of ['svg', 'png']) {
    const out = path.join(diagramsDir, `${name}.${ext}`);
    if (!existsSync(out) || readFileSync(out).length === 0) {
      console.error(`No se generó: ${out}`);
      process.exit(1);
    }
  }
  ok++;
}

// Registra la versión usada y el hash de cada fuente para la verificación en CI.
const versionInfo = spawnSync(java, ['-jar', jar, '-version'], { encoding: 'utf8' });
const versionMatch = /PlantUML version (\S+)/.exec(
  `${versionInfo.stdout ?? ''}${versionInfo.stderr ?? ''}`
);
const manifest = {
  comment: 'Generado por scripts/render-diagrams.mjs. No editar a mano.',
  plantumlVersion: versionMatch ? versionMatch[1] : 'desconocida',
  sources,
};
writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Diagramas regenerados: ${ok} (SVG + PNG en ${diagramsDir})`);
