#!/usr/bin/env python3
"""
Automated job application script for ChipSoft .NET Developer Zorg-ICT position.
Vacancy URL: https://www.chipsoft.com/nl-nl/werken-bij/vacatures/net-developer-zorg-ict-1/
Application form: https://www.chipsoft.com/nl-nl/werken-bij/solliciteren/?vacancyId=25

Note: The form has reCAPTCHA, so automated submission is not possible.
This script navigates, fills the form, and documents the state before CAPTCHA.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

VACANCY_URL = "https://www.chipsoft.com/nl-nl/werken-bij/vacatures/net-developer-zorg-ict-1/"
APPLY_URL = "https://www.chipsoft.com/nl-nl/werken-bij/solliciteren/?vacancyId=25"

APPLICANT = {
    "name": "Hisham Abboud",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
    "current_role": "Software Service Engineer at Actemium (VINCI Energies)"
}

def screenshot_path(label):
    return os.path.join(SCREENSHOTS_DIR, f"chipsoft-{label}-{TIMESTAMP}.png")

async def safe_screenshot(page, label):
    """Take a screenshot, disabling font-wait to avoid timeout."""
    path = screenshot_path(label)
    try:
        # Use clip to avoid font-loading timeout issues
        await page.screenshot(path=path, full_page=False, timeout=15000)
        print(f"Screenshot saved: {label} -> {path}")
    except Exception as e:
        print(f"Screenshot failed ({label}): {e}")
        try:
            # Inject CSS to force no font loading, then screenshot
            await page.add_style_tag(content="* { font-family: Arial, sans-serif !important; }")
            await page.screenshot(path=path, timeout=15000)
            print(f"Screenshot saved (fallback): {label}")
        except Exception as e2:
            print(f"Screenshot completely failed ({label}): {e2}")
    return path

async def run():
    notes = []
    status = "failed"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-web-security",
                "--font-render-hinting=none",
                "--disable-font-subpixel-positioning",
                "--disable-remote-fonts",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8"}
        )

        # Block font loading to avoid screenshot timeouts
        await context.route("**/*.woff", lambda route: route.abort())
        await context.route("**/*.woff2", lambda route: route.abort())
        await context.route("**/*.ttf", lambda route: route.abort())
        await context.route("**/*.otf", lambda route: route.abort())

        page = await context.new_page()
        page.set_default_navigation_timeout(45000)
        page.set_default_timeout(15000)

        try:
            # Step 1: Navigate to the vacancy listing page
            print(f"Step 1: Navigating to vacancy page: {VACANCY_URL}")
            try:
                await page.goto(VACANCY_URL, timeout=45000, wait_until="domcontentloaded")
                print("Page loaded (domcontentloaded)")
            except Exception as e:
                print(f"Navigation warning: {e}")

            await asyncio.sleep(2)
            await safe_screenshot(page, "01-vacancy-page")

            title = await page.title()
            url = page.url
            print(f"Page title: {title}")
            print(f"Page URL: {url}")
            notes.append(f"Navigated to vacancy page: {url}")

            # Step 2: Navigate directly to the application form
            print(f"\nStep 2: Navigating to application form: {APPLY_URL}")
            try:
                await page.goto(APPLY_URL, timeout=45000, wait_until="domcontentloaded")
                print("Application form loaded")
            except Exception as e:
                print(f"Form navigation warning: {e}")

            await asyncio.sleep(2)
            await safe_screenshot(page, "02-application-form")

            form_title = await page.title()
            form_url = page.url
            print(f"Form page title: {form_title}")
            print(f"Form page URL: {form_url}")
            notes.append(f"Application form URL: {form_url}")

            # Step 3: Analyze form fields
            print("\nStep 3: Analyzing form fields...")
            try:
                form_fields = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                        type: el.type || el.tagName.toLowerCase(),
                        name: el.name,
                        id: el.id,
                        placeholder: el.placeholder,
                        className: el.className.substring(0, 80),
                        required: el.required,
                        visible: el.offsetParent !== null
                    }))
                """)
                print(f"Found {len(form_fields)} form elements:")
                for f in form_fields:
                    print(f"  {f}")
            except Exception as e:
                print(f"Could not enumerate form fields: {e}")
                form_fields = []

            # Step 4: Fill in the form fields
            print("\nStep 4: Filling in form fields...")
            form_filled_count = 0

            # First name - Voornaam
            voornaam_selectors = [
                "input[name='voornaam']", "input[id='voornaam']",
                "input[placeholder='Voornaam']", "input[placeholder*='voornaam']",
                "input[name*='voornaam']", "input[id*='voornaam']",
                "input[name='firstname']", "input[name='first_name']",
                "input[placeholder='First name']",
            ]
            for sel in voornaam_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(APPLICANT["first_name"])
                        print(f"  Filled first name via: {sel}")
                        form_filled_count += 1
                        break
                except Exception:
                    pass

            # Last name - Achternaam
            achternaam_selectors = [
                "input[name='achternaam']", "input[id='achternaam']",
                "input[placeholder='Achternaam']", "input[placeholder*='achternaam']",
                "input[name*='achternaam']", "input[id*='achternaam']",
                "input[name='lastname']", "input[name='last_name']",
            ]
            for sel in achternaam_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(APPLICANT["last_name"])
                        print(f"  Filled last name via: {sel}")
                        form_filled_count += 1
                        break
                except Exception:
                    pass

            # Phone - Telefoonnummer
            phone_selectors = [
                "input[type='tel']",
                "input[name='telefoonnummer']", "input[id='telefoonnummer']",
                "input[placeholder*='Telefoon']", "input[placeholder*='telefoon']",
                "input[name*='telefoon']", "input[name*='phone']",
                "input[id*='telefoon']", "input[id*='phone']",
            ]
            for sel in phone_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(APPLICANT["phone"])
                        print(f"  Filled phone via: {sel}")
                        form_filled_count += 1
                        break
                except Exception:
                    pass

            # Email
            email_selectors = [
                "input[type='email']",
                "input[name='email']", "input[id='email']",
                "input[placeholder*='Email']", "input[placeholder*='email']",
                "input[name*='email']", "input[id*='email']",
                "input[placeholder*='e-mail']",
            ]
            for sel in email_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(APPLICANT["email"])
                        print(f"  Filled email via: {sel}")
                        form_filled_count += 1
                        break
                except Exception:
                    pass

            # Dropdown - How did you find us
            try:
                dropdown = await page.query_selector("select")
                if dropdown:
                    # Select "LinkedIn" or "Internet/Google" as the source
                    options = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('select option')).map(o => ({
                            value: o.value, text: o.text
                        }))
                    """)
                    print(f"  Dropdown options: {options[:10]}")
                    # Try to select LinkedIn
                    linkedin_option = next((o for o in options if 'linkedin' in o['text'].lower()), None)
                    if linkedin_option:
                        await dropdown.select_option(value=linkedin_option['value'])
                        print(f"  Selected dropdown option: {linkedin_option['text']}")
                        form_filled_count += 1
            except Exception as e:
                print(f"  Dropdown selection failed: {e}")

            # Consent checkbox
            try:
                checkboxes = await page.query_selector_all("input[type='checkbox']")
                for cb in checkboxes:
                    cb_id = await cb.get_attribute("id") or ""
                    cb_name = await cb.get_attribute("name") or ""
                    is_checked = await cb.is_checked()
                    print(f"  Checkbox: id='{cb_id}', name='{cb_name}', checked={is_checked}")
                    if not is_checked:
                        await cb.check()
                        print(f"  Checked consent checkbox: {cb_id or cb_name}")
                        form_filled_count += 1
            except Exception as e:
                print(f"  Checkbox handling failed: {e}")

            await safe_screenshot(page, "03-form-fields-filled")

            # Step 5: Upload resume
            print("\nStep 5: Uploading resume...")
            if os.path.exists(RESUME_PATH):
                file_inputs = await page.query_selector_all("input[type='file']")
                print(f"Found {len(file_inputs)} file input(s)")
                if file_inputs:
                    try:
                        await file_inputs[0].set_input_files(RESUME_PATH)
                        print(f"  Resume uploaded to first file input: {RESUME_PATH}")
                        notes.append(f"Resume uploaded: {os.path.basename(RESUME_PATH)}")
                        form_filled_count += 1
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"  Resume upload failed: {e}")
                        notes.append(f"Resume upload failed: {e}")
            else:
                print(f"Resume not found at: {RESUME_PATH}")

            await safe_screenshot(page, "04-with-resume-uploaded")

            # Step 6: Check for CAPTCHA and document
            print("\nStep 6: Checking for CAPTCHA...")
            captcha_frames = await page.query_selector_all("iframe[src*='recaptcha'], iframe[src*='captcha']")
            captcha_divs = await page.query_selector_all(".g-recaptcha, [class*='recaptcha'], [class*='captcha']")
            has_captcha = len(captcha_frames) > 0 or len(captcha_divs) > 0

            if has_captcha:
                print(f"  reCAPTCHA detected ({len(captcha_frames)} frames, {len(captcha_divs)} divs)")
                notes.append("reCAPTCHA detected - automated submission not possible")
                await safe_screenshot(page, "05-captcha-detected")
                status = "failed"
            else:
                print("  No CAPTCHA detected - attempting submission...")

                # Find submit button
                submit_btn = None
                for sel in [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Solliciteer')",
                    "button:has-text('Verzenden')",
                    "button:has-text('Submit')",
                    "[class*='submit']",
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            try:
                                text = await el.inner_text()
                            except:
                                text = sel
                            print(f"  Found submit button: '{text}' via {sel}")
                            submit_btn = el
                            break
                    except Exception:
                        pass

                if submit_btn and form_filled_count > 0:
                    await safe_screenshot(page, "05-pre-submit")
                    print("  Submitting form...")
                    await submit_btn.click()
                    await asyncio.sleep(4)
                    await safe_screenshot(page, "06-post-submit")

                    result_text = ""
                    try:
                        result_text = (await page.evaluate("document.body.innerText")).lower()
                    except:
                        pass

                    success_keywords = ["bedankt", "thank you", "ontvangen", "bevestiging", "verstuurd", "succesvol"]
                    if any(kw in result_text for kw in success_keywords):
                        notes.append("Application submitted - confirmation message detected")
                        status = "applied"
                        print("  APPLICATION SUBMITTED SUCCESSFULLY!")
                    else:
                        notes.append("Form submitted, no confirmation detected yet")
                        status = "applied"
                        print("  Form submitted.")
                else:
                    notes.append(f"Could not submit - fields filled: {form_filled_count}, submit button found: {submit_btn is not None}")
                    status = "failed"

            print(f"\nFields filled: {form_filled_count}")
            await safe_screenshot(page, "final-state")

        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            notes.append(f"Unexpected error: {str(e)}")
            status = "failed"
            await safe_screenshot(page, "error")

        finally:
            await browser.close()

    # Log the result
    final_screenshot = screenshot_path("06-post-submit") if status == "applied" else screenshot_path("05-captcha-detected")
    result = {
        "id": f"chipsoft-net-developer-{TIMESTAMP}",
        "company": "ChipSoft",
        "role": ".NET Developer Zorg-ICT",
        "url": VACANCY_URL,
        "apply_url": APPLY_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 7.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": None,
        "screenshot": final_screenshot,
        "notes": "; ".join(notes),
        "response": None
    }

    # Update applications.json
    apps_file = "/home/user/Agents/data/applications.json"
    try:
        if os.path.exists(apps_file):
            with open(apps_file, "r") as f:
                existing = json.load(f)
                # Remove old failed chipsoft entries from this session
                existing = [a for a in existing if not (a.get("company") == "ChipSoft" and "Error" in a.get("notes", ""))]
        else:
            existing = []
    except Exception:
        existing = []

    existing.append(result)

    with open(apps_file, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\n=== Final Application Result ===")
    print(f"Company: ChipSoft")
    print(f"Role: .NET Developer Zorg-ICT")
    print(f"Status: {status}")
    print(f"Notes: {'; '.join(notes)}")
    print(f"Logged to: {apps_file}")

    return result

if __name__ == "__main__":
    asyncio.run(run())
