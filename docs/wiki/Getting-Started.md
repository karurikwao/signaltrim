# Getting Started

This page gets SignalTrim installed and verified quickly.

## Requirements

- Node.js 20.19 or newer.
- GitHub access for install-from-repo paths.
- The target agent installed if you want auto-detection.
- PowerShell 5.1+ on Windows.

## Recommended Install

If you do not like pipe-to-shell installs, read the script first or use the dry-run `npx` path below. The shell shims delegate to the same Node installer and support preview mode before writing.

macOS, Linux, WSL, Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.ps1 | iex
```

Both shims delegate to the unified Node installer:

```bash
npx -y github:karurikwao/signaltrim -- ...
```

## Preview First

Use dry-run mode when you want to see every planned write or external command:

```bash
npx -y github:karurikwao/signaltrim -- --dry-run
```

Dry-run should not call third-party CLIs or create config state.

## Install One Agent

Claude Code:

```bash
claude plugin marketplace add karurikwao/signaltrim && claude plugin install signaltrim@signaltrim
```

Gemini CLI:

```bash
gemini extensions install https://github.com/karurikwao/signaltrim
```

opencode:

```bash
npx -y github:karurikwao/signaltrim -- --only opencode
```

Codex profile through the skills CLI:

```bash
npx skills add karurikwao/signaltrim -a codex
```

Full matrix: [Installation Matrix](Installation-Matrix.md).

Canonical repo docs:

- [INSTALL.md](https://github.com/karurikwao/signaltrim/blob/main/INSTALL.md)
- [Windows install notes](https://github.com/karurikwao/signaltrim/blob/main/docs/install-windows.md)
- [Troubleshooting](Troubleshooting.md)

## Activate

Inside your agent:

```text
/signaltrim
```

Switch mode:

```text
/signaltrim lite
/signaltrim ultra
/signaltrim wenyan-full
```

Turn off:

```text
normal mode
```

## Verify Claude Code Install

Check the active flag:

```bash
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.signaltrim-active"
```

Expected:

```text
full
```

Check settings:

```bash
cat "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
```

Look for hook commands that target:

- `signaltrim-activate.js`
- `signaltrim-mode-tracker.js`

Statusline should show `[SIGNALTRIM]` or a mode-specific badge.

## Verify Repo Installer Health

From a clone:

```bash
python tests/verify_repo.py
npm test
python -m unittest discover -s tests -p "test_*.py"
```

## Uninstall

```bash
npx -y github:karurikwao/signaltrim -- --uninstall
```

The uninstaller removes SignalTrim-managed files and settings entries. It preserves user-authored hooks that merely mention `signaltrim` in a path or filename.
