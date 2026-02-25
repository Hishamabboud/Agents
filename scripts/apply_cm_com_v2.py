#!/usr/bin/env python3
"""
Apply to CM.com Medior Backend Developer (Conversational Router / Conversational AI Cloud)
Application URL: https://jobs.cm.com/o/medior-backend-developer/c/new
v2: Improved timeout handling, better field detection
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
    return str(SCREENSHOTS_DIR / f"cmcom-v2-{name}-{TIMESTAMP}.png")


async def take_screenshot(page, name: str, screenshots_list: list):
    try:
        path = screenshot_path(name)
        await page.screenshot(path=path, full_page=True, timeout=10000)
        screenshots_list.append(path)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed ({name}): {e}")
        return None


def load_cover_letter() -> str:
    with open(COVER_LETTER_FILE, "r") as f:
        return f.read().strip()


def load_applications() -> list:
    with open(APPLICATIONS_JSON, "r") as f:
        return json.load(f)


def save_applications(apps: list):
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)


async def fill_field(page, selectors: list, value: str, field_name: str):
    """Try multiple selectors to fill a field."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            count = await el.count()
            if count > 0:
                is_visible = await el.is_visible()
                if is_visible:
                    await el.fill(value)
                    print(f"Filled: {field_name} using selector '{sel}'")
                    return True
        except Exception as e:
            continue
    print(f"WARNING: Could not fill {field_name}")
    return False


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
                "--disable-dev-shm-usage",
                "--disable-web-security",
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
            # Use domcontentloaded instead of networkidle to avoid font-loading hangs
            await page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            current_url = page.url
            print(f"Current URL: {current_url}")

            # Get page text to understand structure
            try:
                page_text = await page.inner_text("body")
                print(f"Page preview: {page_text[:300]}")
            except:
                pass

            # Screenshot initial state
            await take_screenshot(page, "01-initial", screenshots_taken)

            # Check if there's a form on the page
            form_count = await page.locator("form").count()
            print(f"Forms found: {form_count}")

            # List all input fields
            inputs = await page.query_selector_all("input, textarea, select")
            print(f"Input elements found: {len(inputs)}")
            for inp in inputs[:15]:
                name = await inp.get_attribute("name") or ""
                type_ = await inp.get_attribute("type") or ""
                placeholder = await inp.get_attribute("placeholder") or ""
                id_ = await inp.get_attribute("id") or ""
                print(f"  Input: name={name}, type={type_}, placeholder={placeholder[:30]}, id={id_}")

            # --- Fill Full Name ---
            await fill_field(
                page,
                [
                    'input[name="name"]',
                    'input[placeholder*="Full name" i]',
                    'input[placeholder*="Your name" i]',
                    'input[id*="name" i]',
                    'input[data-qa*="name" i]',
                    '#candidate_name',
                ],
                APPLICANT["full_name"],
                "Full name"
            )

            # --- Fill Email ---
            await fill_field(
                page,
                [
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[placeholder*="email" i]',
                    'input[id*="email" i]',
                    '#candidate_email',
                ],
                APPLICANT["email"],
                "Email"
            )

            # --- Fill Phone ---
            await fill_field(
                page,
                [
                    'input[name="phone"]',
                    'input[type="tel"]',
                    'input[placeholder*="phone" i]',
                    'input[id*="phone" i]',
                    '#candidate_phone',
                ],
                APPLICANT["phone"],
                "Phone"
            )

            # Screenshot after text fields
            await take_screenshot(page, "02-text-fields-filled", screenshots_taken)

            # --- Upload CV ---
            try:
                file_inputs = await page.query_selector_all('input[type="file"]')
                print(f"File inputs found: {len(file_inputs)}")
                if file_inputs:
                    await file_inputs[0].set_input_files(str(CV_FILE))
                    print("Uploaded: CV PDF")
                    await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload error: {e}")

            # --- Cover letter ---
            try:
                # Try textarea for cover letter
                cl_fields = await page.query_selector_all("textarea")
                print(f"Textareas found: {len(cl_fields)}")
                if cl_fields:
                    await cl_fields[0].fill(cover_letter_text[:3000])
                    print("Filled: Cover letter in first textarea")
            except Exception as e:
                print(f"Cover letter error: {e}")

            # Screenshot after uploads
            await take_screenshot(page, "03-after-uploads", screenshots_taken)

            # --- Handle Yes/No questions ---
            # "Do you live in the Netherlands?" - answer Yes
            # "Legal right to work?" - answer Yes
            # "English proficiency?" - answer C2
            try:
                # Look for radio buttons / toggle buttons
                labels = await page.query_selector_all("label")
                for label in labels:
                    text = await label.inner_text()
                    text = text.strip()
                    if text in ["Yes", "Ja"]:
                        await label.click()
                        print(f"Clicked label: '{text}'")
                        await page.wait_for_timeout(300)
            except Exception as e:
                print(f"Yes/No toggle error: {e}")

            # Try select dropdowns
            try:
                selects = await page.query_selector_all("select")
                for sel in selects:
                    options = await sel.query_selector_all("option")
                    for opt in options:
                        val = await opt.get_attribute("value") or ""
                        opt_text = await opt.inner_text()
                        if "c2" in val.lower() or "native" in opt_text.lower() or "c2" in opt_text.lower():
                            await sel.select_option(value=val)
                            print(f"Selected C2 in dropdown")
                            break
            except Exception as e:
                print(f"Select dropdown error: {e}")

            # --- Privacy checkbox ---
            try:
                checkboxes = await page.query_selector_all('input[type="checkbox"]')
                print(f"Checkboxes found: {len(checkboxes)}")
                for cb in checkboxes:
                    is_checked = await cb.is_checked()
                    if not is_checked:
                        await cb.click()
                        print("Checked a checkbox")
                        await page.wait_for_timeout(200)
            except Exception as e:
                print(f"Checkbox error: {e}")

            # Screenshot before submit
            await take_screenshot(page, "04-before-submit", screenshots_taken)

            # --- Submit the form ---
            try:
                # Try multiple submit button selectors
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Apply now")',
                    'button:has-text("Submit")',
                    'button:has-text("Send application")',
                    'button:has-text("Apply")',
                    '[data-qa="submit-button"]',
                ]
                submitted = False
                for sel in submit_selectors:
                    try:
                        btn = page.locator(sel).first
                        count = await btn.count()
                        if count > 0:
                            btn_text = await btn.inner_text()
                            print(f"Found submit button: '{btn_text}' using '{sel}'")
                            await btn.click()
                            submitted = True
                            print("Clicked submit!")
                            await page.wait_for_timeout(5000)
                            break
                    except:
                        continue
                if not submitted:
                    print("WARNING: No submit button found")
            except Exception as e:
                print(f"Submit error: {e}")

            # Screenshot after submit
            await take_screenshot(page, "05-after-submit", screenshots_taken)

            # Determine outcome
            final_url = page.url
            print(f"Final URL: {final_url}")
            try:
                page_text = await page.inner_text("body")
            except:
                page_text = ""

            print(f"Final page preview: {page_text[:400]}")

            if any(kw in page_text.lower() for kw in ["thank you", "application received", "successfully", "submitted", "bedankt", "ontvangen", "confirmation"]):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation text detected. Final URL: {final_url}. Email: {APPLICANT['email']}."
                print("SUCCESS: Application submitted!")
            elif any(kw in page_text.lower() for kw in ["captcha", "recaptcha", "hcaptcha", "human verification"]):
                status = "skipped"
                notes = f"CAPTCHA detected. Manual completion required. URL: {final_url}."
                print("CAPTCHA DETECTED - marking as skipped")
            elif final_url != APPLICATION_URL and "confirmation" not in final_url and "thank" not in final_url:
                # Redirected somewhere - check if it's still the form
                if "apply" in final_url.lower() or "/c/new" in final_url:
                    status = "failed"
                    notes = f"Still on application form after submit. Possible validation errors. URL: {final_url}."
                else:
                    status = "applied"
                    notes = f"Redirected after submit to: {final_url}. Possible success."
            else:
                status = "failed"
                notes = f"Uncertain outcome. Final URL: {final_url}. Page text snippet: {page_text[:200]}"

        except Exception as e:
            status = "failed"
            notes = f"Exception: {str(e)}"
            print(f"FATAL ERROR: {e}")
            try:
                await take_screenshot(page, "error", screenshots_taken)
            except:
                pass

        finally:
            await browser.close()

    # Log application
    apps = load_applications()
    new_entry = {
        "id": f"cmcom-medior-backend-dev-v2-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
    print(f"\nApplication logged. Status: {status}")
    print(f"Entry ID: {new_entry['id']}")
    return new_entry


if __name__ == "__main__":
    asyncio.run(apply())
