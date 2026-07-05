# CLI Smoke Tests

SignalTrim has a fast smoke command for proving that the public CLI surfaces still launch and fail cleanly.

```bash
npm run smoke
```

The smoke suite checks:

- `node bin/install.js --help`
- `node bin/install.js --list`
- invalid flag handling
- `--with-mcp-shrink` missing-upstream failure text
- package `bin` targets
- compression validation rejecting lost inline code

Run this before release work:

```bash
npm test
npm run smoke
npm run check:install-surfaces
npm run test:python
npm run verify
```

CI runs the smoke command on every push and pull request.

## Failure Triage

| Failure | First check |
|---|---|
| `--help` fails | `node --check bin/install.js` |
| `--list` misses providers | `PROVIDERS` in `bin/install.js` |
| invalid flag exits `0` | `parseArgs()` in `bin/install.js` |
| MCP error text missing | `--with-mcp-shrink` branch in `parseArgs()` |
| compression validator smoke fails | `tests/test_validate_inline.py` and `skills/signaltrim-compress/scripts/validate.py` |
