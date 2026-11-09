# envrun

**用指定 `.env` 文件运行命令，不污染当前 shell。**

切换环境时最烦的一步是 `export` 一堆变量、跑完再 `unset`，忘一个就串环境。`envrun` 把变量只注入到子进程：命令怎么跑都用这份环境，退出即消失。

[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Zero deps](https://img.shields.io/badge/dependencies-0-brightgreen)](#设计取舍)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![CI](https://github.com/eathink/envrun/actions/workflows/ci.yml/badge.svg)](https://github.com/eathink/envrun/actions/workflows/ci.yml)

## 快速开始

```bash
pipx install git+https://github.com/eathink/envrun

# 用 .env 运行命令
envrun -- ./scripts/test.sh

# 叠加两份配置，后一份覆盖前一份
envrun -e .env -e .env.local -- python app.py
```

```console
$ envrun -e .env -e .env.prod --set DEBUG=true -- python -c "import os; print(os.environ['APP_ENV'])"
production
```

## 合并顺序

从空到满，后面的覆盖前面的：

1. 当前进程继承的环境变量
2. `-e FILE` 依次加载（没给 `-e` 时，当前目录有 `.env` 就用它）
3. `--set KEY=VALUE`
4. `--unset KEY`

## 查看结果

```bash
envrun -e .env.prod --dry-run
```

```console
$ envrun -e .env --dry-run
API_URL=http://localhost:8000
APP_ENV=development
DEBUG=true
```

默认**只显示被文件或 `--set` 改变/新增的变量**，不会把继承的整份环境（可能含密钥）打印出来。确实要看完整环境时：

```bash
envrun -e .env --dry-run --show-all
```

## 用法

```bash
envrun [-e FILE ...] [--set KEY=VALUE ...] [--unset KEY ...] [--dry-run [--show-all]] -- COMMAND [ARGS...]
```

| 参数 | 说明 |
| --- | --- |
| `-e, --env FILE` | 环境变量文件，可重复；后加载的覆盖先加载的 |
| `--set KEY=VALUE` | 覆盖单个变量，可重复 |
| `--unset KEY` | 删除变量，可重复 |
| `--dry-run` | 打印变化，不执行命令 |
| `--show-all` | 配合 `--dry-run` 打印完整环境（可能含密钥） |
| `--version` | 版本号 |

`--` 后面是原样执行的命令，不会被 `envrun` 解析。

### 退出码

| 码 | 含义 |
| --- | --- |
| 子进程退出码 | 原样返回 |
| 2 | 参数、配置文件或变量名错误 |
| 126 | 命令没有执行权限 |
| 127 | 命令不存在 |
| 130 | 被 Ctrl+C 中断 |

## 已知边界

- **不做变量展开**：`URL=${HOST}:${PORT}` 不会替换，原样传入；展开规则各工具不同，隐式行为容易埋坑
- **不启动 shell**：命令按参数数组执行，`echo $HOME` 这种重定向/通配需要你自己用 `sh -c`
- **不读 `.env.*` 目录树**：只加载显式 `-e` 指定的文件，或当前目录的 `.env`，不向父目录搜索
- 文件解析支持 `export`、单双引号、转义、行内注释，不支持多行值

## 设计取舍

- **只注入子进程**：这是它和 `source .env` 的根本区别，不会污染当前 shell 或后续命令
- **默认 dry-run 只显示变化**：完整环境里常有认证 token，默认打印是安全事故
- **按数组执行而不是拼 shell 字符串**：避免引号和注入问题，代价是不支持通配和重定向
- **零依赖**：`.env` 解析器是几十行标准库代码，不需要为了几个键值引入 YAML

## 开发

```bash
git clone https://github.com/eathink/envrun
cd envrun

# 仅用标准库，无需安装依赖
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 本地运行
PYTHONPATH=src python3 -m envrun -e .env --dry-run
```

## License

[MIT](LICENSE)
