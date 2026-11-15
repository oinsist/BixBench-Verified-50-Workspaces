"""覆盖损坏数据、路径穿越及已有结果保护。"""
import hashlib
import importlib.util
import tempfile
from pathlib import Path
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('prepare', Path(__file__).resolve().parents[1] / 'prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class PrepareTests(unittest.TestCase):
    def test_valid_archive_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            archive = root / 'data.zip'
            content = b'hello'
            capsule = {'files': [{'path': 'nested/input.txt', 'bytes': 5, 'sha256': hashlib.sha256(content).hexdigest()}]}
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('nested/input.txt', content)
            prepare.extract_data(archive, root / 'data', capsule)
            prepare.verify_data(root / 'data', capsule)
            (root / 'data/nested/input.txt').write_text('user change')
            with self.assertRaises(ValueError):
                prepare.extract_data(archive, root / 'data', capsule)
            self.assertEqual((root / 'data/nested/input.txt').read_text(), 'user change')

    def test_unsafe_archive(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            archive = root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../escape', 'bad')
            with self.assertRaises(ValueError):
                prepare.extract_data(archive, root / 'data', {'files': [{'path': '../escape'}]})
            self.assertFalse((root / 'escape').exists())

    def test_bad_checksum_does_not_publish_data(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            archive = root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('input', 'bad')
            with self.assertRaises(ValueError):
                prepare.extract_data(archive, root / 'data', {'files': [{'path': 'input', 'bytes': 3, 'sha256': 'wrong'}]})
            self.assertFalse((root / 'data').exists())


if __name__ == '__main__':
    unittest.main()
