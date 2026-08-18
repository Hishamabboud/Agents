#!/usr/bin/env python3
"""Batch submit v12 — 6 new companies found 2026-07-05 via a fourth LinkedIn
job-listing sweep (10 fresh keywords x 4 pages). Live-verified via Recruitee
API before submission."""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"

BLOCKED_SLUGS = {
    "fridayrecruitment", "bimcollab", "sendent", "funda", "sendcloud",
    "chipsoft", "ubiops", "prodrive", "futuresworks", "yellowtail",
}

CANDIDATES = [
    {"company": 'Dura Vermeer', "slug_company": 'duravermeer',
     "offer_slug": 'applicatiespecialist-systems-engineering', "offer_id": 2384046,
     "role": 'Applicatiespecialist Systems Engineering', "location": 'Utrecht'},
    {"company": 'Klaverblad Verzekeringen', "slug_company": 'klaverbladverzekeringen',
     "offer_slug": 'lead-integration-engineer', "offer_id": 2120294,
     "role": 'Lead Integration Engineer', "location": 'Zoetermeer'},
    {"company": 'Eneve', "slug_company": 'eneve',
     "offer_slug": 'php-developer-laravel', "offer_id": 2669575,
     "role": 'PHP Developer (Laravel)', "location": 'Utrecht'},
    {"company": 'Skrepr', "slug_company": 'skrepr',
     "offer_slug": 'thinkwise-platform-engineer', "offer_id": 2038267,
     "role": 'Thinkwise Platform Engineer', "location": 'Urk'},
    {"company": 'Skrepr', "slug_company": 'skrepr',
     "offer_slug": 'devops-engineer', "offer_id": 1572284,
     "role": 'DevOps Engineer', "location": 'Urk'},
    {"company": 'Toelevering Online', "slug_company": 'toeleveringonline',
     "offer_slug": 'back-end-php-developer', "offer_id": 2137307,
     "role": 'Back-end PHP Developer', "location": 'Nijverdal'},
    {"company": 'MICE Operations', "slug_company": 'miceoperations',
     "offer_slug": 'back-end-developer-php', "offer_id": 1926079,
     "role": 'Back-end Developer (PHP)', "location": 'Breda'},
    {"company": 'CleverIT', "slug_company": 'cleverit',
     "offer_slug": 'symfony-php-ontwikkelaar-software-developer', "offer_id": 1322351,
     "role": 'PHP Ontwikkelaar / Software Developer (Symfony/Vue) bij CleverMobi', "location": 'Eindhoven'},
]


def load_blocked_companies():
    prefs = BASE_DIR / "profile" / "preferences.md"
    blocked = set()
    if prefs.exists():
        in_blocked = False
        for line in prefs.read_text().splitlines():
            if "Blocked Companies" in line:
                in_blocked = True
                continue
            if line.startswith("## ") and in_blocked:
                break
            if in_blocked and line.startswith("- "):
                blocked.add(line.split("—")[0].split("(")[0].strip("- ").strip().lower())
    return blocked


def applied_slug_set(apps):
    import re
    s = set()
    for a in apps:
        for url in [a.get("url", ""), a.get("recruitee_api_url", "")]:
            m = re.search(r"https?://([^.]+)\.recruitee\.com", str(url))
            if m:
                s.add(m.group(1).lower())
    return s


def slug_counts(apps):
    import re
    counts = {}
    for a in apps:
        if a.get("status") not in ("applied", "action_required"):
            continue
        for url in [a.get("url", ""), a.get("recruitee_api_url", "")]:
            m = re.search(r"https?://([^.]+)\.recruitee\.com", str(url))
            if m:
                sl = m.group(1).lower()
                counts[sl] = counts.get(sl, 0) + 1
                break
    return counts


def build_cover_letter(company, role, location):
    return (
        f"Dear Hiring Team at {company},\n\n"
        f"I am writing to express my interest in the {role} position in {location}. "
        f"As a Software Service Engineer at Actemium (VINCI Energies) with experience in "
        f".NET, C#, Python, and full-stack development, I am excited about the opportunity "
        f"to contribute to your team.\n\n"
        f"My background includes:\n"
        f"- Full-stack development using .NET/C#, Python/Flask, JavaScript/React\n"
        f"- Experience at ASML developing Python test suites with Locust and Pytest\n"
        f"- Building and maintaining Manufacturing Execution Systems (MES)\n"
        f"- Azure, Docker, Kubernetes, and CI/CD pipeline experience\n"
        f"- BSc in Software Engineering from Fontys University\n\n"
        f"I am based in Eindhoven and open to working anywhere in the Netherlands. "
        f"I would welcome the opportunity to discuss how my skills and experience can "
        f"benefit {company}.\n\n"
        f"Best regards,\nHisham Abboud\n+31 06 4841 2838\nhiaham123@hotmail.com"
    )


def submit_candidate(c):
    api_url = f"https://{c['slug_company']}.recruitee.com/api/offers/{c['offer_slug']}/candidates"
    cover_letter = build_cover_letter(c["company"], c["role"], c["location"])
    tmp_file = Path("/tmp/recruitee_resp.txt")
    cmd = [
        "curl", "-s", "-o", str(tmp_file), "-w", "%{http_code}",
        "-X", "POST", api_url,
        "-F", "candidate[name]=Hisham Abboud",
        "-F", "candidate[email]=hiaham123@hotmail.com",
        "-F", "candidate[phone]=+31648412838",
        "-F", f"candidate[cover_letter]={cover_letter}",
        "-F", f"candidate[cv]=@{str(RESUME_PATH)};type=application/pdf",
        "--max-time", "30",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    http_status = result.stdout.strip()
    response_text = tmp_file.read_text() if tmp_file.exists() else ""
    candidate_id = ""
    try:
        resp = json.loads(response_text)
        candidate_id = str(resp.get("candidate", {}).get("id", "") or resp.get("id", ""))
    except Exception:
        pass
    ok = http_status == "201" or bool(candidate_id)
    return ok, http_status, response_text, candidate_id, api_url


def main():
    with open(APPS_PATH) as f:
        apps = json.load(f)
    blocked = load_blocked_companies()
    applied_slugs = applied_slug_set(apps)
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
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=387) + 1
    applied = failed = skipped = 0

    for i, c in enumerate(CANDIDATES):
        company, slug, role = c["company"], c["slug_company"], c["role"]
        offer_id, location = c["offer_id"], c["location"]
        cl = company.lower().strip()

        if slug in BLOCKED_SLUGS or cl in blocked:
            print(f"  [~] {company} - {role} | BLOCKED — skipping"); skipped += 1; continue
        if str(offer_id) in already:
            print(f"  [~] {company} - {role} | already applied (offer_id) — skipping"); skipped += 1; continue
        key = f"{cl}|{role.lower().strip()}"
        if key in already:
            print(f"  [~] {company} - {role} | already applied (company+role) — skipping"); skipped += 1; continue
        if sl_counts.get(slug, 0) >= 2:
            print(f"  [~] {company} - {role} | slug '{slug}' already has 2+ apps — skipping"); skipped += 1; continue
        if company_counts.get(cl, 0) >= 2:
            print(f"  [~] {company} - {role} | max 2 per company — skipping"); skipped += 1; continue

        ok, http_status, response_text, candidate_id, api_url = submit_candidate(c)
        status = "applied" if ok else "failed"
        symbol = "+" if ok else "x"
        notes = f"Applied via Recruitee API (multipart). HTTP {http_status}. Response: {response_text[:200]}"
        if candidate_id:
            notes = f"Applied via Recruitee API. Candidate ID {candidate_id}. HTTP {http_status}."
        rec = {
            "id": next_id, "company": company, "role": role,
            "url": f"https://{slug}.recruitee.com/o/{c['offer_slug']}",
            "date_applied": datetime.now().isoformat(), "score": 7, "status": status,
            "resume_file": str(RESUME_PATH.resolve()), "cover_letter_file": None,
            "screenshot": None, "notes": notes, "email_used": "hiaham123@hotmail.com",
            "offer_id": offer_id, "offer_slug": c["offer_slug"],
            "recruitee_api_url": api_url, "location": location, "response": None,
        }
        if candidate_id:
            rec["candidate_id"] = candidate_id
        apps.append(rec)
        already.add(str(offer_id)); already.add(key)
        sl_counts[slug] = sl_counts.get(slug, 0) + 1
        company_counts[cl] = company_counts.get(cl, 0) + 1
        next_id += 1
        if ok: applied += 1
        else: failed += 1
        print(f"  [{symbol}] {next_id-1:3d} {company} - {role} | {status} | HTTP {http_status} | candidate_id={candidate_id}")
        if not ok:
            print(f"       Response: {response_text[:150]}")
        if i < len(CANDIDATES) - 1:
            time.sleep(2)

    with open(APPS_PATH, "w") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)
    print(f"\nDone: {applied} applied, {failed} failed, {skipped} skipped, total tracker: {len(apps)}")


if __name__ == "__main__":
    main()
