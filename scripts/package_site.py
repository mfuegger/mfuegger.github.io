#!/usr/bin/env python3
"""Copy editable static sources into build/ alongside generated pages."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build'


def copy_static_sources():
    # build/ contains generated files only; every build starts from the sources.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for name in ('.nojekyll', 'robots.txt', 'sitemap.xml', 'assets', 'habil', 'projects', 'css'):
        source = ROOT / name
        destination = OUTPUT / name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


if __name__ == '__main__':
    raise SystemExit('Run python3 scripts/build_site.py; it creates the complete build/ directory.')
