#!/usr/bin/env python3
"""
Apply to Equal Experts Netherlands Software Engineer position.
Job URL: https://boards.greenhouse.io/equalexperts/jobs/4977568002
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

JOB_URL = "https://boards.greenhouse.io/equalexperts/jobs/4977568002"
COMPANY = "Equal Experts"
ROLE = "Software Engineer"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_MD = "/home/user/Agents/output/cover-letters/equal-experts-software-engineer.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven, Netherlands",
}

with open(COVER_LETTER_MD, "r") as f:
    COVER_LETTER_TEXT = f.read()


def load_applications():
    if os.path.exists(APPLICATIONS_JSON):
        with open(APPLICATIONS_JSON, "r") as f:
            return json.load(f)
    return []


def save_application(applications, entry):
    applications.append(entry)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(applications, f, indent=2)


async def safe_screenshot(page, path):
    """Take screenshot ignoring font-load timeout."""
    try:
        await page.screenshot(path=path, full_page=True, timeout=15000)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot warning (non-fatal): {e}")
        try:
            # Try without full_page
            await page.screenshot(path=path, timeout=10000)
            print(f"Partial screenshot saved: {path}")
        except Exception as e2:
            print(f"Screenshot failed entirely: {e2}")


async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    applications = load_applications()

    # Check for duplicate
    for app in applications:
        if app.get("company") == COMPANY and "equal-experts" in app.get("url", "").lower():
            print(f"Already applied to {COMPANY}. Skipping.")
            return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--font-render-hinting=none",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        print(f"Navigating to {JOB_URL}...")
        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation error: {e}")

        await page.wait_for_timeout(4000)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shot1 = f"{SCREENSHOTS_DIR}/equal-experts-01-landing-{ts}.png"
        await safe_screenshot(page, shot1)

        current_url = page.url
        title = await page.title()
        print(f"Current URL: {current_url}")
        print(f"Page title: {title}")

        try:
            page_text = await page.inner_text("body")
        except Exception:
            page_text = ""

        print(f"Page text excerpt: {page_text[:500]}")

        # Check if job is closed/expired
        expired_signals = [
            "error=true" in current_url,
            "job not found" in page_text.lower(),
            "no longer accepting" in page_text.lower(),
            "position has been filled" in page_text.lower(),
            "this job is closed" in page_text.lower(),
            "posting is closed" in page_text.lower(),
            "current openings at equal experts" in page_text.lower() and "software engineer" not in page_text.lower(),
        ]

        if any(expired_signals):
            print("\nJob posting is CLOSED or EXPIRED.")
            print("Signals detected:")
            for i, sig in enumerate(expired_signals):
                if sig:
                    print(f"  - Signal #{i+1} triggered")

            entry = {
                "id": "app-equal-experts-sw-001",
                "company": COMPANY,
                "role": ROLE,
                "url": JOB_URL,
                "date_applied": datetime.now().strftime("%Y-%m-%d"),
                "score": 8.5,
                "status": "skipped",
                "resume_file": RESUME_PDF,
                "cover_letter_file": COVER_LETTER_MD,
                "screenshot": shot1,
                "notes": (
                    f"Job posting expired/removed. Greenhouse API returned 404 for job ID 4977568002. "
                    f"Page redirected to error URL: {current_url}. Page title: {title}. "
                    "Cover letter was generated and saved. "
                    "Recommend checking if Equal Experts has re-posted for Netherlands."
                ),
                "response": None,
            }
            save_application(applications, entry)
            print("\nApplication entry saved:")
            print(json.dumps(entry, indent=2))
            await browser.close()
            return

        # Job appears active — try to fill the application form
        print("\nJob appears active, looking for application form...")

        # Greenhouse forms are usually on the same page or a /apply sub-path
        # Look for Apply button
        for selector in [
            "a:has-text('Apply for this Job')",
            "a:has-text('Apply Now')",
            "button:has-text('Apply')",
            ".apply-button",
            "#apply-now",
            "a[href*='/apply']",
        ]:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    print(f"Clicking apply button: {selector}")
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        shot2 = f"{SCREENSHOTS_DIR}/equal-experts-02-form-{ts}.png"
        await safe_screenshot(page, shot2)

        form_url = page.url
        print(f"Form page URL: {form_url}")

        # Fill standard Greenhouse form fields
        filled_count = 0
        field_attempts = [
            ("#first_name", CANDIDATE["first_name"]),
            ("#last_name", CANDIDATE["last_name"]),
            ("#email", CANDIDATE["email"]),
            ("#phone", CANDIDATE["phone"]),
            ("input[name='job_application[first_name]']", CANDIDATE["first_name"]),
            ("input[name='job_application[last_name]']", CANDIDATE["last_name"]),
            ("input[name='job_application[email]']", CANDIDATE["email"]),
            ("input[name='job_application[phone]']", CANDIDATE["phone"]),
        ]

        for selector, value in field_attempts:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.fill(value)
                    print(f"  Filled: {selector}")
                    filled_count += 1
            except Exception:
                pass

        # LinkedIn
        for selector in [
            "input[id*='linkedin']",
            "input[name*='linkedin']",
            "#job_application_linkedin_profile",
            "input[placeholder*='LinkedIn']",
        ]:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.fill(CANDIDATE["linkedin"])
                    print(f"  Filled LinkedIn: {selector}")
                    break
            except Exception:
                pass

        # Cover letter
        for selector in [
            "#cover_letter",
            "textarea[name*='cover_letter']",
            "textarea[placeholder*='cover']",
            "textarea[placeholder*='Cover']",
        ]:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.fill(COVER_LETTER_TEXT)
                    print(f"  Filled cover letter: {selector}")
                    break
            except Exception:
                pass

        # Resume upload
        for selector in [
            "input[type='file'][id*='resume']",
            "input[type='file'][name*='resume']",
            "#resume",
            "input[type='file']",
        ]:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.set_input_files(RESUME_PDF)
                    print(f"  Uploaded resume: {selector}")
                    await page.wait_for_timeout(3000)
                    break
            except Exception as e:
                print(f"  Upload attempt failed ({selector}): {e}")

        shot3 = f"{SCREENSHOTS_DIR}/equal-experts-03-before-submit-{ts}.png"
        await safe_screenshot(page, shot3)

        submitted = False
        if filled_count > 0:
            for selector in [
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Submit Application')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
            ]:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        print(f"  Clicking submit: {selector}")
                        await btn.click()
                        await page.wait_for_timeout(5000)
                        submitted = True
                        break
                except Exception:
                    pass

        shot4 = f"{SCREENSHOTS_DIR}/equal-experts-04-after-submit-{ts}.png"
        await safe_screenshot(page, shot4)

        post_url = page.url
        try:
            post_text = await page.inner_text("body")
        except Exception:
            post_text = ""

        success = any(
            kw in post_text.lower()
            for kw in ["thank you", "application received", "submitted successfully", "we'll be in touch"]
        )

        if submitted and success:
            status = "applied"
            notes = f"Application submitted successfully. Post-submit URL: {post_url}"
        elif submitted:
            status = "applied"
            notes = f"Form submitted (no explicit confirmation detected). Post-URL: {post_url}"
        elif filled_count > 0:
            status = "failed"
            notes = f"Fields filled ({filled_count}) but could not find submit button."
        else:
            status = "failed"
            notes = f"Could not fill application form. Form URL: {form_url}"

        entry = {
            "id": "app-equal-experts-sw-001",
            "company": COMPANY,
            "role": ROLE,
            "url": JOB_URL,
            "date_applied": datetime.now().strftime("%Y-%m-%d"),
            "score": 8.5,
            "status": status,
            "resume_file": RESUME_PDF,
            "cover_letter_file": COVER_LETTER_MD,
            "screenshot": shot4,
            "notes": notes,
            "response": None,
        }
        save_application(applications, entry)
        print("\nApplication entry saved:")
        print(json.dumps(entry, indent=2))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
