---
description: Compress a markdown/text file into signaltrim format to save tokens
---
Compress the file at: $ARGUMENTS

Run the `signaltrim-compress` skill against the given filepath. The skill rewrites
prose into terse signaltrim style — drops articles, filler, hedging — while
preserving code blocks, inline code, URLs, file paths, commands, and markdown
structure exactly. Original is backed up under the platform signaltrim-compress
backup directory before validated output replaces the source.

Only compress natural-language files (`.md`, `.txt`, `.typ`, `.tex`,
extensionless). Refuse source/config files (`.py`, `.js`, `.ts`, `.json`,
`.yaml`, `.toml`, `.sh`, etc.). Never compress an existing `*.original.md`
backup, symlink/reparse point, or sensitive path.
