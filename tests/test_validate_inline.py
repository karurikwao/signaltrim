import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "signaltrim-compress"))

from scripts.validate import (  # noqa: E402
    ValidationResult,
    extract_inline_codes,
    extract_table_shapes,
    validate,
    validate_inline_codes,
)


class TestExtractInlineCodes(unittest.TestCase):
    def test_fenced_blocks_excluded(self):
        text = "```\ncode here\n```\n`inline code`"
        result = extract_inline_codes(text)
        self.assertEqual(result, ["inline code"])

    def test_inline_only(self):
        text = "Use `rm -rf /` to delete everything"
        result = extract_inline_codes(text)
        self.assertEqual(result, ["rm -rf /"])

    def test_mixed_content(self):
        text = """
Some text with `inline1` and `inline2`.

```
code block
```

More text with `inline3`.
"""
        result = extract_inline_codes(text)
        self.assertEqual(set(result), {"inline1", "inline2", "inline3"})

    def test_empty(self):
        self.assertEqual(extract_inline_codes("no backticks here"), [])


class TestValidateInlineCodes(unittest.TestCase):
    def test_match(self):
        result = ValidationResult()
        validate_inline_codes("use `cmd` here", "use `cmd` here", result)
        self.assertTrue(result.is_valid)

    def test_lost(self):
        result = ValidationResult()
        validate_inline_codes("use `cmd` here", "use  here", result)
        self.assertFalse(result.is_valid)
        self.assertIn("Inline code lost", result.errors[0])

    def test_added(self):
        result = ValidationResult()
        validate_inline_codes("use  here", "use `new` here", result)
        self.assertTrue(result.is_valid)
        self.assertIn("Inline code added", result.warnings[0])

    def test_empty_orig(self):
        result = ValidationResult()
        validate_inline_codes("no codes", "use `new` here", result)
        self.assertTrue(result.is_valid)

    def test_both_empty(self):
        result = ValidationResult()
        validate_inline_codes("plain text", "also plain", result)
        self.assertTrue(result.is_valid)


class TestValidateIntegration(unittest.TestCase):
    def test_validate_inline_codes_wired(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / "original.md"
            comp = Path(tmp) / "compressed.md"
            orig.write_text("Run `rm -rf /` to delete")
            comp.write_text("Run  to delete")
            result = validate(orig, comp)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Inline code lost" in e for e in result.errors))

    def test_heading_text_change_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / "original.md"
            comp = Path(tmp) / "compressed.md"
            orig.write_text("# Deployment Checklist\n\nRun tests.\n")
            comp.write_text("# Deploy List\n\nRun tests.\n")
            result = validate(orig, comp)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Heading text/order changed" in e for e in result.errors))

    def test_path_loss_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / "original.md"
            comp = Path(tmp) / "compressed.md"
            orig.write_text("Edit src/hooks/signaltrim-activate.js before release.\n")
            comp.write_text("Edit hook before release.\n")
            result = validate(orig, comp)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Path mismatch" in e for e in result.errors))

    def test_major_bullet_loss_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / "original.md"
            comp = Path(tmp) / "compressed.md"
            orig.write_text("- One\n- Two\n- Three\n- Four\n")
            comp.write_text("- One\n")
            result = validate(orig, comp)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Bullet count dropped too much" in e for e in result.errors))

    def test_table_structure_loss_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / "original.md"
            comp = Path(tmp) / "compressed.md"
            orig.write_text("| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |\n")
            comp.write_text("| A | B |\n| --- | --- |\n| 1 | 2 |\n")
            result = validate(orig, comp)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Table structure changed" in e for e in result.errors))

    def test_table_extractor_ignores_fenced_tables(self):
        text = "```\n| A | B |\n| --- | --- |\n| 1 | 2 |\n```\n\n| C | D |\n| --- | --- |\n| 3 | 4 |\n"
        self.assertEqual(extract_table_shapes(text), [(2, 2, 2)])


if __name__ == "__main__":
    unittest.main()
