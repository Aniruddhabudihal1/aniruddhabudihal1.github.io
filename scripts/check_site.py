#!/usr/bin/env python3
"""Check generated internal links/assets, navigation, preserved URLs, and feeds."""
from html.parser import HTMLParser
from pathlib import Path
import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for attr in ('href', 'src'):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def check(root, base):
    root = root.resolve()
    failures = []
    pages = {}
    for file in root.rglob('*.html'):
        parser = Links()
        parser.feed(file.read_text())
        pages[file] = parser
    for file, parser in pages.items():
        for link in parser.links:
            url = urllib.parse.urlsplit(link)
            if url.scheme or url.netloc:
                continue
            path = urllib.parse.unquote(url.path)
            if path.startswith('/'):
                if base and path != base and not path.startswith(base + '/'):
                    failures.append(f'{file.relative_to(root)}: missing baseurl: {link}')
                    continue
                target = root / path[len(base):].lstrip('/')
            else:
                target = file.parent / path if path else file
            if target.is_dir():
                target /= 'index.html'
            elif not target.exists() and target.suffix == '':
                target /= 'index.html'
            target = target.resolve()
            if not target.exists():
                failures.append(f'{file.relative_to(root)}: missing {link}')
            elif url.fragment and target in pages and urllib.parse.unquote(url.fragment) not in pages[target].ids:
                failures.append(f'{file.relative_to(root)}: missing anchor {link}')
    for path in ('index.html', 'blogs/index.html', 'cool-stuff/index.html', 'music/index.html',
                 'contact/index.html', 'now/index.html', 'aboutme/index.html',
                 '2026-07-24-cow-filesystem-fuse-rust/index.html'):
        file = root / path
        assert file.exists(), f'Missing page {path}'
        text = file.read_text()
        assert 'class="theme-toggle"' in text, f'Missing shared navigation on {path}'
        assert 'rel="canonical"' in text, f'Missing canonical on {path}'
    for path in ('feed.xml', 'cool-stuff/feed.xml', 'sitemap.xml'):
        ET.parse(root / path)
    feed = ET.parse(root / 'feed.xml')
    assert feed.find('.//item') is not None, 'Existing post missing from RSS'
    data = json.loads((root / 'assets/data/lastfm.json').read_text())
    assert isinstance(data['tracks'], list)
    assert 'data-tags="[&quot;systems&quot;' in (root / 'blogs/index.html').read_text()
    assert not failures, '\n'.join(failures)
    print(f'Checked {len(pages)} HTML pages, internal links/assets/anchors, preserved post, and feeds (baseurl={base!r}).')


if __name__ == '__main__':
    check(Path(sys.argv[1] if len(sys.argv) > 1 else '_site'), sys.argv[2].rstrip('/') if len(sys.argv) > 2 else '')
