# Shell Install Matrix

SignalTrim uses Node as the installer core and thin shell shims for entry. The supported runtime is Node 20.19+.

Wiki guide: [Getting Started](https://github.com/karurikwao/signaltrim/wiki/Getting-Started), [Installation Matrix](https://github.com/karurikwao/signaltrim/wiki/Installation-Matrix), and [Troubleshooting](https://github.com/karurikwao/signaltrim/wiki/Troubleshooting).

## PowerShell

Use this on Windows PowerShell 5.1+ or PowerShell 7+:

```powershell
irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.ps1 | iex
```

Local clone:

```powershell
pwsh install.ps1 --list
pwsh install.ps1 --dry-run --only claude --with-hooks
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.ps1 | iex
```

Verify:

```powershell
node -p "process.versions.node"
npx -y github:karurikwao/signaltrim -- --list
```

## Bash

Use this on macOS, Linux, WSL, and Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash
```

Local clone:

```bash
bash install.sh --list
bash install.sh --dry-run --only claude --with-hooks
```

Verify:

```bash
node -p "process.versions.node"
bash -n install.sh
npm run check:install-surfaces
```

## Zsh

Use `bash` explicitly. The installer shim is Bash, not Zsh:

```zsh
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash
```

Local clone:

```zsh
bash install.sh --list
```

Do not run `zsh install.sh`; the file intentionally uses Bash semantics.

## Fish

Use `bash` explicitly from Fish:

```fish
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash
```

Pass flags through Bash:

```fish
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash -s -- --dry-run
```

Do not run `fish install.sh`; the file intentionally uses Bash semantics.

## Compatibility Check

Run:

```bash
npm run check:install-surfaces
```

The check verifies:

- Node package metadata and badge version.
- README install command references.
- Bash syntax where Bash is available and can launch successfully.
- PowerShell parse checks where PowerShell is available.
- Zsh and Fish launch paths are checked when those shells are available; both route through Bash intentionally.
- This matrix includes PowerShell, Bash, Zsh, and Fish paths.
