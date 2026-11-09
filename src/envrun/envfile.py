"""解析 .env 文件。"""

from __future__ import annotations

import re
from pathlib import Path

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}


class EnvFileError(ValueError):
    """环境变量文件无法解析。"""


def _split_quoted(value: str, source: str, lineno: int):
    if not value:
        return None
    quote = value[0]
    if quote not in "\"'":
        return None

    out: list[str] = []
    index = 1
    while index < len(value):
        char = value[index]
        if quote == '"' and char == "\\" and index + 1 < len(value):
            nxt = value[index + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            index += 2
            continue
        if char == quote:
            return "".join(out), value[index + 1 :]
        out.append(char)
        index += 1

    raise EnvFileError(f"{source}:{lineno}: 引号未闭合")


def _strip_comment(rest: str) -> str:
    position = rest.find(" #")
    if position >= 0:
        rest = rest[:position]
    elif rest.startswith("#"):
        rest = ""
    return rest.rstrip()


def parse_dotenv(text: str, source: str = "<input>") -> dict[str, str]:
    result: dict[str, str] = {}

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        if "=" not in line:
            raise EnvFileError(f"{source}:{lineno}: 缺少 '='")

        key, _, value = line.partition("=")
        key = key.strip()
        if not _KEY_RE.match(key):
            raise EnvFileError(f"{source}:{lineno}: 非法变量名 {key!r}")

        value = value.strip()
        quoted = _split_quoted(value, source, lineno)
        if quoted is not None:
            value, rest = quoted
            rest = rest.strip()
            if rest and not rest.startswith("#"):
                raise EnvFileError(f"{source}:{lineno}: 引号后有多余内容 {rest!r}")
        else:
            value = _strip_comment(value)

        result[key] = value

    return result


def load_env_file(path: str | Path) -> dict[str, str]:
    env_path = Path(path)
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EnvFileError(
            f"无法读取 {path}: {exc.strerror or exc}"
        ) from exc
    return parse_dotenv(text, str(env_path))
