#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { sync, sources } from './sync.mjs';
import { root, dataDir, findRuntime } from './runtime.mjs';
import { ContextClient, resultText } from './mcp-client.mjs';

try {
  const [command = 'info', ...args] = process.argv.slice(2);
  if (command === 'info') {
    const runtime = findRuntime();
    console.log(JSON.stringify({ root, dataDir, runtime,
      version: JSON.parse(readFileSync(join(runtime, 'package.json'), 'utf8')).version,
      sourceCount: sources().files.length, missing: sources().missing }, null, 2));
  } else if (command === 'sync') {
    console.log(JSON.stringify(await sync(), null, 2));
  } else if (command === 'search') {
    if (!args.length) throw new Error('Uso: node tools/ai-context/context.mjs search "términos"');
    const client = new ContextClient('codex', dataDir, { bootstrap: true });
    try {
      await client.connect();
      console.log(resultText(await client.call('ctx_search', {
        queries: [args.join(' ')], source: 'S3G4/', sort: 'timeline', limit: 4,
      })));
    } finally { await client.close(); }
  } else {
    throw new Error('Comandos: info, sync, search');
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
