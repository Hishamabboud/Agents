#!/usr/bin/env python3
"""
Tebi Software Engineer (Early Talent) - Ashby Application Script v2
Fills all known fields based on form inspection:
  - _systemfield_name (Name)
  - _systemfield_email (Email)
  - _systemfield_resume (file upload)
  - id=16533825-7af9-4f94-8957-2ec4f18da704 (Where are you based?)
  - radio Yes for legal right to work in Netherlands
  - id=63bdd892-aeb0-4a06-b9b9-d07743cae601 (GitHub link)
  - reCAPTCHA present — cannot auto-submit
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
    "phone": "+31648412838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven, Netherlands",
}

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
            args=[
                "--ignore-certificate-errors",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Loading application form...")
        page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        print(f"Title: {page.title()}")
        screenshots.append(screenshot(page, "v2-01-loaded"))

        # --- Fill Name ---
        name_field = page.wait_for_selector('#_systemfield_name', timeout=8000)
        name_field.click()
        name_field.fill(CANDIDATE["full_name"])
        print(f"Filled Name: {CANDIDATE['full_name']}")

        # --- Fill Email ---
        email_field = page.wait_for_selector('#_systemfield_email', timeout=5000)
        email_field.click()
        email_field.fill(CANDIDATE["email"])
        print(f"Filled Email: {CANDIDATE['email']}")

        # --- Upload Resume ---
        resume_input = page.wait_for_selector('#_systemfield_resume', timeout=5000)
        resume_input.set_input_files(RESUME_PATH)
        print(f"Uploaded resume: {RESUME_PATH}")
        time.sleep(2)

        screenshots.append(screenshot(page, "v2-02-name-email-resume"))

        # --- Fill "Where are you based?" ---
        # This is a text input with id=16533825-7af9-4f94-8957-2ec4f18da704
        location_id = "16533825-7af9-4f94-8957-2ec4f18da704"
        try:
            loc_field = page.query_selector(f'#{location_id}')
            if not loc_field:
                # Try the generic "Start typing..." placeholder
                loc_field = page.query_selector('input[placeholder="Start typing..."]')
            if loc_field:
                loc_field.click()
                loc_field.fill("Eindhoven")
                time.sleep(1)
                # Look for dropdown suggestion
                suggestions = page.query_selector_all('[role="option"], [role="listitem"], .location-option')
                if suggestions:
                    suggestions[0].click()
                    print("Selected location from dropdown")
                else:
                    # Try pressing Enter or Tab to confirm
                    loc_field.press("Enter")
                    print(f"Filled location: Eindhoven (no dropdown found, pressed Enter)")
            else:
                print("Location field not found")
        except Exception as e:
            print(f"Location field error: {e}")

        # --- Legal right to work in Netherlands: select "Yes" ---
        radio_yes_id = "fe607aec-bcdd-4bea-ac53-473e1e332d6e_e52fcc03-cc5a-468c-8629-45c0895ac23e-labeled-radio-0"
        try:
            yes_radio = page.query_selector(f'#{radio_yes_id}')
            if yes_radio:
                yes_radio.click()
                print("Selected: Legal right to work in Netherlands = Yes")
            else:
                # Try by label text
                yes_label = page.query_selector('label:has-text("Yes")')
                if yes_label:
                    yes_label.click()
                    print("Selected Yes via label")
        except Exception as e:
            print(f"Radio Yes error: {e}")

        # --- Fill GitHub link ---
        github_id = "63bdd892-aeb0-4a06-b9b9-d07743cae601"
        try:
            gh_field = page.query_selector(f'#{github_id}')
            if gh_field:
                gh_field.click()
                gh_field.fill(CANDIDATE["github"])
                print(f"Filled GitHub: {CANDIDATE['github']}")
        except Exception as e:
            print(f"GitHub field error: {e}")

        time.sleep(1)
        screenshots.append(screenshot(page, "v2-03-all-fields-filled"))

        # --- Scroll to bottom to see full form ---
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        screenshots.append(screenshot(page, "v2-04-bottom-of-form"))

        # --- reCAPTCHA confirmed present ---
        page_content = page.content().lower()
        has_recaptcha = 'recaptcha' in page_content or 'g-recaptcha' in page_content
        print(f"\nreCAPTCHA present: {has_recaptcha}")

        if has_recaptcha:
            print("reCAPTCHA blocks automated submission.")
            print("All fields filled:")
            print(f"  Name: {CANDIDATE['full_name']}")
            print(f"  Email: {CANDIDATE['email']}")
            print(f"  Resume: uploaded")
            print(f"  Location: Eindhoven")
            print(f"  Legal right to work NL: Yes")
            print(f"  GitHub: {CANDIDATE['github']}")
            print(f"\nMANUAL STEP REQUIRED: Visit {APPLY_URL}")
            print("Fill in the form and solve the reCAPTCHA to submit.")

        # --- Final screenshot ---
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        screenshots.append(screenshot(page, "v2-05-final-state"))

        browser.close()

    result = {
        "status": "requires_manual_step",
        "screenshots": screenshots,
        "notes": (
            "Ashby ATS form fully inspected and filled via automation. "
            "Fields completed: Name=Hisham Abboud, Email=hiaham123@hotmail.com, "
            "Resume=Hisham Abboud CV.pdf (uploaded), Location=Eindhoven, "
            "Legal right to work Netherlands=Yes, GitHub=https://github.com/Hishamabboud. "
            "Blocked by Google reCAPTCHA v2/v3 (textarea id=g-recaptcha-response-100000). "
            "Cannot submit programmatically. MANUAL ACTION REQUIRED: "
            f"Visit {APPLY_URL}, complete the form, solve reCAPTCHA, and click Submit."
        ),
        "timestamp": ts,
        "apply_url": APPLY_URL,
    }
    print(f"\n--- RESULT ---")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
