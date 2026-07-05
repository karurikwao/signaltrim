// End-to-end: dry-run installer prints expected file plan without touching disk.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const INSTALLER = path.resolve(HERE, '..', '..', 'bin', 'install.js');

function freshTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'cm-dryrun-'));
}

function pathWith(prependDir) {
  return `${prependDir}${path.delimiter}${process.env.PATH || ''}`;
}

function shimClaude(markerPath) {
  const dir = freshTmpDir();
  if (process.platform === 'win32') {
    fs.writeFileSync(
      path.join(dir, 'claude.cmd'),
      `@echo off\r\necho called > "${markerPath}"\r\nexit /b 0\r\n`,
    );
  } else {
    const shim = path.join(dir, 'claude');
    fs.writeFileSync(shim, `#!/bin/sh\necho called > "${markerPath}"\nexit 0\n`);
    fs.chmodSync(shim, 0o755);
  }
  return dir;
}

test('dry-run --only claude prints plan and writes nothing', () => {
  const cfg = freshTmpDir();
  const r = spawnSync('node', [INSTALLER,
    // --with-hooks: since #392/#393 the default only wires standalone hooks
    // when the plugin install fails. Force the hook-planning path so the
    // "would install / would merge" assertions below are exercised.
    '--dry-run', '--only', 'claude', '--with-hooks', '--no-mcp-shrink', '--non-interactive',
    '--config-dir', cfg,
  ], { encoding: 'utf8', env: { ...process.env, CLAUDE_CONFIG_DIR: cfg } });
  assert.equal(r.status, 0);
  // Only fires if `claude` is on PATH on the test runner. If not, this assertion
  // is a no-op (the installer just prints "nothing detected" and exits 0).
  if (/Claude Code detected/.test(r.stdout)) {
    assert.match(r.stdout, /would run: claude plugin marketplace add/);
    assert.match(r.stdout, /would run: claude plugin install signaltrim@signaltrim/);
    assert.match(r.stdout, /would mkdir -p .*[/\\]hooks/);
    assert.match(r.stdout, /would install .*signaltrim-activate\.js/);
    assert.match(r.stdout, /would merge SessionStart \+ UserPromptSubmit \+ statusline/);
  }
  // Nothing should have been written.
  assert.equal(fs.existsSync(path.join(cfg, 'settings.json')), false);
  assert.equal(fs.existsSync(path.join(cfg, 'hooks')), false);
});

test('dry-run --only claude never invokes claude CLI or writes temp state', () => {
  const cfg = freshTmpDir();
  const marker = path.join(cfg, 'claude-called.txt');
  const shimDir = shimClaude(marker);
  const r = spawnSync('node', [INSTALLER,
    '--dry-run', '--only', 'claude', '--with-hooks', '--no-mcp-shrink', '--non-interactive',
    '--config-dir', cfg,
  ], {
    encoding: 'utf8',
    env: { ...process.env, CLAUDE_CONFIG_DIR: cfg, PATH: pathWith(shimDir), NO_COLOR: '1' },
  });

  assert.equal(r.status, 0);
  assert.match(r.stdout, /Claude Code detected/);
  assert.match(r.stdout, /would run: claude plugin marketplace add/);
  assert.match(r.stdout, /would run: claude plugin install signaltrim@signaltrim/);
  assert.match(r.stdout, /would install:/);
  assert.doesNotMatch(r.stdout, /\n\s+installed:/);
  assert.equal(fs.existsSync(marker), false, 'dry-run must not call claude CLI');
  assert.deepEqual(fs.readdirSync(cfg).sort(), [], 'dry-run must not create Claude config state');
});

test('dry-run --uninstall does not delete files', () => {
  const cfg = freshTmpDir();
  // Seed a fake installation
  fs.mkdirSync(path.join(cfg, 'hooks'), { recursive: true });
  const fake = path.join(cfg, 'hooks', 'signaltrim-activate.js');
  fs.writeFileSync(fake, '// fake');
  fs.writeFileSync(path.join(cfg, 'settings.json'),
    JSON.stringify({ hooks: { SessionStart: [{ hooks: [{ type: 'command', command: 'node ' + fake }] }] } }, null, 2));
  const before = fs.readFileSync(path.join(cfg, 'settings.json'), 'utf8');

  const r = spawnSync('node', [INSTALLER, '--uninstall', '--dry-run', '--non-interactive', '--config-dir', cfg],
    { encoding: 'utf8', env: { ...process.env, CLAUDE_CONFIG_DIR: cfg } });
  assert.equal(r.status, 0);

  // File still present, settings unchanged.
  assert.equal(fs.existsSync(fake), true);
  assert.equal(fs.readFileSync(path.join(cfg, 'settings.json'), 'utf8'), before);
});
