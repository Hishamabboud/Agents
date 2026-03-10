import json
from datetime import date

APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

with open(APPLICATIONS_JSON) as f:
    apps = json.load(f)

apps = [a for a in apps if a.get("id") != "app-clickhouse-cloud-iam-001"]

entry = {
    "id": "app-clickhouse-cloud-iam-001",
    "company": "ClickHouse",
    "role": "Cloud Software Engineer - Identity and Access Management",
    "url": "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004",
    "date_applied": str(date.today()),
    "score": 8.0,
    "status": "skipped",
    "resume_file": "/home/user/Agents/profile/Hisham Abboud CV.pdf",
    "cover_letter_file": "/home/user/Agents/output/cover-letters/clickhouse-cloud-engineer.md",
    "screenshot": "",
    "all_screenshots": [],
    "notes": (
        "reCAPTCHA Enterprise blocks automated browser submission. "
        "Form data confirmed by Greenhouse (response included candidate email), "
        "but captcha token required. "
        "Candidate must manually complete application at: "
        "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004 — "
        "all materials prepared: tailored cover letter saved, resume PDF ready."
    ),
    "response": "",
}

apps.append(entry)

with open(APPLICATIONS_JSON, "w") as f:
    json.dump(apps, f, indent=2)

print("Updated application log.")
print(json.dumps(entry, indent=2))
