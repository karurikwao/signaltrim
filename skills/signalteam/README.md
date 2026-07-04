# signalteam

Decision guide. When to delegate to signaltrim subagents instead of doing the work inline.

## What it does

Tells the main thread when to spawn a signaltrim-style subagent versus the vanilla equivalent. The win: subagent tool-results inject back into main context verbatim, and signaltrim output is roughly 1/3 the size of vanilla prose. Across 20 delegations in one session, that is the difference between context exhaustion and finishing the task.

Three subagents:

| Subagent | Job | Use when |
|----------|-----|----------|
| `signalteam-investigator` | Locate code (read-only) | "Where is X defined / what calls Y / list uses of Z" |
| `signalteam-builder` | Surgical edit, 1-2 files | Scope is obvious, ≤2 files. Refuses 3+ file scope. |
| `signalteam-reviewer` | Diff/file review | One-line findings with severity emoji |

Use vanilla `Explore` or `Code Reviewer` when you want prose, architecture commentary, or rationale. Use main thread directly for one-line answers and 3+ file refactors.

This skill is a decision guide, not a slash command. It activates when the conversation mentions delegation.

## How to invoke

Triggers on phrases like "delegate to subagent", "use signalteam", "spawn investigator", "save context", "compressed agent output".

## Example chaining

Locate → fix → verify (most common):

1. `signalteam-investigator` returns site list (`path:line — symbol — note`)
2. Main thread picks 1-2 sites, hands paths to `signalteam-builder`
3. `signalteam-reviewer` audits the resulting diff

Parallel scout: spawn 2-3 `signalteam-investigator` calls in one message with different angles (defs, callers, tests). Aggregate in main.

## Model overrides

By default, `signalteam-reviewer` and `signalteam-investigator` pin `model: haiku` in their frontmatter; `signalteam-builder` has no `model:` line (uses the API session default). Set env vars in your shell before launching Claude Code to override per-agent:

| Env var | Agent |
|---|---|
| `SIGNALTEAM_REVIEWER_MODEL` | `signalteam-reviewer` |
| `SIGNALTEAM_BUILDER_MODEL` | `signalteam-builder` |
| `SIGNALTEAM_INVESTIGATOR_MODEL` | `signalteam-investigator` |

Example — run reviewer on sonnet, keep others on default:

```sh
export SIGNALTEAM_REVIEWER_MODEL=sonnet
```

Use the same model name strings you'd use in any Claude Code agent frontmatter (e.g. `haiku`, `sonnet`, `opus`).

Overrides patch only the `model:` line in the installed agent's frontmatter; the prompt body is untouched and keeps receiving upstream updates. Plugin installs only — standalone hook installs have no local agent files to patch. Unset or blank = no change. The patch persists in the installed file until the plugin is updated or reinstalled.

## See also

- [`SKILL.md`](./SKILL.md) — full decision matrix and output contracts
- [`agents/signalteam-investigator.md`](../../agents/signalteam-investigator.md)
- [`agents/signalteam-builder.md`](../../agents/signalteam-builder.md)
- [`agents/signalteam-reviewer.md`](../../agents/signalteam-reviewer.md)
- [SignalTrim README](../../README.md) — repo overview
