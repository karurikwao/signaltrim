# Installation Matrix

SignalTrim supports two installation classes:

- Native or semi-native integration for agents with plugin, hook, extension, or config APIs.
- Static skill/rule installation for agents that load instruction files.

## Unified Installer Flags

Canonical full matrix with every current installer profile: [INSTALL.md](https://github.com/karurikwao/signaltrim/blob/main/INSTALL.md).

| Flag | Use |
|---|---|
| `--dry-run` | Print planned commands and writes. |
| `--only <id>` | Install one agent. Repeatable. |
| `--all` | Plugin, hooks, statusline, and repo-local rules. |
| `--minimal` | Plugin or extension only. |
| `--with-hooks` | Force standalone Claude Code hooks. |
| `--no-hooks` | Skip standalone hooks. |
| `--with-init` | Write repo-local IDE rule files. |
| `--with-mcp-shrink="<cmd>"` | Register MCP shrink proxy around an upstream MCP command. |
| `--no-mcp-shrink` | Skip MCP shrink. Default. |
| `--config-dir <path>` | Claude Code config dir for hooks and settings. |
| `--force` | Re-run even if target reports already installed. |
| `--uninstall` | Remove SignalTrim-managed installation artifacts. |
| `--list` | Print provider matrix and detection status. |

## Primary Agents

| Agent | Installer id | Skills profile | Command | Detection type | Auto-activation |
|---|---|---|---|---|---|
| Claude Code | `claude` | n/a | `claude plugin marketplace add karurikwao/signaltrim && claude plugin install signaltrim@signaltrim` | CLI probe | Yes |
| Gemini CLI | `gemini` | n/a | `gemini extensions install https://github.com/karurikwao/signaltrim` | CLI probe | Yes |
| opencode | `opencode` | n/a | `npx -y github:karurikwao/signaltrim -- --only opencode` | CLI/config probe | Yes |
| OpenClaw | `openclaw` | n/a | `npx -y github:karurikwao/signaltrim -- --only openclaw` | Workspace env | Yes |
| Hermes Agent | `hermes` | n/a | `npx -y github:karurikwao/signaltrim -- --only hermes` | Config probe | Yes |
| Codex CLI | `codex` | `codex` | `npx skills add karurikwao/signaltrim -a codex` | Skills profile | Per session |
| Cursor | `cursor` | `cursor` | `npx skills add karurikwao/signaltrim -a cursor` | Skills profile | Per session unless `--with-init` |
| Windsurf | `windsurf` | `windsurf` | `npx skills add karurikwao/signaltrim -a windsurf` | Skills profile | Per session unless `--with-init` |
| Cline | `cline` | `cline` | `npx skills add karurikwao/signaltrim -a cline` | Skills profile | Per session unless `--with-init` |

## Long-Tail Profiles

The installer delegates many profiles through `npx skills add`:

- Continue
- Kilo Code
- Roo Code
- Augment Code
- Aider Desk
- Sourcegraph Amp
- IBM Bob
- Crush
- Devin
- Droid
- ForgeCode
- Block Goose
- iFlow CLI
- Kiro CLI
- Mistral Vibe
- OpenHands
- Qwen Code
- Atlassian Rovo Dev
- Tabnine CLI
- Trae
- Warp
- Replit Agent
- JetBrains Junie
- Qoder
- Google Antigravity

Use:

```bash
npx skills add karurikwao/signaltrim -a <profile>
```

## Soft Probes

Some agents do not expose a reliable local detection signal. For those, the installer will not auto-install unless you explicitly pass `--only <id>`.

Examples:

```bash
npx -y github:karurikwao/signaltrim -- --only copilot --with-init
npx -y github:karurikwao/signaltrim -- --only junie
```

## Repo-Local Rule Files

`--with-init` writes always-on rules into the current repository where supported:

- `.cursor/rules/signaltrim.mdc`
- `.windsurf/rules/signaltrim.md`
- `.clinerules/signaltrim.md`
- `.github/copilot-instructions.md`
- `.opencode/AGENTS.md`
- `AGENTS.md`

The single source is:

```text
src/rules/signaltrim-activate.md
```

## Safety Notes

- `--config-dir` scopes Claude Code hook files and `settings.json` only.
- `--config-dir` does not redirect third-party CLIs like `claude plugin install` or `gemini extensions install`.
- Dry-run mode is intended to be side-effect free.
- The installer writes a `settings.json.bak` before merging Claude settings.
