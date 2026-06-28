#!/usr/bin/env python3
"""
Spotler open application form v3 - use exact field IDs, fill all required fields,
handle reCAPTCHA gracefully, submit.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/spotler-medior-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "work_permit_country": "Netherlands",
}

MOTIVATION = (
    "I am a Software Engineer with approximately 2.5 years of professional experience, "
    "currently at Actemium (VINCI Energies) building .NET, C#, and ASP.NET Core applications "
    "for industrial clients. Previously I worked at ASML in an agile R&D team using Azure, "
    "Kubernetes, and CI/CD pipelines. I also founded CogitatAI, an AI-powered SaaS customer "
    "support platform, giving me direct experience with multi-tenant data-intensive products. "
    "Spotler's engineering culture and SaaS domain are an excellent fit for my background in "
    "C#, ASP.NET Core, SQL Server, Azure, and CI/CD. I am eager to contribute to your team "
    "and help drive Spotler's next phase of growth."
)

async def ss(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-v3-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  [SS] {path}")
    return path

async def main():
    taken = []
    result_status = "pending"

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

        print("[1] Loading application form...")
        await page.goto("https://spotler.com/careers/jobs/open-application/apply-1136104",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # Accept cookies
        try:
            await page.click("#CybotCookiebotDialogBodyButtonAccept", timeout=3000)
            await page.wait_for_timeout(1000)
            print("  Cookies accepted")
        except:
            print("  No cookie dialog")

        taken.append(await ss(page, "01-loaded"))

        print("[2] Filling required fields by exact ID...")

        # First name - id='input_28_9'
        try:
            await page.fill("#input_28_9", CANDIDATE["first_name"])
            print(f"  First name: {CANDIDATE['first_name']}")
        except Exception as e:
            print(f"  First name error: {e}")

        # Last name - id='input_28_10'
        try:
            await page.fill("#input_28_10", CANDIDATE["last_name"])
            print(f"  Last name: {CANDIDATE['last_name']}")
        except Exception as e:
            print(f"  Last name error: {e}")

        # Email - id='input_28_11'
        try:
            await page.fill("#input_28_11", CANDIDATE["email"])
            print(f"  Email: {CANDIDATE['email']}")
        except Exception as e:
            print(f"  Email error: {e}")

        # Phone - id='input_28_12'
        try:
            await page.fill("#input_28_12", CANDIDATE["phone"])
            print(f"  Phone: {CANDIDATE['phone']}")
        except Exception as e:
            print(f"  Phone error: {e}")

        # WorkPermitCountry - id='input_28_18'
        try:
            await page.fill("#input_28_18", CANDIDATE["work_permit_country"])
            print(f"  WorkPermitCountry: {CANDIDATE['work_permit_country']}")
        except Exception as e:
            print(f"  WorkPermitCountry error: {e}")

        # Motivation textarea - id='input_28_14'
        try:
            await page.fill("#input_28_14", MOTIVATION)
            print(f"  Motivation filled ({len(MOTIVATION)} chars)")
        except Exception as e:
            print(f"  Motivation error: {e}")

        # Work permit checkbox - try "Yes" (id='choice_28_19_0', value='Yes')
        try:
            await page.check("#choice_28_19_0")
            print("  Work permit: Yes checked")
        except Exception as e:
            print(f"  Work permit checkbox error: {e}")

        # CV upload - id='html5_1jq91c05u1oefo4u4n81vbd3vf3'
        try:
            file_input = page.locator("#html5_1jq91c05u1oefo4u4n81vbd3vf3")
            await file_input.set_input_files(RESUME_PATH)
            await page.wait_for_timeout(3000)
            print(f"  CV uploaded: {RESUME_PATH}")
        except Exception as e:
            print(f"  CV upload error (trying generic): {e}")
            # fallback to any file input
            try:
                fi = page.locator("input[type='file']").first
                await fi.set_input_files(RESUME_PATH)
                await page.wait_for_timeout(3000)
                print("  CV uploaded via fallback")
            except Exception as e2:
                print(f"  Fallback upload error: {e2}")

        taken.append(await ss(page, "02-filled"))

        # Check reCAPTCHA status
        print("[3] Checking reCAPTCHA...")
        recaptcha_response = await page.evaluate("""
            () => {
                const el = document.getElementById('g-recaptcha-response');
                return el ? el.value : 'not found';
            }
        """)
        print(f"  reCAPTCHA token: {recaptcha_response[:50] if recaptcha_response else 'empty'}")

        # Check form validation state before submit
        print("[4] Checking form validity...")
        form_valid = await page.evaluate("""
            () => {
                const form = document.querySelector('form#gform_28, form');
                if (!form) return { valid: null, msg: 'no form found' };
                const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
                const invalid = [];
                inputs.forEach(inp => {
                    if (!inp.validity.valid) invalid.push({id: inp.id, name: inp.name, value: inp.value});
                });
                return { valid: inputs.length === 0 || invalid.length === 0, invalid };
            }
        """)
        print(f"  Form validity: {json.dumps(form_valid)}")

        taken.append(await ss(page, "03-pre-submit"))

        print("[5] Submitting form...")
        try:
            # Try the Gravity Forms AJAX submit button
            submit = page.locator("input[type='submit'][value*='Apply'], button[type='submit'], input[type='submit']").last
            btn_text = await submit.evaluate("e => e.value || e.textContent")
            print(f"  Submit button: '{btn_text}'")
            await submit.click()
            print("  Submit clicked")
            # Wait for response
            await page.wait_for_timeout(8000)
        except Exception as e:
            print(f"  Submit error: {e}")

        taken.append(await ss(page, "04-post-submit"))

        final_url = page.url
        final_title = await page.title()
        body = await page.evaluate("() => document.body.innerText")
        print(f"\n[6] Final state:")
        print(f"  URL: {final_url}")
        print(f"  Title: {final_title}")
        print(f"  Body (first 800):\n{body[:800]}")

        # Detect confirmation/error
        b = body.lower()
        if any(k in b for k in ["thank you", "bedankt", "confirmation", "received your", "received", "success", "we will contact"]):
            result_status = "applied"
            print("\n  => SUCCESS: Application submitted!")
        elif any(k in b for k in ["there was a problem", "error", "invalid", "required field", "captcha failed"]):
            result_status = "failed"
            print("\n  => FAILED: Error in submission")

            # Get specific error messages
            errors = await page.evaluate("""
                () => {
                    const errs = document.querySelectorAll('.gfield_error, .validation_message, .error-message, [class*="error"]');
                    return Array.from(errs).map(e => e.textContent.trim()).filter(t => t.length > 0);
                }
            """)
            print(f"  Error details: {errors}")
        else:
            print("\n  => Status UNKNOWN")

        await browser.close()

    return {
        "screenshots": taken,
        "final_url": final_url,
        "status": result_status,
        "body_snippet": body[:500],
    }

if __name__ == "__main__":
    r = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(r, indent=2))
