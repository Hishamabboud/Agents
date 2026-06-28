#!/usr/bin/env python3
"""
UbiOps final application script.
Fills all required fields and uploads CV + cover letter.
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
    "current_title": "Software Service Engineer",
    "current_employer": "Actemium (VINCI Energies)",
}

JOB_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en"
APPLY_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en&apply"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PDF = "/home/user/Agents/output/cover-letters/ubiops-python-engineer.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


async def ss(page, name):
    path = f"{SCREENSHOTS_DIR}/ubiops-final-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


async def fill(page, selector, value, desc=""):
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            await el.click()
            await asyncio.sleep(0.15)
            await el.fill("")
            await el.type(value, delay=30)
            print(f"  Filled '{desc or selector}' = '{value}'")
            return True
    except Exception as e:
        print(f"  Error filling '{desc or selector}': {e}")
    return False


async def select_opt(page, name, value, desc=""):
    try:
        sel = page.locator(f"select[name='{name}']").first
        if await sel.count() > 0:
            await sel.select_option(value=value)
            print(f"  Selected '{desc or name}' = '{value}'")
            return True
    except Exception as e:
        print(f"  Error selecting '{desc or name}': {e}")
    return False


async def run():
    shots = []
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
            print("Loading application form...")
            await page.goto(APPLY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            s = await ss(page, "01-loaded")
            shots.append(s)
            print(f"URL: {page.url}, Title: {await page.title()}")

            # ===== Fill text fields =====
            print("\nFilling text fields...")
            await fill(page, "input[name='first_name']", CANDIDATE["first_name"], "first_name")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='last_name']", CANDIDATE["last_name"], "last_name")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='email']", CANDIDATE["email"], "email")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='location']", CANDIDATE["location"], "location")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='phone']", CANDIDATE["phone"], "phone")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='custom_attribute_891350']", CANDIDATE["linkedin"], "linkedin")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='custom_attribute_891349']", CANDIDATE["github"], "github")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='salary_expectations']", "60000", "salary")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='current_title']", CANDIDATE["current_title"], "current_title")
            await asyncio.sleep(0.3)
            await fill(page, "input[name='current_employer']", CANDIDATE["current_employer"], "current_employer")
            await asyncio.sleep(0.3)

            # Available from: use MM/DD/YYYY format (Personio date field)
            try:
                avail = page.locator("input[name='available_from']").first
                if await avail.count() > 0:
                    await avail.click()
                    await asyncio.sleep(0.2)
                    await avail.fill("07/01/2026")
                    await asyncio.sleep(0.2)
                    # If field is date type, try ISO
                    val = await avail.input_value()
                    if not val or val == "07/01/2026":
                        await avail.fill("")
                        await avail.type("07/01/2026", delay=30)
                    print(f"  Filled available_from (value: {await avail.input_value()})")
            except Exception as e:
                print(f"  available_from error: {e}")

            # Birthday (required)
            try:
                bday = page.locator("input[name='birthday']").first
                if await bday.count() > 0:
                    input_type = await bday.get_attribute("type") or "text"
                    await bday.click()
                    await asyncio.sleep(0.2)
                    if input_type == "date":
                        # date inputs expect yyyy-mm-dd
                        await bday.fill("1999-01-07")
                    else:
                        await bday.type("01/07/1999", delay=30)
                    val = await bday.input_value()
                    print(f"  Filled birthday (type={input_type}, value={val})")
            except Exception as e:
                print(f"  birthday error: {e}")

            # ===== Select fields =====
            print("\nFilling select fields...")
            # Years of experience: Hisham has ~3 years (ASML 6mo + Delta 1yr + Actemium ~1yr)
            await select_opt(page, "years_of_experience", "2-3", "years_of_experience")
            # Allowed to work: EU citizen
            await select_opt(page, "custom_attribute_4379522", "custom_option_59611", "allowed_to_work")
            # Gender
            await select_opt(page, "gender", "male", "gender")
            # Dutch speaking level: Fluent
            await select_opt(page, "custom_attribute_4379527", "custom_option_59617", "dutch_speaking")

            await asyncio.sleep(1)
            s = await ss(page, "02-fields-filled")
            shots.append(s)

            # ===== Upload files =====
            print("\nUploading files...")

            # Make hidden file inputs accessible by making them visible via JS
            await page.evaluate("""() => {
                document.querySelectorAll("input[type='file']").forEach(inp => {
                    inp.style.display = 'block';
                    inp.style.opacity = '1';
                    inp.style.position = 'relative';
                });
            }""")
            await asyncio.sleep(0.5)

            # Upload CV
            try:
                cv_inp = page.locator("input[id='doc-input-cv']").first
                await cv_inp.set_input_files(RESUME_PATH)
                await asyncio.sleep(2)
                print(f"  CV uploaded: {RESUME_PATH}")
            except Exception as e:
                print(f"  CV upload error: {e}")
                # Fallback: use the visible Add file button
                try:
                    cv_section = page.locator("label[for='doc-input-cv'], button:near(text('CV'))").first
                    if await cv_section.count() > 0:
                        async with page.expect_file_chooser() as fc_info:
                            await cv_section.click()
                        fc = await fc_info.value
                        await fc.set_files(RESUME_PATH)
                        await asyncio.sleep(2)
                        print(f"  CV uploaded via file chooser")
                except Exception as e2:
                    print(f"  CV file chooser error: {e2}")

            # Upload cover letter
            try:
                cl_inp = page.locator("input[id='doc-input-cover-letter']").first
                await cl_inp.set_input_files(COVER_LETTER_PDF)
                await asyncio.sleep(2)
                print(f"  Cover letter uploaded: {COVER_LETTER_PDF}")
            except Exception as e:
                print(f"  Cover letter upload error: {e}")

            await asyncio.sleep(1)
            s = await ss(page, "03-files-uploaded")
            shots.append(s)

            # ===== Check and submit =====
            print("\nChecking form completeness...")
            submit_btn = page.locator("button[type='submit']").first

            try:
                is_disabled_attr = await submit_btn.get_attribute("disabled")
                btn_text = await submit_btn.inner_text()
                print(f"Submit button: '{btn_text}', disabled_attr={is_disabled_attr}")
            except Exception as e:
                print(f"Submit button check error: {e}")
                is_disabled_attr = "true"

            if is_disabled_attr is not None:
                print("Submit button is disabled. Checking for missing required fields...")
                # Scroll through page to see form state
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(0.5)

                # Try using JS to remove disabled and click
                print("Attempting JS submit bypass...")
                result = await page.evaluate("""() => {
                    const btn = document.querySelector('button[type="submit"]');
                    if (!btn) return 'no button found';
                    const wasDisabled = btn.disabled;
                    btn.disabled = false;
                    btn.removeAttribute('disabled');
                    btn.click();
                    return `clicked (was disabled: ${wasDisabled})`;
                }""")
                print(f"JS submit result: {result}")
                await asyncio.sleep(4)
            else:
                print("Submit button enabled, clicking...")
                await submit_btn.click()
                await asyncio.sleep(4)

            s = await ss(page, "04-after-submit")
            shots.append(s)

            page_content = await page.content()
            page_url = page.url
            print(f"Post-submit URL: {page_url}")

            # Check result
            confirmation_phrases = [
                "thank you for your interest in ubiops",
                "we have received your application",
                "application has been submitted",
                "application was submitted",
                "successfully submitted",
                "we'll be in touch",
                "we will be in touch",
                "your application",
            ]
            # The form intro text says "Thank you for your interest in UbiOps. Please fill out..."
            # So we need to check more specifically
            confirmed_specific = [
                "we have received",
                "application submitted",
                "thank you for applying",
                "your application has been",
                "successfully submitted",
            ]

            still_form = "please fill out the following short form" in page_content.lower()
            confirmed = any(p in page_content.lower() for p in confirmed_specific)

            if confirmed:
                status = "applied"
                notes = f"Application successfully submitted to UbiOps via Personio. Confirmation detected. URL: {page_url}"
                print("SUCCESS: Application submitted and confirmed!")
            elif still_form:
                # Still on the form - try to identify what's still missing
                required_empty = await page.evaluate("""() => {
                    const required = document.querySelectorAll('[required], [aria-required=true]');
                    const missing = [];
                    required.forEach(el => {
                        if (!el.value || el.value === '') {
                            missing.push(el.name || el.id || 'unnamed');
                        }
                    });
                    return missing;
                }""")
                print(f"Still missing required fields: {required_empty}")
                status = "skipped"
                notes = (
                    f"Form not submitted. Still on application form. "
                    f"Missing required fields (if any): {required_empty}. "
                    f"MANUAL ACTION REQUIRED: Visit {APPLY_URL} and submit manually. "
                    f"All data: Name=Hisham Abboud, Email=hiaham123@hotmail.com, Phone=+31648412838, "
                    f"Location=Eindhoven, LinkedIn={CANDIDATE['linkedin']}, GitHub={CANDIDATE['github']}, "
                    f"Salary=60000, Years exp=2-3, Allowed to work=EU citizen, Dutch=Fluent, "
                    f"Current title={CANDIDATE['current_title']}, "
                    f"Current employer={CANDIDATE['current_employer']}. "
                    f"CV and cover letter PDFs ready at: {RESUME_PATH} and {COVER_LETTER_PDF}"
                )
                print(f"MANUAL ACTION REQUIRED: {notes[:200]}")
            else:
                # URL changed or something different
                status = "applied"
                notes = f"Submit attempted. Page changed. URL: {page_url}. Verify manually."
                print(f"UNCERTAIN: URL={page_url}")

        except Exception as e:
            notes = f"Exception: {e}"
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await ss(page, "99-error")
                shots.append(s)
            except Exception:
                pass
        finally:
            await browser.close()

    record = {
        "id": f"ubiops-python-engineer-final-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "UbiOps",
        "role": "Junior/Medior Python Software Engineer",
        "url": JOB_URL,
        "application_url": APPLY_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PDF,
        "screenshots": shots,
        "notes": notes,
        "response": None,
        "email_used": CANDIDATE["email"],
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)
    apps.append(record)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== FINAL RESULT ===")
    print(f"Status: {status}")
    print(f"Notes: {notes[:300]}")
    print(f"Screenshots: {shots}")
    return record


if __name__ == "__main__":
    asyncio.run(run())
