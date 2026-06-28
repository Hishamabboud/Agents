#!/usr/bin/env python3
"""
Foxtek .NET Developer application script using Playwright.
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
    "phone": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
}

JOB_URL = "https://www.foxtekrs.com/job/dot-net-developer-1"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"foxtek-{name}-{ts()}.png"
    await page.screenshot(path=str(path), full_page=True)
    print(f"Screenshot saved: {path}")
    return str(path)


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Read cover letter text
    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        cover_letter_text = COVER_LETTER_MD.read_text().strip()
        print(f"Cover letter loaded ({len(cover_letter_text)} chars)")
    else:
        print(f"WARNING: Cover letter not found at {COVER_LETTER_MD}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Navigating to: {JOB_URL}")
        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Navigation error: {e}")
            await take_screenshot(page, "01-error")
            await browser.close()
            return {"status": "failed", "reason": str(e)}

        await take_screenshot(page, "01-job-page")
        print(f"Page title: {await page.title()}")
        print(f"Current URL: {page.url}")

        # Check for CAPTCHA
        page_content = await page.content()
        if any(x in page_content.lower() for x in ["captcha", "recaptcha", "hcaptcha", "cloudflare"]):
            print("CAPTCHA detected on job page")
            await take_screenshot(page, "captcha-detected")
            await browser.close()
            return {"status": "failed", "reason": "CAPTCHA detected on job page"}

        # Look for Apply button
        apply_selectors = [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply Now')",
            "button:has-text('Apply Now')",
            "a[href*='apply']",
            ".apply-button",
            "#apply-button",
            "[data-action='apply']",
            "a:has-text('Solliciteer')",
            "button:has-text('Solliciteer')",
        ]

        apply_clicked = False
        for selector in apply_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    print(f"Found apply element with selector: {selector}")
                    text = await elem.inner_text()
                    href = await elem.get_attribute("href") if await elem.get_attribute("href") else ""
                    print(f"  Text: {text!r}, href: {href!r}")
                    await elem.click()
                    await page.wait_for_timeout(2000)
                    apply_clicked = True
                    break
            except Exception as e:
                print(f"  Selector {selector} error: {e}")
                continue

        if not apply_clicked:
            # Check if page itself is the application form
            print("No explicit apply button found, checking if page has a form...")
            form = await page.query_selector("form")
            if form:
                print("Form found directly on job page")
            else:
                print("No form found either. Checking page structure...")
                # Try scrolling to find content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await page.wait_for_timeout(1000)

        await take_screenshot(page, "02-after-apply-click")
        print(f"Current URL after apply click: {page.url}")

        # Check for CAPTCHA after click
        page_content = await page.content()
        if any(x in page_content.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
            print("CAPTCHA detected after apply click")
            await take_screenshot(page, "captcha-after-click")
            await browser.close()
            return {"status": "failed", "reason": "CAPTCHA detected after apply click"}

        # Check if redirected to external site (login required)
        current_url = page.url
        if "linkedin.com" in current_url or "indeed.com" in current_url:
            print(f"Redirected to external platform: {current_url}")
            await take_screenshot(page, "external-redirect")
            await browser.close()
            return {"status": "skipped", "reason": f"Redirected to external platform: {current_url}"}

        # Check for login/account creation requirement
        if any(x in page_content.lower() for x in ["create account", "sign up", "register", "log in", "login required"]):
            print("Account creation/login required")
            await take_screenshot(page, "login-required")
            await browser.close()
            return {"status": "skipped", "reason": "Account creation/login required"}

        # Look for form fields
        print("Looking for application form fields...")

        # Try to fill name fields
        name_selectors = [
            ("input[name*='name'][name*='first']", APPLICANT["first_name"]),
            ("input[id*='first']", APPLICANT["first_name"]),
            ("input[placeholder*='First']", APPLICANT["first_name"]),
            ("input[name*='name'][name*='last']", APPLICANT["last_name"]),
            ("input[id*='last']", APPLICANT["last_name"]),
            ("input[placeholder*='Last']", APPLICANT["last_name"]),
            ("input[name='name']", APPLICANT["name"]),
            ("input[name='full_name']", APPLICANT["name"]),
            ("input[placeholder*='Name']", APPLICANT["name"]),
            ("input[placeholder*='Your name']", APPLICANT["name"]),
        ]

        filled_fields = []
        for selector, value in name_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    await elem.fill(value)
                    filled_fields.append(selector)
                    print(f"Filled: {selector} = {value!r}")
            except Exception as e:
                pass

        # Email
        email_selectors = [
            "input[type='email']",
            "input[name='email']",
            "input[id*='email']",
            "input[placeholder*='email']",
            "input[placeholder*='Email']",
        ]
        for selector in email_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    await elem.fill(APPLICANT["email"])
                    filled_fields.append(selector)
                    print(f"Filled email: {selector}")
                    break
            except Exception:
                pass

        # Phone
        phone_selectors = [
            "input[type='tel']",
            "input[name*='phone']",
            "input[id*='phone']",
            "input[placeholder*='phone']",
            "input[placeholder*='Phone']",
            "input[name*='mobile']",
        ]
        for selector in phone_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    await elem.fill(APPLICANT["phone"])
                    filled_fields.append(selector)
                    print(f"Filled phone: {selector}")
                    break
            except Exception:
                pass

        # Cover letter / message textarea
        cover_letter_selectors = [
            "textarea[name*='cover']",
            "textarea[name*='letter']",
            "textarea[name*='message']",
            "textarea[id*='cover']",
            "textarea[id*='letter']",
            "textarea[id*='message']",
            "textarea",
        ]
        if cover_letter_text:
            for selector in cover_letter_selectors:
                try:
                    elems = await page.query_selector_all(selector)
                    for elem in elems:
                        if await elem.is_visible():
                            await elem.fill(cover_letter_text)
                            filled_fields.append(selector)
                            print(f"Filled cover letter: {selector}")
                            break
                    if selector in filled_fields:
                        break
                except Exception:
                    pass

        # Resume upload
        if RESUME_PDF.exists():
            file_input_selectors = [
                "input[type='file']",
                "input[name*='resume']",
                "input[name*='cv']",
                "input[name*='file']",
            ]
            for selector in file_input_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        await elem.set_input_files(str(RESUME_PDF))
                        filled_fields.append(f"file:{selector}")
                        print(f"Uploaded resume via: {selector}")
                        await page.wait_for_timeout(1000)
                        break
                except Exception as e:
                    print(f"File upload error with {selector}: {e}")

        print(f"Fields filled: {filled_fields}")
        await take_screenshot(page, "03-form-filled")

        # Submit the form
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "button:has-text('Apply')",
            "button:has-text('Send Application')",
            "[type='submit']",
        ]

        submitted = False
        if filled_fields:
            for selector in submit_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        text = await elem.inner_text() if await elem.get_attribute("value") is None else await elem.get_attribute("value")
                        print(f"Found submit button: {selector}, text: {text!r}")
                        await take_screenshot(page, "04-pre-submit")
                        await elem.click()
                        await page.wait_for_timeout(3000)
                        submitted = True
                        break
                except Exception as e:
                    print(f"Submit error with {selector}: {e}")
        else:
            print("No fields were filled, skipping submit to avoid blank submission")

        await take_screenshot(page, "05-final-state")
        print(f"Final URL: {page.url}")
        final_content = await page.content()

        # Check for success indicators
        success_indicators = ["thank you", "application received", "successfully submitted",
                               "confirmation", "we'll be in touch", "received your application"]
        success = any(x in final_content.lower() for x in success_indicators)

        if success:
            print("SUCCESS: Application submitted successfully")
            status = "applied"
        elif submitted:
            print("Form submitted but could not confirm success")
            status = "applied"
        elif not filled_fields:
            print("No form fields found - page may require account or has unusual structure")
            status = "skipped"
            if "account" in final_content.lower() or "login" in final_content.lower():
                return {"status": "skipped", "reason": "Application requires account creation"}
        else:
            status = "failed"

        await browser.close()
        return {
            "status": status,
            "filled_fields": filled_fields,
            "submitted": submitted,
            "success_detected": success,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nResult: {result}")
