"""Build unpublished fixtures to verify Markdown collections and both baseurl modes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('bundle'), 'Ruby/Bundler required for Jekyll fixture build')
class CollectionTests(unittest.TestCase):
    def test_collections_and_baseurls(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            for name in ('_layouts', '_includes', '_data', '_posts', 'assets'):
                shutil.copytree(ROOT / name, source / name)
            for file in ROOT.iterdir():
                if file.suffix in ('.html', '.md', '.xml'):
                    shutil.copy(file, source / file.name)
            cool = source / '_cool_stuff'
            cool.mkdir()
            (cool / 'external.md').write_text('---\ntitle: Fixture link\ndate: 2026-07-01\ntags: [papers, systems]\nlink: https://example.com/paper\n---\n**Fixture** commentary.\n')
            (cool / 'observation.md').write_text('---\ntitle: Fixture observation\ndate: 2026-06-01\ntags: [ideas]\n---\nText without an external link.\n')
            notes = source / '_music_notes'
            notes.mkdir()
            (notes / 'note.md').write_text('---\ntitle: Fixture music note\ndate: 2026-07-02\n---\nA short **Markdown** note.\n')
            (source / '_data/music.yml').write_text('favourites:\n  - name: Fixture record\n    year: 1966\n    note: A fixture, not a personal opinion.\n')
            for base in ('', '/test-project'):
                config = Path(directory) / 'override.yml'
                config.write_text('baseurl: "' + base + '"\n')
                output = Path(directory) / ('project-site' if base else 'root-site')
                subprocess.run(['bundle', 'exec', 'jekyll', 'build', '--future', '--strict_front_matter',
                                '--source', str(source), '--destination', str(output),
                                '--config', str(ROOT / '_config.yml') + ',' + str(config)],
                               cwd=ROOT, check=True, capture_output=True, text=True)
                journal = (output / 'cool-stuff/index.html').read_text()
                self.assertIn('href="https://example.com/paper"', journal)
                self.assertIn('<strong>Fixture</strong> commentary.', journal)
                self.assertLess(journal.index('July 2026'), journal.index('June 2026'))
                self.assertIn('id="observation"', journal)
                self.assertIn('value="papers"', journal)
                music = (output / 'music/index.html').read_text()
                self.assertIn('Fixture record', music)
                self.assertNotIn('Fixture music note', music)
                self.assertNotIn('Music Notes', music)
                self.assertNotIn('A fixture, not a personal opinion.', music)
                self.assertNotIn('data-artwork', music)
                self.assertNotIn('class="lede"', music)
                self.assertIn('stuff I found cool get dumped here', journal)
                feed = ET.parse(output / 'cool-stuff/feed.xml')
                self.assertEqual(len(feed.findall('.//item')), 2)
                self.assertIn(base + '/cool-stuff/#external', feed.find('.//item/link').text)
                post = (output / '2026-07-24-cow-filesystem-fuse-rust/index.html').read_text()
                self.assertIn('src="' + base + '/assets/img/polarizer.png"', post)
                subprocess.run(['python3', str(ROOT / 'scripts/check_site.py'), str(output), base],
                               check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
