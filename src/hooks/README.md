# SignalTrim Hooks

These hooks are **bundled with the signaltrim plugin** and activate automatically when the plugin is installed. No manual setup required.

If you installed signaltrim standalone (without the plugin), the unified Node installer at `bin/install.js` wires them into your `settings.json` for you — run `node bin/install.js --only claude` from a clone, or `npx -y github:karurikwao/signaltrim -- --only claude` for the curl-pipe path.

## What's Included

### `signaltrim-activate.js` — SessionStart hook

- Runs once when Claude Code starts
- Writes `full` to `$CLAUDE_CONFIG_DIR/.signaltrim-active` (default `~/.claude/.signaltrim-active`) via the symlink-safe `safeWriteFlag` helper
- Emits signaltrim rules as hidden SessionStart context
- Detects missing statusline config and emits setup nudge (Claude will offer to help)

### `signaltrim-mode-tracker.js` — UserPromptSubmit hook

- Fires on every user prompt, checks for `/signaltrim` commands and natural-language activation/deactivation phrases ("use SignalTrim mode", "stop SignalTrim", "normal mode")
- Writes the active mode to the flag file when a signaltrim command is detected; deletes it on deactivation
- Emits a small per-turn reinforcement reminder when the flag is set to a non-independent mode (`lite`/`full`/`ultra`/`wenyan*`)
- Supports: `lite`, `full`, `ultra`, `wenyan`, `wenyan-lite`, `wenyan-full`, `wenyan-ultra`, `commit`, `review`, `compress`

### `signaltrim-statusline.sh` / `signaltrim-statusline.ps1` — Statusline badge script

- Reads `$CLAUDE_CONFIG_DIR/.signaltrim-active` (default `~/.claude/.signaltrim-active`) and outputs a colored badge
- Shows `[SIGNALTRIM]`, `[SIGNALTRIM:ULTRA]`, `[SIGNALTRIM:WENYAN]`, etc.
- Appends the lifetime savings suffix `saved 12.4k` from `$CLAUDE_CONFIG_DIR/.signaltrim-statusline-suffix` (written by `signaltrim-stats.js` on each `/signaltrim-stats` run; absent until the first run, so fresh installs render no fake number). Opt out with `SIGNALTRIM_STATUSLINE_SAVINGS=0`.

## Statusline Badge

The statusline badge shows which signaltrim mode is active directly in your Claude Code status bar.

**Plugin users:** If you do not already have a `statusLine` configured, Claude will detect that on your first session after install and offer to set it up for you. Accept and you're done.

If you already have a custom statusline, signaltrim does not overwrite it and Claude stays quiet. Add the badge snippet to your existing script instead.

**Standalone users:** the unified installer (`bin/install.js`, invoked by the `install.sh` / `install.ps1` shims at the repo root) wires the statusline automatically if you do not already have a custom statusline. If you do, the installer leaves it alone and prints the merge note.

**Manual setup:** If you need to configure it yourself, add one of these to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash /path/to/signaltrim-statusline.sh"
  }
}
```

```json
{
  "statusLine": {
    "type": "command",
    "command": "powershell -ExecutionPolicy Bypass -File C:\\path\\to\\signaltrim-statusline.ps1"
  }
}
```

Replace the path with the actual script location (e.g. `~/.claude/hooks/` for standalone installs, or the plugin install directory for plugin installs).

**Custom statusline:** If you already have a statusline script, add this snippet to it:

```bash
signaltrim_text=""
signaltrim_flag="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.signaltrim-active"
if [ -f "$signaltrim_flag" ]; then
  signaltrim_mode=$(cat "$signaltrim_flag" 2>/dev/null)
  if [ "$signaltrim_mode" = "full" ] || [ -z "$signaltrim_mode" ]; then
    signaltrim_text=$'\033[38;5;172m[SIGNALTRIM]\033[0m'
  else
    signaltrim_suffix=$(echo "$signaltrim_mode" | tr '[:lower:]' '[:upper:]')
    signaltrim_text=$'\033[38;5;172m[SIGNALTRIM:'"${signaltrim_suffix}"$']\033[0m'
  fi
fi
```

Badge examples:
- `/signaltrim` → `[SIGNALTRIM]`
- `/signaltrim ultra` → `[SIGNALTRIM:ULTRA]`
- `/signaltrim wenyan` → `[SIGNALTRIM:WENYAN]`
- `/signaltrim-commit` → `[SIGNALTRIM:COMMIT]`
- `/signaltrim-review` → `[SIGNALTRIM:REVIEW]`

## How It Works

```
SessionStart hook ──writes "full"──▶ $CLAUDE_CONFIG_DIR/.signaltrim-active ◀──writes mode── UserPromptSubmit hook
                                              │
                                           reads
                                              ▼
                                     Statusline script
                                    [SIGNALTRIM:ULTRA] │ ...
```

SessionStart stdout is injected as hidden system context — Claude sees it, users don't. The statusline runs as a separate process. The flag file is the bridge.

## Uninstall

If installed via plugin: disable the plugin — hooks deactivate automatically.

If installed via the standalone Node installer:
```bash
npx -y github:karurikwao/signaltrim -- --uninstall
# or, from a clone:
node bin/install.js --uninstall
```

Or manually:
1. Remove the signaltrim hook files from `$CLAUDE_CONFIG_DIR/hooks/` (default `~/.claude/hooks/`): `signaltrim-activate.js`, `signaltrim-mode-tracker.js`, `signaltrim-stats.js`, `signaltrim-config.js`, and `signaltrim-statusline.{sh,ps1}`.
2. Remove the SessionStart, UserPromptSubmit, and statusLine entries from `$CLAUDE_CONFIG_DIR/settings.json`.
3. Delete `$CLAUDE_CONFIG_DIR/.signaltrim-active` (and `$CLAUDE_CONFIG_DIR/.signaltrim-statusline-suffix` if you ran `/signaltrim-stats`).
