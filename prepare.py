#!/usr/bin/env python3
"""准备一个或全部分析工作区，支持全新目录及校验。仅依赖 Python 标准库。"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import venv
import zipfile

ROOT = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_data(data, capsule):
    """逐文件验证，发现变化时保留用户数据并报错。"""
    for item in capsule['files']:
        path = data / item['path']
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise ValueError(f'数据缺失或被修改：{path}。请使用 --destination 指定新目录。')


def get_archive(capsule, manifest, cache, assets):
    path = (assets or cache) / capsule['asset']
    if path.exists():
        if path.is_file() and path.stat().st_size == capsule['bytes'] and sha256(path) == capsule['sha256']:
            return path
        raise ValueError(f'缓存校验失败：{path}。请删除该损坏文件后重试。')
    if assets:
        raise FileNotFoundError(f'本地数据包不存在：{path}')
    cache.mkdir(parents=True, exist_ok=True)
    url = f'https://github.com/{manifest["repository"]}/releases/download/{manifest["release"]}/{capsule["asset"]}'
    fd, temp_name = tempfile.mkstemp(prefix='.download-', dir=cache)
    temp = Path(temp_name)
    try:
        print(f'下载 {capsule["asset"]}', flush=True)
        os.close(fd)
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'BixBench-Workspaces/1'})
                with temp.open('wb') as output, urllib.request.urlopen(request, timeout=120) as response:
                    try:
                        shutil.copyfileobj(response, output, 1024 * 1024)
                    except http.client.IncompleteRead as exc:
                        # 某些代理缺少结束帧；只有完整大小和 SHA-256 都匹配才接受。
                        output.write(exc.partial)
                if temp.stat().st_size != capsule['bytes'] or sha256(temp) != capsule['sha256']:
                    raise ValueError(f'下载校验失败：{capsule["asset"]}')
                break
            except (OSError, ValueError, http.client.HTTPException):
                if attempt == 2:
                    raise
                print(f'下载中断或校验失败，重试 {attempt + 1}/2', flush=True)
                time.sleep(attempt + 1)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return path


def extract_data(archive, target, capsule):
    """先验证路径和清单，再在临时目录解压，完整校验后替换空目录。"""
    expected = {item['path'] for item in capsule['files']}
    with zipfile.ZipFile(archive) as src:
        names = []
        for info in src.infolist():
            path = PurePosixPath(info.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename
                    or stat.S_ISLNK(info.external_attr >> 16) or info.is_dir()):
                raise ValueError(f'数据包路径不安全：{info.filename}')
            names.append(info.filename)
        if set(names) != expected or len(names) != len(expected):
            raise ValueError('数据包文件清单不匹配')
        with tempfile.TemporaryDirectory(prefix='.prepare-', dir=target.parent) as temp_name:
            staged = Path(temp_name) / 'data'
            staged.mkdir()
            src.extractall(staged)
            verify_data(staged, capsule)
            # 再检查一次，避免覆盖准备期间出现的用户文件。
            if target.is_symlink():
                raise ValueError(f'拒绝覆盖符号链接：{target}')
            if target.exists():
                entries = list(target.iterdir())
                if any(p.name != '.gitkeep' or not p.is_file() for p in entries):
                    raise ValueError(f'目标已有数据：{target}')
                for entry in entries:
                    entry.unlink()
                target.rmdir()
            staged.rename(target)


def prepare_task(task, capsule, manifest, destination, cache, assets, verify_only):
    qid = task['id']
    template = ROOT / 'workspaces' / qid
    workspace = destination / qid if destination else template
    if workspace.is_symlink():
        raise ValueError(f'工作区必须是独立目录：{workspace}')
    if not workspace.exists():
        if verify_only:
            raise FileNotFoundError(f'工作区不存在：{workspace}')
        workspace.mkdir(parents=True)
        for filename in ['TASK.md', 'AGENTS.md', 'task.json']:
            shutil.copyfile(template / filename, workspace / filename)
        for dirname in ['data', 'analysis', 'outputs']:
            (workspace / dirname).mkdir()
    elif not (workspace / 'task.json').is_file() or json.loads((workspace / 'task.json').read_text()) != task:
        raise ValueError(f'已有目录不是对应的工作区：{workspace}')
    data = workspace / 'data'
    if data.is_symlink():
        raise ValueError(f'data 必须是独立目录：{data}')
    populated = data.exists() and any(p.name != '.gitkeep' for p in data.iterdir())
    if verify_only or populated:
        verify_data(data, capsule)
    else:
        archive = get_archive(capsule, manifest, cache, assets)
        extract_data(archive, data, capsule)
    print(f'就绪 {qid} → {workspace}', flush=True)


def install_environment():
    target = ROOT / '.venv'
    if target.exists() and not (target / 'pyvenv.cfg').is_file():
        raise ValueError('.venv 已存在且不是虚拟环境')
    venv.EnvBuilder(with_pip=True).create(target)
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
    print(f'Python 分析环境：{python}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tasks', nargs='*', help='题目 ID，例如 bix-18-q3')
    parser.add_argument('--all', action='store_true', help='准备全部 50 题')
    parser.add_argument('--list', action='store_true', help='列出题目')
    parser.add_argument('--destination', type=Path, help='在指定新目录下生成独立工作区')
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache' / 'capsules')
    parser.add_argument('--assets', type=Path, help='从本地已发布数据包准备，无需网络')
    parser.add_argument('--verify', action='store_true', help='只验证已准备的数据')
    parser.add_argument('--install-env', action='store_true', help='安装共享 Python 分析虚拟环境')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    tasks = {task['id']: task for task in manifest['tasks']}
    if args.list:
        for task in tasks.values():
            print(task['id'], task['question'])
        return
    if args.all and args.tasks:
        parser.error('--all 与题目 ID 二选一')
    selected = list(tasks) if args.all else list(dict.fromkeys(args.tasks))
    if not selected or any(qid not in tasks for qid in selected):
        parser.error('请指定有效题目 ID，或使用 --all / --list')
    destination = args.destination.resolve() if args.destination else None
    if destination and not args.verify:
        destination.mkdir(parents=True, exist_ok=True)
    if args.install_env:
        install_environment()
    for qid in selected:
        task = tasks[qid]
        prepare_task(task, manifest['capsules'][task['capsule']], manifest,
                     destination, args.cache.resolve(), args.assets.resolve() if args.assets else None, args.verify)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, http.client.HTTPException, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print(f'准备失败：{exc}', file=sys.stderr)
        sys.exit(1)
