import { existsSync, readFileSync, readdirSync, realpathSync, mkdirSync, openSync, closeSync, unlinkSync, writeFileSync, renameSync } from 'node:fs';
import { join, relative, extname, isAbsolute, resolve, sep } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { root, dataDir } from './runtime.mjs';
import { ContextClient } from './mcp-client.mjs';

function checkedPath(value) {
  const candidate = resolve(root, value);
  const rel = relative(root, candidate);
  if (rel === '..' || rel.startsWith('..' + sep) || isAbsolute(rel)) throw new Error('Fuente fuera del proyecto: ' + value);
  if (existsSync(candidate)) {
    const real = relative(root, realpathSync(candidate));
    if (real === '..' || real.startsWith('..' + sep) || isAbsolute(real)) throw new Error('Enlace fuera del proyecto: ' + value);
  }
  return candidate;
}

export function sources() {
  const spec = JSON.parse(readFileSync(join(root, 'ai-context/index.json'), 'utf8'));
  const files = new Set();
  const missing = [];
  for (const name of spec.files) {
    const file = checkedPath(name);
    if (existsSync(file)) files.add(file); else missing.push(name);
  }
  function walk(folder, rule, depth = 0) {
    if (depth > 5) throw new Error('Directorio de contexto demasiado profundo: ' + folder);
    for (const entry of readdirSync(folder, { withFileTypes: true })) {
      if (entry.isSymbolicLink()) continue;
      const file = join(folder, entry.name);
      if (entry.isDirectory() && rule.recursive) walk(file, rule, depth + 1);
      else if (entry.isFile() && rule.extensions.includes(extname(file))) files.add(file);
    }
  }
  for (const rule of spec.directories) {
    const folder = checkedPath(rule.path);
    if (existsSync(folder)) walk(folder, rule); else missing.push(rule.path);
  }
  if (files.size > 250) throw new Error('Más de 250 fuentes. Acotar ai-context/index.json.');
  return { files: [...files].sort(), missing };
}

export async function sync(platform = 'codex', storage = dataDir, selection = sources) {
  mkdirSync(storage, { recursive: true });
  const lock = join(storage, 'sync.lock');
  let handle;
  const deadline = Date.now() + 50000;
  while (handle === undefined) {
    try {
      handle = openSync(lock, 'wx');
      writeFileSync(handle, String(process.pid));
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      try {
        const pid = Number(readFileSync(lock, 'utf8'));
        if (pid > 0) {
          try { process.kill(pid, 0); }
          catch (e) { if (e.code === 'ESRCH') { unlinkSync(lock); continue; } }
        }
      } catch (e) { if (e.code === 'ENOENT') continue; }
      if (Date.now() > deadline) throw new Error('Otra sincronización mantiene sync.lock; revisar su proceso.');
      await delay(150);
    }
  }
  let client;
  try {
    const { files, missing } = selection();
    const managedPath = join(storage, 'managed-sources.json');
    const previous = existsSync(managedPath) ? JSON.parse(readFileSync(managedPath, 'utf8')) : [];
    const labels = files.map(path => 'S3G4/' + relative(root, path).replaceAll('\\', '/'));
    client = new ContextClient(platform, storage);
    await client.connect();
    for (const path of files) {
      if (readFileSync(path).length > 2 * 1024 * 1024) throw new Error('Fuente supera 2 MiB: ' + path);
      await client.call('ctx_index', { path, source: 'S3G4/' + relative(root, path).replaceAll('\\', '/') });
    }
    // Replace removed sources with an explicit notice so old decisions cannot be
    // mistaken for current files. Only touch labels managed by this synchronizer.
    const removed = previous.filter(label => !labels.includes(label));
    for (const source of removed) {
      await client.call('ctx_index', {
        source,
        content: '# Fuente retirada\n\nEsta fuente ya no forma parte del índice vigente: ' + source +
          '\nNo utilizar su contenido anterior como contexto actual. Revisar ai-context/index.json y el archivo original.',
      });
    }
    const temp = managedPath + '.' + process.pid + '.tmp';
    writeFileSync(temp, JSON.stringify(labels, null, 2) + '\n');
    renameSync(temp, managedPath);
    return { indexed: files.length, retired: removed.length, missing, storage };
  } finally {
    try { if (client) await client.close(); }
    finally { closeSync(handle); unlinkSync(lock); }
  }
}
