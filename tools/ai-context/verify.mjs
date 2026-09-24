// Integration tests against the real installed context-mode MCP, no model calls.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { root, dataDir } from './runtime.mjs';
import { ContextClient, resultText } from './mcp-client.mjs';
import { sync } from './sync.mjs';

const platforms = ['codex', 'claude-code', 'antigravity-cli'];
const storage = join(dataDir, 'verification', randomUUID());
mkdirSync(storage, { recursive: true });
const clients = [];
const checks = [];
const started = performance.now();
const note = message => { checks.push(message); console.log('PASS ' + message); };

try {
  // Exercise auto-indexing at the same time, including lock contention and cwd isolation.
  for (const platform of platforms) {
    clients.push(new ContextClient(platform, storage, { bootstrap: true, cwd: join(root, 'firmware') }));
  }
  await Promise.all(clients.map(async (client, i) => {
    await client.connect();
    const tools = (await client.request('tools/list')).tools;
    for (const name of ['ctx_search', 'ctx_index', 'ctx_execute', 'ctx_execute_file']) {
      assert(tools.some(t => t.name === name), `${platforms[i]} missing ${name}`);
    }
    if (platforms[i] === 'antigravity-cli') {
      const json = JSON.stringify(tools.map(t => t.inputSchema));
      assert(!/"(?:const|additionalProperties)":/.test(json), 'agy incompatible schema');
    }
    note(`${platforms[i]}: arranque automático desde subcarpeta y herramientas MCP`);
  }));

  const source = 'S3G4-verification/shared-probe';
  const first = 's3g4probe' + randomUUID().replaceAll('-', '');
  await clients[0].call('ctx_index', { content: '# Comprobación compartida\n\n' + first, source });
  for (let i = 1; i < clients.length; i++) {
    const result = resultText(await clients[i].call('ctx_search', { queries: [first], source, sort: 'timeline' }));
    assert(result.includes(first), `Lectura cruzada falló para ${platforms[i]}`);
    note(`Codex escribe → ${platforms[i]} recupera en otra sesión`);
  }

  const second = 's3g4update' + randomUUID().replaceAll('-', '');
  await clients[1].call('ctx_index', { content: '# Comprobación actualizada\n\n' + second, source });
  const updated = resultText(await clients[2].call('ctx_search', { queries: [second], source, sort: 'timeline' }));
  assert(updated.includes(second));
  assert(!updated.includes(first));
  note('Claude actualiza → agy obtiene la versión nueva');

  // A file-backed source must refresh after its file changes, without manual re-indexing.
  const file = join(storage, 'freshness.md');
  const before = 's3g4freshnessbefore' + randomUUID().replaceAll('-', '');
  const after = 's3g4freshnessafter' + randomUUID().replaceAll('-', '');
  writeFileSync(file, '# Vigencia\n\n' + before);
  const fileSource = 'S3G4-verification/file-freshness';
  await clients[0].call('ctx_index', { path: file, source: fileSource });
  writeFileSync(file, '# Vigencia\n\n' + after);
  const refreshed = resultText(await clients[2].call('ctx_search', { queries: [after], source: fileSource, sort: 'timeline' }));
  assert(refreshed.includes(after), 'El índice no actualizó el archivo modificado');
  note('Archivo modificado: búsqueda actualiza el contenido');

  await Promise.all(clients.map((client, i) => client.call('ctx_index', {
    content: '# Escritura concurrente\n\nconcurrentS3G4' + i,
    source: 'S3G4-verification/concurrent-' + i,
  })));
  note('Tres escritores concurrentes sin bloqueo SQLite');

  const knowledge = resultText(await clients[0].call('ctx_search', {
    queries: ['M-09 teléfono', 'M-10 pendiente'], source: 'S3G4/ai-context/STATE.md', sort: 'timeline', limit: 3,
  }));
  assert(knowledge.includes('M-09') && knowledge.includes('M-10'));
  note('Recuperación del estado real del proyecto');

  await Promise.all(clients.map(client => client.close()));
  const restarted = new ContextClient('antigravity-cli', storage);
  clients.push(restarted);
  await restarted.connect();
  const persisted = resultText(await restarted.call('ctx_search', { queries: [second], source, sort: 'timeline' }));
  assert(persisted.includes(second));
  note('Persistencia después de cerrar y volver a abrir los procesos');

  // A source removed from the manifest must not remain as an apparently valid fact.
  const retiredDir = join(storage, 'retirement');
  const former = join(storage, 'former.md');
  writeFileSync(former, '# Fuente temporal\n\nobsoleteS3G4fact');
  await sync('codex', retiredDir, () => ({ files: [former], missing: [] }));
  await sync('codex', retiredDir, () => ({ files: [], missing: [] }));
  const retiredClient = new ContextClient('claude-code', retiredDir);
  clients.push(retiredClient);
  await retiredClient.connect();
  const retirement = resultText(await retiredClient.call('ctx_search', {
    queries: ['Fuente retirada'], source: 'S3G4/', sort: 'timeline',
  }));
  assert(retirement.includes('Fuente retirada') && !retirement.includes('obsoleteS3G4fact'));
  note('Fuente retirada: sustituida por aviso, sin conservar su afirmación antigua');

  for (const file of ['AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agents/rules/s3g4-context.md', '.codex/config.toml', '.mcp.json', '.agents/mcp_config.json']) {
    assert(existsSync(join(root, file)), 'Falta ' + file);
  }
  for (const file of ['.mcp.json', '.agents/mcp_config.json']) {
    const config = JSON.parse(readFileSync(join(root, file), 'utf8'));
    const entry = config.mcpServers['s3g4-context'];
    assert(existsSync(entry.command));
    assert(existsSync(entry.args[0]));
  }
  note('Archivos de arranque y rutas MCP presentes');

  const report = { ok: true, timestamp: new Date().toISOString(), seconds: Math.round((performance.now() - started) / 1000), checks, storage };
  writeFileSync(join(dataDir, 'verification-result.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  console.error('FAIL ' + error.message);
  process.exitCode = 1;
} finally {
  await Promise.all(clients.map(client => client.close()));
}
