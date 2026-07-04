# Security

## Snyk High Risk Rating

`signaltrim-compress` receives a Snyk High Risk rating due to static analysis heuristics. This document explains what the skill does and does not do.

### What triggers the rating

1. **subprocess usage**: The skill calls the `claude` CLI via `subprocess.run()` as a fallback when `ANTHROPIC_API_KEY` is not set. The subprocess call uses a fixed argument list — no shell interpolation occurs. User file content is passed via stdin, not as a shell argument.

2. **File read/write**: The skill reads the ordinary file path the user explicitly points it at, refuses symlinks/reparse points and sensitive path names, compresses it, writes a random same-directory temp candidate, validates that candidate, saves a `.original.md` backup under the platform signaltrim-compress backup directory, then atomically replaces the original only after validation passes. No other source files are read.

### What the skill does NOT do

- Does not execute user file content as code
- Does not make network requests except to Anthropic's API (via SDK or CLI)
- Does not follow symlinks/reparse points or read files outside the ordinary path the user provides
- Does not use shell=True or string interpolation in subprocess calls
- Does not collect or transmit any data beyond the file being compressed

### Auth behavior

If `ANTHROPIC_API_KEY` is set, the skill uses the Anthropic Python SDK directly (no subprocess). If not set, it falls back to the `claude` CLI, which uses the user's existing Claude desktop authentication.

### File size limit

Files larger than 500KB are rejected before any API call is made.

### Reporting a vulnerability

If you believe you've found a genuine security issue, do not open a public issue. Use GitHub private vulnerability reporting for this repo or email the maintainers privately.
