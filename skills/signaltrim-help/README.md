# signaltrim-help

Quick-reference card. One shot, no mode change.

## What it does

Prints a cheat sheet of all signaltrim modes, sibling skills, deactivation triggers, and how to set the default mode via env var or config file. One-shot display — does not flip the active mode, write flag files, or persist anything. Use when you forget the slash commands.

## How to invoke

```
/signaltrim-help
```

Also triggers on "signaltrim help", "what signaltrim commands", "how do I use signaltrim".

## Example output

```
Modes:
  /signaltrim              full (default)
  /signaltrim lite         lighter
  /signaltrim ultra        extreme
  /signaltrim wenyan       classical Chinese

Skills:
  /signaltrim-commit       terse Conventional Commits
  /signaltrim-review       one-line PR comments
  /signaltrim-stats        session token savings

Deactivate:
  "stop signaltrim" or "normal mode"
```

## See also

- [`SKILL.md`](./SKILL.md) — full reference card
- [SignalTrim README](../../README.md) — repo overview
