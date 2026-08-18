#!/usr/bin/env python3
"""Batch submit job applications via Recruitee API using multipart form data and offer slugs."""

import json
import time
import subprocess
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"
CANDIDATES_PATH = Path("/tmp/new_candidates_v2.json")

CANDIDATES = [
    # adesso Netherlands
    {"company": "adesso Netherlands", "slug_company": "werkenbijadesso",
     "offer_slug": "kotlin-developer", "offer_id": 2595722,
     "role": "Kotlin Developer", "location": "Utrecht"},
    {"company": "adesso Netherlands", "slug_company": "werkenbijadesso",
     "offer_slug": "full-stack-java-developer-2", "offer_id": 2072750,
     "role": "Full Stack Java Developer", "location": "Utrecht"},
    # Friday Recruitment
    {"company": "Friday Recruitment", "slug_company": "fridayrecruitment",
     "offer_slug": "senior-developer", "offer_id": 2243194,
     "role": "Senior Developer", "location": "Harderwijk"},
    {"company": "Friday Recruitment", "slug_company": "fridayrecruitment",
     "offer_slug": "devops-engineer", "offer_id": 2171436,
     "role": "DevOps Engineer", "location": "Amersfoort"},
    {"company": "Friday Recruitment", "slug_company": "fridayrecruitment",
     "offer_slug": "data-engineer-consultant-2", "offer_id": 2102977,
     "role": "Data Engineer Consultant", "location": "Arnhem"},
    {"company": "Friday Recruitment", "slug_company": "fridayrecruitment",
     "offer_slug": "full-stack-java-developer", "offer_id": 1980026,
     "role": "Full-stack Java Developer", "location": "Amersfoort"},
    {"company": "Friday Recruitment", "slug_company": "fridayrecruitment",
     "offer_slug": "aws-azure-cloud-engineer", "offer_id": 1905686,
     "role": "AWS/Azure Cloud Engineer", "location": "Amersfoort"},
    # Yielder Group
    {"company": "Yielder Group", "slug_company": "yieldergroup",
     "offer_slug": "full-stack-developer", "offer_id": 2591791,
     "role": "Full Stack Developer", "location": "Hoofddorp"},
    {"company": "Yielder Group", "slug_company": "yieldergroup",
     "offer_slug": "senior-net-developer", "offer_id": 2409358,
     "role": "Senior .NET Developer", "location": "Hoofddorp"},
    # CM.com
    {"company": "CM.com", "slug_company": "cmcom",
     "offer_slug": "principal-developer-mobile-service-cloud", "offer_id": 2633464,
     "role": "Principal Developer (Mobile Service Cloud)", "location": "Arnhem"},
    {"company": "CM.com", "slug_company": "cmcom",
     "offer_slug": "senior-developer-2", "offer_id": 2569319,
     "role": "Senior Developer", "location": "Amsterdam"},
    # DPG Media
    {"company": "DPG Media", "slug_company": "dpgmedia",
     "offer_slug": "team-lead-backend-development", "offer_id": 2622234,
     "role": "Team Lead Backend Development", "location": "Amsterdam"},
    {"company": "DPG Media", "slug_company": "dpgmedia",
     "offer_slug": "senior-fullstack-developer-qmusic-joe-willy", "offer_id": 2571508,
     "role": "Software Engineer Broadcast Systems", "location": "Amsterdam"},
    {"company": "DPG Media", "slug_company": "dpgmedia",
     "offer_slug": "medior-fullstack-engineer", "offer_id": 2562179,
     "role": "Medior Fullstack Engineer", "location": "Amsterdam"},
    {"company": "DPG Media", "slug_company": "dpgmedia",
     "offer_slug": "python-software-developer", "offer_id": 2504892,
     "role": "Python Software Developer", "location": "Hilversum"},
    {"company": "DPG Media", "slug_company": "dpgmedia",
     "offer_slug": "senior-back-end-developer-1", "offer_id": 2443057,
     "role": "Senior Back-end Developer", "location": "Rotterdam"},
    # Conclusion
    {"company": "Conclusion", "slug_company": "conclusion",
     "offer_slug": "full-stack-software-engineer-mediorsenior", "offer_id": 2410608,
     "role": "Full-stack Software Engineer medior/senior", "location": "Amsterdam"},
    {"company": "Conclusion", "slug_company": "conclusion",
     "offer_slug": "full-stack-developer-nijmegen-2", "offer_id": 2091469,
     "role": "Full Stack Developer Nieuwegein", "location": "Nieuwegein"},
    {"company": "Conclusion", "slug_company": "conclusion",
     "offer_slug": "here-your-job-title-template-basic", "offer_id": 2091284,
     "role": "Full Stack Developer Nijmegen", "location": "Nijmegen"},
]


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
    company = c["company"]
    slug_company = c["slug_company"]
    offer_slug = c["offer_slug"]
    offer_id = c["offer_id"]
    role = c["role"]
    location = c["location"]

    api_url = f"https://{slug_company}.recruitee.com/api/offers/{offer_slug}/candidates"
    cover_letter = build_cover_letter(company, role, location)

    # Use multipart form data (same as browser form submission)
    cmd = [
        "curl", "-s", "-X", "POST", api_url,
        "-F", "candidate[name]=Hisham Abboud",
        "-F", "candidate[email]=hiaham123@hotmail.com",
        "-F", "candidate[phone]=+31648412838",
        "-F", f"candidate[cover_letter]={cover_letter}",
        "-F", f"candidate[cv]=@{str(RESUME_PATH)};type=application/pdf",
        "--max-time", "30",
        "-w", "\nHTTP_CODE:%{http_code}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    # Extract HTTP code
    http_match = re.search(r"\nHTTP_CODE:(\d+)", output)
    http_code = int(http_match.group(1)) if http_match else 0
    response_text = output.rsplit("\nHTTP_CODE:", 1)[0].strip()

    try:
        resp = json.loads(response_text)
        ok = resp.get("ok", False)
        candidate_id = resp.get("candidate", {}).get("id", "")
    except Exception:
        ok = False
        candidate_id = ""
        # Check if it's a success based on HTTP code
        if http_code in (200, 201):
            ok = True

    return ok, http_code, response_text, candidate_id, api_url


def main():
    with open(APPS_PATH) as f:
        apps = json.load(f)

    # Check already-applied offer IDs from this batch to avoid duplicates
    applied_offer_ids = set()
    for a in apps:
        if a.get("offer_id") and a.get("status") == "applied":
            applied_offer_ids.add(a["offer_id"])

    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=278) + 1

    applied = 0
    failed = 0
    skipped = 0

    for i, c in enumerate(CANDIDATES):
        company = c["company"]
        role = c["role"]
        offer_id = c["offer_id"]
        location = c["location"]

        # Skip if already applied
        if offer_id in applied_offer_ids:
            print(f"  [~] {next_id:3d} {company} - {role} | skipped (already applied)")
            skipped += 1
            next_id += 1
            continue

        ok, http_code, response_text, candidate_id, api_url = submit_candidate(c)

        status = "applied" if ok else "failed"
        symbol = "+" if ok else "x"

        notes = f"Applied via Recruitee API (multipart, offer slug). HTTP {http_code}. Response: {response_text[:200]}"
        if candidate_id:
            notes = f"Applied via Recruitee API. Candidate ID {candidate_id}. HTTP {http_code}."

        app_record = {
            "id": next_id,
            "company": company,
            "role": role,
            "url": f"https://{c['slug_company']}.recruitee.com/o/{c['offer_slug']}",
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
        next_id += 1

        if ok:
            applied += 1
        else:
            failed += 1

        print(f"  [{symbol}] {next_id-1:3d} {company} - {role} | {status} (HTTP {http_code})")
        if not ok:
            print(f"       Response: {response_text[:150]}")

        if i < len(CANDIDATES) - 1:
            time.sleep(2)

    with open(APPS_PATH, "w") as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {applied} applied, {failed} failed, {skipped} skipped, total tracker: {len(apps)}")


if __name__ == "__main__":
    main()
