#!/usr/bin/env python3
"""
Spotler open application form - full fill and submit attempt.
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

with open(COVER_LETTER_PATH, "r") as f:
    COVER_LETTER_TEXT = f.read()

# Short motivation text for form fields
MOTIVATION_SHORT = (
    "I am a Software Engineer with ~2.5 years of .NET/C#/ASP.NET Core experience at Actemium "
    "and Azure/CI/CD experience from ASML. I am excited to contribute to Spotler's SaaS platform. "
    "My background in data-intensive applications, SQL Server optimisation, and cloud-native development "
    "aligns closely with Spotler's Medior Software Engineer profile."
)

async def ss(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-v2-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  [screenshot] {path}")
    return path

async def main():
    taken = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await ctx.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Navigate directly to the application form
        print("[1] Navigating to apply form...")
        await page.goto("https://spotler.com/careers/jobs/open-application/apply-1136104",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        taken.append(await ss(page, "01-form-loaded"))
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")

        # Accept cookies if banner present
        print("[2] Handling cookie banner...")
        try:
            accept_btn = page.locator("#CybotCookiebotDialogBodyButtonAccept, button:has-text('Accept all'), button:has-text('Alles accepteren')").first
            if await accept_btn.count() > 0:
                await accept_btn.click()
                await page.wait_for_timeout(1000)
                print("  Accepted cookies")
        except Exception as e:
            print(f"  No cookie banner or error: {e}")

        # Enumerate all form fields
        print("[3] Enumerating ALL form fields...")
        all_inputs = await page.query_selector_all("input:not([type='hidden']):not([type='checkbox']):not([type='radio']), textarea, select")
        for el in all_inputs:
            tag = await el.evaluate("e => e.tagName")
            name = await el.get_attribute("name") or ""
            id_ = await el.get_attribute("id") or ""
            type_ = await el.get_attribute("type") or ""
            placeholder = await el.get_attribute("placeholder") or ""
            label_text = await el.evaluate("""e => {
                const label = document.querySelector('label[for="' + e.id + '"]');
                return label ? label.textContent.trim() : '';
            }""")
            print(f"  {tag}: name='{name}', id='{id_}', type='{type_}', placeholder='{placeholder}', label='{label_text}'")

        # Also check checkboxes/radios
        checks = await page.query_selector_all("input[type='checkbox'], input[type='radio']")
        for el in checks:
            name = await el.get_attribute("name") or ""
            id_ = await el.get_attribute("id") or ""
            value = await el.get_attribute("value") or ""
            label_text = await el.evaluate("""e => {
                const label = document.querySelector('label[for="' + e.id + '"]');
                return label ? label.textContent.trim() : '';
            }""")
            print(f"  CHECKBOX/RADIO: name='{name}', id='{id_}', value='{value}', label='{label_text}'")

        print("[4] Filling form fields...")

        # --- Name fields ---
        # Try first name
        for sel in ["input[id*='first'], input[name*='first'], input[placeholder*='First name'], input[placeholder*='Voornaam']"]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    await els[0].fill(CANDIDATE["first_name"])
                    print(f"  First name filled via: {sel}")
                    break
            except: pass

        # Try last name
        for sel in ["input[id*='last'], input[name*='last'], input[placeholder*='Last name'], input[placeholder*='Achternaam']"]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    await els[0].fill(CANDIDATE["last_name"])
                    print(f"  Last name filled via: {sel}")
                    break
            except: pass

        # Email
        for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']", "input[placeholder*='mail']"]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    await els[0].fill(CANDIDATE["email"])
                    print(f"  Email filled via: {sel}")
                    break
            except: pass

        # Phone
        for sel in ["input[type='tel']", "input[name*='phone']", "input[name*='Phone']", "input[id*='phone']", "input[placeholder*='Phone'], input[placeholder*='Telefoon']"]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    await els[0].fill(CANDIDATE["phone"])
                    print(f"  Phone filled via: {sel}")
                    break
            except: pass

        # LinkedIn
        for sel in ["input[name*='linkedin'], input[id*='linkedin'], input[placeholder*='LinkedIn'], input[placeholder*='linkedin']"]:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    await els[0].fill(CANDIDATE["linkedin"])
                    print(f"  LinkedIn filled via: {sel}")
                    break
            except: pass

        # Motivation / cover letter textarea
        for sel in ["textarea"]:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    placeholder = await el.get_attribute("placeholder") or ""
                    name = await el.get_attribute("name") or ""
                    await el.fill(MOTIVATION_SHORT)
                    print(f"  Textarea filled: name='{name}', placeholder='{placeholder}'")
            except Exception as e:
                print(f"  Textarea error: {e}")

        # File upload
        file_inputs = await page.query_selector_all("input[type='file']")
        for fi in file_inputs:
            try:
                await fi.set_input_files(RESUME_PATH)
                print(f"  Resume uploaded")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Upload error: {e}")

        taken.append(await ss(page, "04-filled"))

        # Wait a bit for file upload processing
        await page.wait_for_timeout(2000)

        # Screenshot before submit
        taken.append(await ss(page, "05-pre-submit"))

        # --- Try to submit ---
        print("[5] Attempting form submission...")
        submit_sel = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send application')",
            "button:has-text('Apply')",
            "button:has-text('Submit')",
            "button:has-text('Verzenden')",
            "button:has-text('Solliciteer')",
        ]

        submitted = False
        for sel in submit_sel:
            try:
                btns = await page.query_selector_all(sel)
                if btns:
                    btn = btns[-1]  # usually the last submit button is the real one
                    btn_text = await btn.evaluate("e => e.textContent.trim()")
                    btn_type = await btn.get_attribute("type") or ""
                    print(f"  Submit button found: '{btn_text}' (type={btn_type})")
                    await btn.click()
                    submitted = True
                    print(f"  Submit clicked!")
                    await page.wait_for_timeout(5000)
                    break
            except Exception as e:
                print(f"  Submit click error: {e}")

        if not submitted:
            print("  No submit button found or could not click")

        # Post-submit screenshot
        taken.append(await ss(page, "06-post-submit"))

        final_url = page.url
        final_title = await page.title()
        final_text = await page.evaluate("""
            () => document.body.innerText.slice(0, 2000)
        """)

        print(f"\n[6] POST-SUBMIT STATE:")
        print(f"  URL: {final_url}")
        print(f"  Title: {final_title}")
        print(f"  Body text: {final_text[:500]}")

        # Check for success/error indicators
        success_keywords = ["thank you", "bedankt", "confirmation", "bevestig", "received", "ontvangen", "success"]
        error_keywords = ["error", "fout", "invalid", "required", "verplicht", "captcha", "failed"]

        body_lower = final_text.lower()
        is_success = any(k in body_lower for k in success_keywords)
        is_error = any(k in body_lower for k in error_keywords)

        print(f"\n  Success indicators: {is_success}")
        print(f"  Error indicators: {is_error}")

        if is_success:
            status = "applied"
            print("  => Application SUBMITTED SUCCESSFULLY!")
        elif is_error:
            status = "failed"
            print("  => Submission encountered ERRORS")
        else:
            status = "pending"
            print("  => Submission status UNKNOWN")

        await browser.close()

    return {
        "screenshots": taken,
        "final_url": final_url,
        "final_title": final_title,
        "status": status,
        "body_snippet": final_text[:500],
    }

if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
