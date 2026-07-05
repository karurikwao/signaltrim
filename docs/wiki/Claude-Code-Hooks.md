# Claude Code Hooks

SignalTrim's deepest integration is Claude Code. It supports plugin installation plus standalone hooks and a statusline badge.

## Files

| File | Purpose |
|---|---|
| `src/hooks/signaltrim-activate.js` | Loads SignalTrim rules and sets initial active mode. |
| `src/hooks/signaltrim-mode-tracker.js` | Tracks mode switches from prompts and slash commands. |
| `src/hooks/signaltrim-stats.js` | Reads session logs and estimates output savings. |
| `src/hooks/signaltrim-config.js` | Shared config, safe writes, mode history helpers. |
| `src/hooks/signaltrim-statusline.sh` | POSIX statusline badge. |
| `src/hooks/signaltrim-statusline.ps1` | Windows PowerShell statusline badge. |
| `src/hooks/install.sh` | Standalone Bash hook installer. |
| `src/hooks/install.ps1` | Standalone PowerShell hook installer. |
| `src/hooks/uninstall.sh` | Standalone Bash hook uninstaller. |
| `src/hooks/uninstall.ps1` | Standalone PowerShell hook uninstaller. |

## Hook Events

SignalTrim wires:

- `SessionStart`: load rules and set active mode.
- `UserPromptSubmit`: detect mode changes and reinforce compact behavior.

## Settings Merge

Claude settings live at:

```text
$CLAUDE_CONFIG_DIR/settings.json
```

or:

```text
~/.claude/settings.json
```

The installer:

- Reads JSON or JSONC.
- Preserves comments only until write; output is strict JSON.
- Validates hook shapes before write.
- Backs up existing settings to `settings.json.bak`.
- Matches managed hooks by exact script basename.
- Preserves user hooks that merely contain `signaltrim` in their path.

Managed basenames:

```text
signaltrim-activate.js
signaltrim-mode-tracker.js
signaltrim-stats.js
signaltrim-statusline.sh
signaltrim-statusline.ps1
```

## Statusline

When active, the badge shows:

```text
[SIGNALTRIM]
```

Mode-specific examples:

```text
[SIGNALTRIM:ULTRA]
[SIGNALTRIM:WENYAN-ULTRA]
```

After `/signaltrim-stats`, the statusline may append a savings suffix:

```text
[SIGNALTRIM] saved 12.4k
```

## Mode Flag

Active mode is stored in:

```text
$CLAUDE_CONFIG_DIR/.signaltrim-active
```

Typical content:

```text
full
```

The config helper writes this file defensively to avoid symlink clobbering.

## Common Fixes

Reinstall standalone hooks:

```bash
npx -y github:karurikwao/signaltrim -- --only claude --with-hooks --force
```

Skip hooks and use plugin path only:

```bash
npx -y github:karurikwao/signaltrim -- --only claude --no-hooks
```

Check hook syntax:

```bash
node --check src/hooks/signaltrim-activate.js
node --check src/hooks/signaltrim-mode-tracker.js
node --check src/hooks/signaltrim-stats.js
```

Run hook tests:

```bash
python -m unittest tests.test_hooks
npm test
```

Ready-to-copy examples: [docs/examples/claude-code-hooks.md](https://github.com/karurikwao/signaltrim/blob/main/docs/examples/claude-code-hooks.md).
