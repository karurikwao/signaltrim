"""Tests for the data-loss guards in `compress_file` (issue #237).

The compress orchestrator used to overwrite the input even when Claude
returned an empty string or a no-op echo, and used to write a backup
without verifying that the bytes survived the round-trip. These tests
pin the new defensive checks: nothing on disk changes when the compressed
output is empty or identical to the input, and a backup-write that drops
bytes is detected before the input is overwritten.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "signaltrim-compress"))

from scripts import compress as compress_mod  # noqa: E402
from scripts import cli as cli_mod  # noqa: E402


class CompressSafetyTests(unittest.TestCase):
    def _file_with(self, dirpath: Path, text: str) -> Path:
        path = dirpath / "task.md"
        path.write_text(text)
        return path

    def test_empty_input_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._file_with(Path(tmp), "")
            with mock.patch.object(compress_mod, "call_claude") as call:
                ok = compress_mod.compress_file(path)
            self.assertFalse(ok)
            call.assert_not_called()
            self.assertEqual(path.read_text(), "")
            self.assertFalse((Path(tmp) / "task.original.md").exists())

    def test_empty_compressed_output_does_not_touch_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = "# Heading\n\nSome long natural language paragraph that should be compressed.\n"
            path = self._file_with(Path(tmp), original)
            with mock.patch.object(compress_mod, "call_claude", return_value=""):
                ok = compress_mod.compress_file(path)
            self.assertFalse(ok)
            self.assertEqual(path.read_text(), original)
            self.assertFalse((Path(tmp) / "task.original.md").exists())

    def test_whitespace_only_compressed_output_does_not_touch_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = "# Heading\n\nProse that should change.\n"
            path = self._file_with(Path(tmp), original)
            with mock.patch.object(compress_mod, "call_claude", return_value="   \n  "):
                ok = compress_mod.compress_file(path)
            self.assertFalse(ok)
            self.assertEqual(path.read_text(), original)
            self.assertFalse((Path(tmp) / "task.original.md").exists())

    def test_identical_compressed_output_does_not_touch_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = "# Heading\n\nProse.\n"
            path = self._file_with(Path(tmp), original)
            with mock.patch.object(compress_mod, "call_claude", return_value=original):
                ok = compress_mod.compress_file(path)
            self.assertFalse(ok)
            self.assertEqual(path.read_text(), original)
            self.assertFalse((Path(tmp) / "task.original.md").exists())

    def test_lf_only_echo_of_crlf_input_is_treated_as_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = "# Heading\r\n\r\nProse.\r\n"
            path = Path(tmp) / "task.md"
            path.write_bytes(original.encode("utf-8"))
            with mock.patch.object(compress_mod, "call_claude", return_value=original.replace("\r\n", "\n")):
                ok = compress_mod.compress_file(path)
            self.assertFalse(ok)
            self.assertEqual(path.read_bytes(), original.encode("utf-8"))

    def test_invalid_utf8_refused_before_api_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.md"
            path.write_bytes(b"# Heading\n\nValid then invalid: \xff\n")
            with mock.patch.object(compress_mod, "call_claude") as call:
                with self.assertRaises(ValueError):
                    compress_mod.compress_file(path)
            call.assert_not_called()

    def test_symlink_source_refused_before_api_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "private.md"
            target.write_text("# Heading\n\nPrivate notes.\n")
            link = Path(tmp) / "task.md"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable on this platform")
            with mock.patch.object(compress_mod, "call_claude") as call:
                with self.assertRaises(ValueError):
                    compress_mod.compress_file(link)
            call.assert_not_called()
            self.assertEqual(target.read_text(), "# Heading\n\nPrivate notes.\n")

    def test_cli_refuses_symlink_before_resolving_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "private.md"
            target.write_text("# Heading\n\nPrivate notes.\n")
            link = Path(tmp) / "task.md"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable on this platform")

            with mock.patch.object(sys, "argv", ["signaltrim", str(link)]), \
                 mock.patch.object(cli_mod, "compress_file") as call, \
                 self.assertRaises(SystemExit) as raised:
                cli_mod.main()

            self.assertEqual(raised.exception.code, 1)
            call.assert_not_called()
            self.assertEqual(target.read_text(), "# Heading\n\nPrivate notes.\n")

    def test_real_compression_writes_backup_and_target(self):
        # Isolate the backup data dir to a temp location so the out-of-tree
        # backup (issue #420) never lands in the developer's real home dir.
        with tempfile.TemporaryDirectory() as tmp, \
             tempfile.TemporaryDirectory() as data_home, \
             mock.patch.dict(os.environ, {"XDG_DATA_HOME": data_home, "LOCALAPPDATA": data_home}):
            original = "# Heading\n\nThe quick brown fox jumps over the lazy dog.\n"
            compressed = "# Heading\n\nFox jump dog.\n"
            path = self._file_with(Path(tmp), original)
            with mock.patch.object(compress_mod, "call_claude", return_value=compressed), \
                 mock.patch.object(compress_mod, "validate") as v:
                v.return_value = mock.Mock(is_valid=True, errors=[], warnings=[])
                ok = compress_mod.compress_file(path)
            self.assertTrue(ok)
            self.assertEqual(path.read_text(), compressed)
            # Backups now live OUTSIDE the source dir (issue #420), under a
            # platform-aware data dir mirroring the source parent name.
            backup = compress_mod.backup_path_for(path.resolve())
            self.assertEqual(backup.read_text(), original)
            self.assertFalse((Path(tmp) / "task.original.md").exists())

    def test_validation_retry_keeps_live_file_untouched_until_success(self):
        with tempfile.TemporaryDirectory() as tmp, \
             tempfile.TemporaryDirectory() as data_home, \
             mock.patch.dict(os.environ, {"XDG_DATA_HOME": data_home, "LOCALAPPDATA": data_home}):
            original = "# Heading\n\nThe quick brown fox jumps over the lazy dog.\n"
            compressed = "# Heading\n\nBad summary.\n"
            fixed = "# Heading\n\nFox jump dog.\n"
            path = self._file_with(Path(tmp), original)
            candidates = []

            def validate_candidate(_backup, candidate):
                candidates.append(Path(candidate))
                self.assertEqual(path.read_text(), original)
                self.assertNotEqual(Path(candidate), path.resolve())
                if len(candidates) == 1:
                    return mock.Mock(is_valid=False, errors=["summary output"], warnings=[])
                return mock.Mock(is_valid=True, errors=[], warnings=[])

            with mock.patch.object(compress_mod, "call_claude", side_effect=[compressed, fixed]), \
                 mock.patch.object(compress_mod, "validate", side_effect=validate_candidate):
                ok = compress_mod.compress_file(path)

            self.assertTrue(ok)
            self.assertEqual(path.read_text(), fixed)
            self.assertGreaterEqual(len(candidates), 2)
            for candidate in candidates:
                self.assertFalse(candidate.exists(), f"temp candidate left behind: {candidate}")

    def test_validation_failure_leaves_live_file_untouched_and_removes_backup(self):
        with tempfile.TemporaryDirectory() as tmp, \
             tempfile.TemporaryDirectory() as data_home, \
             mock.patch.dict(os.environ, {"XDG_DATA_HOME": data_home, "LOCALAPPDATA": data_home}):
            original = "# Heading\n\nThe quick brown fox jumps over the lazy dog.\n"
            path = self._file_with(Path(tmp), original)
            invalid = mock.Mock(is_valid=False, errors=["still invalid"], warnings=[])

            with mock.patch.object(compress_mod, "call_claude", side_effect=["Bad.", "Still bad."]), \
                 mock.patch.object(compress_mod, "validate", return_value=invalid):
                ok = compress_mod.compress_file(path)

            self.assertFalse(ok)
            self.assertEqual(path.read_text(), original)
            backup = compress_mod.backup_path_for(path.resolve())
            self.assertFalse(backup.exists())
            self.assertEqual(list(Path(tmp).glob("*.signaltrim.tmp")), [])

    def test_sensitive_directory_refused_before_api_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            sensitive_dir = Path(tmp) / "secrets"
            sensitive_dir.mkdir()
            path = self._file_with(sensitive_dir, "# Heading\n\nPrivate deployment notes.\n")
            with mock.patch.object(compress_mod, "call_claude") as call:
                with self.assertRaises(ValueError):
                    compress_mod.compress_file(path)
            call.assert_not_called()

    def test_backup_path_includes_parent_hash_to_avoid_cross_project_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "project-a" / "docs"
            b = Path(tmp) / "project-b" / "docs"
            a.mkdir(parents=True)
            b.mkdir(parents=True)
            path_a = self._file_with(a, "# Heading\n\nNotes.\n")
            path_b = self._file_with(b, "# Heading\n\nNotes.\n")

            self.assertNotEqual(
                compress_mod.backup_path_for(path_a),
                compress_mod.backup_path_for(path_b),
            )

    def test_backup_path_keeps_non_markdown_suffix_to_avoid_same_dir_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = self._file_with(Path(tmp), "# Heading\n\nMarkdown notes.\n")
            txt = Path(tmp) / "task.txt"
            txt.write_text("Plain text notes.\n")

            self.assertNotEqual(
                compress_mod.backup_path_for(md),
                compress_mod.backup_path_for(txt),
            )


if __name__ == "__main__":
    unittest.main()
