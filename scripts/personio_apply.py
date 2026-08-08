#!/usr/bin/env python3
"""Personio ATS application submitter — second automatable channel after Recruitee.

DISCOVERED 2026-08-04. Personio is the dominant ATS in the German-speaking market and
widely used in NL/BE too, so this materially widens the reachable pool.

API surface (all on the tenant host, e.g. https://<slug>.jobs.personio.de):
  GET  /xml                                  public job feed, no auth
  GET  /api/v1/jobs/<id>/application-form    field schema incl. which are required
  POST /api/v1/documents                     multipart CV upload -> returns {uuid,...}
  POST /api/v1/jobs/<id>/application         JSON application submit

Note: the same paths on career-pages-api.personio.de return 401. Use the TENANT host,
which proxies them unauthenticated.

Submit payload shape (reverse-engineered from the career-page JS bundle):
  {
    subcompanyId, channelId, postingId, autoPostingChannelId,   # usually null
    sender: {id: "sender<rand>", value: ""},
    attributes: [{id: <field_name>, value: <str>}, ...],        # all fields EXCEPT email/documents
    files: [{...uploadedDoc, category: "cv"}],
    email: "...",
    idempotencyToken: <uuid4>
  }
Headers: Content-Type: application/json, Idempotency-Key: <same token>,
         x-company-id: <company_id scraped from the apply page>

NO CAPTCHA, no CSRF token, no login. Like Recruitee, this is an open public endpoint --
not a protection being circumvented.

CAUTION -- two required fields are commitments, not facts:
  available_from       -> notice period. Read from preferences, never invented.
  salary_expectations  -> a negotiating position. MUST come from the user.
Both are read from profile/preferences.md and the script refuses to run without them.
"""

import json
import random
import re
import subprocess
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "profile" / "Hisham Abboud CV.pdf"
PREFS_PATH = BASE_DIR / "profile" / "preferences.md"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def read_commitments():
    """Pull salary expectation + availability from preferences. Never guess these."""
    txt = PREFS_PATH.read_text() if PREFS_PATH.exists() else ""
    sal = re.search(r'Salary expectation \(Personio.*?\):\s*(.+)', txt)
    avail = re.search(r'Availability / notice period:\s*(.+)', txt)
    if not sal or not avail:
        raise SystemExit(
            "ABORT: preferences.md must define both:\n"
            "  - Salary expectation (Personio ...): <value>\n"
            "  - Availability / notice period: <value>\n"
            "These are commercial commitments and must be set by the candidate, not inferred."
        )
    return sal.group(1).strip(), avail.group(1).strip()


def get_form_schema(host, job_id):
    out = subprocess.run(
        ["curl", "-s", f"https://{host}/api/v1/jobs/{job_id}/application-form",
         "-A", UA, "-H", "Accept: application/json", "--max-time", "25"],
        capture_output=True, text=True).stdout
    return json.loads(out)


def get_company_id(host, job_id):
    html = subprocess.run(
        ["curl", "-sL", f"https://{host}/job/{job_id}/apply", "-A", UA, "--max-time", "30"],
        capture_output=True, text=True).stdout
    m = re.search(r'company_id\\?"\s*:\s*(\d+)', html)
    return m.group(1) if m else None


def upload_cv(host, job_id):
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", f"https://{host}/api/v1/documents", "-A", UA,
         "-H", f"Referer: https://{host}/job/{job_id}/apply",
         "-F", f"file=@{RESUME_PATH};type=application/pdf",
         "-F", "category=cv", "--max-time", "60"],
        capture_output=True, text=True).stdout
    doc = json.loads(out)
    if "uuid" not in doc:
        raise RuntimeError(f"CV upload failed: {out[:200]}")
    return doc


def submit(host, job_id, company_id, doc, salary, available, first, last, email, phone, location):
    schema = get_form_schema(host, job_id)
    names = {f["name"] for f in schema.get("fields", [])}

    values = {
        "first_name": first, "last_name": last, "phone": phone,
        "available_from": available, "salary_expectations": salary, "location": location,
    }
    attributes = [{"id": k, "value": v} for k, v in values.items() if k in names and v]

    missing = [f["name"] for f in schema.get("fields", [])
               if f.get("required") and f["name"] not in ("email",)
               and f["name"] not in {a["id"] for a in attributes}]
    if missing:
        raise RuntimeError(f"Cannot fill required field(s) {missing} -- log for manual apply, do not guess")

    token = str(uuid.uuid4())
    payload = {
        "subcompanyId": None, "channelId": None, "postingId": None,
        "autoPostingChannelId": None,
        "sender": {"id": f"sender{random.randint(100000, 999999)}", "value": ""},
        "attributes": attributes,
        "files": [{**doc, "category": "cv"}],
        "email": email,
        "idempotencyToken": token,
    }
    tmp = Path("/tmp/personio_payload.json")
    tmp.write_text(json.dumps(payload))

    cmd = ["curl", "-s", "-X", "POST",
           f"https://{host}/api/v1/jobs/{job_id}/application", "-A", UA,
           "-H", "Content-Type: application/json",
           "-H", f"Idempotency-Key: {token}",
           "-H", f"Referer: https://{host}/job/{job_id}/apply",
           "--data-binary", f"@{tmp}", "-w", "\nHTTP_STATUS:%{http_code}", "--max-time", "60"]
    if company_id:
        cmd[-6:-6] = ["-H", f"x-company-id: {company_id}"]
    r = subprocess.run(cmd, capture_output=True, text=True).stdout
    status = r.split("HTTP_STATUS:")[-1].strip()
    return status, r.split("HTTP_STATUS:")[0][:400]


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True, help="e.g. zvoove.jobs.personio.de")
    p.add_argument("--job-id", required=True)
    args = p.parse_args()

    salary, available = read_commitments()
    cid = get_company_id(args.host, args.job_id)
    doc = upload_cv(args.host, args.job_id)
    status, body = submit(
        args.host, args.job_id, cid, doc, salary, available,
        first="Hisham", last="Abboud", email="hiaham123@hotmail.com",
        phone="+31648412838", location="Eindhoven, Netherlands",
    )
    print(f"HTTP {status}\n{body}")
