#!/usr/bin/env python3
"""Batch submit job applications via Recruitee API using multipart form-data."""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"
CANDIDATES_PATH = Path("/tmp/new_candidates.json")


def main():
    with open(APPS_PATH) as f:
        apps = json.load(f)

    with open(CANDIDATES_PATH) as f:
        candidates = json.load(f)

    # Remove previous failed attempts for these offer_ids so we don't duplicate
    existing_offer_ids = {c['offer_id'] for c in candidates}
    apps = [a for a in apps if a.get('offer_id') not in existing_offer_ids or a.get('status') != 'failed']

    next_id = max((a.get('id', 0) for a in apps if isinstance(a.get('id'), int)), default=240) + 1

    applied = 0
    failed = 0

    for i, c in enumerate(candidates):
        slug = c['slug']
        offer_id = c['offer_id']
        company = c['company']
        role = c['role']
        location = c['location']
        # No ?async=true - use the standard candidates endpoint
        api_url = f"https://{slug}.recruitee.com/api/offers/{offer_id}/candidates"

        cover_letter = (
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

        # Use literal bracket notation candidate[name] - NOT URL-encoded %5B%5D
        # The Recruitee Rails backend expects standard nested params: candidate[field]
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", api_url,
             "-F", "candidate[name]=Hisham Abboud",
             "-F", "candidate[email]=hiaham123@hotmail.com",
             "-F", "candidate[phone]=+31 06 4841 2838",
             "-F", f"candidate[cover_letter]={cover_letter}",
             "-F", f"candidate[cv]=@{RESUME_PATH};type=application/pdf",
             "--max-time", "30"],
            capture_output=True, text=True
        )

        response_text = result.stdout.strip()
        try:
            resp = json.loads(response_text)
            ok = resp.get("ok", False)
            candidate_id = resp.get("candidate", {}).get("id", "")
        except Exception:
            ok = False
            candidate_id = ""

        status = "applied" if ok else "failed"
        symbol = "+" if ok else "x"

        app_record = {
            "id": next_id,
            "company": company,
            "role": role,
            "url": f"https://{slug}.recruitee.com/o/{offer_id}",
            "date_applied": datetime.now().isoformat(),
            "score": 7,
            "status": status,
            "resume_file": str(RESUME_PATH.resolve()),
            "cover_letter_file": None,
            "screenshot": None,
            "notes": f"Applied via Recruitee API (multipart). Response: {response_text[:200]}",
            "email_used": "hiaham123@hotmail.com",
            "offer_id": offer_id,
            "recruitee_api_url": api_url,
            "location": location,
            "response": None
        }
        if candidate_id:
            app_record["candidate_id"] = candidate_id

        apps.append(app_record)
        next_id += 1

        if ok:
            applied += 1
        else:
            failed += 1

        print(f"  [{symbol}] {next_id-1:3d} {company} - {role} | {status} | {response_text[:80]}")

        if i < len(candidates) - 1:
            time.sleep(2)

    with open(APPS_PATH, 'w') as f:
        json.dump(apps, f, indent=2, ensure_ascii=False)

    print(f"\nDone: {applied} applied, {failed} failed, total tracker: {len(apps)}")


if __name__ == "__main__":
    main()
