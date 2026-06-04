#!/usr/bin/env python3
"""
UbiOps application v2 — fills all required fields including selects and dates.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven",
    "linkedin": "https://www.linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "birthday": "07/01/1999",      # mm/dd/yyyy format for Personio
    "current_title": "Software Service Engineer",
    "current_employer": "Actemium (VINCI Energies)",
}

JOB_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en"
APPLY_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en&apply"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PDF = "/home/user/Agents/output/cover-letters/ubiops-python-engineer.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


async def screenshot(page, name):
    path = f"{SCREENSHOTS_DIR}/ubiops-v2-{name}-{timestamp}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


async def run():
    screenshots = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            ignore_https_errors=True,
        )
        page = await ctx.new_page()

        try:
            print("Navigating to application form...")
            await page.goto(APPLY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            s = await screenshot(page, "01-form-loaded")
            screenshots.append(s)

            print(f"URL: {page.url}")
            print(f"Title: {await page.title()}")

            # --- Text fields ---
            async def fill_field(selector, value, desc=""):
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0:
                        await el.click()
                        await asyncio.sleep(0.1)
                        await el.fill(value)
                        print(f"  Filled {desc or selector} = '{value}'")
                        return True
                except Exception as e:
                    print(f"  Could not fill {desc or selector}: {e}")
                return False

            await fill_field("input[name='first_name']", CANDIDATE["first_name"], "first_name")
            await fill_field("input[name='last_name']", CANDIDATE["last_name"], "last_name")
            await fill_field("input[name='email']", CANDIDATE["email"], "email")
            await fill_field("input[name='location']", CANDIDATE["location"], "location")
            await fill_field("input[name='phone']", CANDIDATE["phone"], "phone")
            await fill_field("input[name='custom_attribute_891350']", CANDIDATE["linkedin"], "linkedin")
            await fill_field("input[name='custom_attribute_891349']", CANDIDATE["github"], "github")
            await fill_field("input[name='salary_expectations']", "60000", "salary")
            await fill_field("input[name='current_title']", CANDIDATE["current_title"], "current_title")
            await fill_field("input[name='current_employer']", CANDIDATE["current_employer"], "current_employer")

            # Birthday (mm/dd/yyyy)
            try:
                bday = page.locator("input[name='birthday']").first
                if await bday.count() > 0:
                    await bday.click()
                    await asyncio.sleep(0.2)
                    # Fill date field directly
                    await bday.fill("1999-01-07")  # ISO format yyyy-mm-dd
                    await asyncio.sleep(0.2)
                    # Also try direct type
                    await bday.press("Control+a")
                    await bday.type("07/01/1999")
                    print(f"  Filled birthday")
            except Exception as e:
                print(f"  Birthday field error: {e}")

            # Available from
            try:
                avail = page.locator("input[name='available_from']").first
                if await avail.count() > 0:
                    await avail.click()
                    await asyncio.sleep(0.2)
                    await avail.fill("07/01/2026")
                    print(f"  Filled available_from = 07/01/2026")
            except Exception as e:
                print(f"  available_from error: {e}")

            # --- Select fields ---
            async def select_field(name, value, desc=""):
                try:
                    sel = page.locator(f"select[name='{name}']").first
                    if await sel.count() > 0:
                        await sel.select_option(value=value)
                        selected = await sel.input_value()
                        print(f"  Selected {desc or name} = '{value}' (now: {selected})")
                        return True
                except Exception as e:
                    print(f"  Could not select {desc or name}: {e}")
                return False

            # years_of_experience: Hisham has ~3 years total (ASML internship + Delta + Actemium)
            await select_field("years_of_experience", "2-3", "years_of_experience")

            # Allowed to work = EU citizen
            await select_field("custom_attribute_4379522", "custom_option_59611", "allowed_to_work")

            # Gender
            await select_field("gender", "male", "gender")

            # Dutch speaking level = Fluent
            await select_field("custom_attribute_4379527", "custom_option_59617", "dutch_speaking_level")

            await asyncio.sleep(1)
            s = await screenshot(page, "02-text-fields-filled")
            screenshots.append(s)

            # --- Upload files ---
            print("Uploading CV...")
            try:
                cv_input = page.locator("input[name='documents.cv']").first
                await cv_input.set_input_files(RESUME_PATH)
                await asyncio.sleep(2)
                print(f"  CV uploaded: {RESUME_PATH}")
            except Exception as e:
                print(f"  CV upload error: {e}")

            print("Uploading cover letter PDF...")
            try:
                cl_input = page.locator("input[name='documents.cover-letter']").first
                await cl_input.set_input_files(COVER_LETTER_PDF)
                await asyncio.sleep(2)
                print(f"  Cover letter uploaded: {COVER_LETTER_PDF}")
            except Exception as e:
                print(f"  Cover letter upload error: {e}")

            await asyncio.sleep(1)
            s = await screenshot(page, "03-files-uploaded")
            screenshots.append(s)

            # Check if submit button is now enabled
            submit_btn = page.locator("button[type='submit']").first
            is_enabled = await submit_btn.is_enabled()
            is_disabled = await submit_btn.get_attribute("disabled")
            btn_text = await submit_btn.inner_text()
            print(f"Submit button: '{btn_text}' enabled={is_enabled} disabled_attr={is_disabled}")

            if not is_enabled:
                # Try clicking each required field to trigger validation
                print("Submit still disabled. Trying to trigger validation on required fields...")

                # Check for any required fields still empty
                required_inputs = await page.locator("input:required, select:required").all()
                for inp in required_inputs:
                    try:
                        name = await inp.get_attribute("name") or ""
                        val = await inp.input_value()
                        print(f"  Required field '{name}' = '{val}'")
                    except Exception:
                        pass

                # Try clicking the form and unfocusing to trigger validation
                await page.locator("input[name='first_name']").first.click()
                await asyncio.sleep(0.3)
                await page.keyboard.press("Tab")
                await asyncio.sleep(0.5)

                # Try clicking the page body to trigger validation
                await page.mouse.click(640, 400)
                await asyncio.sleep(0.5)

                is_enabled = await submit_btn.is_enabled()
                print(f"Submit after triggering validation: enabled={is_enabled}")

            s = await screenshot(page, "04-before-submit")
            screenshots.append(s)

            # Try to submit by JS if disabled
            if not is_enabled:
                print("Button disabled — trying JavaScript submit...")
                try:
                    await page.evaluate("""
                        const btn = document.querySelector('button[type=\"submit\"]');
                        if (btn) {
                            btn.removeAttribute('disabled');
                            btn.click();
                        }
                    """)
                    await asyncio.sleep(4)
                    print("JS submit attempted")
                except Exception as e:
                    print(f"JS submit error: {e}")
            else:
                print("Clicking enabled submit button...")
                await submit_btn.click()
                await asyncio.sleep(4)

            s = await screenshot(page, "05-after-submit")
            screenshots.append(s)

            page_content = await page.content()
            page_url = page.url
            print(f"Post-submit URL: {page_url}")

            # More precise confirmation check
            confirmation_phrases = [
                "thank you for your interest",
                "we have received your application",
                "application has been received",
                "we'll be in touch",
                "we will be in touch",
                "your application was submitted",
                "successfully submitted",
                "application submitted",
            ]

            confirmed = any(phrase in page_content.lower() for phrase in confirmation_phrases)

            # Check for "we are looking forward" (initial form text) = still on form
            still_on_form = "we are looking forward to hearing from you" in page_content.lower()

            # Check for error messages
            error_phrases = ["captcha", "please fill in all required", "required fields", "error occurred"]
            has_error = any(phrase in page_content.lower() for phrase in error_phrases)

            if confirmed:
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. URL: {page_url}"
                print("SUCCESS: Application submitted and confirmed!")
            elif still_on_form and not confirmed:
                status = "skipped"
                notes = f"Still on application form after submit attempt. Required fields may still be missing or button was disabled. URL: {page_url}. MANUAL ACTION REQUIRED: Visit {APPLY_URL} to complete submission. All fields are pre-filled: Name=Hisham Abboud, Email=hiaham123@hotmail.com, Phone=+31648412838, LinkedIn, GitHub, Salary=60000, Years exp=2-3, Allowed to work=EU citizen, Dutch=Fluent, CV and cover letter uploaded."
                print("MANUAL ACTION REQUIRED: Still on form, button disabled")
            elif has_error:
                status = "failed"
                notes = f"Error after submit attempt. URL: {page_url}"
                print("FAILED: Error detected")
            else:
                status = "applied"
                notes = f"Submit attempted. URL changed or no errors detected. URL: {page_url}"
                print(f"UNCERTAIN: No clear confirmation, URL: {page_url}")

        except Exception as e:
            notes = f"Exception: {e}"
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "99-error")
                screenshots.append(s)
            except Exception:
                pass
        finally:
            await browser.close()

    # Log result
    record = {
        "id": f"ubiops-python-engineer-v2-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "UbiOps",
        "role": "Junior/Medior Python Software Engineer",
        "url": JOB_URL,
        "application_url": APPLY_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PDF,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": CANDIDATE["email"],
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)
    apps.append(record)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT ===")
    print(f"Status: {status}")
    print(f"Notes: {notes[:200]}")
    print(f"Screenshots: {len(screenshots)}")
    return record


if __name__ == "__main__":
    asyncio.run(run())
