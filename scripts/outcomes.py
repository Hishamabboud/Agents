#!/usr/bin/env python3
"""Outcome tracking — the missing feedback loop.

WHY THIS EXISTS
---------------
After 414 submitted applications the tracker held zero employer replies. Every `response`
field contained submission metadata ("awaiting", "HTTP 201"), not outcomes. So there was
no way to answer the only questions that matter:
    which role levels actually get replies?
    which companies/sectors convert?
    is the tailored letter beating the generic one?

Without this the pipeline optimises "applications sent", which is not the goal.

USAGE
-----
  # record an outcome (fuzzy-matches the company, and role if given)
  python3 scripts/outcomes.py log "Xsens" --outcome interview --note "call 12 Aug"
  python3 scripts/outcomes.py log "Infomedics" --role ".Net" --outcome rejected

  # bulk import: paste/forward replies into one file, one per line:
  #   Company | outcome | optional note
  python3 scripts/outcomes.py import replies.txt

  # see what is actually converting
  python3 scripts/outcomes.py report

OUTCOMES: interview | rejected | ghosted | offer | withdrawn | acknowledged
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

APPS = Path(__file__).resolve().parent.parent / "data" / "applications.json"
VALID = {"interview", "rejected", "ghosted", "offer", "withdrawn", "acknowledged"}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load():
    return json.load(open(APPS))


def save(apps):
    json.dump(apps, open(APPS, "w"), indent=2, ensure_ascii=False)


def find(apps, company, role=None):
    """Fuzzy-match applications by company (and role substring if supplied)."""
    c = _norm(company)
    out = []
    for a in apps:
        ac = _norm(a.get("company"))
        if not ac or not c:
            continue
        if c in ac or ac in c:
            if role and role.lower() not in (a.get("role") or "").lower():
                continue
            out.append(a)
    return out


def log(company, outcome, role=None, note=None, when=None):
    if outcome not in VALID:
        sys.exit(f"outcome must be one of {sorted(VALID)}")
    apps = load()
    hits = [a for a in find(apps, company, role) if a.get("status") == "applied"]
    if not hits:
        print(f"no applied entry found for {company!r}"
              + (f" role~{role!r}" if role else ""))
        return 0
    if len(hits) > 1 and not role:
        print(f"{len(hits)} applications match {company!r} — narrow with --role, or all get tagged:")
        for h in hits:
            print(f"    id={h['id']} {h.get('role')}")
    for h in hits:
        h["outcome"] = outcome
        h["outcome_date"] = when or datetime.now().date().isoformat()
        if note:
            h["outcome_note"] = note
    save(apps)
    print(f"tagged {len(hits)} application(s) at {company} as {outcome}")
    return len(hits)


def bulk_import(path):
    n = 0
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            print(f"  skipped (need 'Company | outcome'): {line[:60]}")
            continue
        company, outcome = parts[0], parts[1].lower()
        note = parts[2] if len(parts) > 2 else None
        if outcome not in VALID:
            print(f"  skipped (bad outcome {outcome!r}): {line[:60]}")
            continue
        n += log(company, outcome, note=note)
    print(f"\nimported {n} outcome(s)")


def report():
    apps = load()
    applied = [a for a in apps if a.get("status") == "applied"]
    with_out = [a for a in applied if a.get("outcome")]
    print(f"{len(applied)} applications sent, {len(with_out)} with a recorded outcome "
          f"({100*len(with_out)/max(len(applied),1):.1f}% measured)\n")
    if not with_out:
        print("No outcomes recorded yet — nothing can be concluded about what converts.")
        print("Log replies as they arrive:  python3 scripts/outcomes.py log \"Company\" --outcome interview")
        return

    print("outcomes:", dict(Counter(a["outcome"] for a in with_out)), "\n")

    def bucket_report(title, keyfn):
        buckets = defaultdict(lambda: Counter())
        for a in with_out:
            buckets[keyfn(a)][a["outcome"]] += 1
        rows = []
        for k, c in buckets.items():
            tot = sum(c.values())
            good = c["interview"] + c["offer"]
            rows.append((good / tot, tot, k, dict(c)))
        rows.sort(reverse=True)
        print(f"--- {title} (by interview+offer rate) ---")
        for rate, tot, k, c in rows:
            if tot >= 2:
                print(f"  {str(k)[:34]:34s} {rate*100:5.0f}%  n={tot:3d}  {c}")
        print()

    def level(a):
        t = (a.get("role") or "").lower()
        if "senior" in t or "lead" in t or "principal" in t: return "senior/lead"
        if "junior" in t or "medior" in t or "mid" in t or "trainee" in t: return "junior/medior"
        return "unspecified"

    def stack(a):
        t = (a.get("role") or "").lower()
        for k, lbl in ((r"\.net|c#", ".NET/C#"), (r"python", "Python"),
                       (r"data|analytics", "Data"), (r"devops|cloud|platform", "Cloud/DevOps"),
                       (r"test|qa", "Test/QA"), (r"full.?stack", "Fullstack")):
            if re.search(k, t): return lbl
        return "other"

    bucket_report("by seniority in title", level)
    bucket_report("by stack", stack)
    bucket_report("by ATS", lambda a: a.get("ats", "unknown"))
    bucket_report("by country", lambda a: a.get("country", "unknown"))
    bucket_report("by cover-letter style", lambda a: "tailored" if a.get("letter_tailored") else "generic")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log");     lg.add_argument("company"); lg.add_argument("--role")
    lg.add_argument("--outcome", required=True); lg.add_argument("--note"); lg.add_argument("--date")
    im = sub.add_parser("import");  im.add_argument("path")
    sub.add_parser("report")
    a = p.parse_args()
    if a.cmd == "log":      log(a.company, a.outcome, a.role, a.note, a.date)
    elif a.cmd == "import": bulk_import(a.path)
    else:                   report()
