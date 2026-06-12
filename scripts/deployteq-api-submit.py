#!/usr/bin/env python3
"""
Submit application to DeployTeq via Workable API.
"""

import requests
import json
import os

JOB_SHORTCODE = "5246F389F7"
ACCOUNT_SUBDOMAIN = "deployteq"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"

HEADERS = {
    "Origin": "https://apply.workable.com",
    "Referer": f"https://apply.workable.com/{ACCOUNT_SUBDOMAIN}/j/{JOB_SHORTCODE}/apply/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
}

def upload_resume():
    """Upload resume to S3 and return the key."""
    print("Getting resume upload URL...")
    resp = requests.get(
        f"https://apply.workable.com/api/v1/jobs/{JOB_SHORTCODE}/form/upload/resume",
        params={"contentType": "application/pdf"},
        headers=HEADERS
    )
    print(f"Upload URL status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text[:200]}")
        return None

    data = resp.json()
    post_url = data["uploadPostUrl"]["url"]
    fields = data["uploadPostUrl"]["fields"]
    file_key = fields.get("key", data.get("key", ""))

    print(f"Uploading resume to S3...")
    with open(RESUME_PATH, 'rb') as f:
        file_content = f.read()

    # S3 presigned POST - need to include Content-Type matching the policy
    # Add Content-Type to the form fields (required for s3 POST policy)
    form_data = dict(fields)
    # The S3 policy has a content-type condition - need to match
    # From the error: ["starts-with", "$Content-Type", ""] - content-type can be anything
    upload_headers = {
        "Origin": "https://apply.workable.com",
        "Referer": "https://apply.workable.com/"
    }

    files = {
        **{k: (None, v) for k, v in form_data.items()},
        "Content-Type": (None, "application/pdf"),
        "file": ("Hisham Abboud CV.pdf", file_content, "application/pdf")
    }

    s3_resp = requests.post(post_url, files=files, headers=upload_headers)
    print(f"S3 upload status: {s3_resp.status_code}")
    if s3_resp.status_code not in [200, 201, 204]:
        print(f"S3 error: {s3_resp.text[:300]}")
        # Try alternative approach
        print("Trying alternative S3 upload...")
        form_data_alt = dict(fields)
        form_data_alt["Content-Type"] = "application/pdf"
        files_alt = {"file": ("Hisham Abboud CV.pdf", file_content, "application/pdf")}
        s3_resp2 = requests.post(post_url, data=form_data_alt, files=files_alt)
        print(f"Alt S3 status: {s3_resp2.status_code}")
        if s3_resp2.status_code not in [200, 201, 204]:
            print(f"Alt S3 error: {s3_resp2.text[:300]}")
            return None
        print("Alt S3 upload succeeded!")

    print(f"Resume uploaded. Key: {file_key}")
    return file_key


def discover_submit_endpoint():
    """Find the correct API endpoint for submitting."""
    endpoints = [
        f"https://apply.workable.com/api/v1/accounts/{ACCOUNT_SUBDOMAIN}/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/api/v2/accounts/{ACCOUNT_SUBDOMAIN}/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/api/v1/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/api/v3/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/{ACCOUNT_SUBDOMAIN}/j/{JOB_SHORTCODE}/apply/",
    ]
    print("\nDiscovering submit endpoint...")
    for url in endpoints:
        # Try OPTIONS first
        resp = requests.options(url, headers=HEADERS)
        print(f"OPTIONS {url}: {resp.status_code}")

    return None


def submit_application(resume_key=None):
    """Submit the full application."""
    print("\nSubmitting application...")

    cover_letter = """Dear DeployTeq Hiring Team,

I am writing to apply for the Software Developer position at DeployTeq in Zeist.

As a Software Engineer at Actemium (VINCI Energies), I build and maintain full-stack applications using .NET/C#, ASP.NET, Python/Flask, and JavaScript. DeployTeq's focus on online marketing technology is an exciting domain where I can apply my backend and frontend development skills.

My technical experience includes:
- Backend: C#, .NET Core, ASP.NET MVC, Python, Flask, SQL Server, REST APIs
- Frontend: JavaScript, TypeScript, HTML5, CSS3, React
- DevOps: Git, Azure DevOps, CI/CD, Docker
- Testing: Unit testing, Pytest, Locust performance testing

At ASML, I built performance testing infrastructure on Azure Kubernetes Service. At Delta Electronics, I migrated legacy C++ systems to C#/.NET. I hold a BSc in Software Engineering from Fontys University of Applied Sciences.

I am eager to contribute to DeployTeq's platform development and grow within your team.

Kind regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
Eindhoven, Netherlands"""

    payload = {
        "firstname": "Hisham",
        "lastname": "Abboud",
        "email": "hiaham123@hotmail.com",
        "phone": "+31064841 2838",
        "address": "Eindhoven, Netherlands",
        "headline": "",
        "summary": "",
        "cover_letter": cover_letter,
        "education_entries": [],
        "experience_entries": [],
        "social_profiles": [],
        "answers": [
            {"id": "CA_21813", "body": "1 month"},
            {"id": "CA_21815", "body": "65000"},
            {"id": "CA_21816", "body": True},
            {"id": "QA_11807072", "body": "Yes, I currently reside in Eindhoven, Netherlands."},
            {"id": "QA_11807073", "body": "Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport."}
        ],
        "gdpr_consent": {"gdpr": True}
    }

    if resume_key:
        payload["resume"] = resume_key

    post_headers = {**HEADERS, "Content-Type": "application/json"}

    # Try multiple endpoints
    endpoints_to_try = [
        f"https://apply.workable.com/api/v1/accounts/{ACCOUNT_SUBDOMAIN}/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/api/v1/jobs/{JOB_SHORTCODE}/candidates",
        f"https://apply.workable.com/api/v3/accounts/{ACCOUNT_SUBDOMAIN}/jobs/{JOB_SHORTCODE}/candidates",
    ]

    for url in endpoints_to_try:
        print(f"Trying: POST {url}")
        resp = requests.post(url, json=payload, headers=post_headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:300]}")
        if resp.status_code in [200, 201]:
            return resp
        print()

    return resp


if __name__ == "__main__":
    # First discover endpoints
    discover_submit_endpoint()

    # Upload resume
    resume_key = upload_resume()
    print(f"Resume key: {resume_key}")

    # Submit
    result = submit_application(resume_key)
    if result.status_code in [200, 201]:
        print("\nSUCCESS!")
    else:
        print(f"\nFailed with {result.status_code}: {result.text[:300]}")
