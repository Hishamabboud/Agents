#!/usr/bin/env python3
"""Unified batch applier — replaces submit_batch_v7..v22 (22 near-identical copies).

Each of those scripts was a copy-paste of the last, which is how the same bug shipped
repeatedly and why fixes had to be applied by hand in several places. Everything now
imports from one place:

    tracker_guard.py  freshness check (stale tracker -> blind dedup -> duplicate spam)
    filters.py        blocklist, country scope, language, hard blockers, Personio parsing
    discovery.py      multi-variant slug resolution + collision guard
    cover_letter.py   per-job tailored letter, restricted to CV-backed claims

Usage:
    python3 scripts/apply_batch.py candidates.json [--dry-run]

candidates.json is a list of dicts:
    Recruitee: {"ats":"recruitee","company","slug","offer_slug","role","city","country","offer_id"}
    Personio : {"ats":"personio","company","host","job_id","role","city"}
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracker_guard import assert_tracker_fresh
from filters import load_blocked_companies, blocked_reason, hard_blockers
import cover_letter
import personio_apply

BASE = Path(__file__).resolve().parent.parent
RESUME = BASE / "profile" / "Hisham Abboud CV.pdf"
APPS = BASE / "data" / "applications.json"
PREFS = BASE / "profile" / "preferences.md"
COUNTED = ("applied", "action_required", "duplicate_submitted",
           "overcap_submitted", "requires_manual_step")
MAX_PER_COMPANY = 2


def resolve_redirect(slug, offer_slug):
    """Recruitee tenants rename (adesso -> werkenbijadesso). POSTs don't follow redirects."""
    try:
        head = subprocess.run(
            ["curl", "-sI", "--max-time", "15",
             f"https://{slug}.recruitee.com/api/offers/{offer_slug}"],
            capture_output=True, text=True).stdout
        m = re.search(r"^location:\s*https://([^.]+)\.recruitee\.com", head, re.I | re.M)
        if m:
            print(f"       (tenant redirect {slug} -> {m.group(1)})")
            return m.group(1)
    except Exception:
        pass
    return slug


def fetch_job_text(c):
    """Pull the live posting text (for tailoring AND for the hard-blocker re-check).

    Returns (text, still_open). Listings close between discovery and submission, and a
    title alone never reveals a 10-year requirement, a clearance, a defence programme, or
    a French-language description — those live in the body and must be checked here, on
    the live text, not on the cached search result.
    """
    try:
        if c["ats"] == "recruitee":
            url = f"https://{c['slug']}.recruitee.com/api/offers/{c['offer_slug']}"
            o = json.loads(subprocess.run(["curl", "-sL", "--max-time", "18", url],
                                          capture_output=True, text=True).stdout)
            o = o.get("offer", o)
            text = (o.get("description") or "") + " " + (o.get("requirements") or "")
            return text, (o.get("status") == "published")
        xml = subprocess.run(["curl", "-s", "--max-time", "20", f"https://{c['host']}/xml"],
                             capture_output=True, text=True).stdout
        m = re.search(rf"<position>(?:(?!</position>).)*?<id>{c['job_id']}</id>.*?</position>",
                      xml, re.S)
        # a position missing from the live feed has been taken down
        return (m.group(0), True) if m else ("", False)
    except Exception:
        return "", False


def submit_recruitee(c, letter):
    slug = resolve_redirect(c["slug"], c["offer_slug"])
    api = f"https://{slug}.recruitee.com/api/offers/{c['offer_slug']}/candidates"
    r = subprocess.run(
        ["curl", "-s", "-o", "/tmp/rr.txt", "-w", "%{http_code}", "-X", "POST", api,
         "-F", "candidate[name]=Hisham Abboud",
         "-F", "candidate[email]=hiaham123@hotmail.com",
         "-F", "candidate[phone]=+31648412838",
         "-F", f"candidate[cover_letter]={letter}",
         "-F", f"candidate[cv]=@{RESUME};type=application/pdf", "--max-time", "30"],
        capture_output=True, text=True)
    st = r.stdout.strip()
    body = Path("/tmp/rr.txt").read_text() if Path("/tmp/rr.txt").exists() else ""
    cid = ""
    try:
        cid = str(json.loads(body).get("candidate", {}).get("id", ""))
    except Exception:
        pass
    return (st == "201" or bool(cid)), st, cid, api, slug


def submit_personio(c, letter):
    salary, avail = personio_apply.read_commitments()
    comp = personio_apply.get_company_id(c["host"], c["job_id"])
    doc = personio_apply.upload_cv(c["host"], c["job_id"])
    st, _ = personio_apply.submit(
        c["host"], c["job_id"], comp, doc, salary, avail,
        first="Hisham", last="Abboud", email="hiaham123@hotmail.com",
        phone="+31648412838", location="Eindhoven, Netherlands")
    return st.startswith("2"), st, "", f"https://{c['host']}/job/{c['job_id']}", c["host"]


def main(path, dry_run=False):
    assert_tracker_fresh()
    apps = json.load(open(APPS))
    cands = json.load(open(path))
    blocked = load_blocked_companies(PREFS)

    seen_offer = {str(a["offer_id"]) for a in apps if a.get("offer_id")}
    seen_per = {(str(a.get("personio_host")), str(a.get("personio_job_id")))
                for a in apps if a.get("personio_job_id")}
    seen_cr = {f"{(a.get('company') or '').lower().strip()}|{(a.get('role') or '').lower().strip()}"
               for a in apps}
    ccount = {}
    for a in apps:
        if a.get("status") in COUNTED:
            k = (a.get("company") or "").lower().strip()
            ccount[k] = ccount.get(k, 0) + 1

    nid = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=0) + 1
    applied = failed = skipped = 0

    for c in cands:
        co = c["company"]; cl = co.lower().strip()
        role = c.get("role", "")

        why = blocked_reason(co, c.get("slug"), blocked)
        if why: print(f"  [~] {co} | {why}"); skipped += 1; continue
        if ccount.get(cl, 0) >= MAX_PER_COMPANY:
            print(f"  [~] {co} | at {MAX_PER_COMPANY}-application cap"); skipped += 1; continue
        if f"{cl}|{role.lower().strip()}" in seen_cr:
            print(f"  [~] {co} - {role[:32]} | duplicate company+role"); skipped += 1; continue
        if c["ats"] == "recruitee" and str(c.get("offer_id")) in seen_offer:
            print(f"  [~] {co} - {role[:32]} | duplicate offer id"); skipped += 1; continue
        if c["ats"] == "personio" and (c.get("host"), str(c.get("job_id"))) in seen_per:
            print(f"  [~] {co} - {role[:32]} | duplicate personio job"); skipped += 1; continue

        job_text, still_open = fetch_job_text(c)
        if not still_open:
            print(f"  [~] {co} - {role[:32]} | no longer open"); skipped += 1; continue
        flags = hard_blockers(role, job_text)
        if flags:
            print(f"  [~] {co} - {role[:32]} | live check: {', '.join(flags)}")
            skipped += 1; continue
        letter, matched = cover_letter.build(co, role, c.get("city") or "",
                                             c.get("country", "NL"), job_text)
        if dry_run:
            print(f"  [dry] {co[:22]:22s} | {role[:34]:34s} | tailored_on={matched}")
            continue

        try:
            ok, st, cid, api, tenant = (submit_recruitee(c, letter) if c["ats"] == "recruitee"
                                        else submit_personio(c, letter))
        except Exception as e:
            print(f"  [x] {co} - {role[:30]} | ERROR {e}"); failed += 1; continue

        rec = {"id": nid, "company": co, "role": role, "url": api,
               "date_applied": datetime.now().isoformat(), "score": 7,
               "status": "applied" if ok else "failed", "ats": c["ats"],
               "resume_file": str(RESUME.resolve()), "cover_letter_file": None,
               "screenshot": None,
               "notes": f"Applied via {c['ats']} API. HTTP {st}."
                        + (f" Candidate ID {cid}." if cid else ""),
               "email_used": "hiaham123@hotmail.com",
               "location": c.get("city"), "country": c.get("country"),
               "letter_tailored": bool(matched), "letter_matched_on": matched,
               "outcome": None, "response": None}
        if c["ats"] == "recruitee":
            rec.update({"offer_id": c.get("offer_id"), "offer_slug": c["offer_slug"],
                        "recruitee_api_url": api})
        else:
            rec.update({"personio_host": c["host"], "personio_job_id": c["job_id"]})
        apps.append(rec)

        seen_cr.add(f"{cl}|{role.lower().strip()}")
        ccount[cl] = ccount.get(cl, 0) + 1
        if c["ats"] == "recruitee": seen_offer.add(str(c.get("offer_id")))
        else: seen_per.add((c.get("host"), str(c.get("job_id"))))

        # Persist after EVERY submission. A round-30 run was killed by a 2-minute command
        # timeout after ~24 real submissions and, because the tracker was only written at
        # the end, none of them were recorded — exactly the blind-dedup state that caused
        # the round-23 duplicate spam. An unrecorded application is worse than a slow loop.
        json.dump(apps, open(APPS, "w"), indent=2, ensure_ascii=False)

        applied += ok; failed += (not ok)
        print(f"  [{'+' if ok else 'x'}] {nid} {co[:20]:20s} | {role[:34]:34s} | "
              f"HTTP {st} | tailored_on={matched}")
        nid += 1
        time.sleep(2)

    if not dry_run:
        json.dump(apps, open(APPS, "w"), indent=2, ensure_ascii=False)
        print(f"\n{applied} applied, {failed} failed, {skipped} skipped | tracker: {len(apps)}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("candidates")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    main(a.candidates, a.dry_run)
