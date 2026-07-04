#!/usr/bin/env python3
"""
SignalTrim Memory Compression Orchestrator

Usage:
    python scripts/compress.py <filepath>
"""

import os
import re
import hashlib
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

OUTER_FENCE_REGEX = re.compile(
    r"\A\s*(`{3,}|~{3,})[^\n]*\n(.*)\n\1\s*\Z", re.DOTALL
)

# YAML frontmatter: starts at file start with --- on its own line, ends with --- on its own line.
# Captures the entire block (including delimiters and trailing newline) and the body after.
FRONTMATTER_REGEX = re.compile(
    r"\A(---\r?\n.*?\r?\n---\r?\n)(.*)", re.DOTALL
)


def split_frontmatter(text: str):
    """Split YAML frontmatter from body. Returns (frontmatter, body).

    Memory files (and many other markdown docs) start with a YAML frontmatter
    block delimited by `---` lines. The compression LLM has a habit of stripping
    or rewriting these despite preserve-structure rules in the prompt — so we
    surgically remove the frontmatter before compression and prepend it back
    verbatim to the output. Files without frontmatter pass through unchanged.
    """
    m = FRONTMATTER_REGEX.match(text)
    if m:
        return m.group(1), m.group(2)
    return "", text

# Filenames and paths that almost certainly hold secrets or PII. Compressing
# them ships raw bytes to the Anthropic API — a third-party data boundary that
# developers on sensitive codebases cannot cross. detect.py already skips .env
# by extension, but credentials.md / secrets.txt / ~/.aws/credentials would
# slip through the natural-language filter. This is a hard refuse before read.
SENSITIVE_BASENAME_REGEX = re.compile(
    r"(?ix)^("
    r"\.env(\..+)?"
    r"|\.netrc"
    r"|credentials(\..+)?"
    r"|secrets?(\..+)?"
    r"|passwords?(\..+)?"
    r"|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?"
    r"|authorized_keys"
    r"|known_hosts"
    r"|.*\.(pem|key|p12|pfx|crt|cer|jks|keystore|asc|gpg)"
    r")$"
)

SENSITIVE_PATH_COMPONENTS = frozenset({".ssh", ".aws", ".gnupg", ".kube", ".docker"})

SENSITIVE_NAME_TOKENS = (
    "secret", "credential", "password", "passwd",
    "apikey", "accesskey", "token", "privatekey",
)


def backup_dir_for(filepath: Path) -> Path:
    """Resolve the out-of-tree backup directory for a given source file.

    Backups must live OUTSIDE the source directory so skill auto-loaders
    (Claude Code rules/, opencode instructions/, etc.) stop re-ingesting the
    `.original.md` copies as live files. Base dir is platform-aware:
      - Windows: %LOCALAPPDATA%\\signaltrim-compress\\backups
      - else:    $XDG_DATA_HOME/signaltrim-compress/backups if set,
                 else ~/.local/share/signaltrim-compress/backups

    The source file's parent-dir name is mirrored under the base to reduce
    cross-project collisions (e.g. two `task.md` files in different repos).
    """
    if os.name == "nt" or sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA")
        base = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
        base = base / "signaltrim-compress" / "backups"
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"
        base = base / "signaltrim-compress" / "backups"
    parent_key = hashlib.sha256(str(filepath.parent.resolve()).encode("utf-8")).hexdigest()[:12]
    return base / f"{filepath.parent.name}-{parent_key}"


def backup_path_for(filepath: Path) -> Path:
    """Resolve the exact backup path for a source file."""
    filepath = filepath.resolve()
    if filepath.suffix.lower() == ".md":
        backup_name = filepath.stem + ".original.md"
    else:
        backup_name = filepath.name + ".original.md"
    return backup_dir_for(filepath) / backup_name


def is_reparse_point(st) -> bool:
    """Return True for Windows symlinks/junctions/reparse points."""
    attrs = getattr(st, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attrs & reparse)


def assert_no_symlink_components(filepath: Path) -> None:
    """Refuse symlinks/reparse points anywhere in the user-supplied path."""
    path = filepath if filepath.is_absolute() else Path.cwd() / filepath
    path = Path(os.path.abspath(path))
    if path.anchor:
        current = Path(path.anchor)
        parts = path.parts[1:]
    else:
        current = Path(".")
        parts = path.parts
    for part in parts:
        current = current / part
        try:
            st = current.lstat()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        if stat.S_ISLNK(st.st_mode) or is_reparse_point(st):
            raise ValueError(
                f"Refusing to compress {current}: symlinks and reparse points "
                "are not followed. Pass the real file path instead."
            )


def assert_regular_nonsymlink(filepath: Path, label: str) -> None:
    """Verify path exists, is a regular file, and is not a link/reparse point."""
    st = filepath.lstat()
    if stat.S_ISLNK(st.st_mode) or is_reparse_point(st):
        raise ValueError(f"Refusing to use {label} {filepath}: symlink/reparse point")
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f"Refusing to use {label} {filepath}: not a regular file")


def write_new_file_bytes(filepath: Path, data: bytes, mode: int = 0o600) -> None:
    """Create a new file exclusively and write bytes without following links."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(filepath, flags, mode)
    try:
        with os.fdopen(fd, "wb") as fh:
            fd = None
            fh.write(data)
    finally:
        if fd is not None:
            os.close(fd)


def write_temp_candidate(directory: Path, source_name: str, text: str) -> Path:
    """Write candidate output to a random same-directory temp file."""
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=directory,
        prefix=f".{source_name}.",
        suffix=".signaltrim.tmp",
        delete=False,
    ) as fh:
        fh.write(text)
        return Path(fh.name)


def normalized_identity(text: str) -> str:
    """Normalize newline style before checking for no-op model output."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def is_sensitive_path(filepath: Path) -> bool:
    """Heuristic denylist for files that must never be shipped to a third-party API."""
    name = filepath.name
    if SENSITIVE_BASENAME_REGEX.match(name):
        return True
    lowered_parts = {p.lower() for p in filepath.parts}
    if lowered_parts & SENSITIVE_PATH_COMPONENTS:
        return True
    normalized_dirs = [
        re.sub(r"[_\-\s.]", "", p.lower())
        for p in filepath.parts[:-1]
    ]
    if any(tok in part for part in normalized_dirs for tok in SENSITIVE_NAME_TOKENS):
        return True
    # Normalize separators so "api-key" and "api_key" both match "apikey".
    lower = re.sub(r"[_\-\s.]", "", name.lower())
    return any(tok in lower for tok in SENSITIVE_NAME_TOKENS)


def strip_llm_wrapper(text: str) -> str:
    """Strip outer ```markdown ... ``` fence when it wraps the entire output."""
    m = OUTER_FENCE_REGEX.match(text)
    if m:
        return m.group(2)
    return text

from .detect import should_compress
from .validate import validate

MAX_RETRIES = 2


# ---------- Claude Calls ----------


def call_claude(prompt: str) -> str:
    """Send a prompt to Claude.

    Prefers the Anthropic SDK when ANTHROPIC_API_KEY is set; otherwise falls
    back to the ``claude --print`` CLI (which handles desktop auth).

    On Windows the CLI subprocess decoding defaults to the system codepage
    (cp1251 / cp1252) and crashes on UTF-8 output — see issue #152. Pinning
    ``encoding="utf-8"`` with ``errors="replace"`` matches the CLI's actual
    native I/O and prevents the UnicodeDecodeError before validation can
    report. Windows users with non-ASCII content can also set
    ``ANTHROPIC_API_KEY`` to route through the SDK and skip the subprocess.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get("SIGNALTRIM_MODEL", "claude-sonnet-4-5"),
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return strip_llm_wrapper(msg.content[0].text.strip())
        except ImportError:
            pass  # anthropic not installed, fall back to CLI
    # Fallback: use claude CLI (handles desktop auth).
    # Resolve binary via shutil.which so Windows .cmd/.bat shims (e.g.
    # %APPDATA%\npm\claude.CMD) work without shell=True. On POSIX,
    # shutil.which returns the same absolute path as the implicit lookup,
    # so this is a no-op there. Falls back to bare "claude" if not found
    # on PATH so subprocess raises a clear FileNotFoundError.
    claude_bin = shutil.which("claude") or "claude"
    try:
        result = subprocess.run(
            [claude_bin, "--print"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return strip_llm_wrapper(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Claude call failed:\n{e.stderr}")


def build_compress_prompt(original: str) -> str:
    return f"""
Compress this markdown into signaltrim format.

STRICT RULES:
- Do NOT modify anything inside ``` code blocks
- Do NOT modify anything inside inline backticks
- Preserve ALL URLs exactly
- Preserve ALL headings exactly
- Preserve file paths and commands
- Return ONLY the compressed markdown body — do NOT wrap the entire output in a ```markdown fence or any other fence. Inner code blocks from the original stay as-is; do not add a new outer fence around the whole file.

Only compress natural language.

TEXT:
{original}
"""


def build_fix_prompt(original: str, compressed: str, errors: List[str]) -> str:
    errors_str = "\n".join(f"- {e}" for e in errors)
    return f"""You are fixing a signaltrim-compressed markdown file. Specific validation errors were found.

CRITICAL RULES:
- DO NOT recompress or rephrase the file
- ONLY fix the listed errors — leave everything else exactly as-is
- The ORIGINAL is provided as reference only (to restore missing content)
- Preserve signaltrim style in all untouched sections

ERRORS TO FIX:
{errors_str}

HOW TO FIX:
- Missing URL: find it in ORIGINAL, restore it exactly where it belongs in COMPRESSED
- Code block mismatch: find the exact code block in ORIGINAL, restore it in COMPRESSED
- Heading mismatch: restore the exact heading text from ORIGINAL into COMPRESSED
- Do not touch any section not mentioned in the errors

ORIGINAL (reference only):
{original}

COMPRESSED (fix this):
{compressed}

Return ONLY the fixed compressed file. No explanation.
"""


# ---------- Core Logic ----------


def compress_file(filepath: Path) -> bool:
    # Validate the user-supplied path before resolving it. A malicious project
    # can hide a symlink that points at private notes elsewhere; do not follow
    # links into a third-party API boundary.
    filepath = Path(filepath)
    assert_no_symlink_components(filepath)
    filepath = Path(os.path.abspath(filepath)).resolve(strict=True)
    assert_regular_nonsymlink(filepath, "source file")
    MAX_FILE_SIZE = 500_000  # 500KB
    if filepath.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large to compress safely (max 500KB): {filepath}")

    # Refuse files that look like they contain secrets or PII. Compressing ships
    # the raw bytes to the Anthropic API — a third-party boundary — so we fail
    # loudly rather than silently exfiltrate credentials or keys. Override is
    # intentional: the user must rename the file if the heuristic is wrong.
    if is_sensitive_path(filepath):
        raise ValueError(
            f"Refusing to compress {filepath}: filename looks sensitive "
            "(credentials, keys, secrets, or known private paths). "
            "Compression sends file contents to the Anthropic API. "
            "Rename the file if this is a false positive."
        )

    print(f"Processing: {filepath}")

    if not should_compress(filepath):
        print("Skipping (not natural language)")
        return False

    original_bytes = filepath.read_bytes()
    try:
        original_text = original_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Refusing to compress {filepath}: file is not valid UTF-8 text "
            f"({exc})."
        )
    original_mode = filepath.stat().st_mode & 0o777
    # Store backup outside the source directory so skill auto-loaders don't
    # re-ingest the `.original.md` copy as a live file. Mirror the source's
    # parent-dir name + a resolved-path hash under a platform-aware base to
    # reduce collisions.
    backup_dir = backup_dir_for(filepath)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_path_for(filepath)

    if not original_text.strip():
        print("ERROR: Refusing to compress: file is empty or whitespace-only.")
        return False

    # Check if backup already exists to prevent accidental overwriting
    if backup_path.exists():
        print(f"WARNING: Backup file already exists: {backup_path}")
        print("The original backup may contain important content.")
        print("Aborting to prevent data loss. Please remove or rename the backup file if you want to proceed.")
        return False

    # Split YAML frontmatter off before compression. Claude tends to strip or
    # rewrite frontmatter despite preserve-structure rules; we keep it verbatim
    # by removing it from the input and re-prepending it to the output.
    frontmatter, body = split_frontmatter(original_text)
    if frontmatter:
        print(f"Detected YAML frontmatter ({len(frontmatter)} chars) - preserving verbatim")

    if not body.strip():
        print("ERROR: Refusing to compress: body is empty after frontmatter removal.")
        return False

    # Step 1: Compress (body only, frontmatter excluded)
    print("Compressing with Claude...")
    compressed_body = call_claude(build_compress_prompt(body))

    if compressed_body is None or not compressed_body.strip():
        print("ERROR: Compression aborted: Claude returned an empty response.")
        print("   Original file is untouched (no backup created).")
        return False

    # Compare the BODY (not the whole file) — frontmatter is preserved verbatim
    # and would never change, so identity must be judged on the compressible part.
    if normalized_identity(compressed_body) == normalized_identity(body):
        print("ERROR: Compression aborted: output is identical to input.")
        print("   Likely causes: Claude refused, returned the prompt verbatim, or the file is")
        print("   already in signaltrim form. Original file is untouched (no backup created).")
        return False

    # Reassemble: frontmatter (verbatim) + compressed body
    compressed = frontmatter + compressed_body

    # Save original as backup, then verify the backup readback before
    # touching the input file. If the filesystem dropped bytes (encoding,
    # antivirus, disk full), unlink the bad backup and abort instead of
    # leaving the user with a corrupt backup + compressed primary.
    try:
        write_new_file_bytes(backup_path, original_bytes)
    except FileExistsError:
        print(f"WARNING: Backup file already exists: {backup_path}")
        print("The original backup may contain important content.")
        print("Aborting to prevent data loss. Please remove or rename the backup file if you want to proceed.")
        return False
    try:
        backup_path.chmod(0o600)
    except OSError:
        pass
    backup_readback = backup_path.read_bytes()
    if backup_readback != original_bytes:
        print(f"ERROR: Backup write verification failed: {backup_path}")
        print("   In-memory original bytes differ from on-disk backup. Aborting before touching the input file.")
        try:
            backup_path.unlink()
        except OSError:
            pass
        return False

    # Never write unvalidated model output to the live file. Validation and
    # retries happen against a same-directory candidate path; only a passing
    # candidate is atomically swapped into place. If the process dies mid-run,
    # the user's original file remains untouched.
    tmp_path = None
    try:
        tmp_path = write_temp_candidate(filepath.parent, filepath.name, compressed)

        # Step 2: Validate + Retry
        for attempt in range(MAX_RETRIES):
            print(f"\nValidation attempt {attempt + 1}")

            result = validate(backup_path, tmp_path)

            if result.is_valid:
                print("Validation passed")
                assert_regular_nonsymlink(filepath, "source file")
                assert_regular_nonsymlink(tmp_path, "candidate file")
                os.replace(tmp_path, filepath)
                try:
                    filepath.chmod(original_mode)
                except OSError:
                    pass
                return True

            print("ERROR: Validation failed:")
            for err in result.errors:
                print(f"   - {err}")

            if attempt == MAX_RETRIES - 1:
                backup_path.unlink(missing_ok=True)
                print("ERROR: Failed after retries - original left untouched")
                return False

            print("Fixing with Claude...")
            compressed = call_claude(
                build_fix_prompt(original_text, compressed, result.errors)
            )
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            tmp_path = write_temp_candidate(filepath.parent, filepath.name, compressed)
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    return False
