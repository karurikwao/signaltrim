// Unit tests for the installer process-launch safety helpers.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const INSTALLER = require('../../bin/install.js');

test('Windows shell launch guard rejects cmd.exe metacharacters', () => {
  for (const value of ['foo&calc', 'foo|more', 'foo>out', 'foo%PATH%', 'foo!BAR!', 'foo^bar']) {
    assert.throws(
      () => INSTALLER.assertSafeWinShellToken(value, 'argument'),
      /Refusing unsafe Windows shell argument/
    );
  }
});

test('Windows shell launch guard allows ordinary command arguments', () => {
  assert.doesNotThrow(() => {
    INSTALLER.assertSafeWinShellToken('npx', 'command');
    INSTALLER.assertSafeWinShellToken('@modelcontextprotocol/server-filesystem', 'argument');
    INSTALLER.assertSafeWinShellToken('C:\\Users\\me\\project files', 'argument');
  });
});
