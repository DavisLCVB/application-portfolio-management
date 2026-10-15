import { fileURLToPath } from 'node:url';
import { publishFiles } from './publish-files.mjs';

const presentations = await publishFiles({
  source: fileURLToPath(new URL('../../docs/', import.meta.url)),
  destination: fileURLToPath(new URL('../public/presentaciones/', import.meta.url)),
  manifest: fileURLToPath(new URL('../src/generated/presentaciones.json', import.meta.url)),
  extension: 'pptx',
  urlPrefix: '/presentaciones/',
});
console.log(`Presentaciones preparadas: ${presentations.length}`);
