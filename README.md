# Matthias Függer — academic homepage

A static GitHub Pages website. Visitors receive complete HTML without JavaScript,
a framework, external web fonts, or a client-side rendering step.

## Editing the website

**For routine updates, open [`content/`](content/).** This is the editable source.
The website is generated into `build/`, which is ignored by Git and does not appear
in the GitHub file list. You do not edit the published HTML or JSON exports.

| I want to change… | Open this source | Edit this part |
| --- | --- | --- |
| Courses and lectures | [content/profile.json](content/profile.json) | `teaching.courses` |
| Biography and research | [content/profile.json](content/profile.json) | `description`, `research` |
| Contact and profile links | [content/profile.json](content/profile.json) | `email`, `contact`, `links` |
| Portrait | [content/profile.json](content/profile.json) | `portrait`, `portrait_dimensions` |
| Homepage paper selection and order | [content/selected-publications.txt](content/selected-publications.txt) | One bibliography key per line |
| Privacy and legal notices | [content/notices.json](content/notices.json) | Notice text, hosting details, review date |
| Full bibliography | [content/publications.bib](content/publications.bib) | Usually refreshed automatically from the institutional bibliography |
| Bibliography refresh settings | [content/bibliography-source.json](content/bibliography-source.json) | Source URL and schedule toggle |
| Colors, typography, spacing | [assets/academic.css](assets/academic.css) | CSS |
| Page layout or headings | [templates/](templates/) | HTML templates |

**On GitHub:** open the source file above → click the pencil → make your edit →
commit to `main`. GitHub Actions builds, checks, and publishes the website for you.
No local build command is needed when editing on GitHub.

### What the folders mean

- **`content/`: edit here.** All routine text and course updates, bibliography,
  selected papers, and notice data. Its README includes a course example.
- **`assets/`: images and CSS.** Presentation styles stay separate from content.
- **`templates/`: layouts.** Change these when changing page structure.
- **`scripts/`: build code.** No changes needed for normal content updates.
- **`build/`: generated website.** Created locally or by GitHub Actions; ignored by
  Git. Files here are overwritten on the next build. Public URLs remain unchanged.
- **`habil/` and `projects/`: archived page sources.** Their text can be edited
  directly. The build adds the shared footer to the copies in `build/`.

The portrait is displayed on the right at its natural aspect ratio, without cropping.
To replace it, set `portrait` and `portrait_dimensions` (the image’s actual pixel
width and height) in `content/profile.json`. Its display size is controlled in CSS.
The Privacy and Legal notice footer links appear on every HTML page, including
the archived habilitation and SIC pages. The build updates only the deployment
copies of those archived pages. Their Bootstrap stylesheet is served locally.
Notices reuse the name, email, and professional address from `content/profile.json`.
Maintain their text and review date in `content/notices.json`; check them whenever
hosting, contact handling, cookies, or embedded services change. The site checks
reject external page assets that would contradict the notice. Outbound hyperlinks
are allowed. `content/bibliography-status.json` is maintained automatically and
records the last successful bibliography check and its checksum.

The homepage Research section uses `description` for the current focus and
`research.description` for the additional research areas. Group roles remain in
`research.groups`; the visible text and machine-readable exports share this source.
Use `research.description_links` for inline links in the current-focus paragraph:
each `label` must match a phrase in `description` exactly once, with its target
stored in `url`. Keep the description as plain text; the build adds the links.

The compact thesis entries follow the selected publications. Edit the habilitation
in `habilitation`. The PhD entry uses `doctoral_thesis.bibliography_key` to derive
its title, year, and PDF link from `content/publications.bib`; its display institution and
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
**Do not add counts or positions.** The build calculates `numberOfItems` and
`position` automatically. The same course source generates the visible pages,
JSON-LD metadata, and AI-readable exports.

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
website → Run workflow**. It creates `build/` and deploys that directory through GitHub Pages. Generated
pages are never committed back to the repository; only bibliography refreshes
and their check records are saved.

The weekly run downloads the canonical personal bibliography at:
https://home.lmf.cnrs.fr/downloads/MatthiasFuegger/mf.bib

Maintain that source for routine bibliography updates. The build preserves author
order and publication status, including accepted/to-appear notes. An invalid or
empty download, a loss of more than 20% of entries, or missing selected-paper keys
stops the build before deployment. The previously deployed website remains live.
Successful refreshes commit a dated check record even when the papers did not
change, keeping the scheduled workflow active during quiet publication periods.

If you prefer to maintain the bibliography exclusively in this repository, set
`refresh_on_schedule` to `false` in `content/bibliography-source.json`. Then edit
`content/publications.bib` on GitHub; weekly runs rebuild without replacing it. Manual
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
python3 -m http.server 8765 --bind 127.0.0.1 --directory build
```

Open http://127.0.0.1:8765/. The preview serves `build/`; edit `content/`,
then rerun the build and check commands to update it. To fetch the institutional bibliography explicitly:

```sh
python3 scripts/build_site.py --refresh
```

`build_publications.py` remains a compatibility entry point for the same build.

## Search engines and AI readers

The build generates these public files inside `build/` from the same source data:

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

## Course recording previews

To add a recording, add an optional `recording` object to the corresponding
course in [content/profile.json](content/profile.json), under `teaching.courses`.
For example:

```json
"recording": {
  "title": "Lecture 1 — Introduction",
  "url": "https://www.youtube.com/watch?v=AeclUJJ-wwY&list=PLLGPEjQmmA7DSruH84oHIanAXo44Bf4sI",
  "thumbnail": "assets/course-compbioeng-2025.jpg",
  "width": 1280,
  "height": 720
}
```

The image path points to a file in `assets/`; width and height are its actual pixel
dimensions. The course archive shows the preview on that course. The homepage
also shows the newest course with a recording, with its year clearly labelled.
The full playlist link is preserved. The preview is a local image and a normal
link: YouTube is contacted only after a visitor follows it. Recording metadata
and links are included in the profile/course JSON and Markdown exports.

The course-section YouTube channel link is edited once in `teaching.channel`
in the editable profile: `name` is the channel name and `url` its address.
It appears on the homepage and course archive with a local YouTube icon, and
is exported in the profile/course JSON and Markdown.
