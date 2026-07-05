# signaltrim — uninstaller for the SessionStart + UserPromptSubmit hooks (Windows PowerShell)
# Removes: hook files in ~/.claude/hooks, settings.json entries, and the flag file
# Usage: powershell -ExecutionPolicy Bypass -File src\hooks\uninstall.ps1
#   or:  irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/src/hooks/uninstall.ps1 | iex
param()

$ErrorActionPreference = "Stop"

$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$HooksDir = Join-Path $ClaudeDir "hooks"
$Settings = Join-Path $ClaudeDir "settings.json"
$FlagFile = Join-Path $ClaudeDir ".signaltrim-active"

$HookFiles = @("package.json", "signaltrim-config.js", "signaltrim-activate.js", "signaltrim-mode-tracker.js", "signaltrim-stats.js", "signaltrim-statusline.sh", "signaltrim-statusline.ps1", "signalteam-model-overrides.js")

# Detect if signaltrim is installed as a plugin
$PluginInstalled = $false
$PluginsDir = Join-Path $ClaudeDir "plugins"
if (Test-Path $PluginsDir) {
    $found = Get-ChildItem -Path $PluginsDir -Recurse -Filter "plugin.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "signaltrim" }
    if ($found) { $PluginInstalled = $true }
}

if ($PluginInstalled) {
    Write-Host "SignalTrim appears to be installed as a Claude Code plugin." -ForegroundColor Yellow
    Write-Host "To uninstall the plugin, run:"
    Write-Host ""
    Write-Host "  claude plugin disable signaltrim" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This script removes standalone hooks (installed via install.ps1)."
    Write-Host "Continuing with standalone hook removal..."
    Write-Host ""
}

Write-Host "Uninstalling signaltrim hooks..."

# 1. Remove hook files
$RemovedFiles = 0
foreach ($hook in $HookFiles) {
    $path = Join-Path $HooksDir $hook
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  Removed: $path"
        $RemovedFiles++
    }
}

if ($RemovedFiles -eq 0) {
    Write-Host "  No hook files found in $HooksDir"
}

# 2. Remove signaltrim entries from settings.json (idempotent)
if (Test-Path $Settings) {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "WARNING: 'node' not found - cannot safely edit settings.json." -ForegroundColor Yellow
        Write-Host "         Remove the signaltrim SessionStart and UserPromptSubmit"
        Write-Host "         entries from $Settings manually."
    } else {
        # Back up before editing
        Copy-Item $Settings "$Settings.bak" -Force

        # Pass path via env var — avoids injection if username contains a single quote.
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

let removed = 0;
if (settings.hooks) {
  for (const event of ['SessionStart', 'UserPromptSubmit']) {
    if (Array.isArray(settings.hooks[event])) {
      settings.hooks[event] = settings.hooks[event]
        .map(e => {
          if (!e || !Array.isArray(e.hooks)) return e;
          const before = e.hooks.length;
          const hooks = e.hooks.filter(h => !(h.command && referencesManagedScript(h.command)));
          removed += before - hooks.length;
          return { ...e, hooks };
        })
        .filter(e => !(e && Array.isArray(e.hooks) && e.hooks.length === 0));
      if (settings.hooks[event].length === 0) {
        delete settings.hooks[event];
      }
    }
  }
  if (Object.keys(settings.hooks).length === 0) {
    delete settings.hooks;
  }
}

if (settings.statusLine) {
  const cmd = typeof settings.statusLine === 'string'
    ? settings.statusLine
    : (settings.statusLine.command || '');
  if (cmd.includes(managedStatusLinePath)) {
    delete settings.statusLine;
    console.log('  Removed signaltrim statusLine from settings.json');
  }
}

fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
console.log('  Removed ' + removed + ' signaltrim hook entries from settings.json');
'@

        $tmpScript = Join-Path $env:TEMP "signaltrim-uninstall-$([System.Diagnostics.Process]::GetCurrentProcess().Id).js"
        try {
            [System.IO.File]::WriteAllText($tmpScript, $nodeScript, [System.Text.Encoding]::UTF8)
            node $tmpScript
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to remove SignalTrim hooks from $Settings"
            }
        } finally {
            if (Test-Path $tmpScript) { Remove-Item $tmpScript -Force }
        }

        # Clean up backup file left by installer
        if (Test-Path "$Settings.bak") {
            Remove-Item "$Settings.bak" -Force
            Write-Host "  Removed: $Settings.bak"
        }
    }
}

# 3. Remove flag file
if (Test-Path $FlagFile) {
    Remove-Item $FlagFile -Force
    Write-Host "  Removed: $FlagFile"
}

Write-Host ""
Write-Host "Done! Restart Claude Code to complete the uninstall." -ForegroundColor Green

# Guidance for other agents
Write-Host ""
Write-Host "Other agents:"
Write-Host "  npx skills remove signaltrim      # Cursor, Windsurf, Cline, Copilot, etc."
Write-Host "  claude plugin disable signaltrim   # Claude Code plugin"
Write-Host "  gemini extensions uninstall signaltrim  # Gemini CLI"
