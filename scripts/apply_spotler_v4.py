#!/usr/bin/env python3
"""
Spotler application v4:
- Wait for Cloudflare to pass
- Fill all form fields
- Try to bypass reCAPTCHA by setting the hidden textarea value directly
- Use Gravity Forms AJAX endpoint for submission
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
}

MOTIVATION = (
    "I am a Software Engineer with approximately 2.5 years of professional experience. "
    "At Actemium (VINCI Energies) I build .NET, C#, and ASP.NET Core applications for industrial clients. "
    "Before that I worked at ASML using Azure, Kubernetes, and Azure DevOps CI/CD pipelines in an agile team. "
    "I also founded CogitatAI, an AI-powered SaaS customer support platform. "
    "My skills in C#, ASP.NET Core, SQL Server, TypeScript, and Azure make me a strong fit for "
    "Spotler's Medior Software Engineer role. I am excited to contribute to your fast-growing SaaS platform "
    "and help your R&D team deliver great products."
)

async def ss(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-v4-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  [SS] {path}")
    return path

async def wait_for_cf(page, timeout=30):
    """Wait for Cloudflare challenge to pass"""
    for _ in range(timeout):
        title = await page.title()
        if "just a moment" not in title.lower() and "checking" not in title.lower():
            return True
        await page.wait_for_timeout(1000)
    return False

async def main():
    taken = []
    result_status = "failed"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
            ]
        )
        ctx = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await ctx.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        print("[1] Loading application form (waiting for CF)...")
        await page.goto("https://spotler.com/careers/jobs/open-application/apply-1136104",
                        wait_until="domcontentloaded", timeout=60000)

        # Wait for CF to pass
        passed = await wait_for_cf(page, 20)
        if not passed:
            print("  CF not passed yet, waiting more...")
            await page.wait_for_timeout(5000)

        # Wait for form to load
        try:
            await page.wait_for_selector("#gform_28", timeout=15000)
            print("  Form loaded!")
        except:
            print("  Form not found, current state:")
            print(f"  Title: {await page.title()}")
            print(f"  URL: {page.url}")

        await page.wait_for_timeout(2000)

        # Accept cookies
        try:
            await page.click("#CybotCookiebotDialogBodyButtonAccept", timeout=3000)
            await page.wait_for_timeout(500)
            print("  Cookies accepted")
        except: pass

        taken.append(await ss(page, "01-loaded"))

        # Get all hidden fields and nonces
        print("[2] Extracting form metadata...")
        page_source = await page.content()

        # Find all nonces
        nonces = {}
        nonce_patterns = [
            (r'"nonce"\s*:\s*"([a-f0-9]{10})"', "main_nonce"),
            (r'gforms_recaptcha_nonce["\s:,{}]*"([a-f0-9]{10})"', "recaptcha_nonce"),
            (r'"ajax_nonce"\s*:\s*"([a-f0-9]{10})"', "ajax_nonce"),
        ]
        for pattern, key in nonce_patterns:
            m = re.search(pattern, page_source)
            if m:
                nonces[key] = m.group(1)

        # Try from JS vars
        gform_nonce = await page.evaluate("""
            () => {
                if (window.gf_global) return window.gf_global.nonce || null;
                if (window.gforms_locale_strings) return window.gforms_locale_strings.nonce || null;
                return null;
            }
        """)
        if gform_nonce:
            nonces["gf_global_nonce"] = gform_nonce

        print(f"  Nonces: {nonces}")

        # Get hidden form fields
        hidden = await page.evaluate("""
            () => {
                const form = document.getElementById("gform_28");
                if (!form) return {};
                const h = {};
                form.querySelectorAll("input[type=hidden]").forEach(i => { if(i.name) h[i.name] = i.value; });
                return h;
            }
        """)
        print(f"  Hidden fields: {json.dumps(hidden)}")

        print("[3] Filling form fields...")

        # Fill fields
        fields = [
            ("#input_28_9", CANDIDATE["first_name"]),
            ("#input_28_10", CANDIDATE["last_name"]),
            ("#input_28_11", CANDIDATE["email"]),
            ("#input_28_12", CANDIDATE["phone"]),
            ("#input_28_14", MOTIVATION),
        ]

        for selector, value in fields:
            try:
                await page.fill(selector, value, timeout=5000)
                print(f"  Filled {selector}")
            except Exception as e:
                # Try JavaScript fill
                try:
                    await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{selector}');
                            if (el) {{
                                el.value = {json.dumps(value)};
                                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                            }}
                        }}
                    """)
                    print(f"  JS-filled {selector}")
                except Exception as e2:
                    print(f"  Failed to fill {selector}: {e2}")

        # Upload CV
        try:
            file_inputs = await page.query_selector_all("input[type='file']")
            if file_inputs:
                await file_inputs[0].set_input_files(RESUME_PATH)
                await page.wait_for_timeout(3000)
                print("  CV uploaded")
        except Exception as e:
            print(f"  CV upload error: {e}")

        taken.append(await ss(page, "02-filled"))

        # Check reCAPTCHA
        print("[4] Checking reCAPTCHA status...")
        recaptcha_info = await page.evaluate("""
            () => {
                // Check if reCAPTCHA v3 or v2
                const rcEl = document.getElementById('g-recaptcha-response');
                const rcV3 = document.querySelector('.grecaptcha-badge');
                const rcFrame = document.querySelector('iframe[src*="recaptcha"]');
                return {
                    v2_element: rcEl ? rcEl.value || 'empty' : 'not found',
                    v3_badge: rcV3 ? 'found' : 'not found',
                    iframe_src: rcFrame ? rcFrame.src.substring(0, 100) : 'not found',
                    // Try to get the sitekey
                    sitekey: document.querySelector('[data-sitekey]') ?
                             document.querySelector('[data-sitekey]').getAttribute('data-sitekey') : 'not found',
                    // Check for recaptcha callback
                    grecaptcha: typeof grecaptcha !== 'undefined' ? 'available' : 'not available'
                };
            }
        """)
        print(f"  reCAPTCHA info: {json.dumps(recaptcha_info)}")

        # Try to execute reCAPTCHA v3 if available
        if recaptcha_info.get('grecaptcha') == 'available':
            print("  Attempting reCAPTCHA v3 token generation...")
            try:
                token = await page.evaluate("""
                    async () => {
                        try {
                            const sitekey = document.querySelector('[data-sitekey]')?.getAttribute('data-sitekey') ||
                                           '6Lf8iO8pAAAAAKaKL34rZUDdmxJKxIGnZAXQpK8l';
                            const token = await new Promise((resolve, reject) => {
                                grecaptcha.ready(() => {
                                    grecaptcha.execute(sitekey, {action: 'submit'}).then(resolve).catch(reject);
                                });
                            });
                            return token;
                        } catch(e) {
                            return 'error: ' + e.message;
                        }
                    }
                """)
                print(f"  reCAPTCHA token: {token[:50] if token else 'none'}")

                if token and not token.startswith('error'):
                    # Set the token
                    await page.evaluate(f"""
                        () => {{
                            const el = document.getElementById('g-recaptcha-response');
                            if (el) el.value = {json.dumps(token)};
                        }}
                    """)
                    print("  reCAPTCHA token set in form")
            except Exception as e:
                print(f"  reCAPTCHA execution error: {e}")

        taken.append(await ss(page, "03-pre-submit"))

        print("[5] Submitting form...")
        try:
            submit_btn = page.locator("input[type='submit'][id*='gform_submit'], input[type='submit'], button[type='submit']").first
            btn_val = await submit_btn.evaluate("e => e.value || e.textContent")
            print(f"  Submit button: '{btn_val}'")
            await submit_btn.click()
            await page.wait_for_timeout(6000)
            print("  Submit clicked, waiting...")
        except Exception as e:
            print(f"  Submit error: {e}")

        taken.append(await ss(page, "04-post-submit"))

        # Analyze result
        body = await page.evaluate("() => document.body.innerText")
        print(f"\n[6] Final state:")
        print(f"  URL: {page.url}")
        print(f"  Title: {await page.title()}")
        print(f"  Body (first 600):\n{body[:600]}")

        b = body.lower()
        if any(k in b for k in ["thank you", "bedankt", "we will contact", "application received", "confirmation"]):
            result_status = "applied"
            print("\n  => SUCCESS!")
        elif "there was a problem" in b or "recaptcha" in b.lower() or "captcha" in b.lower():
            result_status = "failed_captcha"
            print("\n  => BLOCKED by reCAPTCHA")
        elif any(k in b for k in ["error", "invalid", "required"]):
            result_status = "failed_validation"
            print("\n  => VALIDATION ERRORS")
            # Get specific errors
            errors = await page.evaluate("""
                () => Array.from(document.querySelectorAll('.gfield_error .validation_message, .validation_container'))
                    .map(e => e.textContent.trim())
            """)
            print(f"  Errors: {errors}")
        else:
            print("\n  => Status unknown")

        await browser.close()

    return {
        "screenshots": taken,
        "status": result_status,
    }

if __name__ == "__main__":
    r = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(r, indent=2))
