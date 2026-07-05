#!/bin/bash
# signaltrim — uninstaller for the SessionStart + UserPromptSubmit hooks
# Removes: hook files in ~/.claude/hooks, settings.json entries, and the flag file
# Usage: bash src/hooks/uninstall.sh
#   or:  bash <(curl -s https://raw.githubusercontent.com/karurikwao/signaltrim/main/src/hooks/uninstall.sh)
set -e

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS="$CLAUDE_DIR/settings.json"
FLAG_FILE="$CLAUDE_DIR/.signaltrim-active"

HOOK_FILES=("package.json" "signaltrim-config.js" "signaltrim-activate.js" "signaltrim-mode-tracker.js" "signaltrim-stats.js" "signaltrim-statusline.sh" "signaltrim-statusline.ps1" "signalteam-model-overrides.js")

# Detect if signaltrim is installed as a plugin (check plugin cache)
PLUGIN_INSTALLED=0
if [ -d "$CLAUDE_DIR/plugins" ]; then
  if find "$CLAUDE_DIR/plugins" -path "*/signaltrim*" -name "plugin.json" -print -quit 2>/dev/null | grep -q .; then
    PLUGIN_INSTALLED=1
  fi
fi

if [ "$PLUGIN_INSTALLED" -eq 1 ]; then
  echo "SignalTrim appears to be installed as a Claude Code plugin."
  echo "To uninstall the plugin, run:"
  echo ""
  echo "  claude plugin disable signaltrim"
  echo ""
  echo "This script removes standalone hooks (installed via install.sh)."
  echo "Continuing with standalone hook removal..."
  echo ""
fi

echo "Uninstalling signaltrim hooks..."

# 1. Remove hook files
REMOVED_FILES=0
for hook in "${HOOK_FILES[@]}"; do
  if [ -f "$HOOKS_DIR/$hook" ]; then
    rm "$HOOKS_DIR/$hook"
    echo "  Removed: $HOOKS_DIR/$hook"
    REMOVED_FILES=$((REMOVED_FILES + 1))
  fi
done

if [ "$REMOVED_FILES" -eq 0 ]; then
  echo "  No hook files found in $HOOKS_DIR"
fi

# 2. Remove signaltrim entries from settings.json (idempotent)
if [ -f "$SETTINGS" ]; then
  # Require node for the same reason install.sh does — safe JSON editing
  if ! command -v node >/dev/null 2>&1; then
    echo "WARNING: 'node' not found — cannot safely edit settings.json."
    echo "         Remove the signaltrim SessionStart and UserPromptSubmit"
    echo "         entries from $SETTINGS manually."
  else
    # Back up before editing, same policy as install.sh
    cp "$SETTINGS" "$SETTINGS.bak"

    # Pass paths via env vars — avoids shell injection if $HOME contains single quotes
    SIGNALTRIM_SETTINGS="$SETTINGS" SIGNALTRIM_HOOKS_DIR="$HOOKS_DIR" node -e "
      const fs = require('fs');
      const path = require('path');
      const settingsPath = process.env.SIGNALTRIM_SETTINGS;
      const hooksDir = process.env.SIGNALTRIM_HOOKS_DIR;
      const managedStatusLinePath = hooksDir + '/signaltrim-statusline.sh';

      function stripTrailingCommas(src) {
        let out = '';
        let inString = false;
        let stringChar = '';
        for (let i = 0; i < src.length; i++) {
          const c = src[i];
          if (inString) {
            out += c;
            if (c === '\\\\' && i + 1 < src.length) out += src[++i];
            else if (c === stringChar) inString = false;
            continue;
          }
          if (c === '\"' || c === \"'\") { inString = true; stringChar = c; out += c; continue; }
          if (c === ',') {
            let j = i + 1;
            while (j < src.length && /\\s/.test(src[j])) j++;
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
          if (inLine) { if (c === '\\n') { inLine = false; out += c; } continue; }
          if (inBlock) { if (c === '*' && next === '/') { inBlock = false; i++; } continue; }
          if (inString) {
            out += c;
            if (c === '\\\\' && i + 1 < src.length) out += src[++i];
            else if (c === stringChar) inString = false;
            continue;
          }
          if (c === '\"' || c === \"'\") { inString = true; stringChar = c; out += c; continue; }
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
        const re = /\"([^\"]*)\"|'([^']*)'|(\\S+)/g;
        let m;
        while ((m = re.exec(command || '')) !== null) out.push(m[1] ?? m[2] ?? m[3]);
        return out;
      }

      function normalizeToken(tok) {
        return String(tok || '').replace(/^file:\\/\\//i, '').replace(/\\\\/g, '/');
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
            // Drop the event key if it's now empty (keeps settings.json tidy)
            if (settings.hooks[event].length === 0) {
              delete settings.hooks[event];
            }
          }
        }
        // Drop settings.hooks if it's now empty
        if (Object.keys(settings.hooks).length === 0) {
          delete settings.hooks;
        }
      }

      // Remove statusLine if it references signaltrim
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
    "
  fi
fi

# 3. Clean up backup file left by installer
if [ -f "$SETTINGS.bak" ]; then
  rm "$SETTINGS.bak"
  echo "  Removed: $SETTINGS.bak"
fi

# 4. Remove flag file
if [ -f "$FLAG_FILE" ]; then
  rm "$FLAG_FILE"
  echo "  Removed: $FLAG_FILE"
fi

echo ""
echo "Done! Restart Claude Code to complete the uninstall."

# Guidance for other agents
echo ""
echo "Other agents:"
echo "  npx skills remove signaltrim    # Cursor, Windsurf, Cline, Copilot, etc."
echo "  claude plugin disable signaltrim  # Claude Code plugin"
echo "  gemini extensions uninstall signaltrim  # Gemini CLI"
