"""Regression checks for safe refreshes and portable generated output."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import generate_readme as generator


class ProfileGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('profile.json', 'README.template.md', 'data/repositories.json'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(generator.ROOT / name, target)

    def run_generator(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return generator.main(list(args), root=self.root)

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_offline_refresh_is_reproducible_and_check_never_writes(self):
        self.assertEqual(self.run_generator('--offline'), 0)
        original = self.snapshot()
        self.assertEqual(self.run_generator('--offline', '--check'), 0)
        self.assertEqual(self.snapshot(), original)
        stale = self.root / 'assets/gen/obsolete.svg'
        stale.write_text('<svg/>')
        self.assertEqual(self.run_generator('--offline', '--check'), 1)
        self.assertTrue(stale.exists())
        self.assertEqual(self.run_generator('--offline'), 0)
        self.assertEqual(self.snapshot(), original)

    def test_failed_network_refresh_preserves_last_good_profile(self):
        self.run_generator('--offline')
        original = self.snapshot()
        with patch.object(generator, 'fetch_repositories', side_effect=TimeoutError('offline')):
            self.assertEqual(self.run_generator(), 2)
        self.assertEqual(self.snapshot(), original)

    def test_missing_selected_repository_preserves_output(self):
        self.run_generator('--offline')
        original = self.snapshot()
        with patch.object(generator, 'fetch_repositories', return_value={}):
            self.assertEqual(self.run_generator(), 2)
        self.assertEqual(self.snapshot(), original)

    def test_svg_escapes_live_about_text_and_links_selected_projects(self):
        metadata = json.loads((self.root / generator.CACHE).read_text())
        metadata['RAG']['description'] = 'Search <documents> & compare "answers" ' + 'longword' * 40
        with patch.object(generator, 'fetch_repositories', return_value=metadata):
            self.assertEqual(self.run_generator(), 0)
        for svg in (self.root / generator.GEN).glob('*.svg'):
            ET.parse(svg)
        readme = (self.root / 'README.md').read_text()
        profile = json.loads((self.root / 'profile.json').read_text())
        for project in profile['projects']:
            self.assertIn('https://github.com/Flowerf19/' + project['repo'], readme)
        self.assertNotIn('ModelsReview', readme)
        self.assertNotIn('vietnamese-reranker-benchmark', readme)
        self.assertIn('SQLite lexical search', readme)


if __name__ == '__main__':
    unittest.main()
