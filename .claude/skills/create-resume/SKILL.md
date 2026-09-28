---
name: create-resume
version: 2.4.0
description: Build an ATS-optimized resume PDF (LaTeX) from the user's own career facts, tailored to a pasted job description or, with no JD, to their stated career goals. Also onboards new users and adds or updates their career facts (meta). Never fabricates; asks before using any claim not in meta. Use for "/create-resume", "create/build/tailor my resume", "resume for this JD", "add this to my resume/meta", "I also worked on…", or when the user pastes a job description and wants a resume.
---

# Create Resume

One entry point: `/create-resume [anything]`. Work out what the user wants from
the arguments, then run exactly one workflow below.

**The one rule that overrides everything:** the resume may only state what
`meta.json` supports. If a claim would help but isn't in meta, *ask* the user;
save a yes to meta, save a no to `declined`. Past job titles are never altered,
with one exception: an entry the user set themselves in
`preferences.title_overrides` (see `reference/meta-schema.md`). Never create
one on your own initiative. If the user asks for one, first tell them the
real title and that background checks verify it, then save it only if they
confirm.
A fabricated metric or skill is a serious defect, not a rough draft.

## Where things live

```
resume-data/                            the user's own PRIVATE git repo, cloned here;
                                        gitignored by this tool repo
  profiles/<name>/meta/meta.json        the fact base (reference/meta-schema.md)
  profiles/<name>/meta/inbox/           raw files to import (old resume, LinkedIn export, notes)
  profiles/<name>/resume.json           master for evergreen builds (./build.sh --profile)
  applications/<name>/index.md          one row per application
  applications/<name>/<date>-<co>-<role>/   one tailored build (reference/schema.md → Application dirs)
```

Read these references when the workflow step says to — not all up front:

- `reference/meta-schema.md` — meta.json fields, how to update, evidence lookup
- `reference/jd-intake.md` — detecting and normalizing JD input
- `reference/ats-rules.md` — keyword extraction, composition, fit loop, regional rules
- `reference/writing-rules.md` — global bullet rules (plus the user's `preferences.rules`)
- `reference/schema.md` — resume.json / settings.json the renderer accepts

## Step 0 — Route

1. **Data repo.** Before anything else:
   - `resume-data/` missing and an old `data/` present → run
     `./build.sh --migrate-data`, then `--init-data`, then offer the GitHub step
     below.
   - `resume-data/` missing → ask: *"Do you already have a resume-data repo
     (e.g. on another machine)?"*
     - Yes → ask for the git URL and run `./build.sh --init-data <url>`.
     - No → run `./build.sh --init-data`, then onboard. Afterwards offer to
       create the private GitHub repo:
       `gh repo create <github-user>/resume-data --private --source resume-data --remote origin --push`.
       It must be **private**: it holds contact details and every application.
   - Otherwise run `./build.sh --data-pull`.
     - **Exit 3 (diverged):** stop. Diff the local and remote `meta.json`
       (`git -C resume-data diff HEAD...@{u} -- '*meta.json'` and the reverse),
       show conflicting facts side by side, ask which is right, write the
       merged file, commit, and push. Never pick a side silently.
2. **Profile.** List `resume-data/profiles/*/` (ignore names starting with `_`).
   None → **Onboard**. One → use it. Several → ask which (or use one the user
   named).
3. **Meta readiness.** If `meta/meta.json` is missing, or has no `basics.name`
   and no `experience`, → **Onboard** (even if a JD was passed; keep the JD and
   resume tailoring once onboarding is done).
4. **Intent**, from the arguments:
   - empty → **General**
   - add/update language ("add…", "update…", "I also…", "I forgot…",
     "change my…", "remember that…") → **Meta update**
   - "mark <company> as applied / interviewing / rejected / offer" → update
     that row's Status in `resume-data/applications/<name>/index.md` (statuses:
     `draft`, `applied`, `interviewing`, `rejected`, `offer`), then stop
   - "deep dive", "interview me", "enrich my meta" → **Deep dive**
   - "rebuild", "evergreen", "build all" → **Evergreen**
   - JD input per `reference/jd-intake.md` → **Tailor**
   - unclear → ask one short question
5. **Freshness** (Tailor and General only). Run
   `python3 lib/meta_status.py resume-data/profiles/<name>`. If `"stale": true`,
   do the check-in from `reference/meta-schema.md` → Freshness check-in before
   building: open with *"Your meta was last updated N days ago"*, then ask
   targeted questions. The answers go into meta as usual, which resets the
   clock. If the user skips, set `stale_snoozed_until` to today + 7 days.
   Separately, if `"deep_dive_due": true`, add one line after the build:
   *"It's been a while since a deep dive (or you've never done one). Your meta
   is N% complete; `/create-resume deep dive` would strengthen your bullets."*
   Get N from `lib/meta_completeness.py`. It never blocks the build.

**After every change**, whether a meta write or an application build: run
`./build.sh --data-push "<message>"` with a short descriptive message, e.g.
`meta: add Acme Slack bot metrics`, `app: zomato sde-backend`,
`index: mark Zomato applied`. The push is automatic; don't ask.

## Workflow: Onboard

Goal: a filled `meta.json` without inventing anything.

1. If the profile dir doesn't exist: `./build.sh --new <name>` (ask for a short
   lowercase name, e.g. first name). That copies the blank template into
   `meta/meta.json`.
2. Offer three ways in, and let the user mix them:
   - **Import:** drop an old resume PDF, a LinkedIn "Save to PDF", or notes
     into `resume-data/profiles/<name>/meta/inbox/`, or paste them in chat. Read them
     and normalize them into meta.json.
   - **Fill the template:** the user edits `meta/meta.json` directly (the
     `_hints` and `_example_*` keys explain each field).
   - **Interview:** basics → target roles and region → each role's title
     and dates → projects → education and certifications → skills →
     anything else (goes to `facts`). Then run the **Deep dive** workflow for
     the substance of each role. Write to meta.json after each round so
     nothing is lost.
3. After importing, list anything ambiguous (overlapping dates, missing end
   dates, a metric without context) and ask about it. Don't resolve it yourself.
4. Finish by summarizing what's in meta and what's thin (e.g. "no metrics for
   the 2021 role"), then continue to the workflow the user originally asked
   for.

## Workflow: Deep dive

The most valuable thing the skill does. Follow `reference/meta-schema.md` →
Deep-dive interview:

1. Open with the framing: more detail means better resumes; it's a one-time
   investment; rough notes are fine; you can stop at any time.
2. Run `lib/meta_completeness.py`, show the score and weakest roles.
3. For each role, weakest first: brain-dump the list of work, fill the role
   context, then drill each achievement's missing fields.
4. Save and `--data-push` after every achievement.
5. Finish by setting `last_deep_dive`, showing the before/after score, and
   giving the redo advice (rerun every few months or after a big project).

## Workflow: Meta update

Follow `reference/meta-schema.md` → Updating meta. Put each piece in its most
specific slot; anything that doesn't fit goes in `facts` as a `{q, a}` pair.
Confirm in one or two lines what was saved and where. Don't rebuild unless
asked.

## Workflow: Tailor (JD given)

1. **Intake.** Follow `reference/jd-intake.md`: create the application dir and
   write `jd.txt`.
2. **Extract keywords.** Following `reference/ats-rules.md` §2, write
   `keywords.json` (must / nice, exact JD spellings, aliases, categories,
   role_title, seniority, company).
3. **Check evidence.** For each keyword, look it up in meta
   (`meta-schema.md` → Evidence lookup). Sort into:
   - **backed**: use it
   - **declined**: skip silently and list it in the report
   - **unbacked**: ask
   - **inferable**: meta strongly implies it, but it isn't stated; ask
4. **Ask once, in a batch.** Use AskUserQuestion, up to 4 questions per call,
   must-haves first, one question per keyword. Options: *Yes, I've used it
   (tell me where)* / *Adjacent: I've done something similar* / *No*.
   - Yes or Adjacent → record the user's words in meta (the right slot, or
     `facts` with `source: "jd-gap"`), then treat the keyword as backed, but
     only to the extent the answer supports. "Adjacent" backs the adjacent
     thing, not the JD term.
   - No → append `{term, date}` to `declined`.
   - If more than about 8 keywords are unbacked, ask about the must-haves and
     list the rest in the report, rather than burying the user in questions.
5. **Compose `resume.json` and `settings.json`** in the application dir, from
   meta only:
   - Use the section order, summary, skills grouping, bullet counts and
     keyword placement rules from `ats-rules.md` §3–4.
   - Write bullets per `writing-rules.md` plus the user's `preferences.rules`.
   - Use the JD's vocabulary where it describes the same fact.
   - Header: name, email, phone (unless `include_phone: false`), location,
     and links from `basics`.
   - Set `settings.json` `documents[0].basename` per `ats-rules.md` §7.
   - Apply any matching `preferences.title_overrides` (by experience `id`
     and `applies_to`), drop bullets that contradict the overridden title
     (e.g. "Promoted to <real title>"), and list the override under
     **Title overrides** in report.md.
   - Start *with* a summary; the fit loop decides whether it stays.
6. **Build:** `./build.sh --app <dir>`. On a LaTeX error, fix the content
   (usually a stray character) and rebuild.
7. **Fit loop:** follow `ats-rules.md` §5 until the page count is within the
   limit. **Content always beats the summary:** trim without it, restore
   trimmed content first, and add the summary last, only if it fits without
   changing anything else. Never shorten or drop a detail to make room for a
   summary. Priority: full-time content, then relevant internships (3+ years of
   experience; see `ats-rules.md` §4 Internships), then the summary.
8. **Coverage:** `python3 lib/coverage.py <dir>`. If a *backed* must-have
   shows MISSING, or "JD spelling missing", fix the composition and go back to
   step 6. That's a composition bug, not a gap.
9. **Report:** write `report.md` in the dir: a header (company, role, date,
   pages, PDF filename), the coverage Markdown the script printed, then:
   - **Gaps**: declined terms, unasked terms, and requirements like years of
     experience or a degree that the profile doesn't meet
   - **Would be stronger with a number**: bullets without metrics that
     matter for this JD
   - **Rewordings**: bullets whose wording was changed to use JD terms, with
     the original meta text beside each, so the user can check nothing drifted

   Also write `interview-prep.md` in the dir. It's for the user only and
   may use `private.*`:
   - **60-second pitch:** current role, strongest 2–3 achievements for this
     JD, and why this company/role (from `goals`).
   - **3–5 STAR stories**, one per top must-have: Situation (`why`/`need`),
     Task (`ownership`), Action (`how`, `challenges`, `alternatives`), Result
     (`metrics`, `outcomes`), plus a "what I learned" line (`learnings`).
     Only meta facts. If a field is empty, say so rather than filling it.
   - **Talking points:** why leaving (`private.why_left`), any applied
     `title_overrides` and how to explain them, and declined keywords with an
     honest "haven't used it, closest is X" answer.
10. **Index:** add or update the row in `resume-data/applications/<name>/index.md`
    (create it with the header if it's missing):
    ```
    | Date | Company | Role | Must % | Nice % | Pages | Status | Folder |
    |---|---|---|---|---|---|---|---|
    ```
    Status starts as `draft`. The user can say "mark Acme as applied /
    interviewing / rejected / offer", and you update the row.
11. **Review with the user.** Show the PDF path, the must/nice coverage, the
    top gaps, and the 2–3 weakest bullets. Offer specific tweaks. If they ask
    for a change, edit the application `resume.json` and rerun steps 6–10. If
    the change adds a new fact, save it to meta too.

## Workflow: General (no JD)

Same as **Tailor** from step 2, except:

- The application dir is `<date>-general-<primary target role slug>`, with no
  `jd.txt`.
- `keywords.json` is synthesized: `role_title` = `goals.target_roles[0]`;
  **must** = `goals.ats_keywords` plus the core stack for that role, taken
  from the user's own most recent roles; **nice** = the other target roles'
  typical terms that meta backs.
- Don't ask gap questions about synthesized keywords unless they came from
  `goals.ats_keywords`.
- If `goals.target_roles` is empty, ask for the target role and seniority
  first, and save them to meta.

## Workflow: Evergreen

`./build.sh --check --profile <name>`, then `./build.sh --profile <name>`.
This builds the documents × variants matrix from the profile's master
`resume.json` into `resume-data/final/`. It's the pre-JD flow, kept for fixed
variants such as a LinkedIn copy. See `reference/schema.md`.

## Before handing back — checklist

- [ ] Every claim traces to meta.json; nothing invented, no title changed.
- [ ] Within the page limit; no spill onto a partial page.
- [ ] No content was shortened or dropped to fit the summary; every trim that
      stayed out is listed in report.md.
- [ ] Internship rule applied (3+ years: only relevant internships, and only
      with space to spare); omitted internships noted in report.md.
- [ ] Must-have coverage checked; each backed must-have is present.
- [ ] Repeated-word check from `writing-rules.md` done; no verb starts more than 2 bullets.
- [ ] The user's `preferences.rules` applied.
- [ ] report.md, interview-prep.md and index.md written.
- [ ] Nothing from `private.*` on the resume.
- [ ] Anything the user newly confirmed is saved to meta.

## Maintaining this skill

The repo README documents only the current version of this skill. Any change
to this skill folder, `build.sh`, `lib/` or `templates/` must, in the same
change, update the affected README sections, bump `version` above and the
README's version line (semver: MAJOR = breaking format, layout or behaviour
change), and add a README changelog entry. Breaking entries are marked
**BREAKING** with "How to migrate" steps. See the README's "Maintaining"
section and `CLAUDE.md`.
