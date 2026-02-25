#!/usr/bin/env python3
"""
Apply to Bright Cubes - AI/ML Engineer position.
Phase 1: Screenshot via Playwright (with aggressive font/resource blocking)
Phase 2: Submit via HubSpot Forms API directly
"""

import os
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# Applicant details
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
}

CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
JOB_URL = "https://brightcubes.nl/vacatures/machine-learning-engineer/"

MOTIVATION = (
    "I am excited to apply for the AI/ML Engineer position at Bright Cubes. "
    "I am currently building CogitatAI, an AI chatbot platform featuring sentiment analysis "
    "and NLP capabilities, demonstrating hands-on experience with ML in production. "
    "At ASML, I developed Python-based software solutions for high-tech systems, "
    "and I have extensive experience with Azure cloud infrastructure including "
    "CI/CD pipelines and cloud-native deployments. "
    "My BSc from Fontys University of Applied Sciences (ICT - Software Engineering) "
    "and my strong passion for AI/ML make me a great fit for this role. "
    "I am eager to join Bright Cubes and help clients derive real value from their data."
)

PORTAL_ID = "5923754"
FORM_ID = "74702e29-a714-49ed-b9cc-a6a51a2f99d8"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def take_screenshot_of_page():
    """Take a screenshot of the job page with all heavy resources blocked."""
    screenshots = []
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print("\n=== Taking page screenshots ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        )

        # Block all fonts, images, media, and heavy scripts to speed up loading
        blocked_types = {"font", "media"}
        blocked_domains = [
            "google-analytics.com", "analytics.google.com",
            "fonts.googleapis.com", "fonts.gstatic.com",
            "youtube.com", "ytimg.com",
            "doubleclick.net", "googletagmanager.com",
            "hotjar.com", "intercom.io",
        ]

        def route_handler(route):
            request = route.request
            resource_type = request.resource_type
            url = request.url

            if resource_type in blocked_types:
                route.abort()
                return

            for domain in blocked_domains:
                if domain in url:
                    route.abort()
                    return

            route.continue_()

        context.route("**/*", route_handler)

        page = context.new_page()

        print(f"Loading {JOB_URL}")
        try:
            # Use 'commit' to get the initial HTML without waiting for resources
            page.goto(JOB_URL, wait_until="commit", timeout=20000)
            print("Page committed")
        except Exception as e:
            print(f"Goto error: {e}")

        # Wait a bit for initial render
        time.sleep(3)

        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")

        # Try screenshot with a short timeout
        path1 = f"{SCREENSHOTS_DIR}/brightcubes-01-job-page-{timestamp}.png"
        try:
            page.screenshot(path=path1, timeout=8000)
            screenshots.append(path1)
            print(f"Screenshot 1 saved: {path1}")
        except Exception as e:
            print(f"Screenshot 1 failed: {e}")
            # Try with omit_background
            try:
                page.screenshot(path=path1, omit_background=True, timeout=8000)
                screenshots.append(path1)
                print(f"Screenshot 1 (no bg) saved: {path1}")
            except Exception as e2:
                print(f"Screenshot 1 (no bg) also failed: {e2}")

        # Scroll to the form area and take another screenshot
        try:
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(1)
        except Exception as e:
            print(f"Scroll failed: {e}")

        path2 = f"{SCREENSHOTS_DIR}/brightcubes-02-form-section-{timestamp}.png"
        try:
            page.screenshot(path=path2, timeout=8000)
            screenshots.append(path2)
            print(f"Screenshot 2 saved: {path2}")
        except Exception as e:
            print(f"Screenshot 2 failed: {e}")

        browser.close()

    return screenshots


def submit_application():
    """Submit application via HubSpot Forms API."""
    print("\n=== Submitting via HubSpot Forms API ===")

    submit_url = f"https://api.hsforms.com/submissions/v3/integration/submit/{PORTAL_ID}/{FORM_ID}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://brightcubes.nl",
        "Referer": JOB_URL,
    }

    data = {
        "fields": [
            {"objectTypeId": "0-1", "name": "firstname", "value": APPLICANT["first_name"]},
            {"objectTypeId": "0-1", "name": "lastname", "value": APPLICANT["last_name"]},
            {"objectTypeId": "0-1", "name": "email", "value": APPLICANT["email"]},
            {"objectTypeId": "0-1", "name": "phone", "value": APPLICANT["phone"]},
            {"objectTypeId": "0-1", "name": "linkedin", "value": APPLICANT["linkedin"]},
            {"objectTypeId": "0-1", "name": "message", "value": MOTIVATION},
        ],
        "context": {
            "pageUri": JOB_URL,
            "pageName": "Machine Learning Engineer - Bright Cubes",
        },
        "legalConsentOptions": {
            "consent": {
                "consentToProcess": True,
                "text": "I agree to allow Bright Cubes to store and process my personal data.",
            }
        },
    }

    print("Sending application with fields:")
    for field in data["fields"]:
        val_display = field["value"][:80] + "..." if len(field["value"]) > 80 else field["value"]
        print(f"  {field['name']}: {val_display}")

    try:
        resp = requests.post(submit_url, json=data, headers=headers, timeout=30)
        print(f"\nHTTP {resp.status_code}: {resp.text}")

        if resp.status_code == 200:
            print("SUCCESS: Application submitted!")
            return True, resp.json()
        else:
            print(f"FAILED: HTTP {resp.status_code}")
            try:
                return False, resp.json()
            except Exception:
                return False, {"raw": resp.text}

    except Exception as e:
        print(f"Request failed: {e}")
        return False, {"error": str(e)}


def save_confirmation(status, api_response, screenshots):
    """Save confirmation record."""
    path = f"{SCREENSHOTS_DIR}/brightcubes-03-confirmation-{timestamp}.txt"
    with open(path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("BRIGHT CUBES APPLICATION CONFIRMATION\n")
        f.write("=" * 60 + "\n")
        f.write(f"Status: {status.upper()}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Job URL: {JOB_URL}\n")
        f.write(f"HubSpot Portal ID: {PORTAL_ID}\n")
        f.write(f"HubSpot Form ID: {FORM_ID}\n")
        f.write(f"Submit URL: https://api.hsforms.com/submissions/v3/integration/submit/{PORTAL_ID}/{FORM_ID}\n")
        f.write(f"API Response: {json.dumps(api_response, indent=2)}\n")
        f.write("\nAPPLICANT DETAILS:\n")
        f.write(f"  Name: {APPLICANT['first_name']} {APPLICANT['last_name']}\n")
        f.write(f"  Email: {APPLICANT['email']}\n")
        f.write(f"  Phone: {APPLICANT['phone']}\n")
        f.write(f"  LinkedIn: {APPLICANT['linkedin']}\n")
        f.write(f"  City: {APPLICANT['city']}\n")
        f.write(f"  Country: {APPLICANT['country']}\n")
        f.write("\nMOTIVATION:\n")
        f.write(MOTIVATION + "\n")
        f.write("\nSCREENSHOTS:\n")
        for s in screenshots:
            f.write(f"  {s}\n")
    print(f"Confirmation saved: {path}")
    screenshots.append(path)
    return path


if __name__ == "__main__":
    print("=" * 60)
    print("BRIGHT CUBES - AI/ML Engineer Application")
    print(f"Applicant: {APPLICANT['first_name']} {APPLICANT['last_name']}")
    print(f"Email: {APPLICANT['email']}")
    print("=" * 60)

    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    all_screenshots = []

    # Phase 1: Take screenshots
    page_shots = take_screenshot_of_page()
    all_screenshots.extend(page_shots)

    # Phase 2: Submit application
    success, api_response = submit_application()
    status = "applied" if success else "failed"

    # Phase 3: Save confirmation
    save_confirmation(status, api_response, all_screenshots)

    print("\n" + "=" * 60)
    print(f"FINAL STATUS: {status.upper()}")
    print("=" * 60)
    print("Files saved:")
    for s in all_screenshots:
        print(f"  {s}")
