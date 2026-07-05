# Troubleshooting

## Installer Does Nothing

Run:

```bash
npx -y github:karurikwao/signaltrim -- --list
```

Check whether your target agent is detected.

If not detected:

- Confirm the agent CLI is on `PATH`.
- Use `--only <id>` for soft-probe agents.
- Use static rule install with `--with-init` where needed.

## Dry Run Says Installed

Dry-run should say `would install:` and should not create config state. If it calls third-party CLIs or writes files, that is a regression.

Run:

```bash
npx -y github:karurikwao/signaltrim -- --dry-run --only claude --with-hooks --non-interactive
```

## Claude Code Does Not Activate

Check flag:

```bash
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.signaltrim-active"
```

Check settings:

```bash
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

Look for:

- `signaltrim-activate.js`
- `signaltrim-mode-tracker.js`

Restart Claude Code after installing. `SessionStart` does not fire mid-session.

## Statusline Missing

If you already had a custom statusline, SignalTrim does not overwrite it. Add the SignalTrim statusline manually or merge it into your existing statusline.

POSIX:

```bash
bash "$CLAUDE_CONFIG_DIR/hooks/signaltrim-statusline.sh"
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_CONFIG_DIR\hooks\signaltrim-statusline.ps1"
```

## Windows Install Problems

Use PowerShell path:

```powershell
irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.ps1 | iex
```

If execution policy blocks:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then rerun install.

More detail:

```text
docs/install-windows.md
```

## Settings JSON Problems

SignalTrim supports JSONC comments and trailing commas, then writes strict JSON.

If settings break:

1. Check `settings.json.bak`.
2. Validate JSON.
3. Re-run installer with `--force`.

```bash
npx -y github:karurikwao/signaltrim -- --only claude --with-hooks --force
```

## Compression Refuses A File

Common reasons:

- File is not natural language.
- File is too large.
- File is invalid UTF-8.
- File path looks sensitive.
- File is a symlink or reparse point.
- Backup already exists.

This is usually intentional. Rename or pass a non-sensitive real file path only if you are sure.

## MCP Shrink Does Not Start

Check that you passed an upstream command:

```bash
npx -y github:karurikwao/signaltrim -- --with-mcp-shrink="npx @modelcontextprotocol/server-filesystem /tmp"
```

Bare `--with-mcp-shrink` is invalid because the proxy needs a server to wrap.

For paths with spaces, quote the upstream executable:

```bash
--with-mcp-shrink="\"C:\Program Files\MCP Server\server.exe\" --stdio"
```

## Uninstall Leaves Rule Files

By design, uninstall does not remove repo-local static rule files created by `--with-init`.

Remove manually:

- `.cursor/rules/signaltrim.mdc`
- `.windsurf/rules/signaltrim.md`
- `.clinerules/signaltrim.md`
- `.github/copilot-instructions.md`
- `.opencode/AGENTS.md`
- `AGENTS.md`

## Full Local Health Check

```bash
python tests/verify_repo.py
python -m unittest discover -s tests -p "test_*.py"
npm test
node tests/test_mcp_shrink.js
npm pack --dry-run --json
```

