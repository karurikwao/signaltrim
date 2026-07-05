# Security and Privacy

SignalTrim is local-first. Core SignalTrim has no hosted backend, account, analytics, crash reporting, or background telemetry.

## What Stays Local

Core mode:

- Skill markdown.
- Rule files.
- Hook scripts.
- Mode flag.
- Claude settings merge.
- Session stats reads.
- Statusline suffix.

The core hook and statusline path does not call `fetch`, `http`, or `https`.

## Install-Time Network Activity

Install can fetch:

- `install.sh` or `install.ps1` from GitHub raw.
- This repository via `npx -y github:karurikwao/signaltrim`.
- Claude plugin marketplace/install data through Claude Code.
- Gemini extension data through Gemini CLI.
- Skills CLI packages through npm.
- MCP shrink GitHub package through `npx --package github:karurikwao/signaltrim`.

Nothing is uploaded by SignalTrim during install.

## Optional Network Activity

`/signaltrim-compress` sends the named file content to the model provider used by the compression path.

`signaltrim-shrink` can wrap an upstream MCP server. Any network activity from that server belongs to the upstream.

## Symlink and Reparse Safety

Compression refuses:

- Symlink source files.
- Reparse points.
- Symlink components anywhere in the path.

Reason: a project-local symlink must not trick the tool into sending private files from elsewhere.

## Sensitive Path Refusal

Compression refuses filenames or directories that look sensitive, including:

- `.env`
- `.netrc`
- `.ssh`
- `.aws`
- `.gnupg`
- `.kube`
- `credentials`
- `secret`
- private key extensions

## Hook Safety

The installer and uninstaller identify managed hooks by exact script basename, not substring.

This means user hooks like:

```text
node /Users/me/signaltrim-notes/my-hook.js
node /tmp/user-signaltrim-helper.js
```

are preserved.

## Windows Shell Safety

Windows `.cmd` shims require shell mediation in some places. SignalTrim rejects unsafe command metacharacters before invoking shell-backed commands.

## Reporting Vulnerabilities

Use GitHub private vulnerability reporting:

https://github.com/karurikwao/signaltrim/security/advisories/new

Do not open public issues for vulnerabilities.

## Security Test Commands

```bash
python -m unittest tests.test_compress_safety tests.test_symlink_flag tests.test_hooks
npm test
python tests/verify_repo.py
```

Release audit checklist: [docs/SECURITY-AUDIT.md](https://github.com/karurikwao/signaltrim/blob/main/docs/SECURITY-AUDIT.md).
