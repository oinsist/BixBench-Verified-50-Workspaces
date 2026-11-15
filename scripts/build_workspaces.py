#!/usr/bin/env python3
"""从本地题库生成不含标准答案的工作区和可发布数据资产。"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--assets', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.source / 'BixBench-Verified-50.jsonl').read_text().splitlines() if line.strip()]
    assert len(rows) == 50 and len({row['question_id'] for row in rows}) == 50
    args.assets.mkdir(parents=True, exist_ok=True)
    capsules = {}
    for capsule in sorted({row['capsule_uuid'] for row in rows}):
        source = args.source / 'capsules' / f'CapsuleFolder-{capsule}.zip'
        asset = args.assets / f'data-{capsule}.zip'
        files = []
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(asset, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as dst:
            prefix = f'CapsuleData-{capsule}/'
            for info in sorted(src.infolist(), key=lambda item: item.filename):
                if not info.filename.startswith(prefix) or info.is_dir():
                    continue
                name = info.filename[len(prefix):]
                path = PurePosixPath(name)
                if not name or path.is_absolute() or '..' in path.parts or '\\' in name or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError(f'不安全的源路径：{name}')
                if any(part in {'.DS_Store', '__MACOSX'} for part in path.parts):
                    continue
                digest = hashlib.sha256()
                target_info = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 0, 0, 0))
                target_info.compress_type = zipfile.ZIP_DEFLATED
                target_info.external_attr = 0o100644 << 16
                with src.open(info) as input_file, dst.open(target_info, 'w', force_zip64=True) as output_file:
                    for chunk in iter(lambda: input_file.read(1024 * 1024), b''):
                        digest.update(chunk)
                        output_file.write(chunk)
                files.append({'path': name, 'bytes': info.file_size, 'sha256': digest.hexdigest()})
        if not files:
            raise ValueError(f'数据为空：{capsule}')
        capsules[capsule] = {'asset': asset.name, 'bytes': asset.stat().st_size, 'sha256': sha256(asset), 'files': files}
        print(f'打包 {len(capsules)}/33 {asset.name} {asset.stat().st_size}', flush=True)
    tasks = []
    for row in rows:
        qid = row['question_id']
        task = {'id': qid, 'question': row['question'], 'capsule': row['capsule_uuid']}
        tasks.append(task)
        work = ROOT / 'workspaces' / qid
        work.mkdir(parents=True, exist_ok=True)
        (work / 'task.json').write_text(json.dumps(task, ensure_ascii=False, indent=2) + '\n')
        (work / 'TASK.md').write_text(f'# {qid}\n\n## Question\n\n{row["question"]}\n\n## 工作目录\n\n- `data/`：已校验的原始输入。先从仓库根目录执行 `python3 prepare.py {qid}`。\n- `analysis/`：分析脚本或 Notebook。\n- `outputs/`：结果文件及图表。\n\n完成后写入 `outputs/answer.json`，格式见 `AGENTS.md`。\n')
        (work / 'AGENTS.md').write_text('''# 工作区约定

阅读 TASK.md 并根据原始英文题目完成分析。

- 在当前工作区内开展分析，输入数据位于 data/，保持原始输入不变。
- 将代码保存在 analysis/，将结果、图表及日志保存在 outputs/。
- 分析说明写入 outputs/report.md，记录数据选择、方法、参数、依赖版本和限制。
- 最终写入 outputs/answer.json，例如 {"answer": "简洁答案", "status": "completed"}。无法完成时用 status="blocked" 并增加 reason 字段。
- 根据实际数据计算，不编造数据或结果，不查找标准答案或参考解题 Notebook。
- 先检查当前环境中的依赖；需要额外工具时记录安装方法和实际版本。
- API 密钥通过运行环境提供，不写入文件或分析输出。
- 文件夹是分析任务入口；Agent 的模型、工具权限和轮数由运行该 Agent 的应用配置。
''')
        for name in ['data', 'analysis', 'outputs']:
            (work / name).mkdir(exist_ok=True)
            (work / name / '.gitkeep').touch()
    manifest = {'version': 1, 'repository': 'oinsist/BixBench-Verified-50-Workspaces', 'release': 'data-v1', 'tasks': tasks, 'capsules': capsules}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (args.assets / 'SHA256SUMS').write_text(''.join(f'{v["sha256"]}  {v["asset"]}\n' for v in capsules.values()))
    print('生成完成：50 个工作区，33 个数据包', flush=True)


if __name__ == '__main__':
    main()
