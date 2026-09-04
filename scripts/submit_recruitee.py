#!/usr/bin/env python3
"""
Submit one application to a Recruitee-hosted vacancy.

Generalizes submit_budgetthuis.py: pass the company, board slug and offer on
the command line instead of editing a script per application. Runs the same
five dedupe guards as submit_batch_v6.py and appends the outcome to
data/applications.json.

Usage:
    python3 scripts/submit_recruitee.py \
        --company "Portbase" --slug portbase \
        --offer full-stack-developer --offer-id 2324137 \
        --role "Full-Stack Developer" --location Rotterdam \
        --cover output/cover-letters/portbase-full-stack-developer.md \
        --dry-run
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

BLOCKED_SLUGS = {
    "fridayrecruitment", "bimcollab", "sendent", "funda", "sendcloud",
    "chipsoft", "ubiops", "prodrive", "futuresworks", "yellowtail",
}


def load_cover_letter(path: Path) -> str:
    """Read the letter body, dropping the markdown header block."""
    text = path.read_text()
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) > 2 else text.strip()


def check_guards(apps: list[dict], company: str, slug: str, role: str, offer_id: int) -> list[str]:
    """Return a list of guard failures; empty means safe to submit."""
    company_key = company.lower().strip()
    role_key = role.lower().strip()
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

    if offer_id and str(offer_id) in already:
        failures.append("this offer_id was already applied to")
    if f"{company_key}|{role_key}" in already:
        failures.append("this company and role were already applied to")
    if slug_counts.get(slug, 0) >= 2:
        failures.append(f"slug '{slug}' already has {slug_counts[slug]} applications")
    if company_counts.get(company_key, 0) >= 2:
        failures.append(f"'{company}' already has {company_counts[company_key]} applications")
    return failures


def submit(slug: str, offer: str, cover_letter: str) -> tuple[bool, str, str, str]:
    """POST the application to the Recruitee candidates endpoint."""
    api_url = f"https://{slug}.recruitee.com/api/offers/{offer}/candidates"
    tmp = Path(f"/tmp/recruitee_{slug}.json")
    cmd = [
        "curl", "-s", "-o", str(tmp), "-w", "%{http_code}",
        "-X", "POST", api_url,
        "-F", "candidate[name]=Hisham Abboud",
        "-F", "candidate[email]=hiaham123@hotmail.com",
        "-F", "candidate[phone]=+31648412838",
        "-F", f"candidate[cover_letter]={cover_letter}",
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
    parser = argparse.ArgumentParser(description="Submit one Recruitee application")
    parser.add_argument("--company", required=True)
    parser.add_argument("--slug", required=True, help="Recruitee board slug")
    parser.add_argument("--offer", required=True, help="Offer slug")
    parser.add_argument("--offer-id", type=int, default=0)
    parser.add_argument("--role", required=True)
    parser.add_argument("--location", default="")
    parser.add_argument("--cover", required=True, help="Path to the cover letter markdown")
    parser.add_argument("--careers-url", default="", help="Public posting URL for the tracker")
    parser.add_argument("--score", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cover_path = BASE_DIR / args.cover if not Path(args.cover).is_absolute() else Path(args.cover)
    if not RESUME_PATH.exists():
        sys.exit(f"ERROR: CV not found at {RESUME_PATH}")
    if not cover_path.exists():
        sys.exit(f"ERROR: cover letter not found at {cover_path}")

    apps = json.loads(APPS_PATH.read_text())
    failures = check_guards(apps, args.company, args.slug, args.role, args.offer_id)
    if failures:
        print("Refusing to submit:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All dedupe guards passed.")

    if args.dry_run:
        print(f"[dry run] would POST to {args.slug}.recruitee.com offer {args.offer} ({args.offer_id})")
        return

    ok, status, body, candidate_id = submit(args.slug, args.offer, load_cover_letter(cover_path))
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
        "company": args.company,
        "role": args.role,
        "url": args.careers_url or f"https://{args.slug}.recruitee.com/o/{args.offer}",
        "date_applied": datetime.now().isoformat(),
        "score": args.score,
        "status": "applied" if ok else "failed",
        "resume_file": str(RESUME_PATH.resolve()),
        "cover_letter_file": str(cover_path.resolve()),
        "screenshot": None,
        "notes": notes,
        "email_used": "hiaham123@hotmail.com",
        "offer_id": args.offer_id,
        "offer_slug": args.offer,
        "recruitee_api_url": f"https://{args.slug}.recruitee.com/api/offers/{args.offer}/candidates",
        "location": args.location,
        "response": None,
        **({"candidate_id": candidate_id} if candidate_id else {}),
    })
    APPS_PATH.write_text(json.dumps(apps, indent=2, ensure_ascii=False))
    print(f"Tracker updated: {'applied' if ok else 'failed'} (id {next_id})")


if __name__ == "__main__":
    main()
