#!/usr/bin/env python3
"""Score how complete a profile's meta.json is, and list what's missing.

Usage:
  python3 lib/meta_completeness.py <profile dir>

Prints JSON: an overall score (0-100), per-role scores, the missing fields of
every achievement, and `weakest`, the roles to deep-dive first. The create-resume
skill uses it to aim deep-dive questions where the gaps are.

Scoring
  achievement  weighted fields, summing to 100 (see ACHIEVEMENT_WEIGHTS)
  role         60% mean of its achievements + 40% role context
               (capped at 50 with fewer than 2 achievements)
  profile      recency-weighted mean of roles: most recent x3, next x2, rest x1
"""

import json
import os
import sys

ACHIEVEMENT_WEIGHTS = {
    "why": 15,
    "how": 15,
    "metrics_or_scale": 20,
    "tech": 10,
    "ownership": 10,
    "outcomes": 10,
    "challenges": 10,
    "learnings": 5,
    "dates_or_status": 5,
}

ROLE_CONTEXT_WEIGHTS = {
    "company_context": 15,
    "team": 10,
    "recognition": 10,
    "reporting_to": 5,
}


def filled(value):
    if isinstance(value, dict):
        return any(filled(v) for k, v in value.items() if not k.startswith("_"))
    if isinstance(value, (list, tuple)):
        return any(filled(v) for v in value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None and value is not False


def achievement_checks(ach):
    return {
        "why": filled(ach.get("why")) or filled(ach.get("need")),
        "how": filled(ach.get("how")),
        "metrics_or_scale": filled(ach.get("metrics")) or filled(ach.get("scale")),
        "tech": filled(ach.get("tech")),
        "ownership": filled((ach.get("ownership") or {}).get("role")),
        "outcomes": filled(ach.get("outcomes")),
        "challenges": filled(ach.get("challenges")) or filled(ach.get("alternatives")),
        "learnings": filled(ach.get("learnings")),
        "dates_or_status": filled(ach.get("start")) or filled(ach.get("status")),
    }


def score_achievement(ach):
    checks = achievement_checks(ach)
    score = sum(ACHIEVEMENT_WEIGHTS[k] for k, ok in checks.items() if ok)
    return score, [k for k, ok in checks.items() if not ok]


def score_role(role):
    achievements = [a for a in role.get("achievements", []) if isinstance(a, dict)]
    scored = []
    for ach in achievements:
        score, missing = score_achievement(ach)
        scored.append({"id": ach.get("id", ""), "text": ach.get("text", "")[:70],
                       "score": score, "missing": missing})
    ach_mean = sum(a["score"] for a in scored) / len(scored) if scored else 0

    context_missing = [k for k in ROLE_CONTEXT_WEIGHTS if not filled(role.get(k))]
    context = sum(w for k, w in ROLE_CONTEXT_WEIGHTS.items() if k not in context_missing)
    context_pct = 100 * context / sum(ROLE_CONTEXT_WEIGHTS.values())

    score = 0.6 * ach_mean + 0.4 * context_pct
    if len(scored) < 2:
        score = min(score, 50)
    return {
        "id": role.get("id", ""),
        "organization": role.get("organization", ""),
        "score": round(score),
        "achievement_count": len(scored),
        "context_missing": context_missing,
        "achievements": sorted(scored, key=lambda a: a["score"]),
    }


def analyse(meta):
    roles = [score_role(r) for r in meta.get("experience", []) if isinstance(r, dict)]
    weights = [3, 2] + [1] * max(0, len(roles) - 2)
    total_weight = sum(weights[:len(roles)])
    overall = (sum(r["score"] * w for r, w in zip(roles, weights)) / total_weight
               if roles else 0)
    # Priority: how much is missing, scaled by how recent (and so how read) the role is.
    ranked = sorted(zip(roles, weights), key=lambda rw: -(100 - rw[0]["score"]) * rw[1])
    return {
        "score": round(overall),
        "roles": roles,
        "weakest": [{"id": r["id"], "organization": r["organization"], "score": r["score"]}
                    for r, _ in ranked],
    }


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = os.path.join(argv[1], "meta", "meta.json")
    if not os.path.isfile(path):
        print(json.dumps({"error": f"missing {path}"}))
        return 0
    with open(path, encoding="utf-8") as handle:
        print(json.dumps(analyse(json.load(handle)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
