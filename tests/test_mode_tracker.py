"""Tests for signaltrim-mode-tracker.js prompt parsing (issues #598, #599).

Drives the UserPromptSubmit hook with real prompts over stdin against an
isolated CLAUDE_CONFIG_DIR and asserts the flag-file state afterwards.

#598: natural-language triggers misfired — "turn signaltrim mode off"
ACTIVATED signaltrim (and clobbered the level to default), "turn signaltrim off"
was a no-op, questions about signaltrim armed it, and vim's "normal mode"
deactivated it.

#599: one-shot independent modes (/signaltrim-commit etc.) permanently
overwrote the active prose level, and the plugin-namespaced
/signaltrim:signaltrim-commit|-review variants were not recognized at all.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKER = REPO_ROOT / "src" / "hooks" / "signaltrim-mode-tracker.js"


class ModeTrackerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="signaltrim-tracker-")
        self.claude_dir = Path(self._tmp.name) / ".claude"
        self.claude_dir.mkdir(parents=True)
        self.flag = self.claude_dir / ".signaltrim-active"
        self.prev = self.claude_dir / ".signaltrim-active.prev"

    def tearDown(self):
        self._tmp.cleanup()

    def send(self, prompt):
        env = os.environ.copy()
        env.pop("SIGNALTRIM_DEFAULT_MODE", None)
        env["HOME"] = self._tmp.name
        env["USERPROFILE"] = self._tmp.name
        env["CLAUDE_CONFIG_DIR"] = str(self.claude_dir)
        return subprocess.run(
            ["node", str(TRACKER)],
            cwd=REPO_ROOT,
            env=env,
            input=json.dumps({"prompt": prompt}),
            text=True,
            capture_output=True,
            check=True,
        )

    def flag_value(self):
        return self.flag.read_text() if self.flag.exists() else None

    # ── #598: deactivation word orders ──────────────────────────────────

    def test_turn_signaltrim_mode_off_deactivates(self):
        # Pre-fix: this ACTIVATED signaltrim and downgraded ultra -> full.
        self.flag.write_text("ultra")
        self.send("turn signaltrim mode off")
        self.assertIsNone(self.flag_value())

    def test_turn_signaltrim_off_deactivates(self):
        self.flag.write_text("full")
        self.send("turn signaltrim off")
        self.assertIsNone(self.flag_value())

    def test_turn_off_signaltrim_deactivates(self):
        self.flag.write_text("full")
        self.send("turn off signaltrim")
        self.assertIsNone(self.flag_value())

    def test_stop_signaltrim_multiline_deactivates(self):
        # Pre-fix: `.*` without the s flag never matched across lines.
        self.flag.write_text("ultra")
        self.send("stop\nsignaltrim")
        self.assertIsNone(self.flag_value())

    def test_normal_mode_command_deactivates(self):
        self.flag.write_text("full")
        self.send("normal mode")
        self.assertIsNone(self.flag_value())

    def test_back_to_normal_mode_deactivates(self):
        self.flag.write_text("full")
        self.send("back to normal mode please")
        self.assertIsNone(self.flag_value())

    def test_vim_normal_mode_does_not_deactivate(self):
        self.flag.write_text("full")
        self.send("how do I exit vim normal mode")
        self.assertEqual(self.flag_value(), "full")

    # ── #598: activation guards ─────────────────────────────────────────

    def test_enable_signaltrim_with_stop_elsewhere_activates(self):
        # Pre-fix: "stop" anywhere suppressed activation, then the
        # deactivation regex matched "signaltrim and stop" and deleted the flag.
        self.flag.write_text("full")
        self.send("enable signaltrim and stop apologizing")
        self.assertEqual(self.flag_value(), "full")

    def test_question_does_not_activate(self):
        self.send("what is signaltrim mode?")
        self.assertIsNone(self.flag_value())
        self.send("does signaltrim lite mode drop articles?")
        self.assertIsNone(self.flag_value())

    def test_scoped_brevity_does_not_activate(self):
        self.send("be brief in the summary section")
        self.assertIsNone(self.flag_value())

    def test_unscoped_brevity_activates(self):
        self.send("be brief")
        self.assertEqual(self.flag_value(), "full")

    def test_activate_signaltrim_still_works(self):
        self.send("activate signaltrim")
        self.assertEqual(self.flag_value(), "full")

    def test_turn_on_signaltrim_mode_still_works(self):
        self.send("turn on signaltrim mode")
        self.assertEqual(self.flag_value(), "full")

    def test_use_signaltrim_mode_still_works(self):
        self.send("use SignalTrim mode")
        self.assertEqual(self.flag_value(), "full")

    def test_bare_signaltrim_mode_still_works(self):
        self.send("signaltrim mode")
        self.assertEqual(self.flag_value(), "full")

    # ── slash commands ──────────────────────────────────────────────────

    def test_slash_signaltrim_level_switch(self):
        self.send("/signaltrim ultra")
        self.assertEqual(self.flag_value(), "ultra")

    def test_slash_signaltrim_off(self):
        self.flag.write_text("full")
        self.send("/signaltrim off")
        self.assertIsNone(self.flag_value())

    # ── #599: one-shot independent modes ────────────────────────────────

    def test_commit_restores_prior_level_on_next_prompt(self):
        self.flag.write_text("ultra")
        self.send("/signaltrim-commit")
        self.assertEqual(self.flag_value(), "commit")
        r = self.send("ordinary follow-up question")
        self.assertEqual(self.flag_value(), "ultra")
        self.assertIn("SIGNALTRIM MODE ACTIVE (ultra)", r.stdout)

    def test_commit_with_no_prior_mode_deactivates_after(self):
        self.send("/signaltrim-commit")
        self.assertEqual(self.flag_value(), "commit")
        r = self.send("ordinary follow-up question")
        self.assertIsNone(self.flag_value())
        self.assertNotIn("SIGNALTRIM MODE ACTIVE", r.stdout)

    def test_chained_independent_modes_keep_original_prev(self):
        self.flag.write_text("wenyan-ultra")
        self.send("/signaltrim-commit")
        self.send("/signaltrim-review")
        self.assertEqual(self.flag_value(), "review")
        self.send("ordinary follow-up question")
        self.assertEqual(self.flag_value(), "wenyan-ultra")

    def test_namespaced_commit_and_review_recognized(self):
        # Pre-fix: only compress and stats had the /signaltrim:signaltrim- variant.
        self.flag.write_text("full")
        self.send("/signaltrim:signaltrim-commit")
        self.assertEqual(self.flag_value(), "commit")
        self.send("next prompt")  # restore
        self.send("/signaltrim:signaltrim-review")
        self.assertEqual(self.flag_value(), "review")

    def test_no_reinforcement_during_independent_turn(self):
        self.flag.write_text("full")
        r = self.send("/signaltrim-commit")
        self.assertNotIn("SIGNALTRIM MODE ACTIVE", r.stdout)

    def test_deactivation_clears_saved_prev(self):
        self.flag.write_text("ultra")
        self.send("/signaltrim-commit")
        self.send("stop signaltrim")
        self.assertIsNone(self.flag_value())
        self.assertFalse(self.prev.exists(), "prev file must not survive deactivation")
        self.send("ordinary prompt")
        self.assertIsNone(self.flag_value(), "nothing should resurrect the mode")


if __name__ == "__main__":
    unittest.main()
