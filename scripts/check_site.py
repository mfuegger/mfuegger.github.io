#!/usr/bin/env python3
"""Check source/output consistency, citations, metadata, and local links."""
from html.parser import HTMLParser
import json
from pathlib import Path
from string import Template
from urllib.parse import unquote, urlsplit
import bibtexparser

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE / "build"


class Page(HTMLParser):
    def __init__(self, path, check_styles=True):
        super().__init__()
        self.check_styles = check_styles
        self.ids = set()
        self.links = []
        self.assets = []
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
        if self.check_styles:
            assert 'style' not in attrs and tag != 'style', 'Styles belong in academic.css'
        if tag in ('img', 'script', 'iframe') and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag == 'link' and 'stylesheet' in attrs.get('rel', '').split():
            self.assets.append(attrs['href'])
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
    data = json.loads((SOURCE / 'content/profile.json').read_text(encoding='utf-8'))
    profile_data = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    person = profile_data['schemaOrg']
    for key, value in data.items():
        assert profile_data[key] == value, f'Profile data drift: {key}'
    machine = json.loads((ROOT / 'publications.json').read_text(encoding='utf-8'))
    teaching = json.loads((ROOT / 'teaching.json').read_text(encoding='utf-8'))
    assert (ROOT / 'publications.bib').read_bytes() == (SOURCE / 'content/publications.bib').read_bytes()
    library = bibtexparser.parse_file(str(ROOT / 'publications.bib'))
    assert not library.failed_blocks
    entries = {entry.key: entry for entry in library.entries}
    pages = {name: Page(ROOT / name) for name in ('index.html', 'publications.html', 'teaching.html', 'privacy.html', 'legal.html')}
    legacy_pages = {name: Page(ROOT / name, check_styles=False)
                    for name in ('habil/index.html', 'projects/sic.html')}
    homepage = pages['index.html']
    publication_page = pages['publications.html']
    assert person['name'] == data['name'] and person['email'] == data['email']
    assert person['description'] == data['description']
    assert person['worksFor']['name'] == data['employer']['name']
    visible = ' '.join(''.join(homepage.text).split())
    markdown = (ROOT / 'profile.md').read_text(encoding='utf-8')
    for course in sorted(data['teaching']['courses'], key=lambda c: int(c['year']), reverse=True)[:2]:
        assert course['name'] in visible and course['details'] in visible
        assert course['name'] in markdown and course['details'] in markdown
    teaching_visible = ' '.join(''.join(pages['teaching.html'].text).split())
    teaching_markdown = (ROOT / 'teaching.md').read_text(encoding='utf-8')
    assert teaching['courses'] == sorted(data['teaching']['courses'], key=lambda c: int(c['year']), reverse=True)
    assert len([id for id in pages['teaching.html'].ids if id.startswith('course-')]) == len(teaching['courses'])
    for course in data['teaching']['courses']:
        assert course['name'] in teaching_visible and course['details'] in teaching_visible
        assert course['name'] in teaching_markdown and course['details'] in teaching_markdown
        if course.get('recording'):
            recording = course['recording']
            assert recording['url'] in pages['teaching.html'].links
            assert recording['thumbnail'] in pages['teaching.html'].assets
            assert recording['url'] in teaching_markdown
            assert recording['title'] in teaching_visible
    assert 'videos' in homepage.ids
    for course in data['teaching']['courses']:
        if course.get('recording'):
            recording = course['recording']
            assert recording['url'] in homepage.links
            assert recording['thumbnail'] in homepage.assets
    for video in data.get('videos', []):
        assert video['url'] in homepage.links and video['url'] in markdown
        assert video['thumbnail'] in homepage.assets
        assert video['title'] in visible and video['title'] in markdown
    if data['teaching'].get('channel'):
        channel = data['teaching']['channel']
        assert teaching['channel'] == channel
        for page in (homepage, pages['teaching.html']):
            assert channel['url'] in page.links
            assert 'assets/youtube-icon.svg' in page.assets
        assert channel['url'] in teaching_markdown and channel['url'] in markdown
    assert 'Teaching archive on my institutional profile' not in visible
    assert 'archive_url' not in data['teaching']
    for page in pages.values():
        assert 'teaching.html' in page.links
    assert json.loads(pages['teaching.html'].json_texts[0]) == teaching['schemaOrg']
    assert teaching['schemaOrg']['mainEntity']['numberOfItems'] == len(teaching['courses'])
    for item in teaching['schemaOrg']['mainEntity']['itemListElement']:
        assert urlsplit(item['url']).fragment in pages['teaching.html'].ids
    assert 'https://mfuegger.github.io/teaching.html' in (ROOT / 'sitemap.xml').read_text()
    source_notices = json.loads((SOURCE / 'content/notices.json').read_text())
    exported_notices = json.loads((ROOT / 'notices.json').read_text())
    for key, value in source_notices.items():
        if key != 'pages':
            assert exported_notices[key] == value, f'Notice data drift: {key}'
    assert exported_notices['publisher'] == {
        'name': data['name'], 'email': data['email'], 'address': data['contact']['address']}
    hosting = source_notices['hosting']
    context = {'name': data['name'], 'hosting_name': hosting['name'],
               'hosting_service': hosting['service'], 'hosting_address': ', '.join(hosting['address'])}
    assert len(exported_notices['pages']) == len(source_notices['pages'])
    for notice in source_notices['pages']:
        slug = notice['slug']
        page = pages[slug + '.html']
        visible_notice = ' '.join(''.join(page.text).split())
        readable_notice = (ROOT / (slug + '.md')).read_text()
        exported = next(item for item in exported_notices['pages'] if item['slug'] == slug)
        assert exported['url'] == 'https://mfuegger.github.io/' + slug + '.html'
        assert data['name'] in visible_notice and data['email'] in visible_notice
        for section in notice['sections']:
            exported_section = next(item for item in exported['sections'] if item['id'] == section['id'])
            assert exported_section['paragraphs'] == [Template(value).substitute(context) for value in section['paragraphs']]
            for paragraph in section['paragraphs']:
                expected = Template(paragraph).substitute(context)
                assert expected in visible_notice and expected in readable_notice
        assert json.loads(page.json_texts[0])['dateModified'] == source_notices['last_reviewed']
        assert 'https://mfuegger.github.io/' + slug + '.html' in (ROOT / 'sitemap.xml').read_text()
    for name, page in {**pages, **legacy_pages}.items():
        prefix = '..' if name in legacy_pages else '.'
        assert prefix + '/privacy.html' in page.links and prefix + '/legal.html' in page.links
        for asset in page.assets:
            assert not urlsplit(asset).scheme and not urlsplit(asset).netloc, f'External asset contradicts privacy notice: {asset}'
            assert (ROOT / name).parent.joinpath(asset.split('?')[0]).is_file(), f'Missing local asset: {asset}'
    assert machine['count'] == len(entries) == len(publication_page.papers)
    assert set(publication_page.papers) == set(entries)
    assert len(machine['publications']) == len(entries)
    for record in machine['publications']:
        entry = entries[record['key']]
        assert record['bibtex'] == entry.raw
        assert publication_page.citations[entry.key] == entry.raw, f'Changed citation: {entry.key}'
        assert record['year'] == int(entry['year'])
        assert record['authors'], f'No authors: {entry.key}'
    doctoral_record = next(record for record in machine['publications']
                           if record['key'] == data['doctoral_thesis']['bibliography_key'])
    doctoral = profile_data['theses'][1]
    assert doctoral['title'] == doctoral_record['title']
    assert doctoral['year'] == doctoral_record['year']
    assert doctoral['pdf_url'] == doctoral_record['links']['pdf']
    assert doctoral['title'] in visible and doctoral['title'] in markdown
    assert doctoral['pdf_url'] in homepage.links
    assert doctoral['details_url'] in homepage.links
    assert profile_data['theses'][0]['title'] == data['habilitation']['title']
    selected = [line.strip() for line in (SOURCE / 'content/selected-publications.txt').read_text().splitlines()
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
    print(f'Checked profile consistency, {len(entries)} exact BibTeX citations, {len(teaching["courses"])} teaching entries, notices, footer links, local assets, JSON-LD, and local links.')


if __name__ == '__main__':
    main()
