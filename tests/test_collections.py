"""Build unpublished fixtures to verify Markdown collections and both baseurl modes."""
from pathlib import Path
import shlex
import shutil
import sys
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('bundle'), 'Ruby/Bundler required for Jekyll fixture build')
class CollectionTests(unittest.TestCase):
    def run_stage(self, stage, command, base):
        context = f'{stage} (baseurl={base!r})'
        print(f'\n[collections] {context}\n$ {shlex.join(command)}', flush=True)
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            self.fail(f'{context} failed with exit code {result.returncode}\n'
                      f'Command: {shlex.join(command)}\n'
                      f'stdout:\n{result.stdout or "(empty)"}\n'
                      f'stderr:\n{result.stderr or "(empty)"}')
        if result.stdout:
            print(result.stdout, end='', flush=True)
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr, flush=True)
        print(f'[collections] PASS: {context}', flush=True)

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
                self.run_stage('Jekyll build', ['bundle', 'exec', 'jekyll', 'build', '--future', '--strict_front_matter',
                                '--source', str(source), '--destination', str(output),
                                '--config', str(ROOT / '_config.yml') + ',' + str(config)],
                               base)
                print(f'[collections] Checking fixture content (baseurl={base!r}, output={output})', flush=True)
                contact = (output / 'contact/index.html').read_text()
                self.assertIn('href="tel:+919535594466"', contact)
                self.assertIn('href="https://www.last.fm/user/maxverstrapon"', contact)
                self.assertIn('Last.fm', contact)
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
                self.run_stage('Site validation', [sys.executable, str(ROOT / 'scripts/check_site.py'),
                                                  str(output), base], base)


if __name__ == '__main__':
    unittest.main()
