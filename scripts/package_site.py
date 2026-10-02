#!/usr/bin/env python3
"""Copy only public pages and assets into the Pages deployment directory."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '_site'
OUTPUT.mkdir(exist_ok=True)
for name in (
    'index.html', 'publications.html', 'publications.bib', 'publications.json',
    'profile.json', 'profile.md', 'llms.txt', 'robots.txt', 'sitemap.xml',
    'bibliography-status.json', 'teaching.html', 'teaching.json', 'teaching.md',
    '.nojekyll', 'assets', 'habil', 'projects', 'css',
):
    source = ROOT / name
    destination = OUTPUT / name
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
