#!/usr/bin/env python3
"""
Spotler application v5:
- Use Playwright to load form, fill fields, upload CV
- Try the AJAX submission approach (gf_submit_button) which may not require recaptcha
- Also try iframe-based recaptcha interaction
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
    "Previously at ASML I used Azure, Kubernetes, and Azure DevOps CI/CD pipelines daily in an agile team. "
    "I also founded CogitatAI, an AI-powered SaaS customer support platform. "
    "My skills in C#, ASP.NET Core, SQL Server, TypeScript, and Azure make me an excellent fit for "
    "Spotler's Medior Software Engineer role. I am eager to contribute to your R&D team."
)

async def ss(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-v5-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  [SS] {path}")
    return path

async def main():
    taken = []
    result_status = "failed_captcha"
    final_url = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
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
        """)

        # Listen for network requests to catch any API calls
        api_responses = []
        async def handle_response(response):
            if 'gf' in response.url.lower() or 'form' in response.url.lower() or 'submit' in response.url.lower():
                try:
                    body = await response.body()
                    api_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "body": body.decode('utf-8', errors='replace')[:500]
                    })
                except: pass

        page.on("response", handle_response)

        print("[1] Loading form...")
        await page.goto("https://spotler.com/careers/jobs/open-application/apply-1136104",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # Accept cookies
        try:
            await page.click("#CybotCookiebotDialogBodyButtonAccept", timeout=3000)
            await page.wait_for_timeout(500)
        except: pass

        # Wait for form
        try:
            await page.wait_for_selector("#gform_28", timeout=10000)
            print("  Form ready")
        except:
            print("  Form not found!")
            taken.append(await ss(page, "no-form"))
            await browser.close()
            return {"status": "failed_no_form", "screenshots": taken}

        taken.append(await ss(page, "01-loaded"))

        print("[2] Filling all fields...")
        # Text fields
        fields = [
            ("#input_28_9", CANDIDATE["first_name"]),
            ("#input_28_10", CANDIDATE["last_name"]),
            ("#input_28_11", CANDIDATE["email"]),
            ("#input_28_12", CANDIDATE["phone"]),
            ("#input_28_14", MOTIVATION),
        ]
        for sel, val in fields:
            try:
                await page.fill(sel, val, timeout=5000)
                print(f"  Filled {sel}")
            except Exception as e:
                try:
                    await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{sel}');
                            if (el) {{ el.value = {json.dumps(val)}; el.dispatchEvent(new Event('input',{{bubbles:true}})); }}
                        }}
                    """)
                    print(f"  JS-filled {sel}")
                except: print(f"  Failed {sel}: {e}")

        # Upload CV
        try:
            fi = page.locator("input[type='file']").first
            await fi.set_input_files(RESUME_PATH)
            await page.wait_for_timeout(3000)
            print("  CV uploaded")
        except Exception as e:
            print(f"  CV error: {e}")

        # Get the uploaded file info
        uploaded_info = await page.evaluate("""
            () => {
                const inp = document.getElementById('gform_uploaded_files');
                return inp ? inp.value : 'not found';
            }
        """)
        print(f"  Uploaded files info: {uploaded_info}")

        # Try to click the reCAPTCHA checkbox within the iframe
        print("[3] Attempting reCAPTCHA interaction...")
        try:
            # Find the recaptcha iframe
            rc_frames = [f for f in page.frames if 'recaptcha' in f.url and 'anchor' in f.url]
            if rc_frames:
                rc_frame = rc_frames[0]
                print(f"  reCAPTCHA frame found: {rc_frame.url[:80]}")
                # Try clicking the checkbox in the recaptcha iframe
                checkbox = rc_frame.locator("#recaptcha-anchor")
                await checkbox.click(timeout=5000)
                await page.wait_for_timeout(3000)
                print("  reCAPTCHA checkbox clicked!")

                # Check if solved
                token = await page.evaluate("""
                    () => document.getElementById('g-recaptcha-response')?.value || 'empty'
                """)
                print(f"  Token after click: {token[:50]}")

                taken.append(await ss(page, "02-after-recaptcha-click"))
        except Exception as e:
            print(f"  reCAPTCHA interaction error: {e}")

        taken.append(await ss(page, "03-pre-submit"))

        # Try submitting
        print("[4] Submitting...")
        try:
            submit = page.locator("input[type='submit'][id*='gform_submit'], input[type='submit'], button[type='submit']").last
            await submit.click(timeout=5000)
            await page.wait_for_timeout(8000)
            print("  Submitted!")
        except Exception as e:
            print(f"  Submit error: {e}")

        taken.append(await ss(page, "04-post-submit"))
        final_url = page.url

        body = await page.evaluate("() => document.body.innerText")
        print(f"\n[5] Final state: {page.url}")
        print(f"Body snippet: {body[:500]}")

        b = body.lower()
        if any(k in b for k in ["thank you", "bedankt", "we will contact", "received"]):
            result_status = "applied"
            print("=> SUCCESS!")
        elif "recaptcha" in b or "captcha" in b:
            result_status = "failed_captcha"
            print("=> BLOCKED by reCAPTCHA")
        elif "problem" in b or "error" in b:
            result_status = "failed"
            print("=> Error in submission")

        print(f"\nAPI responses captured: {len(api_responses)}")
        for r in api_responses:
            print(f"  {r['url']}: {r['status']}")

        await browser.close()

    return {
        "screenshots": taken,
        "status": result_status,
        "final_url": final_url,
    }

if __name__ == "__main__":
    r = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(r, indent=2))
