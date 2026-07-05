# Benchmark Comparison

SignalTrim reports output-token reduction only. It does not claim input tokens, reasoning tokens, or rule overhead disappear.

## Current Snapshot

Version: `0.6.4`

| Task | Normal | SignalTrim | Saved | Quality note |
|---|---:|---:|---:|---|
| Explain React re-render bug | 1180 | 159 | 87% | Core cause and `useMemo` fix preserved. |
| Fix auth middleware token expiry | 704 | 121 | 83% | Operator-level bug preserved. |
| Set up PostgreSQL connection pool | 2347 | 380 | 84% | Steps and key pool settings preserved. |
| Explain git rebase vs merge | 702 | 292 | 58% | Tradeoff still clear. |
| Refactor callback to async/await | 387 | 301 | 22% | Already-compact task leaves less room. |
| Architecture: microservices vs monolith | 446 | 310 | 30% | Pros and cons retained. |
| Review PR for security issues | 678 | 398 | 41% | Findings-first structure retained. |
| Docker multi-stage build | 1042 | 290 | 72% | Commands and stage names retained. |
| Debug PostgreSQL race condition | 1200 | 232 | 81% | Locking and transaction details retained. |
| Implement React error boundary | 3454 | 456 | 87% | Code-oriented guidance retained. |
| **Average** | **1214** | **294** | **65%** | Output-token reduction only. |

## Repeat The Eval

```bash
python benchmarks/run.py
uv run --with tiktoken python evals/measure.py
```

Committed snapshot:

```text
evals/snapshots/results.json
```

Prompt sources:

```text
benchmarks/prompts.json
evals/prompts/en.txt
```

## What To Compare

Track three values separately:

- Compression ratio: output token reduction.
- Fidelity: exact technical artifacts preserved.
- Runtime cost: input, output, reasoning, and rule overhead.

## Regression Rules

A benchmark update is acceptable only when:

- Prompt inputs are committed.
- Snapshot data is committed.
- The README headline number matches snapshot evidence.
- `docs/HONEST-NUMBERS.md` still explains the caveats.
- Exact commands, paths, URLs, identifiers, and error strings are not lost.
