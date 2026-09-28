#!/usr/bin/env python3
"""Report how fresh a profile's meta.json is.

Usage:
  python3 lib/meta_status.py <profile dir> [--today YYYY-MM-DD]

Prints JSON and always exits 0; the create-resume skill decides what to do:

  {"last_updated": "2026-09-28", "days": 0, "threshold": 30,
   "stale": false, "snoozed_until": null, "sources": {...},
   "days_since_deep_dive": null, "deep_dive_due": true}

deep_dive_due is true when meta.last_deep_dive is missing or older than
preferences.deep_dive_every_days (default 90).

The effective update date is the latest of:
  - meta.last_updated        set by the skill on every change it makes
  - the last git commit that touched meta/meta.json (catches hand edits
    made and committed on any machine)
  - the file's mtime, but only while it has uncommitted changes (catches a
    hand edit not yet committed; mtime alone is meaningless after a clone)
"""

import datetime
import json
import os
import subprocess
import sys

DEFAULT_THRESHOLD = 30
DEFAULT_DEEP_DIVE_DAYS = 90


def parse_day(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def git(meta_path, *args):
    try:
        out = subprocess.run(
            ["git", "-C", os.path.dirname(meta_path)] + list(args),
            capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def status(profile_dir, today):
    meta_path = os.path.abspath(os.path.join(profile_dir, "meta", "meta.json"))
    if not os.path.isfile(meta_path):
        return {"error": f"missing {meta_path}"}
    with open(meta_path, encoding="utf-8") as handle:
        meta = json.load(handle)

    sources = {
        "last_updated": parse_day(meta.get("last_updated")),
        "git_commit": parse_day(git(meta_path, "log", "-1", "--format=%cs", "--", "meta.json")),
        "uncommitted_edit": None,
    }
    if git(meta_path, "status", "--porcelain", "--", "meta.json"):
        sources["uncommitted_edit"] = datetime.date.fromtimestamp(os.path.getmtime(meta_path))

    dates = [d for d in sources.values() if d]
    effective = max(dates) if dates else None
    prefs = meta.get("preferences") or {}
    threshold = prefs.get("stale_after_days") or DEFAULT_THRESHOLD
    deep_every = prefs.get("deep_dive_every_days") or DEFAULT_DEEP_DIVE_DAYS
    deep = parse_day(meta.get("last_deep_dive"))
    deep_days = (today - deep).days if deep else None
    snoozed = parse_day(meta.get("stale_snoozed_until"))
    days = (today - effective).days if effective else None
    overdue = days is None or days > threshold
    is_snoozed = bool(snoozed and snoozed >= today)

    return {
        "last_updated": effective.isoformat() if effective else None,
        "days": days,
        "threshold": threshold,
        "stale": overdue and not is_snoozed,
        "snoozed_until": snoozed.isoformat() if is_snoozed else None,
        "sources": {k: v.isoformat() if v else None for k, v in sources.items()},
        "days_since_deep_dive": deep_days,
        "deep_dive_due": deep_days is None or deep_days > deep_every,
    }


def main(argv):
    args = argv[1:]
    today = datetime.date.today()
    if "--today" in args:
        index = args.index("--today")
        today = datetime.date.fromisoformat(args[index + 1])
        del args[index:index + 2]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(status(args[0], today), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
