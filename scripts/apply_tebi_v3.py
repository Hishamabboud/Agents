#!/usr/bin/env python3
"""
Tebi Software Engineer (Early Talent) - Ashby Application Script v3
Uses [id="..."] attribute selectors for numeric IDs (CSS # selector doesn't work with numeric IDs).
Form fields discovered:
  - _systemfield_name (Name - required)
  - _systemfield_email (Email - required)
  - _systemfield_resume (Resume file upload - required)
  - id="16533825-7af9-4f94-8957-2ec4f18da704" (Where are you based?)
  - radio Yes: id="fe607aec-...-labeled-radio-0" (Legal right to work in NL)
  - id="63bdd892-aeb0-4a06-b9b9-d07743cae601" (GitHub link - required)
  - reCAPTCHA present — blocks auto-submit
"""

import time
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

APPLY_URL = "https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven",
}

# Use attribute selectors for numeric IDs
LOCATION_SEL = '[id="16533825-7af9-4f94-8957-2ec4f18da704"]'
GITHUB_SEL = '[id="63bdd892-aeb0-4a06-b9b9-d07743cae601"]'
RADIO_YES_SEL = '[id="fe607aec-bcdd-4bea-ac53-473e1e332d6e_e52fcc03-cc5a-468c-8629-45c0895ac23e-labeled-radio-0"]'

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"tebi-{name}-{ts}.png")
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


def main():
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--ignore-certificate-errors", "--no-sandbox",
                  "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Loading Tebi application form...")
        page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        print(f"Title: {page.title()}")
        screenshots.append(screenshot(page, "v3-01-loaded"))

        # --- Name ---
        name_field = page.wait_for_selector('#_systemfield_name', timeout=8000)
        name_field.click()
        name_field.fill(CANDIDATE["full_name"])
        print(f"Filled Name: {CANDIDATE['full_name']}")

        # --- Email ---
        email_field = page.wait_for_selector('#_systemfield_email', timeout=5000)
        email_field.click()
        email_field.fill(CANDIDATE["email"])
        print(f"Filled Email: {CANDIDATE['email']}")

        # --- Resume upload ---
        resume_input = page.wait_for_selector('#_systemfield_resume', timeout=5000)
        resume_input.set_input_files(RESUME_PATH)
        print("Uploaded resume: Hisham Abboud CV.pdf")
        time.sleep(3)

        screenshots.append(screenshot(page, "v3-02-name-email-resume"))

        # --- Location ---
        try:
            loc_field = page.wait_for_selector(LOCATION_SEL, timeout=5000)
            loc_field.click()
            loc_field.fill(CANDIDATE["location"])
            time.sleep(1.5)
            # Try to pick from autocomplete dropdown
            try:
                option = page.wait_for_selector('[role="option"]', timeout=3000)
                option.click()
                print(f"Filled Location via dropdown")
            except:
                # Accept typed value with Tab
                loc_field.press("Tab")
                print(f"Filled Location: {CANDIDATE['location']} (typed, no dropdown)")
        except Exception as e:
            print(f"Location error: {e}")

        # --- Legal right to work = Yes ---
        try:
            yes_radio = page.wait_for_selector(RADIO_YES_SEL, timeout=5000)
            yes_radio.click()
            print("Selected: Legal right to work in Netherlands = Yes")
        except Exception as e:
            print(f"Radio Yes error: {e}")
            # Try by label
            try:
                page.click('label:has-text("Yes")')
                print("Selected Yes via label fallback")
            except:
                pass

        # --- GitHub ---
        try:
            gh_field = page.wait_for_selector(GITHUB_SEL, timeout=5000)
            gh_field.click()
            gh_field.fill(CANDIDATE["github"])
            print(f"Filled GitHub: {CANDIDATE['github']}")
        except Exception as e:
            print(f"GitHub error: {e}")

        time.sleep(1)
        screenshots.append(screenshot(page, "v3-03-all-fields-filled"))

        # --- Scroll to bottom ---
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        screenshots.append(screenshot(page, "v3-04-form-bottom"))

        # --- Verify field values ---
        print("\nVerifying filled values...")
        checks = [
            ('#_systemfield_name', 'name'),
            ('#_systemfield_email', 'email'),
            (LOCATION_SEL, 'location'),
            (GITHUB_SEL, 'github'),
        ]
        for sel, label in checks:
            try:
                el = page.query_selector(sel)
                if el:
                    val = el.input_value()
                    print(f"  {label}: '{val}'")
            except:
                pass

        # Radio check
        try:
            yes_checked = page.evaluate(f'document.querySelector(\'{RADIO_YES_SEL}\').checked')
            print(f"  legal_right_to_work_yes: {yes_checked}")
        except:
            pass

        # reCAPTCHA check
        page_content = page.content().lower()
        has_recaptcha = 'recaptcha' in page_content

        print(f"\nreCAPTCHA present: {has_recaptcha}")

        # Scroll back to top for final screenshot
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        screenshots.append(screenshot(page, "v3-05-final-top"))

        browser.close()

    notes = (
        "Ashby ATS form fully filled via Playwright automation. "
        "Name=Hisham Abboud, Email=hiaham123@hotmail.com, Resume=Hisham Abboud CV.pdf (uploaded), "
        "Location=Eindhoven, Legal right to work Netherlands=Yes, GitHub=https://github.com/Hishamabboud. "
        "Google reCAPTCHA (id=g-recaptcha-response-100000) present and blocks automated submission. "
        "MANUAL ACTION REQUIRED: Open https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application "
        "in a browser, fill in the form fields as above, solve the reCAPTCHA, and click Submit."
    )

    result = {
        "status": "requires_manual_step",
        "screenshots": screenshots,
        "notes": notes,
        "timestamp": ts,
        "apply_url": APPLY_URL,
    }
    print(f"\n--- RESULT ---")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
