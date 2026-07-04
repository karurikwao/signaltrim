# signaltrim — opencode plugin

Native opencode plugin. Mirrors the Claude Code hook architecture using
opencode's `session.created` + `tui.prompt.append` lifecycle hooks.

## What this ships

| File | Role |
|---|---|
| `plugin.js` | ESM Bun module. Default-exports an opencode `Plugin` factory. |
| `package.json` | Marks the directory as ESM so Bun loads `plugin.js` correctly. |
| `commands/*.md` | Six slash-command prompt templates (`/signaltrim`, `/signaltrim-commit`, …). |

The installer (`bin/install.js --only opencode`) copies these alongside
`src/hooks/signaltrim-config.js` (for the symlink-safe flag-write helpers, renamed
to `signaltrim-config.cjs` because this directory is `"type": "module"`) into
`~/.config/opencode/plugins/signaltrim/` and patches `opencode.json` with a
`"plugin"` array entry.

## What it does

- `session.created` → writes the configured default mode to
  `~/.config/opencode/.signaltrim-active` via the same `safeWriteFlag` helper
  Claude Code uses (O_NOFOLLOW, atomic temp+rename, 0600 perms, symlink
  refusal, ownership check).
- `tui.prompt.append` → flips the flag in response to `/signaltrim[ <level>]`,
  `/signaltrim-commit`, `/signaltrim-review`, `/signaltrim-compress`, and natural
  language ("turn on signaltrim", "stop signaltrim", "normal mode"). When a
  non-independent mode is active, appends a one-line reinforcement to keep
  signaltrim in the model's attention each turn.

## What it does NOT do

- **No statusline badge.** opencode's TUI does not expose a plugin-writable
  statusline. The flag file is at `~/.config/opencode/.signaltrim-active` if
  you want to surface mode in your shell prompt.
- **No system-prompt injection from `session.created`.** opencode's docs
  don't expose a return shape for that. The always-on signaltrim ruleset comes
  from `~/.config/opencode/AGENTS.md` (also written by the installer) so
  the rules load even when the plugin runtime is broken.

## Why no separate npm package

Plugin code reuses `signaltrim-config.js` from the main repo. Shipping as an
in-repo plugin avoids a second release cadence and a name collision with
the existing third-party `opencode-signaltrim` npm package.
