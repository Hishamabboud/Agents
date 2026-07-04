#!/usr/bin/env python3
"""Batch submit v9 — 27 new companies found 2026-07-04 via LinkedIn job-listing
mining (real company names cross-referenced against live Recruitee tenants,
rather than guessing subdomains). Live-verified via Recruitee API before submission."""

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
    {"company": 'alfa1 group', "slug_company": 'alfa1',
     "offer_slug": 'full-stack-developer', "offer_id": 2633279,
     "role": 'Full stack Developer', "location": 'Veldhoven'},
    {"company": 'Tools4ever B.V.', "slug_company": 'tools4ever',
     "offer_slug": 'ai-automation-engineer', "offer_id": 2511162,
     "role": 'AI & Automation Engineer', "location": 'Baarn'},
    {"company": 'Tools4ever B.V.', "slug_company": 'tools4ever',
     "offer_slug": 'net-developer', "offer_id": 2498723,
     "role": '.NET Developer', "location": 'Baarn'},
    {"company": 'VWE Automotive', "slug_company": 'vweautomotive',
     "offer_slug": 'devops-cloud-platform-engineer-azure', "offer_id": 2535450,
     "role": 'DevOps / Cloud Platform Engineer (Azure)', "location": 'Heerhugowaard'},
    {"company": 'VWE Automotive', "slug_company": 'vweautomotive',
     "offer_slug": 'senior-backend-developer-1', "offer_id": 2397184,
     "role": 'Senior Backend Developer', "location": 'Heerhugowaard'},
    {"company": 'SkyGeo', "slug_company": 'skygeo',
     "offer_slug": 'scientific-software-developer-2-3', "offer_id": 1966696,
     "role": 'Full-Stack Developer', "location": 'Delft'},
    {"company": 'Workspace 365', "slug_company": 'workspace365',
     "offer_slug": 'aipython-engineer-mediorsenior', "offer_id": 2403366,
     "role": 'AI/Python Engineer (Medior/Senior)', "location": 'Nijkerk'},
    {"company": 'Freeday', "slug_company": 'freeday',
     "offer_slug": 'software-engineer-3', "offer_id": 2604583,
     "role": 'Software Engineer', "location": 'Rotterdam'},
    {"company": 'Puur Data', "slug_company": 'puurdata',
     "offer_slug": 'data-engineer-3', "offer_id": 2620306,
     "role": 'Data Engineer', "location": 'Ede'},
    {"company": 'UPFRONT', "slug_company": 'upfront',
     "offer_slug": 'backend-engineer', "offer_id": 2630774,
     "role": 'Backend Engineer', "location": 'Rotterdam'},
    {"company": 'Samotics', "slug_company": 'samotics',
     "offer_slug": 'full-stack-software-engineer-3015', "offer_id": 2637005,
     "role": 'Full-stack Software Engineer', "location": 'Leiden'},
    {"company": 'RebelsAI', "slug_company": 'rebelsai',
     "offer_slug": 'machine-learning-engineer', "offer_id": 2334073,
     "role": 'Machine Learning Engineer', "location": 'Rotterdam'},
    {"company": 'umob', "slug_company": 'umob',
     "offer_slug": 'backend-software-engineer-net', "offer_id": 2262019,
     "role": 'Backend Software Engineer (.NET)', "location": 'Rotterdam'},
    {"company": '12Build', "slug_company": '12build',
     "offer_slug": 'data-engineer-3', "offer_id": 2650864,
     "role": 'Data Engineer', "location": 'Nijverdal'},
    {"company": '12Build', "slug_company": '12build',
     "offer_slug": 'ai-engineer', "offer_id": 2650472,
     "role": 'AI Engineer', "location": 'Nijverdal'},
    {"company": 'GRID', "slug_company": 'grid',
     "offer_slug": 'backend-engineer-mfx', "offer_id": 2663303,
     "role": 'Backend Engineer (m/f/x)', "location": 'Berlin'},
    {"company": 'Lleverage', "slug_company": 'lleverage',
     "offer_slug": 'forward-deployed-ai-engineer', "offer_id": 2320753,
     "role": 'Forward Deployed AI Engineer', "location": 'Amsterdam'},
    {"company": 'Lleverage', "slug_company": 'lleverage',
     "offer_slug": 'ai-engineer-2', "offer_id": 2220488,
     "role": 'AI Engineer', "location": 'Amsterdam'},
    {"company": 'Digital Survival Company', "slug_company": 'digitalsurvivalcompany',
     "offer_slug": 'senior-cloud-engineer', "offer_id": 2532582,
     "role": 'Senior Cloud Engineer', "location": 'Nieuwegein'},
    {"company": 'DataVisual', "slug_company": 'datavisual',
     "offer_slug": 'medior-devops-engineer', "offer_id": 869338,
     "role": 'Medior DevOps Engineer', "location": 'Enter'},
    {"company": 'DataVisual', "slug_company": 'datavisual',
     "offer_slug": 'software-developer', "offer_id": 1621822,
     "role": 'Software Developer', "location": 'Enter'},
    {"company": '4CEE', "slug_company": '4cee',
     "offer_slug": 'back-end-developer-1', "offer_id": 2424799,
     "role": 'Back-end developer', "location": 'Ede'},
    {"company": 'TicketSwap', "slug_company": 'ticketswap',
     "offer_slug": 'software-engineer-backend', "offer_id": 2600511,
     "role": 'Software Engineer Backend', "location": 'Amsterdam'},
    {"company": 'SIDN', "slug_company": 'sidn',
     "offer_slug": 'backend-engineer-registry-services', "offer_id": 2646380,
     "role": 'Backend Engineer - Registry Services', "location": 'Arnhem'},
    {"company": 'Mantel', "slug_company": 'mantel',
     "offer_slug": 'back-enddeveloper', "offer_id": 2209822,
     "role": 'Back-End Developer', "location": 'Arnhem'},
    {"company": 'Bluerock TMS', "slug_company": 'careerbluerocktms',
     "offer_slug": 'java-software-developer-2', "offer_id": 1847746,
     "role": '.NET Software Developer', "location": "'s-Hertogenbosch"},
    {"company": 'Voetencentrum Wender', "slug_company": 'steppfootcare',
     "offer_slug": 'software-engineer-rd', "offer_id": 2356961,
     "role": 'Software Engineer R&D', "location": 'Haaksbergen'},
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
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=312) + 1
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
