# signaltrim — one-command hook installer for Claude Code (Windows PowerShell)
# Installs: SessionStart hook (auto-load rules) + UserPromptSubmit hook (mode tracking)
# Usage: powershell -ExecutionPolicy Bypass -File src\hooks\install.ps1
#   or:  powershell -ExecutionPolicy Bypass -File src\hooks\install.ps1 -Force
# Local/development helper only. Remote installs must use repo-root install.ps1,
# which delegates to the unified pinned/checksummed Node installer.
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Require node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: 'node' is required to install the signaltrim hooks (used to merge" -ForegroundColor Red
    Write-Host "       the hook config into settings.json safely)." -ForegroundColor Red
    Write-Host "       Install Node.js from https://nodejs.org and re-run this script." -ForegroundColor Red
    exit 1
}

$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$HooksDir = Join-Path $ClaudeDir "hooks"
$Settings = Join-Path $ClaudeDir "settings.json"
$TempRoot = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { [System.IO.Path]::GetTempPath() }
$HookFiles = @("package.json", "signaltrim-config.js", "signaltrim-activate.js", "signaltrim-mode-tracker.js", "signaltrim-stats.js", "signaltrim-statusline.sh", "signaltrim-statusline.ps1", "signalteam-model-overrides.js")

# Resolve source — works from repo clone or remote
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { $null }

# Check if already installed (unless -Force). Older installs only had two hook
# files, so require the full current set plus the hook registrations before we
# short-circuit.
if (-not $Force) {
    $AllFilesPresent = $true
    foreach ($hook in $HookFiles) {
        if (-not (Test-Path (Join-Path $HooksDir $hook))) {
            $AllFilesPresent = $false
            break
        }
    }

    $HooksWired = $false
    $HasStatusLine = $false
    if ($AllFilesPresent -and (Test-Path $Settings)) {
        $env:SIGNALTRIM_SETTINGS = $Settings -replace '\\', '/'
        $preflightScript = @'
const fs = require('fs');

function stripTrailingCommas(src) {
  let out = '';
  let inString = false;
  let stringChar = '';
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if (inString) {
      out += c;
      if (c === '\\' && i + 1 < src.length) out += src[++i];
      else if (c === stringChar) inString = false;
      continue;
    }
    if (c === '"' || c === "'") { inString = true; stringChar = c; out += c; continue; }
    if (c === ',') {
      let j = i + 1;
      while (j < src.length && /\s/.test(src[j])) j++;
      if (src[j] === '}' || src[j] === ']') continue;
    }
    out += c;
  }
  return out;
}

function stripJsonComments(src) {
  let out = '';
  let inString = false;
  let stringChar = '';
  let inLine = false;
  let inBlock = false;
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    const next = src[i + 1] || '';
    if (inLine) { if (c === '\n') { inLine = false; out += c; } continue; }
    if (inBlock) { if (c === '*' && next === '/') { inBlock = false; i++; } continue; }
    if (inString) {
      out += c;
      if (c === '\\' && i + 1 < src.length) out += src[++i];
      else if (c === stringChar) inString = false;
      continue;
    }
    if (c === '"' || c === "'") { inString = true; stringChar = c; out += c; continue; }
    if (c === '/' && next === '/') { inLine = true; i++; continue; }
    if (c === '/' && next === '*') { inBlock = true; i++; continue; }
    out += c;
  }
  return stripTrailingCommas(out);
}

function readSettings(p) {
  const raw = fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '{}';
  if (!raw.trim()) return {};
  try { return JSON.parse(raw); } catch (_) {}
  return JSON.parse(stripJsonComments(raw));
}

const MANAGED_HOOK_BASENAMES = new Set([
  'signaltrim-activate.js',
  'signaltrim-mode-tracker.js',
  'signaltrim-stats.js',
  'signaltrim-statusline.sh',
  'signaltrim-statusline.ps1',
]);

function tokenizeCommand(command) {
  const out = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let m;
  while ((m = re.exec(command || '')) !== null) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

function normalizeToken(tok) {
  return String(tok || '').replace(/^file:\/\//i, '').replace(/\\/g, '/');
}

function basenameOf(tok) {
  return normalizeToken(tok).split('/').pop();
}

function referencesManagedScript(command) {
  for (const tok of tokenizeCommand(command)) {
    if (MANAGED_HOOK_BASENAMES.has(basenameOf(tok))) return true;
  }
  return false;
}

try {
  const settings = readSettings(process.env.SIGNALTRIM_SETTINGS);
  const hasSignalTrimHook = (event) =>
    Array.isArray(settings.hooks?.[event]) &&
    settings.hooks[event].some(e =>
      e.hooks && e.hooks.some(h => h.command && referencesManagedScript(h.command))
    );
  process.exit(
    hasSignalTrimHook('SessionStart') &&
    hasSignalTrimHook('UserPromptSubmit') &&
    !!settings.statusLine
      ? 0
      : 1
  );
} catch (_) {
  process.exit(1);
}
'@
        $tmpPreflight = Join-Path $TempRoot "signaltrim-install-preflight-$([System.Diagnostics.Process]::GetCurrentProcess().Id).js"
        try {
            [System.IO.File]::WriteAllText($tmpPreflight, $preflightScript, [System.Text.Encoding]::UTF8)
            node $tmpPreflight | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $HooksWired = $true
                $HasStatusLine = $true
            }
        } finally {
            if (Test-Path $tmpPreflight) { Remove-Item $tmpPreflight -Force }
        }
    }

    if ($AllFilesPresent -and $HooksWired -and $HasStatusLine) {
        Write-Host "SignalTrim hooks already installed in $HooksDir"
        Write-Host "  Re-run with -Force to overwrite: powershell -File hooks\install.ps1 -Force"
        Write-Host ""
        Write-Host "Nothing to do. Hooks are already in place."
        exit 0
    }
}

if ($Force -and (Test-Path (Join-Path $HooksDir "signaltrim-activate.js"))) {
    Write-Host "Reinstalling signaltrim hooks (-Force)..."
} else {
    Write-Host "Installing signaltrim hooks..."
}

# 1. Ensure hooks dir exists
if (-not (Test-Path $HooksDir)) {
    New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null
}

# 2. Copy or download hook files
foreach ($hook in $HookFiles) {
    $dest = Join-Path $HooksDir $hook
    $localSource = if ($ScriptDir) { Join-Path $ScriptDir $hook } else { $null }

    if ($localSource -and (Test-Path $localSource)) {
        Copy-Item $localSource $dest -Force
    } else {
        Write-Host "ERROR: hook source not found: $hook" -ForegroundColor Red
        Write-Host "       Run from a local clone, or use the repo-root installer:" -ForegroundColor Red
        Write-Host "       npx -y github:karurikwao/signaltrim -- --only claude --with-hooks" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Installed: $dest"
}

# 3. Wire hooks + statusline into settings.json (idempotent)
if (-not (Test-Path $Settings)) {
    Set-Content -Path $Settings -Value "{}"
}

# Back up existing settings.json before touching it
Copy-Item $Settings "$Settings.bak" -Force

# Use node for safe JSON merging — pass paths via env vars to avoid injection
# if the username contains a single quote (e.g., O'Brien).
# Use a single-quote here-string so PowerShell does NOT expand $variables inside.
$env:SIGNALTRIM_SETTINGS = $Settings -replace '\\', '/'
$env:SIGNALTRIM_HOOKS_DIR = $HooksDir -replace '\\', '/'

$nodeScript = @'
const fs = require('fs');
const settingsPath = process.env.SIGNALTRIM_SETTINGS;
const hooksDir = process.env.SIGNALTRIM_HOOKS_DIR;
const managedStatusLinePath = hooksDir + '/signaltrim-statusline.ps1';

function stripTrailingCommas(src) {
  let out = '';
  let inString = false;
  let stringChar = '';
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if (inString) {
      out += c;
      if (c === '\\' && i + 1 < src.length) out += src[++i];
      else if (c === stringChar) inString = false;
      continue;
    }
    if (c === '"' || c === "'") { inString = true; stringChar = c; out += c; continue; }
    if (c === ',') {
      let j = i + 1;
      while (j < src.length && /\s/.test(src[j])) j++;
      if (src[j] === '}' || src[j] === ']') continue;
    }
    out += c;
  }
  return out;
}

function stripJsonComments(src) {
  let out = '';
  let inString = false;
  let stringChar = '';
  let inLine = false;
  let inBlock = false;
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    const next = src[i + 1] || '';
    if (inLine) { if (c === '\n') { inLine = false; out += c; } continue; }
    if (inBlock) { if (c === '*' && next === '/') { inBlock = false; i++; } continue; }
    if (inString) {
      out += c;
      if (c === '\\' && i + 1 < src.length) out += src[++i];
      else if (c === stringChar) inString = false;
      continue;
    }
    if (c === '"' || c === "'") { inString = true; stringChar = c; out += c; continue; }
    if (c === '/' && next === '/') { inLine = true; i++; continue; }
    if (c === '/' && next === '*') { inBlock = true; i++; continue; }
    out += c;
  }
  return stripTrailingCommas(out);
}

function readSettings(p) {
  const raw = fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '{}';
  if (!raw.trim()) return {};
  try { return JSON.parse(raw); } catch (_) {}
  return JSON.parse(stripJsonComments(raw));
}

const MANAGED_HOOK_BASENAMES = new Set([
  'signaltrim-activate.js',
  'signaltrim-mode-tracker.js',
  'signaltrim-stats.js',
  'signaltrim-statusline.sh',
  'signaltrim-statusline.ps1',
]);

function tokenizeCommand(command) {
  const out = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let m;
  while ((m = re.exec(command || '')) !== null) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

function normalizeToken(tok) {
  return String(tok || '').replace(/^file:\/\//i, '').replace(/\\/g, '/');
}

function basenameOf(tok) {
  return normalizeToken(tok).split('/').pop();
}

function referencesManagedScript(command) {
  for (const tok of tokenizeCommand(command)) {
    if (MANAGED_HOOK_BASENAMES.has(basenameOf(tok))) return true;
  }
  return false;
}

const settings = readSettings(settingsPath);
if (!settings.hooks) settings.hooks = {};

// SessionStart
if (!settings.hooks.SessionStart) settings.hooks.SessionStart = [];
const hasStart = settings.hooks.SessionStart.some(e =>
  e.hooks && e.hooks.some(h => h.command && referencesManagedScript(h.command))
);
if (!hasStart) {
  settings.hooks.SessionStart.push({
    hooks: [{
      type: 'command',
      command: 'node "' + hooksDir + '/signaltrim-activate.js"',
      timeout: 5,
      statusMessage: 'Loading signaltrim mode...'
    }]
  });
}

// UserPromptSubmit
if (!settings.hooks.UserPromptSubmit) settings.hooks.UserPromptSubmit = [];
const hasPrompt = settings.hooks.UserPromptSubmit.some(e =>
  e.hooks && e.hooks.some(h => h.command && referencesManagedScript(h.command))
);
if (!hasPrompt) {
  settings.hooks.UserPromptSubmit.push({
    hooks: [{
      type: 'command',
      command: 'node "' + hooksDir + '/signaltrim-mode-tracker.js"',
      timeout: 5,
      statusMessage: 'Tracking signaltrim mode...'
    }]
  });
}

// Statusline
if (!settings.statusLine) {
  settings.statusLine = {
    type: 'command',
    command: 'powershell -ExecutionPolicy Bypass -File "' + managedStatusLinePath + '"'
  };
  console.log('  Statusline badge configured.');
} else {
  const cmd = typeof settings.statusLine === 'string'
    ? settings.statusLine
    : (settings.statusLine.command || '');
  if (cmd.includes(managedStatusLinePath)) {
    console.log('  Statusline badge already configured.');
  } else {
    console.log('  NOTE: Existing statusline detected - signaltrim badge NOT added.');
    console.log('        See src/hooks/README.md to add the badge to your existing statusline.');
  }
}

fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
console.log('  Hooks wired in settings.json');
'@

$tmpScript = Join-Path $TempRoot "signaltrim-install-$([System.Diagnostics.Process]::GetCurrentProcess().Id).js"
try {
    [System.IO.File]::WriteAllText($tmpScript, $nodeScript, [System.Text.Encoding]::UTF8)
    node $tmpScript
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to merge SignalTrim hooks into $Settings"
    }
} finally {
    if (Test-Path $tmpScript) { Remove-Item $tmpScript -Force }
}

Write-Host ""
Write-Host "Done! Restart Claude Code to activate." -ForegroundColor Green
Write-Host ""
Write-Host "What's installed:"
Write-Host "  - SessionStart hook: auto-loads signaltrim rules every session"
Write-Host "  - Mode tracker hook: updates statusline badge when you switch modes"
Write-Host "    (/signaltrim lite, /signaltrim ultra, /signaltrim-commit, etc.)"
Write-Host "  - Statusline badge: shows [SIGNALTRIM] or [SIGNALTRIM:ULTRA] etc."
