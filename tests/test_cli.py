import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from envrun.cli import main

SRC = str(Path(__file__).resolve().parents[1] / "src")


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_dry_run(self):
        path = self.write("a.env", "FOO=bar\nSECRET=x\n")

        code, out, _ = self.run_cli(
            "-e", path, "--set", "FOO=override", "--unset", "SECRET", "--dry-run"
        )

        self.assertEqual(code, 0)
        self.assertIn("FOO=override", out)
        self.assertNotIn("SECRET", out)

    def test_dry_run_hides_unrelated_inherited_vars(self):
        path = self.write("a.env", "FOO=bar\n")

        _, out, _ = self.run_cli("-e", path, "--dry-run")

        self.assertIn("FOO=bar", out)
        self.assertFalse(any(line.startswith("PATH=") for line in out.splitlines()))

    def test_dry_run_show_all(self):
        path = self.write("a.env", "FOO=bar\n")

        _, out, _ = self.run_cli("-e", path, "--dry-run", "--show-all")

        self.assertIn("FOO=bar", out)
        self.assertTrue(any(line.startswith("PATH=") for line in out.splitlines()))

    def test_show_all_requires_dry_run(self):
        code, _, err = self.run_cli("--show-all", "--", "echo", "hi")

        self.assertEqual(code, 2)
        self.assertIn("--show-all", err)

    def test_missing_env_file_returns_two(self):
        code, _, err = self.run_cli(
            "-e", str(self.root / "missing.env"), "--dry-run"
        )

        self.assertEqual(code, 2)
        self.assertIn("envrun:", err)

    def test_invalid_set_returns_two(self):
        code, _, err = self.run_cli("--set", "NOEQUALS", "--dry-run")

        self.assertEqual(code, 2)
        self.assertIn("KEY=VALUE", err)

    def test_no_command_returns_two(self):
        code, _, err = self.run_cli()

        self.assertEqual(code, 2)
        self.assertIn("需要提供要运行的命令", err)

    def test_dry_run_with_command_rejected(self):
        code, _, err = self.run_cli("--dry-run", "--", "echo", "hi")

        self.assertEqual(code, 2)
        self.assertIn("不能同时", err)

    def test_child_exit_code_is_propagated(self):
        code, _, _ = self.run_cli(
            "--", sys.executable, "-c", "import sys; sys.exit(3)"
        )

        self.assertEqual(code, 3)

    def test_missing_command_returns_127(self):
        code, _, err = self.run_cli("--", "definitely-not-a-real-command-xyz")

        self.assertEqual(code, 127)
        self.assertIn("命令不存在", err)

    def test_command_sees_env(self):
        path = self.write("a.env", "FOO=fromfile\n")
        env = os.environ.copy()
        env["PYTHONPATH"] = SRC

        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "envrun",
                "-e",
                path,
                "--",
                sys.executable,
                "-c",
                "import os; print(os.environ['FOO'])",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout.strip(), "fromfile")

    def test_default_dotenv_is_used(self):
        (self.root / ".env").write_text("FOO=fromdefault\n", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = SRC

        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "envrun",
                "--",
                sys.executable,
                "-c",
                "import os; print(os.environ['FOO'])",
            ],
            capture_output=True,
            text=True,
            cwd=self.root,
            env=env,
        )

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout.strip(), "fromdefault")


if __name__ == "__main__":
    unittest.main()
