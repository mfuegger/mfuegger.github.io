# Edit website content here

This folder contains the editable sources. For routine updates, start here.
After a commit to `main`, GitHub Actions builds and publishes the site automatically.

| Update | File |
| --- | --- |
| Courses, research, biography, contact, links, portrait | [profile.json](profile.json) |
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

For layout changes and local preview commands, see the [main README](../README.md).
