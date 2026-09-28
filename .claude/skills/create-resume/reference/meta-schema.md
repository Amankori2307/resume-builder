# `meta.json` — the fact base

`resume-data/profiles/<name>/meta/meta.json` is the only thing the skill may claim
about a person. Every resume, tailored or general, is composed from it. If a
statement cannot be traced to a field here, it does not go on the resume.

The blank template is `assets/meta.template.json`. `./build.sh --new <name>`
copies it into place.

Keys beginning with `_` are hints and examples; ignore them when composing.

## Why JSON, and why a `facts` escape hatch

Structured fields let the skill select, filter and match keywords reliably
(`experience[].tech`, `skills.*`). But no fixed schema covers every career.
Anything that doesn't fit goes into `facts` as a question and answer, so the
schema never forces information to be dropped or bent to fit.

## Fields

| Path | Type | Notes |
|---|---|---|
| `last_updated` | `YYYY-MM-DD` | Set to today on **every** change the skill makes to this file. Drives the freshness check. |
| `stale_snoozed_until` | `YYYY-MM-DD` / null | Set to today + 7 days when the user skips a freshness check-in. |
| `last_deep_dive` | `YYYY-MM-DD` / null | Set when a deep dive finishes. A new one is suggested after `preferences.deep_dive_every_days`. |
| `basics.name/email/phone/location` | string | Header. `preferences.include_phone: false` hides the phone. |
| `basics.links[]` | `{label, url}` | LinkedIn, GitHub, portfolio, LeetCode… |
| `goals.target_roles[]` | string | Drives no-JD mode. First entry = primary target. |
| `goals.seniority` | string | `junior` / `mid` / `senior` / `staff` / `manager` … |
| `goals.industries[]`, `goals.locations[]` | string | Context; used for the summary and ranking, never invented. |
| `goals.ats_keywords[]` | string | Keywords the user wants to rank for when there's no JD. |
| `experience[]` | object | Most recent first. |
| `experience[].id` | slug | Stable id, reused as the resume.json item id. |
| `experience[].organization/title/location` | string | `title` is the **current or final** title. Never altered on output. |
| `experience[].title_history[]` | `{title, start, end}` | Earlier titles at the same company; source for "Promoted from X to Y". |
| `experience[].start/end` | `YYYY-MM` / `present` | |
| `experience[].employment_type` | string | full-time, contract, internship… |
| `experience[].team` | string | Team size, scope, reporting line. |
| `experience[].tech[]` | string | Everything used in this role. Evidence for skills. |
| `experience[].company_context` | `{what, product, stage, size, domain}` | What the company and product do. Feeds summaries and domain matching. |
| `experience[].reporting_to` / `partners[]` | string | Reporting line and cross-team partners. |
| `experience[].recognition[]` | string | Promotions, ratings, awards, manager or client quotes. |
| `experience[].private` | `{why_joined, why_left}` | **Never rendered on a resume.** Interview prep only. |
| `experience[].achievements[]` | object | Raw material for bullets. |
| `…achievements[].text` | string | What was done, in the user's words. |
| `…achievements[].how` | string | Mechanism — how it worked. |
| `…achievements[].metrics[]` | string | Only real numbers. Empty is fine. |
| `…achievements[].tech[]` | string | Tech used for this specific achievement. |
| `…achievements[].leadership` | bool | True for hiring, mentoring, team leading, process ownership. |
| `…achievements[].why` / `need` | string | The problem, and who needed it solved and why then. |
| `…achievements[].outcomes[]` | string | Non-numeric results (adopted as default, unblocked deals…). |
| `…achievements[].scale` / `constraints` | string | Users, volume, RPS, team size; deadline, budget, legacy limits. |
| `…achievements[].ownership` | `{role, my_part, collaborators[]}` | `role`: `solo` / `led` / `contributed`. Prevents claiming team work as solo. |
| `…achievements[].challenges[]` / `alternatives[]` | string | What was hard; options considered and why this one won. |
| `…achievements[].learnings[]` | string | Interview prep and summaries; rarely a bullet. |
| `…achievements[].start/end/status/links[]` | | When it shipped, `status` (e.g. "in pilot, not GA"), links to a PR, demo or case study. |
| `projects[]` | `{name, url, description, tech[], achievements[]}` | Side projects, OSS. |
| `education[]` | `{institution, degree, field, location, start, end, notes[]}` | |
| `certifications[]` | `{name, issuer, date}` | |
| `skills.<category>[]` | string | Free category names. Only interview-ready skills. |
| `facts[]` | `{q, a, tags[], source, added}` | Free-form. `source` is `user`, `jd-gap` (answered during tailoring) or `inference` (the user confirmed a suggested claim). |
| `declined[]` | `{term, date, note?}` | Keywords the user said they lack. Never ask again, never include. |
| `preferences.rules[]` | string | Per-user writing rules, applied on top of the global ones. |
| `preferences.region` | string | `IN`, `US`, `UK`, `EU`… See `ats-rules.md` → Regional conventions. |
| `preferences.include_phone` | bool | Default true. |
| `preferences.max_pages` | int / null | null = auto (see `ats-rules.md` → Length). |
| `preferences.section_order` | string[] / null | Override the default order. |
| `preferences.filename_stem` | string | e.g. `Jane-Doe-Resume`. Default `<First>-<Last>-Resume`. |
| `preferences.stale_after_days` | int | Days before a freshness check-in. Default 30. |
| `preferences.deep_dive_every_days` | int | Days before suggesting a new deep dive. Default 90. |
| `preferences.title_overrides` | `{ "<experience id>": {applies_to, title, acknowledged} }` | **User-set only.** Shows `title` in place of the real title on matching resumes. `applies_to`: `ic` (target role isn't a manager/lead role), `manager`, or `all`. `acknowledged` records that the user was told the real title and the background-check risk. Optional `excludes` describes target roles where the real title is used instead (e.g. hybrid lead roles). The real title in `experience[]` is never changed. |

## Updating meta

When the user says "add…", "update…", "I also…", "I forgot…", or answers a
gap question:

0. Set `last_updated` to today (YYYY-MM-DD) and clear `stale_snoozed_until`.
   After writing, run `./build.sh --data-push "meta: <what changed>"`.
1. Put the information in its most specific structured slot. A new metric on a
   known achievement goes in that achievement's `metrics`, not in `facts`.
2. If no slot fits, append to `facts` with a clear `q` (the question it
   answers) and `a` (the user's answer, close to verbatim), plus `tags` that
   will help find it later (`["kubernetes", "infra"]`).
3. Set `added` to today's date (YYYY-MM-DD).
4. If the new fact backs a term in `declined` ("I now use Kubernetes at…"),
   remove that `declined` entry.
5. Never delete or overwrite an existing fact silently. If new info
   contradicts old, show both and ask which is right.
6. Echo back what was saved and where, in one or two lines.

Raw files the user drops into `meta/inbox/` (old resume PDF, LinkedIn export,
notes, previous JSON) are **input to normalize**: read them, move their facts
into meta.json, and tell the user what was imported and what was ambiguous.
Leave the inbox files in place — they are the audit trail.

## Evidence lookup (used during tailoring)

A keyword is **backed** if it appears (case-insensitive, alias-aware) in any
of: `experience[].tech`, `experience[].achievements[].{text,how,tech}`,
`projects[].{description,tech,achievements}`, `skills.*`, `certifications`,
`education`, or `facts[].{q,a,tags}`. A keyword in `declined` is never
backed, even if it appears elsewhere — ask the user to resolve the conflict.

## Freshness check-in

`python3 lib/meta_status.py <profile dir>` reports the effective last-update
date. That's the latest of `last_updated`, the last git commit touching
meta.json, and an uncommitted hand edit. It also reports whether that date is
past `preferences.stale_after_days`, and whether a snooze is active.

When `stale` is true on a Tailor or General run, don't send a generic "update
your meta?". Build **targeted** questions from meta itself, most valuable
first, and ask them with AskUserQuestion (max 4 per call, one or two rounds):

1. **Current role still current?** "Still at <organization> as <title>?"
   Also ask about any new role, promotion or title change.
2. **Pending statuses:** every achievement with a `status` field (e.g.
   "in testing, not GA"). "Has <feature> launched? Any adoption numbers yet?"
3. **New work in the current role:** "Anything shipped at <org> since
   <last_updated>?" Offer the categories from existing achievements.
4. **Missing metrics:** current and previous-role achievements with empty
   `metrics`. "Do you have a number for <achievement>?"
5. **`_open_questions`**: anything still unresolved.
6. **Goals:** "Still targeting <target_roles>?"

Always include a way to say *nothing changed* and a way to *skip for now*.
Both set `stale_snoozed_until` to today + 7 days and continue the build.
Only a real change to meta resets `last_updated`; a review with nothing new
doesn't. Save
answers per "Updating meta" above, then continue to the requested workflow.

## Deep-dive interview

The deep dive is how meta gets good. Run it at onboarding, whenever the user
says "deep dive" / "interview me" / "enrich my meta", and offer it every
`deep_dive_every_days`.

**Open with this framing (in your own words):** the more you tell me, the
better every future resume gets. This is a one-time investment. Rough notes
are fine; I'll turn them into bullets. Details you think are boring
(numbers, what broke, what you'd do differently) are usually the most
valuable. You can stop at any time; everything is saved as we go.

**Procedure:**
1. Run `python3 lib/meta_completeness.py <profile dir>`. Show the overall
   score and the `weakest` roles, then go in that order.
2. For each role:
   - **Brain-dump:** "List everything you worked on at <org>. One line
     each, rough is fine." Take this as free chat text. Add new items as
     achievements with just `text`.
   - **Role context**, for fields in `context_missing`: company and product
     (`company_context`), team and reporting line, recognition, and the
     private why joined / why left.
   - **Drill each achievement**, weakest first. Ask only about its
     `missing` fields, up to 4 questions per AskUserQuestion round. Free
     text works better for why and how, so ask those in chat.
3. Save after each achievement (`last_updated`, then
   `./build.sh --data-push "meta: deep dive <org>/<item>"`).
4. At the end, set `last_deep_dive` to today and rerun the score to show the
   before and after. Then give the redo advice: *memory comes back in layers.
   Rerun the deep dive every few months, or right after a big project, and
   you'll recall things worth adding.*

**Question bank**. Phrase questions to trigger recall, not self-assessment:

| Field | Ask |
|---|---|
| why / need | What was broken or painful before this existed? Who was asking for it, and why then? |
| how | Walk me through how it works. What was the key design decision? |
| tech | What did you build it with? Anything you introduced to the stack? |
| metrics / scale | What number changed: latency, cost, volume, errors, revenue, time saved? How big was it (users, rows/day, RPS, accounts)? What number did your manager care about? |
| outcomes | What happened after it shipped? Adopted as the default? Unblocked a deal? Fewer incidents? |
| ownership | Did you do this solo, lead it, or contribute? What exactly was your part? Who else was involved? |
| challenges / alternatives | What was the hardest part? What else did you consider, and why not that? |
| constraints | Deadline, team size, legacy system, budget? |
| learnings | What would you do differently? What did it teach you? |
| dates / status / links | When did it ship? Is it live, in pilot or deprecated? Any PR, doc, demo or case study? |

Never fill a field with a guess. An empty field is better than a wrong one,
and the score just reflects it.
