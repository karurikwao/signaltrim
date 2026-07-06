# Advanced Compression Modes

SignalTrim modes change response density, not task semantics.

Wiki guide: [Concepts and Modes](https://github.com/karurikwao/signaltrim/wiki/Concepts-and-Modes).

## Mode Matrix

| Mode | Use when | Avoid when | Quality check |
|---|---|---|---|
| `lite` | User wants concise but complete prose. | The user asked for maximal brevity. | Sentences remain natural. |
| `full` | Default coding work. | High-stakes clarity needs extra words. | Commands, paths, and findings survive. |
| `ultra` | Experienced user wants dense technical output. | Onboarding, teaching, or ambiguous tasks. | No invented abbreviations. |
| `wenyan-lite` | Chinese-language compression with readability. | Mixed-language code review. | Chinese register preserves exact code terms. |
| `wenyan-full` | Balanced classical Chinese compression. | User did not ask for Chinese. | Meaning remains traceable. |
| `wenyan-ultra` | Maximum classical compression. | Safety, legal, medical, financial, or uncertain work. | No loss of warning text. |
| `off` | Normal agent tone. | None. | SignalTrim flag removed. |

## Examples

### Code Review

```text
/signaltrim full
Review this PR for bugs. Findings first, exact file paths.
```

Good output shape:

```text
P1 src/auth/session.ts:42 - expiry check uses `<`, so tokens valid at exact expiry pass. Use `<=`.
Tests missing for boundary timestamp.
```

### Bug Triage

```text
/signaltrim ultra
Triage this failing install log.
```

Good output shape:

```text
Root cause: `node` absent from PATH. Installer exits before `npx`.
Fix: install Node 20.19+, reopen shell, run `node -p "process.versions.node"`.
```

### Handoff Summary

```text
/signaltrim lite
Summarize implementation state for the next maintainer.
```

Good output shape:

```text
Implemented CI badge and smoke workflow. Local tests pass. Latest CI run is green. Remaining risk: publish the first GitHub release before advertising package registries.
```

## Failure Modes

| Failure | Symptom | Fix |
|---|---|---|
| Too terse | User cannot safely act. | Drop to `lite` or normal prose. |
| Artifact loss | Path, command, URL, or error string changed. | Restore exact artifact. |
| Unsupported abbreviation | New acronym appears without source. | Spell it out. |
| Hidden uncertainty | Risky assumption sounds final. | State uncertainty directly. |
