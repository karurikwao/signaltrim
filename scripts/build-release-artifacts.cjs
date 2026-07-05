#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const child_process = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'dist', 'release');
const BUNDLE_ROOT = path.join(DIST, 'bundles');
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
const targets = ['windows-x64', 'macos-x64', 'linux-x64'];

function write(rel, body, mode) {
  const file = path.join(BUNDLE_ROOT, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, body);
  if (mode) fs.chmodSync(file, mode);
}

function copy(relFrom, relTo) {
  const from = path.join(DIST, relFrom);
  const to = path.join(BUNDLE_ROOT, relTo);
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
}

function archive(bundleName) {
  const out = path.join(DIST, `${bundleName}.tar.gz`);
  const result = child_process.spawnSync('tar', ['-czf', out, bundleName], {
    cwd: BUNDLE_ROOT,
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(`tar failed for ${bundleName}\n${result.stderr || result.stdout}`);
  }
}

function extractPackage(bundleName) {
  const result = child_process.spawnSync('tar', ['-xzf', path.join(DIST, tarball)], {
    cwd: path.join(BUNDLE_ROOT, bundleName),
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(`tar extraction failed for ${bundleName}\n${result.stderr || result.stdout}`);
  }
}

fs.mkdirSync(DIST, { recursive: true });
fs.rmSync(BUNDLE_ROOT, { recursive: true, force: true });
fs.mkdirSync(BUNDLE_ROOT, { recursive: true });

const tarball = fs.readdirSync(DIST).find((name) => name === `signaltrim-${pkg.version}.tgz`);
if (!tarball) {
  throw new Error(`Run npm pack first; expected dist/release/signaltrim-${pkg.version}.tgz`);
}

for (const target of targets) {
  const bundle = `signaltrim-${pkg.version}-${target}`;
  copy(tarball, path.join(bundle, tarball));
  extractPackage(bundle);
  write(path.join(bundle, 'README.txt'), [
    `SignalTrim ${pkg.version} ${target}`,
    '',
    'This bundle is a platform launch pack for the SignalTrim Node CLI.',
    'It includes the npm package tarball plus shell wrappers for the target OS.',
    'Node.js 20.19+ is still required; SignalTrim does not ship a hosted backend.',
    '',
    'Install from the package tarball:',
    `  npm install -g ./${tarball}`,
    '',
    'Or run from a cloned repo:',
    '  npm run smoke',
    '  node bin/install.js --help',
    '',
  ].join('\n'));

  if (target === 'windows-x64') {
    write(path.join(bundle, 'signaltrim.cmd'), [
      '@echo off',
      'setlocal',
      'node "%~dp0package\\bin\\install.js" %*',
      '',
    ].join('\r\n'));
    write(path.join(bundle, 'signaltrim.ps1'), [
      '$ErrorActionPreference = "Stop"',
      '$Root = Split-Path -Parent $MyInvocation.MyCommand.Path',
      'node (Join-Path $Root "package\\bin\\install.js") @args',
      '',
    ].join('\r\n'));
  } else {
    write(path.join(bundle, 'signaltrim'), [
      '#!/usr/bin/env sh',
      'set -eu',
      'DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
      'node "$DIR/package/bin/install.js" "$@"',
      '',
    ].join('\n'), 0o755);
  }

  archive(bundle);
}

console.log(`Built ${targets.length} platform release bundles in ${DIST}`);
