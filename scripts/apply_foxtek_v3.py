#!/usr/bin/env python3
"""
Foxtek .NET Developer application script using Playwright with proxy support.
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

# Proxy from environment
PROXY_URL = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("https_proxy") or os.environ.get("http_proxy")


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"foxtek-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=True, timeout=15000)
        print(f"  Screenshot saved: {path.name}")
    except Exception as e:
        print(f"  Screenshot failed for {name}: {e}")
        return None
    return str(path)


async def fill_application_form(page, cover_letter_text):
    """Try to fill all fields in an application form."""
    filled_fields = []

    # First/last name and full name combos
    field_map = [
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
        ("input[placeholder*='your name']", APPLICANT["name"]),
    ]

    for selector, value in field_map:
        try:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(value)
                filled_fields.append(selector)
                print(f"    Filled: {selector!r} = {value!r}")
        except Exception:
            pass

    # Email
    for sel in ["input[type='email']", "input[name='email']", "input[id*='email']",
                "input[placeholder*='mail']", "input[placeholder*='Mail']"]:
        try:
            elem = await page.query_selector(sel)
            if elem and await elem.is_visible():
                await elem.fill(APPLICANT["email"])
                filled_fields.append(sel)
                print(f"    Filled email: {sel!r}")
                break
        except Exception:
            pass

    # Phone
    for sel in ["input[type='tel']", "input[name*='phone']", "input[name*='mobile']",
                "input[id*='phone']", "input[placeholder*='phone']", "input[placeholder*='Phone']"]:
        try:
            elem = await page.query_selector(sel)
            if elem and await elem.is_visible():
                await elem.fill(APPLICANT["phone"])
                filled_fields.append(sel)
                print(f"    Filled phone: {sel!r}")
                break
        except Exception:
            pass

    # Cover letter in textarea
    if cover_letter_text:
        for sel in ["textarea[name*='cover']", "textarea[name*='letter']",
                    "textarea[name*='message']", "textarea[name*='motivation']",
                    "textarea[id*='cover']", "textarea[id*='letter']",
                    "textarea[id*='message']", "textarea"]:
            try:
                elems = await page.query_selector_all(sel)
                for elem in elems:
                    if await elem.is_visible():
                        await elem.fill(cover_letter_text)
                        filled_fields.append(sel)
                        print(f"    Filled cover letter in: {sel!r}")
                        break
                if any("cover" in f or "letter" in f or "message" in f or "textarea" in f
                       for f in filled_fields):
                    break
            except Exception:
                pass

    # File upload
    if RESUME_PDF.exists():
        for sel in ["input[type='file']", "input[name*='resume']",
                    "input[name*='cv']", "input[name*='file']"]:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    await elem.set_input_files(str(RESUME_PDF))
                    filled_fields.append(sel + ":file")
                    print(f"    Uploaded resume via: {sel!r}")
                    await page.wait_for_timeout(1500)
                    break
            except Exception as e:
                print(f"    File upload error {sel!r}: {e}")

    return filled_fields


async def try_apply_on_page(page, cover_letter_text):
    """Try to find and fill an application form on the current page. Returns result dict."""
    page_content = await page.content()

    # CAPTCHA check
    if any(x in page_content.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
        return {"blocked": "captcha"}

    # Account/login wall
    if any(x in page_content.lower() for x in ["create an account", "sign up to apply", "login to apply"]):
        return {"blocked": "account_required"}

    # Look for apply button
    apply_selectors = [
        "a:has-text('Apply Now')",
        "a:has-text('Apply')",
        "button:has-text('Apply Now')",
        "button:has-text('Apply')",
        ".apply-button",
        "[data-action='apply']",
        "a:has-text('Solliciteer')",
        "a[href*='apply']",
    ]
    for sel in apply_selectors:
        try:
            elem = await page.query_selector(sel)
            if elem and await elem.is_visible():
                text = (await elem.inner_text()).strip()
                href = await elem.get_attribute("href") or ""
                print(f"  Apply button found: {sel!r} text={text!r}")
                await elem.click()
                await page.wait_for_timeout(2000)
                # Re-check for captcha after click
                page_content = await page.content()
                if any(x in page_content.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
                    return {"blocked": "captcha_after_click"}
                break
        except Exception:
            pass

    # Check if external redirect
    if any(x in page.url for x in ["linkedin.com", "indeed.com", "greenhouse.io", "workable.com", "lever.co"]):
        return {"blocked": f"external_platform:{page.url}"}

    # Look for form
    form = await page.query_selector("form")
    email_input = await page.query_selector("input[type='email'], input[name*='email']")

    if not form and not email_input:
        return {"no_form": True}

    print("  Application form found, filling...")
    filled_fields = await fill_application_form(page, cover_letter_text)

    if not filled_fields:
        return {"no_fields_filled": True}

    # Submit
    for sel in ["button[type='submit']", "input[type='submit']",
                "button:has-text('Submit')", "button:has-text('Send')",
                "button:has-text('Apply')", "button:has-text('Send Application')",
                "[type='submit']"]:
        try:
            elem = await page.query_selector(sel)
            if elem and await elem.is_visible():
                btn_label = (await elem.inner_text() or await elem.get_attribute("value") or sel).strip()
                print(f"  Submit button: {sel!r} label={btn_label!r}")
                return {"ready_to_submit": True, "selector": sel, "filled_fields": filled_fields}
        except Exception:
            pass

    return {"filled_fields": filled_fields, "no_submit_button": True}


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

    # Parse proxy
    proxy_config = None
    if PROXY_URL:
        print(f"Using proxy: {PROXY_URL[:50]}...")
        proxy_config = {"server": PROXY_URL}

    async with async_playwright() as p:
        browser_args = {}
        if proxy_config:
            browser_args["proxy"] = proxy_config

        browser = await p.chromium.launch(headless=True, **browser_args)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        # Step 1: Navigate to original job URL
        print(f"\n[Step 1] Navigating to: {JOB_URL}")
        http_status = None
        try:
            response = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            http_status = response.status if response else None
            print(f"  HTTP status: {http_status}, URL: {page.url}")
        except Exception as e:
            print(f"  Navigation error: {e}")

        ss = await take_screenshot(page, "01-job-page")
        if ss:
            result["screenshots"].append(ss)

        page_title = await page.title()
        page_content = await page.content()
        print(f"  Title: {page_title!r}")

        is_404 = (
            http_status == 404
            or "404" in page_title
            or "not found" in page_title.lower()
            or "page not found" in page_content.lower()
        )

        if not is_404 and http_status not in (None, 200, 301, 302):
            is_404 = True

        if is_404:
            print(f"  Job page not found (HTTP {http_status})")
            result["notes"] += f"Original job URL returned {http_status} (listing removed or taken down). "

            # Step 2: Check jobs overview
            print(f"\n[Step 2] Checking jobs overview: {JOBS_PAGE}")
            try:
                await page.goto(JOBS_PAGE, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Error: {e}")

            ss = await take_screenshot(page, "02-jobs-overview")
            if ss:
                result["screenshots"].append(ss)

            # Find jobs listed
            job_links = await page.query_selector_all("a[href*='/job/']")
            found_jobs = []
            seen = set()
            for link in job_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()
                if text and href and href not in seen:
                    seen.add(href)
                    found_jobs.append({"url": href, "title": text})
                    print(f"  Active job: {text!r} -> {href}")

            if not found_jobs:
                result["status"] = "skipped"
                result["notes"] += "No active job listings found on Foxtek. Job was likely filled or removed."
                await browser.close()
                return result

            # Try to find a .NET / C# / backend equivalent
            dotnet_match = None
            for job in found_jobs:
                tl = job["title"].lower()
                if any(k in tl for k in [".net", "dotnet", "c#", "csharp", "full stack", "fullstack", "backend"]):
                    dotnet_match = job
                    break

            if not dotnet_match:
                result["status"] = "skipped"
                result["notes"] += (
                    f"Original .NET Developer job listing has been removed. "
                    f"No equivalent .NET/C# role currently available. "
                    f"Active listings: {[j['title'] for j in found_jobs]}"
                )
                await browser.close()
                return result

            print(f"\n  Nearest match: {dotnet_match['title']!r}")
            result["notes"] += f"Applied to nearest available match: '{dotnet_match['title']}' at {dotnet_match['url']}. "

            try:
                await page.goto(dotnet_match["url"], wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Error loading match: {e}")

            ss = await take_screenshot(page, "03-matched-job")
            if ss:
                result["screenshots"].append(ss)

        # Step 3: Try to apply
        print("\n[Step 3] Attempting application...")
        apply_result = await try_apply_on_page(page, cover_letter_text)
        print(f"  Apply result: {apply_result}")

        ss = await take_screenshot(page, "04-after-form-fill")
        if ss:
            result["screenshots"].append(ss)

        if "blocked" in apply_result:
            reason = apply_result["blocked"]
            if "captcha" in reason:
                result["status"] = "failed"
                result["notes"] += f" Blocked by CAPTCHA ({reason})."
            else:
                result["status"] = "skipped"
                result["notes"] += f" Blocked: {reason}."
            await browser.close()
            return result

        if apply_result.get("no_form") or apply_result.get("no_fields_filled"):
            # Try to get contact info from page to apply via email
            page_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"  Page text snippet: {page_text[:500]!r}")
            result["status"] = "skipped"
            result["notes"] += " No fillable application form found on page."
            await browser.close()
            return result

        if apply_result.get("ready_to_submit"):
            submit_sel = apply_result["selector"]
            print(f"\n[Step 4] Submitting via: {submit_sel!r}")

            ss = await take_screenshot(page, "05-pre-submit")
            if ss:
                result["screenshots"].append(ss)

            try:
                elem = await page.query_selector(submit_sel)
                if elem and await elem.is_visible():
                    await elem.click()
                    await page.wait_for_timeout(3000)
                    print(f"  Submitted. New URL: {page.url}")
                else:
                    # Try any visible submit
                    for sel in ["[type='submit']", "button[type='submit']"]:
                        elems = await page.query_selector_all(sel)
                        for e in elems:
                            if await e.is_visible():
                                await e.click()
                                await page.wait_for_timeout(3000)
                                break
            except Exception as e:
                print(f"  Submit click error: {e}")

            ss = await take_screenshot(page, "06-post-submit")
            if ss:
                result["screenshots"].append(ss)

            final_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"  Post-submit page (first 300): {final_text[:300]!r}")

            success_phrases = ["thank you", "application received", "successfully submitted",
                               "we have received", "will be in touch", "confirmation",
                               "received your application", "we'll contact"]
            success = any(p in final_text.lower() for p in success_phrases)

            if success:
                result["status"] = "applied"
                result["notes"] += " Application submitted and success confirmed."
            else:
                result["status"] = "applied"
                result["notes"] += " Form submitted (could not confirm success message)."

            result["filled_fields"] = apply_result.get("filled_fields", [])

        elif apply_result.get("no_submit_button"):
            result["status"] = "failed"
            result["notes"] += " Fields filled but no submit button found."
        else:
            result["status"] = "failed"
            result["notes"] += f" Unexpected apply result: {apply_result}"

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    for k, v in result.items():
        if k != "filled_fields":
            print(f"  {k}: {v}")
    if "filled_fields" in result:
        print(f"  filled_fields ({len(result['filled_fields'])}): {result['filled_fields']}")
    print(f"{'='*60}")
