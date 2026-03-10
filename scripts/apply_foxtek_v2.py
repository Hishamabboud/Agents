#!/usr/bin/env python3
"""
Foxtek .NET Developer application script using Playwright.
Handles the case where the original URL may be down.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PDF = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
COVER_LETTER_MD = Path("/home/user/Agents/output/cover-letters/foxtek-net-developer.md")

APPLICANT = {
    "name": "Hisham Abboud",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31064841 2838",
    "location": "Eindhoven, Netherlands",
}

JOB_URL = "https://www.foxtekrs.com/job/dot-net-developer-1"
JOBS_PAGE = "https://www.foxtekrs.com/jobs/"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"foxtek-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=True)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed for {name}: {e}")
        path = None
    return str(path) if path else None


async def fill_application_form(page, cover_letter_text):
    """Try to fill and submit an application form on the current page."""
    filled_fields = []

    # Try first/last name fields
    name_pairs = [
        ("input[name*='first_name']", APPLICANT["first_name"]),
        ("input[name*='firstname']", APPLICANT["first_name"]),
        ("input[id*='first_name']", APPLICANT["first_name"]),
        ("input[id*='firstname']", APPLICANT["first_name"]),
        ("input[placeholder*='First name']", APPLICANT["first_name"]),
        ("input[placeholder*='First Name']", APPLICANT["first_name"]),
        ("input[name*='last_name']", APPLICANT["last_name"]),
        ("input[name*='lastname']", APPLICANT["last_name"]),
        ("input[id*='last_name']", APPLICANT["last_name"]),
        ("input[id*='lastname']", APPLICANT["last_name"]),
        ("input[placeholder*='Last name']", APPLICANT["last_name"]),
        ("input[placeholder*='Last Name']", APPLICANT["last_name"]),
        ("input[name='name']", APPLICANT["name"]),
        ("input[id='name']", APPLICANT["name"]),
        ("input[placeholder='Name']", APPLICANT["name"]),
        ("input[placeholder='Full Name']", APPLICANT["name"]),
        ("input[placeholder*='Your name']", APPLICANT["name"]),
    ]

    for selector, value in name_pairs:
        try:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(value)
                filled_fields.append(f"{selector}={value!r}")
                print(f"  Filled: {selector} = {value!r}")
        except Exception:
            pass

    # Email
    for selector in ["input[type='email']", "input[name='email']", "input[id*='email']",
                      "input[placeholder*='mail']", "input[placeholder*='Mail']"]:
        try:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(APPLICANT["email"])
                filled_fields.append(f"{selector}=email")
                print(f"  Filled email: {selector}")
                break
        except Exception:
            pass

    # Phone
    for selector in ["input[type='tel']", "input[name*='phone']", "input[name*='mobile']",
                     "input[id*='phone']", "input[placeholder*='phone']", "input[placeholder*='Phone']"]:
        try:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(APPLICANT["phone"])
                filled_fields.append(f"{selector}=phone")
                print(f"  Filled phone: {selector}")
                break
        except Exception:
            pass

    # Cover letter / message area
    if cover_letter_text:
        for selector in ["textarea[name*='cover']", "textarea[name*='letter']",
                         "textarea[name*='message']", "textarea[name*='motivation']",
                         "textarea[id*='cover']", "textarea[id*='letter']",
                         "textarea[id*='message']", "textarea"]:
            try:
                elems = await page.query_selector_all(selector)
                for elem in elems:
                    if await elem.is_visible():
                        await elem.fill(cover_letter_text)
                        filled_fields.append(f"{selector}=cover_letter")
                        print(f"  Filled cover letter in: {selector}")
                        break
                if any("cover_letter" in f for f in filled_fields):
                    break
            except Exception:
                pass

    # Resume upload
    if RESUME_PDF.exists():
        for selector in ["input[type='file']", "input[name*='resume']",
                         "input[name*='cv']", "input[name*='file']"]:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    await elem.set_input_files(str(RESUME_PDF))
                    filled_fields.append(f"{selector}=resume")
                    print(f"  Uploaded resume via: {selector}")
                    await page.wait_for_timeout(1500)
                    break
            except Exception as e:
                print(f"  File upload error {selector}: {e}")

    return filled_fields


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        cover_letter_text = COVER_LETTER_MD.read_text().strip()
        print(f"Cover letter loaded ({len(cover_letter_text)} chars)")

    result = {
        "company": "Foxtek",
        "role": ".NET Developer",
        "original_url": JOB_URL,
        "status": "unknown",
        "screenshots": [],
        "notes": "",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # --- Step 1: Try the original job URL ---
        print(f"\n[Step 1] Navigating to job URL: {JOB_URL}")
        try:
            response = await page.goto(JOB_URL, wait_until="commit", timeout=20000)
            await page.wait_for_timeout(3000)
            status_code = response.status if response else None
            print(f"  HTTP status: {status_code}, URL: {page.url}")
        except Exception as e:
            print(f"  Navigation error: {e}")
            status_code = None

        ss = await take_screenshot(page, "01-job-url")
        if ss:
            result["screenshots"].append(ss)

        page_title = await page.title()
        print(f"  Page title: {page_title!r}")

        page_content = await page.content()
        is_404 = (
            status_code == 404
            or "404" in page_title
            or "not found" in page_title.lower()
            or "page not found" in page_content.lower()
        )

        if is_404:
            print("  Job URL returned 404 — job listing has been removed.")
            result["notes"] += "Original job URL returned 404 (listing removed). "

            # --- Step 2: Check jobs overview page ---
            print(f"\n[Step 2] Checking jobs overview: {JOBS_PAGE}")
            try:
                await page.goto(JOBS_PAGE, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Error loading jobs page: {e}")

            ss = await take_screenshot(page, "02-jobs-overview")
            if ss:
                result["screenshots"].append(ss)

            # Look for .NET / C# related jobs
            job_links = await page.query_selector_all("a[href*='/job/']")
            found_jobs = []
            for link in job_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()
                if text and href:
                    found_jobs.append({"url": href, "title": text})
                    print(f"  Found job: {text!r} -> {href}")

            # Look for a C# or .NET match as fallback
            dotnet_match = None
            for job in found_jobs:
                title_lower = job["title"].lower()
                if any(k in title_lower for k in [".net", "dotnet", "c#", "csharp", "full stack", "backend"]):
                    dotnet_match = job
                    break

            if not found_jobs:
                print("  No active job listings found on Foxtek.")
                result["status"] = "skipped"
                result["notes"] += "No active job listings found. Job was likely filled or removed."
                await browser.close()
                return result

            if not dotnet_match:
                print("  No matching .NET/C# job found. Available jobs:")
                for j in found_jobs:
                    print(f"    - {j['title']}: {j['url']}")
                result["status"] = "skipped"
                result["notes"] += f"Job listing removed. No equivalent .NET/C# role currently available. Active jobs: {[j['title'] for j in found_jobs]}"
                await browser.close()
                return result

            print(f"\n  Found possible replacement job: {dotnet_match['title']!r}")
            result["notes"] += f"Applying to nearest match: {dotnet_match['title']}"

            try:
                await page.goto(dotnet_match["url"], wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Error loading replacement job page: {e}")

            ss = await take_screenshot(page, "03-replacement-job")
            if ss:
                result["screenshots"].append(ss)

        # --- Check for CAPTCHA or login walls ---
        page_content = await page.content()
        if any(x in page_content.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
            print("CAPTCHA detected!")
            ss = await take_screenshot(page, "captcha-blocked")
            if ss:
                result["screenshots"].append(ss)
            result["status"] = "failed"
            result["notes"] += " CAPTCHA encountered."
            await browser.close()
            return result

        if any(x in page_content.lower() for x in ["create an account", "create account", "sign up to apply", "login to apply"]):
            print("Account creation required!")
            result["status"] = "skipped"
            result["notes"] += " Account creation required to apply."
            await browser.close()
            return result

        # --- Step 3: Look for Apply button ---
        print("\n[Step 3] Looking for Apply button...")
        apply_clicked = False
        apply_selectors = [
            "a:has-text('Apply Now')",
            "a:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Apply')",
            "a[href*='apply']",
            ".apply-button",
            "#apply",
            "[data-action='apply']",
            "a:has-text('Solliciteer')",
        ]
        for selector in apply_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    text = await elem.inner_text()
                    href = await elem.get_attribute("href") or ""
                    print(f"  Found: {selector} text={text!r} href={href!r}")
                    await elem.click()
                    await page.wait_for_timeout(2000)
                    apply_clicked = True
                    print(f"  Clicked. New URL: {page.url}")
                    break
            except Exception as e:
                pass

        ss = await take_screenshot(page, "04-after-apply-click")
        if ss:
            result["screenshots"].append(ss)

        # Check if redirected to external site
        current_url = page.url
        if "linkedin.com" in current_url or "indeed.com" in current_url or "greenhouse.io" in current_url:
            print(f"Redirected to external platform: {current_url}")
            result["status"] = "skipped"
            result["notes"] += f" Redirected to external platform: {current_url}"
            await browser.close()
            return result

        # Check for form on the page
        print("\n[Step 4] Looking for application form...")
        page_content = await page.content()

        form_elem = await page.query_selector("form")
        has_form = form_elem is not None

        # Check for email input as proxy for form
        email_input = await page.query_selector("input[type='email'], input[name*='email']")
        has_email_input = email_input is not None

        if not has_form and not has_email_input:
            print("  No application form found on current page.")
            # Print some of the visible text to understand what we see
            visible_text = await page.evaluate("() => document.body.innerText")
            print(f"  Page text preview: {visible_text[:500]!r}")
            result["status"] = "skipped"
            result["notes"] += " No application form found. Job may require emailing directly or using an external system."
            ss = await take_screenshot(page, "05-no-form")
            if ss:
                result["screenshots"].append(ss)
            await browser.close()
            return result

        print(f"  Form found: {has_form}, Email input found: {has_email_input}")

        # --- Step 5: Fill form ---
        print("\n[Step 5] Filling application form...")
        filled_fields = await fill_application_form(page, cover_letter_text)
        print(f"  Filled {len(filled_fields)} field(s)")

        ss = await take_screenshot(page, "05-form-filled")
        if ss:
            result["screenshots"].append(ss)

        if not filled_fields:
            print("  No fields were filled. Aborting submit to avoid blank form.")
            result["status"] = "skipped"
            result["notes"] += " No form fields could be filled (form structure unrecognized)."
            await browser.close()
            return result

        # --- Step 6: Submit ---
        print("\n[Step 6] Submitting application...")
        submitted = False
        for selector in ["button[type='submit']", "input[type='submit']",
                         "button:has-text('Submit')", "button:has-text('Send')",
                         "button:has-text('Apply')", "button:has-text('Send Application')",
                         "[type='submit']"]:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    btn_text = await elem.inner_text() if not await elem.get_attribute("value") else await elem.get_attribute("value")
                    print(f"  Found submit: {selector}, text={btn_text!r}")
                    ss = await take_screenshot(page, "06-pre-submit")
                    if ss:
                        result["screenshots"].append(ss)
                    await elem.click()
                    await page.wait_for_timeout(3000)
                    submitted = True
                    print(f"  Submitted. New URL: {page.url}")
                    break
            except Exception as e:
                print(f"  Submit error {selector}: {e}")

        ss = await take_screenshot(page, "07-post-submit")
        if ss:
            result["screenshots"].append(ss)

        # Check for success
        final_content = await page.content()
        final_text = await page.evaluate("() => document.body.innerText")
        success_phrases = ["thank you", "application received", "successfully submitted",
                           "we have received", "confirmation", "we'll be in touch",
                           "will be in touch", "received your application"]
        success_detected = any(p in final_text.lower() for p in success_phrases)

        print(f"  Submitted: {submitted}, Success detected: {success_detected}")
        print(f"  Final page text (first 300 chars): {final_text[:300]!r}")

        if success_detected:
            result["status"] = "applied"
            result["notes"] += " Application submitted successfully."
        elif submitted:
            result["status"] = "applied"
            result["notes"] += " Form submitted (success confirmation not detected)."
        else:
            result["status"] = "failed"
            result["notes"] += " Could not submit form."

        result["filled_fields"] = filled_fields

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n{'='*60}")
    print(f"FINAL RESULT:")
    for k, v in result.items():
        if k != "filled_fields":
            print(f"  {k}: {v}")
    print(f"{'='*60}")
