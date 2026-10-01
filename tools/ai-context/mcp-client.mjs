// Small JSON-RPC stdio client for synchronization and checks; no external dependencies.
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { once } from 'node:events';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';
import { root, dataDir, environment } from './runtime.mjs';

export function resultText(result) {
  return (result.content || []).filter(c => c.type === 'text').map(c => c.text).join('\n');
}

export class ContextClient {
  constructor(platform = 'codex', storage = dataDir, { bootstrap = false, cwd = root } = {}) {
    this.platform = platform;
    this.nextId = 0;
    this.pending = new Map();
    this.stderr = '';
    this.child = spawn(process.execPath, [join(root, 'tools/ai-context/server.mjs'), platform,
      '--storage', storage, ...(bootstrap ? [] : ['--raw'])], {
      cwd, env: { ...environment(platform, storage), CLAUDE_SESSION_ID: randomUUID(),
        CODEX_THREAD_ID: randomUUID(), GEMINI_SESSION_ID: randomUUID() },
      windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'],
    });
    this.lines = createInterface({ input: this.child.stdout });
    this.child.stderr.on('data', b => { this.stderr = (this.stderr + b).slice(-6000); });
    const fail = error => {
      this.failure = error;
      for (const { reject, timer } of this.pending.values()) { clearTimeout(timer); reject(error); }
      this.pending.clear();
    };
    this.child.on('error', fail);
    this.child.on('exit', code => fail(new Error(`MCP terminó (${code}). ${this.stderr}`)));
    this.child.stdin.on('error', fail);
    this.lines.on('line', line => {
      let message;
      try { message = JSON.parse(line); } catch { return; }
      if (message.method && message.id !== undefined) {
        if (message.method === 'roots/list') {
          this.send({ id: message.id, result: { roots: [{ uri: pathToFileURL(root).href, name: 'S3G4 LAB' }] } });
        } else {
          this.send({ id: message.id, error: { code: -32601, message: 'Method not supported' } });
        }
        return;
      }
      const pending = this.pending.get(message.id);
      if (!pending) return;
      clearTimeout(pending.timer);
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
      else pending.resolve(message.result);
    });
  }
  send(message) { this.child.stdin.write(JSON.stringify({ jsonrpc: '2.0', ...message }) + '\n'); }
  request(method, params = {}, timeout = 60000) {
    if (this.failure) return Promise.reject(this.failure);
    return new Promise((resolve, reject) => {
      const id = ++this.nextId;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Tiempo agotado: ${method}. ${this.stderr}`));
      }, timeout);
      this.pending.set(id, { resolve, reject, timer });
      this.send({ id, method, params });
    });
  }
  async connect() {
    const names = { codex: 'codex', 'claude-code': 'claude-code', 'antigravity-cli': 'agy' };
    const info = await this.request('initialize', {
      protocolVersion: '2024-11-05', capabilities: { roots: { listChanged: false } },
      clientInfo: { name: names[this.platform], version: 's3g4-context-1' },
    });
    this.send({ method: 'notifications/initialized' });
    return info;
  }
  async call(name, args) {
    const result = await this.request('tools/call', { name, arguments: args });
    if (result.isError) throw new Error(`${name}: ${resultText(result)}`);
    return result;
  }
  async close() {
    if (this.child.exitCode !== null || this.child.signalCode !== null) return;
    const exit = once(this.child, 'exit').catch(() => {});
    this.child.stdin.end();
    const timer = setTimeout(() => this.child.kill(), 2500);
    await exit;
    clearTimeout(timer);
    this.lines.close();
  }
}
