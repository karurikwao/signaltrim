# Claude Code Hook Examples

These examples are ready-to-copy starting points. Prefer the installer unless you need manual control.

Wiki guide: [Claude Code Hooks](https://github.com/karurikwao/signaltrim/wiki/Claude-Code-Hooks) and [Examples](https://github.com/karurikwao/signaltrim/wiki/Examples).

## Install Hooks

```bash
npx -y github:karurikwao/signaltrim -- --only claude --with-hooks
```

Force refresh:

```bash
npx -y github:karurikwao/signaltrim -- --only claude --with-hooks --force
```

Disable standalone hook wiring:

```bash
npx -y github:karurikwao/signaltrim -- --only claude --no-hooks
```

## Manual Settings Shape

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"$CLAUDE_CONFIG_DIR/hooks/signaltrim-activate.js\"",
            "timeout": 5,
            "statusMessage": "Loading SignalTrim mode..."
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"$CLAUDE_CONFIG_DIR/hooks/signaltrim-mode-tracker.js\"",
            "timeout": 5,
            "statusMessage": "Tracking SignalTrim mode..."
          }
        ]
      }
    ]
  }
}
```

## When To Compress Automatically

Use automatic hooks for:

- Normal coding sessions.
- Repeated review loops.
- Teams that want a consistent concise style.

Use manual `/signaltrim` activation for:

- Teaching sessions.
- Safety-heavy reviews.
- Any session where a user may need fuller context.

## Safety Notes

- Managed hooks are matched by exact script basename.
- User hooks that merely contain `signaltrim` in a path are preserved.
- The installer backs up `settings.json` before writing.
- Existing statuslines are not overwritten.
