import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def find_usable_bash():
    candidates = ["bash"]
    if os.name == "nt":
        candidates.extend(
            [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files\Git\usr\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]
        )
    for candidate in candidates:
        try:
            subprocess.run(
                [candidate, "-lc", "pwd >/dev/null"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
                timeout=5,
            )
            return candidate
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    return None


def find_usable_powershell():
    candidates = ["pwsh", "powershell"]
    if os.name == "nt":
        candidates.extend(
            [
                r"C:\Program Files\PowerShell\7\pwsh.exe",
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            ]
        )
    for candidate in candidates:
        try:
            subprocess.run(
                [candidate, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString() | Out-Null"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
                timeout=5,
            )
            return candidate
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    return None


class HookScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bash_cmd = find_usable_bash()
        cls._powershell_cmd = find_usable_powershell()

    def require_bash(self):
        if not self._bash_cmd:
            self.skipTest("bash cannot execute inside this repo")

    def require_powershell(self):
        if not self._powershell_cmd:
            self.skipTest("PowerShell cannot execute inside this repo")

    def run_cmd(self, cmd, home, extra_env=None):
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_install_upgrades_old_two_file_install(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-upgrade-") as tmp:
            home = Path(tmp)
            hooks_dir = home / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True)
            (home / ".claude" / "settings.json").write_text("{}\n")
            (hooks_dir / "signaltrim-activate.js").write_text("")
            (hooks_dir / "signaltrim-mode-tracker.js").write_text("")

            self.run_cmd([self._bash_cmd, "src/hooks/install.sh"], home)

            statusline = hooks_dir / "signaltrim-statusline.sh"
            self.assertTrue(statusline.exists(), "upgrade should install statusline script")

            settings = json.loads((home / ".claude" / "settings.json").read_text())
            self.assertIn("statusLine", settings)
            self.assertIn(statusline.as_posix(), settings["statusLine"]["command"])

    def test_install_reconfigures_missing_statusline(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-statusline-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            hooks_dir = claude_dir / "hooks"
            hooks_dir.mkdir(parents=True)

            for name in ("signaltrim-activate.js", "signaltrim-mode-tracker.js", "signaltrim-statusline.sh"):
                (hooks_dir / name).write_text("")

            settings = {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-activate.js"}"',
                                }
                            ]
                        }
                    ],
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-mode-tracker.js"}"',
                                }
                            ]
                        }
                    ],
                }
            }
            (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")

            result = self.run_cmd([self._bash_cmd, "src/hooks/install.sh"], home)

            self.assertNotIn("Nothing to do", result.stdout)

            updated = json.loads((claude_dir / "settings.json").read_text())
            self.assertIn("statusLine", updated)
            self.assertIn((hooks_dir / "signaltrim-statusline.sh").as_posix(), updated["statusLine"]["command"])

    def test_install_accepts_jsonc_settings(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-jsonc-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "settings.json").write_text(
                """{
  // Claude settings often keep comments during manual edits.
  "hooks": {
    "Notification": [
      {
        "hooks": [
          { "type": "command", "command": "echo keep-me", },
        ],
      },
    ],
  },
}
"""
            )

            self.run_cmd([self._bash_cmd, "src/hooks/install.sh"], home)

            updated = json.loads((claude_dir / "settings.json").read_text())
            self.assertIn("Notification", updated["hooks"])
            self.assertIn("SessionStart", updated["hooks"])
            self.assertIn("UserPromptSubmit", updated["hooks"])
            self.assertIn("statusLine", updated)

    def test_install_preserves_user_signaltrim_named_hook(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-preserve-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            user_hook = Path(tmp) / "user-signaltrim-helper.js"
            user_hook.write_text("")
            settings = {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{user_hook}"',
                                }
                            ]
                        }
                    ]
                }
            }
            (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")

            self.run_cmd([self._bash_cmd, "src/hooks/install.sh"], home)

            updated = json.loads((claude_dir / "settings.json").read_text())
            commands = [
                hook["command"]
                for entry in updated["hooks"]["SessionStart"]
                for hook in entry.get("hooks", [])
            ]
            self.assertTrue(any("user-signaltrim-helper.js" in cmd for cmd in commands))
            self.assertTrue(any("signaltrim-activate.js" in cmd for cmd in commands))

    def test_uninstall_preserves_custom_statusline(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-uninstall-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            hooks_dir = claude_dir / "hooks"
            hooks_dir.mkdir(parents=True)

            for name in ("signaltrim-activate.js", "signaltrim-mode-tracker.js", "signaltrim-statusline.sh"):
                (hooks_dir / name).write_text("")

            settings = {
                "statusLine": {
                    "type": "command",
                    "command": "bash /tmp/custom-status-with-signaltrim.sh",
                },
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-activate.js"}"',
                                }
                            ]
                        }
                    ],
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-mode-tracker.js"}"',
                                }
                            ]
                        }
                    ],
                },
            }
            (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")

            self.run_cmd([self._bash_cmd, "src/hooks/uninstall.sh"], home)

            updated = json.loads((claude_dir / "settings.json").read_text())
            self.assertEqual(
                updated["statusLine"]["command"],
                "bash /tmp/custom-status-with-signaltrim.sh",
            )
            self.assertNotIn("hooks", updated)

    def test_uninstall_preserves_user_signaltrim_named_hook(self):
        self.require_bash()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-uninstall-preserve-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            hooks_dir = claude_dir / "hooks"
            hooks_dir.mkdir(parents=True)

            for name in ("signaltrim-activate.js", "signaltrim-mode-tracker.js", "signaltrim-statusline.sh"):
                (hooks_dir / name).write_text("")

            user_hook = Path(tmp) / "user-signaltrim-helper.js"
            user_hook.write_text("")
            settings = {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-activate.js"}"',
                                },
                                {
                                    "type": "command",
                                    "command": f'node "{user_hook}"',
                                },
                            ]
                        }
                    ],
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'node "{hooks_dir / "signaltrim-mode-tracker.js"}"',
                                }
                            ]
                        }
                    ],
                },
            }
            (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")

            self.run_cmd([self._bash_cmd, "src/hooks/uninstall.sh"], home)

            updated = json.loads((claude_dir / "settings.json").read_text())
            commands = [
                hook["command"]
                for entry in updated["hooks"]["SessionStart"]
                for hook in entry.get("hooks", [])
            ]
            self.assertEqual(len(commands), 1)
            self.assertIn("user-signaltrim-helper.js", commands[0])
            self.assertNotIn("UserPromptSubmit", updated.get("hooks", {}))

    def test_powershell_install_uninstall_accepts_jsonc_and_preserves_user_signaltrim_hook(self):
        self.require_powershell()
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-ps-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            user_hook = Path(tmp) / "user-signaltrim-helper.js"
            user_hook.write_text("")
            command_json = json.dumps(f"node {user_hook}")
            (claude_dir / "settings.json").write_text(
                f"""{{
  // User-authored hook should survive install and uninstall.
  "hooks": {{
    "SessionStart": [
      {{
        "hooks": [
          {{ "type": "command", "command": {command_json}, }},
        ],
      }},
    ],
  }},
}}
"""
            )

            ps_cmd = [
                self._powershell_cmd,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
            ]
            env = {"CLAUDE_CONFIG_DIR": str(claude_dir)}
            self.run_cmd(ps_cmd + ["src/hooks/install.ps1"], home, env)

            installed = json.loads((claude_dir / "settings.json").read_text())
            install_commands = [
                hook["command"]
                for entry in installed["hooks"]["SessionStart"]
                for hook in entry.get("hooks", [])
            ]
            self.assertTrue(any("user-signaltrim-helper.js" in cmd for cmd in install_commands))
            self.assertTrue(any("signaltrim-activate.js" in cmd for cmd in install_commands))

            self.run_cmd(ps_cmd + ["src/hooks/uninstall.ps1"], home, env)

            uninstalled = json.loads((claude_dir / "settings.json").read_text())
            remaining_commands = [
                hook["command"]
                for entry in uninstalled["hooks"]["SessionStart"]
                for hook in entry.get("hooks", [])
            ]
            self.assertEqual(remaining_commands, [f"node {user_hook}"])
            self.assertNotIn("UserPromptSubmit", uninstalled.get("hooks", {}))

    def test_activate_does_not_nudge_when_custom_statusline_exists(self):
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-activate-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "statusLine": {
                            "type": "command",
                            "command": "bash /tmp/my-statusline.sh",
                        }
                    }
                )
                + "\n"
            )

            result = self.run_cmd(["node", "src/hooks/signaltrim-activate.js"], home)

            self.assertNotIn("STATUSLINE SETUP NEEDED", result.stdout)
            self.assertEqual((claude_dir / ".signaltrim-active").read_text(), "full")

    # Regression for #587/#589 — hook at <root>/src/hooks/ must resolve SKILL.md
    # at <root>/skills/signaltrim/, not the nonexistent <root>/src/skills/.
    def test_activate_emits_skill_md_not_fallback_from_repo_layout(self):
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-skillpath-") as tmp:
            home = Path(tmp)
            (home / ".claude").mkdir(parents=True)

            result = self.run_cmd(["node", "src/hooks/signaltrim-activate.js"], home)

            # Intensity table exists only in SKILL.md, never in the fallback
            self.assertIn("## Intensity", result.stdout)
            # Default mode is full — table filtered to the active level's row
            self.assertIn("| **full** |", result.stdout)
            self.assertNotIn("| **lite** |", result.stdout)

    def test_activate_finds_skill_beside_config_dir_hooks(self):
        # Standalone layout: hooks at $CLAUDE_CONFIG_DIR/hooks/, skill installed
        # at $CLAUDE_CONFIG_DIR/skills/signaltrim/SKILL.md
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-standalone-") as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            hooks_dir = claude_dir / "hooks"
            hooks_dir.mkdir(parents=True)
            for name in ("signaltrim-activate.js", "signaltrim-config.js", "package.json"):
                shutil.copy(REPO_ROOT / "src" / "hooks" / name, hooks_dir / name)
            skill_dir = claude_dir / "skills" / "signaltrim"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: signaltrim\n---\nSTANDALONE MARKER RULESET\n"
            )

            result = self.run_cmd(["node", str(hooks_dir / "signaltrim-activate.js")], home)

            self.assertIn("STANDALONE MARKER RULESET", result.stdout)

    def test_activate_prefers_claude_plugin_root(self):
        with tempfile.TemporaryDirectory(prefix="signaltrim-hooks-pluginroot-") as tmp:
            home = Path(tmp)
            (home / ".claude").mkdir(parents=True)
            plugin_root = home / "plugin-cache"
            skill_dir = plugin_root / "skills" / "signaltrim"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: signaltrim\n---\nPLUGIN ROOT MARKER RULESET\n"
            )

            result = self.run_cmd(
                ["node", "src/hooks/signaltrim-activate.js"],
                home,
                extra_env={"CLAUDE_PLUGIN_ROOT": str(plugin_root)},
            )

            self.assertIn("PLUGIN ROOT MARKER RULESET", result.stdout)


if __name__ == "__main__":
    unittest.main()
