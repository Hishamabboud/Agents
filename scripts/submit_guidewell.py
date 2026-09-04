#!/usr/bin/env python3
"""
Submit one application through the Guidewell vacancy form.

Guidewell is a recruitment agency that runs several .NET vacancies on behalf
of named employers. Its postings use a WordPress multipart form rather than an
ATS API, so this mirrors submit_recruitee.py for that form.

Agency rules from profile/preferences.md apply: every Guidewell listing counts
against one shared cap of two applications, and applications to the same agency
are spaced at least a week apart. Both are enforced below.

Usage:
    python3 scripts/submit_guidewell.py \
        --vacancy-id 730 \
        --vacancy-title "Fullstack Developer | 45K-60K | Sierteelt | Leiden" \
        --role "Fullstack Developer (C#/.NET)" \
        --employer "ALFA PRO (via Guidewell)" \
        --location Leiden \
        --slug fullstack-developer-45k-60k-sierteelt-leiden \
        --dry-run
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
APPS_PATH = BASE_DIR / "data" / "applications.json"

AGENCY = "guidewell"
FORM_ENDPOINT = "https://guidewell.nl/wp-admin/admin-post.php"
FORM_ACTION = "send_application_form_to_rf"
AGENCY_CAP = 2
SPACING_DAYS = 7


def agency_applications(apps: list[dict]) -> list[dict]:
    """Every application routed through this agency, however it was recorded."""
    found = []
    for a in apps:
        haystack = " ".join(
            str(a.get(k, "")) for k in ("company", "url", "notes", "recruitee_api_url")
        ).lower()
        if AGENCY in haystack:
            found.append(a)
    return found


def check_guards(apps: list[dict], vacancy_id: int, role: str) -> list[str]:
    """Agency cap, spacing and duplicate checks. Empty list means safe."""
    failures = []
    prior = agency_applications(apps)

    if len(prior) >= AGENCY_CAP:
        failures.append(f"agency '{AGENCY}' already has {len(prior)} applications (cap {AGENCY_CAP})")

    for a in prior:
        if str(a.get("vacancy_id", "")) == str(vacancy_id):
            failures.append(f"vacancy_id {vacancy_id} was already applied to")
        if (a.get("role") or "").lower().strip() == role.lower().strip():
            failures.append(f"role '{role}' was already applied to via this agency")
        try:
            when = datetime.fromisoformat(a["date_applied"])
        except (KeyError, ValueError):
            continue
        gap = datetime.now() - when
        if gap < timedelta(days=SPACING_DAYS):
            failures.append(
                f"last {AGENCY} application was {gap.days}d ago; policy is {SPACING_DAYS}d spacing"
            )
    return failures


def submit(vacancy_id: int, vacancy_title: str, slug: str) -> tuple[bool, str, str]:
    """POST the multipart application form."""
    tmp = Path(f"/tmp/guidewell_{vacancy_id}.html")
    cmd = [
        "curl", "-s", "-L", "-o", str(tmp), "-w", "%{http_code}",
        "-X", "POST", FORM_ENDPOINT,
        "-e", f"https://guidewell.nl/vacature/{slug}/",
        "-F", f"action={FORM_ACTION}",
        "-F", f"vacancy_title={vacancy_title}",
        "-F", f"vacancy_id={vacancy_id}",
        "-F", "firstName=Hisham",
        "-F", "lastName=Abboud",
        "-F", "email=hiaham123@hotmail.com",
        "-F", "phone=+31648412838",
        "-F", "linkedin=https://linkedin.com/in/hisham-abboud",
        "-F", f"cv_file=@{RESUME_PATH};type=application/pdf",
        "--max-time", "60",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    status = result.stdout.strip()
    body = tmp.read_text(errors="ignore") if tmp.exists() else ""
    ok = status in ("200", "302")
    return ok, status, body


def main():
    parser = argparse.ArgumentParser(description="Submit a Guidewell application")
    parser.add_argument("--vacancy-id", type=int, required=True)
    parser.add_argument("--vacancy-title", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--employer", required=True, help="Company name for the tracker")
    parser.add_argument("--location", default="")
    parser.add_argument("--slug", required=True, help="Vacancy URL slug, used as the referer")
    parser.add_argument("--score", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not RESUME_PATH.exists():
        sys.exit(f"ERROR: CV not found at {RESUME_PATH}")

    apps = json.loads(APPS_PATH.read_text())
    failures = check_guards(apps, args.vacancy_id, args.role)
    if failures:
        print("Refusing to submit:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"Guards passed ({len(agency_applications(apps))} prior {AGENCY} applications).")

    if args.dry_run:
        print(f"[dry run] would POST vacancy {args.vacancy_id} to {FORM_ENDPOINT}")
        return

    ok, status, body = submit(args.vacancy_id, args.vacancy_title, args.slug)
    print(f"HTTP {status} | response {len(body)} bytes")
    lowered = body.lower()
    for marker in ("bedankt", "thank", "success", "verzonden", "ontvangen", "error", "fout"):
        if marker in lowered:
            print(f"  response mentions: '{marker}'")

    next_id = max((a.get("id", 0) for a in apps if isinstance(a.get("id"), int)), default=282) + 1
    apps.append({
        "id": next_id,
        "company": args.employer,
        "role": args.role,
        "url": f"https://guidewell.nl/vacature/{args.slug}/",
        "date_applied": datetime.now().isoformat(),
        "score": args.score,
        "status": "applied" if ok else "failed",
        "resume_file": str(RESUME_PATH.resolve()),
        "cover_letter_file": None,
        "screenshot": None,
        "notes": (
            f"Applied via Guidewell vacancy form (WordPress admin-post, multipart). "
            f"HTTP {status}. vacancy_id={args.vacancy_id}. Agency handles recruitment "
            f"exclusively for this employer; form accepts CV only, no cover letter field."
        ),
        "email_used": "hiaham123@hotmail.com",
        "vacancy_id": args.vacancy_id,
        "location": args.location,
        "response": None,
    })
    APPS_PATH.write_text(json.dumps(apps, indent=2, ensure_ascii=False))
    print(f"Tracker updated: {'applied' if ok else 'failed'} (id {next_id})")


if __name__ == "__main__":
    main()
