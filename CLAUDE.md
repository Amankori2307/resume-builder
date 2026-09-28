# resume-builder

A Claude Code skill (`/create-resume`) plus a LaTeX build that produces
ATS-optimized resume PDFs from a user's own facts. The skill lives in
`.claude/skills/create-resume/SKILL.md`; user-facing docs are in `README.md`.

## Keep the README in sync

`README.md` documents **only the current version** of the skill. Whenever you
change anything in `.claude/skills/create-resume/`, `build.sh`, `lib/` or
`templates/`, do all of the following in the same change:

1. Update every README section the change affects (commands, workflows,
   files, meta fields, preferences, troubleshooting). Remove anything that is
   no longer true; don't keep notes about old behaviour outside the changelog.
2. Bump `version` in the SKILL.md frontmatter and the "Current version" line
   at the top of the README. Both must match.
3. Add an entry at the top of the README's `## Changelog`.

Semver:
- **MAJOR**: breaking changes to the `meta.json` / `resume.json` /
  `settings.json` format, the `resume-data/` layout, or command behaviour. Mark the
  entry **BREAKING** and include "How to migrate" steps.
- **MINOR**: new features.
- **PATCH**: fixes and doc-only corrections.

## Never commit personal data

All personal data (profiles, meta, applications, builds) lives in
`resume-data/`: the user's own **private** git repo, cloned inside this folder
and gitignored here. Never add it to this repo, never reference it from here
(no submodule), and never make it public. Sync it only via
`./build.sh --data-pull` / `--data-push`. Don't add real names, contact details
or resumes anywhere in this repo; examples in docs use fictional people.
