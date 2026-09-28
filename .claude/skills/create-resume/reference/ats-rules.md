# ATS rules — software engineering profile

These rules target engineering roles (IC and engineering management). Other
role families can get their own file later; until then apply this one.

An ATS does two things: **parse** the PDF into fields (name, contact, jobs,
dates, skills) and **rank** it against the JD by keyword match. A human then
skims the top of page one for about ten seconds. Every rule below serves one of
those three readers.

## 1. Parsing — the template already enforces these; don't fight it

- Single column, linear reading order. No tables, text boxes, icons, images,
  headers/footers, or multi-column skill grids.
- Real text layer: `cmap`, `T1` fonts and `glyphtounicode` are in
  `templates/classic.tex.tmpl`. Don't add packages that break this.
- Contact details as plain text in the body, not in a PDF header.
- Standard section headings only: `Summary`, `Experience`, `Skills`,
  `Projects`, `Education`, `Certifications`. Not "Where I've Been" or
  "Toolbox".
- Each role: organization, title, location, and a date range in one
  consistent format (`MM/YYYY - MM/YYYY` or `Present`).
- Don't use symbols as content (★, →, |) — they parse as garbage.

## 2. Keyword extraction from a JD

Produce `keywords.json` in the application dir:

```json
{
  "company": "Acme",
  "role_title": "Senior Backend Engineer",
  "seniority": "senior",
  "must": [{ "term": "Node.js", "aliases": ["NodeJS"], "category": "language" }],
  "nice": [{ "term": "Kafka", "aliases": [], "category": "infra" }]
}
```

How to classify:

- **must**: in a "Requirements" / "What you'll need" / "Must have" block,
  repeated two or more times, or in the job title itself.
- **nice**: "Nice to have" / "Bonus" / "Preferred", or mentioned once in passing.
- Keep the **JD's exact spelling** as `term` (`PostgreSQL` vs `Postgres`,
  `CI/CD` vs `continuous integration`). Put the other spellings in `aliases`.
  ATS matching is mostly literal.
- Extract concrete, matchable terms: languages, frameworks, datastores,
  cloud services, protocols, practices (`TDD`, `code review`, `on-call`),
  domain words (`payments`, `ad tech`), and scope words for managers
  (`hiring`, `roadmap`, `stakeholder`, `mentoring`, `sprint planning`).
- Skip soft filler ("passionate", "fast-paced", "team player"). Nobody ranks on it.
- Record years-of-experience and degree requirements separately in the
  report; they aren't keywords.
- Aim for 10–20 must and 5–15 nice. More than that means you're extracting
  noise.

## 3. Using keywords without lying

- A keyword may appear on the resume only if it is **backed** in meta (see
  `meta-schema.md` → Evidence lookup).
- Put it where it is **earned**: in a bullet that describes using it beats a
  mention in the skills line. Best is both — once in Skills with the exact JD
  spelling, once in context in a bullet.
- Reword existing bullets to use the JD's vocabulary when it describes the
  same thing (meta says "pub/sub via SQS", JD says "event-driven messaging" →
  "event-driven messaging over SQS"). Same fact, the reader's words.
- No stuffing. A term appearing five or more times is flagged by
  `lib/coverage.py`. Two or three natural uses is ideal.
- No hidden or white text, and no keyword dump sections. Parsers and
  recruiters both catch these, and it gets resumes rejected.
- The **role title** from the JD should appear verbatim once, in the headline
  or summary ("Senior Backend Engineer with 5 years…"), **never** as a past
  job title unless it was the actual title.

## 4. Composition order for engineers

Default section order:

- **≥ 3 years experience:** Summary → Experience → Skills → Projects → Education → Certifications
- **< 3 years / new grad:** Summary → Skills → Projects → Experience → Education
- **Engineering manager targets:** same as ≥ 3 years, but the first two
  bullets of each recent role lead with scope (team size, hiring, delivery),
  then technical depth.

`preferences.section_order` overrides this.

### Skills section

- Group into 3–5 labelled lines: `Languages`, `Backend`, `Frontend`,
  `Data & Messaging`, `Cloud & DevOps`, `Practices`. Rename them to fit the
  person.
- Within each line, put the JD-matching items first.
- Drop skills irrelevant to the JD only if space is tight. Never drop a
  must-have match.
- No proficiency bars, ratings, or "(basic)".

### Summary

2–3 lines: target title (verbatim from JD) + years of experience + the 2–3
strongest must-have matches with evidence + one distinctive thing. No
adjectives about personality.

The summary is **optional** and has the **lowest priority of anything on the
page** (see §5, the Summary rule). It only gets space that is left over once
every piece of real content is at full length. It never displaces, shortens
or removes a bullet, a skill, a project or a role.

### Bullets

Per recent role, 4–6 bullets; older roles 2–3; roles older than about 8 years
1–2 or folded into one line. Order within a role by JD relevance. The first
bullet of the most recent role is the most-read line on the page — make it the
strongest must-have match with a number.

## 5. Length and the fit loop

Page limit (unless `preferences.max_pages` is set):

- total professional experience < 7 years → **1 page**
- ≥ 7 years → **2 pages max**

After each build, read `pages:` from `./build.sh --app`.

**The Summary rule (global, never overridden): content always beats the
summary.** Never shorten, merge or remove any detail to make room for a
summary. If the only way to include a summary is to cut content, omit the
summary.

The loop runs in this order:

1. **Remove the summary** if the build is over the limit.
2. **Trim to fit without the summary.** Remove or shorten the
   lowest-relevance content (oldest roles first), rebuilding after each
   change. Never remove the only evidence for a must-have keyword; shorten
   that bullet instead. Record every trim, with its original text.
3. **Restore trimmed content** once it fits. Put each trimmed item back at
   full length, most relevant first, keeping each one that still fits. Only
   the trims that truly can't fit stay out.
4. **Add the summary last**, and only if it fits alongside everything from
   step 3 without changing any of it. If it overflows, remove it again and
   ship without a summary.
5. A spill of a few lines onto the next page is the worst outcome, so trim
   to fit (steps 2–3).
6. Stop after 8 iterations. In report.md, list every trim that stayed out,
   and state whether the summary was included and why.

## 6. Regional conventions (`preferences.region`)

- **IN / US / UK / EU default:** no photo, no DOB, no marital status, no
  full street address (city + country only).
- **US:** no nationality or visa status unless the user asks; "Present" for
  current roles; US English.
- **UK / IN / EU:** British spelling is acceptable. "CV" in the filename is
  fine for UK/EU.
- **Sponsorship needed:** only mention it if the user added a fact saying so.

## 7. File naming

`<filename_stem>-<Company>-<Role>.pdf`, e.g.
`Jane-Doe-Resume-Acme-Senior-Backend-Engineer.pdf`. ASCII, hyphens, no spaces.
Recruiters see this filename.
