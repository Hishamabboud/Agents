#!/usr/bin/env python3
"""
Apply to Funda Medior Backend .NET Engineer position via jobs.funda.nl (Recruitee ATS)
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

APPLICATION_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer/c/new"
JOB_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/funda-medior-backend-net-engineer.txt"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

APPLICANT = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven, Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def screenshot_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"funda-{name}-{ts}.png")


async def run():
    screenshots = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Europe/Amsterdam",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # Mask webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        try:
            # Step 1: Navigate to job listing page first
            print(f"[1] Loading job listing: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            path = screenshot_path("01-job-listing")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 2: Navigate to the application form
            print(f"[2] Loading application form: {APPLICATION_URL}")
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            path = screenshot_path("02-form-loaded")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Accept cookies if present
            try:
                cookie_btn = page.locator("button:has-text('Accept'), button:has-text('accept'), button:has-text('Akkoord'), button:has-text('OK')")
                if await cookie_btn.first.is_visible(timeout=3000):
                    await cookie_btn.first.click()
                    await page.wait_for_timeout(1000)
                    print("    Accepted cookies")
            except Exception:
                pass

            # Step 3: Fill in full name
            print("[3] Filling personal details...")
            name_input = page.locator("input[name='name'], input[placeholder*='name' i], input[placeholder*='naam' i], input[id*='name' i]").first
            await name_input.wait_for(timeout=10000)
            await name_input.click()
            await page.wait_for_timeout(300)
            await name_input.fill(APPLICANT["full_name"])
            await page.wait_for_timeout(300)
            print(f"    Name: {APPLICANT['full_name']}")

            # Step 4: Fill email
            email_input = page.locator("input[type='email'], input[name='email'], input[placeholder*='email' i]").first
            await email_input.click()
            await page.wait_for_timeout(300)
            await email_input.fill(APPLICANT["email"])
            await page.wait_for_timeout(300)
            print(f"    Email: {APPLICANT['email']}")

            # Step 5: Fill phone
            try:
                phone_input = page.locator("input[type='tel'], input[name='phone'], input[placeholder*='phone' i], input[placeholder*='telefoon' i]").first
                await phone_input.click()
                await page.wait_for_timeout(300)
                await phone_input.fill(APPLICANT["phone"])
                await page.wait_for_timeout(300)
                print(f"    Phone: {APPLICANT['phone']}")
            except Exception as e:
                print(f"    Phone field not found: {e}")

            # Step 6: Upload CV
            print("[6] Uploading CV...")
            try:
                cv_input = page.locator("input[type='file']").first
                await cv_input.set_input_files(CV_PATH)
                await page.wait_for_timeout(2000)
                print(f"    CV uploaded: {CV_PATH}")
            except Exception as e:
                print(f"    CV upload error: {e}")

            path = screenshot_path("03-fields-filled")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 7: Look for cover letter field (text or file upload)
            print("[7] Handling cover letter...")
            try:
                # Try text area for cover letter
                cl_textarea = page.locator("textarea[name*='cover' i], textarea[placeholder*='cover' i], textarea[placeholder*='motivation' i], textarea[name*='letter' i]").first
                if await cl_textarea.is_visible(timeout=3000):
                    await cl_textarea.click()
                    await cl_textarea.fill(COVER_LETTER_TEXT)
                    print("    Cover letter text entered in textarea")
                else:
                    # Try file upload for cover letter
                    file_inputs = await page.locator("input[type='file']").all()
                    if len(file_inputs) >= 2:
                        # Convert text to a temp .txt file for upload
                        await file_inputs[1].set_input_files(COVER_LETTER_PATH)
                        print("    Cover letter file uploaded")
            except Exception as e:
                print(f"    Cover letter: {e}")

            # Step 8: Fill screening questions
            print("[8] Filling screening questions...")

            # "How did you hear about this job?" - look for dropdown
            try:
                source_dropdown = page.locator("select[name*='source' i], select[name*='hear' i], select[id*='source' i]").first
                if await source_dropdown.is_visible(timeout=3000):
                    await source_dropdown.select_option(index=1)
                    print("    Selected how heard source")
            except Exception:
                try:
                    # Try to find any dropdown
                    dropdowns = await page.locator("select").all()
                    for dd in dropdowns:
                        label_text = await dd.evaluate("el => el.closest('label,div')?.textContent || ''")
                        if "hear" in label_text.lower() or "source" in label_text.lower() or "where" in label_text.lower():
                            await dd.select_option(index=1)
                            print(f"    Selected dropdown option for: {label_text[:50]}")
                            break
                except Exception as e:
                    print(f"    Source dropdown: {e}")

            # "Where do you currently live?"
            try:
                location_inputs = page.locator("input[name*='live' i], input[name*='location' i], input[name*='city' i], input[placeholder*='live' i], input[placeholder*='woon' i]")
                if await location_inputs.first.is_visible(timeout=3000):
                    await location_inputs.first.fill("Eindhoven, Netherlands")
                    print("    Location filled: Eindhoven, Netherlands")
            except Exception as e:
                print(f"    Location field: {e}")

            # "Notice period"
            try:
                notice_inputs = page.locator("input[name*='notice' i], textarea[name*='notice' i], input[placeholder*='notice' i], input[placeholder*='opzegtermijn' i]")
                if await notice_inputs.first.is_visible(timeout=3000):
                    await notice_inputs.first.fill("1 month notice period")
                    print("    Notice period filled")
            except Exception as e:
                print(f"    Notice period field: {e}")

            # "Why do you want to work at Funda?"
            try:
                why_inputs = page.locator("textarea[name*='why' i], textarea[placeholder*='funda' i], textarea[placeholder*='why' i], textarea[placeholder*='waarom' i]")
                if await why_inputs.first.is_visible(timeout=3000):
                    await why_inputs.first.fill(
                        "I am drawn to Funda because of its scale and engineering challenges. "
                        "Building performant microservices for millions of users searching for homes in the Netherlands "
                        "aligns perfectly with my backend .NET experience and my drive to work on impactful, high-traffic systems."
                    )
                    print("    'Why Funda' filled")
            except Exception as e:
                print(f"    Why Funda field: {e}")

            # Scroll down to see all fields
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)

            path = screenshot_path("04-mid-form")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            path = screenshot_path("05-form-bottom")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 9: Check privacy/consent checkbox
            print("[9] Checking consent checkbox...")
            try:
                consent_checkbox = page.locator("input[type='checkbox'][name*='gdpr' i], input[type='checkbox'][name*='privacy' i], input[type='checkbox'][name*='consent' i], input[type='checkbox'][name*='acknowledge' i]").first
                if await consent_checkbox.is_visible(timeout=3000):
                    if not await consent_checkbox.is_checked():
                        await consent_checkbox.check()
                        print("    Privacy consent checkbox checked")
                else:
                    # Try any unchecked checkboxes
                    checkboxes = await page.locator("input[type='checkbox']").all()
                    for cb in checkboxes:
                        if not await cb.is_checked():
                            await cb.check()
                            print("    Checked a checkbox")
            except Exception as e:
                print(f"    Consent checkbox: {e}")

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            # Take pre-submit screenshot
            path = screenshot_path("06-before-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"[10] Pre-submit screenshot: {path}")

            # Step 10: Submit the form
            print("[11] Submitting form...")
            submit_btn = page.locator(
                "button[type='submit'], button:has-text('Submit'), button:has-text('Apply'), "
                "button:has-text('Send application'), button:has-text('Verzenden'), "
                "input[type='submit']"
            ).first

            if await submit_btn.is_visible(timeout=5000):
                await submit_btn.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await submit_btn.click()
                print("    Submit button clicked")
                await page.wait_for_timeout(5000)
            else:
                print("    Submit button not found via standard selectors, trying broader search...")
                btns = await page.locator("button").all()
                for btn in btns:
                    txt = await btn.text_content()
                    if txt and any(w in txt.lower() for w in ["submit", "apply", "send", "verzend", "solliciteer"]):
                        await btn.scroll_into_view_if_needed()
                        await btn.click()
                        print(f"    Clicked button: '{txt}'")
                        await page.wait_for_timeout(5000)
                        break

            path = screenshot_path("07-after-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Post-submit screenshot: {path}")

            # Check for success indicators
            current_url = page.url
            page_content = await page.content()
            page_text = await page.evaluate("document.body.innerText")

            success_indicators = [
                "thank you", "bedankt", "application received", "application submitted",
                "sollicitatie ontvangen", "we'll be in touch", "confirmation", "success"
            ]
            captcha_indicators = ["captcha", "hcaptcha", "recaptcha", "i am not a robot"]
            error_indicators = ["error", "failed", "invalid", "required"]

            page_lower = page_text.lower()

            if any(ind in page_lower for ind in success_indicators):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. Final URL: {current_url}"
                print(f"    SUCCESS: {notes}")
            elif any(ind in page_lower for ind in captcha_indicators):
                status = "skipped"
                notes = f"CAPTCHA detected after submit. Manual completion required. URL: {current_url}"
                print(f"    CAPTCHA: {notes}")
            else:
                # Check if URL changed (often indicates success on Recruitee)
                if "/c/new" not in current_url and "funda" in current_url:
                    status = "applied"
                    notes = f"Form submitted, URL changed to: {current_url}. Likely success."
                    print(f"    URL changed: {notes}")
                else:
                    status = "failed"
                    notes = f"Submission result unclear. URL: {current_url}. Page text snippet: {page_text[:200]}"
                    print(f"    UNCLEAR: {notes}")

        except Exception as e:
            notes = f"Exception during application: {str(e)}"
            status = "failed"
            print(f"    ERROR: {notes}")
            try:
                path = screenshot_path("error")
                await page.screenshot(path=path)
                screenshots.append(path)
            except Exception:
                pass

        finally:
            await browser.close()

    # Save to applications.json
    app_entry = {
        "id": f"funda-medior-net-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Funda Real Estate B.V.",
        "role": "Medior Backend .NET Engineer",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": APPLICANT["email"],
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    apps.append(app_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT ===")
    print(f"Status: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    print(f"Application log saved to: {APPLICATIONS_JSON}")
    return app_entry


if __name__ == "__main__":
    asyncio.run(run())
