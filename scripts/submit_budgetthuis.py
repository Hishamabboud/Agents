#!/usr/bin/env python3
"""
Submit the Budget Thuis Full-Stack Software Engineer application.

Verified fit: the posting asks for hands-on C# and TypeScript across backend
and React front-end, microservices, Docker, CI/CD and fluent English, states
no minimum years, is located in Amsterdam and rules out relocation (already
resident). Cover letter lives in output/cover-letters/.

Runs the same five dedupe guards as submit_batch_v6.py before posting, and
appends the result to data/applications.json.

Usage:
    python3 scripts/submit_budgetthuis.py --dry-run   # check guards only
    python3 scripts/submit_budgetthuis.py             # submit
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"
COVER_PATH = BASE_DIR / "output" / "cover-letters" / "budget-thuis-full-stack-software-engineer.md"

CANDIDATE = {
    "company": "Budget Thuis",
    "slug_company": "budgetthuis",
    "offer_slug": "full-stack-software-engineer",
    "offer_id": 2687743,
    "role": "Full-Stack Software Engineer",
    "location": "Amsterdam",
}

BLOCKED_SLUGS = {
    "fridayrecruitment", "bimcollab", "sendent", "funda", "sendcloud",
    "chipsoft", "ubiops", "prodrive", "futuresworks", "yellowtail",
}


def load_cover_letter() -> str:
    """Read the letter body, dropping the markdown header block."""
    text = COVER_PATH.read_text()
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) > 2 else text.strip()


def check_guards(apps: list[dict]) -> list[str]:
    """Return a list of guard failures; empty means safe to submit."""
    slug = CANDIDATE["slug_company"]
    company = CANDIDATE["company"].lower().strip()
    role = CANDIDATE["role"].lower().strip()
    failures = []

    if slug in BLOCKED_SLUGS:
        failures.append(f"slug '{slug}' is blocklisted")

    slug_counts: dict[str, int] = {}
    already: set[str] = set()
    company_counts: dict[str, int] = {}
    for a in apps:
        for url in (a.get("url", ""), a.get("recruitee_api_url", "")):
            m = re.search(r"https?://([^.]+)\.recruitee\.com", str(url))
            if m:
                slug_counts[m.group(1)] = slug_counts.get(m.group(1), 0) + 1
        already.add(f"{(a.get('company') or '').lower().strip()}|{(a.get('role') or '').lower().strip()}")
        if a.get("offer_id"):
            already.add(str(a["offer_id"]))
        if a.get("status") in ("applied", "action_required"):
            cn = (a.get("company") or "").lower().strip()
            company_counts[cn] = company_counts.get(cn, 0) + 1

    if str(CANDIDATE["offer_id"]) in already:
        failures.append("this offer_id was already applied to")
    if f"{company}|{role}" in already:
        failures.append("this company and role were already applied to")
    if slug_counts.get(slug, 0) >= 2:
        failures.append(f"slug '{slug}' already has {slug_counts[slug]} applications")
    if company_counts.get(company, 0) >= 2:
        failures.append(f"'{CANDIDATE['company']}' already has {company_counts[company]} applications")
    return failures


def submit() -> tuple[bool, str, str, str]:
    """POST the application to the Recruitee candidates endpoint."""
    api_url = (
        f"https://{CANDIDATE['slug_company']}.recruitee.com"
        f"/api/offers/{CANDIDATE['offer_slug']}/candidates"
    )
    tmp = Path("/tmp/recruitee_budgetthuis.json")
    cmd = [
        "curl", "-s", "-o", str(tmp), "-w", "%{http_code}",
        "-X", "POST", api_url,
        "-F", "candidate[name]=Hisham Abboud",
        "-F", "candidate[email]=hiaham123@hotmail.com",
        "-F", "candidate[phone]=+31648412838",
        "-F", f"candidate[cover_letter]={load_cover_letter()}",
        "-F", f"candidate[cv]=@{RESUME_PATH};type=application/pdf",
        "--max-time", "60",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    status = result.stdout.strip()
    body = tmp.read_text() if tmp.exists() else ""
    candidate_id = ""
    try:
        payload = json.loads(body)
        candidate_id = str(payload.get("candidate", {}).get("id", "") or payload.get("id", ""))
    except json.JSONDecodeError:
        pass
    return (status == "201" or bool(candidate_id)), status, body, candidate_id


def main():
    parser = argparse.ArgumentParser(description="Submit the Budget Thuis application")
    parser.add_argument("--dry-run", action="store_true", help="Run the guards without submitting")
    args = parser.parse_args()

    if not RESUME_PATH.exists():
        sys.exit(f"ERROR: CV not found at {RESUME_PATH}")
    if not COVER_PATH.exists():
        sys.exit(f"ERROR: cover letter not found at {COVER_PATH}")

    apps = json.loads(APPS_PATH.read_text())
    failures = check_guards(apps)
    if failures:
        print("Refusing to submit:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All dedupe guards passed.")

    if args.dry_run:
        print(f"[dry run] would POST to {CANDIDATE['slug_company']}.recruitee.com "
              f"offer {CANDIDATE['offer_slug']} ({CANDIDATE['offer_id']})")
        return

    ok, status, body, candidate_id = submit()
    print(f"HTTP {status} | candidate_id={candidate_id or '-'}")
    if not ok:
        print(f"Response: {body[:300]}")

    notes = (
        f"Applied via Recruitee API. Candidate ID {candidate_id}. HTTP {status}."
        if candidate_id
        else f"Recruitee API submission. HTTP {status}. Response: {body[:200]}"
    )
    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=282) + 1
    apps.append({
        "id": next_id,
        "company": CANDIDATE["company"],
        "role": CANDIDATE["role"],
        "url": f"https://werkenbijbudgetthuis.nl/o/{CANDIDATE['offer_slug']}",
        "date_applied": datetime.now().isoformat(),
        "score": 9,
        "status": "applied" if ok else "failed",
        "resume_file": str(RESUME_PATH.resolve()),
        "cover_letter_file": str(COVER_PATH.resolve()),
        "screenshot": None,
        "notes": notes,
        "email_used": "hiaham123@hotmail.com",
        "offer_id": CANDIDATE["offer_id"],
        "offer_slug": CANDIDATE["offer_slug"],
        "recruitee_api_url": (
            f"https://{CANDIDATE['slug_company']}.recruitee.com"
            f"/api/offers/{CANDIDATE['offer_slug']}/candidates"
        ),
        "location": CANDIDATE["location"],
        "response": None,
        **({"candidate_id": candidate_id} if candidate_id else {}),
    })
    APPS_PATH.write_text(json.dumps(apps, indent=2, ensure_ascii=False))
    print(f"Tracker updated: {'applied' if ok else 'failed'} (id {next_id})")


if __name__ == "__main__":
    main()
