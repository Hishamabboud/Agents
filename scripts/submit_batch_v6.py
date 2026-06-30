#!/usr/bin/env python3
"""Batch submit v6 — new companies found 2026-06-30 (deep search, strict dedup)."""

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
    {"company": "AIHR", "slug_company": "aihr",
     "offer_slug": "ai-first-software-engineer", "offer_id": 2613887,
     "role": "AI-First Software Engineer", "location": "Rotterdam"},

    {"company": "Weeztix", "slug_company": "weeztix",
     "offer_slug": "backend-developer", "offer_id": 636698,
     "role": "Senior Back-end Developer", "location": "Eindhoven"},

    {"company": "Stimmt", "slug_company": "stimmt",
     "offer_slug": "backend-developer-ai-focused", "offer_id": 2340481,
     "role": "Backend Developer (AI focused)", "location": "Enschede / Amsterdam"},
    {"company": "Stimmt", "slug_company": "stimmt",
     "offer_slug": "tech-consultant-senior-developer-ai-focused", "offer_id": 2337144,
     "role": "Tech Consultant / Senior Developer (AI focused)", "location": "Enschede"},

    {"company": "Rocketsourcers", "slug_company": "rocketsourcers",
     "offer_slug": "senior-backend-developer-api-platform", "offer_id": 2598887,
     "role": "Senior Backend Developer (API Platform)", "location": "Capelle aan den IJssel"},
    {"company": "Rocketsourcers", "slug_company": "rocketsourcers",
     "offer_slug": "senior-data-engineer", "offer_id": 2624783,
     "role": "Senior Data Engineer", "location": "Utrecht"},

    {"company": "OpenClaims", "slug_company": "openclaims",
     "offer_slug": "junior-backend-developer-mendixreactjavapython", "offer_id": 2627012,
     "role": "Junior Backend Developer (Mendix/React/Java/Python)", "location": "Amsterdam"},
    {"company": "OpenClaims", "slug_company": "openclaims",
     "offer_slug": "medior-backend-developer-mendixreactjavapython", "offer_id": 711457,
     "role": "Medior Backend Developer (Mendix/React/Java/Python)", "location": "Amsterdam"},

    {"company": "Harvest Digital", "slug_company": "harvestdigital1",
     "offer_slug": "full-stack-developer", "offer_id": 2574603,
     "role": "Full-Stack Developer", "location": "Groningen"},
    {"company": "Harvest Digital", "slug_company": "harvestdigital1",
     "offer_slug": "back-end-developer-3", "offer_id": 2574536,
     "role": "Back-End Developer", "location": "Groningen"},

    {"company": "Quad Solutions", "slug_company": "quadsolutions",
     "offer_slug": "software-developer", "offer_id": 607340,
     "role": "Software Developer", "location": "Eindhoven"},
    {"company": "Quad Solutions", "slug_company": "quadsolutions",
     "offer_slug": "junior-software-developer-1", "offer_id": 2513588,
     "role": "Junior Software Developer", "location": "Eindhoven"},

    {"company": "FreshMinds", "slug_company": "freshminds",
     "offer_slug": "ai-engineer", "offer_id": 2595094,
     "role": "AI Engineer", "location": "Leiden"},
    {"company": "FreshMinds", "slug_company": "freshminds",
     "offer_slug": "cloud-engineer-2", "offer_id": 1826018,
     "role": "Python Consultant", "location": "Leiden"},

    {"company": "Proforto", "slug_company": "proforto",
     "offer_slug": "senior-software-developer-bij-proforto", "offer_id": 2183081,
     "role": "Senior Software Developer", "location": "Nijmegen"},
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
    """Count applications per recruitee slug (status applied/action_required)."""
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
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=282) + 1
    applied = failed = skipped = 0

    for i, c in enumerate(CANDIDATES):
        company, slug, role = c["company"], c["slug_company"], c["role"]
        offer_id, location = c["offer_id"], c["location"]
        cl = company.lower().strip()

        # Guard 1: blocklist
        if slug in BLOCKED_SLUGS or cl in blocked:
            print(f"  [~] {company} - {role} | BLOCKED — skipping"); skipped += 1; continue
        # Guard 2: same offer already applied
        if str(offer_id) in already:
            print(f"  [~] {company} - {role} | already applied (offer_id) — skipping"); skipped += 1; continue
        # Guard 3: same company+role already applied
        key = f"{cl}|{role.lower().strip()}"
        if key in already:
            print(f"  [~] {company} - {role} | already applied (company+role) — skipping"); skipped += 1; continue
        # Guard 4: slug already applied 2+ times (catches renamed companies)
        if sl_counts.get(slug, 0) >= 2:
            print(f"  [~] {company} - {role} | slug '{slug}' already has 2+ apps — skipping"); skipped += 1; continue
        # Guard 5: company name already has 2+ apps
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
