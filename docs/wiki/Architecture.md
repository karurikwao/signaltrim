# Architecture

SignalTrim is organized as a local integration toolkit with one installer and several agent-specific surfaces.

## High-Level Flow

```text
User install command
  -> install.sh / install.ps1 shim
  -> npx -y github:karurikwao/signaltrim
  -> bin/install.js
  -> provider detection
  -> native plugin / extension / hook / skill / rule install
```

## Main Components

| Component | Path | Purpose |
|---|---|---|
| Installer | `bin/install.js` | Detects agents, installs, uninstalls, prints matrix. |
| Settings helper | `bin/lib/settings.js` | Parses JSONC, validates Claude settings hooks, preserves user hooks. |
| OpenClaw helper | `bin/lib/openclaw.js` | Installs SignalTrim into OpenClaw workspace. |
| opencode helper | `bin/lib/opencode-agent.js` | Sanitizes opencode agent frontmatter. |
| Skills | `skills/` | Agent-readable behavior definitions. |
| Commands | `commands/` | Slash-command markdown/TOML templates. |
| Claude hooks | `src/hooks/` | Runtime activation, mode tracking, stats, statusline. |
| Static rules | `src/rules/` | Repo-local always-on instructions. |
| Init tool | `src/tools/signaltrim-init.js` | Writes static rule files into a repo. |
| MCP proxy | `src/mcp-servers/signaltrim-shrink/` | Compresses MCP description fields. |
| opencode plugin | `src/plugins/opencode/` | Native opencode integration. |
| SignalTeam agents | `agents/` | Compact subagents for investigation, build, review. |

## Installer Responsibilities

`bin/install.js` owns:

- CLI flag parsing.
- Agent detection.
- Safe dry-run behavior.
- Claude Code plugin installation.
- Standalone hook installation fallback.
- opencode native install.
- OpenClaw and Hermes installs.
- `npx skills add` fallback routing.
- MCP shrink registration.
- Uninstall cleanup.

The root shell scripts are shims only. They should stay small and delegate to the Node installer.

## Claude Runtime Responsibilities

Claude Code runtime behavior is split:

- `signaltrim-activate.js`: emits rules and sets mode flag.
- `signaltrim-mode-tracker.js`: tracks `/signaltrim` commands and natural-language toggles.
- `signaltrim-stats.js`: reads local session logs and estimates output savings.
- `signaltrim-statusline.sh`: POSIX statusline badge.
- `signaltrim-statusline.ps1`: Windows statusline badge.
- `signaltrim-config.js`: shared config, safe flag writes, history helpers.

## Data Flow

Core mode:

```text
Skill/rule text -> agent context -> compact reply
```

Claude Code hooks:

```text
SessionStart -> signaltrim-activate.js -> .signaltrim-active
UserPromptSubmit -> signaltrim-mode-tracker.js -> .signaltrim-active
Statusline -> signaltrim-statusline.* -> badge
```

Stats:

```text
Claude session JSONL -> signaltrim-stats.js -> local history + statusline suffix
```

Compression:

```text
Named file -> safety checks -> model compression -> temp candidate -> validation -> backup -> atomic replace
```

MCP shrink:

```text
MCP client -> signaltrim-shrink -> upstream MCP server
tools/list response -> description fields compressed -> client
tools/call response -> passed through unchanged
```

## Duplication Policy

The repo has mirrored artifacts for packaging and plugin support. When editing a source file, check whether a mirror exists:

- `skills/signaltrim-compress/...`
- `plugins/signaltrim/skills/signaltrim-compress/...`
- `skills/...`
- `plugins/signaltrim/skills/...`
- `agents/...`
- `plugins/signaltrim/agents/...`

Run:

```bash
python tests/verify_repo.py
```

before release to catch sync drift.

