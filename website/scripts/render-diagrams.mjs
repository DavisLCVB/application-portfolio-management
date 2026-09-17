// Regenera los diagramas ArchiMate (PlantUML) de /docs/arquitectura/diagramas.
//
// Requisitos: Java 17+ y plantuml.jar.
//   - PLANTUML_JAR: ruta al jar (opcional).
//   - JAVA_HOME:     ruta al JDK/JRE (opcional; también busca `java` en PATH).
//   - Caché por defecto: /tmp/opencode/plantuml/plantuml.jar y jdk-*/bin/java.
//
// Uso:  npm run diagrams
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..', '..');
const diagramsDir = path.join(repoRoot, 'docs', 'arquitectura', 'diagramas');

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
if (!existsSync(diagramsDir)) {
  console.error(`No existe el directorio de diagramas: ${diagramsDir}`);
  process.exit(1);
}

const pumls = readdirSync(diagramsDir).filter((f) => f.endsWith('.puml')).sort();
if (pumls.length === 0) {
  console.error('No hay archivos .puml en ' + diagramsDir);
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
console.log(`Diagramas regenerados: ${ok} (SVG + PNG en ${diagramsDir})`);