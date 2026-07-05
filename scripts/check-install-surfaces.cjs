#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const child_process = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const failures = [];
const notes = [];

function read(rel) {
  return fs.readFileSync(path.join(ROOT, rel), 'utf8');
}

function requireText(rel, needle) {
  const body = read(rel);
  if (!body.includes(needle)) failures.push(`${rel} missing ${needle}`);
}

function commandExists(cmd) {
  const probe = process.platform === 'win32'
    ? child_process.spawnSync('where', [cmd], { encoding: 'utf8' })
    : child_process.spawnSync('command', ['-v', cmd], { shell: true, encoding: 'utf8' });
  return probe.status === 0;
}

function runOptional(label, cmd, args) {
  if (!commandExists(cmd)) {
    notes.push(`${label}: skipped (${cmd} unavailable)`);
    return;
  }
  const result = child_process.spawnSync(cmd, args, {
    cwd: ROOT,
    encoding: 'utf8',
    env: { ...process.env, NO_COLOR: '1' },
  });
  const output = `${result.stderr || ''}${result.stdout || ''}`.replace(/\u0000/g, '');
  const launchFailure = [
    'Failed to attach disk',
    'WSL2',
    'CreateInstance',
    'ERROR_PATH_NOT_FOUND',
    'The system cannot find the path specified',
  ].some((needle) => output.includes(needle));
  if (launchFailure) {
    notes.push(`${label}: skipped (${cmd} launch failed)`);
    return;
  }
  if (result.status !== 0) {
    failures.push(`${label}: ${cmd} ${args.join(' ')} failed\n${output}`);
  } else {
    notes.push(`${label}: ok`);
  }
}

const pkg = JSON.parse(read('package.json'));
if (pkg.version !== '0.6.4') failures.push(`package.json version is ${pkg.version}, expected 0.6.4`);
if (pkg.engines?.node !== '>=20.19') failures.push(`package.json engines.node is ${pkg.engines?.node}, expected >=20.19`);
if (!fs.existsSync(path.join(ROOT, pkg.bin.signaltrim))) failures.push('package.json bin.signaltrim target missing');
if (!fs.existsSync(path.join(ROOT, pkg.bin['signaltrim-shrink']))) failures.push('package.json bin.signaltrim-shrink target missing');

requireText('README.md', 'npm-v0.6.4');
requireText('README.md', 'node-20.19%2B');
requireText('README.md', 'npm run smoke');
requireText('docs/INSTALL-SHELLS.md', 'PowerShell');
requireText('docs/INSTALL-SHELLS.md', 'Bash');
requireText('docs/INSTALL-SHELLS.md', 'Zsh');
requireText('docs/INSTALL-SHELLS.md', 'Fish');
requireText('docs/INSTALL-SHELLS.md', 'bash -s --');
requireText('docs/INSTALL-SHELLS.md', 'Do not run `zsh install.sh`');
requireText('docs/INSTALL-SHELLS.md', 'Do not run `fish install.sh`');

runOptional('bash installer syntax', 'bash', ['-n', 'install.sh']);
runOptional('hook installer syntax', 'bash', ['-n', 'src/hooks/install.sh']);
runOptional('hook uninstaller syntax', 'bash', ['-n', 'src/hooks/uninstall.sh']);
runOptional('Zsh launch path can find Bash', 'zsh', ['-c', 'command -v bash >/dev/null']);
runOptional('Fish launch path can find Bash', 'fish', ['-c', 'command -v bash >/dev/null']);

const ps = commandExists('pwsh') ? 'pwsh' : (commandExists('powershell') ? 'powershell' : null);
if (ps) {
  runOptional('PowerShell installer syntax', ps, [
    '-NoProfile',
    '-Command',
    '[scriptblock]::Create((Get-Content -Raw "install.ps1")) | Out-Null; [scriptblock]::Create((Get-Content -Raw "src/hooks/install.ps1")) | Out-Null; [scriptblock]::Create((Get-Content -Raw "src/hooks/uninstall.ps1")) | Out-Null',
  ]);
} else {
  notes.push('PowerShell installer syntax: skipped (PowerShell unavailable)');
}

if (failures.length) {
  console.error('Install surface check failed:\n');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log('Install surface check passed');
for (const note of notes) console.log(`- ${note}`);
