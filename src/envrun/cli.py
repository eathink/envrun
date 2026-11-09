"""命令行入口。"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core import EnvError, EnvFileError, build_environment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envrun",
        description="用指定 .env 文件运行命令，不污染当前 shell。",
    )
    parser.add_argument(
        "-e",
        "--env",
        action="append",
        default=[],
        metavar="FILE",
        help="环境变量文件，可重复；后加载的覆盖先加载的",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="覆盖单个变量，可重复",
    )
    parser.add_argument(
        "--unset", action="append", default=[], metavar="KEY", help="删除变量，可重复"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只打印合并后的环境变量变化，不执行命令"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="配合 --dry-run 打印完整环境（含继承变量，可能包含密钥）",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="要执行的命令（建议用 -- 与选项分隔）",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    if args.dry_run and command:
        print("envrun: --dry-run 不能同时指定命令", file=sys.stderr)
        return 2
    if not args.dry_run and not command:
        print("envrun: 需要提供要运行的命令（用 -- 分隔）", file=sys.stderr)
        return 2
    if args.show_all and not args.dry_run:
        print("envrun: --show-all 只能配合 --dry-run 使用", file=sys.stderr)
        return 2

    files = list(args.env)
    if not files and Path(".env").is_file():
        files = [".env"]

    base = dict(os.environ)
    try:
        environment = build_environment(base, files, args.set, args.unset)
    except (EnvFileError, EnvError) as exc:
        print(f"envrun: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        if args.show_all:
            items = sorted(environment.items())
        else:
            items = [
                (key, value)
                for key, value in sorted(environment.items())
                if base.get(key) != value
            ]
        for key, value in items:
            print(f"{key}={value}")
        if not args.show_all:
            for key in args.unset:
                if key in base and key not in environment:
                    print(f"# unset {key}")
        return 0

    try:
        process = subprocess.run(command, env=environment)
    except FileNotFoundError:
        print(f"envrun: 命令不存在：{command[0]}", file=sys.stderr)
        return 127
    except PermissionError:
        print(f"envrun: 没有执行权限：{command[0]}", file=sys.stderr)
        return 126
    except KeyboardInterrupt:
        return 130

    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
