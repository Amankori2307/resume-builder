#!/usr/bin/env python3
"""Measure how well a rendered resume covers a job description's keywords.

Usage:
  python3 lib/coverage.py <application dir>

Reads, from the application dir:
  keywords.json  extracted JD keywords (see the create-resume skill)
  resume.txt     plain-text rendering written by ./build.sh --app
  resume.json    used only to find section titles

Writes coverage.json next to them and prints a Markdown summary to stdout.

This is deliberately deterministic: the skill decides which keywords matter,
this script only answers "does the text an ATS will parse actually contain
them, and where".

keywords.json shape:
  {
    "company": "Acme", "role_title": "Senior Backend Engineer",
    "must": [{"term": "Node.js", "aliases": ["NodeJS"], "category": "language"}],
    "nice": [{"term": "Kafka", "aliases": [], "category": "infra"}]
  }
"""

import json
import os
import re
import sys

STUFFING_THRESHOLD = 5


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle) if path.endswith(".json") else handle.read()


def spellings(term, aliases):
    """The term, its aliases, and punctuation-free forms of each.

    ATS matching is usually literal, so 'Node.js' and 'NodeJS' are different
    strings to a parser; checking the collapsed form tells us the concept is
    present even if the exact JD spelling is not.
    """
    forms = []
    for raw in [term] + list(aliases or []):
        base = raw.strip().lower()
        if not base:
            continue
        for form in (base, base.replace(".", ""), base.replace("-", " "),
                     re.sub(r"[.\-\s]", "", base)):
            if form and form not in forms:
                forms.append(form)
    return forms


def pattern(form):
    return re.compile(r"(?<![a-z0-9])" + re.escape(form) + r"(?![a-z0-9])")


def split_sections(text, titles):
    """Map each line of resume.txt to the section heading above it."""
    headings = {t.upper() for t in titles}
    current, sections = "HEADER", {"HEADER": []}
    for line in text.splitlines():
        if line.strip() in headings:
            current = line.strip()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return {name: "\n".join(lines).lower() for name, lines in sections.items()}


def analyse(app_dir):
    keywords = load(os.path.join(app_dir, "keywords.json"))
    text = load(os.path.join(app_dir, "resume.txt"))
    resume = load(os.path.join(app_dir, "resume.json"))
    titles = [s.get("title", "") for s in resume.get("sections", [])]
    sections = split_sections(text, titles)
    full = text.lower()

    results = {"tiers": {}, "terms": []}
    for tier in ("must", "nice"):
        entries = keywords.get(tier, [])
        covered = 0
        for entry in entries:
            if isinstance(entry, str):
                entry = {"term": entry}
            term = entry["term"]
            exact = pattern(term.lower())
            hits, total = {}, 0
            for name, body in sections.items():
                count = max(len(pattern(f).findall(body))
                            for f in spellings(term, entry.get("aliases")))
                if count:
                    hits[name] = count
                    total += count
            if total:
                covered += 1
            results["terms"].append({
                "term": term,
                "tier": tier,
                "category": entry.get("category", ""),
                "hits": hits,
                "total": total,
                "exact_spelling": bool(exact.search(full)),
                "stuffed": total >= STUFFING_THRESHOLD,
            })
        results["tiers"][tier] = {
            "covered": covered,
            "total": len(entries),
            "pct": round(100 * covered / len(entries)) if entries else 100,
        }

    role = (keywords.get("role_title") or "").lower()
    results["role_title"] = keywords.get("role_title", "")
    results["role_title_present"] = bool(role) and role in full
    return results


def markdown(results):
    must, nice = results["tiers"]["must"], results["tiers"]["nice"]
    out = [
        "## Keyword coverage",
        "",
        f"- Must-have: **{must['covered']}/{must['total']}** ({must['pct']}%)",
        f"- Nice-to-have: **{nice['covered']}/{nice['total']}** ({nice['pct']}%)",
    ]
    if results["role_title"]:
        mark = "yes" if results["role_title_present"] else "no"
        out.append(f"- Target title \"{results['role_title']}\" appears verbatim: {mark}")
    out += ["", "| Keyword | Tier | Found in | Notes |", "|---|---|---|---|"]
    for term in results["terms"]:
        where = ", ".join(f"{k.title()} ×{v}" for k, v in term["hits"].items()) or "—"
        notes = []
        if term["total"] and not term["exact_spelling"]:
            notes.append("JD spelling missing")
        if term["stuffed"]:
            notes.append("possible stuffing")
        if not term["total"]:
            notes.append("MISSING")
        out.append(f"| {term['term']} | {term['tier']} | {where} | {'; '.join(notes)} |")
    return "\n".join(out) + "\n"


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    app_dir = argv[1]
    for name in ("keywords.json", "resume.txt", "resume.json"):
        if not os.path.isfile(os.path.join(app_dir, name)):
            print(f"error: missing {name} in {app_dir}", file=sys.stderr)
            return 1
    results = analyse(app_dir)
    with open(os.path.join(app_dir, "coverage.json"), "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    sys.stdout.write(markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
