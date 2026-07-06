#!/usr/bin/env node
'use strict';

const child_process = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const TEST_DIR = path.join(ROOT, 'tests');

const tests = fs.readdirSync(TEST_DIR)
  .filter((name) => /^test_.*\.js$/.test(name))
  .sort()
  .map((name) => path.join(TEST_DIR, name));

if (tests.length === 0) {
  console.error('No standalone JS tests found under tests/test_*.js');
  process.exit(1);
}

for (const file of tests) {
  const rel = path.relative(ROOT, file);
  console.log(`\n==> ${rel}`);
  const result = child_process.spawnSync(process.execPath, [file], {
    cwd: ROOT,
    stdio: 'inherit',
    env: { ...process.env, NO_COLOR: '1' },
  });
  if (result.error) {
    console.error(`${rel}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    console.error(`${rel}: exited with status ${result.status}`);
    process.exit(result.status || 1);
  }
}

console.log(`\nStandalone JS tests passed (${tests.length} files).`);
