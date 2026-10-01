import { existsSync, readFileSync, readdirSync, realpathSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

export const root = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), '../..'));
export const dataDir = join(root, '.ai-runtime');

export function findRuntime() {
  const local = join(root, 'ai-context/runtime.local.json');
  if (existsSync(local)) {
    const config = JSON.parse(readFileSync(local, 'utf8'));
    if (config.contextModeDir && existsSync(join(config.contextModeDir, 'server.bundle.mjs'))) {
      return config.contextModeDir;
    }
    throw new Error('runtime.local.json apunta a una instalación ausente. Actualizar contextModeDir.');
  }
  const candidates = [];
  for (const host of ['.codex', '.claude']) {
    const base = join(homedir(), host, 'plugins/cache/context-mode/context-mode');
    if (!existsSync(base)) continue;
    for (const version of readdirSync(base).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }))) {
      candidates.push(join(base, version));
    }
  }
  const found = candidates.find(p => existsSync(join(p, 'server.bundle.mjs')));
  if (!found) throw new Error('No se encontró context-mode. Configurar ai-context/runtime.local.json.');
  return found;
}

export function environment(platform, storage = dataDir) {
  if (!['codex', 'claude-code', 'antigravity-cli'].includes(platform)) {
    throw new Error('Plataforma no admitida: ' + platform);
  }
  return {
    ...process.env,
    CONTEXT_MODE_PLATFORM: platform,
    CONTEXT_MODE_PROJECT_DIR: root,
    CONTEXT_MODE_DATA_DIR: storage,
    CLAUDE_PROJECT_DIR: root,
    GEMINI_PROJECT_DIR: root,
    PWD: root,
  };
}
