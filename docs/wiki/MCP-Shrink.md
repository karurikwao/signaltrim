# MCP Shrink

`signaltrim-shrink` is an MCP stdio proxy. It wraps an upstream MCP server and compresses prose fields before the model reads them.

## Why It Exists

Many MCP servers return large tool catalogs. Tool descriptions can consume meaningful context before any work begins.

`signaltrim-shrink` reduces that overhead by compressing descriptions while preserving identifiers, paths, URLs, code-like tokens, and semantics.

## Install Through SignalTrim

```bash
npx -y github:karurikwao/signaltrim -- --with-mcp-shrink="npx @modelcontextprotocol/server-filesystem /tmp"
```

Windows path with spaces:

```bash
npx -y github:karurikwao/signaltrim -- --with-mcp-shrink="\"C:\Program Files\MCP Server\server.exe\" --stdio"
```

## Direct Run

```bash
npx -y --package github:karurikwao/signaltrim signaltrim-shrink <upstream-command> [...args]
```

## Claude MCP Shape

The installer registers a command equivalent to:

```text
claude mcp add signaltrim-shrink -- npx -y --package github:karurikwao/signaltrim signaltrim-shrink <upstream>
```

## What It Touches

Compressed by default:

- `description`

Response families:

- `tools/list`
- `prompts/list`
- `resources/list`

Passed through unchanged:

- Requests.
- Tool call results.
- Resource content.
- Prompt content except listed fields.

## Environment

| Env var | Default | Meaning |
|---|---|---|
| `SIGNALTRIM_SHRINK_FIELDS` | `description` | Comma-separated field names to compress. |
| `SIGNALTRIM_SHRINK_DEBUG` | `0` | Set `1` to log per-field deltas to stderr. |

## Source

```text
src/mcp-servers/signaltrim-shrink/index.js
src/mcp-servers/signaltrim-shrink/compress.js
src/mcp-servers/signaltrim-shrink/spawn-options.js
```

## Safety Notes

- The proxy makes no model or network calls of its own.
- Any network activity belongs to the upstream MCP server or `npx` install path.
- Windows spawn uses shell support so `.cmd` shims resolve.
- Windows arguments are checked for unsafe shell metacharacters.
- Upstream commands with quoted spaces are preserved by the installer parser.

## Tests

```bash
node tests/test_mcp_shrink.js
npm test
```

Preset examples: [docs/examples/mcp-shrink-presets.md](https://github.com/karurikwao/signaltrim/blob/main/docs/examples/mcp-shrink-presets.md).
