#!/usr/bin/env python3
"""Batch submit v19 — round 23. First full-time sweep run across BOTH the
Netherlands and Belgium after geography was broadened on 2026-07-29.

10 untried keywords x 4 pages x 2 countries (MES engineer, SCADA engineer,
PLC programmer, Application engineer, Software architect, Embedded engineer,
API developer, Microservices engineer, TypeScript developer, SQL developer),
leaning into the MES/industrial-automation background. Live-verified via the
Recruitee API before submission.

Cover letter is country-aware: Belgian applications lead with proximity to the
border and Dutch/English fluency rather than "anywhere in the Netherlands".
"""

import json
import re
import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"
CANDIDATES_PATH = Path("/tmp/claude-0/-home-user-Agents/9fd85063-ee93-588d-a736-933ead644540/scratchpad/final_r23.json")

BLOCKED_SLUGS = {
    "fridayrecruitment", "bimcollab", "sendent", "funda", "sendcloud",
    "chipsoft", "ubiops", "prodrive", "futuresworks", "yellowtail",
}


def load_blocked_companies():
    prefs = BASE_DIR / "profile" / "preferences.md"
    blocked, inb = set(), False
    for line in prefs.read_text().splitlines():
        if "Blocked Companies" in line:
            inb = True
            continue
        if line.startswith("## ") and inb:
            break
        if inb and line.startswith("- "):
            blocked.add(line.split("—")[0].split("(")[0].strip("- ").strip().lower())
    return blocked


def slug_counts(apps):
    counts = {}
    for a in apps:
        if a.get("status") not in ("applied", "action_required"):
            continue
        for url in (a.get("url", ""), a.get("recruitee_api_url", "")):
            m = re.search(r"https?://([^.]+)\.recruitee\.com", str(url))
            if m:
                counts[m.group(1).lower()] = counts.get(m.group(1).lower(), 0) + 1
                break
    return counts


def build_cover_letter(company, role, location, country):
    if country == "BE":
        closing = (
            f"I am based in Eindhoven in the Netherlands, close to the Belgian border, and am "
            f"open to working in Belgium. I am fluent in Dutch and English. I would welcome the "
            f"opportunity to discuss how my skills and experience can benefit {company}.\n\n"
        )
    else:
        closing = (
            f"I am based in Eindhoven and open to working anywhere in the Netherlands. "
            f"I would welcome the opportunity to discuss how my skills and experience can "
            f"benefit {company}.\n\n"
        )
    return (
        f"Dear Hiring Team at {company},\n\n"
        f"I am writing to express my interest in the {role} position in {location}. "
        f"As a Software Service Engineer at Actemium (VINCI Energies) with experience in "
        f".NET, C#, Python, and full-stack development, I am excited about the opportunity "
        f"to contribute to your team.\n\n"
        f"My background includes:\n"
        f"- Full-stack development using .NET/C#, Python/Flask, JavaScript/React\n"
        f"- Building and maintaining Manufacturing Execution Systems (MES) for industrial clients\n"
        f"- Experience at ASML developing Python test suites with Locust and Pytest\n"
        f"- Azure, Docker, Kubernetes, and CI/CD pipeline experience\n"
        f"- BSc in Software Engineering from Fontys University\n\n"
        + closing +
        f"Best regards,\nHisham Abboud\n+31 06 4841 2838\nhiaham123@hotmail.com"
    )


def submit_candidate(c):
    api_url = f"https://{c['slug_company']}.recruitee.com/api/offers/{c['offer_slug']}/candidates"
    cover = build_cover_letter(c["company"], c["role"], c["location"], c.get("country", "NL"))
    tmp = Path("/tmp/recruitee_resp.txt")
    cmd = [
        "curl", "-s", "-o", str(tmp), "-w", "%{http_code}", "-X", "POST", api_url,
        "-F", "candidate[name]=Hisham Abboud",
        "-F", "candidate[email]=hiaham123@hotmail.com",
        "-F", "candidate[phone]=+31648412838",
        "-F", f"candidate[cover_letter]={cover}",
        "-F", f"candidate[cv]=@{RESUME_PATH};type=application/pdf",
        "--max-time", "30",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    http_status = r.stdout.strip()
    body = tmp.read_text() if tmp.exists() else ""
    cid = ""
    try:
        j = json.loads(body)
        cid = str(j.get("candidate", {}).get("id", "") or j.get("id", ""))
    except Exception:
        pass
    return (http_status == "201" or bool(cid)), http_status, body, cid, api_url


def main():
    from tracker_guard import assert_tracker_fresh
    assert_tracker_fresh()          # abort if local tracker is stale (see v19 incident)
    apps = json.load(open(APPS_PATH))
    candidates = json.load(open(CANDIDATES_PATH))
    blocked = load_blocked_companies()
    sl_counts = slug_counts(apps)

    already = set()
    for a in apps:
        already.add(f"{a.get('company','').lower().strip()}|{a.get('role','').lower().strip()}")
        if a.get("offer_id"):
            already.add(str(a["offer_id"]))
    company_counts = {}
    for a in apps:
        if a.get("status") in ("applied", "action_required"):
            cn = a.get("company", "").lower().strip()
            company_counts[cn] = company_counts.get(cn, 0) + 1

    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=442) + 1
    applied = failed = skipped = 0

    for i, c in enumerate(candidates):
        company, slug, role = c["company"], c["slug_company"], c["role"]
        offer_id, location = c["offer_id"], c["location"]
        cl = company.lower().strip()

        if slug in BLOCKED_SLUGS or cl in blocked:
            print(f"  [~] {company} - {role} | BLOCKED"); skipped += 1; continue
        if str(offer_id) in already:
            print(f"  [~] {company} - {role} | dup offer_id"); skipped += 1; continue
        if f"{cl}|{role.lower().strip()}" in already:
            print(f"  [~] {company} - {role} | dup company+role"); skipped += 1; continue
        if sl_counts.get(slug, 0) >= 2:
            print(f"  [~] {company} - {role} | slug '{slug}' at cap"); skipped += 1; continue
        if company_counts.get(cl, 0) >= 2:
            print(f"  [~] {company} - {role} | company at cap"); skipped += 1; continue

        ok, http_status, body, cid, api_url = submit_candidate(c)
        status = "applied" if ok else "failed"
        notes = (f"Applied via Recruitee API. Candidate ID {cid}. HTTP {http_status}." if cid
                 else f"Applied via Recruitee API (multipart). HTTP {http_status}. Response: {body[:200]}")
        rec = {
            "id": next_id, "company": company, "role": role,
            "url": f"https://{slug}.recruitee.com/o/{c['offer_slug']}",
            "date_applied": datetime.now().isoformat(), "score": 7, "status": status,
            "resume_file": str(RESUME_PATH.resolve()), "cover_letter_file": None,
            "screenshot": None, "notes": notes, "email_used": "hiaham123@hotmail.com",
            "offer_id": offer_id, "offer_slug": c["offer_slug"],
            "recruitee_api_url": api_url, "location": location,
            "country": c.get("country", "NL"), "response": None,
        }
        if cid:
            rec["candidate_id"] = cid
        apps.append(rec)
        already.add(str(offer_id)); already.add(f"{cl}|{role.lower().strip()}")
        sl_counts[slug] = sl_counts.get(slug, 0) + 1
        company_counts[cl] = company_counts.get(cl, 0) + 1
        next_id += 1
        applied += ok; failed += (not ok)
        print(f"  [{'+' if ok else 'x'}] {next_id-1:3d} {company} - {role[:44]} | {status} | "
              f"HTTP {http_status} | {c.get('country','NL')} | cid={cid}")
        if not ok:
            print(f"       {body[:150]}")
        if i < len(candidates) - 1:
            time.sleep(2)

    json.dump(apps, open(APPS_PATH, "w"), indent=2, ensure_ascii=False)
    print(f"\nDone: {applied} applied, {failed} failed, {skipped} skipped, total tracker: {len(apps)}")


if __name__ == "__main__":
    main()
