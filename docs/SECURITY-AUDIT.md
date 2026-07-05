# Security Audit Checklist

Use this before releases and after touching installer, hook, compression, or MCP code.

Wiki guide: [Security and Privacy](https://github.com/karurikwao/signaltrim/wiki/Security-and-Privacy).

## Privacy Model

- Core SignalTrim has no backend.
- Hooks read and write local config/session files only.
- `/signaltrim-stats` reads local Claude Code logs only.
- `signaltrim-shrink` makes no model or network calls of its own.
- `/signaltrim-compress` sends only the named file through the user's model provider.

## Installer Review

- No unbounded recursive deletes.
- Windows shell arguments are guarded.
- User hooks are preserved unless they reference managed script basenames.
- `settings.json` backups are written before mutation.
- JSONC settings parse and rewrite to strict JSON.
- Root install shims require Node 20.19+.

## Compression Review

- Refuses symlinks and reparse points.
- Refuses sensitive-looking paths.
- Backs up before replace.
- Validates headings, paths, URLs, code blocks, inline code, and table shape.
- Leaves original untouched on empty, identical, or invalid model output.

## MCP Review

- Upstream command is required.
- Tool call results pass through.
- Requests pass through.
- Description fields are the default compression target.
- Debug logs never print secrets beyond the upstream catalog text already returned.

## Dependency And Provenance

- Runtime package has no npm dependencies.
- GitHub release artifacts include SHA-256 checksums.
- CI must pass on release commit.
- `npm pack --dry-run --json` reviewed before publish.

## High-Risk Changes

Require extra review for:

- `bin/install.js`
- `bin/lib/settings.js`
- `src/hooks/*`
- `skills/signaltrim-compress/scripts/*`
- `src/mcp-servers/signaltrim-shrink/*`
- `.github/workflows/release.yml`
