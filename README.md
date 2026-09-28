# resume-builder

Paste a job description into Claude Code and get back a one-page, ATS-optimized
LaTeX PDF tailored to it, built only from facts you've given it.

**Current version: 2.4.0** · see [Changelog](#changelog)

```
/create-resume <paste the job description here>
```

## What it does

- **Tailors to a JD.** Pulls the must-have and nice-to-have keywords out of the
  posting, checks which ones your experience actually backs, and rewrites and
  reorders your resume around them.
- **Builds a general resume** when you don't pass a JD, aimed at the target
  roles you've set.
- **Never makes things up.** Every line comes from your fact base
  (`meta.json`). If a JD wants something that isn't there, it asks you rather
  than inventing it, and remembers your answer.
- **Produces an ATS-safe PDF.** Single column, standard headings, and a clean,
  parseable text layer, fitted to the page limit.
- **Reports keyword coverage** for each application: which JD keywords made it
  in, where they appear, what's missing and why.
- **Tracks applications** in an index with coverage and status.

## Install

### Prerequisites

| Tool | Why | Check |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | runs the `/create-resume` skill | `claude --version` |
| git | clone the repo | `git --version` |
| python3 (3.8+) | renderer and coverage checker | `python3 --version` |
| pdflatex (TeX Live / MacTeX) | builds the PDF | `pdflatex --version` |

There are no Python packages to install; only the standard library is used.

### LaTeX

**macOS:** either the full distribution:

```bash
brew install --cask mactex-no-gui
```

or the smaller BasicTeX plus the packages the template needs:

```bash
brew install --cask basictex
```

```bash
sudo tlmgr update --self && sudo tlmgr install preprint titlesec enumitem cmap lm
```

Open a new terminal afterwards so `pdflatex` is on your `PATH`.

**Linux (Debian/Ubuntu):**

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended lmodern
```

**Windows:** use [WSL](https://learn.microsoft.com/windows/wsl/install) and
follow the Linux steps. `build.sh` is a bash script.

### Get the skill

```bash
git clone https://github.com/Amankori2307/resume-builder.git
```

```bash
cd resume-builder && claude
```

The skill lives in `.claude/skills/create-resume/`, so Claude Code picks it up
automatically when it's opened in this folder. It depends on `build.sh`,
`lib/` and `templates/` in the same repo, so run it from here rather than
copying the skill folder elsewhere.

### Your data repo

Your facts, applications and PDFs live in **`resume-data/`**, a separate
**private** git repo cloned inside this folder and gitignored by it. The public
tool repo never contains or references your data, and the private repo gives
you backup, history, and the same resume data on every machine.

The first `/create-resume` sets it up, asking whether you already have one:

- **First time:** it runs `./build.sh --init-data`, onboards you, then offers
  to create the private GitHub repo:

  ```bash
  gh repo create <your-github-user>/resume-data --private --source resume-data --remote origin --push
  ```

- **New machine:** give it the URL, or run:

  ```bash
  ./build.sh --init-data git@github.com:<your-github-user>/resume-data.git
  ```

## Quick start

1. **Run `/create-resume`.** With no profile yet, it onboards you. Pick any
   mix of:
   - **Import:** drop an old resume PDF, a LinkedIn "Save to PDF", or notes into
     `resume-data/profiles/<you>/meta/inbox/`, or paste them in chat.
   - **Fill the template:** edit `resume-data/profiles/<you>/meta/meta.json` yourself.
     The `_hints` and `_example_*` keys explain each field.
   - **Interview:** answer questions round by round (basics, target roles,
     each job, projects, education, skills).
2. **Paste a job description:** `/create-resume <JD text>`. Answer the few
   questions it asks about keywords it couldn't find in your meta.
3. **Open the PDF** at
   `resume-data/applications/<you>/<date>-<company>-<role>/`, and read `report.md` next
   to it.

## Commands

### In Claude Code

Everything goes through one command, and the skill works out what you want
from what you pass:

| You type | Workflow | What happens |
|---|---|---|
| `/create-resume` (no profile yet) | Onboard | Creates your profile and fills `meta.json` from imports, the template or an interview |
| `/create-resume <JD text or URL>` | Tailor | Builds a tailored PDF, coverage report and index row for that JD |
| `/create-resume` | General | Builds the best general resume for `goals.target_roles` |
| `/create-resume add: …` / `update my …` / `I also …` | Meta update | Saves new facts to `meta.json`, in a structured field or as a Q&A fact |
| `/create-resume mark Acme as applied` | Index update | Sets the status of an application: `draft`, `applied`, `interviewing`, `rejected`, `offer` |
| `/create-resume deep dive` | Deep dive | Interviews you role by role (why, how, tech, impact, ownership, challenges, learnings), weakest areas first |
| `/create-resume rebuild` | Evergreen | Rebuilds the fixed document × variant set (see [Advanced](#advanced-evergreen-builds)) |

You can also just ask in plain words: "tailor my resume to this JD", "add
this project to my resume". The skill triggers on those too.

JD input: **pasted text** or a **job-posting URL**
(`/create-resume https://…`). For URLs:

- Tracking parameters (`utm_*`, `email_uid`…) are stripped before fetching,
  so links from job-alert emails don't leak your identity.
- If the page needs sign-in or JavaScript, the skill opens it in Claude's
  built-in browser, where you can sign in yourself.
- If it's still blocked, the skill asks you to paste the text.

File paths and reusing a saved JD by name aren't supported yet.

### In the shell

Claude runs these for you, but they work on their own too:

| Command | What it does |
|---|---|
| `./build.sh --new <name>` | Scaffold `resume-data/profiles/<name>/` with a blank `meta.json` |
| `./build.sh --app <application dir>` | Build one tailored application: writes the PDF and `resume.txt`, prints `pages: N` |
| `python3 lib/coverage.py <application dir>` | Measure JD keyword coverage: writes `coverage.json`, prints a Markdown table |
| `./build.sh --list` | List profiles with their documents and variants |
| `./build.sh --check --profile <name>` | Validate a profile's `resume.json` + `settings.json` without building |
| `./build.sh --profile <name>` | Evergreen build of every document × variant into `resume-data/final/` |
| `… --document <id>` / `--variant <id>` / `--format pdf\|docx` | Narrow an evergreen build |
| `./build.sh --init-data [url]` | Clone your data repo into `resume-data/`, or create a new one (git init, `.gitignore`, first commit) |
| `./build.sh --data-pull` | Fast-forward `resume-data/` from GitHub; exits 3 if two machines diverged |
| `./build.sh --data-push "<msg>"` | Commit everything in `resume-data/` and push |
| `./build.sh --migrate-data` | Move a pre-2.0 `data/` folder to `resume-data/` |
| `python3 lib/meta_status.py <profile dir>` | Report how many days since meta was updated, and whether a check-in or deep dive is due |
| `python3 lib/meta_completeness.py <profile dir>` | Score meta 0–100 and list the missing fields per role and achievement |
| `./build.sh --help` | Usage |

| Environment variable | Effect |
|---|---|
| `RESUME_DATA_DIR` | Where your data repo lives (default `./resume-data`) |
| `RESUME_PROFILE` | Default profile for evergreen builds when there are several |

## How it works

Every run starts by pulling `resume-data/` and ends by committing and pushing
whatever changed (see [Sync across machines](#sync-across-machines)). Tailor
and General runs also check [freshness](#staying-up-to-date) first.

For `/create-resume <JD>`:

1. **Intake:** the JD is cleaned of boilerplate (benefits, EEO text) and
   saved as `jd.txt` in a new application folder.
2. **Keyword extraction:** must-have and nice-to-have terms go to
   `keywords.json`, using the JD's exact spellings (`PostgreSQL`, not
   `Postgres`), with aliases, plus the role title and seniority.
3. **Evidence check:** each keyword is looked up in your `meta.json`, and
   sorted into backed, declined, unbacked or inferable.
4. **Questions:** unbacked and inferable keywords are asked about in one
   batch (up to 4 per prompt, must-haves first). You answer *Yes* / *Adjacent*
   / *No*. Yes and adjacent answers are saved to meta; a no goes to `declined`.
5. **Compose:** a tailored `resume.json` is built from meta only. Bullets are
   chosen and ordered by JD relevance, reworded using the JD's vocabulary
   where it describes the same fact, skills are ordered with JD matches first,
   and a summary names the target title.
6. **Build:** `./build.sh --app` renders LaTeX, runs pdflatex, and reports
   the page count.
7. **Fit loop:** over the page limit, the summary goes first, then the
   lowest-relevance content from the oldest roles is trimmed. Once it fits,
   trimmed content is restored, most relevant first. The summary is added
   last, only if it fits without changing anything else; otherwise the
   resume ships without one. At most 8 iterations.
8. **Coverage:** `lib/coverage.py` checks the text an ATS will actually
   parse. If a backed must-have is missing from it, that's treated as a
   composition bug and fixed before continuing.
9. **Report:** `report.md` covers the coverage table, gaps, bullets that need
   a number, and every reworded bullet next to its original meta text.
10. **Index:** a row is added to `resume-data/applications/<you>/index.md`.
11. **Review:** you get the PDF path, coverage, top gaps and weakest bullets,
    with suggested tweaks.

**No-JD mode** is the same pipeline with a synthesized keyword set: the role
title from `goals.target_roles[0]`, must-haves from `goals.ats_keywords` plus
your core stack. The output folder is `<date>-general-<role>/`.

### Honesty rules

- `meta.json` is the only source. Nothing appears on a resume that isn't
  backed there.
- Likely-but-unstated claims ("you ran SQS workers, so you know message
  queues") are **asked about**, never assumed.
- Past job titles are never changed to match a target role. The JD title goes
  in the summary or headline only. The one exception is an override **you**
  set in `preferences.title_overrides`: the skill warns you that background
  checks verify real titles, and saves it only if you confirm.
- Every reworded bullet is listed in `report.md` next to its original text, so
  you can check nothing drifted.
- Declined keywords are never asked about again and never used.

## Getting the best results

**The data is the product.** Every bullet, keyword match and interview story
comes from `meta.json`, so the more you put in, the better every resume gets.
Run the deep dive once, properly:

```
/create-resume deep dive
```

For each role you first list everything you worked on (rough is fine). Then,
for each item, it asks about whatever is missing:

- **Why:** what was broken or painful before? Who needed it?
- **How:** how does it work, and what was the key design decision?
- **Tech:** what did you build it with?
- **Impact:** what number changed (latency, cost, volume, errors, revenue)?
  How big was it? What happened after it shipped?
- **Ownership:** solo, led, or contributed? What exactly was your part?
- **Challenges:** what was hard? What did you consider instead, and why not?
- **Scale and constraints:** users, rows/day, deadline, team size, budget.
- **Learnings:** what would you do differently?
- **Dates, status, links:** when it shipped, live or pilot, PR or case study.

Plus, per role: what the company and product do, your team and reporting
line, recognition you received, and privately why you joined and left (never
put on a resume, only used for interview prep).

It's a one-time investment of an hour or so, and you can stop at any point;
everything is saved as you go. `lib/meta_completeness.py` scores meta 0–100
and the interview goes to the weakest spots first.

**Do it again every few months.** Memory comes back in layers: a second
pass recalls numbers and projects the first one missed. The skill suggests a
new deep dive every 90 days (`preferences.deep_dive_every_days`).

## Your data: `meta.json`

`resume-data/profiles/<you>/meta/meta.json` is your fact base. The full field
reference is in
[`reference/meta-schema.md`](.claude/skills/create-resume/reference/meta-schema.md).

| Section | Holds |
|---|---|
| `basics` | Name, email, phone, location, links |
| `goals` | Target roles, seniority, industries, locations, ATS keywords (drives no-JD mode) |
| `experience[]` | Per employer: title, earlier titles (`title_history`), dates, team, tech, company context, reporting line, recognition, `private` (why joined/left, never on a resume), and `achievements[]`: what, why, how, tech, metrics, outcomes, scale, ownership, challenges, learnings, dates, status, links |
| `projects[]`, `education[]`, `certifications[]` | As named |
| `skills` | Free categories; only skills you'd be comfortable being interviewed on |
| `facts[]` | Free-form `{q, a, tags}` for anything that doesn't fit a field: awards, gaps, visa status, context behind a role. Answers to JD questions land here too. |
| `declined[]` | Keywords you said you don't have |
| `preferences` | See below |

`preferences`:

| Key | Default | Effect |
|---|---|---|
| `rules` | `[]` | Your own writing rules, applied on top of the built-in ones |
| `region` | `""` | `IN`, `US`, `UK`, `EU`… (photo, DOB, address and spelling conventions) |
| `include_phone` | `true` | Hide the phone number when false |
| `max_pages` | `null` | `null` = auto: 1 page under 7 years of experience, otherwise 2 |
| `section_order` | `null` | e.g. `["summary","experience","skills","projects","education"]` |
| `filename_stem` | `""` | e.g. `Jane-Doe-Resume`; default `<First>-<Last>-Resume` |
| `stale_after_days` | `30` | Days before the [freshness check-in](#staying-up-to-date) |
| `deep_dive_every_days` | `90` | Days before a new [deep dive](#getting-the-best-results) is suggested |
| `title_overrides` | `{}` | Per-role display title for `ic`, `manager` or `all` targets, set by you, e.g. `{"acme": {"applies_to": "ic", "title": "Senior Software Engineer"}}`. Your real title stays in `experience[]`. |

**Rules layering:** the global rules ship with the skill in
[`writing-rules.md`](.claude/skills/create-resume/reference/writing-rules.md)
and [`ats-rules.md`](.claude/skills/create-resume/reference/ats-rules.md). Your
`preferences.rules` apply on top and win on conflict, except the no-fabrication
rule, which is never overridden.

**Editing:** say `/create-resume add: …` or edit the JSON directly. Files you
drop into `meta/inbox/` stay there as an audit trail after import.

`last_updated` (set on every change), `stale_snoozed_until` and
`preferences.stale_after_days` (default 30) drive the freshness check below.

## Staying up to date

A tailored resume is only as good as the facts behind it. When you ask for a
resume and meta hasn't changed in over `stale_after_days` (default 30), the
skill checks in first:

> Your meta was last updated 47 days ago.

Then it asks **targeted** questions drawn from your own meta:
- Are you still at your current employer, in the same title?
- Has a feature marked "not GA" launched?
- What's new since the last update?
- Do you have a number yet for a bullet that has none?
- Are any open questions now answered?
- Are your target roles unchanged?

Your answers are saved to meta, and the build continues. *Nothing changed* or
*skip* snoozes the check for 7 days.

"Last updated" is the latest of three things, so edits made by hand or on
another machine count too:
- `meta.last_updated`
- the last commit touching `meta.json` in the data repo
- an uncommitted edit to the file

Check it yourself with `python3 lib/meta_status.py resume-data/profiles/<you>`.

## Sync across machines

- **Before each run:** `./build.sh --data-pull` fast-forwards from GitHub, so
  changes made on another machine are picked up.
- **After each change:** a meta update, an application build or a status
  change runs `./build.sh --data-push "<message>"`, which commits with a
  descriptive message (e.g. `meta: add Acme Slack bot metrics`) and pushes.
- **If two machines both changed meta:** the pull stops (exit 3) instead of
  merging. The skill shows the conflicting facts side by side, asks which is
  right, then commits and pushes the resolution.

Application PDFs are committed, so the exact file you sent each company is
always available. Build scratch (`.build/`, `dist/`, LaTeX logs) isn't.

## Output files

```
resume-data/                             your private data repo (see above)
  profiles/<you>/meta/meta.json          your facts
  profiles/<you>/meta/inbox/             raw files you imported
  profiles/<you>/resume.json             master for evergreen builds
  applications/<you>/index.md            all applications
  applications/<you>/<date>-<company>-<role>/
  final/<variant>/                       evergreen builds
```

Each application folder contains:

| File | Contents |
|---|---|
| `<Name>-Resume-<Company>-<Role>.pdf` | The deliverable |
| `report.md` | Coverage, gaps, bullets needing numbers, rewordings |
| `jd.txt` | The cleaned JD |
| `keywords.json` | Extracted keywords |
| `coverage.json` | Machine-readable coverage |
| `resume.json`, `settings.json` | The tailored source; edit these and rerun `./build.sh --app` |
| `resume.txt` | Plain-text rendering, handy for pasting into ATS form fields |
| `interview-prep.md` | 60-second pitch, STAR stories for the top must-haves, talking points (why leaving, title overrides, gaps) |
| `.build/` | LaTeX intermediates and log |

`index.md` columns: Date · Company · Role · Must % · Nice % · Pages · Status ·
Folder. Status starts as `draft`.

## ATS choices

- Single column, standard section headings (Summary, Experience, Skills,
  Projects, Education, Certifications), and no tables, icons or graphics.
- A text layer that parses correctly: `cmap`, T1 fonts, `glyphtounicode`,
  `\pdfinterwordspaceon` (real space characters), and text-mode bullets
  (U+2022). Math-mode bullets extract as U+2219 and stick to the preceding
  link.
- Keywords use the JD's exact spelling, ideally once in Skills and once in a
  bullet that shows them being used. Five or more uses gets flagged as
  possible stuffing.
- The target role title appears verbatim once, in the summary.
- Page limit: 1 page under 7 years of experience, otherwise 2. The summary
  is optional and always the lowest priority. Content is trimmed to fit
  without it, trimmed content is restored first, and the summary is added
  only into space that's left over. No detail is ever shortened or dropped
  to make room for a summary.
- Internships: with under 3 years of experience they're full entries. With 3+
  years they're included only when relevant to the target role and there's
  room. Priority when fitting: full-time content, then relevant internships,
  then the summary. Omitted internships are noted in report.md.
- Section order: Summary → Experience → Skills → Projects → Education for 3+
  years of experience; skills and projects come first for earlier-career
  profiles.

Tuned for software engineering and engineering management roles in 1.0.0.

## Example session

*(Fictional person and company.)*

```
> /create-resume Senior Backend Engineer at Northwind. Requirements: 5+ years
  Node.js, PostgreSQL, AWS (SQS, Lambda), event-driven architecture, Kubernetes.
  Nice to have: Kafka, Terraform...

Created resume-data/applications/jane/2026-10-02-northwind-senior-backend-engineer/
Extracted 9 must-have and 5 nice-to-have keywords.
Backed in your meta: Node.js, PostgreSQL, AWS SQS, AWS Lambda, event-driven, Terraform…

? Have you used Kubernetes?   ○ Yes  ○ Adjacent  ○ No
? Have you used Kafka?        ○ Yes  ○ Adjacent  ○ No
  → Kubernetes: No (saved to declined)
  → Kafka: Adjacent, "RabbitMQ at Contoso" (saved as a fact)

Built Jane-Doe-Resume-Northwind-Senior-Backend-Engineer.pdf, 1 page (summary kept)
Must-have 8/9 (89%) · Nice-to-have 3/5 (60%)
```

`report.md` excerpt:

```markdown
## Keyword coverage
- Must-have: **8/9** (89%)
- Nice-to-have: **3/5** (60%)
- Target title "Senior Backend Engineer" appears verbatim: yes

| Keyword    | Tier | Found in                    | Notes   |
|------------|------|-----------------------------|---------|
| Node.js    | must | Summary ×1, Experience ×2, Skills ×1 |  |
| Kubernetes | must | —                           | MISSING |

## Gaps
- Kubernetes: declined 2026-10-02
- "5+ years": met (6 years)

## Would be stronger with a number
- Contoso: "Moved billing webhooks onto a retry queue". How many events/day? Failure rate before/after?
```

`index.md` excerpt:

```markdown
| Date       | Company   | Role                    | Must % | Nice % | Pages | Status  | Folder |
|------------|-----------|-------------------------|--------|--------|-------|---------|--------|
| 2026-10-02 | Northwind | Senior Backend Engineer | 89     | 60     | 1     | applied | 2026-10-02-northwind-senior-backend-engineer |
```

## Troubleshooting & FAQ

**`pdflatex is required` / `pdflatex: command not found`:** install LaTeX (see
[Install](#latex)) and open a new terminal. On macOS, check that
`/Library/TeX/texbin` is on your `PATH`.

**`pdflatex failed`:** the first error lines are printed, and the full log is
at `<application dir>/.build/resume.log`. Characters like `& % $ # _ { }` are
escaped automatically, so write them literally in JSON. A missing package
(`File 'titlesec.sty' not found`) means a BasicTeX install is missing the
`tlmgr install` step.

**Still over one page:** the fit loop trims for up to 6 iterations, then
reports what it cut. Set `preferences.max_pages` to `2`, or tell the skill
which bullets to drop.

**Why did it ask me about X?** X is in the JD and wasn't found anywhere in
your meta. It asks once, then remembers your answer.

**I answered wrong / I've learned it since.** `/create-resume update: I now
use Kubernetes at …` records the new fact and removes the keyword from
`declined`. Or edit `meta.json` directly.

**Several people on one machine?** Each person gets
`./build.sh --new <name>`. The skill asks which profile to use when there's
more than one.

**Is my data committed?** Not to this repo. Everything personal lives in
`resume-data/`, which this repo gitignores, and which is its own **private**
repo on GitHub. Set `RESUME_DATA_DIR` to keep it somewhere else entirely.

**`resume-data has diverged from its remote`:** meta changed on two machines
between syncs. Run `/create-resume` again and it walks you through merging
the conflicting facts. Or resolve it by hand in `resume-data/` with git.

**I edited meta by hand. Is it synced?** On the next `/create-resume` run it
is committed and pushed. You can also run
`./build.sh --data-push "meta: hand edit"`.

**`found data/ from a pre-2.0 install`:** see the 2.0.0 migration steps in the
[Changelog](#changelog).

**Where are the rules it follows?** In
`.claude/skills/create-resume/`: `SKILL.md` (workflows) and
`reference/` (ATS rules, writing rules, meta schema, JD intake, and the
resume.json schema).

## Advanced: evergreen builds

Besides per-JD applications, a profile's master `resume-data/profiles/<you>/resume.json`
can produce a fixed set of resumes: every **document** × **variant** declared in
its `settings.json`. For example, a `main` copy and a `linkedin` copy (no
phone), each in `IC` and `Lead` variants.

- Tag any contact, link, section, item or bullet with
  `"include_in": ["<document id>"]` or `"variants": ["<variant id>"]`. Untagged
  content appears everywhere.
- `title_overrides` in a variant, keyed by an experience item's `id`, retitles
  only that role for that variant.
- Build with `./build.sh --profile <you>`. Output goes to
  `resume-data/final/<variant>/` as PDF, DOCX (needs `textutil` on macOS or `pandoc`)
  and TXT.

Full reference:
[`reference/schema.md`](.claude/skills/create-resume/reference/schema.md).

## Repository layout

```
.claude/skills/create-resume/
  SKILL.md                     workflows and routing (the skill itself)
  assets/meta.template.json    blank fact base for new profiles
  reference/
    meta-schema.md             meta.json fields and update rules
    ats-rules.md               keyword extraction, composition, fit loop, regions
    writing-rules.md           global bullet-quality rules
    jd-intake.md               JD input detection and normalization
    schema.md                  resume.json / settings.json / application dirs
build.sh                       build driver (profiles, applications, evergreen)
lib/render.py                  resume.json -> LaTeX / plain text, validator
lib/coverage.py                keyword coverage over the rendered text
lib/meta_status.py             meta freshness (days since last update)
templates/classic.tex.tmpl     ATS-safe LaTeX template
templates/profile/             scaffold copied by --new
templates/data.gitignore       .gitignore for a new resume-data repo
CLAUDE.md                      maintenance rules for Claude Code
LICENSE
```

## Maintaining

The README documents **only the current version** of the skill and has to
stay in sync with it. Any change to `.claude/skills/create-resume/`,
`build.sh`, `lib/` or `templates/` must, in the same change:

1. update the affected README sections,
2. bump `version` in the `SKILL.md` frontmatter and the version line at the
   top of this README,
3. add a changelog entry below.

Versioning follows [semver](https://semver.org):

- **MAJOR**: breaking changes to the `meta.json` / `resume.json` /
  `settings.json` format, the `resume-data/` layout, or command behaviour. The entry
  is marked **BREAKING** and includes *How to migrate* steps.
- **MINOR**: new features (e.g. a new JD input type or template).
- **PATCH**: fixes and doc corrections.

Entry format:

```markdown
### 1.1.0 — YYYY-MM-DD
- Added: …
- Changed: …
- Fixed: …

### 2.0.0 — YYYY-MM-DD — BREAKING
- Changed: …
**How to migrate:** 1. … 2. …
```

## License

[MIT](LICENSE) © 2026 Aman Kori

## Changelog

### 2.4.0 — 2026-09-28
- Added: global internship rule (`ats-rules.md` §4). Under 3 years of
  experience, internships are full entries. At 3+ years, they're included
  only if relevant to the target role and there's room. Fit priority is
  full-time content, then relevant internships, then the summary.

### 2.3.1 — 2026-09-28
- Fixed: the fit loop could shorten or drop real content and then use the
  freed space for a summary. The summary is now the lowest-priority content:
  trim without it, restore trims first, add the summary only if it fits
  without changing anything else (global rule, `ats-rules.md` §5).

### 2.3.0 — 2026-09-28
- Added: job-posting **URL** input. It strips tracking parameters, fetches
  with WebFetch, falls back to the built-in browser for sign-in or JS-only
  pages, and records `Source:` and `Fetched:` in `jd.txt`.

### 2.2.0 — 2026-09-28
- Added: the **deep dive** workflow (`/create-resume deep dive`). A
  brain-dump-then-drill interview per role, weakest first, also run at
  onboarding and suggested every 90 days.
- Added: optional achievement fields (`why`, `need`, `outcomes`, `scale`,
  `constraints`, `ownership`, `challenges`, `alternatives`, `learnings`,
  `start`/`end`/`status`/`links`) and role fields (`company_context`,
  `reporting_to`, `partners`, `recognition`, `private`).
- Added: `lib/meta_completeness.py` (0–100 score and gap list), plus
  `last_deep_dive` / `deep_dive_due` in `lib/meta_status.py`.
- Added: `interview-prep.md` in every application (pitch, STAR stories,
  talking points).

### 2.1.0 — 2026-09-28
- Added: `preferences.title_overrides`, a user-set display title per role for
  IC, manager or all targets. The skill confirms the background-check risk
  before saving one, drops bullets that contradict it, and lists it in
  report.md.

### 2.0.0 — 2026-09-28 — BREAKING
- Changed: personal data moved from `data/` to **`resume-data/`**, a
  separate private git repo cloned inside this folder (gitignored here).
- Added: `./build.sh --init-data [url]`, `--data-pull`, `--data-push`,
  `--migrate-data`. The skill pulls before each run and commits and pushes
  after each change, and stops for you to resolve if two machines diverge.
- Added: meta freshness. New `last_updated` and `stale_snoozed_until` fields,
  `preferences.stale_after_days` (default 30), `lib/meta_status.py`, and a
  targeted check-in before building when meta is out of date.

**How to migrate:**
1. `./build.sh --migrate-data`: moves `data/` to `resume-data/`.
2. `./build.sh --init-data`: makes it a git repo with its own `.gitignore`.
3. `gh repo create <your-github-user>/resume-data --private --source resume-data --remote origin --push`

### 1.0.1 — 2026-09-28
- Fixed: an experience entry with no bullets (e.g. a role you just started)
  overlapped the next role's heading in the PDF.

### 1.0.0 — 2026-09-28
Initial release.
- `/create-resume` with a single entry point and intent routing: onboard,
  tailor to a pasted JD, general resume, meta update, application status,
  evergreen rebuild.
- `meta.json` fact base with a free-form `facts` Q&A, `declined` keywords and
  per-user `preferences.rules`.
- JD keyword extraction (`keywords.json`), evidence check against meta, and
  batched gap questions whose answers are saved back to meta.
- Per-application folders with PDF, `report.md` and `coverage.json`, plus an
  applications `index.md` with statuses.
- `./build.sh --app` for single application builds with page count, and a
  fit loop (the summary is dropped before bullets; 1 page under 7 years).
- `lib/coverage.py`: alias-aware keyword coverage by section, with
  exact-spelling and stuffing flags.
- ATS-hardened template: single column, `cmap`/T1/`glyphtounicode`,
  real interword spaces, text-mode bullets, and a `summary` section type.
- All personal data under a gitignored `data/` (`RESUME_DATA_DIR` to relocate).
- Evergreen documents × variants builds (`./build.sh --profile`).
