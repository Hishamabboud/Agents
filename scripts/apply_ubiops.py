#!/usr/bin/env python3
"""
Automated application script for UbiOps - Junior/Medior Python Software Engineer
Job URL: https://ubiops.jobs.personio.com/job/1576488?language=en
Uses Playwright to fill out and submit the Personio application form.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Candidate details
CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven",
    "linkedin": "https://www.linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
}

JOB_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en"
APPLY_URL = "https://ubiops.jobs.personio.com/job/1576488?language=en&apply"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/ubiops-python-engineer.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


async def screenshot(page, name):
    path = f"{SCREENSHOTS_DIR}/ubiops-{name}-{timestamp}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")
    return path


async def run():
    screenshots_taken = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            ignore_https_errors=True,
        )
        page = await context.new_page()

        try:
            print(f"Navigating to job page: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            s = await screenshot(page, "01-job-page")
            screenshots_taken.append(s)
            print(f"Page title: {await page.title()}")
            print(f"URL: {page.url}")

            # Accept cookies if present
            try:
                for btn_text in ["Accept all", "Accept All", "Accept", "Akkoord", "OK", "Agree"]:
                    cookie_btn = page.locator(f"button:has-text('{btn_text}')")
                    if await cookie_btn.count() > 0:
                        await cookie_btn.first.click()
                        await asyncio.sleep(1)
                        print(f"Accepted cookies: {btn_text}")
                        break
            except Exception:
                pass

            # Click the Apply button
            print("Looking for Apply button...")
            apply_selectors = [
                "a[href*='apply']",
                "button:has-text('Apply now')",
                "button:has-text('Apply')",
                "a:has-text('Apply now')",
                "a:has-text('Apply')",
                "[data-testid='apply-button']",
                ".apply-button",
                "[class*='apply']",
            ]
            apply_clicked = False
            for sel in apply_selectors:
                try:
                    btn = page.locator(sel).first
                    cnt = await btn.count()
                    if cnt > 0 and await btn.is_visible():
                        btn_text = await btn.inner_text()
                        print(f"Found apply button: '{btn_text}' ({sel})")
                        await btn.click()
                        await asyncio.sleep(3)
                        apply_clicked = True
                        print(f"Clicked apply button: {sel}")
                        break
                except Exception:
                    continue

            if not apply_clicked:
                # Navigate directly to apply URL
                print("Navigating directly to apply URL")
                await page.goto(APPLY_URL, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)

            s = await screenshot(page, "02-after-apply-click")
            screenshots_taken.append(s)
            print(f"Current URL: {page.url}")

            # Wait for the form to load
            try:
                await page.wait_for_selector("form, input[type='text'], input[type='email']", timeout=15000)
                print("Form found")
            except Exception:
                print("No form found within timeout")

            # Log all form inputs to understand the structure
            print("\n--- Analyzing form structure ---")
            all_inputs = await page.locator("input, textarea, select").all()
            print(f"Total form elements: {len(all_inputs)}")
            for inp in all_inputs:
                try:
                    tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                    itype = await inp.get_attribute("type") or tag
                    name_attr = await inp.get_attribute("name") or ""
                    id_attr = await inp.get_attribute("id") or ""
                    placeholder = await inp.get_attribute("placeholder") or ""
                    print(f"  {tag}[type={itype}] name='{name_attr}' id='{id_attr}' placeholder='{placeholder}'")
                except Exception as e:
                    print(f"  Error reading element: {e}")
            print("--- End form structure ---\n")

            # Fill fields intelligently
            await _fill_form(page, CANDIDATE, COVER_LETTER_TEXT)

            await asyncio.sleep(1)
            s = await screenshot(page, "03-form-filled")
            screenshots_taken.append(s)

            # Upload resume PDF
            print("Looking for file upload input...")
            file_inputs = await page.locator("input[type='file']").all()
            print(f"Found {len(file_inputs)} file inputs")
            for fi in file_inputs:
                try:
                    accept = await fi.get_attribute("accept") or ""
                    name_attr = await fi.get_attribute("name") or ""
                    print(f"  File input: accept={accept}, name={name_attr}")
                    await fi.set_input_files(RESUME_PATH)
                    print(f"  Uploaded resume to: {name_attr}")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"  File upload error: {e}")

            await asyncio.sleep(1)
            s = await screenshot(page, "04-after-upload")
            screenshots_taken.append(s)

            # Handle checkboxes (privacy policy, consent, GDPR)
            checkboxes = await page.locator("input[type='checkbox']").all()
            print(f"Found {len(checkboxes)} checkboxes")
            for cb in checkboxes:
                try:
                    checked = await cb.is_checked()
                    if not checked:
                        await cb.check()
                        print("  Checked checkbox")
                except Exception as e:
                    print(f"  Checkbox error: {e}")

            await asyncio.sleep(1)
            s = await screenshot(page, "05-before-submit")
            screenshots_taken.append(s)

            # Submit the form
            print("Looking for submit button...")
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "button:has-text('Apply now')",
                "button:has-text('Apply')",
                "button:has-text('Send application')",
                "button:has-text('Send')",
                "[data-testid='submit']",
                "[data-testid='apply-submit']",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    cnt = await btn.count()
                    if cnt > 0 and await btn.is_visible():
                        btn_text = await btn.inner_text()
                        print(f"Found submit button: '{btn_text}' ({sel})")
                        await btn.click()
                        await asyncio.sleep(4)
                        submitted = True
                        print("Submit button clicked")
                        break
                except Exception as e:
                    print(f"Submit selector {sel} failed: {e}")

            if not submitted:
                print("No submit button found with standard selectors, listing all visible buttons:")
                all_btns = await page.locator("button:visible").all()
                for btn in all_btns:
                    try:
                        txt = await btn.inner_text()
                        btn_type = await btn.get_attribute("type") or ""
                        print(f"  Button: '{txt}' type='{btn_type}'")
                    except Exception:
                        pass

            await asyncio.sleep(3)
            s = await screenshot(page, "06-after-submit")
            screenshots_taken.append(s)

            # Check for confirmation
            page_content = await page.content()
            page_url = page.url
            print(f"Post-submit URL: {page_url}")

            confirmation_indicators = [
                "thank you", "thanks", "application received", "successfully submitted",
                "we will be in touch", "confirmation", "we have received", "received your application",
                "danke", "bedankt", "ingediend"
            ]
            error_indicators = [
                "captcha", "robot", "error occurred", "please try again"
            ]

            confirmed = any(ind in page_content.lower() for ind in confirmation_indicators)
            has_captcha = any(ind in page_content.lower() for ind in error_indicators)

            if confirmed:
                status = "applied"
                notes = f"Application submitted successfully via Personio form. Confirmation detected on page. URL after submit: {page_url}"
                print("SUCCESS: Confirmation message detected!")
            elif has_captcha:
                status = "skipped"
                notes = f"Blocked by CAPTCHA or error. URL: {page_url}"
                print("BLOCKED: CAPTCHA or error detected")
            elif submitted:
                status = "applied"
                notes = f"Submit button clicked. No clear confirmation found but no errors detected. URL: {page_url}. Manual verification recommended."
                print("UNCERTAIN: Submit clicked, no clear confirmation")
            else:
                status = "failed"
                notes = f"Could not find submit button. URL: {page_url}"
                print("FAILED: Could not find submit button")

        except Exception as e:
            notes = f"Exception during application: {str(e)}"
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "99-error")
                screenshots_taken.append(s)
            except Exception:
                pass
        finally:
            await browser.close()

    # Log the application
    app_record = {
        "id": f"ubiops-python-engineer-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "UbiOps",
        "role": "Junior/Medior Python Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots_taken,
        "notes": notes,
        "response": None,
    }

    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except Exception:
        apps = []

    apps.append(app_record)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== APPLICATION LOG ===")
    print(json.dumps(app_record, indent=2))
    print(f"======================")
    print(f"Status: {status}")

    return app_record


async def _fill_form(page, candidate, cover_letter_text):
    """Smart form filler that inspects field labels/names to fill correctly."""

    # Get all visible inputs
    inputs = await page.locator("input[type='text']:visible, input[type='email']:visible, input[type='tel']:visible, input[type='url']:visible").all()
    textareas = await page.locator("textarea:visible").all()

    for inp in inputs:
        try:
            name_attr = (await inp.get_attribute("name") or "").lower()
            id_attr = (await inp.get_attribute("id") or "").lower()
            placeholder = (await inp.get_attribute("placeholder") or "").lower()

            # Try to get label text
            label_text = ""
            if id_attr:
                try:
                    label = page.locator(f"label[for='{id_attr}']")
                    if await label.count() > 0:
                        label_text = (await label.inner_text()).lower()
                except Exception:
                    pass

            combined = name_attr + " " + id_attr + " " + placeholder + " " + label_text

            current_val = await inp.input_value()
            if current_val:
                continue

            value = None
            if "first" in combined:
                value = candidate["first_name"]
            elif "last" in combined or "surname" in combined or "family" in combined:
                value = candidate["last_name"]
            elif "name" in combined and "company" not in combined and "user" not in combined:
                # Could be full name
                value = f"{candidate['first_name']} {candidate['last_name']}"
            elif "email" in combined:
                value = candidate["email"]
            elif "phone" in combined or "tel" in combined or "mobile" in combined:
                value = candidate["phone"]
            elif "linkedin" in combined:
                value = candidate["linkedin"]
            elif "github" in combined or "git" in combined:
                value = candidate["github"]
            elif "website" in combined or "portfolio" in combined or "url" in combined or "link" in combined:
                value = candidate["linkedin"]
            elif "city" in combined or "location" in combined or "residence" in combined:
                value = candidate["location"]
            elif "salary" in combined or "expectation" in combined or "desired" in combined:
                value = "60000"

            if value:
                await inp.click()
                await asyncio.sleep(0.1)
                await inp.fill(value)
                print(f"    Filled '{combined[:40].strip()}' = '{value[:40]}'")

        except Exception as e:
            print(f"    Error filling input: {e}")

    for ta in textareas:
        try:
            name_attr = (await ta.get_attribute("name") or "").lower()
            id_attr = (await ta.get_attribute("id") or "").lower()
            placeholder = (await ta.get_attribute("placeholder") or "").lower()
            current_val = await ta.input_value()
            combined = name_attr + " " + id_attr + " " + placeholder

            print(f"  Textarea: '{combined[:50].strip()}'")

            if current_val:
                print(f"    Already filled (len={len(current_val)})")
                continue

            await ta.click()
            await asyncio.sleep(0.1)
            await ta.fill(cover_letter_text)
            print(f"    Filled textarea with cover letter")

        except Exception as e:
            print(f"    Error filling textarea: {e}")


if __name__ == "__main__":
    result = asyncio.run(run())
    sys.exit(0 if result["status"] in ("applied", "action_required") else 1)
