# BixBench-Verified-50 Workspaces

50 个 Agent 可以直接打开的独立分析文件夹，基于 [BixBench-Verified-50](https://huggingface.co/datasets/phylobio/BixBench-Verified-50)。每题包含英文原题、中文操作说明、数据目录、分析代码目录和输出目录。

## 快速开始

需要 Git 和 Python 3.9+，安装分析依赖建议使用 Python 3.12。数据准备脚本仅使用 Python 标准库。

```sh
git clone https://github.com/oinsist/BixBench-Verified-50-Workspaces.git
cd BixBench-Verified-50-Workspaces

# 准备一道小数据题
python3 prepare.py bix-18-q3

# 或准备全部 50 题，并安装共享 Python 分析环境
python3 prepare.py --all --install-env
```

在 Agent 应用中打开 `workspaces/bix-18-q3/`，输入“阅读 TASK.md，完成分析，并按 AGENTS.md 保存结果”。Python 环境安装后位于仓库的 `.venv/`，在 Agent 应用中选择对应解释器。Windows 可将 `python3` 改为 `python`。

克隆会得到 50 个工作区模板。准备命令从 GitHub Releases 下载原始数据并校验 SHA-256，再填入每题的 `data/`。`--all` 会复用 33 个数据包的下载缓存，解压后的每题数据是独立文件，修改一个工作区不会改变另一个工作区的数据。

```text
workspaces/bix-18-q3/
├── TASK.md
├── AGENTS.md
├── task.json
├── data/
├── analysis/
└── outputs/
```

## 开始一轮全新分析

用一个新目录名生成新的工作区，数据包缓存可复用。准备中断时可重跑同一命令，已完成的数据会重新校验，已有分析输出会保留。

```sh
python3 prepare.py --all --destination runs/experiment-001
# 单题也可以独立生成
python3 prepare.py bix-18-q3 --destination runs/single-question-001
```

新目录下每题都有自己的题目、数据、空白分析目录和空白输出目录。共享 Python 环境仍位于仓库根目录的 `.venv/`。重复运行默认工作区的准备命令会校验已有数据，保留分析代码和输出。数据被修改时会报告错误，可用新的 `--destination` 重新准备。

```sh
# 查看全部题目
python3 prepare.py --list
# 验证默认工作区的全部数据
python3 prepare.py --all --verify
# 验证另一轮分析的数据
python3 prepare.py --all --destination runs/experiment-001 --verify
```

## 数据与环境

发布的 33 个数据包仅包含原始 CapsuleData。工作区模板仅包含题号、题目和数据包标识。每个数据包和数据文件都有 SHA-256 校验值，记录在 `manifest.json`，数据资产版本为 `data-v1`。

Python 基础分析依赖见 `requirements.txt`。部分题目还需要 R、DESeq2、apeglm、BUSCO、比对工具或在线富集服务等。按题目和数据实际需要安装，并在分析报告中记录版本。依赖文件采用兼容版本范围，复现实验时请额外保存实际安装版本。此仓库提供工作目录与数据，Agent 应用负责模型、工具权限、轮数和运行环境配置。

模型密钥使用 Agent 应用的配置或环境变量。标准答案、参考 Notebook、以前的运行结果不随工作区分发。原始数据按来源保留内容，可能自带中间结果或相关材料。

可先手动下载 Release 数据包，再离线准备：

```sh
python3 prepare.py --all --assets /absolute/path/to/downloaded-assets
```

数据包缓存默认位于 `.cache/capsules/`，可通过 `--cache` 更改位置。准备过程会下载和解压较大的文件，请预留约 20 GB 磁盘空间；每增加一轮全部工作区，需再预留约 12 GB。

## 许可与来源

题目与数据来自 [phylobio/BixBench-Verified-50](https://huggingface.co/datasets/phylobio/BixBench-Verified-50)，源于 [FutureHouse BixBench](https://huggingface.co/datasets/futurehouse/BixBench)。本仓库按 Apache-2.0 分发，来源说明见 NOTICE，许可全文见 LICENSE。

维护者可用 `scripts/build_workspaces.py` 从原始本地数据重新生成工作区、清单和数据资产。该步骤不需要运行分析 Agent。
