#!/usr/bin/env python3
"""Render the existing public BibTeX as static, readable HTML.
Run from any directory: python3 scripts/build_publications.py
Dependencies: bibtexparser==2.0.1, pylatexenc==2.11
"""
from pathlib import Path
from html import escape
from urllib.parse import quote, urlsplit
import re
import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ['cravo2025mobspy', 'PPHPCFNK24:nar', 'BFN26:isola', 'FNS21:jacm']
latex = LatexNodes2Text()

def text(value):
    return ' '.join(latex.latex_to_text(value).split())

def safe_url(value):
    value = value.strip()
    if urlsplit(value).scheme not in ('https', 'http'):
        raise ValueError(f'Unsupported bibliography URL: {value}')
    return escape(value, quote=True)

def fields(entry):
    return {key: field.value for key, field in entry.fields_dict.items()}

def authors(value):
    names = []
    for raw in re.split(r'\s+and\s+', value):
        name = text(raw)
        parts = [p.strip() for p in name.split(',')]
        if len(parts) == 2:
            name = parts[1] + ' ' + parts[0]
        elif len(parts) == 3:
            name = parts[2] + ' ' + parts[0] + ', ' + parts[1]
        name = name.replace('Matthias Fugger', 'Matthias Függer')
        names.append(name)
    return ', '.join(names)

def paper(entry, citation=False):
    f = fields(entry)
    title = escape(text(f['title']))
    primary = f.get('doi')
    primary = 'https://doi.org/' + primary.removeprefix('https://doi.org/') if primary else f.get('url', f.get('pdf', ''))
    title_link = f'<a href="{safe_url(primary)}">{title}</a>' if primary else title
    venue = text(f.get('journal', f.get('booktitle', f.get('school', ''))))
    if not venue:
        venue = {'phdthesis': 'Doctoral thesis', 'techreport': 'Technical report', 'misc': ''}.get(entry.entry_type, '')
    note = text(f.get('note', ''))
    pieces = [escape(venue)] if venue else []
    pieces.append(escape(text(f['year'])))
    metadata = ' · '.join(pieces)
    if note:
        metadata += ' <span class="paper-note">· ' + escape(note.rstrip('.')) + '</span>'
    links = []
    seen = set()
    for key, label in [('pdf', 'PDF'), ('doi', 'DOI'), ('arxiv_long', 'Preprint'), ('biorxiv_long', 'Preprint'), ('hal', 'HAL')]:
        value = f.get(key)
        if not value:
            continue
        if key == 'doi':
            value = 'https://doi.org/' + value.removeprefix('https://doi.org/')
        if value in seen:
            continue
        seen.add(value)
        if label == 'Preprint':
            host = urlsplit(value).hostname or ''
            label = 'bioRxiv' if host.endswith('biorxiv.org') else 'arXiv' if host.endswith('arxiv.org') else 'Preprint'
        links.append(f'<a href="{safe_url(value)}">{label}</a>')
    if not links and f.get('url'):
        links.append(f'<a href="{safe_url(f["url"])}">Publication</a>')
    if citation:
        raw = entry.raw or ''
        links.append('<details class="citation"><summary>BibTeX</summary><pre>' + escape(raw) + '</pre></details>')
    return f'<li class="paper" id="paper-{quote(entry.key, safe="")}"><h3 class="paper-title">{title_link}</h3><p class="authors">{escape(authors(f.get("author", "")))}</p><p class="venue">{metadata}</p><div class="paper-links">{"".join(links)}</div></li>'

library = bibtexparser.parse_file(str(ROOT / 'publications.bib'))
if library.failed_blocks:
    raise ValueError('Bibliography contains unparsed blocks; fix source before rendering.')
entries = library.entries
for entry in entries:
    f = fields(entry)
    if not all(f.get(key) for key in ('title', 'year', 'author')):
        raise ValueError(f'Missing required bibliography fields: {entry.key}')
by_key = {entry.key: entry for entry in entries}
selected = '<ul class="papers">' + ''.join(paper(by_key[key]) for key in SELECTED) + '</ul>'
index = ROOT / 'index.html'
s = index.read_text()
s = re.sub(r'<!-- SELECTED_START -->.*?<!-- SELECTED_END -->', '<!-- SELECTED_START -->\n' + selected + '\n<!-- SELECTED_END -->', s, flags=re.S)
index.write_text(s)
years = sorted({int(entry['year']) for entry in entries}, reverse=True)
sections = []
for year in years:
    papers = sorted((entry for entry in entries if int(entry['year']) == year), key=lambda entry: text(entry['title']).casefold())
    sections.append(f'<section class="year-section" id="year-{year}" aria-labelledby="heading-{year}"><h2 id="heading-{year}">{year}</h2><ul class="papers">' + ''.join(paper(entry, citation=True) for entry in papers) + '</ul></section>')
nav = ''.join(f'<a href="#year-{year}">{year}</a>' for year in years)
head = s.split('</head>')[0].replace('<title>Matthias Függer — CNRS · LMF</title>', '<title>Publications — Matthias Függer</title>').replace('href="https://mfuegger.github.io/"', 'href="https://mfuegger.github.io/publications.html"').replace('Matthias Függer, Research Director at CNRS and Laboratoire Méthodes Formelles. Research in microbial systems, distributed computing, and digital circuits.', 'Publications by Matthias Függer and collaborators, with papers, preprints, and BibTeX citations.') + '</head>'
page = head + f'''\n<body><a class="skip" href="#main">Skip to content</a><div class="wrap"><header class="site-header"><a class="wordmark" href="./">Matthias Függer</a><nav aria-label="Main navigation"><a href="./#research">Research</a><a href="publications.html" aria-current="page">Publications</a><a href="./#software">Software</a><a href="./#teaching">Teaching</a><a href="./#contact">Contact</a></nav></header><main id="main"><div class="page-intro"><h1>Publications</h1><p><a href="publications.bib" download>Download bibliography (BibTeX)</a></p><nav class="year-nav" aria-label="Publication years">{nav}</nav></div>{''.join(sections)}</main><footer class="footer"><a href="./">Matthias Függer · CNRS / LMF</a><a href="#main">Back to top</a></footer></div></body></html>'''
(ROOT / 'publications.html').write_text(page)
print(f'Rendered {len(entries)} publications across {len(years)} years; {len(SELECTED)} selected papers.')
