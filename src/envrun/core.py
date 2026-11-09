"""合并环境变量。"""

from __future__ import annotations

import re

from .envfile import EnvFileError, load_env_file

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EnvError(ValueError):
    """覆盖项或 unset 项不合法。"""


def parse_assignment(raw: str) -> tuple[str, str]:
    key, separator, value = raw.partition("=")
    if not separator:
        raise EnvError(f"--set 需要 KEY=VALUE 形式：{raw!r}")
    key = key.strip()
    if not _KEY_RE.match(key):
        raise EnvError(f"非法变量名：{key!r}")
    return key, value


def build_environment(
    base: dict[str, str],
    files: list[str],
    overrides: list[str],
    unsets: list[str],
) -> dict[str, str]:
    """先文件（后加载的覆盖前面的），再 --set，最后 --unset。"""
    environment = dict(base)

    for path in files:
        environment.update(load_env_file(path))

    for raw in overrides:
        key, value = parse_assignment(raw)
        environment[key] = value

    for key in unsets:
        key = key.strip()
        if not _KEY_RE.match(key):
            raise EnvError(f"非法变量名：{key!r}")
        environment.pop(key, None)

    return environment


__all__ = ["EnvError", "EnvFileError", "build_environment", "parse_assignment"]
