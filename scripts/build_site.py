#!/usr/bin/env python3
"""Build the static website from content/profile.json and publications.bib.
Run from any directory: python3 scripts/build_site.py
Dependencies: bibtexparser==2.0.1, pylatexenc==2.11
"""
from pathlib import Path
from html import escape
from urllib.parse import quote, urlsplit
from string import Template
from urllib.request import Request, urlopen
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import unicodedata
import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text
from build_agent_data import json_text, profile_outputs, structured_script

ROOT = Path(__file__).resolve().parents[1]
latex = LatexNodes2Text()


def render(template_name, **values):
    """HTML layouts live in templates/, separately from bibliography logic."""
    template = (ROOT / 'templates' / template_name).read_text(encoding='utf-8')
    return Template(template).substitute(values).rstrip()


def nested(html, spaces):
    """Indent markup while keeping the copyable BibTeX exactly as supplied."""
    parts = re.split(r'(<pre>.*?</pre>)', html, flags=re.S)
    return ''.join(
        part if i % 2 else re.sub(r'(?m)^[ \t]+$', '', part.replace('\n', '\n' + ' ' * spaces))
        for i, part in enumerate(parts)
    )


def link(value, label):
    """Profile links may also be relative paths or email addresses."""
    if urlsplit(value).scheme not in ('', 'https', 'http', 'mailto') or value.startswith('//'):
        raise ValueError(f'Unsupported profile URL: {value}')
    return f'<a href="{escape(value, quote=True)}">{escape(label)}</a>'


def common_layout(data, page='home'):
    return {
        'header': nested(render(
            'header.html', name=escape(data['name']),
            home_current=' aria-current="page"' if page == 'home' else '',
            publications_current=' aria-current="page"' if page == 'publications' else '',
            teaching_current=' aria-current="page"' if page == 'teaching' else '',
            anchor_prefix='' if page == 'home' else './',
        ), 6),
        'footer': nested(render('footer.html', name=escape(data['name']), affiliation_label=escape(data['affiliation_label']), root_prefix='.'), 6),
    }


def head(data, structured, page='home', notice=None):
    titles = {
        'home': data['name'] + ' — ' + data['affiliation_label'].replace(' / ', ' · '),
        'publications': 'Publications — ' + data['name'],
        'teaching': 'Courses and lectures — ' + data['name'],
    }
    descriptions = {
        'home': data['name'] + ', ' + data['role'] + '. ' + data['description'],
        'publications': 'Publications by ' + data['name'] + ' and collaborators, with papers, preprints, and BibTeX citations.',
        'teaching': 'Courses and lectures by ' + data['name'] + ': courses and guest lectures, with the complete archive by year.',
    }
    if notice:
        titles[page] = notice['title'] + ' — ' + data['name']
        descriptions[page] = notice['description']
    alternatives = [
        ('application/json', 'publications.json' if page == 'publications' else 'profile.json', 'Structured data'),
        ('application/x-bibtex', 'publications.bib', 'BibTeX bibliography') if page == 'publications' else
        ('text/markdown', 'profile.md', 'Profile in Markdown'),
    ]
    if page == 'teaching':
        alternatives = [('application/json', 'teaching.json', 'Course data'),
                        ('text/markdown', 'teaching.md', 'Courses in Markdown')]
    if notice:
        alternatives = [('application/json', 'notices.json', 'Site notices data'),
                        ('text/markdown', page + '.md', notice['title'] + ' in Markdown')]
    alternate_links = '\n'.join(
        f'<link rel="alternate" type="{kind}" href="{path}" title="{title}" />'
        for kind, path, title in alternatives
    )
    return nested(render(
        'head.html',
        name=escape(data['name']),
        portrait_url='https://mfuegger.github.io/' + escape(data['portrait'], quote=True),
        page_title=escape(titles[page]),
        stylesheet_url='assets/academic.css?v=' + hashlib.sha256((ROOT / 'assets/academic.css').read_bytes()).hexdigest()[:12],
        description=escape(descriptions[page]),
        canonical='https://mfuegger.github.io/' + (page + '.html' if page != 'home' else ''),
        alternates=nested(alternate_links, 2),
        structured_data=nested(structured_script(structured), 4),
    ), 2)


def ordered_courses(data):
    return sorted(data['teaching']['courses'], key=lambda course: int(course['year']), reverse=True)


def course_id(course):
    name = unicodedata.normalize('NFKD', course['name']).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', name).strip('-')
    term = course.get("term", "").lower()
    return f'course-{course["year"]}-' + (term + '-' if term else '') + slug


def course_metadata(course, include_year=True):
    date = ' '.join(str(value) for value in
                    (course.get('term', ''), course['year'] if include_year else '') if value)
    return ' · '.join(value for value in (date, course['details']) if value)


def notice_outputs(data):
    notices = json.loads((ROOT / 'content/notices.json').read_text(encoding='utf-8'))
    hosting = notices['hosting']
    context = {'name': data['name'], 'hosting_name': hosting['name'],
               'hosting_service': hosting['service'],
               'hosting_address': ', '.join(hosting['address'])}
    outputs = {}
    exported_pages = []
    for notice in notices['pages']:
        slug = notice['slug']
        sections = []
        exported_sections = []
        markdown = [f'# {notice["title"]} — {data["name"]}\n\n{notice["intro"]}\n\n'
                    f'Last reviewed: {notices["last_reviewed"]}\n\n'
                    f'## {notice["contact_heading"]}\n\n{data["name"]}\n\n'
                    + '\n'.join(data['contact']['address'])
                    + f'\n\nEmail: {data["email"]}\n']
        for section in notice['sections']:
            paragraphs = [Template(value).substitute(context) for value in section['paragraphs']]
            links = [dict(label=item['label'], url=hosting[item['hosting_key']] if 'hosting_key' in item else item['url'])
                     for item in section.get('links', [])]
            exported_sections.append(dict(section, paragraphs=paragraphs, links=[
                dict(item, url=item['url'] if urlsplit(item['url']).scheme else 'https://mfuegger.github.io/' + item['url'])
                for item in links]))
            sections.append(render(
                'notice-section.html', id=escape(section['id'], quote=True),
                heading=escape(section['heading']),
                paragraphs=nested('\n'.join('<p>' + escape(value) + '</p>' for value in paragraphs), 2),
                links='<p class="paper-links">' + ' '.join(link(item['url'], item['label']) for item in links) + '</p>' if links else '',
            ))
            markdown.append('\n## ' + section['heading'] + '\n\n' + '\n\n'.join(paragraphs) + '\n')
            for item in links:
                absolute = item['url'] if urlsplit(item['url']).scheme else 'https://mfuegger.github.io/' + item['url']
                markdown.append(f'\n[{item["label"]}]({absolute})\n')
        structured = {'@context': 'https://schema.org', '@type': 'WebPage',
                      'name': notice['title'] + ' — ' + data['name'],
                      'url': 'https://mfuegger.github.io/' + slug + '.html',
                      'dateModified': notices['last_reviewed'],
                      'about': {'@id': 'https://mfuegger.github.io/#person'}}
        outputs[slug + '.html'] = render(
            'notice.html', head=head(data, structured, page=slug, notice=notice),
            **common_layout(data, page=slug), title=escape(notice['title']),
            intro=escape(notice['intro']), last_reviewed=escape(notices['last_reviewed']),
            contact_heading=escape(notice['contact_heading']), name=escape(data['name']),
            address='<br />'.join(escape(value) for value in data['contact']['address']),
            email=link('mailto:' + data['email'], data['email']),
            sections=nested('\n'.join(sections), 8),
        ) + '\n'
        outputs[slug + '.md'] = ''.join(markdown)
        exported_pages.append(dict(notice, url=structured['url'], sections=exported_sections))
    outputs['notices.json'] = json_text({
        'publisher': {'name': data['name'], 'email': data['email'], 'address': data['contact']['address']},
        **notices, 'pages': exported_pages,
    })
    return outputs


def update_legacy_footers(data):
    footer = render('footer.html', name=escape(data['name']),
                    affiliation_label=escape(data['affiliation_label']), root_prefix='..')
    stylesheet = '../assets/legacy-footer.css?v=' + hashlib.sha256((ROOT / 'assets/legacy-footer.css').read_bytes()).hexdigest()[:12]
    for name in ('habil/index.html', 'projects/sic.html'):
        path = ROOT / name
        markup = path.read_text(encoding='utf-8')
        markup = re.sub(r'<!-- Site footer -->.*?<!-- End site footer -->',
                        '<!-- Site footer -->\n' + footer + '\n<!-- End site footer -->', markup, flags=re.S)
        markup = re.sub(r'<!-- Footer stylesheet -->.*?<!-- End footer stylesheet -->',
                        '<!-- Footer stylesheet -->\n<link rel="stylesheet" href="' + stylesheet + '" />\n<!-- End footer stylesheet -->',
                        markup, flags=re.S)
        path.write_text(markup, encoding='utf-8')


def teaching_outputs(data):
    courses = ordered_courses(data)
    ids = [course_id(course) for course in courses]
    if len(ids) != len(set(ids)):
        raise ValueError('Teaching records contain duplicate course/year/term combinations.')
    years = sorted({int(course['year']) for course in courses}, reverse=True)
    sections = []
    markdown = [f'# Courses and lectures — {data["name"]}\n\nCourses and guest lectures, listed by year.\n']
    for year in years:
        rendered = []
        markdown.append(f'\n## {year}\n')
        for course in (item for item in courses if int(item['year']) == year):
            rendered.append(render(
                'teaching-course.html', id=course_id(course), name=escape(course['name']),
                details=escape(course_metadata(course, include_year=False)),
                course_link='<p class="paper-links">' + link(course['url'], 'Course website') + '</p>' if course.get('url') else '',
            ))
            markdown.append(f'\n### {course["name"]}\n\n{course_metadata(course, include_year=False)}\n')
            if course.get('url'):
                markdown.append(f'\n[Course website]({course["url"]})\n')
        sections.append(render('teaching-year.html', year=year, courses=nested('\n'.join(rendered), 4)))
    structured = {
        '@context': 'https://schema.org', '@type': 'CollectionPage',
        'name': 'Courses and lectures — ' + data['name'],
        'url': 'https://mfuegger.github.io/teaching.html',
        'about': {'@id': 'https://mfuegger.github.io/#person'},
        'mainEntity': {
            '@type': 'ItemList', 'numberOfItems': len(courses),
            'itemListElement': [
                {'@type': 'ListItem', 'position': i + 1, 'name': course['name'],
                 'description': course_metadata(course),
                 'url': 'https://mfuegger.github.io/teaching.html#' + course_id(course)}
                for i, course in enumerate(courses)
            ],
        },
    }
    page = render(
        'teaching.html', head=head(data, structured, page='teaching'),
        **common_layout(data, page='teaching'),
        year_links=nested('\n'.join(f'<a href="#year-{year}">{year}</a>' for year in years), 12),
        sections=nested('\n'.join(sections), 8),
    ) + '\n'
    return page, {'teacher': data['name'], 'courses': courses, 'schemaOrg': structured}, ''.join(markdown)


def homepage(data, selected, structured, doctoral):
    description = escape(data['description'])
    for item in data['research'].get('description_links', []):
        if not item['label'] or data['description'].count(item['label']) != 1:
            raise ValueError('Each research link label must occur exactly once in the description.')
        description = description.replace(escape(item['label']), link(item['url'], item['label']), 1)
    affiliations = data['affiliations']
    affiliation_html = link(affiliations[0]['url'], affiliations[0]['name']) + '<br />' + ' · '.join(escape(item['name']) for item in affiliations[1:])
    group_roles = 'I am ' + ' and '.join(escape(group['role']) + ' of the ' + link(group['url'], group['name']) for group in data['research']['groups']) + ' ' + escape(data['research']['group_context']) + '.'
    courses = '\n'.join(render('course.html', name=link('teaching.html#' + course_id(course), course['name']),
                              details=escape(course_metadata(course)))
                        for course in ordered_courses(data)[:2])
    values = {
        'head': head(data, structured),
        **common_layout(data),
        'name': escape(data['name']), 'role': escape(data['role']),
        'description': description, 'portrait': escape(data['portrait'], quote=True),
        'affiliations': affiliation_html,
        'quick_links': nested('\n'.join([link('mailto:' + data['email'], 'Email')] + [link(item['url'], item['label']) for item in data['links']]), 14),
        'research_description': escape(data['research']['description']),
        'group_roles': group_roles,
        'selected_papers': nested(selected, 10),
        'courses': nested(courses, 12),
        'email': escape(data['email'], quote=True), 'contact_invitation': escape(data['contact']['invitation']),
        'address': '<br />'.join(escape(line) for line in data['contact']['address']),
    }
    values.update({'software_' + key: escape(str(value), quote=True) for key, value in data['software'].items()})
    values.update({'thesis_' + key: escape(str(value), quote=True) for key, value in data['habilitation'].items()})
    values.update({'doctoral_' + key: escape(str(value), quote=True) for key, value in doctoral.items()})
    return render('index.html', **values) + '\n'


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
        # Encode trailing whitespace so Git stays clean while copied BibTeX
        # remains byte-for-byte equivalent after HTML entity decoding.
        citation = re.sub(r'[ \t]+(?=\n|$)',
                          lambda match: ''.join('&#32;' if c == ' ' else '&#9;' for c in match[0]),
                          escape(raw))
        links.append(render('citation.html', bibtex=citation))
    return render(
        'paper.html',
        key=escape(entry.key, quote=True),
        title_link=title_link,
        authors=escape(authors(f.get('author', ''))),
        metadata=metadata,
        links=nested('\n'.join(links), 4),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Download the configured source bibliography before building.')
    parser.add_argument('--refresh-if-enabled', action='store_true', help='Refresh only when bibliography-source.json enables scheduled refreshes.')
    args = parser.parse_args()
    source_config = json.loads((ROOT / 'bibliography-source.json').read_text(encoding='utf-8'))
    bibliography = (ROOT / 'publications.bib').read_text(encoding='utf-8')
    refresh = args.refresh or (args.refresh_if_enabled and source_config['refresh_on_schedule'])
    if refresh:
        url = source_config['url']
        if urlsplit(url).scheme != 'https':
            raise ValueError('The bibliography source must use HTTPS.')
        request = Request(url, headers={'User-Agent': 'mfuegger.github.io bibliography refresh'})
        with urlopen(request, timeout=30) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError('Downloaded bibliography exceeds 2 MB.')
        bibliography = data.decode('utf-8')
    library = bibtexparser.parse_string(bibliography)
    if library.failed_blocks:
        raise ValueError('Bibliography contains unparsed blocks; fix source before rendering.')
    entries = library.entries
    if not entries:
        raise ValueError('Bibliography is empty.')
    if refresh:
        previous = bibtexparser.parse_file(str(ROOT / 'publications.bib')).entries
        if len(entries) < 0.8 * len(previous):
            raise ValueError('Source lost over 20% of entries; review before replacing the bibliography.')
    for entry in entries:
        f = fields(entry)
        if not all(f.get(key) for key in ('title', 'year', 'author')):
            raise ValueError(f'Missing required bibliography fields: {entry.key}')
    by_key = {entry.key: entry for entry in entries}
    if len(by_key) != len(entries):
        raise ValueError('Bibliography contains duplicate entry keys.')

    selected_keys = [
        line.strip()
        for line in (ROOT / 'selected-publications.txt').read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    ]
    if len(set(selected_keys)) != len(selected_keys):
        raise ValueError('Selected-publications list contains duplicate keys.')
    missing = set(selected_keys) - by_key.keys()
    if missing:
        raise ValueError(f'Selected paper keys missing from bibliography: {sorted(missing)}')

    selected_papers = '\n'.join(paper(by_key[key]) for key in selected_keys)
    selected = '<ul class="papers">\n  ' + nested(selected_papers, 2) + '\n</ul>'
    data = json.loads((ROOT / 'content/profile.json').read_text(encoding='utf-8'))
    doctoral_config = data['doctoral_thesis']
    doctoral_entry = by_key[doctoral_config['bibliography_key']]
    if doctoral_entry.entry_type != 'phdthesis':
        raise ValueError('The doctoral thesis must reference a PhD thesis bibliography entry.')
    doctoral_fields = fields(doctoral_entry)
    doctoral = {
        'bibliography_key': doctoral_entry.key,
        'title': text(doctoral_fields['title']),
        'institution': doctoral_config['institution'],
        'year': int(doctoral_fields['year']),
        'pdf_url': doctoral_fields['pdf'].strip(),
        'details_url': doctoral_config['details_url'].strip(),
    }
    if any(urlsplit(doctoral[key]).scheme not in ('https', 'http')
           for key in ('pdf_url', 'details_url')):
        raise ValueError('Doctoral thesis links must use HTTPS or HTTP.')
    initial_homepage = homepage(data, selected, {}, doctoral)
    profile, markdown, llms = profile_outputs(initial_homepage, data)
    profile_page = {
        '@context': 'https://schema.org', '@type': 'ProfilePage',
        'url': 'https://mfuegger.github.io/', 'mainEntity': profile,
    }
    rendered_homepage = homepage(data, selected, profile_page, doctoral)
    years = sorted({int(entry['year']) for entry in entries}, reverse=True)
    sections = []
    for year in years:
        papers = sorted(
            (entry for entry in entries if int(entry['year']) == year),
            key=lambda entry: text(entry['title']).casefold(),
        )
        sections.append(render(
            'year.html', year=year,
            papers=nested('\n'.join(paper(entry, citation=True) for entry in papers), 4),
        ))
    year_links = '\n'.join(f'<a href="#year-{year}">{year}</a>' for year in years)
    records = []
    scholarly_articles = []
    for entry in sorted(entries, key=lambda e: (-int(e['year']), text(e['title']).casefold())):
        f = fields(entry)
        venue = text(f.get('journal', f.get('booktitle', f.get('school', ''))))
        record = {
            'key': entry.key,
            'type': entry.entry_type,
            'title': text(f['title']),
            'authors': [authors(raw) for raw in re.split(r'\s+and\s+', f['author'])],
            'year': int(f['year']),
            'venue': venue,
            'note': text(f.get('note', '')),
            'doi': f.get('doi', ''),
            'links': {key: f[key] for key in ('url', 'pdf', 'hal', 'arxiv_long', 'biorxiv_long') if f.get(key)},
            'bibtex': entry.raw,
        }
        records.append(record)
        article = {
            '@type': 'Thesis' if entry.entry_type in ('phdthesis', 'mastersthesis') else 'ScholarlyArticle',
            '@id': 'https://mfuegger.github.io/publications.html#paper-' + quote(entry.key, safe=''),
            'name': record['title'],
            'author': [{'@type': 'Person', 'name': authors(raw)} for raw in re.split(r'\s+and\s+', f['author'])],
            'description': ' · '.join(str(value) for value in (venue, record['year'], record['note']) if value),
        }
        if record['doi']:
            article['identifier'] = {'@type': 'PropertyValue', 'propertyID': 'DOI', 'value': record['doi']}
            article['sameAs'] = 'https://doi.org/' + record['doi'].removeprefix('https://doi.org/')
        scholarly_articles.append({'@type': 'ListItem', 'position': len(scholarly_articles) + 1, 'item': article})
    structured = {
        '@context': 'https://schema.org', '@type': 'ItemList',
        'name': 'Publications — ' + profile['name'],
        'numberOfItems': len(records), 'itemListElement': scholarly_articles,
    }
    page = render(
        'publications.html',
        year_links=nested(year_links, 12),
        sections=nested('\n'.join(sections), 8),
        head=head(data, structured, page='publications'),
        **common_layout(data, page='publications'),
    ) + '\n'

    teaching_page, teaching_data, teaching_markdown = teaching_outputs(data)
    notices = notice_outputs(data)
    # Render and validate everything before writing the outputs.
    (ROOT / 'index.html').write_text(rendered_homepage, encoding='utf-8')
    (ROOT / 'publications.html').write_text(page, encoding='utf-8')
    (ROOT / 'teaching.html').write_text(teaching_page, encoding='utf-8')
    (ROOT / 'teaching.json').write_text(json_text(teaching_data), encoding='utf-8')
    (ROOT / 'teaching.md').write_text(teaching_markdown, encoding='utf-8')
    (ROOT / 'profile.json').write_text(json_text({
        'url': 'https://mfuegger.github.io/', **data, 'schemaOrg': profile,
        'theses': [dict(label='Habilitation thesis', **data['habilitation']),
                   dict(label='PhD thesis', **doctoral)],
    }), encoding='utf-8')
    (ROOT / 'profile.md').write_text(markdown, encoding='utf-8')
    (ROOT / 'llms.txt').write_text(llms, encoding='utf-8')
    (ROOT / 'publications.json').write_text(json_text({
        'profile': profile['@id'], 'source': source_config['url'],
        'count': len(records), 'publications': records,
    }), encoding='utf-8')
    for name, contents in notices.items():
        (ROOT / name).write_text(contents, encoding='utf-8')
    update_legacy_footers(data)
    if refresh:
        (ROOT / 'publications.bib').write_text(bibliography, encoding='utf-8')
        (ROOT / 'bibliography-status.json').write_text(json_text({
            'source': source_config['url'],
            'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'entries': len(entries),
            'source_sha256': hashlib.sha256(bibliography.encode('utf-8')).hexdigest(),
        }), encoding='utf-8')
    print(f'Rendered {len(entries)} publications across {len(years)} years; {len(selected_keys)} selected papers.')


if __name__ == '__main__':
    main()
