#!/usr/bin/env python3
"""Derive machine-readable profile data from the editable homepage."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://mfuegger.github.io/'


class ProfileParser(HTMLParser):
    """Read visible main content; navigation and metadata are excluded."""

    def __init__(self):
        super().__init__()
        self.in_main = False
        self.markdown = []
        self.links = []
        self.stack = []
        self.captured = {'name': [], 'role': [], 'lead': []}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if not self.in_main:
            return
        capture = ('name' if attrs.get('id') == 'name' else
                   'lead' if attrs.get('id') == 'research-summary' else
                   next((key for key in ('role', 'lead')
                         if key in attrs.get('class', '').split()), None))
        if tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.stack.append((tag, capture, attrs))
        if tag in ('h1', 'h2', 'h3'):
            self.markdown.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag in ('p', 'address'):
            self.markdown.append('\n\n')
        elif tag == 'li':
            self.markdown.append('\n\n' if 'paper' in attrs.get('class', '').split() else '\n\n- ')
        elif tag == 'br':
            self.markdown.append('\n')
        elif tag == 'a':
            self.markdown.append('[')
            self.links.append({'url': urljoin(SITE, attrs.get('href', '')), 'text': ''})

    def handle_endtag(self, tag):
        if not self.in_main:
            return
        if tag == 'a' and self.stack:
            self.markdown.append('](' + urljoin(SITE, self.stack[-1][2].get('href', '')) + ') ')
        elif tag == 'strong' and any(item[0] == 'li' for item in self.stack):
            self.markdown.append(' — ')
        elif tag in ('p', 'h1', 'h2', 'h3', 'li', 'address', 'section', 'div'):
            self.markdown.append('\n\n')
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        if tag == 'main':
            self.in_main = False

    def handle_data(self, value):
        if not self.in_main:
            return
        value = re.sub(r'\s+', ' ', value)
        self.markdown.append(value)
        for _, capture, _ in self.stack:
            if capture:
                self.captured[capture].append(value)
        if self.stack and self.stack[-1][0] == 'a':
            self.links[-1]['text'] += value


def profile_outputs(homepage, data):
    parser = ProfileParser()
    parser.feed(homepage)
    captured = {key: ' '.join(''.join(value).split())
                for key, value in parser.captured.items()}
    if not all(captured.values()):
        raise ValueError('Homepage must retain name, role, and lead markers for profile data.')
    profile = {
        '@context': 'https://schema.org',
        '@type': 'Person',
        '@id': SITE + '#person',
        'name': captured['name'],
        'alternateName': data.get('alternate_names', []),
        'url': SITE,
        'image': urljoin(SITE, data['portrait']),
        'jobTitle': captured['role'],
        'description': captured['lead'],
        'sameAs': list(dict.fromkeys(item['url'] for item in data['links']
                      if urlsplit(item['url']).scheme in ('https', 'http'))),
        'affiliation': [{'@type': 'Organization', **item} for item in data['affiliations']],
        'worksFor': {'@type': 'Organization', **data['employer']},
    }
    email = next((link['url'][7:] for link in parser.links
                  if link['url'].startswith('mailto:')), None)
    if email:
        profile['email'] = email
    markdown = ''.join(parser.markdown)
    markdown = '\n'.join(line.strip() for line in markdown.splitlines())
    markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip() + '\n'
    markdown = re.sub(r' +', ' ', markdown)
    markdown = markdown.replace('</', '&lt;/')
    llms = f'''# {captured['name']}

> {captured['role']}. {captured['lead']}

This is the personal academic website of {captured['name']}. The files below
are generated from the visible homepage and its source bibliography.
Publication status and author order are preserved; accepted papers may be
listed before publication.

## Profile
- [Homepage]({SITE}): Research, affiliations, software, teaching, and contact.
- [Profile in Markdown]({SITE}profile.md): Full readable homepage content.
- [Structured profile]({SITE}profile.json): Complete profile, research, teaching, contact, and Schema.org Person data.

## Publications
- [Full publication list]({SITE}publications.html): All papers, by year.
- [Publications in JSON]({SITE}publications.json): Titles, authors, years, venues, status, links, and source BibTeX.
- [BibTeX bibliography]({SITE}publications.bib): Authoritative source entries.
- [Last bibliography source check]({SITE}bibliography-status.json): Check date and source checksum.

## Courses
- [Full course archive]({SITE}teaching.html): Courses and guest lectures by year.
- [Courses in JSON]({SITE}teaching.json): Complete teaching records from the editable profile data.
- [Courses in Markdown]({SITE}teaching.md): Readable course archive with links.

## Primary sources
- [Institutional profile](https://home.lmf.cnrs.fr/MatthiasFuegger/)
- [Institutional bibliography](https://home.lmf.cnrs.fr/downloads/MatthiasFuegger/mf.bib)
'''
    return profile, markdown, llms


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def structured_script(value):
    # Keep arbitrary publication titles from ending an HTML script element.
    return json_text(value).rstrip().replace('<', '\\u003c')
