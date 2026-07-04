<p align="center">
  <img src="../../docs/assets/signaltrim-mark.svg" width="80" alt="SignalTrim mark" />
</p>

<h1 align="center">signaltrim-compress</h1>

<p align="center">
  <strong>Compress memory files. Save input tokens on future sessions.</strong>
</p>

---

`signaltrim-compress` rewrites natural-language memory files such as `CLAUDE.md`, todos, and preference notes into SignalTrim style. The goal is simple: keep the same instructions with fewer tokens loaded every session.

## Usage

```text
/signaltrim-compress CLAUDE.md
```

After success:

```text
CLAUDE.md     compressed file Claude reads next session
backup path   printed after success, stored in the SignalTrim backup directory
```

Original content is preserved in a human-readable backup. Run the command again after editing the file.

## Benchmarks

Real results on fixture files:

| File | Original | Compressed | Saved |
|------|----------:|----------:|------:|
| `claude-md-preferences.md` | 706 | 285 | **59.6%** |
| `project-notes.md` | 1145 | 535 | **53.3%** |
| `claude-md-project.md` | 1122 | 636 | **43.3%** |
| `todo-list.md` | 627 | 388 | **38.1%** |
| `mixed-with-code.md` | 888 | 560 | **36.9%** |
| **Average** | **898** | **481** | **46%** |

Validation checks headings, code blocks, URLs, file paths, commands, bullets, and table structure before replacement.

## Before / After

<table>
<tr>
<td width="50%">

### Original

> "I strongly prefer TypeScript with strict mode enabled for all new code. Please don't use `any` type unless there's genuinely no way around it, and if you do, leave a comment explaining the reasoning. I find that taking the time to properly type things catches a lot of bugs before they ever make it to runtime."

</td>
<td width="50%">

### SignalTrim

> "Prefer TypeScript strict mode always. No `any` unless unavoidable. Comment why if used. Proper types catch bugs early."

</td>
</tr>
</table>

Same instruction. Fewer tokens. No code or command mutation.

## Security

`signaltrim-compress` uses subprocess and file I/O because it validates and replaces a named local file. It refuses sensitive paths, refuses symlink/reparse targets, writes a same-directory temp candidate, validates that candidate, saves a backup, then atomically replaces the original only after validation passes. See [SECURITY.md](./SECURITY.md).

## Files It Accepts

| Type | Compress? |
|------|-----------|
| `.md`, `.txt`, `.rst`, `.typ`, `.typst`, `.tex` | Yes |
| Extensionless natural language | Yes |
| `.py`, `.js`, `.ts`, `.json`, `.yaml` | No, treated as code/config |
| `*.original.md` | No, treated as backup |

## Flow

```text
/signaltrim-compress CLAUDE.md
        |
detect file type
        |
model compresses prose
        |
validate headings, code blocks, URLs, file paths, commands, bullets
        |
targeted repair if validation fails
        |
write temp candidate
        |
validate candidate
        |
write backup
        |
atomic replace
```

Only the compression and targeted repair calls use model tokens. Detection, validation, backup, and replace are local Python.

## Part Of SignalTrim

- `signaltrim` compresses agent replies.
- `signaltrim-compress` compresses memory files the agent reads.
