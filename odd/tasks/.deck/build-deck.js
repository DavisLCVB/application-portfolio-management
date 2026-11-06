const pptxgen = require('pptxgenjs');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const sharp = require('sharp');
const fa = require('react-icons/fa');

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'Davis Cartagena';
pres.title = 'APM con IA agéntica';
pres.subject = 'Descubrimiento continuo y gobierno del portafolio de aplicaciones';

// Visual identity taken from docs/presentaciones/apm-agents.pptx: Calibri, petrol + teal, coral and yellow accents, white cards on a cool gray canvas.
const F = 'Calibri';
const C = {
  navy: '0B3C49',
  deep: '134C5B',
  blue: '127C86',
  blueL: 'D7EAEC',
  ice: 'B9D7DA',
  iceL: 'E3EEF0',
  canvas: 'EEF3F4',
  ink: '1E2A30',
  gray: '5F7480',
  line: '9CC6CB',
  amber: 'C4533A',
  amberL: 'F7E1DB',
  yellow: 'F2A900',
  green: '3F8F6B',
  greenL: 'DCEFE5',
  red: 'A83A2A',
  redL: 'F3D9D3',
  white: 'FFFFFF',
};

function bg(s, color) { s.background = { color }; }
function txt(s, t, x, y, w, h, size = 15, color = C.ink, bold = false, opts = {}) {
  s.addText(t, {
    x, y, w, h, fontFace: F, fontSize: size, color, bold,
    margin: 0, valign: 'top', isTextBox: true, ...opts,
  });
}
function label(s, t, x, y, w, color = C.blue) {
  txt(s, t.toUpperCase(), x, y, w, 0.28, 12, color, true, { charSpacing: 1 });
}
function title(s, t, dark = false, size = 30) {
  txt(s, t, 0.6, 0.42, 12.1, 0.65, size, dark ? C.white : C.navy, true);
}
function sub(s, t, dark = false) {
  txt(s, t, 0.6, 1.1, 12.1, 0.4, 16, dark ? C.ice : C.gray);
}
function takeaway(s, t, color = C.blue, y = 6.25) {
  txt(s, t, 0.6, y, 12.1, 0.45, 19, color, true);
}
// ref: section of the final report this slide summarizes.
function foot(s, n, ref, dark = false) {
  const color = dark ? C.ice : C.gray;
  txt(s, 'APM con IA agéntica · Davis Cartagena', 0.6, 7.0, 6.0, 0.25, 10, color);
  txt(s, ref ? `Informe · ${ref}    ${n}` : String(n), 6.7, 7.0, 6.03, 0.25, 10, color, false, { align: 'right' });
}
function notes(s, t) { s.addNotes(t); }
function card(s, x, y, w, h, fill = C.white, radius = 0.06, extra = {}) {
  const shadow = fill === C.white && h > 0.5
    ? { type: 'outer', color: C.navy, opacity: 0.14, blur: 6, offset: 2, angle: 90 } : undefined;
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: fill },
    line: { color: fill, width: 0.5 }, rectRadius: radius, shadow, ...extra,
  });
}
function chip(s, n, x, y, d = 0.46, fill = C.blue, size = 14) {
  s.addShape(pres.ShapeType.ellipse, {
    x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0.5 },
  });
  txt(s, String(n), x, y, d, d, size, C.white, true, { align: 'center', valign: 'middle' });
}
function bullets(s, items, x, y, w, h, size = 15, color = C.gray) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: { bullet: true, breakLine: i < items.length - 1 },
  })), {
    x, y, w, h, fontFace: F, fontSize: size, color, margin: 0,
    valign: 'top', paraSpaceAfter: 10, isTextBox: true,
  });
}
function pill(s, t, x, y, w, fill, color, size = 12, h = 0.38) {
  card(s, x, y, w, h, fill, 0.18);
  txt(s, t, x, y, w, h, size, color, true, { align: 'center', valign: 'middle' });
}
function vline(s, x, y, h) {
  s.addShape(pres.ShapeType.line, { x, y, w: 0, h, line: { color: C.line, width: 1.5 } });
}
function hline(s, x, y, w, color = C.line, width = 1.5) {
  s.addShape(pres.ShapeType.line, { x, y, w, h: 0, line: { color, width } });
}
// straight connector between two points; flips keep the arrowhead on (x2, y2)
function conn(s, x1, y1, x2, y2, color = C.line, opts = {}) {
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color, width: 1.5, endArrowType: 'triangle', ...opts },
  });
}

const ICONS = {};
async function loadIcons(names) {
  for (const n of names) {
    if (!fa[n]) throw new Error(`Unknown icon ${n}`);
    const svg = renderToStaticMarkup(React.createElement(fa[n], { color: '#FFFFFF', size: 256 }));
    ICONS[n] = 'image/png;base64,' + (await sharp(Buffer.from(svg)).png().toBuffer()).toString('base64');
  }
}
// icon in a colored circle: the reference deck's motif
function ico(s, name, x, y, d = 0.5, fill = C.blue) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0.5 } });
  const p = d * 0.25;
  s.addImage({ data: ICONS[name], x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
// hub-and-spoke motif from apm-agents: one catalog fed by many sources
function hub(s, hx, hy, R, center) {
  const spokes = [['FaFileContract', C.gray], ['FaDatabase', C.blue], ['FaShieldAlt', C.green], ['FaUserCheck', C.gray], ['FaPlug', C.blue], ['FaCodeBranch', C.blue]];
  spokes.forEach(([n, fill], i) => {
    const a = -Math.PI / 2 + i * (Math.PI / 3);
    const x = hx + R * Math.cos(a), y = hy + R * Math.sin(a);
    conn(s, hx, hy, x, y, C.deep, { endArrowType: 'none', width: 2 });
    ico(s, n, x - 0.36, y - 0.36, 0.72, fill);
  });
  s.addShape(pres.ShapeType.ellipse, { x: hx - 0.95, y: hy - 0.95, w: 1.9, h: 1.9, fill: { color: C.yellow, transparency: 75 }, line: { color: C.yellow, width: 0.5, transparency: 75 } });
  ico(s, center, hx - 0.68, hy - 0.68, 1.36, C.yellow);
}

async function main() {
await loadIcons(['FaProjectDiagram', 'FaCodeBranch', 'FaFileContract', 'FaDatabase', 'FaShieldAlt', 'FaUserCheck', 'FaPlug', 'FaCheck',
  'FaEdit', 'FaSyncAlt', 'FaCoins', 'FaBalanceScale', 'FaRandom', 'FaFingerprint', 'FaWallet', 'FaUserSecret', 'FaChartLine', 'FaUnlink',
  'FaCode', 'FaIdCard', 'FaSearch', 'FaBell', 'FaExclamationTriangle', 'FaLink', 'FaHandPointer', 'FaRobot', 'FaGlobe', 'FaBuilding',
  'FaLock', 'FaBan', 'FaPowerOff', 'FaEye', 'FaKeyboard', 'FaIdBadge', 'FaClipboardList', 'FaVial', 'FaGavel', 'FaExchangeAlt',
  'FaTachometerAlt', 'FaUserShield', 'FaHourglassHalf', 'FaUserCog']);

// ---------------------------------------------------------------- 1. Portada
{
  const s = pres.addSlide();
  bg(s, C.navy);
  hub(s, 10.3, 3.6, 1.95, 'FaProjectDiagram');
  txt(s, 'GOBERNANZA DE IA CON ENFOQUE OCDE · TRABAJO FINAL', 0.6, 0.9, 7.6, 0.3, 12, C.yellow, true, { charSpacing: 2 });
  txt(s, 'APM con IA agéntica: descubrimiento continuo y gobierno del portafolio', 0.6, 1.45, 7.4, 2.1, 38, C.white, true);
  txt(s, 'Arquitectura, conciliación con el catálogo y control humano en una plataforma de gestión del portafolio de aplicaciones', 0.6, 3.7, 7.0, 0.95, 17, C.ice);
  const meta = [
    ['Autor', 'Davis Leonardo Cartagena Valera Brush'],
    ['Docente', 'Jorge Pantoja'],
    ['Caso', 'Portafolio de aplicaciones con IA agéntica'],
    ['Fecha', 'Noviembre de 2026'],
  ];
  meta.forEach(([k, v], i) => {
    const y = 5.3 + i * 0.4;
    txt(s, k, 0.6, y, 1.4, 0.3, 14, C.ice);
    txt(s, v, 2.0, y, 6.0, 0.3, 14, C.white);
  });
  notes(s, 'Abrir con la tesis: el catálogo no falla por falta de análisis, sino porque mantenerlo cuesta más de lo que vale. La IA ayuda si ataca la captura y la identidad; y eso solo se sostiene si se gobierna.');
}

// ---------------------------------------------------------------- 2. El problema
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'El catálogo llega tarde');
  sub(s, 'El catálogo manual no sigue el ritmo real del portafolio');
  const items = [
    ['FaEdit', 'Se mantiene a mano', 'Cuestionarios, planillas y una CMDB incompleta compiten con el trabajo operativo.'],
    ['FaSyncAlt', 'Cada cambio deja la ficha atrás', 'Cambia el dueño, la versión o el proveedor, y el catálogo sigue mostrando el estado anterior.'],
    ['FaCoins', 'El costo supera el valor', 'Mantenerlo actualizado cuesta más de lo que produce; por eso se degrada.'],
  ];
  items.forEach(([icon, t, b], i) => {
    const y = 1.9 + i * 1.38;
    ico(s, icon, 0.6, y, 0.55, C.amber);
    txt(s, t, 1.4, y + 0.02, 4.9, 0.4, 19, C.navy, true);
    txt(s, b, 1.4, y + 0.47, 4.9, 0.85, 15, C.gray);
  });

  card(s, 6.5, 1.9, 6.23, 3.95);
  hline(s, 7.2, 3.9, 4.8, C.line, 3);
  const pts = [[7.6, 'La aplicación cambia'], [9.6, 'La ficha sigue igual'], [11.6, 'Se decide con dato viejo']];
  pts.forEach(([x, l], i) => {
    s.addShape(pres.ShapeType.ellipse, {
      x: x - 0.14, y: 3.76, w: 0.28, h: 0.28,
      fill: { color: i === 2 ? C.amber : C.blue }, line: { color: C.white, width: 1.5 },
    });
    txt(s, l, x - 0.95, i === 1 ? 4.2 : 2.85, 1.9, 0.75, 14, i === 2 ? C.amber : C.navy, true, { align: 'center', valign: i === 1 ? 'top' : 'bottom' });
  });
  txt(s, 'La ficha envejece mientras el portafolio cambia.', 6.85, 5.2, 5.6, 0.4, 14, C.gray);
  takeaway(s, 'No falta un repositorio: falta bajar el costo de captura.');
  foot(s, 2, '1.1');
  notes(s, 'El problema no es la falta de un repositorio: hay varios. Es que el costo de mantenerlo actualizado supera el valor que produce.');
}

// ---------------------------------------------------------------- 3. Causas y consecuencias
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Por qué se degrada y qué se pierde');
  sub(s, 'Cuatro causas alimentan un catálogo desactualizado; sus efectos se refuerzan');
  label(s, 'Causas', 0.6, 1.65, 3.9, C.amber);
  const causes = [
    ['FaBalanceScale', 'Incentivos mal alineados', 'Quien reporta paga; otro se beneficia.'],
    ['FaRandom', 'Dispersión sin árbitro', 'Nadie define qué fuente manda.'],
    ['FaFingerprint', 'Identidad sin dueño', 'Una aplicación, varios nombres.'],
    ['FaWallet', 'Presupuesto', 'Licencias comerciales fuera de alcance.'],
  ];
  const mx = 5.05, mw = 3.1, my = 2.6, mh = 2.55, mcy = my + mh / 2;
  causes.forEach(([icon, t, b], i) => {
    const y = 1.98 + i * 1.0;
    card(s, 0.6, y, 3.95, 0.88);
    ico(s, icon, 0.78, y + 0.19, 0.5, C.amber);
    txt(s, t, 1.45, y + 0.12, 3.0, 0.35, 15, C.navy, true);
    txt(s, b, 1.45, y + 0.48, 3.0, 0.35, 13, C.gray);
    conn(s, 4.55, y + 0.44, mx, mcy, C.amber, { dashType: 'dash' });
  });
  card(s, mx, my, mw, mh, C.amberL, 0.06, { line: { color: C.amber, width: 1.25, dashType: 'dash' } });
  ico(s, 'FaExclamationTriangle', mx + mw / 2 - 0.35, my + 0.3, 0.7, C.amber);
  txt(s, 'Catálogo desactualizado', mx + 0.2, my + 1.12, mw - 0.4, 0.4, 18, C.amber, true, { align: 'center' });
  txt(s, 'Llega tarde y nadie confía en él.', mx + 0.2, my + 1.6, mw - 0.4, 0.7, 14, C.ink, false, { align: 'center' });

  label(s, 'Consecuencias', 8.75, 1.65, 3.9, C.blue);
  const effects = [
    ['FaUserSecret', 'Shadow IT', 'Aplicaciones y contratos fuera de la vista de TI.'],
    ['FaChartLine', 'Decisiones incompletas', 'Inversión, TIME y retiro sobre datos viejos.'],
    ['FaUnlink', 'Desconfianza', 'El equipo deja de usar el catálogo.'],
  ];
  effects.forEach(([icon, t, b], i) => {
    const y = 2.0 + i * 1.45;
    card(s, 8.75, y, 3.98, 1.25);
    ico(s, icon, 8.93, y + 0.2, 0.5, C.blue);
    txt(s, t, 9.6, y + 0.18, 3.0, 0.35, 16, C.navy, true);
    txt(s, b, 9.6, y + 0.56, 3.0, 0.6, 13, C.gray);
    conn(s, mx + mw, mcy, 8.75, y + 0.62, C.blue);
  });
  takeaway(s, '↻  Dato viejo → desconfianza → menos reporte: el ciclo se repite.', C.amber);
  foot(s, 3, '1.1');
  notes(s, 'Las causas no son solo técnicas: incentivos, dispersión, identidad y presupuesto. Todas desembocan en un catálogo desactualizado, y sus efectos —Shadow IT, decisiones incompletas y desconfianza— reducen aún más el reporte.');
}

// ---------------------------------------------------------------- 4. Arquitectura de la solución
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Arquitectura de la solución');
  sub(s, 'Upstream descubre y concilia; downstream consume un catálogo ya gobernado');
  const stages = [
    ['FaDatabase', 'Fuentes', 'Git, CI/CD, contratos, TDR, CMDB y planillas', C.gray],
    ['FaSearch', 'Descubrimiento', 'Agente 1 Code-to-Catalog y Agente 2 Dark Data Miner', C.blue],
    ['FaLink', 'Reconciliación', 'Agente 3 vincula N:M con un score de 0 a 1', C.blue],
    ['FaHandPointer', 'Validación', 'Agente 4 pregunta con micro-nudges de un clic', C.blue],
    ['FaUserCheck', 'Aprobación', 'Arquitecto o Gobierno de Arquitectura aprueba y publica', C.yellow],
  ];
  const w = 2.2, gap = 0.28;
  stages.forEach(([icon, t, b, fill], i) => {
    const x = 0.6 + i * (w + gap);
    card(s, x, 1.75, w, 2.6);
    ico(s, icon, x + w / 2 - 0.32, 1.98, 0.64, fill);
    txt(s, t, x + 0.15, 2.78, w - 0.3, 0.38, 16, C.navy, true, { align: 'center' });
    txt(s, b, x + 0.15, 3.2, w - 0.3, 1.05, 13, C.gray, false, { align: 'center' });
    if (i < stages.length - 1) conn(s, x + w + 0.03, 3.05, x + w + gap - 0.03, 3.05, C.blue, { width: 2 });
  });
  const lx = 0.6 + 4 * (w + gap) + w / 2;
  conn(s, lx, 4.35, lx, 4.72, C.yellow, { width: 2 });

  card(s, 0.6, 4.75, 12.13, 1.25, C.navy);
  ico(s, 'FaProjectDiagram', 0.85, 5.05, 0.64, C.yellow);
  txt(s, 'Catálogo APM gobernado', 1.7, 5.02, 4.0, 0.4, 18, C.white, true);
  txt(s, 'Fuente única para personas y agentes', 1.7, 5.45, 4.0, 0.35, 13, C.ice);
  ['Consulta MCP', 'Vulnerabilidades', 'Obsolescencia', 'TIME / what-if'].forEach((t, i) => {
    const x = 5.95 + i * 1.68;
    card(s, x, 4.98, 1.56, 0.8, C.blue, 0.06);
    txt(s, t, x, 4.98, 1.56, 0.8, 13, C.white, true, { align: 'center', valign: 'middle' });
  });
  takeaway(s, 'El valor está en la captura y la identidad, no en el chat.');
  foot(s, 4, '1.2 y 1.3');
  notes(s, 'La IA tradicional en APM es un bombero downstream: asume un catálogo limpio que no existe. Aquí se pone en el descubrimiento y la reconciliación: cuatro agentes llevan el dato crudo hasta una ficha aprobada, y todo lo downstream consume ese catálogo.');
}

// ---------------------------------------------------------------- 5. Cómo descubre
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Cada dato nace con evidencia');
  sub(s, 'Dos agentes de descubrimiento; ningún valor sin cita');
  const agents = [
    ['FaCode', 'Code-to-Catalog', 'Parsers deterministas sobre manifiestos, dependencias y despliegues. Sin LLM.'],
    ['FaFileContract', 'Dark Data Miner', 'OCR y extracción guiada por esquema en contratos y TDR.'],
  ];
  agents.forEach(([icon, t, b], i) => {
    const y = 1.85 + i * 2.15;
    card(s, 0.6, y, 5.95, 1.95);
    ico(s, icon, 0.9, y + 0.3, 0.55);
    txt(s, t, 1.65, y + 0.34, 4.6, 0.42, 19, C.navy, true);
    txt(s, b, 1.65, y + 0.87, 4.6, 0.95, 15, C.gray);
  });
  card(s, 6.85, 1.85, 5.88, 4.1, C.navy);
  label(s, 'Evidencia primaria', 7.2, 2.12, 5.2, C.ice);
  const ev = [
    ['Código', 'commit 8f3a… · src/deploy.yaml:42'],
    ['Contrato', 'TDR-2024-0723 · p. 7 · cláusula 4.2'],
    ['CMDB', 'CI-0042'],
  ];
  ev.forEach(([k, v], i) => {
    const y = 2.65 + i * 0.75;
    txt(s, k, 7.2, y, 1.3, 0.35, 13, C.ice);
    txt(s, v, 8.5, y, 4.0, 0.35, 16, C.white, true);
  });
  hline(s, 7.2, 4.95, 5.2, C.deep, 1);
  txt(s, 'Cada valor se puede rastrear hasta su fuente.', 7.2, 5.15, 5.2, 0.5, 15, C.ice);
  takeaway(s, 'Si no hay cita, el campo queda vacío.', C.amber);
  foot(s, 5, '1.3');
  notes(s, 'La evidencia no es opcional: hash de commit y archivo:línea para código; documento, página y cláusula para contratos.');
}

// ---------------------------------------------------------------- 6. Reconciliación
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'El sistema propone; no fusiona solo');
  sub(s, 'Un score y un umbral deciden qué pasa a revisión humana');
  // score bar: 0..1 mapped to x 0.8..12.5; threshold 0.85
  const x0 = 0.8, x1 = 12.5, xt = x0 + (x1 - x0) * 0.85;
  txt(s, 'Requiere Verificación', x0, 2.0, 6.0, 0.35, 15, C.amber, true);
  txt(s, 'Publicación directa', xt - 1.0, 2.0, x1 - xt + 1.0, 0.35, 15, C.blue, true, { align: 'right' });
  card(s, x0, 2.5, xt - x0, 0.8, C.amberL, 0.04);
  card(s, xt, 2.5, x1 - xt, 0.8, C.blueL, 0.04);
  s.addShape(pres.ShapeType.line, { x: xt, y: 2.35, w: 0, h: 1.1, line: { color: C.navy, width: 2.5 } });
  [[0, '0'], [0.5, '0,5'], [0.85, 'umbral 0,85'], [1, '1']].forEach(([v, l]) => {
    const x = x0 + (x1 - x0) * v;
    const lw = v === 0.85 ? 1.6 : 0.6;
    const align = v === 0 ? 'left' : v === 1 ? 'right' : 'center';
    const xx = v === 0 ? x : v === 1 ? x - lw : x - lw / 2;
    txt(s, l, xx, 3.45, lw, 0.3, 13, v === 0.85 ? C.navy : C.gray, v === 0.85, { align });
  });
  const cards = [
    ['Score de 0 a 1', 'Heurístico, por cada vínculo propuesto entre fuentes.'],
    ['Umbral único', 'Configurable: por debajo, el caso queda en revisión.'],
    ['Huérfanos y conflictos', 'Van siempre a la cola del arquitecto; nunca se fusionan solos.'],
  ];
  cards.forEach(([t, b], i) => {
    const x = 0.6 + i * 4.13;
    card(s, x, 4.1, 3.9, 1.75);
    txt(s, t, x + 0.3, 4.3, 3.3, 0.4, 17, C.navy, true);
    txt(s, b, x + 0.3, 4.8, 3.3, 0.95, 14, C.gray);
  });
  takeaway(s, 'El score no es una probabilidad hasta calibrarse.');
  foot(s, 6, '1.3');
  notes(s, 'El reconciliador propone vínculos N:M con un score. Bajo el umbral, Requiere Verificación. Huérfanos y conflictos a revisión humana.');
}

// ---------------------------------------------------------------- 7. Cómo pregunta
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Preguntar solo lo que las reglas no resuelven');
  sub(s, 'Avisos por evento y confirmaciones de un clic');
  card(s, 0.6, 1.85, 5.95, 3.35);
  pill(s, 'NUEVA CVE', 0.9, 2.12, 1.75, C.redL, C.red, 12);
  txt(s, 'Pagos Digitales', 0.9, 2.75, 5.3, 0.5, 22, C.navy, true);
  txt(s, 'CVSS 9.1 · detectada hoy', 0.9, 3.3, 5.3, 0.35, 15, C.gray);
  txt(s, 'Dueña: María P. · Equipo: Pagos', 0.9, 3.72, 5.3, 0.35, 15, C.gray);
  txt(s, 'Aviso al momento, no en la próxima campaña.', 0.9, 4.4, 5.3, 0.4, 15, C.blue, true);

  card(s, 6.85, 1.85, 5.88, 3.35);
  txt(s, '¿Confirmas este responsable?', 7.15, 2.12, 5.3, 0.45, 20, C.navy, true);
  txt(s, 'La sugerencia salió de los commits; el dueño la confirma en un clic.', 7.15, 2.7, 5.3, 0.75, 15, C.gray);
  pill(s, 'Sí, es correcto', 7.15, 3.6, 2.2, C.blue, C.white, 13, 0.45);
  pill(s, 'No, es otro equipo', 9.55, 3.6, 2.55, C.iceL, C.navy, 13, 0.45);
  txt(s, 'Límite de preguntas por persona · escalamiento al arquitecto.', 7.15, 4.35, 5.3, 0.6, 13, C.gray);

  ico(s, 'FaBell', 0.6, 5.55, 0.42, C.amber);
  txt(s, 'Eventos que disparan un aviso', 1.15, 5.55, 6.0, 0.42, 15, C.navy, true, { valign: 'middle' });
  const ev = [['CVE', 1.0], ['Fin de vida', 1.65], ['Contrato por vencer', 2.6], ['Discrepancia', 1.85], ['Atributo faltante', 2.35]];
  let x = 0.6;
  ev.forEach(([t, w]) => { pill(s, t, x, 6.12, w, C.white, C.navy, 13, 0.45); x += w + 0.2; });
  foot(s, 7, '1.3');
  notes(s, 'El sistema avisa al momento y pregunta solo lo que las reglas no resolvieron. La lógica de a quién y cuándo es determinista; el LLM solo redacta.');
}

// ---------------------------------------------------------------- 8. Valor para el equipo
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'El sistema también trabaja para el equipo');
  sub(s, 'La reciprocidad es el incentivo para reportar');
  const vals = [
    ['FaIdCard', 'Su ficha, sus CVE, su EOL', 'El dato le sirve a quien lo reporta, no solo a Arquitectura.'],
    ['FaSearch', 'Consulta abierta a todo TI', 'Lectura con permisos heredados sobre datos públicos e internos.'],
    ['FaBell', 'Avisos, no campañas', 'El sistema avisa cuando algo cambia; no hay que perseguir a nadie.'],
  ];
  vals.forEach(([icon, t, b], i) => {
    const x = 0.6 + i * 4.13;
    card(s, x, 1.9, 3.9, 3.6);
    ico(s, icon, x + 0.3, 2.2, 0.6);
    txt(s, t, x + 0.3, 3.05, 3.3, 0.85, 19, C.navy, true);
    txt(s, b, x + 0.3, 3.95, 3.3, 1.3, 15, C.gray);
  });
  takeaway(s, 'Reportar deja de ser una carga unilateral.', C.blue, 6.05);
  foot(s, 8, '1.1');
  notes(s, 'La reciprocidad es el incentivo: el equipo ve su ficha, sus vulnerabilidades y su fin de vida, y puede consultar el portafolio completo.');
}

// ---------------------------------------------------------------- 9. Regla de gobierno
{
  const s = pres.addSlide();
  bg(s, C.navy);
  title(s, 'La IA propone con evidencia; la persona dispone', true);
  sub(s, 'Dos carriles de publicación y una compuerta humana', true);
  card(s, 0.6, 1.85, 2.9, 3.75, C.deep);
  ico(s, 'FaRobot', 0.9, 2.15, 0.7, C.blue);
  txt(s, 'Propuesta con evidencia', 0.9, 3.05, 2.4, 0.8, 18, C.white, true);
  txt(s, 'Un agente propone un valor y cita su fuente.', 0.9, 3.9, 2.4, 1.0, 14, C.ice);
  const y1 = 1.85, y2 = 3.95, lh = 1.65;
  // lane 1: automatic
  conn(s, 3.5, y1 + lh / 2, 4.2, y1 + lh / 2, C.ice, { width: 2 });
  card(s, 4.2, y1, 8.53, lh, C.deep);
  label(s, 'Automático', 4.5, y1 + 0.22, 7.9, C.ice);
  txt(s, 'Solo atributos técnicos deterministas: stack, versiones, dependencias, endpoints.', 4.5, y1 + 0.58, 7.9, 0.4, 16, C.white, true);
  txt(s, 'Publicación directa · con procedencia · reversible por cualquier persona', 4.5, y1 + 1.05, 7.9, 0.4, 14, C.ice);
  // lane 2: gated by a person
  const gy = y2 + lh / 2;
  conn(s, 3.5, gy, 4.2, gy, C.yellow, { width: 2 });
  ico(s, 'FaUserCheck', 4.25, gy - 0.48, 0.96, C.yellow);
  txt(s, 'persona', 4.0, gy + 0.52, 1.46, 0.3, 12, C.yellow, true, { align: 'center' });
  conn(s, 5.21, gy, 5.75, gy, C.yellow, { width: 2 });
  card(s, 5.75, y2, 6.98, lh, C.deep);
  label(s, 'Requiere aprobación', 6.05, y2 + 0.22, 6.4, C.yellow);
  txt(s, 'Dueño, criticidad, costo, contrato, huérfanos y fusiones de identidad.', 6.05, y2 + 0.58, 6.4, 0.65, 16, C.white, true);
  txt(s, 'Aprobador distinto de quien propone', 6.05, y2 + 1.17, 6.4, 0.35, 14, C.ice);
  takeaway(s, 'Ningún agente aprueba.', C.yellow, 6.05);
  foot(s, 9, '3.1', true);
  notes(s, 'La regla es simple: la IA propone con evidencia y la persona dispone. La publicación automática se limita a atributos técnicos deterministas, trazables y reversibles; todo lo demás pasa por una persona distinta de quien propone.');
}

// ---------------------------------------------------------------- 10. Riesgos OCDE
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Diez dimensiones, cinco principios');
  sub(s, 'Principios OCDE (2024) y UNESCO (2021) desplegados en riesgos con mitigación por diseño');
  const pr = [['Crecimiento inclusivo', 2.3], ['Derechos y equidad', 2.1], ['Transparencia', 1.65], ['Robustez', 1.25], ['Rendición de cuentas', 2.3]];
  let px = 0.6;
  pr.forEach(([t, w]) => { pill(s, t, px, 1.65, w, C.blueL, C.navy, 13, 0.42); px += w + 0.15; });
  label(s, 'Riesgo', 0.6, 2.35, 4.6, C.amber);
  label(s, 'Mitigación por diseño', 6.0, 2.35, 6.5, C.blue);
  const rows = [
    ['FaLink', 'Vinculación errónea', 'Score y umbral; huérfanos y conflictos siempre a revisión humana.'],
    ['FaUserShield', 'Datos personales', 'Minimización y seudonimización de autores y firmantes.'],
    ['FaHourglassHalf', 'Fatiga de revisión', 'Límite de preguntas, métricas de cola y priorización por lotes.'],
    ['FaUserCog', 'Sesgo de automatización', 'Aprobar solo tras ver evidencia y diferencias; sin lotes de baja confianza.'],
  ];
  rows.forEach(([icon, r, m], i) => {
    const y = 2.75 + i * 0.86;
    card(s, 0.6, y, 4.9, 0.7);
    ico(s, icon, 0.75, y + 0.12, 0.46, C.amber);
    txt(s, r, 1.4, y, 3.95, 0.7, 15, C.navy, true, { valign: 'middle' });
    conn(s, 5.55, y + 0.35, 5.95, y + 0.35, C.gray);
    card(s, 6.0, y, 6.73, 0.7, C.greenL);
    txt(s, m, 6.25, y, 6.3, 0.7, 14, C.ink, false, { valign: 'middle' });
  });
  txt(s, 'Criterios de aceptabilidad por dimensión: A · A+C · NA', 0.6, 6.35, 12.1, 0.3, 13, C.gray);
  foot(s, 10, '2 y 3');
  notes(s, 'Los cinco principios de la OCDE se despliegan en diez dimensiones. Cada riesgo relevante tiene una mitigación incorporada en el diseño, no un control posterior.');
}

// ---------------------------------------------------------------- 11. Datos y roles
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Cada dato tiene un nivel y un lector');
  sub(s, 'Cuatro niveles de clasificación y acceso por rol');
  const levels = [
    ['FaGlobe', 'Público', 'Fuentes abiertas: CVE, EOL', C.greenL, C.green],
    ['FaBuilding', 'Interno', 'Catálogo y dependencias', C.blueL, C.blue],
    ['FaLock', 'Confidencial', 'Contratos, montos, firmantes', C.amberL, C.amber],
    ['FaBan', 'Restringido', 'Secretos y datos sensibles', C.redL, C.red],
  ];
  levels.forEach(([icon, t, d, fill, color], i) => {
    const y = 1.85 + i * 1.03;
    card(s, 0.6, y, 6.6, 0.86, fill);
    ico(s, icon, 0.8, y + 0.19, 0.48, color);
    txt(s, t, 1.5, y, 1.8, 0.86, 17, color, true, { valign: 'middle' });
    txt(s, d, 3.35, y, 3.7, 0.86, 15, C.ink, false, { valign: 'middle' });
  });
  txt(s, 'Los Restringidos no se cargan nunca.', 0.6, 6.1, 6.6, 0.4, 17, C.red, true);

  card(s, 7.5, 1.85, 5.23, 3.95);
  label(s, 'Por rol', 7.8, 2.1, 4.6);
  const roles = [
    ['Lectura', 'Todo TI · datos públicos e internos'],
    ['Edición', 'Equipos de aplicación · su ficha'],
    ['Aprobación', 'Gobierno de Arquitectura'],
    ['Descarga', 'Según rol y nivel de detalle'],
  ];
  roles.forEach(([t, d], i) => {
    const y = 2.6 + i * 0.78;
    txt(s, t, 7.8, y, 4.7, 0.32, 15, C.navy, true);
    txt(s, d, 7.8, y + 0.33, 4.7, 0.32, 14, C.gray);
  });
  foot(s, 11, '4.3');
  notes(s, 'Cuatro niveles de clasificación y una segmentación por rol: lectura, edición, aprobación y descarga. Los confidenciales solo para autorizados; los restringidos no se cargan.');
}

// ---------------------------------------------------------------- 12. Gobernanza de agentes
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Un agente se puede detener');
  sub(s, 'Tres niveles de detención, de menor a mayor alcance');
  const levels = [
    ['FaPowerOff', '1 · Detener un agente', 'Se revoca su identidad o sus herramientas. El resto sigue operando.'],
    ['FaEye', '2 · Solo lectura', 'No crea borradores, no publica, no envía micro-nudges.'],
    ['FaKeyboard', '3 · Sin IA', 'La interfaz usa búsqueda y filtros; el registro manual continúa.'],
  ];
  levels.forEach(([icon, t, b], i) => {
    const x = 0.6 + i * 4.13;
    card(s, x, 1.85, 3.9, 2.65, i === 2 ? C.amberL : C.white);
    ico(s, icon, x + 0.3, 2.12, 0.6, i === 2 ? C.amber : C.blue);
    txt(s, t, x + 0.3, 2.9, 3.3, 0.42, 19, C.navy, true);
    txt(s, b, x + 0.3, 3.4, 3.3, 1.0, 15, C.gray);
    if (i < 2) conn(s, x + 3.92, 3.17, x + 4.11, 3.17, C.blue, { width: 2 });
  });
  label(s, 'Controles transversales', 0.6, 4.85, 6.0);
  const ctl = [
    ['FaIdBadge', 'Identidad propia y mínimo privilegio para cada agente.'],
    ['FaClipboardList', 'Bitácora por acción: evidencia, score, versión y aprobador.'],
    ['FaVial', 'La detención se simula antes de escalar.'],
  ];
  ctl.forEach(([icon, t], i) => {
    const x = 0.6 + i * 4.13;
    ico(s, icon, x, 5.3, 0.48, C.gray);
    txt(s, t, x + 0.65, 5.27, 3.25, 0.85, 15, C.ink);
  });
  foot(s, 12, '4.2 y 4.5');
  notes(s, 'Tres niveles de detención: detener un agente, modo solo lectura y operar sin IA. Un interruptor que no se ha probado no es un control.');
}

// ---------------------------------------------------------------- 13. ¿Funciona?
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Qué se midió y qué no');
  sub(s, 'Lo que prueba el prototipo y lo que todavía no');
  const stats = [
    ['36', 'casos de prueba en el prototipo'],
    ['26 / 10', 'casos de calibración y de evaluación'],
    ['49', 'combinaciones de parámetros probadas'],
    ['0,85', 'umbral propuesto, aún sin calibrar'],
  ];
  stats.forEach(([n, l], i) => {
    const x = 0.6 + i * 3.08;
    const dark = i === 0;
    card(s, x, 1.75, 2.9, 1.85, dark ? C.navy : C.white);
    txt(s, n, x + 0.3, 1.9, 2.4, 0.9, 44, dark ? C.yellow : C.blue, true);
    txt(s, l, x + 0.3, 2.85, 2.4, 0.65, 14, dark ? C.white : C.gray);
  });
  const status = [
    ['Pipeline medible', 'El score y el umbral se pueden medir y comparar.', C.green, C.greenL],
    ['Calibración no concluyente', 'La combinación ganadora no generaliza.', C.amber, C.amberL],
    ['Gobernanza no evaluada', 'Aprobaciones, roles y política aún no operan.', C.gray, C.iceL],
  ];
  status.forEach(([t, d, color, fill], i) => {
    const x = 0.6 + i * 4.13;
    card(s, x, 3.95, 3.9, 1.85, fill);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.3, y: 4.2, w: 0.34, h: 0.34, fill: { color }, line: { color, width: 0.5 } });
    txt(s, t, x + 0.8, 4.17, 2.95, 0.4, 16, C.navy, true);
    txt(s, d, x + 0.3, 4.75, 3.3, 0.9, 15, C.ink);
  });
  takeaway(s, 'Evidencia de diseño, no de operación.', C.amber);
  foot(s, 13, '1.4');
  notes(s, 'La corrida prueba que el pipeline es medible; no prueba que el modelo de gobernanza funcione en operación. La calibración no fue concluyente.');
}

// ---------------------------------------------------------------- 14. Hoja de ruta
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Cuatro hitos, cuatro compuertas');
  sub(s, 'Una hoja de ruta sin fechas, con condiciones de avance');
  const hitos = [
    ['1', 'Cimientos y calibración', 'Lote ampliado, umbral documentado, permisos aprobados.'],
    ['2', 'Catálogo núcleo', 'Auditoría, CVE y EOL vinculados, cambios con aprobador.'],
    ['3', 'Descubrimiento técnico', 'Score calibrado, cola en plazo, cero publicaciones sin evidencia.'],
    ['4', 'Contratos y analítica', 'Evidencia citada, micro-nudges en plazo, revisión sin hallazgos.'],
  ];
  hitos.forEach(([n, t, g], i) => {
    const x = 0.6 + i * 3.08;
    card(s, x, 1.85, 2.9, 3.95, i === 0 ? C.blueL : C.white);
    chip(s, n, x + 0.25, 2.12, 0.46, i === 0 ? C.blue : C.amber);
    txt(s, `HITO ${n}`, x + 0.85, 2.12, 1.8, 0.46, 12, C.gray, true, { valign: 'middle', charSpacing: 1 });
    txt(s, t, x + 0.25, 2.8, 2.45, 0.85, 18, C.navy, true);
    txt(s, 'Compuerta', x + 0.25, 3.8, 2.45, 0.3, 12, C.blue, true);
    txt(s, g, x + 0.25, 4.15, 2.45, 1.5, 14, C.ink);
  });
  takeaway(s, 'Sin fechas: la compuerta se abre con evidencia.');
  foot(s, 14, '6.3');
  notes(s, 'La hoja de ruta no fija fechas: fija orden, dependencias y compuertas. Cada organización adapta el punto de entrada y la duración.');
}

// ---------------------------------------------------------------- 15. Adopción
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'La adopción es política, no solo técnica');
  sub(s, 'Un ciclo que se sostiene con tres palancas');
  card(s, 0.6, 1.75, 6.0, 4.6);
  const d = 0.95;
  const nodes = [
    ['FaEdit', 'Reportar', 'La ficha se mantiene al día con bajo costo.', 3.6, 2.55],
    ['FaSearch', 'Usar', 'El equipo consulta su ficha y el portafolio.', 5.2, 4.7],
    ['FaCheck', 'Confiar', 'El dato sirve para decidir y se defiende.', 2.0, 4.7],
  ];
  nodes.forEach(([, , , x1, y1], i) => {
    const [, , , x2, y2] = nodes[(i + 1) % 3];
    const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), k = (d / 2 + 0.1) / L;
    conn(s, x1 + dx * k, y1 + dy * k, x2 - dx * k, y2 - dy * k, C.blue, { width: 2 });
  });
  nodes.forEach(([icon, t, b, x, y], i) => {
    ico(s, icon, x - d / 2, y - d / 2, d, i === 2 ? C.yellow : C.blue);
    if (i === 0) {
      txt(s, t, 0.85, y - 0.5, 2.15, 0.4, 18, C.navy, true, { align: 'right' });
      txt(s, b, 0.85, y - 0.08, 2.15, 0.7, 13, C.gray, false, { align: 'right' });
    } else {
      txt(s, t, x - 1.15, y + 0.55, 2.3, 0.4, 18, C.navy, true, { align: 'center' });
      txt(s, b, x - 1.15, y + 0.93, 2.3, 0.6, 13, C.gray, false, { align: 'center' });
    }
  });
  const levers = [
    ['FaGavel', 'Política', 'La Dirección de TI hace de mantener la ficha parte del proceso.'],
    ['FaExchangeAlt', 'Reciprocidad', 'Consulta abierta y avisos por evento: el sistema devuelve valor.'],
    ['FaTachometerAlt', 'Capacidad', 'Carga de revisión medida; si se supera, se ajusta el umbral o se priorizan lotes.'],
  ];
  levers.forEach(([icon, t, b], i) => {
    const y = 1.75 + i * 1.6;
    card(s, 6.9, y, 5.83, 1.4);
    ico(s, icon, 7.15, y + 0.25, 0.55, C.amber);
    txt(s, t, 7.95, y + 0.22, 4.6, 0.38, 17, C.navy, true);
    txt(s, b, 7.95, y + 0.62, 4.6, 0.7, 14, C.gray);
  });
  foot(s, 15, '6.3');
  notes(s, 'La adopción no se sostiene solo con el sistema: necesita una política de la Dirección, reciprocidad para el equipo y medición de la carga de revisión.');
}

// ---------------------------------------------------------------- 16. Modelo institucional
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Quién responde por qué');
  sub(s, 'Cada publicación tiene un responsable humano');
  const cx = 6.667, bw = 4.4;
  card(s, cx - bw / 2, 1.8, bw, 0.95, C.navy);
  txt(s, 'Dirección de TI', cx - bw / 2 + 0.3, 1.9, bw - 0.6, 0.4, 17, C.white, true);
  txt(s, 'patrocina la política', cx - bw / 2 + 0.3, 2.3, bw - 0.6, 0.35, 14, C.ice);
  vline(s, cx, 2.75, 0.3);
  card(s, cx - bw / 2, 3.05, bw, 0.95, C.blue);
  txt(s, 'Arquitectura TI', cx - bw / 2 + 0.3, 3.15, bw - 0.6, 0.4, 17, C.white, true);
  txt(s, 'dueña del producto y de los agentes', cx - bw / 2 + 0.3, 3.55, bw - 0.6, 0.35, 14, C.white);
  vline(s, cx, 4.0, 0.35);
  const roles = [
    ['FaGavel', 'Gobierno de Arquitectura', 'aprueba atributos críticos', C.yellow],
    ['FaShieldAlt', 'Seguridad', 'controla permisos y entorno', C.green],
    ['FaDatabase', 'Datos', 'clasifica y autoriza fuentes', C.blue],
    ['FaClipboardList', 'Auditoría', 'revisa la bitácora', C.gray],
  ];
  const w = 2.9, gap = 0.18, xs = roles.map((_, i) => 0.6 + i * (w + gap));
  hline(s, xs[0] + w / 2, 4.35, xs[3] - xs[0]);
  roles.forEach(([icon, t, d, fill], i) => {
    const x = xs[i];
    vline(s, x + w / 2, 4.35, 0.3);
    card(s, x, 4.65, w, 1.75);
    ico(s, icon, x + 0.25, 4.88, 0.5, fill);
    txt(s, t, x + 0.9, 4.85, w - 1.1, 0.6, 16, C.navy, true, { valign: 'middle' });
    txt(s, d, x + 0.25, 5.62, w - 0.5, 0.6, 14, C.gray);
  });
  foot(s, 16, '6.1');
  notes(s, 'La Dirección patrocina; Arquitectura TI es dueña; Gobierno de Arquitectura aprueba; Seguridad, Datos y Auditoría controlan. Cada publicación tiene un responsable humano.');
}

// ---------------------------------------------------------------- 17. Conclusiones
{
  const s = pres.addSlide();
  bg(s, C.navy);
  title(s, 'Tres ideas para llevarse', true);
  sub(s, 'Lo esencial del modelo en tres frases', true);
  const ideas = [
    ['01', 'El cuello de botella es captura e identidad', 'No falta análisis: falta un sistema que mantenga el catálogo sin fricción.'],
    ['02', 'La IA se gobierna con evidencia y compuertas', 'Cada dato cita su fuente; cada avance se gana con una compuerta.'],
    ['03', 'La adopción es política, no solo técnica', 'Sin política y reciprocidad, el sistema se usa una vez y se abandona.'],
  ];
  ideas.forEach(([n, t, b], i) => {
    const y = 1.95 + i * 1.6;
    card(s, 0.6, y, 12.13, 1.35, C.deep);
    txt(s, n, 0.9, y, 1.0, 1.35, 32, C.yellow, true, { valign: 'middle' });
    txt(s, t, 2.0, y + 0.25, 10.4, 0.5, 22, C.white, true);
    txt(s, b, 2.0, y + 0.77, 10.4, 0.45, 16, C.ice);
  });
  foot(s, 17, '7', true);
  notes(s, 'Cerrar con las tres ideas antes de abrir las preguntas.');
}

// ---------------------------------------------------------------- 18. Gracias
{
  const s = pres.addSlide();
  bg(s, C.navy);
  hub(s, 3.6, 3.75, 1.95, 'FaCheck');
  txt(s, 'Gracias', 7.0, 2.3, 5.7, 1.1, 60, C.white, true);
  txt(s, 'Un catálogo vivo y gobernado: la IA propone, la persona dispone.', 7.0, 3.55, 5.5, 0.9, 20, C.ice);
  txt(s, 'Preguntas', 7.0, 4.75, 5.5, 0.5, 22, C.yellow, true);
  foot(s, 18, null, true);
  notes(s, 'Abrir las preguntas. Los respaldos cubren calibración y proveedor.');
}

// ---------------------------------------------------------------- 19. Respaldo calibración
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Calibración: qué dicen los números');
  sub(s, 'Respaldo · calibración del score con 36 casos');
  txt(s, 'Tabla — Exactitud y F1 por combinación de parámetros', 0.6, 1.85, 12.1, 0.3, 12, C.gray, false, { italic: true });
  const head = { bold: true, color: C.navy, fill: { color: C.iceL } };
  const rows = [
    [{ text: 'Parámetros', options: head }, { text: 'Calibración (n=26)', options: head }, { text: 'Evaluación (n=10)', options: head }],
    [{ text: '0,60 / 0,01', options: { bold: true } }, '92,3 % · F1 91,1 %', '70,0 % · F1 59,9 %'],
    [{ text: '0,50 / 0,05', options: { bold: true } }, '84,6 % · F1 81,9 %', '80,0 % · F1 81,7 %'],
  ];
  s.addTable(rows, {
    x: 0.6, y: 2.25, w: 12.13, colW: [3.33, 4.4, 4.4],
    fontFace: F, fontSize: 16, color: C.ink,
    border: { type: 'solid', color: C.ice, pt: 1 },
    fill: { color: C.white }, rowH: 0.62, valign: 'middle', align: 'left', margin: 0.12,
  });
  bullets(s, [
    'Intervalos de confianza del 95 % solapados: 76–98 %, 40–89 % y 49–94 %.',
    'Se eligió la mejor de 49 combinaciones sobre 26 casos: riesgo de sobreajuste.',
  ], 0.6, 4.6, 12.1, 1.2, 16, C.ink);
  takeaway(s, 'Los umbrales siguen como propuestas; el detalle está en el MVP.', C.amber, 6.15);
  foot(s, 19, '1.4');
  notes(s, 'Respaldo para preguntas de metodología: splits, métricas, intervalos, sobreajuste y protocolo de etiquetado.');
}

// ---------------------------------------------------------------- 20. Respaldo proveedor
{
  const s = pres.addSlide();
  bg(s, C.canvas);
  title(s, 'Si ya tienes un proveedor');
  sub(s, 'Respaldo · capacidades mínimas antes de adoptar un producto');
  const cols = [
    ['Capacidades técnicas', ['Exportación completa por API en formato abierto', 'Identificador estable con claves externas', 'Procedencia y auditoría por atributo', 'Permisos por rol con aprobaciones registradas']],
    ['Capacidades contractuales', ['Propiedad del dato', 'Retención definida', 'Ruta de salida con migración asistida']],
  ];
  cols.forEach(([h, items], i) => {
    const x = 0.6 + i * 6.25;
    card(s, x, 1.85, 5.88, 3.9);
    label(s, h, x + 0.35, 2.12, 5.2);
    bullets(s, items, x + 0.35, 2.65, 5.2, 2.9, 16, C.ink);
  });
  takeaway(s, 'Si falta una, sirve como fuente, no como registro maestro.', C.amber, 6.15);
  foot(s, 20, '4.1');
  notes(s, 'Respaldo para la pregunta de proveedor: cuatro capacidades técnicas y tres contractuales. Sin ellas, el proveedor puede ser fuente, pero no registro maestro.');
}

// ---------------------------------------------------------------- guardar
await pres.writeFile({ fileName: 'GobIA_TF_Presentacion_Final.pptx' });
console.log('OK: GobIA_TF_Presentacion_Final.pptx');
}

main().catch((e) => { console.error(e); process.exit(1); });
