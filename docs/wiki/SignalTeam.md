# SignalTeam

SignalTeam is the compact subagent pack bundled with SignalTrim.

## Agents

| Agent | File | Role |
|---|---|---|
| Investigator | `agents/signalteam-investigator.md` | Find facts, map code paths, isolate causes. |
| Builder | `agents/signalteam-builder.md` | Make bounded implementation changes. |
| Reviewer | `agents/signalteam-reviewer.md` | Review for regressions, missing tests, and risks. |

Mirrors:

```text
plugins/signaltrim/agents/
```

## Behavior

SignalTeam follows SignalTrim style by default:

- Compact.
- Technical.
- Low ceremony.
- Findings first.
- No fake certainty.

It should drop back to normal clarity for:

- Security warnings.
- Irreversible actions.
- Ambiguous multi-step instructions.
- Anything where fragments could be unsafe.

## opencode Packaging

opencode has stricter frontmatter expectations. The installer sanitizes agent files before copying them into opencode config.

Relevant helper:

```text
bin/lib/opencode-agent.js
```

Test:

```bash
npm test
```

## Maintainer Notes

When changing an agent:

1. Edit the source under `agents/`.
2. Sync the mirror under `plugins/signaltrim/agents/`.
3. Run `python tests/verify_repo.py`.
4. Run `npm test`.

Workflow examples:

```text
docs/examples/signalteam-workflows.md
```
