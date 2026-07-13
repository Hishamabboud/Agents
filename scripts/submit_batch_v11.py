#!/usr/bin/env python3
"""Batch submit v11 — 17 new companies found 2026-07-05 via a third LinkedIn
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
    {"company": 'Syntho', "slug_company": 'syntho',
     "offer_slug": 'senior-software-engineer-3', "offer_id": 2619823,
     "role": 'Senior Software Engineer', "location": 'Amsterdam'},
    {"company": 'Wefabricate', "slug_company": 'wefabricate',
     "offer_slug": 'embedded-devops-integration-engineer', "offer_id": 2620962,
     "role": 'Embedded DevOps & Integration Engineer', "location": 'Duizel'},
    {"company": 'Wefabricate', "slug_company": 'wefabricate',
     "offer_slug": 'data-platform-engineer', "offer_id": 2540637,
     "role": 'Data Platform Engineer', "location": 'Duizel'},
    {"company": 'Quality', "slug_company": 'quality',
     "offer_slug": 'cloud-engineer-medior', "offer_id": 1211926,
     "role": 'Cloud Engineer (Medior)', "location": 'Capelle aan den IJssel'},
    {"company": 'Social Deal', "slug_company": 'socialdeal',
     "offer_slug": 'teamlead-backend-2', "offer_id": 2608798,
     "role": 'Teamlead Backend', "location": "'s-Hertogenbosch"},
    {"company": 'Social Deal', "slug_company": 'socialdeal',
     "offer_slug": 'devops-engineer-aws-6', "offer_id": 2527828,
     "role": 'Devops Engineer (AWS)', "location": "'s-Hertogenbosch"},
    {"company": 'Aquablu', "slug_company": 'aquablu',
     "offer_slug": 'senior-ai-platform-engineer', "offer_id": 2670919,
     "role": 'Senior AI Platform Engineer', "location": 'Amsterdam'},
    {"company": 'Aquablu', "slug_company": 'aquablu',
     "offer_slug": 'embedded-engineer', "offer_id": 1611312,
     "role": 'Embedded Software Engineer', "location": 'Amsterdam'},
    {"company": 'ISISPACE Group', "slug_company": 'isispace',
     "offer_slug": 'embedded-software-engineer-senior', "offer_id": 2356266,
     "role": 'Embedded Software Engineer - Senior', "location": 'Delft'},
    {"company": 'Online Payment Platform', "slug_company": 'onlinepaymentplatform',
     "offer_slug": 'senior-backend-developer-php', "offer_id": 2230602,
     "role": 'Senior Backend Developer (PHP)', "location": 'Delft'},
    {"company": 'Online Payment Platform', "slug_company": 'onlinepaymentplatform',
     "offer_slug": 'devops-engineer', "offer_id": 1329614,
     "role": 'Senior DevOps Engineer', "location": 'Delft'},
    {"company": 'Realworks', "slug_company": 'realworks',
     "offer_slug": 'platform-engineer-on-premise', "offer_id": 2155308,
     "role": 'Platform Engineer (on-premise)', "location": 'Amsterdam'},
    {"company": 'QuandaGo', "slug_company": 'quandago',
     "offer_slug": 'data-engineer', "offer_id": 1972127,
     "role": 'Data Engineer', "location": 'Capelle aan den IJssel'},
    {"company": 'QuandaGo', "slug_company": 'quandago',
     "offer_slug": 'golang-developer', "offer_id": 1698605,
     "role": 'Medior Software Engineer Golang', "location": 'Capelle aan den IJssel'},
    {"company": 'Vandoren', "slug_company": 'vandoren',
     "offer_slug": 'full-stack-developer-netreact-veghel', "offer_id": 2600419,
     "role": 'Full-stack Developer (.NET/React) (Veghel)', "location": 'Veghel'},
    {"company": 'Vandoren', "slug_company": 'vandoren',
     "offer_slug": 'software-engineer-heteren-5', "offer_id": 2550514,
     "role": 'Software engineer (Heteren)', "location": 'Heteren'},
    {"company": 'E-mergo', "slug_company": 'emergo',
     "offer_slug": 'senior-data-engineer-azure-microsoft-fabric', "offer_id": 2665035,
     "role": 'Senior Data Engineer Azure / Microsoft Fabric', "location": 'Delft'},
    {"company": 'E-mergo', "slug_company": 'emergo',
     "offer_slug": 'senior-data-engineer-backend-developer', "offer_id": 1079861,
     "role": 'Senior Data Engineer (Backend developer)', "location": 'Delft'},
    {"company": 'HatchTech Group', "slug_company": 'hatchtech',
     "offer_slug": 'fullstack-developer', "offer_id": 2666609,
     "role": 'Fullstack Developer', "location": 'Veenendaal - De Klomp'},
    {"company": 'TRIMIT', "slug_company": 'trimit',
     "offer_slug": 'software-developer-microsoft-business-central', "offer_id": 2430713,
     "role": 'Software Developer Microsoft Business Central', "location": 'Arnhem'},
    {"company": 'Qblox', "slug_company": 'qblox',
     "offer_slug": 'devops-engineer-3', "offer_id": 2654622,
     "role": 'DevOps Engineer', "location": 'Delft'},
    {"company": 'Qblox', "slug_company": 'qblox',
     "offer_slug": 'software-engineering-team-lead', "offer_id": 2513299,
     "role": 'Software Engineering Team Lead', "location": 'Delft'},
    {"company": 'Whitevision', "slug_company": 'whitevision',
     "offer_slug": 'tech-lead-c-net-saas-low-code-5500-7000-zoetermeer', "offer_id": 2658371,
     "role": 'Tech Lead (C# .NET - SaaS & Low-Code), €5.500 - €7.000 | Zoetermeer', "location": 'Zoetermeer'},
    {"company": 'Whitevision', "slug_company": 'whitevision',
     "offer_slug": 'mediorsenior-ai-engineer-5000-6500-bredazoetermeer', "offer_id": 2587415,
     "role": 'Medior/Senior AI Engineer, €5.000 - €6.500 | Breda/Zoetermeer', "location": 'Breda'},
    {"company": 'Pacmed', "slug_company": 'pacmed',
     "offer_slug": 'senior-software-engineer', "offer_id": 2673615,
     "role": 'Senior Software Engineer', "location": 'Amsterdam'},
    {"company": 'Pacmed', "slug_company": 'pacmed',
     "offer_slug": 'senior-data-scientist-ml-statistical-modelling', "offer_id": 2673560,
     "role": 'Senior Data Scientist (ML & Statistical Modelling)', "location": 'Amsterdam'},
    {"company": 'ITQ', "slug_company": 'joinitq',
     "offer_slug": 'ai-platform-engineer', "offer_id": 2583855,
     "role": 'AI Platform Engineer', "location": 'Beverwijk'},
    {"company": 'ITQ', "slug_company": 'joinitq',
     "offer_slug": 'hybrid-cloud-engineer-1', "offer_id": 2580733,
     "role": 'Hybrid Cloud Engineer', "location": 'Beverwijk'},
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
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=359) + 1
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
