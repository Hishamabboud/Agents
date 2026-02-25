#!/usr/bin/env python3
"""
Apply to CM.com Medior Backend Developer (Conversational Router / Conversational AI Cloud)
Application URL: https://jobs.cm.com/o/medior-backend-developer/c/new
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Paths
AGENTS_DIR = Path("/home/user/Agents")
SCREENSHOTS_DIR = AGENTS_DIR / "output" / "screenshots"
CV_FILE = AGENTS_DIR / "profile" / "Hisham Abboud CV.pdf"
COVER_LETTER_FILE = AGENTS_DIR / "output" / "cover-letters" / "cm-com-medior-backend-developer-conversational-ai.txt"
APPLICATIONS_JSON = AGENTS_DIR / "data" / "applications.json"

# Application details
JOB_URL = "https://jobs.cm.com/o/medior-backend-developer"
APPLICATION_URL = "https://jobs.cm.com/o/medior-backend-developer/c/new"
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "location": "Eindhoven, Netherlands",
}

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_path(name: str) -> str:
    return str(SCREENSHOTS_DIR / f"cmcom-{name}-{TIMESTAMP}.png")


def load_cover_letter() -> str:
    with open(COVER_LETTER_FILE, "r") as f:
        return f.read().strip()


def load_applications() -> list:
    with open(APPLICATIONS_JSON, "r") as f:
        return json.load(f)


def save_applications(apps: list):
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)


async def apply():
    cover_letter_text = load_cover_letter()
    screenshots_taken = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await context.new_page()

        try:
            print(f"Navigating to {APPLICATION_URL}")
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Screenshot: initial load
            sc1 = screenshot_path("01-initial")
            await page.screenshot(path=sc1, full_page=True)
            screenshots_taken.append(sc1)
            print(f"Screenshot: {sc1}")

            # Check current URL
            current_url = page.url
            print(f"Current URL: {current_url}")

            # --- Fill Full Name ---
            try:
                name_field = page.locator('input[name="name"], input[placeholder*="name" i], input[id*="name" i]').first
                await name_field.wait_for(state="visible", timeout=5000)
                await name_field.fill(APPLICANT["full_name"])
                print("Filled: Full name")
            except Exception as e:
                print(f"Name field error: {e}")
                # Try separate first/last name fields
                try:
                    first_field = page.locator('input[name="first_name"], input[placeholder*="first" i]').first
                    last_field = page.locator('input[name="last_name"], input[placeholder*="last" i]').first
                    await first_field.fill(APPLICANT["first_name"])
                    await last_field.fill(APPLICANT["last_name"])
                    print("Filled: First + Last name (separate fields)")
                except Exception as e2:
                    print(f"Separate name fields error: {e2}")

            # --- Fill Email ---
            try:
                email_field = page.locator('input[name="email"], input[type="email"], input[placeholder*="email" i]').first
                await email_field.fill(APPLICANT["email"])
                print("Filled: Email")
            except Exception as e:
                print(f"Email field error: {e}")

            # --- Fill Phone ---
            try:
                phone_field = page.locator('input[name="phone"], input[type="tel"], input[placeholder*="phone" i]').first
                await phone_field.fill(APPLICANT["phone"])
                print("Filled: Phone")
            except Exception as e:
                print(f"Phone field error: {e}")

            # --- Upload CV ---
            try:
                cv_input = page.locator('input[type="file"]').first
                await cv_input.set_input_files(str(CV_FILE))
                print("Uploaded: CV")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload error: {e}")

            # Screenshot after basic fields
            sc2 = screenshot_path("02-basic-filled")
            await page.screenshot(path=sc2, full_page=True)
            screenshots_taken.append(sc2)
            print(f"Screenshot: {sc2}")

            # --- Cover letter (optional text area) ---
            try:
                cl_field = page.locator('textarea[name*="cover" i], textarea[placeholder*="cover" i], textarea[name*="letter" i]').first
                await cl_field.fill(cover_letter_text[:2000])
                print("Filled: Cover letter")
            except Exception as e:
                print(f"Cover letter field error: {e}")

            # --- Answer: Do you live in Netherlands? ---
            # Look for Yes/No radio or toggle
            try:
                # Recruitee often uses custom toggles or radio buttons
                yes_options = page.locator('label:has-text("Yes"), button:has-text("Yes"), [data-value="true"]')
                count = await yes_options.count()
                if count > 0:
                    await yes_options.first.click()
                    print("Clicked: Yes (live in Netherlands)")
            except Exception as e:
                print(f"Netherlands question error: {e}")

            # --- Legal right to work ---
            try:
                # Look for dropdown or radio with "Yes" for work permit
                work_permit_yes = page.locator('label:has-text("Yes"), option[value*="yes" i]')
                count = await work_permit_yes.count()
                if count > 1:
                    await work_permit_yes.nth(1).click()
                    print("Clicked: Yes (work permit)")
            except Exception as e:
                print(f"Work permit question error: {e}")

            # --- English proficiency ---
            try:
                # C2 / C1 option for fluent English
                c2_option = page.locator('label:has-text("C2"), option[value*="C2" i], label:has-text("C1")').first
                await c2_option.click()
                print("Selected: C2 English proficiency")
            except Exception as e:
                print(f"English proficiency error: {e}")

            # Screenshot before submit
            sc3 = screenshot_path("03-before-submit")
            await page.screenshot(path=sc3, full_page=True)
            screenshots_taken.append(sc3)
            print(f"Screenshot: {sc3}")

            # --- Privacy/consent checkbox ---
            try:
                consent = page.locator('input[type="checkbox"]').first
                is_checked = await consent.is_checked()
                if not is_checked:
                    await consent.check()
                    print("Checked: Privacy consent")
            except Exception as e:
                print(f"Consent checkbox error: {e}")

            # --- Submit ---
            try:
                submit_btn = page.locator('button[type="submit"], input[type="submit"], button:has-text("Apply now"), button:has-text("Submit"), button:has-text("Send")').first
                submit_text = await submit_btn.text_content()
                print(f"Clicking submit button: '{submit_text}'")
                await submit_btn.click()
                await page.wait_for_timeout(4000)
            except Exception as e:
                print(f"Submit button error: {e}")

            # Screenshot after submit
            sc4 = screenshot_path("04-after-submit")
            await page.screenshot(path=sc4, full_page=True)
            screenshots_taken.append(sc4)
            print(f"Screenshot: {sc4}")

            # Check for confirmation
            page_text = await page.inner_text("body")
            final_url = page.url
            print(f"Final URL: {final_url}")

            if any(kw in page_text.lower() for kw in ["thank you", "application received", "successfully", "submitted", "bedankt", "ontvangen"]):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. Final URL: {final_url}. Email: {APPLICANT['email']}."
                print("SUCCESS: Application submitted!")
            elif "captcha" in page_text.lower() or "recaptcha" in page_text.lower() or "hcaptcha" in page_text.lower():
                status = "skipped"
                notes = f"CAPTCHA detected on submission. Manual completion required. URL: {final_url}."
                print("CAPTCHA DETECTED - marking as skipped")
            else:
                # Check if still on form or error
                if "/c/new" in final_url or "apply" in final_url.lower():
                    status = "failed"
                    notes = f"Still on form page after submit. Possible validation error. URL: {final_url}."
                    # Get any error messages
                    errors = []
                    error_els = await page.query_selector_all('.error, .alert, [class*="error" i], [class*="invalid" i]')
                    for el in error_els[:5]:
                        err_text = await el.inner_text()
                        if err_text.strip():
                            errors.append(err_text.strip())
                    if errors:
                        notes += f" Errors: {'; '.join(errors)}"
                else:
                    status = "applied"
                    notes = f"Submit clicked, redirected to: {final_url}. Assumed successful."
                print(f"Status: {status}. Notes: {notes}")

        except Exception as e:
            status = "failed"
            notes = f"Exception during application: {str(e)}"
            print(f"ERROR: {e}")
            try:
                sc_err = screenshot_path("error")
                await page.screenshot(path=sc_err, full_page=True)
                screenshots_taken.append(sc_err)
            except:
                pass

        finally:
            await browser.close()

    # Log to applications.json
    apps = load_applications()
    new_entry = {
        "id": f"cmcom-medior-backend-developer-conversational-ai-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "CM.com",
        "role": "Medior Backend Developer (Conversational AI Cloud)",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": status,
        "resume_file": str(CV_FILE),
        "cover_letter_file": str(COVER_LETTER_FILE),
        "screenshots": screenshots_taken,
        "notes": notes,
        "email_used": APPLICANT["email"],
        "response": None,
    }
    apps.append(new_entry)
    save_applications(apps)
    print(f"\nApplication logged with status: {status}")
    print(f"Entry ID: {new_entry['id']}")
    return new_entry


if __name__ == "__main__":
    asyncio.run(apply())
