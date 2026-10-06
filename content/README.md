# Edit website content here

This folder contains the editable sources. For routine updates, start here.
After a commit to `main`, GitHub Actions builds and publishes the site automatically.

| Update | File |
| --- | --- |
| Courses, research, biography, contact, links, portrait | [profile.json](profile.json) |
| Standalone research videos (`videos` list) | [profile.json](profile.json) |
| Selected homepage papers | [selected-publications.txt](selected-publications.txt) |
| Privacy and legal notices | [notices.json](notices.json) |
| Bibliography (normally refreshed from the institutional source) | [publications.bib](publications.bib) |
| Bibliography source and refresh settings | [bibliography-source.json](bibliography-source.json) |

`bibliography-status.json` is updated automatically; do not edit it.

## Add or update a course

Open [profile.json](profile.json), find `"teaching"`, then `"courses"`.
Edit an existing entry or add another object to that array. A course looks like:

```json
{
  "year": 2026,
  "name": "Computational Bioengineering",
  "details": "ENS Paris-Saclay · With Thomas Nowak.",
  "url": "https://compbioeng.biodis.co"
}
```

Use the actual course information. `year`, `name`, and `details` are required.
`url` is optional. Add `"term": "Winter"` or `"term": "Summer"` only when known.
Separate objects with commas; do not add a comma after the final object.

You never enter course counts, list positions, HTML, or Schema.org metadata.
The build calculates them and updates the homepage, course archive, JSON-LD,
and machine-readable exports from this same array.

## Generated files

The published `profile.json`, `teaching.json`, and HTML pages are exports.
They are created in `build/` and are not committed to this repository. The editable
profile is this folder’s `profile.json`, not the JSON export on the live website.

For layout changes, edit [templates/](../templates/) or [assets/academic.css](../assets/academic.css).
Build and check from the repository root with `python3 scripts/build_site.py`
and `python3 scripts/check_site.py`. Preview with
`python3 -m http.server 8765 --bind 127.0.0.1 --directory build`.

## Course recording previews

To add a recording, add an optional `recording` object to the corresponding
course in [profile.json](profile.json), under `teaching.courses`. For example:

```json
"recording": {
  "title": "Full lecture series",
  "url": "https://www.youtube.com/playlist?list=PLLGPEjQmmA7DSruH84oHIanAXo44Bf4sI",
  "thumbnail": "assets/course-compbioeng-2025.jpg",
  "width": 1280,
  "height": 720
}
```

The image path points to a file in `assets/`; width and height are its actual pixel
dimensions. The course archive shows the preview on that course. The homepage
has a separate **Videos** section listing all course recordings, with their
course names and years clearly labelled.
The full playlist link is preserved. The preview is a local image and a normal
link: YouTube is contacted only after a visitor follows it. Recording metadata
and links are included in the profile/course JSON and Markdown exports.

The Videos-section YouTube channel link is edited once in `teaching.channel`
in the editable profile: `name` is the channel name and `url` its address.
It appears on the homepage and course archive with a local YouTube icon, and
is exported in the profile/course JSON and Markdown.

## Other videos

Add standalone research videos to the top-level `videos` array in the editable
profile. Each entry has `title`, `url`, a local `thumbnail` path, and its pixel
`width` and `height`; `year` and `description` are optional. The Videos section
shows course playlists first, followed by these entries in the order you choose.
The same source is exported to profile JSON and Markdown; do not edit the HTML.
