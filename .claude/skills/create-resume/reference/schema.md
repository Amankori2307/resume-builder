# Profile schema reference

Two files per profile. Both are strict JSON — no comments, no trailing commas.
Any key beginning with `_` is ignored by the builder and is a safe place for
notes (`_notes`, `_comment`).

---

## `resume.json`

```jsonc
{
  "basics": { ... },
  "sections": [ ... ]
}
```

### `basics`

| Field | Type | Notes |
|---|---|---|
| `name` | string | **Required.** |
| `contact` | array | Rendered on one line, joined with bullets. |
| `links` | array | Rendered on the next line. |

A `contact` entry is either a bare string or an object:

```json
{ "text": "you@example.com", "href": "mailto:you@example.com" }
```

A `links` entry adds a label:

```json
{ "label": "GitHub", "text": "github.com/you", "href": "https://github.com/you" }
```

Both accept the `include_in` / `variants` tags (see **Tagging**). Tagging the
phone number `"include_in": ["main"]` keeps it off a copy you post publicly.

### `sections`

Each section has a `type`, a `title`, and `items`. Sections render in array
order; the title is upper-cased in output.

#### `type: "summary"`

```json
{ "type": "summary", "title": "Summary",
  "items": [{ "text": "Senior Backend Engineer with **5 years** building ..." }] }
```

Items are joined into one paragraph. Usually a single item.

#### `type: "experience"`

```json
{
  "id": "acme",
  "organization": "Acme (formerly Widgets Inc)",
  "title": "Engineering Manager",
  "location": "Bengaluru, India",
  "start": "2023-02",
  "end": "2026-06",
  "bullets": [
    { "text": "Scaled revenue from **$0 to $1.2M ARR** by ..." }
  ]
}
```

`id` is required if any variant needs a `title_overrides` entry for this role,
and is good practice regardless. A bullet is either a bare string or an object
with `text` plus optional tags.

#### `type: "education"`

Same fields as `experience`. `bullets` is optional. Add
`"text_date_precision": "year"` on the *section* to print `2017 – 2020` in the
text output while the PDF keeps `08/2017 - 07/2020`.

#### `type: "skills"`

```json
{ "label": "Languages", "value": "JavaScript, TypeScript, Go" }
```

#### `type: "list"`

Free-form bullets — certifications, publications, talks. Items are strings or
`{ "text": ... }` objects.

### Dates

Accepted: `"YYYY-MM"`, `"YYYY"`, `"present"` / `"current"` / `"now"`, or `null`.
Anything else is a validation error. Output style is set per format in
`settings.dates`:

| Style | Renders |
|---|---|
| `numeric` | `06/2026` |
| `short_month` | `Jun 2026` |

`present` always renders as `Present`.

### Emphasis

Wrap text in `**double asterisks**` to bold it in the PDF. The markers are
stripped from the text/DOCX output. Use it on the number, not the whole clause:

- Good: `processing **2M events daily**`
- Bad: `**processing 2M events daily across the platform**`

All content is LaTeX-escaped automatically. Write `$`, `&`, `%`, `#`, `_`,
`{`, `}` literally — do **not** pre-escape them.

### Tagging

Two independent, optional filters on any contact, link, section, item, or
bullet:

```json
{ "text": "...", "include_in": ["linkedin"], "variants": ["EM"] }
```

- `include_in` — document ids from `settings.documents`
- `variants` — variant ids from `settings.variants`

Absent tag = appears everywhere. Both must pass for content to render. Tags
referencing an unknown id are a validation error, so a typo fails loudly rather
than silently dropping a bullet.

---

## `settings.json`

```json
{
  "profile": "jane",
  "template": "classic",
  "formats": ["pdf", "docx"],
  "dates": { "tex_style": "numeric", "txt_style": "short_month" },
  "documents": [
    { "id": "main", "basename": "Jane-Doe-Resume" }
  ],
  "variants": [
    { "id": "EM", "label": "Engineering-Manager", "title_overrides": {} }
  ]
}
```

| Field | Notes |
|---|---|
| `template` | Base name of a file in `templates/` (`classic` → `templates/classic.tex.tmpl`). Can also be set per document. |
| `formats` | Any of `pdf`, `docx`. TXT is always written. |
| `documents[].basename` | Filename stem. |
| `variants[].label` | Appended to the stem as `-<label>`. Use `""` for no suffix. |
| `variants[].title_overrides` | `{ "<item id>": "Replacement Title" }`, scoped to that variant. |

Output path: `resume-data/final/<variant.id>/<basename>-<label>.<ext>`

The build matrix is every document × every variant. Four documents from two of
each. The validator rejects any two combinations that would collide on one
filename.

---

## Templates

`templates/<name>.tex.tmpl` is a complete LaTeX document containing two
placeholder tokens, `HEADER` and `SECTIONS`, each wrapped in double braces. The
renderer substitutes generated LaTeX into them and skips any line starting with
`%`, so you can safely name the placeholders in template comments.

The template owns all styling and must define the macros the renderer emits:
`\resumeItem`, `\resumeSubheading`, `\resumeSubHeadingListStart` / `End`,
`\resumeItemListStart` / `End`. Copy `classic.tex.tmpl` as a starting point.

---

## Application dirs

A tailored build lives in
`resume-data/applications/<profile>/<YYYY-MM-DD>-<company>-<role>/` and holds its own
`resume.json` plus a minimal `settings.json`, so the validator and renderer
treat it exactly like a profile:

```json
{
  "template": "classic",
  "formats": ["pdf"],
  "dates": { "tex_style": "numeric", "txt_style": "short_month" },
  "documents": [{ "id": "main", "basename": "Jane-Doe-Resume-Acme-Senior-Backend-Engineer" }]
}
```

No `variants`, no tags: the application's resume.json already *is* the
tailored cut. Build it with `./build.sh --app <dir>`, which writes
`<basename>.pdf` and `resume.txt` into the dir and prints `pages: N`.

Full contents of an application dir:

| File | Written by |
|---|---|
| `jd.txt` | skill (intake) |
| `keywords.json` | skill (extraction) |
| `resume.json`, `settings.json` | skill (composition) |
| `<basename>.pdf`, `resume.txt`, `.build/` | `./build.sh --app` |
| `coverage.json` | `python3 lib/coverage.py <dir>` |
| `report.md` | skill (coverage output + gaps + notes) |
| `interview-prep.md` | skill (pitch, STAR stories, talking points; may use `private.*`) |
