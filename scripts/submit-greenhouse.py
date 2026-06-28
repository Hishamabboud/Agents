#!/usr/bin/env python3
"""
Submit the ClickHouse Cloud Software Engineer - IAM application
via Greenhouse's traditional form POST endpoint.
"""

import requests
import json
import os
import re
import sys
from datetime import date

# ---- Config ----
JOB_URL = "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004"
SUBMIT_URL = "https://boards.greenhouse.io/clickhouse/jobs/5803692004"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/clickhouse-cloud-engineer.md"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

AUTH_ANSWER = (
    "I have worked with OAuth2 and OIDC-based authentication flows when building "
    "REST APIs in .NET (ASP.NET Core) and Python (Flask). I have integrated third-party "
    "identity providers and implemented JWT-based authorization with role-based access "
    "control. I am familiar with Auth0 as an identity platform and have used Azure Active "
    "Directory for enterprise authentication. I am eager to extend this experience to SAML, "
    "SCIM, and MFA/passwordless standards in a production cloud environment."
)

with open(COVER_LETTER_PATH) as f:
    COVER_LETTER_TEXT = f.read()

# ---- Step 1: Get the page and extract CSRF token ----
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": JOB_URL,
})

print("Loading job page...")
r = session.get(JOB_URL, timeout=20)
print(f"Page status: {r.status_code}")

# Look for any CSRF token (Greenhouse may not use one on the public form)
csrf_token = None
csrf_patterns = [
    r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"',
    r'<input[^>]+name="authenticity_token"[^>]+value="([^"]+)"',
    r'"csrf_token"\s*:\s*"([^"]+)"',
    r'"_token"\s*:\s*"([^"]+)"',
]
for pattern in csrf_patterns:
    m = re.search(pattern, r.text)
    if m:
        csrf_token = m.group(1)
        print(f"CSRF token found: {csrf_token[:20]}...")
        break

if not csrf_token:
    print("No CSRF token found — form may not require one (public Greenhouse forms often don't)")

# ---- Step 2: Check if the traditional POST endpoint works ----
# First try a HEAD to see what the submit URL returns
print(f"\nChecking submit URL: {SUBMIT_URL}")
r_check = session.get(SUBMIT_URL, timeout=20)
print(f"Submit URL status: {r_check.status_code}")
print(f"Content type: {r_check.headers.get('content-type', 'unknown')}")

# Extract any hidden fields from the form
hidden_fields = {}
for m in re.finditer(r'<input[^>]+type="hidden"[^>]+name="([^"]+)"[^>]+value="([^"]*)"', r_check.text):
    hidden_fields[m.group(1)] = m.group(2)
    print(f"Hidden field: {m.group(1)} = {m.group(2)[:50]}")

for m in re.finditer(r'<input[^>]+name="([^"]+)"[^>]+type="hidden"[^>]+value="([^"]*)"', r_check.text):
    hidden_fields[m.group(1)] = m.group(2)
    print(f"Hidden field (alt): {m.group(1)} = {m.group(2)[:50]}")

# ---- Step 3: Build the multipart form data ----
print("\nPreparing form submission...")

# Standard Greenhouse fields
form_data = {
    "utf8": "✓",
    "job_application[first_name]": "Hisham",
    "job_application[last_name]": "Abboud",
    "job_application[email]": "hiaham123@hotmail.com",
    "job_application[phone]": "+3106 4841 2838",
    # Custom questions
    "job_application[question_15422494004]": "https://linkedin.com/in/hisham-abboud",  # LinkedIn
    "job_application[question_15422495004]": "Eindhoven, Netherlands",  # Current location
    "job_application[question_15422496004]": "0",  # Visa sponsorship: No (value=0)
    "job_application[question_15422497004]": AUTH_ANSWER,  # Auth experience
    # Cover letter text
    "job_application[cover_letter_text]": COVER_LETTER_TEXT,
}

# Add any hidden fields (like CSRF)
if csrf_token:
    form_data["authenticity_token"] = csrf_token
for k, v in hidden_fields.items():
    if k not in form_data:
        form_data[k] = v

# ---- Step 4: Build files dict for resume ----
files = {}
if os.path.exists(RESUME_PDF):
    files["job_application[resume]"] = (
        "Hisham_Abboud_CV.pdf",
        open(RESUME_PDF, "rb"),
        "application/pdf"
    )
    print(f"Resume PDF ready: {RESUME_PDF}")
else:
    print(f"WARNING: Resume PDF not found at {RESUME_PDF}")

# ---- Step 5: Set headers for POST ----
headers = {
    "Referer": JOB_URL,
    "Origin": "https://job-boards.greenhouse.io",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

print("\nSubmitting application...")
print(f"POST to: {SUBMIT_URL}")
print("Form fields:")
for k, v in form_data.items():
    print(f"  {k}: {str(v)[:80]}")

try:
    response = session.post(
        SUBMIT_URL,
        data=form_data,
        files=files if files else None,
        headers=headers,
        timeout=30,
        allow_redirects=True,
    )
    print(f"\nResponse status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Content type: {response.headers.get('content-type', 'unknown')}")

    # Save response
    with open("/tmp/greenhouse-submit-response.html", "w") as f:
        f.write(response.text)
    print("Response saved to /tmp/greenhouse-submit-response.html")

    response_lower = response.text.lower()
    success_signals = [
        "thank you" in response_lower,
        "application received" in response_lower,
        "successfully" in response_lower,
        "we've received" in response_lower,
        "we have received" in response_lower,
        "confirmation" in response.url,
        "success" in response.url,
        "thank" in response.url,
    ]

    if any(success_signals):
        print("\nSUCCESS: Application submitted successfully!")
        status = "applied"
        notes = f"Application submitted via Greenhouse POST API. Response URL: {response.url}"
    elif response.status_code in [200, 201, 302]:
        # Check for errors in response
        error_patterns = [
            r'<div[^>]*class="[^"]*error[^"]*"[^>]*>([^<]{5,200})<',
            r'"error"\s*:\s*"([^"]+)"',
            r'alert-danger[^>]*>([^<]{5,200})<',
        ]
        errors = []
        for pattern in error_patterns:
            for m in re.finditer(pattern, response.text, re.IGNORECASE):
                err_text = m.group(1).strip()
                if err_text and len(err_text) > 3:
                    errors.append(err_text)

        if errors:
            print(f"\nForm errors detected: {errors[:3]}")
            status = "failed"
            notes = f"Form submission errors: {'; '.join(errors[:3])}"
        else:
            print(f"\nResponse {response.status_code} - no clear success/error signals")
            print("Response snippet:", response.text[:1000])
            status = "applied"
            notes = f"Submitted (status {response.status_code}), could not confirm from response. Manual verification needed."
    else:
        print(f"\nUnexpected status {response.status_code}")
        print("Response snippet:", response.text[:500])
        status = "failed"
        notes = f"Unexpected HTTP status {response.status_code}"

except requests.exceptions.RequestException as e:
    print(f"\nRequest failed: {e}")
    status = "failed"
    notes = f"Request exception: {e}"

# ---- Step 6: Close file handles ----
for v in files.values():
    if hasattr(v[1], "close"):
        v[1].close()

# ---- Step 7: Update applications.json ----
print(f"\nUpdating applications tracker...")
with open(APPLICATIONS_JSON) as f:
    apps = json.load(f)

apps = [a for a in apps if a.get("id") != "app-clickhouse-cloud-iam-001"]

entry = {
    "id": "app-clickhouse-cloud-iam-001",
    "company": "ClickHouse",
    "role": "Cloud Software Engineer - Identity and Access Management",
    "url": JOB_URL,
    "date_applied": str(date.today()),
    "score": 8.0,
    "status": status,
    "resume_file": RESUME_PDF,
    "cover_letter_file": COVER_LETTER_PATH,
    "screenshot": "",
    "all_screenshots": [],
    "notes": notes,
    "response": "",
}
apps.append(entry)

with open(APPLICATIONS_JSON, "w") as f:
    json.dump(apps, f, indent=2)

print("\n--- RESULT ---")
print(json.dumps(entry, indent=2))
