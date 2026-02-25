#!/usr/bin/env python3
"""
Apply to Datenna Python Engineer - Data Acquisition role.
Uses Playwright to navigate and fill the application form.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Paths
SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")

# Applicant details
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

MOTIVATION = (
    "I am applying for the Python Engineer - Data Acquisition role at Datenna. "
    "At ASML I built Python automation tooling using Playwright-compatible browser automation, "
    "Pytest, and Locust to handle complex, dynamic test environments at scale. "
    "I have solid experience with HTTP fundamentals, session handling, BeautifulSoup, requests, "
    "and building resilient data pipelines. Currently I am building CogitatAI, an AI platform "
    "with a Python/Flask backend that includes real-time data acquisition pipelines and structured "
    "JSON output. I am based in Eindhoven and excited to contribute to Datenna's intelligence work."
)

APPLICATION_URL = "https://jobs.datenna.com/o/python-engineer-data-acquisition"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def screenshot(page, name):
    path = SCREENSHOTS_DIR / f"datenna-{name}-{ts()}.png"
    await page.screenshot(path=str(path), full_page=True)
    print(f"Screenshot saved: {path}")
    return str(path)


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"Navigating to {APPLICATION_URL}")
        try:
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Navigation error: {e}")
            await page.goto(APPLICATION_URL, timeout=30000)

        await asyncio.sleep(2)
        shot_job = await screenshot(page, "01-job-page")

        # Check page title/content
        title = await page.title()
        print(f"Page title: {title}")
        content = await page.content()
        print(f"Page URL: {page.url}")

        # Look for Apply button
        apply_selectors = [
            "a[href*='apply']",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "button:has-text('apply')",
            "[class*='apply']",
            "a:has-text('Apply now')",
            "button:has-text('Apply now')",
        ]

        apply_clicked = False
        for sel in apply_selectors:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    print(f"Found apply button with selector: {sel}")
                    await elem.click()
                    await asyncio.sleep(2)
                    apply_clicked = True
                    break
            except Exception:
                continue

        if apply_clicked:
            await screenshot(page, "02-after-apply-click")
            print(f"After clicking apply, URL: {page.url}")

        # Wait for form to be present
        await asyncio.sleep(2)
        current_url = page.url
        print(f"Current URL: {current_url}")

        # Take screenshot of current state
        await screenshot(page, "03-form-state")

        # Get all form inputs
        inputs = await page.locator("input, textarea, select").all()
        print(f"Found {len(inputs)} form elements")

        # Print all input names/types/placeholders for debugging
        for inp in inputs:
            try:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                itype = await inp.get_attribute("type") or ""
                name = await inp.get_attribute("name") or ""
                placeholder = await inp.get_attribute("placeholder") or ""
                input_id = await inp.get_attribute("id") or ""
                label_text = ""
                try:
                    # Try to get associated label
                    if input_id:
                        lbl = page.locator(f"label[for='{input_id}']")
                        if await lbl.count() > 0:
                            label_text = await lbl.first.inner_text()
                except Exception:
                    pass
                print(f"  {tag}[type={itype}] name={name} id={input_id} placeholder={placeholder} label={label_text}")
            except Exception as e:
                print(f"  Error reading input: {e}")

        # Attempt to fill the form
        # Strategy: fill by common patterns (name, email, phone, etc.)

        filled = []

        async def try_fill(selector, value, desc):
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=2000):
                    await elem.fill(value)
                    filled.append(desc)
                    print(f"  Filled {desc}: {value}")
                    return True
            except Exception as e:
                print(f"  Could not fill {desc}: {e}")
            return False

        # First name
        for sel in [
            "input[name*='first'][name*='name' i]",
            "input[name='firstName']",
            "input[name='first_name']",
            "input[placeholder*='First name' i]",
            "input[placeholder*='Voornaam' i]",
            "input[id*='first'][id*='name' i]",
        ]:
            if await try_fill(sel, APPLICANT["first_name"], "first_name"):
                break

        # Last name
        for sel in [
            "input[name*='last'][name*='name' i]",
            "input[name='lastName']",
            "input[name='last_name']",
            "input[placeholder*='Last name' i]",
            "input[placeholder*='Achternaam' i]",
            "input[id*='last'][id*='name' i]",
        ]:
            if await try_fill(sel, APPLICANT["last_name"], "last_name"):
                break

        # Full name (if separate first/last not found)
        for sel in [
            "input[name='name']",
            "input[name='fullName']",
            "input[name='full_name']",
            "input[placeholder*='Full name' i]",
            "input[placeholder*='Name' i]",
            "input[id='name']",
        ]:
            if await try_fill(sel, APPLICANT["full_name"], "full_name"):
                break

        # Email
        for sel in [
            "input[type='email']",
            "input[name*='email' i]",
            "input[placeholder*='email' i]",
            "input[id*='email' i]",
        ]:
            if await try_fill(sel, APPLICANT["email"], "email"):
                break

        # Phone
        for sel in [
            "input[type='tel']",
            "input[name*='phone' i]",
            "input[placeholder*='phone' i]",
            "input[placeholder*='Phone' i]",
            "input[id*='phone' i]",
        ]:
            if await try_fill(sel, APPLICANT["phone"], "phone"):
                break

        # LinkedIn
        for sel in [
            "input[name*='linkedin' i]",
            "input[placeholder*='linkedin' i]",
            "input[id*='linkedin' i]",
        ]:
            if await try_fill(sel, APPLICANT["linkedin"], "linkedin"):
                break

        # Cover letter / motivation textarea
        for sel in [
            "textarea[name*='cover' i]",
            "textarea[name*='motivation' i]",
            "textarea[name*='letter' i]",
            "textarea[placeholder*='cover' i]",
            "textarea[placeholder*='motivation' i]",
            "textarea[placeholder*='letter' i]",
            "textarea",
        ]:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    await elem.fill(MOTIVATION)
                    filled.append("motivation")
                    print(f"  Filled motivation textarea")
                    break
            except Exception:
                continue

        await screenshot(page, "04-form-filled-partial")

        # Handle CV upload
        cv_uploaded = False
        file_inputs = await page.locator("input[type='file']").all()
        print(f"Found {len(file_inputs)} file inputs")
        for i, fi in enumerate(file_inputs):
            try:
                name = await fi.get_attribute("name") or ""
                accept = await fi.get_attribute("accept") or ""
                print(f"  File input {i}: name={name} accept={accept}")
                # Upload CV to first file input or one that accepts PDFs/CVs
                if i == 0 or "pdf" in accept.lower() or "cv" in name.lower() or "resume" in name.lower():
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  Uploaded CV to file input {i}")
                    await asyncio.sleep(1)
                    break
            except Exception as e:
                print(f"  Error uploading to file input {i}: {e}")

        if not cv_uploaded:
            print("WARNING: Could not upload CV")

        await asyncio.sleep(1)
        await screenshot(page, "05-cv-uploaded")

        # Handle checkboxes (privacy/consent)
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"Found {len(checkboxes)} checkboxes")
        for i, cb in enumerate(checkboxes):
            try:
                name = await cb.get_attribute("name") or ""
                label_for = await cb.get_attribute("id") or ""
                is_checked = await cb.is_checked()
                print(f"  Checkbox {i}: name={name} id={label_for} checked={is_checked}")
                if not is_checked:
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Error with checkbox {i}: {e}")

        await asyncio.sleep(1)
        await screenshot(page, "06-before-submit")
        print("Pre-submit screenshot saved.")

        # Find and click submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Versturen')",
            "[class*='submit']",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    btn_text = await elem.inner_text()
                    print(f"Found submit button: '{btn_text}' with selector: {sel}")
                    await elem.click()
                    await asyncio.sleep(3)
                    submitted = True
                    break
            except Exception as e:
                print(f"  Submit selector {sel} failed: {e}")

        if submitted:
            await screenshot(page, "07-after-submit")
            print(f"After submit URL: {page.url}")
            # Check for success/confirmation
            body_text = await page.evaluate("document.body.innerText")
            print(f"Page text preview: {body_text[:500]}")

            success_indicators = [
                "thank", "confirm", "success", "received", "application",
                "bedankt", "ontvangen", "verstuurd",
            ]
            lower_text = body_text.lower()
            is_success = any(ind in lower_text for ind in success_indicators)

            if is_success:
                await screenshot(page, "08-confirmation")
                print("Application submitted successfully!")
                status = "applied"
                notes = "Successfully submitted application to Datenna Python Engineer - Data Acquisition"
            else:
                await screenshot(page, "08-post-submit-state")
                print("Submitted but could not confirm success. Check screenshot.")
                status = "applied"
                notes = "Form submitted; success confirmation unclear. Check screenshots."
        else:
            await screenshot(page, "07-submit-failed")
            print("ERROR: Could not find or click submit button")
            status = "failed"
            notes = "Could not find submit button on application form"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": page.url,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nResult: {json.dumps(result, indent=2)}")
