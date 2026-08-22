#!/usr/bin/env python3
"""Export a manual-application queue — the bridge between this pipeline and a human browser.

Only ~5-7% of discovered companies expose an open API this pipeline may use. Everything
else — captcha-gated careers forms, Personio custom questions, roles held for screening
essays — needs a human in the loop. This compiles those into ONE file with everything
pre-computed (public URL, tailored letter, profile-backed answers, and exactly which
questions still need Hisham's own words), so a manual session is paste-work, not research.

The queue applies the SAME guards as the automated path (blocklist, tenant cap, seniority
bar, dedup against the tracker): a role the pipeline would refuse to automate is not a
role to hand-apply to either.

Usage:
    python3 scripts/export_queue.py candidates_r31.json [more.json ...]
Writes data/apply-queue.md.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from filters import (load_blocked_companies, blocked_reason, hard_blockers,
                     seniority_mismatch, tenant_counts, wrong_discipline)
import cover_letter
import questions
import personio_apply

BASE = Path(__file__).resolve().parent.parent
COUNTED = ("applied", "action_required", "duplicate_submitted",
           "overcap_submitted", "requires_manual_step")


def fetch_offer(c):
    try:
        url = f"https://{c['slug']}.recruitee.com/api/offers/{c['offer_slug']}"
        o = json.loads(subprocess.run(["curl", "-sL", "--max-time", "18", url],
                                      capture_output=True, text=True).stdout)
        return o.get("offer", o) or {}
    except Exception:
        return {}


def main(paths):
    apps = json.load(open(BASE / "data" / "applications.json"))
    blocked = load_blocked_companies(BASE / "profile" / "preferences.md")
    tcount = tenant_counts(apps, COUNTED)
    seen_cr = {f"{(a.get('company') or '').lower().strip()}|{(a.get('role') or '').lower().strip()}"
               for a in apps}
    salary, notice = personio_apply.read_commitments()

    cands, seen_key = [], set()
    for path in paths:
        for c in json.load(open(path)):
            k = (c["company"].lower().strip(), (c.get("role") or "").lower().strip())
            if k not in seen_key:
                seen_key.add(k)
                cands.append(c)

    entries, dropped = [], {}
    def drop(why): dropped[why] = dropped.get(why, 0) + 1

    for c in cands:
        co, role = c["company"], c.get("role") or ""
        if f"{co.lower().strip()}|{role.lower().strip()}" in seen_cr:
            drop("already applied"); continue
        if seniority_mismatch(role):
            drop("senior-only title"); continue
        if blocked_reason(co, c.get("slug"), blocked):
            drop("blocklisted"); continue
        tkey = (f"recruitee:{c['slug'].lower()}" if c["ats"] == "recruitee"
                else f"personio:{c['host'].split('.')[0].lower()}")
        if tcount.get(tkey, 0) >= 2:
            drop("tenant at 2-app cap"); continue

        if c["ats"] == "recruitee":
            offer = fetch_offer(c)
            if offer.get("status") != "published":
                drop("no longer open"); continue
            body = re.sub(r"<[^>]+>", " ", (offer.get("description") or "") +
                          " " + (offer.get("requirements") or ""))
            if hard_blockers(role, body):
                drop("hard blocker in live text"); continue
            if wrong_discipline(role, body, offer.get("department") or ""):
                drop("not a software role"); continue
            oq = offer.get("open_questions") or []
            url = f"https://{c['slug']}.recruitee.com/o/{c['offer_slug']}"
        else:
            # The clearance/defence/language blockers live in the body, and Personio bodies
            # are only in the feed. Round 31 held NUNC Capital for "clearance" -- an
            # exporter that skips this check would have handed that same role to a human.
            try:
                xml = subprocess.run(["curl", "-s", "--max-time", "20",
                                      f"https://{c['host']}/xml"],
                                     capture_output=True, text=True).stdout
                m = re.search(rf"<position>(?:(?!</position>).)*?<id>{c['job_id']}</id>"
                              rf".*?</position>", xml, re.S)
                body = re.sub(r"<[^>]+>", " ", m.group(0)) if m else ""
                if not m:
                    drop("no longer open"); continue
            except Exception:
                body = ""
            if hard_blockers(role, body):
                drop("hard blocker in live text"); continue
            oq = []
            url = f"https://{c['host']}/job/{c['job_id']}"

        letter, matched = cover_letter.build(co, role, c.get("city") or "",
                                             c.get("country", "NL"), body)
        answers, blockers = questions.build_answers(oq, salary, notice)
        entries.append({"c": c, "url": url, "letter": letter, "matched": matched,
                        "answers": answers, "blockers": blockers})

    out = ["# Manual apply queue",
           "",
           "Everything below passed the same filters as the automated path but needs a human",
           "browser (captcha-gated form, custom questions, or an answer only you can give).",
           "Work top to bottom; after submitting one, log it:",
           "",
           '    python3 scripts/outcomes.py log "<Company>" --outcome acknowledged  # or record in tracker',
           ""]
    for e in entries:
        c = e["c"]
        out += [f"## {c['company']} — {c['role']}",
                f"- URL: {e['url']}",
                f"- Location: {c.get('city') or '?'} | ATS: {c['ats']}"]
        if e["answers"]:
            out += ["- Pre-computed answers (profile-backed):"]
            for a in e["answers"]:
                q = re.sub(r"<[^>]+>", " ", str(a.get("question") or "")).strip()[:90]
                v = ("Yes" if a["flag"] else "No") if "flag" in a else a["content"]
                out += [f"    - {q} -> **{v}**"]
        if e["blockers"]:
            out += ["- NEEDS YOUR OWN ANSWER:"]
            for b in e["blockers"]:
                out += [f"    - [{'required' if b['required'] else 'optional'}] {b['question'][:110]}"]
        out += ["- Cover letter (tailored on "
                f"{', '.join(e['matched']) if e['matched'] else 'nothing — general letter'}):",
                "", "```", e["letter"], "```", ""]

    qpath = BASE / "data" / "apply-queue.md"
    qpath.write_text("\n".join(out))
    print(f"{len(entries)} entries -> {qpath}")
    for k, v in sorted(dropped.items(), key=lambda x: -x[1]):
        print(f"   excluded {v:3d}  {k}")


if __name__ == "__main__":
    main(sys.argv[1:])
