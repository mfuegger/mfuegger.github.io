#!/usr/bin/env python3
"""Check source/output consistency, citations, metadata, and local links."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import bibtexparser

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = []
        self.papers = []
        self.citations = {}
        self.paper = None
        self.pre = False
        self.script = False
        self.json_texts = []
        self.h1_count = 0
        self.text = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert 'style' not in attrs and tag != 'style', 'Styles belong in academic.css'
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, f'Duplicate id: {attrs["id"]}'
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == 'h1':
            self.h1_count += 1
        if tag == 'li' and 'paper' in attrs.get('class', '').split():
            self.paper = attrs['id'].removeprefix('paper-')
            self.papers.append(self.paper)
        if tag == 'pre':
            self.pre = True
            self.citations[self.paper] = ''
        if tag == 'script':
            assert attrs.get('type') == 'application/ld+json', 'Only JSON-LD scripts are needed'
            self.script = True
            self.json_texts.append('')

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.pre = False
        if tag == 'script':
            self.script = False

    def handle_data(self, value):
        if self.pre:
            self.citations[self.paper] += value
        if self.script:
            self.json_texts[-1] += value
        else:
            self.text.append(value)


def main():
    data = json.loads((ROOT / 'content/profile.json').read_text(encoding='utf-8'))
    profile_data = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    person = profile_data['schemaOrg']
    for key, value in data.items():
        assert profile_data[key] == value, f'Profile data drift: {key}'
    machine = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
    library = bibtexparser.parse_file(str(ROOT / 'publications.bib'))
    assert not library.failed_blocks
    entries = {entry.key: entry for entry in library.entries}
    pages = {name: Page(ROOT / name) for name in ('index.html', 'publications.html')}
    homepage = pages['index.html']
    publication_page = pages['publications.html']
    assert person['name'] == data['name'] and person['email'] == data['email']
    assert person['description'] == data['description']
    assert person['worksFor']['name'] == data['employer']['name']
    visible = ' '.join(''.join(homepage.text).split())
    markdown = (ROOT / 'profile.md').read_text(encoding='utf-8')
    for course in data['teaching']['courses']:
        assert course['name'] in visible and course['details'] in visible
        assert course['name'] in markdown and course['details'] in markdown
    assert machine['count'] == len(entries) == len(publication_page.papers)
    assert set(publication_page.papers) == set(entries)
    assert len(machine['publications']) == len(entries)
    for record in machine['publications']:
        entry = entries[record['key']]
        assert record['bibtex'] == entry.raw
        assert publication_page.citations[entry.key] == entry.raw, f'Changed citation: {entry.key}'
        assert record['year'] == int(entry['year'])
        assert record['authors'], f'No authors: {entry.key}'
    selected = [line.strip() for line in (ROOT / 'selected-publications.txt').read_text().splitlines()
                if line.strip() and not line.lstrip().startswith('#')]
    assert homepage.papers == selected
    assert json.loads(homepage.json_texts[0])['mainEntity'] == person
    structured = json.loads(publication_page.json_texts[0])
    assert structured['numberOfItems'] == len(entries)
    assert len(structured['itemListElement']) == len(entries)
    for name, page in pages.items():
        assert page.h1_count == 1
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = ROOT / unquote(url.path) if url.path else ROOT / name
            if target.is_dir():
                target /= 'index.html'
            assert target.is_file(), f'Broken local link in {name}: {href}'
            if url.fragment:
                destination = pages.get(target.name) or Page(target)
                assert unquote(url.fragment) in destination.ids, f'Broken anchor: {href}'
    for item in structured['itemListElement']:
        assert unquote(urlsplit(item['item']['@id']).fragment) in publication_page.ids
    assert 'Disallow: /' not in (ROOT / 'robots.txt').read_text()
    print(f'Checked profile consistency, {len(entries)} exact BibTeX citations, selected papers, JSON-LD, and local links.')


if __name__ == '__main__':
    main()
