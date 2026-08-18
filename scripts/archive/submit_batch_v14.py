#!/usr/bin/env python3
"""Batch submit v14 — 9 new companies found 2026-07-06 via a fifth LinkedIn
job-listing sweep (10 fresh keywords x 4 pages: Automation, ERP, Product,
Network, Test Automation, Cloud Developer, SaaS, Power Platform, IT Consultant,
Robotics Software Engineer). Live-verified via Recruitee API before submission."""

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
    {"company": 'Quooker', "slug_company": 'quooker',
     "offer_slug": 'plc-software-engineer', "offer_id": 2431363,
     "role": 'PLC software engineer', "location": 'Ridderkerk'},
    {"company": 'Quooker', "slug_company": 'quooker',
     "offer_slug": 'automation-engineer-1', "offer_id": 2247544,
     "role": 'Automation engineer', "location": 'Ridderkerk'},
    {"company": 'Hollander Techniek', "slug_company": 'hollandertechniek',
     "offer_slug": 'software-engineer-industrie', "offer_id": 2669285,
     "role": 'Software engineer industrie', "location": 'Almelo'},
    {"company": 'Hollander Techniek', "slug_company": 'hollandertechniek',
     "offer_slug": 'lead-software-engineer-5', "offer_id": 2617838,
     "role": 'Lead software engineer', "location": 'Almelo'},
    {"company": 'VIRO', "slug_company": 'viro',
     "offer_slug": 'software-engineer-applicaties-industrial-automation', "offer_id": 2564128,
     "role": 'Software Engineer Applicaties & Industrial Automation', "location": 'Hengelo'},
    {"company": 'VIRO', "slug_company": 'viro',
     "offer_slug": 'software-engineer-industriele-automatisering-3', "offer_id": 2130152,
     "role": 'Software Engineer Industriële Automatisering', "location": 'Zwolle'},
    {"company": 'SUPERP', "slug_company": 'superp',
     "offer_slug": 'azure-data-engineer-medior', "offer_id": 2336389,
     "role": 'Azure Data Engineer (Medior)', "location": "'s-Hertogenbosch"},
    {"company": 'SUPERP', "slug_company": 'superp',
     "offer_slug": 'junior-mendix-engineer', "offer_id": 2309236,
     "role": 'Junior Mendix Engineer', "location": 'De Meern'},
    {"company": 'Blue10', "slug_company": 'blue10',
     "offer_slug": 'back-end-engineer', "offer_id": 2410618,
     "role": 'Back-end Engineer', "location": 'Den Haag'},
    {"company": 'Talk360', "slug_company": 'talk360',
     "offer_slug": 'senior-qa-automation-engineer', "offer_id": 2608787,
     "role": 'Senior QA Automation Engineer', "location": 'Amsterdam'},
    {"company": 'Royal Swinkels', "slug_company": 'royalswinkels',
     "offer_slug": 'ot-network-engineer', "offer_id": 2605942,
     "role": 'OT Network Engineer', "location": 'Lieshout'},
    {"company": 'RAM Infotechnology', "slug_company": 'raminfotechnology',
     "offer_slug": 'software-engineer-zorg-it-en-ai-3500-4500-4501', "offer_id": 2662970,
     "role": 'Software Engineer - Zorg, IT en AI - €3500-€4500', "location": 'Utrecht'},
    {"company": 'OGD ict-diensten', "slug_company": 'ogdictdiensten',
     "offer_slug": 'medior-network-devops-engineer', "offer_id": 595065,
     "role": 'Medior Network DevOps Engineer', "location": 'Delft'},
    {"company": 'Source.ag', "slug_company": 'source',
     "offer_slug": 'control-systems-engineer', "offer_id": 2460735,
     "role": 'Control Systems Engineer', "location": 'Amsterdam'},
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
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=401) + 1
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
