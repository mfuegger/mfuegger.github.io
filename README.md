# Matthias Függer — academic homepage

A static website for GitHub Pages. No JavaScript, framework, web fonts, or build step is required to serve it.

## Editing

- Edit biography, research, teaching, and contact text in `index.html`.
- Edit visual styles in `assets/academic.css`.
- Edit bibliography entries in `publications.bib`, then regenerate the publication pages:

```sh
python3 -m pip install -r scripts/requirements.txt
python3 scripts/build_publications.py
```

The generator updates the selected-publication block in `index.html` and the full `publications.html` page. Select papers using the `SELECTED` list in the generator. Keep author order and publication status from the source bibliography.

To preview locally:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/ in a browser. GitHub Pages can serve the repository root directly; the generated HTML is committed alongside the BibTeX source.

## Content sources

Initial content verified on 2 October 2026:

- Position, affiliations, group roles, research, teaching and contact: https://home.lmf.cnrs.fr/MatthiasFuegger/
- Bibliography: https://home.lmf.cnrs.fr/downloads/MatthiasFuegger/mf.bib
- Existing portrait: https://register.lmf.cnrs.fr/uploads/SSD/avatar-mfuegger.jpg
- ORCID and MobsPy description/repository: https://doi.org/10.1371/journal.pcbi.1013024
- Habilitation: existing `habil/index.html` and `habil/thesis.pdf` in this repository.

The imported bibliography is preserved. Displayed author names normalize “Matthias Fugger” to “Matthias Függer”; other names and author order follow the bibliography. Preprint and accepted/to-appear status are retained. No unverified telephone number, CV, award, or current vacancy is included.

The existing `habil/`, `projects/`, and `css/` files are preserved so existing URLs continue to work.
