# Agent Integrations

SignalTrim is designed to meet each agent where it already loads instructions.

## Claude Code

Surfaces:

- Plugin marketplace install.
- Slash commands.
- Hooks.
- Statusline.
- Local stats.

Recommended:

```bash
claude plugin marketplace add karurikwao/signaltrim && claude plugin install signaltrim@signaltrim
```

Fallback:

```bash
npx -y github:karurikwao/signaltrim -- --only claude --with-hooks
```

## Gemini CLI

Gemini reads `GEMINI.md` and extension metadata.

```bash
gemini extensions install https://github.com/karurikwao/signaltrim
```

Main files:

- `gemini-extension.json`
- `GEMINI.md`
- `commands/*.toml`

## opencode

SignalTrim ships a native opencode plugin.

```bash
npx -y github:karurikwao/signaltrim -- --only opencode
```

Writes:

- `~/.config/opencode/plugins/signaltrim/`
- `~/.config/opencode/commands/`
- `~/.config/opencode/agents/`
- `~/.config/opencode/skills/`
- `~/.config/opencode/AGENTS.md`
- `~/.config/opencode/opencode.json`

Main source:

```text
src/plugins/opencode/
```

## OpenClaw

OpenClaw installs into the workspace skill folder and `SOUL.md`.

```bash
npx -y github:karurikwao/signaltrim -- --only openclaw
```

Main source:

```text
bin/lib/openclaw.js
src/rules/signaltrim-openclaw-bootstrap.md
```

## Hermes

Hermes gets native skill directories copied into its skills root.

```bash
npx -y github:karurikwao/signaltrim -- --only hermes
```

## Codex, Cursor, Windsurf, Cline, and Skills CLI Agents

These use:

```bash
npx skills add karurikwao/signaltrim -a <profile>
```

For repo-local always-on behavior:

```bash
npx -y github:karurikwao/signaltrim -- --with-init
```

## GitHub Copilot and Static Rule Agents

Some agents do not have a runtime hook or plugin API. SignalTrim writes static instruction files where possible:

- `.github/copilot-instructions.md`
- `.cursor/rules/signaltrim.mdc`
- `.windsurf/rules/signaltrim.md`
- `.clinerules/signaltrim.md`
- `AGENTS.md`

## Integration Rule

If an agent has a native plugin API, prefer it.

If an agent only reads files, write one small rule file from `src/rules/signaltrim-activate.md`.

If an agent supports neither, use skills CLI profiles where available.

