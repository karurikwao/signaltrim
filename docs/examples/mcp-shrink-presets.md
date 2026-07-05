# MCP Shrink Presets

`signaltrim-shrink` wraps an upstream MCP server. It compresses listed prose fields before the model reads them.

Wiki guide: [MCP Shrink](https://github.com/karurikwao/signaltrim/wiki/MCP-Shrink) and [Examples](https://github.com/karurikwao/signaltrim/wiki/Examples).

## Concise

Use when tool descriptions are long but already structured.

```bash
SIGNALTRIM_SHRINK_FIELDS=description \
npx -y --package github:karurikwao/signaltrim signaltrim-shrink \
  npx @modelcontextprotocol/server-filesystem /tmp
```

Expected shape:

```text
Before: "Read files from a configured filesystem root. This tool should be used whenever..."
After:  "Read files from configured filesystem root."
```

## Balanced

Use for mixed tool, prompt, and resource lists.

```bash
SIGNALTRIM_SHRINK_FIELDS=description,title,summary \
npx -y --package github:karurikwao/signaltrim signaltrim-shrink \
  npx @modelcontextprotocol/server-filesystem /tmp
```

Expected shape:

```text
Identifiers unchanged. Prose shorter. Paths and argument names preserved.
```

## High Compression

Use only when the MCP catalog is huge and you already know the tool family.

```bash
SIGNALTRIM_SHRINK_FIELDS=description,title,summary,details \
SIGNALTRIM_SHRINK_DEBUG=1 \
npx -y --package github:karurikwao/signaltrim signaltrim-shrink \
  npx @modelcontextprotocol/server-filesystem /tmp
```

Expected shape:

```text
Debug logs print per-field deltas to stderr. Tool call results are still passed through.
```

## Installer Form

```bash
npx -y github:karurikwao/signaltrim -- \
  --with-mcp-shrink="npx @modelcontextprotocol/server-filesystem /tmp"
```

Bare `--with-mcp-shrink` is invalid. The proxy needs an upstream command.
