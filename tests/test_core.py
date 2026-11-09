import tempfile
import unittest
from pathlib import Path

from envrun.core import EnvError, EnvFileError, build_environment, parse_assignment


class CoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_files_merge_in_order(self):
        first = self.write("a.env", "A=1\nB=1\n")
        second = self.write("b.env", "B=2\nC=3\n")

        env = build_environment({"BASE": "x"}, [first, second], [], [])

        self.assertEqual(env["BASE"], "x")
        self.assertEqual(env["A"], "1")
        self.assertEqual(env["B"], "2")
        self.assertEqual(env["C"], "3")

    def test_overrides_and_unsets(self):
        path = self.write("a.env", "A=1\nB=2\n")

        env = build_environment(
            {}, [path], ["A=9", "D=4"], ["B"]
        )

        self.assertEqual(env["A"], "9")
        self.assertNotIn("B", env)
        self.assertEqual(env["D"], "4")

    def test_invalid_assignment(self):
        with self.assertRaises(EnvError):
            parse_assignment("NOEQUALS")
        with self.assertRaises(EnvError):
            parse_assignment("1BAD=x")

    def test_invalid_unset(self):
        with self.assertRaises(EnvError):
            build_environment({}, [], [], ["1BAD"])

    def test_missing_file(self):
        with self.assertRaises(EnvFileError):
            build_environment({}, [str(self.root / "missing.env")], [], [])


if __name__ == "__main__":
    unittest.main()
