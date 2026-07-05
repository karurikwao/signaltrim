# SignalTeam Workflow Examples

SignalTeam is the compact subagent pack for investigation, implementation, and review.

## Reviewer Loop

Use when a change already exists and needs risk-focused review.

```text
Investigator: map changed files and test surface.
Reviewer: findings first, file/line references, missing tests.
Builder: fix only confirmed issues.
Reviewer: verify fix and residual risk.
```

Handoff:

```text
Context: auth middleware change.
Evidence: failing boundary test at token expiry.
Decision: use `<=` for expiry comparison.
Verification: unit test added; CI green.
Open risk: clock skew policy not specified.
```

## Builder Loop

Use when scope is known and implementation can proceed.

```text
Investigator: identify owner files and local patterns.
Builder: implement smallest coherent patch.
Reviewer: check regression, docs, and tests.
Builder: address review deltas.
```

## Verifier Loop

Use when the repo needs proof after a broad edit.

```text
Verifier A: run local commands and capture failures.
Verifier B: inspect docs, links, and public surface.
Verifier C: compare issue acceptance criteria to changed files.
```

## Avoiding Duplicated Context

Each handoff should contain:

- What changed.
- Where it changed.
- Why that path was chosen.
- Which commands passed.
- Which risks remain.

Do not copy full logs unless the next agent needs exact error text.
