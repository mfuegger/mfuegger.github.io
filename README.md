# Matthias Függer — academic homepage

A static GitHub Pages website. Visitors receive complete HTML without JavaScript,
a framework, external web fonts, or a client-side rendering step.

## Edit these source files

| Change | File |
| --- | --- |
| Biography, research, affiliations, software, teaching, contact | `content/profile.json` |
| Privacy and legal notices, hosting details, review date | `content/notices.json` |
| Full bibliography | `publications.bib` |
| Homepage paper selection and order | `selected-publications.txt` |
| Colors, typography, spacing, responsive layout | `assets/academic.css` |
| Page layout, navigation, or section headings | `templates/` |
| Bibliography refresh source and schedule toggle | `bibliography-source.json` |

**Do not edit generated `index.html`, `publications.html`, `profile.json`,
`profile.md`, `publications.json`, `teaching.html`, `teaching.json`, `teaching.md`,
`privacy.html`, `legal.html`, `privacy.md`, `legal.md`, `notices.json`, or `llms.txt`.** They are rebuilt from the
source files above. All presentation styles for these pages live in CSS.
The build versions the stylesheet URL from its contents so CSS edits refresh in browsers.
The Privacy and Legal notice footer links appear on every HTML page, including
the archived habilitation and SIC pages. The build updates the marked footer and
footer stylesheet blocks in those archived pages; their remaining content can be
edited directly. The habilitation page uses its original Bootstrap stylesheet,
now served locally, and no longer loads the unused Bootstrap script from a CDN.
Notices reuse the name, email, and professional address from `content/profile.json`.
Maintain their text and review date in `content/notices.json`; check them whenever
hosting, contact handling, cookies, or embedded services change. The site checks
reject external page assets so an unnoticed CDN or embedded script cannot silently
contradict the notice. Outbound hyperlinks are allowed.
`bibliography-status.json` is also generated; it records the last successful
source check and its checksum.

The homepage Research section uses `description` for the current focus and
`research.description` for the additional research areas. Group roles remain in
`research.groups`; the visible text and machine-readable exports share this source.
Use `research.description_links` for inline links in the current-focus paragraph:
each `label` must match a phrase in `description` exactly once, with its target
stored in `url`. Keep the description as plain text; the build adds the links.

The compact thesis entries follow the selected publications. Edit the habilitation
in `habilitation`. The PhD entry uses `doctoral_thesis.bibliography_key` to derive
its title, year, and PDF link from `publications.bib`; its display institution and
repository details link are in `doctoral_thesis`. Both entries are exported in
`profile.json` under `theses` and in `profile.md`.

For example, add a course to `teaching.courses` in `content/profile.json`:

```json
{
  "year": 2026,
  "term": "Winter",
  "name": "Course title",
  "details": "Institution · Collaborators",
  "url": "https://example.org/course"
}
```

Replace the example with accurate information; do not publish placeholder courses.
JSON uses double quotes and requires commas between array entries, without a
trailing comma after the final entry. Edit the source directly on GitHub:
committing to `main` rebuilds, checks, and publishes the site automatically.

The teaching archive lives entirely at `teaching.html`. Its 17 initial records
were imported from the institutional profile's 2015–2025 archive; the three 2026
entries were added from the owner's updates and the TU Wien course catalogue.
Maintain all records under `teaching.courses`; no teaching data is fetched from the institutional
page during builds. `year`, `name`, and `details` are required; `term` and `url` are
optional. Omit `term` when only the year is known. The homepage automatically
shows the two most recent records and links to the full archive. All pages share the same Courses navigation link.
Names and typography were normalized (including Christoph Lenzen and French
accents); dates, collaborators, lecture durations, and course URLs follow the source.

## Automatic bibliography and publishing

`.github/workflows/site.yml` builds after every push to `main`, every Monday at
06:17 UTC, and on demand from GitHub's **Actions → Build and publish academic
website → Run workflow**. It saves regenerated files to the repository and deploys
the public site through GitHub Pages.

The weekly run downloads the canonical personal bibliography at:
https://home.lmf.cnrs.fr/downloads/MatthiasFuegger/mf.bib

Maintain that source for routine bibliography updates. The build preserves author
order and publication status, including accepted/to-appear notes. An invalid or
empty download, a loss of more than 20% of entries, or missing selected-paper keys
stops the build before deployment. The previously deployed website remains live.
Successful refreshes commit a dated check record even when the papers did not
change, keeping the scheduled workflow active during quiet publication periods.

If you prefer to maintain the bibliography exclusively in this repository, set
`refresh_on_schedule` to `false` in `bibliography-source.json`. Then edit
`publications.bib` on GitHub; weekly runs rebuild without replacing it. Manual
**Run workflow** refreshes can still be requested explicitly.

GitHub Pages uses **GitHub Actions** as its publishing source. The workflow
packages public pages and assets only; templates, scripts, and editing data remain
in the GitHub repository. Existing `habil/`, `projects/`, and `css/` URLs are kept.

## Build and preview locally

One-time setup:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r scripts/requirements.txt
```

After editing:

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/. To fetch the institutional bibliography explicitly:

```sh
python3 scripts/build_site.py --refresh
```

`build_publications.py` remains a compatibility entry point for the same build.

## Search engines and AI readers

The build generates all outputs from the same source data:

- Semantic, crawlable HTML with descriptive titles, canonical URLs, and metadata.
- Schema.org `ProfilePage` / `Person` JSON-LD, including ORCID, affiliations, and
  the institutional profile; publication metadata as an `ItemList`.
- `profile.json` containing the complete profile, teaching, research, and contact
  data, plus derived Schema.org data.
- `profile.md` containing the readable homepage content with absolute links.
- `publications.json` containing every paper's title, ordered author list, year,
  venue, status note, identifiers, links, and original BibTeX.
- `teaching.json` and `teaching.md`, the complete teaching archive from the same source.
- `notices.json`, `privacy.md`, and `legal.md`, the site notices from structured source data.
- `llms.txt`, a convenience index for agents; this is an emerging convention,
  not a guarantee that agents or Google will use it.
- `robots.txt` allowing crawlers and announcing `sitemap.xml`.

To improve discovery, link to https://mfuegger.github.io/ from the institutional
profile and ORCID, and verify the site in Google Search Console. Submit
https://mfuegger.github.io/sitemap.xml and request indexing of the homepage and
publication page. Search Console verification needs the owner's Google account;
no verification token is fabricated or included here.

Structured data helps identify the person and content. It does not guarantee a
ranking, rich result, or Google knowledge panel. Knowledge panels are generated
by Google from information across the web.

References:
- https://developers.google.com/search/docs/appearance/structured-data/profile-page
- https://support.google.com/knowledgepanel/answer/9163198
- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

## Content provenance

Initial content verified on 2 October 2026:

- Position, affiliations, group roles, research, teaching and contact:
  https://home.lmf.cnrs.fr/MatthiasFuegger/
- Bibliography: https://home.lmf.cnrs.fr/downloads/MatthiasFuegger/mf.bib
- Existing portrait: https://register.lmf.cnrs.fr/uploads/SSD/avatar-mfuegger.jpg
- ORCID and MobsPy description/repository:
  https://doi.org/10.1371/journal.pcbi.1013024
- Habilitation: existing `habil/index.html` and `habil/thesis.pdf`.

The bibliography is preserved. Displayed author names normalize “Matthias Fugger”
to “Matthias Függer”; other names and author order follow the source. No unverified
telephone number, CV, award, or current vacancy is included.
