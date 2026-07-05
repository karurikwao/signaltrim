# SignalTrim Wiki

![SignalTrim banner](https://raw.githubusercontent.com/karurikwao/signaltrim/main/docs/assets/signaltrim-logo-banner.svg)

SignalTrim is a local toolkit for making AI coding agents answer with less filler while preserving technical meaning. It ships as a prompt skill, installer, Claude Code hook system, statusline badge, memory compression workflow, MCP proxy, and compact subagent pack.

Core promise:

- Shorter agent output.
- Same code, commands, errors, paths, URLs, and identifiers.
- No hosted backend.
- Honest measurement of where tokens are saved and where they are not.

Useful links:

- Live site: https://signaltrim.pages.dev/
- Repository: https://github.com/karurikwao/signaltrim
- Install guide: [Getting Started](Getting-Started.md)
- Full install matrix: [Installation Matrix](Installation-Matrix.md)
- Security model: [Security and Privacy](Security-and-Privacy.md)
- Troubleshooting: [Troubleshooting](Troubleshooting.md)

## What SignalTrim Is

SignalTrim is not one prompt pasted into every editor. It is a multi-surface integration layer:

- Skills and slash commands for agents that understand skill packs.
- Claude Code hooks for automatic activation, mode tracking, and statusline feedback.
- Static rules for IDE-style agents that only support instruction files.
- Native opencode plugin files.
- OpenClaw and Hermes workspace skill installation.
- Memory compression for natural-language files, with backups and validation.
- MCP tool-description shrinker for tool-heavy setups.
- Benchmarks, eval scripts, and honest public numbers.

## What SignalTrim Is Not

SignalTrim does not:

- Reduce every cost category.
- Remove input tokens from normal conversations.
- Hide a network service behind the install path.
- Mutate code blocks, shell commands, URLs, file paths, or exact error text.
- Read arbitrary files in the background.
- Replace normal judgment for safety warnings or irreversible actions.

## First Three Pages To Read

1. [Getting Started](Getting-Started.md) if you want SignalTrim installed.
2. [Concepts and Modes](Concepts-and-Modes.md) if you want to understand how replies change.
3. [Architecture](Architecture.md) if you want to maintain or extend the repo.

## Repo Map

| Path | Purpose |
|---|---|
| `bin/install.js` | Unified installer and uninstall entrypoint. |
| `bin/lib/settings.js` | JSONC-tolerant Claude settings helper. |
| `skills/` | User-facing skills for SignalTrim modes, reviews, commits, stats, help, and compression. |
| `commands/` | Slash-command templates for agent surfaces. |
| `src/hooks/` | Claude Code hook scripts, statusline scripts, and standalone hook installers. |
| `src/plugins/opencode/` | Native opencode plugin, commands, and README. |
| `src/mcp-servers/signaltrim-shrink/` | MCP stdio proxy for compressing tool descriptions. |
| `src/rules/` | Static always-on rule files consumed by `signaltrim-init`. |
| `agents/` | SignalTeam compact subagents. |
| `benchmarks/` | Reproducible output-token benchmark harness. |
| `evals/` | Evaluation helpers and snapshots. |
| `docs/` | Cloudflare Pages launch site and public proof docs. |
| `tests/` | Python and Node regression coverage. |

## Design Principles

- Be local first.
- Preserve exact technical artifacts.
- Prefer agent-native install routes.
- Make every write reversible or obvious.
- Keep proof close to claims.
- Avoid duplicated feature families.
- Fail closed around user content and secrets.

## Current Published Surfaces

- GitHub repo: `karurikwao/signaltrim`
- Cloudflare Pages: `signaltrim.pages.dev`
- GitHub Wiki: this documentation set
- GitHub package install path: `npx -y github:karurikwao/signaltrim -- ...`

## Quick Install

macOS, Linux, WSL, Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/karurikwao/signaltrim/main/install.ps1 | iex
```

Preview first:

```bash
npx -y github:karurikwao/signaltrim -- --dry-run
```

## After Install

In a supported agent, activate with:

```text
/signaltrim
```

Deactivate with:

```text
normal mode
```

Claude Code plugin installs can auto-activate at session start. Static rule installs may need the first command per session.

