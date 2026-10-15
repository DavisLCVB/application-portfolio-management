import { fileURLToPath } from 'node:url';
import { publishFiles } from './publish-files.mjs';

const documents = await publishFiles({
  source: fileURLToPath(new URL('../../docs/', import.meta.url)),
  destination: fileURLToPath(new URL('../public/documentos/', import.meta.url)),
  manifest: fileURLToPath(new URL('../src/generated/pdfs.json', import.meta.url)),
  extension: 'pdf',
  urlPrefix: '/documentos/',
});
console.log(`PDF preparados: ${documents.length}`);
