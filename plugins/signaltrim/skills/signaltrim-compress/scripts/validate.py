#!/usr/bin/env python3
import re
from collections import Counter
from pathlib import Path

URL_REGEX = re.compile(r"https?://[^\s)]+")
FENCE_OPEN_REGEX = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
BULLET_REGEX = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
TABLE_SEPARATOR_CELL_REGEX = re.compile(r"^:?-{3,}:?$")

# crude but effective path detection
# Requires either a path prefix (./ ../ / or drive letter) or a slash/backslash within the match
PATH_REGEX = re.compile(r"(?:\./|\.\./|/|[A-Za-z]:\\)[\w\-/\\\.]+|[\w\-\.]+[/\\][\w\-/\\\.]+")


class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []

    def add_error(self, msg):
        self.is_valid = False
        self.errors.append(msg)

    def add_warning(self, msg):
        self.warnings.append(msg)


def read_file(path: Path) -> str:
    return path.read_text(errors="ignore")


# ---------- Extractors ----------


def extract_headings(text):
    return [(level, title.strip()) for level, title in HEADING_REGEX.findall(text)]


def extract_code_blocks(text):
    """Line-based fenced code block extractor.

    Handles ``` and ~~~ fences with variable length (CommonMark: closing
    fence must use same char and be at least as long as opening). Supports
    nested fences (e.g. an outer 4-backtick block wrapping inner 3-backtick
    content).
    """
    blocks = []
    lines = text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        m = FENCE_OPEN_REGEX.match(lines[i])
        if not m:
            i += 1
            continue
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        open_line = lines[i]
        block_lines = [open_line]
        i += 1
        closed = False
        while i < n:
            close_m = FENCE_OPEN_REGEX.match(lines[i])
            if (
                close_m
                and close_m.group(2)[0] == fence_char
                and len(close_m.group(2)) >= fence_len
                and close_m.group(3).strip() == ""
            ):
                block_lines.append(lines[i])
                closed = True
                i += 1
                break
            block_lines.append(lines[i])
            i += 1
        if closed:
            blocks.append("\n".join(block_lines))
        # Unclosed fences are silently skipped — they indicate malformed markdown
        # and including them would cause false-positive validation failures.
    return blocks


def strip_fenced_code_blocks(text):
    """Remove fenced code blocks before validating prose-only structures."""
    out = []
    lines = text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        m = FENCE_OPEN_REGEX.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        i += 1
        while i < n:
            close_m = FENCE_OPEN_REGEX.match(lines[i])
            if (
                close_m
                and close_m.group(2)[0] == fence_char
                and len(close_m.group(2)) >= fence_len
                and close_m.group(3).strip() == ""
            ):
                i += 1
                break
            i += 1
    return "\n".join(out)


def extract_urls(text):
    return set(URL_REGEX.findall(text))


def extract_paths(text):
    return set(PATH_REGEX.findall(text))


def count_bullets(text):
    return len(BULLET_REGEX.findall(text))


def split_table_row(line):
    stripped = line.strip()
    if "|" not in stripped:
        return []
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip() for cell in stripped.split("|")]
    return cells if len(cells) >= 2 else []


def is_table_separator(line):
    cells = split_table_row(line)
    return bool(cells) and all(TABLE_SEPARATOR_CELL_REGEX.match(cell or "") for cell in cells)


def extract_table_shapes(text):
    """Return Markdown table row/column shapes outside fenced code blocks.

    We intentionally validate shape instead of cell text: compression may
    shorten prose inside cells, but it must not drop rows, columns, or the
    header/separator structure.
    """
    lines = strip_fenced_code_blocks(text).splitlines()
    shapes = []
    i = 0
    while i < len(lines) - 1:
        header = split_table_row(lines[i])
        separator = split_table_row(lines[i + 1])
        if not header or not separator or not is_table_separator(lines[i + 1]):
            i += 1
            continue
        if len(header) != len(separator):
            i += 1
            continue

        column_counts = [len(header), len(separator)]
        i += 2
        while i < len(lines):
            row = split_table_row(lines[i])
            if not row:
                break
            column_counts.append(len(row))
            i += 1
        shapes.append(tuple(column_counts))
    return shapes


def extract_inline_codes(text):
    text_without_fences = re.sub(r"^```[\s\S]*?^```", "", text, flags=re.MULTILINE)
    text_without_fences = re.sub(r"^~~~[\s\S]*?^~~~", "", text_without_fences, flags=re.MULTILINE)
    return re.findall(r"`([^`]+)`", text_without_fences)


# ---------- Validators ----------


def validate_headings(orig, comp, result):
    h1 = extract_headings(orig)
    h2 = extract_headings(comp)

    if len(h1) != len(h2):
        result.add_error(f"Heading count mismatch: {len(h1)} vs {len(h2)}")

    if h1 != h2:
        result.add_error("Heading text/order changed")


def validate_code_blocks(orig, comp, result):
    c1 = extract_code_blocks(orig)
    c2 = extract_code_blocks(comp)

    if c1 != c2:
        result.add_error("Code blocks not preserved exactly")


def validate_urls(orig, comp, result):
    u1 = extract_urls(orig)
    u2 = extract_urls(comp)

    if u1 != u2:
        result.add_error(f"URL mismatch: lost={u1 - u2}, added={u2 - u1}")


def validate_paths(orig, comp, result):
    p1 = extract_paths(orig)
    p2 = extract_paths(comp)

    if p1 != p2:
        result.add_error(f"Path mismatch: lost={p1 - p2}, added={p2 - p1}")


def validate_bullets(orig, comp, result):
    b1 = count_bullets(orig)
    b2 = count_bullets(comp)

    if b1 == 0:
        return

    if b2 < b1 and (b1 - b2) / b1 > 0.15:
        result.add_error(f"Bullet count dropped too much: {b1} -> {b2}")
    elif b2 > b1 and (b2 - b1) / b1 > 0.15:
        result.add_warning(f"Bullet count expanded significantly: {b1} -> {b2}")


def validate_tables(orig, comp, result):
    t1 = extract_table_shapes(orig)
    t2 = extract_table_shapes(comp)

    if t1 != t2:
        result.add_error(f"Table structure changed: {t1} -> {t2}")


def validate_inline_codes(orig, comp, result):
    c1 = Counter(extract_inline_codes(orig))
    c2 = Counter(extract_inline_codes(comp))

    if c1 != c2:
        lost = set(c1.keys()) - set(c2.keys())
        added = set(c2.keys()) - set(c1.keys())
        for code, count in c1.items():
            if code in c2 and c2[code] < count:
                lost.add(f"{code} (lost {count - c2[code]} of {count} occurrences)")
        if lost:
            result.add_error(f"Inline code lost: {lost}")
        if added:
            result.add_warning(f"Inline code added: {added}")


# ---------- Main ----------


def validate(original_path: Path, compressed_path: Path) -> ValidationResult:
    result = ValidationResult()

    orig = read_file(original_path)
    comp = read_file(compressed_path)

    validate_headings(orig, comp, result)
    validate_code_blocks(orig, comp, result)
    validate_urls(orig, comp, result)
    validate_paths(orig, comp, result)
    validate_bullets(orig, comp, result)
    validate_tables(orig, comp, result)
    validate_inline_codes(orig, comp, result)

    return result


# ---------- CLI ----------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python validate.py <original> <compressed>")
        sys.exit(1)

    orig = Path(sys.argv[1]).resolve()
    comp = Path(sys.argv[2]).resolve()

    res = validate(orig, comp)

    print(f"\nValid: {res.is_valid}")

    if res.errors:
        print("\nErrors:")
        for e in res.errors:
            print(f"  - {e}")

    if res.warnings:
        print("\nWarnings:")
        for w in res.warnings:
            print(f"  - {w}")
