# Security Policy

## Supported Versions

Only the latest stable release builds are supported with security patches.

## Reporting a Vulnerability

If you identify a security vulnerability in signaltrim (such as arbitrary shell execution, workspace folder escapes, token/credentials hijack via prompts, or malicious JSON parsing flaws in extension settings), please do **not** open a public issue.

Please report vulnerabilities privately by emailing the maintainers or using [GitHub's private vulnerability reporting](https://github.com/karurikwao/signaltrim/security/advisories/new).

## Privacy & Telemetry

**SignalTrim has no telemetry. Zero.** No analytics, no crash reporting, no phone-home, no accounts, no API keys collected. There is no signaltrim backend — nothing to send data to.

### After install: no background network calls

Once installed, the core signaltrim mode does not phone home or run background network activity. Verified against the code (audit it yourself — every file is in this repo):

- **The skill itself** (`skills/signaltrim/SKILL.md`) is a markdown prompt. It contains no code.
- **The hooks** (`src/hooks/*.js`, statusline scripts) are local Node/shell scripts. They read and write local files only (flag file, session log, statusline savings file, and optional signalteam agent markdown when you set override env vars). No `http`/`https`/`fetch` anywhere in them.
- **`/signaltrim-stats`** reads Claude Code's session JSONL from your local disk and prints counts. USD figures come from pricing constants hardcoded in the script. Nothing leaves your machine.
- **`signaltrim-shrink`** (MCP middleware) spawns the MCP server *you* configure, locally, and compresses its output in-process. It makes no network calls of its own; any network activity belongs to the server you wrapped.
- **`/signaltrim-compress`** is optional and user-initiated. It reads only the ordinary file path you name, refuses symlinks/reparse points and sensitive path names, sends that content to Claude/Anthropic for compression, validates the candidate locally, saves a human-readable backup under the platform data directory, and atomically replaces the source only after validation passes.

### At install time: exactly these network requests, nothing else

- `curl … install.sh | bash` (or `irm … install.ps1 | iex`) fetches the shim from raw.githubusercontent.com, which delegates to `npx -y github:karurikwao/signaltrim` — npm fetches this repo from GitHub.
- The installer shells out to per-agent CLIs which fetch from their own registries: `claude plugin marketplace add` / `claude plugin install` (Anthropic/GitHub), `gemini extensions install`, `npm view signaltrim-shrink`, `npx -y skills add` (npm).
- **Rare fallback:** if the installer runs detached from a repo checkout, it downloads the hook files from raw.githubusercontent.com **pinned to an immutable release tag** and verifies each against a published SHA-256 manifest before wiring anything (a mismatch aborts). From a normal clone or npx run, files are copied locally — offline installs work.

Nothing is uploaded in any of these steps. Details and the full list of paths written: [INSTALL.md → Privacy](./INSTALL.md#privacy).

### What stays on your machine

Everything except the file content you explicitly pass to `/signaltrim-compress`. Skill/rule files in your agents' config dirs, the mode flag file and merged `settings.json` under `~/.claude/` (or `$CLAUDE_CONFIG_DIR`), the lifetime-savings statusline file, optional signalteam agent overrides, and `.original.md` backups from `/signaltrim-compress` stay local. Uninstall removes what the installer wrote: `npx -y github:karurikwao/signaltrim -- --uninstall`.

### Enterprise / air-gapped use

Core signaltrim mode is self-contained after install and fully functional offline. There is no license server, no external backend, and no data flow to audit beyond the install-time fetches above. Optional `/signaltrim-compress` needs Claude/Anthropic access, and `signaltrim-shrink` may proxy an upstream MCP server that uses the network. For air-gapped environments, clone the repo internally and run the installer from the clone — no network needed for core mode.

## About scanner warnings

- **Windows Defender / SmartScreen on `install.ps1` (#383):** piping a script from the internet into `iex` and writing into agent config directories matches generic dropper heuristics, so AV tools may warn. The script is short and readable in this repo; the hook files it installs are SHA-256-verified against the pinned release manifest. If you'd rather not pipe-to-shell, clone the repo and run `node bin/install.js` — same result, fully inspectable first.
- **Snyk "High Risk" on `signaltrim-compress` (#28):** the compress skill reads a file you name, sends that content to Claude/Anthropic for compression, writes a backup, validates the output, and atomically replaces the file only after validation passes. That file I/O plus model-call behavior is a real capability, not hidden — it does not execute file contents, does not use `shell=True`, and never reads files you did not name.
