#!/usr/bin/env python3
"""
Automated job application script for Scholt Energy .NET Software Engineer position.
"""

import os
import sys
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
    "email": "Hisham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

COVER_LETTER_TEXT = """Dear Recruitment Team at Scholt Energy,

I am writing to express my interest in the .NET Software Engineer position at Scholt Energy. Your mission toward climate-neutral energy for all businesses is compelling, and I am eager to contribute to intelligent information systems that drive efficiency in the evolving energy market.

In my current role as Software Service Engineer at Actemium (VINCI Energies) in Eindhoven, I design and maintain full-stack applications using .NET, C#, ASP.NET, Python, and JavaScript. I build custom integrations, API connections, and database optimizations for industrial clients — experience that directly maps to your need for a developer who translates strategic objectives into smart information systems. I work daily with Azure, SQL, and integration monitoring in production environments.

Beyond technical skills, I bring multilingual capabilities — fluent in English, Dutch, Arabic, and Persian — valuable for your international team environment. My experience at ASML with Azure, Kubernetes, and CI/CD in agile settings, combined with founding CogitatAI, demonstrates both technical depth and initiative.

I am based in Eindhoven, hold a valid Dutch work permit, and am available for the hybrid arrangement you offer.

Best regards,
Hisham Abboud"""


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


def apply_to_job():
    ensure_dirs()
    cover_letter_path = save_cover_letter()

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
        browser = p.chromium.launch(
            headless=True,
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Navigating to job page: {JOB_URL}")
            page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Take screenshot of job page
            shot = take_screenshot(page, "01-job-page")
            results["screenshots"].append(shot)

            # Look for apply button and click it
            print("Looking for Apply button...")
            apply_selectors = [
                'a[href*="/apply/"]',
                'a:has-text("Apply directly")',
                'a:has-text("Apply")',
                'button:has-text("Apply")',
            ]

            clicked = False
            for selector in apply_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        print(f"Found apply button with selector: {selector}")
                        elem.click()
                        clicked = True
                        break
                except Exception as e:
                    continue

            if not clicked:
                print("Could not find apply button, navigating directly to application URL")
                page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)

            time.sleep(3)
            print(f"Current URL: {page.url}")

            # Take screenshot of application form
            shot = take_screenshot(page, "02-application-form")
            results["screenshots"].append(shot)

            # Handle cookie consent if present
            try:
                cookie_btn = page.locator('button:has-text("Accept"), button:has-text("OK"), button:has-text("Akkoord"), button:has-text("Agree")').first
                if cookie_btn.is_visible(timeout=3000):
                    print("Accepting cookie consent...")
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                pass

            print("Filling in the application form...")

            # Fill First Name
            try:
                first_name_selectors = [
                    'input[name*="first"], input[name*="voornaam"], input[placeholder*="First"], input[id*="first"]',
                    'input[type="text"]:nth-of-type(1)',
                    'input[name="firstname"]',
                    'input[name="first_name"]',
                ]
                for sel in first_name_selectors:
                    try:
                        field = page.locator(sel).first
                        if field.is_visible(timeout=2000):
                            field.fill(PERSONAL_DETAILS["first_name"])
                            print(f"Filled first name with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not fill first name: {e}")

            # Fill Last Name
            try:
                last_name_selectors = [
                    'input[name*="last"], input[name*="achternaam"], input[placeholder*="Last"], input[id*="last"]',
                    'input[name="lastname"]',
                    'input[name="last_name"]',
                ]
                for sel in last_name_selectors:
                    try:
                        field = page.locator(sel).first
                        if field.is_visible(timeout=2000):
                            field.fill(PERSONAL_DETAILS["last_name"])
                            print(f"Filled last name with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not fill last name: {e}")

            # Fill Email
            try:
                email_selectors = [
                    'input[type="email"]',
                    'input[name*="email"], input[id*="email"], input[placeholder*="email"]',
                ]
                for sel in email_selectors:
                    try:
                        field = page.locator(sel).first
                        if field.is_visible(timeout=2000):
                            field.fill(PERSONAL_DETAILS["email"])
                            print(f"Filled email with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not fill email: {e}")

            # Fill Phone
            try:
                phone_selectors = [
                    'input[type="tel"]',
                    'input[name*="phone"], input[name*="tel"], input[id*="phone"], input[placeholder*="phone"]',
                ]
                for sel in phone_selectors:
                    try:
                        field = page.locator(sel).first
                        if field.is_visible(timeout=2000):
                            field.fill(PERSONAL_DETAILS["phone"])
                            print(f"Filled phone with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not fill phone: {e}")

            # Upload CV
            print("Uploading CV...")
            try:
                cv_selectors = [
                    'input[type="file"][name*="cv"], input[type="file"][name*="CV"]',
                    'input[type="file"][id*="cv"]',
                    'input[type="file"]',
                ]
                for sel in cv_selectors:
                    try:
                        file_input = page.locator(sel).first
                        if file_input.count() > 0:
                            file_input.set_input_files(RESUME_PATH)
                            print(f"Uploaded CV with selector: {sel}")
                            time.sleep(2)
                            break
                    except Exception as e:
                        print(f"  CV upload attempt failed for {sel}: {e}")
                        continue
            except Exception as e:
                print(f"Could not upload CV: {e}")

            # Upload motivation letter as file (second file input)
            print("Looking for motivation letter upload field...")
            try:
                # Save cover letter as PDF-like text file for upload
                all_file_inputs = page.locator('input[type="file"]').all()
                print(f"Found {len(all_file_inputs)} file input(s)")

                if len(all_file_inputs) > 1:
                    # Second file input is for motivation letter
                    all_file_inputs[1].set_input_files(cover_letter_path)
                    print("Uploaded cover letter to second file input")
                    time.sleep(2)
            except Exception as e:
                print(f"Could not upload motivation letter: {e}")

            # Look for textarea to paste cover letter
            try:
                textarea_selectors = [
                    'textarea[name*="motivation"], textarea[name*="letter"], textarea[id*="motivation"]',
                    'textarea[placeholder*="motivation"], textarea[placeholder*="letter"]',
                    'textarea',
                ]
                for sel in textarea_selectors:
                    try:
                        textarea = page.locator(sel).first
                        if textarea.is_visible(timeout=2000):
                            textarea.fill(COVER_LETTER_TEXT)
                            print(f"Filled cover letter textarea with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"No textarea for motivation letter: {e}")

            # Handle "How did you find us" dropdown
            try:
                dropdown_selectors = [
                    'select[name*="source"], select[name*="how"], select[id*="source"]',
                    'select',
                ]
                for sel in dropdown_selectors:
                    try:
                        dropdown = page.locator(sel).first
                        if dropdown.is_visible(timeout=2000):
                            # Try to select "Website" or first option
                            dropdown.select_option(index=1)
                            print(f"Selected dropdown option with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not interact with dropdown: {e}")

            # Handle consent checkbox
            try:
                consent_selectors = [
                    'input[type="checkbox"][name*="consent"], input[type="checkbox"][name*="privacy"]',
                    'input[type="checkbox"][id*="consent"], input[type="checkbox"][id*="privacy"]',
                    'input[type="checkbox"]',
                ]
                for sel in consent_selectors:
                    try:
                        checkbox = page.locator(sel).first
                        if checkbox.is_visible(timeout=2000):
                            if not checkbox.is_checked():
                                checkbox.check()
                                print(f"Checked consent checkbox with selector: {sel}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Could not check consent checkbox: {e}")

            time.sleep(2)

            # Take pre-submission screenshot
            shot = take_screenshot(page, "03-before-submit")
            results["screenshots"].append(shot)
            print(f"Pre-submission screenshot saved: {shot}")

            # Look for and click submit button
            print("Looking for submit button...")
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send job application")',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Verstuur")',
            ]

            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        print(f"Found submit button with selector: {sel}")
                        btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if submitted:
                print("Submit button clicked, waiting for response...")
                time.sleep(5)

                # Take post-submission screenshot
                shot = take_screenshot(page, "04-after-submit")
                results["screenshots"].append(shot)
                print(f"Post-submission screenshot saved: {shot}")

                # Check for success indicators
                page_content = page.content().lower()
                current_url = page.url
                print(f"Post-submission URL: {current_url}")

                success_indicators = [
                    "thank you", "bedankt", "application received", "sollicitatie ontvangen",
                    "success", "submitted", "ingediend", "verzonden"
                ]
                error_indicators = [
                    "error", "fout", "invalid", "required", "verplicht"
                ]

                success = any(indicator in page_content for indicator in success_indicators)
                has_error = any(indicator in page_content for indicator in error_indicators)

                if success:
                    results["status"] = "applied"
                    results["notes"] = "Application submitted successfully"
                    print("Application submitted successfully!")
                elif has_error:
                    results["status"] = "failed"
                    results["notes"] = "Form validation errors detected"
                    print("Form has validation errors")
                else:
                    results["status"] = "applied"
                    results["notes"] = "Submit button clicked, no clear success/error message detected"
                    print("Submit clicked but result unclear")
            else:
                results["status"] = "failed"
                results["notes"] = "Could not find submit button"
                print("Could not find submit button")

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
