#!/usr/bin/env python3
"""Batch submit job applications via Recruitee API — v3 with new companies found 2026-06-25."""

import json
import time
import subprocess
import re
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
    # CowManager — .NET roles in Harmelen, Utrecht (max 2)
    {"company": "CowManager", "slug_company": "cowmanager",
     "offer_slug": "net-backend-developer", "offer_id": 2342926,
     "role": ".NET Backend Developer", "location": "Harmelen, Utrecht"},
    {"company": "CowManager", "slug_company": "cowmanager",
     "offer_slug": "net-fullstack-developer", "offer_id": 2342842,
     "role": ".NET Fullstack Developer", "location": "Harmelen, Utrecht"},

    # Momo Medical — Backend/fullstack in Delft (max 2)
    {"company": "Momo Medical", "slug_company": "momomedicalbv",
     "offer_slug": "senior-backend-developer-devops-3", "offer_id": 2496832,
     "role": "Senior Backend Developer | DevOps", "location": "Delft"},
    {"company": "Momo Medical", "slug_company": "momomedicalbv",
     "offer_slug": "mediorsenior-full-stack-developer", "offer_id": 2310665,
     "role": "Medior/Senior Full Stack Developer", "location": "Delft"},

    # Learned — Full stack in Utrecht (max 2)
    {"company": "Learned", "slug_company": "learned",
     "offer_slug": "medior-full-stack-developer", "offer_id": 2549586,
     "role": "Medior Full Stack Developer", "location": "Utrecht"},
    {"company": "Learned", "slug_company": "learned",
     "offer_slug": "senior-full-stack-developer", "offer_id": 1715577,
     "role": "Senior Full Stack Developer", "location": "Utrecht"},

    # FutureWhiz — Python backend in Amsterdam (1 role, medior fits better)
    {"company": "FutureWhiz", "slug_company": "futurewhiz",
     "offer_slug": "medior-python-backend-developer", "offer_id": 2635283,
     "role": "Medior Python Backend Developer", "location": "Amsterdam"},

    # Fastned — Senior backend in Amsterdam (1 role)
    {"company": "Fastned", "slug_company": "fastned",
     "offer_slug": "senior-backend-engineer-4", "offer_id": 2648027,
     "role": "Senior Backend Engineer", "location": "Amsterdam"},

    # Axual — Backend/fullstack in Utrecht (1 role)
    {"company": "Axual", "slug_company": "axual",
     "offer_slug": "backend-fullstack-software-engineer", "offer_id": 2120983,
     "role": "Backend (Full-stack) Software Engineer", "location": "Utrecht"},

    # Eraneos — AI/Data engineering in Amsterdam (1 role)
    {"company": "Eraneos", "slug_company": "eraneos",
     "offer_slug": "senior-ai-engineer-mvx", "offer_id": 2541175,
     "role": "Senior AI Engineer", "location": "Amsterdam"},

    # Fixico — Backend in Amsterdam (1 role)
    {"company": "Fixico", "slug_company": "fixico",
     "offer_slug": "senior-backend-engineer", "offer_id": 2617053,
     "role": "Senior Backend Engineer", "location": "Amsterdam"},

    # VolkerWessels Digital — Senior Software Engineer in Vianen (1 role)
    {"company": "VolkerWessels Digital", "slug_company": "vwml",
     "offer_slug": "senior-software-engineer", "offer_id": 2411180,
     "role": "Senior Software Engineer", "location": "Vianen, Utrecht"},

    # GreenFlux — .NET backend in Amsterdam (1 role)
    {"company": "GreenFlux", "slug_company": "greenflux",
     "offer_slug": "senior-net-back-end-software-engineer-2-3", "offer_id": 1883938,
     "role": "(Senior) Software Engineer", "location": "Amsterdam"},
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
    slug_company = c["slug_company"]
    offer_slug = c["offer_slug"]
    role = c["role"]
    location = c["location"]
    company = c["company"]

    api_url = f"https://{slug_company}.recruitee.com/api/offers/{offer_slug}/candidates"
    cover_letter = build_cover_letter(company, role, location)

    tmp_file = Path("/tmp/recruitee_resp.txt")
    cmd = [
        "curl", "-s",
        "-o", str(tmp_file),
        "-w", "%{http_code}",
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

    already_applied = set()
    for a in apps:
        key = f"{a.get('company','').lower()}|{a.get('role','').lower()}"
        already_applied.add(key)
        if a.get("offer_id"):
            already_applied.add(str(a["offer_id"]))

    company_counts = {}
    for a in apps:
        c_name = a.get("company", "").lower()
        if a.get("status") in ("applied", "action_required"):
            company_counts[c_name] = company_counts.get(c_name, 0) + 1

    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=259) + 1

    applied = 0
    failed = 0
    skipped = 0

    for i, c in enumerate(CANDIDATES):
        company = c["company"]
        slug = c["slug_company"]
        role = c["role"]
        offer_id = c["offer_id"]
        location = c["location"]

        if slug in BLOCKED_SLUGS or company.lower() in blocked:
            print(f"  [~] {company} - {role} | BLOCKED — skipping")
            skipped += 1
            continue

        if str(offer_id) in already_applied:
            print(f"  [~] {company} - {role} | already applied (offer_id) — skipping")
            skipped += 1
            continue

        key = f"{company.lower()}|{role.lower()}"
        if key in already_applied:
            print(f"  [~] {company} - {role} | already applied (company+role) — skipping")
            skipped += 1
            continue

        if company_counts.get(company.lower(), 0) >= 2:
            print(f"  [~] {company} - {role} | max 2 per company reached — skipping")
            skipped += 1
            continue

        ok, http_status, response_text, candidate_id, api_url = submit_candidate(c)

        status = "applied" if ok else "failed"
        symbol = "+" if ok else "x"

        notes = f"Applied via Recruitee API (multipart). HTTP {http_status}. Response: {response_text[:200]}"
        if candidate_id:
            notes = f"Applied via Recruitee API. Candidate ID {candidate_id}. HTTP {http_status}."

        app_record = {
            "id": next_id,
            "company": company,
            "role": role,
            "url": f"https://{slug}.recruitee.com/o/{c['offer_slug']}",
            "date_applied": datetime.now().isoformat(),
            "score": 7,
            "status": status,
            "resume_file": str(RESUME_PATH.resolve()),
            "cover_letter_file": None,
            "screenshot": None,
            "notes": notes,
            "email_used": "hiaham123@hotmail.com",
            "offer_id": offer_id,
            "offer_slug": c["offer_slug"],
            "recruitee_api_url": api_url,
            "location": location,
            "response": None,
        }
        if candidate_id:
            app_record["candidate_id"] = candidate_id

        apps.append(app_record)
        already_applied.add(str(offer_id))
        already_applied.add(key)
        company_counts[company.lower()] = company_counts.get(company.lower(), 0) + 1
        next_id += 1

        if ok:
            applied += 1
        else:
            failed += 1

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
