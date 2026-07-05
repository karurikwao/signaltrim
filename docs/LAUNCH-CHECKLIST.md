# Launch Checklist

Use this before a public launch push.

Wiki guide: [Home](https://github.com/karurikwao/signaltrim/wiki) and [Development and Releases](https://github.com/karurikwao/signaltrim/wiki/Development-and-Releases).

## Repo Surface

- README badge row shows CI, version, license, and Node engine.
- README GIF renders and uses current SignalTrim name.
- Live demo link works.
- Launch page link works.
- Wiki tab has Home, install, troubleshooting, MCP, hooks, and security pages.
- Project tab shows a public roadmap.

## Proof Surface

- `npm test` passes.
- `npm run smoke` passes.
- `npm run check:install-surfaces` passes.
- `npm run verify` passes.
- Latest GitHub CI run is green.
- Benchmark headline links to reproducible data.
- Honest numbers caveat remains visible.

## Assets

- `docs/assets/signaltrim-demo.gif`
- `docs/assets/signaltrim-logo-banner.svg`
- `docs/assets/signaltrim-mark.svg`
- `docs/assets/launch-page-preview.svg`

## Community Posts

### GitHub Trending

Lead with:

```text
SignalTrim makes AI coding agents answer with less filler while preserving code, commands, paths, and errors.
```

Show:

- Before/after example.
- Local install command.
- Benchmark caveat.
- Link to roadmap.

### Hacker News

Keep the title plain:

```text
Show HN: SignalTrim - proof-first token discipline for AI coding agents
```

Avoid:

- Huge cost-saving claims.
- Claims about input tokens.
- "Replaces your agent" language.

### Reddit / Product Communities

Use practical framing:

```text
I built a local prompt/hook toolkit that makes coding agents less verbose without hiding the tradeoffs.
```

## Pinned Issue Readiness

- One issue for installation support.
- One issue for integration requests.
- One issue for benchmark discussion.
- Labels and templates are current.
