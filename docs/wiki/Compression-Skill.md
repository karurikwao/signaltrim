# Compression Skill

`/signaltrim-compress` is different from normal SignalTrim mode. Normal mode reduces output tokens in replies. The compression skill rewrites natural-language files to reduce future input size.

## Use Case

Good targets:

- `CLAUDE.md`
- Project memory files.
- Team preferences.
- Long TODO notes.
- Agent behavior notes.

Bad targets:

- Source code.
- Config files.
- Secrets.
- Credentials.
- Generated lockfiles.
- Binary files.

## Command

```text
/signaltrim-compress path/to/file.md
```

or run the Python module from the skill directory during development.

## Safety Model

Before calling a model, compression checks:

- File exists.
- File is a regular file.
- No symlink or reparse-point components.
- File looks like natural language.
- File is valid UTF-8.
- File is not too large.
- Path and filename do not look sensitive.

Sensitive examples refused:

- `.env`
- `.ssh/`
- `.aws/`
- `credentials.*`
- `secrets.*`
- private key file extensions

## Write Model

Compression uses this sequence:

```text
read original bytes
preserve YAML frontmatter
call model for body compression
write backup outside source directory
write temp candidate beside source
validate candidate
retry fix if needed
atomic replace only after validation passes
```

The original file is not overwritten until a candidate passes validation.

## Backups

Backups live under a platform-aware data directory, not beside the source file.

Reason: source-side `.original.md` backups can be re-ingested by agent skill loaders as live instructions.

## Validation

The validator checks:

- Heading count and order.
- Heading text.
- Fenced code blocks exactly.
- URLs exactly.
- File paths exactly.
- Inline code counts.
- Bullet loss.
- Markdown table shape.

Table validation checks structure, not cell prose. Cell text may be compressed, but rows and columns must remain.

## Known Tradeoffs

- Bullet expansion can be a warning rather than an error.
- Bullet loss is an error.
- Table cell text is not compared exactly.
- The model provider receives the file content you explicitly pass.

## Development Tests

```bash
python -m unittest tests.test_compress_safety tests.test_validate_inline tests.test_detect
python tests/verify_repo.py
```

## Source Files

```text
skills/signaltrim-compress/scripts/compress.py
skills/signaltrim-compress/scripts/cli.py
skills/signaltrim-compress/scripts/detect.py
skills/signaltrim-compress/scripts/validate.py
```

Plugin mirror:

```text
plugins/signaltrim/skills/signaltrim-compress/scripts/
```

Keep these in sync.

