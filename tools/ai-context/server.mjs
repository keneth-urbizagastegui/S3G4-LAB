// One project, one runtime version, one persistent store for all three clients.
import { join, resolve, relative, isAbsolute, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
import { findRuntime, root, dataDir, environment } from './runtime.mjs';

const platform = process.argv[2] || 'codex';
// Ignore a host's generic storage override: this connection belongs to S3G4.
// The optional internal argument gives integration tests an isolated local store.
const storageArg = process.argv.indexOf('--storage');
const storage = storageArg < 0 ? dataDir : resolve(process.argv[storageArg + 1]);
const storageRelative = relative(dataDir, storage);
if (storageRelative === '..' || storageRelative.startsWith('..' + sep) || isAbsolute(storageRelative)) {
  throw new Error('El almacén debe permanecer dentro de .ai-runtime/');
}
Object.assign(process.env, environment(platform, storage));
process.chdir(root);

if (!process.argv.includes('--raw')) {
  const { sync } = await import('./sync.mjs');
  const result = await sync(platform, storage);
  console.error('[s3g4-context] ' + JSON.stringify(result));
}

// The installed bundle is self-contained. Avoid start.mjs's global cache-healing
// side effects; this connection only owns project-local data.
await import(pathToFileURL(join(findRuntime(), 'server.bundle.mjs')).href);
