# FAQ

## Does SignalTrim save input tokens?

Normal SignalTrim mode saves output tokens. It does not make input tokens disappear.

`/signaltrim-compress` is separate. It rewrites selected natural-language files so future sessions may load fewer input tokens.

## Does SignalTrim reduce reasoning tokens?

No. It controls reply style, not hidden reasoning budget.

## Does SignalTrim have a backend?

No. Core SignalTrim has no hosted backend, account, telemetry, or analytics.

## Does it upload my code?

Core mode does not upload files.

`/signaltrim-compress` sends the named file content to the configured model provider because compression is model-backed. It only reads the file you name and refuses symlinks and sensitive paths.

## Why are there multiple install paths?

Different agents load instructions differently. SignalTrim uses native paths where possible:

- Claude Code plugin and hooks.
- Gemini extension.
- opencode plugin.
- OpenClaw and Hermes skill locations.
- Skills CLI profiles.
- Static rule files.

## Why not only one prompt?

One prompt cannot provide:

- Automatic Claude activation.
- Statusline feedback.
- Local stats.
- Safe memory compression.
- MCP description shrink.
- Native opencode behavior.
- Agent-specific uninstall cleanup.

## Can I use it in a corporate or air-gapped environment?

Yes for core mode if you clone internally and install from the clone. Optional compression and upstream MCP servers may need network access depending on your setup.

## What happens if I already have a Claude statusline?

SignalTrim does not overwrite it. The installer prints a note and leaves your statusline alone.

## What if my hook path contains the word `signaltrim` but is not SignalTrim?

The installer and uninstaller match managed hooks by exact script basename. User hooks that merely mention `signaltrim` are preserved.

## Can I remove it?

Yes:

```bash
npx -y github:karurikwao/signaltrim -- --uninstall
```

You may still need to manually remove repo-local rule files created by `--with-init`.

## Why does the README say 65%?

That is the current average output-token reduction from the committed benchmark prompts. Read [Benchmarks and Evals](Benchmarks-and-Evals.md) and `docs/HONEST-NUMBERS.md` for caveats.

## Why does compression refuse some markdown files?

Because the file path or content may be unsafe, non-natural-language, too large, invalid UTF-8, or structurally risky. Refusal is preferred over silent data loss.

