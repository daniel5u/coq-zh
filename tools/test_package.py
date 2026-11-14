"""Release regressions: reproducibility, archive boundaries, and tag validation."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from check_release import validate_mod, REQUIRED
from package import mod_files, package


class PackageChecks(unittest.TestCase):
    def fixture(self, root):
        source = root / "mod"
        for name in REQUIRED:
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == "manifest.json":
                text = json.dumps({"ID": "QudZH", "Version": "0.2.0"})
            elif name == "Languages.xml":
                text = '<languages><lang Code="zh" /></languages>'
            elif name.endswith(".xml"):
                text = '<strings Lang="zh" />'
            elif name.endswith(".json"):
                text = '{}'
            elif name.endswith(".tsv"):
                text = 'Food\t食物\n'
            else:
                text = '// Source fixture\n'
            path.write_text(text, encoding="utf-8")
        return source

    def test_deterministic_archive_and_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = self.fixture(root)
            (source / '.DS_Store').write_bytes(b'ignored')
            (source / 'Scripts' / 'obj').mkdir()
            (source / 'Scripts' / 'obj' / 'private.dll').write_bytes(b'ignored')
            first = package(source, root / 'first.zip').read_bytes()
            for p in mod_files(source):
                os.utime(p, (2000000000, 2000000000))
                p.chmod(0o600)
            output = package(source, root / 'second.zip')
            self.assertEqual(first, output.read_bytes())
            self.assertEqual(output.with_name('second.zip.sha256').read_text(), hashlib.sha256(first).hexdigest() + '  second.zip\n')
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertTrue(all(name.startswith('QudZH/') for name in names))
                self.assertFalse(any('obj' in name or '.DS_Store' in name for name in names))
                self.assertEqual(archive.read('QudZH/runtime_strings.tsv').decode(), 'Food\t食物\n')

    def test_rejects_payload_symlinks_and_nested_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = self.fixture(root)
            extra = source / 'game.dll'
            extra.write_bytes(b'not distributable')
            with self.assertRaisesRegex(ValueError, 'Unexpected mod payload'):
                mod_files(source)
            extra.unlink()
            (root / 'outside.cs').write_text('secret')
            link = source / 'Scripts' / 'link.cs'
            link.symlink_to(root / 'outside.cs')
            with self.assertRaisesRegex(ValueError, 'Symlinks'):
                package(source, root / 'archive.zip')
            link.unlink()
            with self.assertRaisesRegex(ValueError, 'outside the mod'):
                package(source, source / 'archive.zip')

    def test_tag_and_shipped_content_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self.fixture(Path(folder))
            self.assertEqual(validate_mod(source, 'v0.2.0')[0], '0.2.0')
            with self.assertRaisesRegex(ValueError, 'does not match'):
                validate_mod(source, 'v0.3.0')
            (source / 'Strings.xml').write_text('<broken>')
            with self.assertRaises(Exception):
                validate_mod(source)
            (source / 'Strings.xml').unlink()
            with self.assertRaisesRegex(ValueError, 'Missing required'):
                validate_mod(source)


if __name__ == '__main__':
    unittest.main()
