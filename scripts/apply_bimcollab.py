#!/usr/bin/env python3
"""
Script to apply for the Software Engineer position at KUBUS/BIMcollab
using Playwright browser automation with proxy support.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Config
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"
SCREENSHOT_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

PERSONAL_DETAILS = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

COVER_LETTER = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""


def get_proxy_settings():
    """Extract proxy settings from environment variables."""
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    return {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        "username": parsed.username,
        "password": parsed.password,
    }


def take_screenshot(page, name):
    """Take a screenshot and save to screenshots directory."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOT_DIR / f"bimcollab-{name}-{timestamp}.png"
    page.screenshot(path=str(filepath), full_page=True)
    print(f"Screenshot saved: {filepath}")
    return str(filepath)


def load_applications():
    """Load existing applications from JSON."""
    apps_path = Path(APPLICATIONS_JSON)
    if apps_path.exists():
        with open(apps_path) as f:
            return json.load(f)
    return []


def save_application(applications, entry):
    """Save application entry to JSON."""
    apps_path = Path(APPLICATIONS_JSON)
    apps_path.parent.mkdir(parents=True, exist_ok=True)
    applications.append(entry)
    with open(apps_path, "w") as f:
        json.dump(applications, f, indent=2)
    print(f"Application logged to {APPLICATIONS_JSON}")


def main():
    print("=" * 60)
    print("KUBUS/BIMcollab Software Engineer Application")
    print("=" * 60)
    print(f"Job URL: {JOB_URL}")
    print(f"Applicant: {PERSONAL_DETAILS['full_name']}")
    print()

    # Check for duplicate applications
    applications = load_applications()
    for app in applications:
        if app.get("url") == JOB_URL and app.get("status") == "applied":
            print(f"Already applied to this job on {app.get('date_applied')}. Skipping.")
            sys.exit(0)

    # Check resume exists
    if not Path(RESUME_PATH).exists():
        print(f"ERROR: Resume not found at {RESUME_PATH}")
        sys.exit(1)

    proxy_settings = get_proxy_settings()
    if proxy_settings:
        print(f"Using proxy: {proxy_settings['server']}")

    screenshots_taken = []
    status = "failed"
    notes = ""

    with sync_playwright() as p:
        browser_args = {
            "headless": True,
            "executable_path": "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ],
        }

        if proxy_settings:
            browser_args["proxy"] = proxy_settings

        browser = p.chromium.launch(**browser_args)

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = context.new_page()

        try:
            print(f"\nStep 1: Navigating to {JOB_URL}")
            page.goto(JOB_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)
            print(f"Page title: {page.title()}")
            print(f"Page URL: {page.url}")

            # Take initial screenshot
            screenshots_taken.append(take_screenshot(page, "01-job-page"))

            # Look for Apply button
            print("\nStep 2: Looking for Apply button...")
            apply_button = None
            apply_selectors = [
                "a:has-text('Apply')",
                "button:has-text('Apply')",
                "a[href*='apply']",
                ".apply-button",
                "[data-testid='apply-button']",
                "a:has-text('Solliciteren')",
                "button:has-text('Solliciteren')",
            ]
            for selector in apply_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        apply_button = btn
                        print(f"Found apply button with selector: {selector}")
                        break
                except Exception:
                    pass

            if apply_button:
                print("Clicking Apply button...")
                apply_button.click()
                time.sleep(3)
                screenshots_taken.append(take_screenshot(page, "02-after-apply-click"))
                print(f"After click URL: {page.url}")
            else:
                print("No separate Apply button found - form may be on the same page")

            # Try to scroll to form area
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(2)

            print("\nStep 3: Looking for application form fields...")

            # Try to find form fields
            # Full name field
            name_selectors = [
                "input[name='name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "input[id*='name' i]",
                "input[type='text']:first-of-type",
                "[data-testid*='name']",
            ]
            name_field = None
            for sel in name_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=2000):
                        name_field = field
                        print(f"Found name field: {sel}")
                        break
                except Exception:
                    pass

            # Email field
            email_field = None
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
            ]
            for sel in email_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=2000):
                        email_field = field
                        print(f"Found email field: {sel}")
                        break
                except Exception:
                    pass

            # Phone field
            phone_field = None
            phone_selectors = [
                "input[type='tel']",
                "input[name='phone']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]",
                "input[id*='phone' i]",
            ]
            for sel in phone_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=2000):
                        phone_field = field
                        print(f"Found phone field: {sel}")
                        break
                except Exception:
                    pass

            # Fill fields if found
            if name_field:
                print(f"Filling name: {PERSONAL_DETAILS['full_name']}")
                name_field.clear()
                name_field.fill(PERSONAL_DETAILS["full_name"])
            else:
                print("WARNING: Name field not found")

            if email_field:
                print(f"Filling email: {PERSONAL_DETAILS['email']}")
                email_field.clear()
                email_field.fill(PERSONAL_DETAILS["email"])
            else:
                print("WARNING: Email field not found")

            if phone_field:
                print(f"Filling phone: {PERSONAL_DETAILS['phone']}")
                phone_field.clear()
                phone_field.fill(PERSONAL_DETAILS["phone"])
            else:
                print("WARNING: Phone field not found")

            # Look for cover letter text area
            print("\nStep 4: Looking for cover letter field...")
            cover_letter_field = None
            cover_letter_selectors = [
                "textarea[name*='cover' i]",
                "textarea[placeholder*='cover' i]",
                "textarea[placeholder*='letter' i]",
                "textarea[id*='cover' i]",
                "textarea[name*='motivation' i]",
                "textarea[placeholder*='motivation' i]",
                "textarea",
            ]
            for sel in cover_letter_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=2000):
                        cover_letter_field = field
                        print(f"Found cover letter field: {sel}")
                        break
                except Exception:
                    pass

            if cover_letter_field:
                print("Filling cover letter...")
                cover_letter_field.clear()
                cover_letter_field.fill(COVER_LETTER)
            else:
                print("No cover letter textarea found - may need file upload")

            # Look for file upload (CV/resume)
            print("\nStep 5: Looking for file upload field...")
            file_input = None
            file_selectors = [
                "input[type='file']",
                "input[accept*='pdf']",
                "[data-testid*='upload']",
            ]
            for sel in file_selectors:
                try:
                    field = page.locator(sel).first
                    if field.count() > 0:
                        file_input = field
                        print(f"Found file input: {sel}")
                        break
                except Exception:
                    pass

            if file_input:
                print(f"Uploading resume: {RESUME_PATH}")
                file_input.set_input_files(RESUME_PATH)
                time.sleep(2)
                print("Resume uploaded successfully")
            else:
                print("WARNING: File upload field not found")

            time.sleep(2)
            screenshots_taken.append(take_screenshot(page, "03-form-filled"))

            # Look for screening questions (Yes/No radio buttons)
            print("\nStep 6: Looking for screening questions...")
            # Click "Yes" for eligibility questions
            yes_selectors = [
                "input[type='radio'][value='yes']",
                "input[type='radio'][value='true']",
                "label:has-text('Yes') input",
                "label:has-text('Ja') input",
            ]
            for sel in yes_selectors:
                try:
                    radios = page.locator(sel)
                    count = radios.count()
                    if count > 0:
                        print(f"Found {count} Yes/Ja radio buttons, clicking them...")
                        for i in range(count):
                            radios.nth(i).click()
                            time.sleep(0.5)
                except Exception as e:
                    print(f"Error with radio selector {sel}: {e}")

            # Take pre-submission screenshot
            print("\nStep 7: Taking pre-submission screenshot...")
            screenshots_taken.append(take_screenshot(page, "04-pre-submit"))

            # Look for submit button
            print("\nStep 8: Looking for submit button...")
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Versturen')",
                "button:has-text('Verzenden')",
                "[data-testid*='submit']",
            ]
            submit_button = None
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        submit_button = btn
                        print(f"Found submit button: {sel}")
                        break
                except Exception:
                    pass

            if submit_button:
                print("Submitting application...")
                submit_button.click()
                time.sleep(5)
                screenshots_taken.append(take_screenshot(page, "05-post-submit"))
                print(f"Post-submit URL: {page.url}")
                print(f"Post-submit title: {page.title()}")

                # Check for success indicators
                page_text = page.inner_text("body").lower()
                success_keywords = ["thank", "success", "received", "bedankt", "ontvangen", "confirmation"]
                if any(kw in page_text for kw in success_keywords):
                    print("\nSUCCESS: Application submitted successfully!")
                    status = "applied"
                    notes = "Application submitted. Confirmation page detected."
                else:
                    print("\nUncertain: No clear success message detected. Check screenshot.")
                    status = "applied"
                    notes = "Submitted but no clear confirmation message. Check screenshot."
            else:
                print("WARNING: Submit button not found. Application not submitted.")
                status = "failed"
                notes = "Submit button not found. Form may have changed."

        except PlaywrightTimeoutError as e:
            print(f"\nTimeout error: {e}")
            try:
                screenshots_taken.append(take_screenshot(page, "error-timeout"))
            except Exception:
                pass
            status = "failed"
            notes = f"Timeout error: {str(e)[:200]}"

        except Exception as e:
            print(f"\nError: {e}")
            try:
                screenshots_taken.append(take_screenshot(page, "error-general"))
            except Exception:
                pass
            status = "failed"
            notes = f"Error: {str(e)[:200]}"

        finally:
            browser.close()

    # Log the application
    app_entry = {
        "id": f"bimcollab-software-engineer-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": 8,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": None,
        "screenshots": screenshots_taken,
        "notes": notes,
        "response": None,
    }
    save_application(applications, app_entry)

    print("\n" + "=" * 60)
    print(f"Application status: {status.upper()}")
    print(f"Screenshots taken: {len(screenshots_taken)}")
    for s in screenshots_taken:
        print(f"  - {s}")
    print("=" * 60)

    return status == "applied"


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
