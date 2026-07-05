import assert from 'node:assert/strict';
import { existsSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const NODE = process.execPath;

function runNode(args) {
  return spawnSync(NODE, args, {
    cwd: ROOT,
    encoding: 'utf8',
    env: { ...process.env, NO_COLOR: '1' },
  });
}

function runPython(args) {
  const candidates = process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python'];
  for (const cmd of candidates) {
    const probeArgs = cmd === 'py' ? ['-3', '--version'] : ['--version'];
    const probe = spawnSync(cmd, probeArgs, { cwd: ROOT, encoding: 'utf8' });
    if (probe.status === 0) {
      const finalArgs = cmd === 'py' ? ['-3', ...args] : args;
      return spawnSync(cmd, finalArgs, { cwd: ROOT, encoding: 'utf8' });
    }
  }
  return null;
}

test('installer help launches', () => {
  const result = runNode(['bin/install.js', '--help']);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /signaltrim installer/);
  assert.match(result.stdout, /--with-mcp-shrink/);
});

test('provider matrix launches', () => {
  const result = runNode(['bin/install.js', '--list']);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /SignalTrim provider matrix/);
  assert.match(result.stdout, /Claude Code/);
  assert.match(result.stdout, /Codex CLI/);
});

test('invalid CLI input exits cleanly', () => {
  const result = runNode(['bin/install.js', '--definitely-not-a-real-flag']);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /unknown flag/);
});

test('MCP shrink rejects missing upstream command', () => {
  const result = runNode(['bin/install.js', '--with-mcp-shrink']);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /requires an upstream command/);
});

test('package bin entries point at real files', () => {
  const installer = resolve(ROOT, 'bin/install.js');
  const shrink = resolve(ROOT, 'src/mcp-servers/signaltrim-shrink/index.js');
  assert.ok(existsSync(installer), 'signaltrim bin target missing');
  assert.ok(existsSync(shrink), 'signaltrim-shrink bin target missing');
  assert.ok(statSync(installer).isFile());
  assert.ok(statSync(shrink).isFile());
});

test('compression validator catches lost inline code', (t) => {
  const result = runPython([
    '-m',
    'unittest',
    'tests.test_validate_inline.TestValidateIntegration.test_validate_inline_codes_wired',
  ]);
  if (!result) {
    t.skip('python unavailable');
    return;
  }
  assert.equal(result.status, 0, result.stderr || result.stdout);
});
