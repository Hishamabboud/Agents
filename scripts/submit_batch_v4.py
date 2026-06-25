#!/usr/bin/env python3
"""Batch submit v4 — junior/medior focused roles found 2026-06-25."""

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
    # Creative Clicks — FullStack Engineer, Amsterdam (no seniority prefix)
    {"company": "Creative Clicks", "slug_company": "creativeclicks",
     "offer_slug": "fullstack-engineer", "offer_id": 2570950,
     "role": "FullStack Engineer", "location": "Amsterdam"},

    # LOAVIES — Back-end Developer, Zwolle (no seniority prefix)
    {"company": "LOAVIES", "slug_company": "loavies",
     "offer_slug": "backend-developer-loavies", "offer_id": 2367442,
     "role": "Back-end Developer", "location": "Zwolle"},

    # W3S Digital — .NET/Azure Developer, Rotterdam (medior/senior)
    {"company": "W3S Digital", "slug_company": "w3sdigital",
     "offer_slug": "net-developer-medior-senior", "offer_id": 609129,
     "role": ".NET/Azure Developer", "location": "Rotterdam"},

    # BAS Group — AI Engineer, Veghel (no seniority prefix)
    {"company": "BAS Group", "slug_company": "basgroup",
     "offer_slug": "ai-engineer-1", "offer_id": 2637371,
     "role": "AI Engineer", "location": "Veghel, Noord-Brabant"},

    # BAS Group — Medior PHP Developer, Veghel
    {"company": "BAS Group", "slug_company": "basgroup",
     "offer_slug": "medior-php-developer-6", "offer_id": 2621357,
     "role": "Medior PHP Developer", "location": "Veghel, Noord-Brabant"},

    # Formelio — Senior Backend Engineer, Den Haag (Rust & Java but worth a shot)
    {"company": "Formelio", "slug_company": "formelio",
     "offer_slug": "senior-backend-engineer", "offer_id": 2240877,
     "role": "Backend Engineer", "location": "Den Haag"},

    # iWell — Hands-on Software Architect, Utrecht
    {"company": "iWell", "slug_company": "iwell",
     "offer_slug": "hands-on-software-architect", "offer_id": 2588482,
     "role": "Hands-on Software Architect", "location": "Utrecht"},

    # Linkit — AI Engineer, De Meern/Utrecht (no seniority prefix)
    {"company": "Linkit", "slug_company": "linkit",
     "offer_slug": "ai-engineer", "offer_id": 2532431,
     "role": "AI Engineer", "location": "De Meern, Utrecht"},

    # Linkit — Data Engineer, De Meern/Utrecht (no seniority prefix)
    {"company": "Linkit", "slug_company": "linkit",
     "offer_slug": "dataengineer", "offer_id": 2421268,
     "role": "Data Engineer", "location": "De Meern, Utrecht"},

    # Ockto — Medior Backend Engineer (.NET), Naarden
    {"company": "Ockto", "slug_company": "ockto",
     "offer_slug": "net-engineer-2", "offer_id": 2175147,
     "role": "Medior Backend Engineer", "location": "Naarden"},

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

    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=272) + 1

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
