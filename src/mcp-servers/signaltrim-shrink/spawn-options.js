// Spawn options for the upstream MCP child process.
//
// Windows: spawn('npx', ...) (and any .cmd shim such as 'gemini') hits ENOENT
// because PATHEXT resolution only happens when child_process spawns through
// a shell. POSIX systems resolve fine without a shell. Keep shell:false on
// POSIX to avoid argv quoting surprises. Because Windows uses cmd.exe, reject
// metacharacters before spawning so upstream args cannot become shell syntax.
//
// Exported standalone so the behavior is unit-testable without re-running
// the CLI entry point (index.js exits immediately when args are empty).

'use strict';

const WIN_CMD_META = /[&|<>^%!()\r\n]/;

function assertSafeSpawnInput(command, args = [], platform = process.platform) {
  if (platform !== 'win32') return;
  for (const [label, value] of [['command', command], ...args.map((arg, idx) => [`argument ${idx + 1}`, arg])]) {
    if (WIN_CMD_META.test(String(value))) {
      throw new Error(`unsafe Windows shell ${label}: contains cmd.exe metacharacter`);
    }
  }
}

function getSpawnOptions(platform = process.platform) {
  return {
    stdio: ['pipe', 'pipe', 'inherit'],
    shell: platform === 'win32',
    windowsHide: true,
  };
}

module.exports = { getSpawnOptions, assertSafeSpawnInput };
