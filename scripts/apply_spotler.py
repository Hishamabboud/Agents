#!/usr/bin/env python3
"""
Spotler Medior Software Engineer application script.
Navigates to spotler.com careers, finds the job listing (or open application),
fills the form, uploads resume, and submits.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/spotler-medior-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

# Read cover letter text
with open(COVER_LETTER_PATH, "r") as f:
    COVER_LETTER_TEXT = f.read()

async def screenshot(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")
    return path

async def main():
    screenshots_taken = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        # Mask webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        # --- Step 1: Navigate to careers jobs page ---
        print("[1] Navigating to Spotler careers page...")
        await page.goto("https://spotler.com/careers/jobs", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        s = await screenshot(page, "01-careers-jobs")
        screenshots_taken.append(s)
        print(f"  Page title: {await page.title()}")
        print(f"  URL: {page.url}")

        # --- Step 2: Look for Medior Software Engineer listing ---
        print("[2] Looking for Medior Software Engineer job...")
        page_content = await page.content()

        # Check if the specific job exists
        job_found = False
        if "medior" in page_content.lower() or "software engineer" in page_content.lower():
            print("  Found software engineer reference on page!")
            # Try to find and click the link
            try:
                link = page.locator("a:has-text('Medior Software Engineer'), a:has-text('medior software'), a[href*='medior-software']").first
                await link.wait_for(timeout=5000)
                await link.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2000)
                job_found = True
                s = await screenshot(page, "02-job-listing")
                screenshots_taken.append(s)
                print(f"  Navigated to job: {page.url}")
            except Exception as e:
                print(f"  Could not click job link: {e}")

        if not job_found:
            # Try direct URL
            print("  Trying direct job URL...")
            await page.goto("https://spotler.com/careers/jobs/medior-software-engineer", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            current_url = page.url
            status_code_check = await page.evaluate("() => document.title")
            print(f"  Direct URL result: {current_url} - Title: {status_code_check}")

            s = await screenshot(page, "02b-direct-url")
            screenshots_taken.append(s)

            # If 404, go to open application
            if "404" in status_code_check or "not found" in status_code_check.lower() or "404" in current_url:
                print("  Job URL returns 404. Using open application form...")
                await page.goto("https://spotler.com/careers/jobs/open-application", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                s = await screenshot(page, "03-open-application")
                screenshots_taken.append(s)
                print(f"  Open application URL: {page.url}")

        # --- Step 3: Find Apply button ---
        print("[3] Looking for Apply button or form...")
        current_url = page.url
        page_content = await page.content()

        # Print key page info
        print(f"  Current URL: {current_url}")
        title = await page.title()
        print(f"  Page title: {title}")

        # Look for apply buttons
        apply_selectors = [
            "a:has-text('Apply now')",
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Solliciteer')",
            "a[href*='apply']",
            "a[href*='solliciteer']",
        ]

        apply_clicked = False
        for sel in apply_selectors:
            try:
                btn = page.locator(sel).first
                count = await page.locator(sel).count()
                if count > 0:
                    print(f"  Found apply button: {sel}")
                    await btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)
                    apply_clicked = True
                    s = await screenshot(page, "04-after-apply-click")
                    screenshots_taken.append(s)
                    print(f"  After click URL: {page.url}")
                    break
            except Exception as e:
                pass

        if not apply_clicked:
            print("  No apply button found. Checking if form is already on page...")

        # --- Step 4: Detect form fields ---
        print("[4] Detecting form fields...")
        page_content = await page.content()

        # Check for iframes (common in ATS systems)
        iframes = await page.query_selector_all("iframe")
        print(f"  Iframes found: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            src = await iframe.get_attribute("src") or ""
            print(f"    iframe[{i}] src: {src}")

        # Check for common form inputs
        inputs = await page.query_selector_all("input, textarea, select")
        print(f"  Form inputs found: {len(inputs)}")
        for inp in inputs[:10]:
            tag = await inp.evaluate("el => el.tagName")
            name = await inp.get_attribute("name") or ""
            id_ = await inp.get_attribute("id") or ""
            type_ = await inp.get_attribute("type") or ""
            placeholder = await inp.get_attribute("placeholder") or ""
            print(f"    {tag}: name={name}, id={id_}, type={type_}, placeholder={placeholder}")

        # --- Step 5: Fill the form if fields exist ---
        print("[5] Attempting to fill form...")

        filled = False

        # Try common field patterns
        field_patterns = [
            # (selector, value, fill_type)
            (["input[name*='first'], input[name*='firstname'], input[id*='first'], input[placeholder*='First'], input[placeholder*='Voornaam']"], CANDIDATE["first_name"], "text"),
            (["input[name*='last'], input[name*='lastname'], input[id*='last'], input[placeholder*='Last'], input[placeholder*='Achternaam']"], CANDIDATE["last_name"], "text"),
            (["input[name*='name']:not([name*='first']):not([name*='last']), input[id*='name']:not([id*='first']):not([id*='last']), input[placeholder*='Name'], input[placeholder*='Naam']"], CANDIDATE["full_name"], "text"),
            (["input[name*='email'], input[id*='email'], input[type='email'], input[placeholder*='Email'], input[placeholder*='email']"], CANDIDATE["email"], "text"),
            (["input[name*='phone'], input[id*='phone'], input[name*='tel'], input[type='tel'], input[placeholder*='Phone'], input[placeholder*='Telefoon']"], CANDIDATE["phone"], "text"),
            (["input[name*='linkedin'], input[id*='linkedin'], input[placeholder*='LinkedIn'], input[placeholder*='linkedin']"], CANDIDATE["linkedin"], "text"),
            (["textarea[name*='motivation'], textarea[id*='motivation'], textarea[name*='cover'], textarea[placeholder*='motivation'], textarea[placeholder*='letter'], textarea"], COVER_LETTER_TEXT[:2000], "text"),
        ]

        for selectors_list, value, fill_type in field_patterns:
            for sel in selectors_list:
                try:
                    el = page.locator(sel).first
                    count = await page.locator(sel).count()
                    if count > 0:
                        await el.fill(value)
                        print(f"  Filled: {sel[:50]}")
                        filled = True
                        break
                except Exception:
                    pass

        # Try file upload for resume
        file_inputs = await page.query_selector_all("input[type='file']")
        print(f"  File inputs: {len(file_inputs)}")
        for fi in file_inputs:
            name = await fi.get_attribute("name") or ""
            accept = await fi.get_attribute("accept") or ""
            print(f"    File input: name={name}, accept={accept}")
            try:
                await fi.set_input_files(RESUME_PATH)
                print(f"  Uploaded resume to file input: {name}")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  File upload error: {e}")

        s = await screenshot(page, "05-form-filled")
        screenshots_taken.append(s)

        # --- Step 6: Check page state and print info for manual action ---
        print("[6] Final page analysis...")
        final_url = page.url
        final_title = await page.title()
        final_content = await page.content()

        # Extract visible text
        visible_text = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('h1, h2, h3, p, label, button, a');
                return Array.from(elements).map(el => el.textContent.trim()).filter(t => t.length > 0).join(' | ');
            }
        """)

        print(f"  Final URL: {final_url}")
        print(f"  Final title: {final_title}")
        print(f"  Visible text (first 1000): {visible_text[:1000]}")

        # Look for submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "button:has-text('Apply')",
            "button:has-text('Verzenden')",
        ]

        for sel in submit_selectors:
            count = await page.locator(sel).count()
            if count > 0:
                print(f"  Found submit button: {sel}")

        await browser.close()

    return {
        "screenshots": screenshots_taken,
        "final_url": final_url,
        "status": "analyzed",
    }

if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
