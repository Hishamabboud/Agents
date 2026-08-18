#!/usr/bin/env python3
"""Batch submit v5 — new companies found 2026-06-30."""

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
    # RIPE NCC — Software Engineer Intermediate, Amsterdam (TS/React)
    {"company": "RIPE NCC", "slug_company": "ripencc",
     "offer_slug": "software-engineer-intermediate", "offer_id": 2421813,
     "role": "Software Engineer - Intermediate", "location": "Amsterdam"},

    # Eurail — Platform Engineer, Utrecht
    {"company": "Eurail", "slug_company": "eurail",
     "offer_slug": "platform-engineer", "offer_id": 2553134,
     "role": "Platform Engineer", "location": "Utrecht"},

    # Clockworks — Full-Stack Software Engineer, Rotterdam
    {"company": "Clockworks", "slug_company": "clockworks",
     "offer_slug": "full-stack-software-engineer-1", "offer_id": 2365979,
     "role": "Full-Stack Software Engineer", "location": "Rotterdam"},

    # Clockworks — Experienced Back-end & Platform Engineer, Rotterdam
    {"company": "Clockworks", "slug_company": "clockworks",
     "offer_slug": "experienced-back-end-platform-engineer", "offer_id": 2365964,
     "role": "Experienced Back-end & Platform Engineer", "location": "Rotterdam"},

    # BPM Company — AI Solutions Engineer, Utrecht
    {"company": "BPM Company", "slug_company": "bpmcompany",
     "offer_slug": "ai-solutions-engineer", "offer_id": 2409441,
     "role": "AI Solutions Engineer", "location": "Utrecht"},

    # Polaroid — ERP Developer, Amsterdam
    {"company": "Polaroid", "slug_company": "polaroid",
     "offer_slug": "erp-developer", "offer_id": 2577390,
     "role": "ERP Developer", "location": "Amsterdam"},
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
    already_applied = set()
    for a in apps:
        already_applied.add(f"{a.get('company','').lower()}|{a.get('role','').lower()}")
        if a.get("offer_id"):
            already_applied.add(str(a["offer_id"]))
    company_counts = {}
    for a in apps:
        if a.get("status") in ("applied", "action_required"):
            c_name = a.get("company", "").lower()
            company_counts[c_name] = company_counts.get(c_name, 0) + 1
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=282) + 1
    applied = failed = skipped = 0

    for i, c in enumerate(CANDIDATES):
        company, slug, role = c["company"], c["slug_company"], c["role"]
        offer_id, location = c["offer_id"], c["location"]
        if slug in BLOCKED_SLUGS or company.lower() in blocked:
            print(f"  [~] {company} - {role} | BLOCKED — skipping"); skipped += 1; continue
        if str(offer_id) in already_applied:
            print(f"  [~] {company} - {role} | already applied — skipping"); skipped += 1; continue
        key = f"{company.lower()}|{role.lower()}"
        if key in already_applied:
            print(f"  [~] {company} - {role} | already applied — skipping"); skipped += 1; continue
        if company_counts.get(company.lower(), 0) >= 2:
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
        already_applied.add(str(offer_id)); already_applied.add(key)
        company_counts[company.lower()] = company_counts.get(company.lower(), 0) + 1
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
