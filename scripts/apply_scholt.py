#!/usr/bin/env python3
"""
Automated job application script for Scholt Energy .NET Software Engineer position.
"""

import os
import sys
import re
import time
import json
from datetime import datetime

# Set the playwright browsers path to use existing installation
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/root/.cache/ms-playwright"

from playwright.sync_api import sync_playwright

# Configuration
APPLICATION_URL = "https://www.scholt.nl/en/apply/?page=3630"
JOB_URL = "https://www.scholt.nl/en/working-at/job-vacancy-overview/net-software-engineer/"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

# Personal details
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
    """Parse proxy settings from environment variables."""
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or \
                os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    if not proxy_url:
        return None

    match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if match:
        username, password, host, port = match.groups()
        server = f"http://{host}:{port}"
        print(f"Using proxy: {server}")
        return {
            "server": server,
            "username": username,
            "password": password,
        }
    return None


def ensure_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def take_screenshot(page, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOTS_DIR}/scholt-{name}-{timestamp}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"Screenshot saved: {filename}")
    return filename


def save_cover_letter():
    """Save cover letter as a text file that can be uploaded if needed."""
    cl_path = "/home/user/Agents/output/cover-letters/scholt-net-software-engineer.txt"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER_TEXT)
    return cl_path


def inspect_form(page):
    """Inspect the form to understand its structure."""
    print("\n--- Inspecting form structure ---")
    try:
        # Get all input fields
        inputs = page.locator("input").all()
        print(f"Found {len(inputs)} input elements")
        for i, inp in enumerate(inputs):
            try:
                inp_type = inp.get_attribute("type") or "text"
                inp_name = inp.get_attribute("name") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_placeholder = inp.get_attribute("placeholder") or ""
                print(f"  Input {i}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
            except Exception:
                pass

        # Get all textareas
        textareas = page.locator("textarea").all()
        print(f"Found {len(textareas)} textarea elements")
        for i, ta in enumerate(textareas):
            try:
                ta_name = ta.get_attribute("name") or ""
                ta_id = ta.get_attribute("id") or ""
                ta_placeholder = ta.get_attribute("placeholder") or ""
                print(f"  Textarea {i}: name={ta_name}, id={ta_id}, placeholder={ta_placeholder}")
            except Exception:
                pass

        # Get all selects
        selects = page.locator("select").all()
        print(f"Found {len(selects)} select elements")
        for i, sel in enumerate(selects):
            try:
                sel_name = sel.get_attribute("name") or ""
                sel_id = sel.get_attribute("id") or ""
                print(f"  Select {i}: name={sel_name}, id={sel_id}")
            except Exception:
                pass

        # Get all buttons
        buttons = page.locator("button").all()
        print(f"Found {len(buttons)} button elements")
        for i, btn in enumerate(buttons):
            try:
                btn_type = btn.get_attribute("type") or ""
                btn_text = btn.inner_text()
                print(f"  Button {i}: type={btn_type}, text={btn_text[:50]}")
            except Exception:
                pass

    except Exception as e:
        print(f"Error inspecting form: {e}")
    print("--- End form inspection ---\n")


def apply_to_job():
    ensure_dirs()
    cover_letter_path = save_cover_letter()
    proxy_config = get_proxy_config()

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
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors", "--ignore-ssl-errors"],
        }
        if proxy_config:
            launch_args["proxy"] = proxy_config

        browser = p.chromium.launch(**launch_args)

        context_args = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "ignore_https_errors": True
        }
        # Also pass proxy to context if available
        if proxy_config:
            context_args["proxy"] = proxy_config

        context = browser.new_context(**context_args)
        page = context.new_page()

        try:
            print(f"Navigating to application form: {APPLICATION_URL}")
            page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            print(f"Current URL: {page.url}")

            # Take screenshot of application form
            shot = take_screenshot(page, "01-application-form")
            results["screenshots"].append(shot)

            # Handle cookie consent if present
            try:
                cookie_selectors = [
                    'button:has-text("Accept all")',
                    'button:has-text("Accept")',
                    'button:has-text("OK")',
                    'button:has-text("Akkoord")',
                    'button:has-text("Agree")',
                    'button[id*="accept"]',
                    'button[class*="accept"]',
                ]
                for sel in cookie_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            print(f"Accepting cookies with: {sel}")
                            btn.click()
                            time.sleep(1)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Inspect form structure first
            inspect_form(page)

            print("Filling in the application form...")

            # Fill First Name - try multiple strategies
            filled_first_name = False
            for sel in ['input[name="firstname"]', 'input[name="first_name"]', 'input[name*="voornaam"]',
                        'input[id*="firstname"]', 'input[id*="first_name"]', 'input[placeholder*="First"]',
                        'input[placeholder*="Voornaam"]']:
                try:
                    field = page.locator(sel).first
                    if field.count() > 0 and field.is_visible(timeout=1000):
                        field.fill(PERSONAL_DETAILS["first_name"])
                        print(f"Filled first name: {sel}")
                        filled_first_name = True
                        break
                except Exception:
                    continue

            if not filled_first_name:
                # Try by label text
                try:
                    page.get_by_label("First name", exact=False).fill(PERSONAL_DETAILS["first_name"])
                    print("Filled first name via label 'First name'")
                    filled_first_name = True
                except Exception:
                    pass
            if not filled_first_name:
                try:
                    page.get_by_label("Voornaam", exact=False).fill(PERSONAL_DETAILS["first_name"])
                    print("Filled first name via label 'Voornaam'")
                    filled_first_name = True
                except Exception:
                    pass
            if not filled_first_name:
                # Try first visible text input
                try:
                    text_inputs = page.locator('input[type="text"]').all()
                    if text_inputs:
                        text_inputs[0].fill(PERSONAL_DETAILS["first_name"])
                        print("Filled first name as first text input")
                        filled_first_name = True
                except Exception:
                    pass

            # Fill Last Name
            filled_last_name = False
            for sel in ['input[name="lastname"]', 'input[name="last_name"]', 'input[name*="achternaam"]',
                        'input[id*="lastname"]', 'input[id*="last_name"]', 'input[placeholder*="Last"]',
                        'input[placeholder*="Achternaam"]']:
                try:
                    field = page.locator(sel).first
                    if field.count() > 0 and field.is_visible(timeout=1000):
                        field.fill(PERSONAL_DETAILS["last_name"])
                        print(f"Filled last name: {sel}")
                        filled_last_name = True
                        break
                except Exception:
                    continue

            if not filled_last_name:
                try:
                    page.get_by_label("Last name", exact=False).fill(PERSONAL_DETAILS["last_name"])
                    print("Filled last name via label 'Last name'")
                    filled_last_name = True
                except Exception:
                    pass
            if not filled_last_name:
                try:
                    page.get_by_label("Achternaam", exact=False).fill(PERSONAL_DETAILS["last_name"])
                    print("Filled last name via label 'Achternaam'")
                    filled_last_name = True
                except Exception:
                    pass
            if not filled_last_name:
                try:
                    text_inputs = page.locator('input[type="text"]').all()
                    if len(text_inputs) >= 2:
                        text_inputs[1].fill(PERSONAL_DETAILS["last_name"])
                        print("Filled last name as second text input")
                        filled_last_name = True
                except Exception:
                    pass

            # Fill Email
            filled_email = False
            try:
                field = page.locator('input[type="email"]').first
                if field.count() > 0 and field.is_visible(timeout=1000):
                    field.fill(PERSONAL_DETAILS["email"])
                    print("Filled email (type=email)")
                    filled_email = True
            except Exception:
                pass
            if not filled_email:
                for sel in ['input[name*="email"]', 'input[id*="email"]', 'input[placeholder*="email"]',
                            'input[placeholder*="Email"]']:
                    try:
                        field = page.locator(sel).first
                        if field.count() > 0 and field.is_visible(timeout=1000):
                            field.fill(PERSONAL_DETAILS["email"])
                            print(f"Filled email: {sel}")
                            filled_email = True
                            break
                    except Exception:
                        continue
            if not filled_email:
                try:
                    page.get_by_label("E-mail", exact=False).fill(PERSONAL_DETAILS["email"])
                    print("Filled email via label 'E-mail'")
                    filled_email = True
                except Exception:
                    pass

            # Fill Phone
            filled_phone = False
            try:
                field = page.locator('input[type="tel"]').first
                if field.count() > 0 and field.is_visible(timeout=1000):
                    field.fill(PERSONAL_DETAILS["phone"])
                    print("Filled phone (type=tel)")
                    filled_phone = True
            except Exception:
                pass
            if not filled_phone:
                for sel in ['input[name*="phone"]', 'input[name*="tel"]', 'input[id*="phone"]',
                            'input[placeholder*="phone"]', 'input[placeholder*="Phone"]',
                            'input[placeholder*="Telefoon"]']:
                    try:
                        field = page.locator(sel).first
                        if field.count() > 0 and field.is_visible(timeout=1000):
                            field.fill(PERSONAL_DETAILS["phone"])
                            print(f"Filled phone: {sel}")
                            filled_phone = True
                            break
                    except Exception:
                        continue
            if not filled_phone:
                try:
                    page.get_by_label("Phone", exact=False).fill(PERSONAL_DETAILS["phone"])
                    print("Filled phone via label 'Phone'")
                    filled_phone = True
                except Exception:
                    pass
            if not filled_phone:
                try:
                    page.get_by_label("Telefoonnummer", exact=False).fill(PERSONAL_DETAILS["phone"])
                    print("Filled phone via label 'Telefoonnummer'")
                    filled_phone = True
                except Exception:
                    pass

            # Upload CV (resume PDF)
            print("Uploading CV (resume PDF)...")
            uploaded_cv = False
            try:
                file_inputs = page.locator('input[type="file"]').all()
                print(f"Found {len(file_inputs)} file input(s)")
                if file_inputs:
                    file_inputs[0].set_input_files(RESUME_PATH)
                    print(f"Uploaded CV to first file input")
                    uploaded_cv = True
                    time.sleep(2)
            except Exception as e:
                print(f"Could not upload CV: {e}")

            # Upload motivation letter if there's a second file input
            print("Looking for motivation letter upload field...")
            try:
                file_inputs = page.locator('input[type="file"]').all()
                if len(file_inputs) > 1:
                    file_inputs[1].set_input_files(cover_letter_path)
                    print("Uploaded cover letter to second file input")
                    time.sleep(2)
                else:
                    print(f"Only {len(file_inputs)} file input(s) found, no separate motivation letter upload")
            except Exception as e:
                print(f"Could not upload motivation letter: {e}")

            # Handle "How did you find us" dropdown
            try:
                selects = page.locator("select").all()
                if selects:
                    for sel_elem in selects:
                        try:
                            if sel_elem.is_visible(timeout=1000):
                                options = sel_elem.locator("option").all()
                                if len(options) > 1:
                                    sel_elem.select_option(index=1)
                                    sel_name = sel_elem.get_attribute("name") or "unknown"
                                    print(f"Selected dropdown option for: {sel_name}")
                                    break
                        except Exception:
                            continue
            except Exception as e:
                print(f"Could not interact with dropdown: {e}")

            # Handle consent checkbox
            try:
                checkboxes = page.locator('input[type="checkbox"]').all()
                print(f"Found {len(checkboxes)} checkbox(es)")
                for cb in checkboxes:
                    try:
                        if cb.is_visible(timeout=1000):
                            if not cb.is_checked():
                                cb.check()
                                print(f"Checked checkbox")
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not check consent checkbox: {e}")

            time.sleep(2)

            # Take pre-submission screenshot
            shot = take_screenshot(page, "02-before-submit")
            results["screenshots"].append(shot)
            print(f"Pre-submission screenshot saved: {shot}")

            # Look for and click submit button
            print("Looking for submit button...")
            submitted = False
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send job application")',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Verstuur")',
                'button:has-text("Solliciteer")',
                'button:has-text("Verzenden")',
            ]

            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible(timeout=2000):
                        btn_text = btn.inner_text()
                        print(f"Found submit button: '{btn_text}' with selector: {sel}")
                        btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if submitted:
                print("Submit button clicked, waiting for response...")
                time.sleep(5)

                # Take post-submission screenshot
                shot = take_screenshot(page, "03-after-submit")
                results["screenshots"].append(shot)
                print(f"Post-submission screenshot saved: {shot}")

                # Check for success indicators
                page_content = page.content().lower()
                current_url = page.url
                print(f"Post-submission URL: {current_url}")

                success_indicators = [
                    "thank you", "bedankt", "application received", "sollicitatie ontvangen",
                    "success", "submitted", "ingediend", "verzonden", "we will contact",
                    "we'll contact", "nemen contact"
                ]
                error_indicators = [
                    "error", "fout", "invalid", "required", "verplicht", "please fill"
                ]

                success = any(indicator in page_content for indicator in success_indicators)
                has_error = any(indicator in page_content for indicator in error_indicators)

                if success:
                    results["status"] = "applied"
                    results["notes"] = "Application submitted successfully - confirmation message detected"
                    print("Application submitted successfully!")
                elif has_error:
                    results["status"] = "failed"
                    results["notes"] = "Form validation errors detected after submit"
                    print("Form has validation errors - check screenshot")
                else:
                    results["status"] = "applied"
                    results["notes"] = "Submit button clicked. No clear success/error message detected - check screenshots."
                    print("Submit clicked but outcome unclear - check screenshot")
            else:
                results["status"] = "failed"
                results["notes"] = "Could not find submit button"
                print("Could not find submit button - check screenshot")

        except Exception as e:
            results["status"] = "failed"
            results["notes"] = f"Error during application: {str(e)}"
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


def update_applications_log(results):
    """Update the applications.json tracker."""
    log_path = "/home/user/Agents/data/applications.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    try:
        with open(log_path, "r") as f:
            applications = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        applications = []

    # Generate ID
    new_id = len(applications) + 1
    results["id"] = new_id
    applications.append(results)

    with open(log_path, "w") as f:
        json.dump(applications, f, indent=2)

    print(f"Application logged to {log_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Scholt Energy - .NET Software Engineer Application")
    print("=" * 60)

    results = apply_to_job()

    print("\n" + "=" * 60)
    print("Application Result:")
    print(json.dumps(results, indent=2))

    update_applications_log(results)
    print("\nDone!")
