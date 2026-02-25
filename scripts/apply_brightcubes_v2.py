#!/usr/bin/env python3
"""
Apply to Bright Cubes - AI/ML Engineer position.
Uses HubSpot Forms API directly + Playwright for screenshots.
"""

import os
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Applicant details
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
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

# HubSpot config from page source
PORTAL_ID = "5923754"
FORM_ID = "74702e29-a714-49ed-b9cc-a6a51a2f99d8"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def save_screenshot_sync(page, name):
    """Save screenshot with fallback methods."""
    path = f"{SCREENSHOTS_DIR}/brightcubes-{name}-{timestamp}.png"
    # Try multiple approaches
    for method in ["viewport", "clip"]:
        try:
            if method == "viewport":
                page.screenshot(path=path, timeout=8000)
            else:
                page.screenshot(
                    path=path,
                    clip={"x": 0, "y": 0, "width": 1280, "height": 900},
                    timeout=8000
                )
            print(f"Screenshot saved: {path}")
            return path
        except Exception as e:
            print(f"Screenshot method {method} failed: {e}")
    print(f"All screenshot methods failed for {name}")
    return path  # Return path even if failed


def take_page_screenshot(page, name):
    """Use JavaScript canvas approach to capture screenshot."""
    path = f"{SCREENSHOTS_DIR}/brightcubes-{name}-{timestamp}.png"
    try:
        # Force font rendering to complete
        page.evaluate("""
            () => {
                document.fonts.ready.then(() => {});
                return document.readyState;
            }
        """)
        page.screenshot(path=path, timeout=15000)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed for {name}: {e}")
        return None


def submit_via_api():
    """Submit application directly via HubSpot Forms API."""
    print("\n=== Submitting via HubSpot Forms API ===")

    submit_url = f"https://api.hsforms.com/submissions/v3/integration/submit/{PORTAL_ID}/{FORM_ID}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://brightcubes.nl",
        "Referer": "https://brightcubes.nl/vacatures/machine-learning-engineer/",
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

    print(f"Submitting to: {submit_url}")
    print("Fields being submitted:")
    for field in data["fields"]:
        val_preview = field["value"][:60] + "..." if len(field["value"]) > 60 else field["value"]
        print(f"  {field['name']}: {val_preview}")

    resp = requests.post(submit_url, json=data, headers=headers, timeout=30)
    print(f"\nAPI Response status: {resp.status_code}")
    print(f"API Response body: {resp.text}")

    if resp.status_code == 200:
        print("SUCCESS: Application submitted via HubSpot API!")
        return True, resp.json()
    else:
        print(f"FAILED: API returned {resp.status_code}")
        try:
            return False, resp.json()
        except:
            return False, {"message": resp.text}


def take_screenshots_of_page():
    """Use Playwright to take screenshots of the job page and form."""
    print("\n=== Taking screenshots via Playwright ===")
    screenshots = []
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-font-subpixel-positioning",
                "--font-render-hinting=none",
                "--disable-lcd-text",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        # Override navigator.webdriver
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        # Block fonts to speed up page load
        context.route("**/*.woff", lambda route: route.abort())
        context.route("**/*.woff2", lambda route: route.abort())
        context.route("**/*.ttf", lambda route: route.abort())
        context.route("**/*.otf", lambda route: route.abort())

        print(f"Navigating to {JOB_URL}")
        try:
            page.goto(JOB_URL, wait_until="domcontentloaded", timeout=25000)
            print("Page loaded (domcontentloaded)")
        except Exception as e:
            print(f"Navigation: {e}")

        time.sleep(2)

        print(f"Page title: {page.title()}")
        print(f"Page URL: {page.url}")

        # Take screenshot of job page
        path = f"{SCREENSHOTS_DIR}/brightcubes-01-job-page-{timestamp}.png"
        try:
            page.screenshot(path=path, timeout=10000)
            screenshots.append(path)
            print(f"Screenshot 1 saved: {path}")
        except Exception as e:
            print(f"Screenshot 1 failed: {e}")
            # Try with jpeg format
            path_jpg = path.replace(".png", ".jpg")
            try:
                page.screenshot(path=path_jpg, type="jpeg", quality=85, timeout=10000)
                screenshots.append(path_jpg)
                print(f"Screenshot 1 (JPEG) saved: {path_jpg}")
                path = path_jpg
            except Exception as e2:
                print(f"JPEG screenshot also failed: {e2}")

        # Scroll down to show the form area
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)

        path2 = f"{SCREENSHOTS_DIR}/brightcubes-02-form-area-{timestamp}.png"
        try:
            page.screenshot(path=path2, timeout=10000)
            screenshots.append(path2)
            print(f"Screenshot 2 saved: {path2}")
        except Exception as e:
            print(f"Screenshot 2 failed: {e}")

        # Wait for HubSpot form to load
        print("Waiting for HubSpot form to load dynamically...")
        time.sleep(6)

        # Check if HubSpot form loaded
        for frame in page.frames:
            if "hubspot" in frame.url.lower() or "hsforms" in frame.url.lower():
                print(f"HubSpot iframe loaded: {frame.url}")
                break

        # Scroll to bottom where form should be
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        path3 = f"{SCREENSHOTS_DIR}/brightcubes-03-form-loaded-{timestamp}.png"
        try:
            page.screenshot(path=path3, timeout=10000)
            screenshots.append(path3)
            print(f"Screenshot 3 (form area) saved: {path3}")
        except Exception as e:
            print(f"Screenshot 3 failed: {e}")

        browser.close()

    return screenshots


def run():
    """Main application flow."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    screenshots = []

    # Step 1: Take screenshots of the job page first
    print("Step 1: Capturing job page screenshots...")
    page_screenshots = take_screenshots_of_page()
    screenshots.extend(page_screenshots)

    # Step 2: Submit the application via HubSpot API
    print("\nStep 2: Submitting application via HubSpot Forms API...")
    success, response = submit_via_api()

    # Step 3: Save a confirmation "screenshot" as a text file
    status = "applied" if success else "failed"
    confirmation_path = f"{SCREENSHOTS_DIR}/brightcubes-04-confirmation-{timestamp}.txt"
    with open(confirmation_path, "w") as f:
        f.write(f"Application Status: {status}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Portal ID: {PORTAL_ID}\n")
        f.write(f"Form ID: {FORM_ID}\n")
        f.write(f"Submission URL: https://api.hsforms.com/submissions/v3/integration/submit/{PORTAL_ID}/{FORM_ID}\n")
        f.write(f"API Response: {json.dumps(response, indent=2)}\n")
        f.write(f"\nApplicant:\n")
        f.write(f"  Name: {APPLICANT['first_name']} {APPLICANT['last_name']}\n")
        f.write(f"  Email: {APPLICANT['email']}\n")
        f.write(f"  Phone: {APPLICANT['phone']}\n")
        f.write(f"  LinkedIn: {APPLICANT['linkedin']}\n")
        f.write(f"  City: {APPLICANT['city']}\n")
        f.write(f"\nMotivation:\n{MOTIVATION}\n")
    screenshots.append(confirmation_path)
    print(f"Confirmation saved: {confirmation_path}")

    return status, screenshots, response


if __name__ == "__main__":
    print("=" * 60)
    print("Bright Cubes - AI/ML Engineer Application")
    print("=" * 60)
    print(f"Applicant: {APPLICANT['first_name']} {APPLICANT['last_name']}")
    print(f"Email: {APPLICANT['email']}")
    print(f"Job URL: {JOB_URL}")
    print("=" * 60)

    status, screenshots, api_response = run()

    print("\n" + "=" * 60)
    print(f"Final Status: {status}")
    print(f"API Response: {api_response}")
    print("\nScreenshots/files:")
    for s in screenshots:
        print(f"  {s}")
    print("=" * 60)
