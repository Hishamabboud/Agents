#!/usr/bin/env python3
"""
Script to apply for the Software Engineer position at KUBUS/BIMcollab
using Playwright browser automation with proxy support.
Version 2: Handles the actual application form at /c/new
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
APPLICATION_URL = "https://jobs.bimcollab.com/o/software-engineer-3/c/new"
SCREENSHOT_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

PERSONAL_DETAILS = {
    "full_name": "Hisham Abboud",
    "email": "Hisham123@hotmail.com",
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
    filepath = SCREENSHOT_DIR / f"bimcollab-v2-{name}-{timestamp}.png"
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
    print("KUBUS/BIMcollab Software Engineer Application v2")
    print("=" * 60)
    print(f"Job URL: {JOB_URL}")
    print(f"Application URL: {APPLICATION_URL}")
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
            viewport={"width": 1280, "height": 1024},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = context.new_page()

        try:
            # Navigate directly to the application form
            print(f"\nStep 1: Navigating to application form...")
            page.goto(APPLICATION_URL, timeout=60000, wait_until="domcontentloaded")
            time.sleep(4)
            print(f"Page title: {page.title()}")
            print(f"Page URL: {page.url}")

            screenshots_taken.append(take_screenshot(page, "01-application-form-initial"))

            # Handle cookie consent dialog
            print("\nStep 2: Handling cookie consent...")
            cookie_selectors = [
                "button:has-text('Agree to all')",
                "button:has-text('Accept all')",
                "button:has-text('Accept')",
                "button:has-text('Agree to necessary')",
                "[data-testid='cookie-accept']",
                ".cookie-accept",
                "#cookie-accept",
            ]
            for sel in cookie_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        print(f"Clicking cookie consent: {sel}")
                        btn.click()
                        time.sleep(2)
                        break
                except Exception:
                    pass

            screenshots_taken.append(take_screenshot(page, "02-after-cookies"))

            # Fill in Full Name
            print("\nStep 3: Filling in personal details...")
            name_selectors = [
                "input[placeholder='Full name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "input[name='name']",
                "input[id*='name' i]",
                "input[type='text']",
            ]
            name_field = None
            for sel in name_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=3000):
                        name_field = field
                        print(f"Found name field: {sel}")
                        break
                except Exception:
                    pass

            if name_field:
                name_field.click()
                name_field.fill(PERSONAL_DETAILS["full_name"])
                print(f"Filled name: {PERSONAL_DETAILS['full_name']}")
            else:
                print("WARNING: Name field not found")

            # Fill Email
            email_selectors = [
                "input[type='email']",
                "input[placeholder*='email' i]",
                "input[name='email']",
                "input[id*='email' i]",
            ]
            email_field = None
            for sel in email_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=3000):
                        email_field = field
                        print(f"Found email field: {sel}")
                        break
                except Exception:
                    pass

            if email_field:
                email_field.click()
                email_field.fill(PERSONAL_DETAILS["email"])
                print(f"Filled email: {PERSONAL_DETAILS['email']}")
            else:
                print("WARNING: Email field not found")

            # Fill Phone - the form has a dropdown for country code + input for number
            phone_selectors = [
                "input[type='tel']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='Phone number' i]",
                "input[name='phone']",
                "input[id*='phone' i]",
            ]
            phone_field = None
            for sel in phone_selectors:
                try:
                    field = page.locator(sel).first
                    if field.is_visible(timeout=3000):
                        phone_field = field
                        print(f"Found phone field: {sel}")
                        break
                except Exception:
                    pass

            if phone_field:
                phone_field.click()
                # The phone field has a country code prefix (+31) so just enter the number part
                phone_field.fill("+31 06 4841 2838")
                print(f"Filled phone: +31 06 4841 2838")
            else:
                print("WARNING: Phone field not found")

            time.sleep(1)
            screenshots_taken.append(take_screenshot(page, "03-personal-details-filled"))

            # Upload CV/Resume
            print("\nStep 4: Uploading CV/Resume...")
            file_inputs = page.locator("input[type='file']")
            file_input_count = file_inputs.count()
            print(f"Found {file_input_count} file input(s)")

            if file_input_count > 0:
                # First file input is usually for CV
                file_inputs.nth(0).set_input_files(RESUME_PATH)
                time.sleep(3)
                print(f"Uploaded CV: {RESUME_PATH}")
            else:
                print("WARNING: No file input found")

            time.sleep(2)
            screenshots_taken.append(take_screenshot(page, "04-cv-uploaded"))

            # Handle cover letter - check if there's a "Write a cover letter" option
            print("\nStep 5: Adding cover letter...")
            write_cover_letter_link = None
            write_cl_selectors = [
                "a:has-text('Write a cover letter')",
                "button:has-text('Write a cover letter')",
                "a:has-text('write a cover letter')",
                "[href*='cover']",
                "span:has-text('Write a cover letter')",
            ]
            for sel in write_cl_selectors:
                try:
                    link = page.locator(sel).first
                    if link.is_visible(timeout=3000):
                        write_cover_letter_link = link
                        print(f"Found write cover letter option: {sel}")
                        break
                except Exception:
                    pass

            if write_cover_letter_link:
                write_cover_letter_link.click()
                time.sleep(2)
                # Now look for textarea
                cover_letter_field = None
                cl_selectors = ["textarea", "div[contenteditable='true']"]
                for sel in cl_selectors:
                    try:
                        field = page.locator(sel).first
                        if field.is_visible(timeout=3000):
                            cover_letter_field = field
                            print(f"Found cover letter textarea: {sel}")
                            break
                    except Exception:
                        pass

                if cover_letter_field:
                    cover_letter_field.fill(COVER_LETTER)
                    print("Filled cover letter text")
                else:
                    print("WARNING: Cover letter textarea not found after clicking link")
            else:
                # Try to find existing textarea
                cl_field = None
                try:
                    cl_field = page.locator("textarea").first
                    if cl_field.is_visible(timeout=2000):
                        cl_field.fill(COVER_LETTER)
                        print("Filled cover letter in existing textarea")
                except Exception:
                    print("No cover letter field found - will skip")

            time.sleep(2)
            screenshots_taken.append(take_screenshot(page, "05-cover-letter"))

            # Handle screening questions
            print("\nStep 6: Answering screening questions...")
            # "I am currently eligible to work and am residing in the Netherlands" -> Yes
            # "I am willing to work at KUBUS under an employment contract" -> Yes

            # Look for radio buttons with label "Yes"
            # Strategy: find labels that contain "Yes" and click the associated radio
            try:
                # Find all radio buttons and their parent labels
                all_radios = page.locator("input[type='radio']")
                radio_count = all_radios.count()
                print(f"Found {radio_count} radio buttons total")

                # Get page content to understand structure
                page_content = page.inner_html("body")

                # Try clicking "Yes" labels
                yes_labels = page.locator("label:has-text('Yes')")
                yes_count = yes_labels.count()
                print(f"Found {yes_count} 'Yes' labels")

                for i in range(yes_count):
                    try:
                        label = yes_labels.nth(i)
                        if label.is_visible(timeout=2000):
                            label.click()
                            print(f"Clicked Yes label {i+1}")
                            time.sleep(0.5)
                    except Exception as e:
                        print(f"  Could not click Yes label {i+1}: {e}")

                # Also try clicking radio buttons that have value='yes' via JavaScript
                page.evaluate("""
                    document.querySelectorAll('input[type="radio"]').forEach(radio => {
                        const label = document.querySelector(`label[for="${radio.id}"]`);
                        if (label && (label.textContent.trim() === 'Yes' || label.textContent.trim() === 'Ja')) {
                            radio.click();
                        }
                    });
                """)

            except Exception as e:
                print(f"Error handling radio buttons: {e}")

            time.sleep(2)
            screenshots_taken.append(take_screenshot(page, "06-screening-questions"))

            # Scroll to bottom and take pre-submit screenshot
            print("\nStep 7: Scrolling to submit button and taking pre-submit screenshot...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            screenshots_taken.append(take_screenshot(page, "07-pre-submit"))

            # Find and click submit button
            print("\nStep 8: Looking for submit button...")
            submit_selectors = [
                "button:has-text('Send')",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Versturen')",
                "button:has-text('Verzenden')",
            ]
            submit_button = None
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=3000):
                        submit_button = btn
                        btn_text = btn.inner_text()
                        print(f"Found submit button '{btn_text}' with selector: {sel}")
                        break
                except Exception:
                    pass

            if submit_button:
                print("Submitting application...")
                submit_button.click()
                time.sleep(6)
                print(f"Post-submit URL: {page.url}")
                print(f"Post-submit title: {page.title()}")
                screenshots_taken.append(take_screenshot(page, "08-post-submit"))

                # Check for success indicators
                page_text = page.inner_text("body").lower()
                print(f"\nPage text preview: {page_text[:300]}")

                success_keywords = ["thank", "success", "received", "bedankt", "ontvangen", "confirmation", "submitted", "we will"]
                error_keywords = ["error", "required", "invalid", "fout", "verplicht"]

                if any(kw in page_text for kw in success_keywords):
                    print("\nSUCCESS: Application submitted successfully!")
                    status = "applied"
                    notes = "Application submitted. Confirmation page detected."
                elif any(kw in page_text for kw in error_keywords):
                    print("\nFAILED: Form validation errors detected.")
                    status = "failed"
                    notes = "Form had validation errors. Check screenshot."
                else:
                    print("\nUncertain: No clear success/error message. Check screenshot.")
                    status = "applied"
                    notes = "Submitted - no clear confirmation text. Check screenshot for verification."
            else:
                print("WARNING: Submit button not found.")
                status = "failed"
                notes = "Submit button not found."

        except PlaywrightTimeoutError as e:
            print(f"\nTimeout error: {e}")
            try:
                screenshots_taken.append(take_screenshot(page, "error-timeout"))
            except Exception:
                pass
            status = "failed"
            notes = f"Timeout error: {str(e)[:200]}"

        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()
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
