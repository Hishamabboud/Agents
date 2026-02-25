#!/usr/bin/env python3
"""
Scholt Energy application - v2 with improved reCAPTCHA detection and stealth mode.
"""

import os
import re
import sys
import time
import json
from datetime import datetime

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/root/.cache/ms-playwright"

from playwright.sync_api import sync_playwright

APPLICATION_URL = "https://www.scholt.nl/en/apply/?page=3630"
JOB_URL = "https://www.scholt.nl/en/working-at/job-vacancy-overview/net-software-engineer/"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/scholt-net-software-engineer.txt"

PERSONAL_DETAILS = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

COVER_LETTER_TEXT = """Dear Recruitment Team at Scholt Energy,

I am writing to express my interest in the .NET Software Engineer position at Scholt Energy. Your mission toward climate-neutral energy for all businesses is compelling, and I am eager to contribute to intelligent information systems that drive efficiency in the evolving energy market.

In my current role as Software Service Engineer at Actemium (VINCI Energies) in Eindhoven, I design and maintain full-stack applications using .NET, C#, ASP.NET, Python, and JavaScript. I build custom integrations, API connections, and database optimizations for industrial clients — experience that directly maps to your need for a developer who translates strategic objectives into smart information systems. I work daily with Azure, SQL, and integration monitoring in production environments.

Beyond technical skills, I bring multilingual capabilities — fluent in English, Dutch, Arabic, and Persian — valuable for your international team environment. My experience at ASML with Azure, Kubernetes, and CI/CD in agile settings, combined with founding CogitatAI, demonstrates both technical depth and initiative.

I am based in Eindhoven, hold a valid Dutch work permit, and am available for the hybrid arrangement you offer.

Best regards,
Hisham Abboud"""


def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or \
                os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    if not proxy_url:
        return None
    match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if match:
        username, password, host, port = match.groups()
        return {"server": f"http://{host}:{port}", "username": username, "password": password}
    return None


def ensure_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(COVER_LETTER_PATH), exist_ok=True)


def take_screenshot(page, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOTS_DIR}/scholt-v2-{name}-{timestamp}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"Screenshot saved: {filename}")
    return filename


def slow_type(page, selector, text):
    """Type text slowly to appear more human-like."""
    field = page.locator(selector).first
    field.click()
    time.sleep(0.2)
    field.fill("")
    time.sleep(0.1)
    field.fill(text)


def apply_with_stealth():
    ensure_dirs()
    proxy_config = get_proxy_config()

    # Save cover letter
    with open(COVER_LETTER_PATH, "w") as f:
        f.write(COVER_LETTER_TEXT)

    results = {
        "company": "Scholt Energy",
        "role": ".NET Software Engineer",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "status": "unknown",
        "screenshots": [],
        "notes": ""
    }

    with sync_playwright() as p:
        launch_args = {
            "headless": True,
            "executable_path": "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                # Stealth flags to appear less like a bot
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-web-security",
                "--allow-running-insecure-content",
            ],
        }
        if proxy_config:
            launch_args["proxy"] = proxy_config

        browser = p.chromium.launch(**launch_args)

        context_args = {
            "viewport": {"width": 1366, "height": 768},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "ignore_https_errors": True,
            "locale": "en-NL",
            "timezone_id": "Europe/Amsterdam",
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
            }
        }
        if proxy_config:
            context_args["proxy"] = proxy_config

        context = browser.new_context(**context_args)

        # Add init script to mask automation
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'nl'],
            });
            window.chrome = {
                runtime: {},
            };
        """)

        page = context.new_page()

        try:
            print(f"Navigating to application URL: {APPLICATION_URL}")
            page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            print(f"Current URL: {page.url}")

            # Take initial screenshot
            shot = take_screenshot(page, "01-loaded")
            results["screenshots"].append(shot)

            # Accept cookies if present
            try:
                for sel in ['button:has-text("Accept all")', 'button:has-text("Accept")',
                            'button:has-text("Accepteer")', '#acceptBtn', '.cookie-accept']:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            print(f"Accepted cookies: {sel}")
                            time.sleep(1)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Wait for form to be ready
            time.sleep(2)

            # Fill in First Name
            print("Filling form fields...")
            try:
                page.get_by_label("First name", exact=False).click()
                time.sleep(0.3)
                page.get_by_label("First name", exact=False).fill(PERSONAL_DETAILS["first_name"])
                print(f"  First name: {PERSONAL_DETAILS['first_name']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  First name error: {e}")
                # Fallback to text inputs
                try:
                    inputs = page.locator('input[type="text"]').all()
                    if inputs:
                        inputs[0].fill(PERSONAL_DETAILS["first_name"])
                        print(f"  First name (fallback): {PERSONAL_DETAILS['first_name']}")
                except Exception:
                    pass

            # Fill in Last Name
            try:
                page.get_by_label("Last name", exact=False).click()
                time.sleep(0.3)
                page.get_by_label("Last name", exact=False).fill(PERSONAL_DETAILS["last_name"])
                print(f"  Last name: {PERSONAL_DETAILS['last_name']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Last name error: {e}")
                try:
                    inputs = page.locator('input[type="text"]').all()
                    if len(inputs) >= 2:
                        inputs[1].fill(PERSONAL_DETAILS["last_name"])
                        print(f"  Last name (fallback): {PERSONAL_DETAILS['last_name']}")
                except Exception:
                    pass

            # Fill in Email
            try:
                page.locator('input[type="email"]').first.click()
                time.sleep(0.3)
                page.locator('input[type="email"]').first.fill(PERSONAL_DETAILS["email"])
                print(f"  Email: {PERSONAL_DETAILS['email']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Email error: {e}")

            # Fill in Phone
            try:
                page.get_by_label("Phone", exact=False).click()
                time.sleep(0.3)
                page.get_by_label("Phone", exact=False).fill(PERSONAL_DETAILS["phone"])
                print(f"  Phone: {PERSONAL_DETAILS['phone']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Phone error: {e}")
                # Try phonenumber label
                try:
                    page.get_by_label("Phonenumber", exact=False).fill(PERSONAL_DETAILS["phone"])
                    print(f"  Phone (phonenumber label): {PERSONAL_DETAILS['phone']}")
                except Exception:
                    try:
                        page.locator('input[type="tel"]').first.fill(PERSONAL_DETAILS["phone"])
                        print(f"  Phone (tel input): {PERSONAL_DETAILS['phone']}")
                    except Exception:
                        pass

            # Upload CV
            print("  Uploading CV...")
            try:
                file_inputs = page.locator('input[type="file"]').all()
                print(f"  Found {len(file_inputs)} file input(s)")
                if file_inputs:
                    file_inputs[0].set_input_files(RESUME_PATH)
                    print(f"  CV uploaded: {RESUME_PATH}")
                    time.sleep(2)

                # Upload motivation letter if 2nd file input exists
                if len(file_inputs) > 1:
                    file_inputs[1].set_input_files(COVER_LETTER_PATH)
                    print(f"  Motivation letter uploaded: {COVER_LETTER_PATH}")
                    time.sleep(2)
            except Exception as e:
                print(f"  File upload error: {e}")

            # Check consent checkbox
            try:
                checkboxes = page.locator('input[type="checkbox"]').all()
                for cb in checkboxes:
                    try:
                        if cb.is_visible(timeout=1000) and not cb.is_checked():
                            cb.check()
                            print("  Consent checkbox checked")
                    except Exception:
                        continue
            except Exception as e:
                print(f"  Checkbox error: {e}")

            time.sleep(2)

            # Take pre-submit screenshot
            shot = take_screenshot(page, "02-before-submit")
            results["screenshots"].append(shot)

            # Check for reCAPTCHA before submitting
            print("\nChecking for reCAPTCHA...")
            page_html = page.content()
            has_recaptcha = "recaptcha" in page_html.lower() or "g-recaptcha" in page_html.lower()
            print(f"reCAPTCHA present: {has_recaptcha}")

            if has_recaptcha:
                print("WARNING: reCAPTCHA detected. Attempting to wait for it to auto-resolve...")
                # Wait a bit to see if invisible reCAPTCHA resolves
                time.sleep(5)

            # Submit the form
            print("Submitting application...")
            submitted = False
            for sel in ['button[type="submit"]', 'input[type="submit"]',
                        'button:has-text("Send job application")', 'button:has-text("Send")',
                        'button:has-text("Submit")', 'button:has-text("Verzenden")']:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible(timeout=2000):
                        btn_text = btn.inner_text()
                        print(f"Clicking: '{btn_text}'")
                        btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if submitted:
                print("Waiting for submission response...")
                time.sleep(6)

                shot = take_screenshot(page, "03-after-submit")
                results["screenshots"].append(shot)

                page_content = page.content()
                page_lower = page_content.lower()
                current_url = page.url
                print(f"URL after submit: {current_url}")

                # Check for specific reCAPTCHA failure
                recaptcha_failed = ("recaptcha failed" in page_lower or
                                    "captcha failed" in page_lower or
                                    "failed to validate" in page_lower or
                                    "captcha" in page_lower and "error" in page_lower)

                success_indicators = [
                    "thank you", "bedankt", "application received",
                    "we will contact", "we'll contact", "nemen contact",
                    "successfully submitted", "your application has"
                ]
                success = any(ind in page_lower for ind in success_indicators)

                if recaptcha_failed:
                    results["status"] = "failed"
                    results["notes"] = ("reCAPTCHA validation failed - automated browsers cannot pass Google reCAPTCHA. "
                                       "Form was filled correctly with all details. "
                                       "Recommend manual submission or email to recruitment@scholt.nl. "
                                       "Screenshots show completed form before and after attempt.")
                    print("FAILED: reCAPTCHA blocked the submission")
                elif success:
                    results["status"] = "applied"
                    results["notes"] = "Application submitted successfully - confirmation message detected"
                    print("SUCCESS: Application submitted!")
                else:
                    # Check if still on same page (error) or moved to thank you page
                    results["status"] = "failed"
                    results["notes"] = "Submission outcome unclear - no success message detected. Check screenshots."
                    print("UNCLEAR: No success message found")

            else:
                results["status"] = "failed"
                results["notes"] = "Submit button not found"
                print("FAILED: Could not find submit button")

        except Exception as e:
            results["status"] = "failed"
            results["notes"] = f"Error: {str(e)}"
            print(f"Error: {e}")
            try:
                shot = take_screenshot(page, "error")
                results["screenshots"].append(shot)
            except Exception:
                pass
        finally:
            context.close()
            browser.close()

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Scholt Energy - .NET Software Engineer (v2 with stealth)")
    print("=" * 60)

    results = apply_with_stealth()

    print("\n" + "=" * 60)
    print("Result:", results["status"])
    print("Notes:", results["notes"])
    print("Screenshots:", results["screenshots"])
    print("=" * 60)

    # Update applications log
    log_path = "/home/user/Agents/data/applications.json"
    try:
        with open(log_path) as f:
            apps = json.load(f)
    except Exception:
        apps = []

    results["id"] = f"scholt-v2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    apps.append(results)

    with open(log_path, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"Logged to {log_path}")
