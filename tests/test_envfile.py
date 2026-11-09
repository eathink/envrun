import unittest

from envrun.envfile import EnvFileError, parse_dotenv


class EnvFileTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_dotenv("A=1\nB=hello\n"), {"A": "1", "B": "hello"})

    def test_export_and_comments(self):
        text = "# note\n\nexport A=1\nB=2 # inline\n"
        self.assertEqual(parse_dotenv(text), {"A": "1", "B": "2"})

    def test_quotes_and_escapes(self):
        self.assertEqual(
            parse_dotenv(r'A="line1\nline2"' + "\n"), {"A": "line1\nline2"}
        )
        self.assertEqual(parse_dotenv("B='a # b'\n"), {"B": "a # b"})
        self.assertEqual(parse_dotenv('C="x # y"\n'), {"C": "x # y"})

    def test_empty_value(self):
        self.assertEqual(parse_dotenv("A=\n"), {"A": ""})

    def test_invalid_line(self):
        with self.assertRaises(EnvFileError):
            parse_dotenv("JUSTAKEY\n")

    def test_invalid_name(self):
        with self.assertRaises(EnvFileError):
            parse_dotenv("1BAD=x\n")

    def test_unclosed_quote(self):
        with self.assertRaises(EnvFileError):
            parse_dotenv('A="oops\n')


if __name__ == "__main__":
    unittest.main()
