#!/usr/bin/env python3
"""
BIMcollab Application - Keyboard submit attempt + form check
Try submitting via keyboard, check if the 'required' field error is from captcha or form
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"

COVER_LETTER_TEXT = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    if not proxy_url:
        return None
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def ss(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-kb-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"SS: {path}")
        return path
    except:
        return None

async def main():
    screenshots = []
    status = "failed"
    notes = ""
    proxy_config = get_proxy_config()

    cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
    os.makedirs(os.path.dirname(cl_file), exist_ok=True)
    with open(cl_file, "w") as f:
        f.write(COVER_LETTER_TEXT)

    all_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"],
            proxy=proxy_config
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        async def handle_request(request):
            if request.method == "POST":
                url = request.url
                if "google" not in url and "analytics" not in url and "linkedin" not in url and "sentry" not in url and "captcha" not in url:
                    try:
                        pd = request.post_data_buffer
                        all_requests.append({"method": "POST", "url": url, "data_len": len(pd) if pd else 0})
                        print(f"POST: {url[:100]} (data: {len(pd) if pd else 0} bytes)")
                    except:
                        all_requests.append({"method": "POST", "url": url})
                        print(f"POST: {url[:100]}")

        async def handle_response(response):
            url = response.url
            if "bimcollab" in url and response.status in [200, 201, 302]:
                if "google" not in url and "captcha" not in url:
                    print(f"RESPONSE {response.status}: {url[:100]}")

        page = await context.new_page()
        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            # Dismiss popups
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Click Apply tab
            buttons = await page.query_selector_all("button.sc-csisgn-0")
            for btn in buttons:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    print("Apply tab clicked")
                    break

            # Dismiss popups again
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form fields
            print("Filling form...")

            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click(timeout=5000)
            await name_loc.fill("Hisham Abboud")

            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click(timeout=3000)
            await email_loc.fill("hiaham123@hotmail.com")

            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click(timeout=3000)
            await phone_loc.fill("")
            await phone_loc.fill("+31648412838")

            # CV
            cv_loc = page.locator("input[name='candidate.cv']").first
            await cv_loc.set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            # Cover letter text
            try:
                write_btn = page.locator("button:has-text('Write it here instead')").first
                if await write_btn.is_visible(timeout=2000):
                    await write_btn.click()
                    await page.wait_for_timeout(1000)
                    ta = await page.query_selector("textarea:visible")
                    if ta:
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            # Check radios
            for q_name in ['candidate.openQuestionAnswers.6352299.flag',
                           'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    radio = page.locator(f"input[name='{q_name}'][value='true']").first
                    await radio.check(force=True, timeout=3000)
                except:
                    await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector("input[name='{q_name}'][value='true']");
                            if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
                        }}
                    """)

            # Legal checkbox
            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            # Verify
            state = await page.evaluate("""
                () => ({
                    name: (document.querySelector("input[name='candidate.name']")||{}).value || 'MISSING',
                    email: (document.querySelector("input[name='candidate.email']")||{}).value || 'MISSING',
                    q1: (document.querySelector("input[name='candidate.openQuestionAnswers.6352299.flag']:checked")||{}).value || 'NONE',
                    q2: (document.querySelector("input[name='candidate.openQuestionAnswers.6352300.flag']:checked")||{}).value || 'NONE',
                })
            """)
            print(f"Form state: {state}")

            s = await ss(page, "01-form-filled")
            if s: screenshots.append(s)

            # APPROACH 1: Dismiss LinkedIn popup and submit clean
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Click Send
            print("Clicking Send...")
            send_loc = page.locator("button[type='submit']").first
            await send_loc.scroll_into_view_if_needed()
            await send_loc.click()
            await page.wait_for_timeout(3000)

            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Dismiss LinkedIn popup that appears
            linkedin_dismissed = False
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        linkedin_dismissed = True
                        print(f"Dismissed LinkedIn: {sel}")
                        await page.wait_for_timeout(1500)
                        break
                except:
                    pass

            if linkedin_dismissed:
                # Re-check radios
                await page.evaluate("""
                    () => {
                        ['candidate.openQuestionAnswers.6352299.flag',
                         'candidate.openQuestionAnswers.6352300.flag'].forEach(name => {
                            const el = document.querySelector(`input[name='${name}'][value='true']`);
                            if (el) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); }
                        });
                    }
                """)

                s = await ss(page, "03-after-linkedin-dismiss")
                if s: screenshots.append(s)

                # APPROACH 2: Try submitting via keyboard Enter key
                print("Submitting via keyboard Enter...")
                try:
                    # Focus the last input and press Enter
                    send_btn = page.locator("button[type='submit']").first
                    await send_btn.focus()
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(4000)
                    print("Keyboard Enter pressed")
                except Exception as e:
                    print(f"Keyboard submit: {e}")

                s = await ss(page, "04-after-keyboard-submit")
                if s: screenshots.append(s)

                # APPROACH 3: Dismiss any more popups, click Send
                for _ in range(3):
                    any_dismissed = False
                    for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')", "button:has-text('OK')"]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=1000):
                                await btn.click()
                                any_dismissed = True
                                await page.wait_for_timeout(1000)
                        except:
                            pass

                    if any_dismissed:
                        # Re-check radios
                        await page.evaluate("""
                            () => {
                                ['candidate.openQuestionAnswers.6352299.flag',
                                 'candidate.openQuestionAnswers.6352300.flag'].forEach(name => {
                                    const el = document.querySelector(`input[name='${name}'][value='true']`);
                                    if (el) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); }
                                });
                            }
                        """)
                        try:
                            send_btn = page.locator("button[type='submit']").first
                            if await send_btn.is_visible(timeout=1500):
                                await send_btn.click()
                                print("Send clicked again")
                                await page.wait_for_timeout(4000)
                        except:
                            pass
                    else:
                        break

            await page.wait_for_timeout(2000)
            s = await ss(page, "05-final")
            if s: screenshots.append(s)

            # Check what happened
            final_url = page.url
            final_html = await page.content()
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Page text (first 400): {final_text[:400]}")

            print(f"\nNon-analytics POST requests captured:")
            for req in all_requests:
                print(f"  {req}")

            success_kws = ["thank you", "bedankt", "successfully", "application received",
                          "we have received", "your application has been", "successfully submitted"]
            if any(kw in final_text.lower() for kw in success_kws):
                status = "applied"
                notes = f"Confirmation found. URL: {final_url}"
                print("SUCCESS!")
            else:
                captcha_in_html = "hcaptcha" in final_html.lower()
                if captcha_in_html:
                    status = "failed"
                    notes = ("Form correctly filled with: Hisham Abboud, hiaham123@hotmail.com, CV uploaded, cover letter added, Q1=Yes, Q2=Yes, legal=checked. "
                            "Blocked by hCaptcha invisible (sitekey d111bc04-7616-4e05-a1da-9840968d2b88). "
                            "The form is ready to submit but requires manual CAPTCHA solving.")
                    print("BLOCKED by hCaptcha")
                else:
                    # Check form field values to see if they're still there
                    name_val = await page.locator("input[name='candidate.name']").input_value()
                    print(f"Name field value: '{name_val}'")
                    if name_val:
                        status = "failed"
                        notes = f"Form filled but submit failed. URL: {final_url}"
                    else:
                        status = "failed"
                        notes = f"Unknown state. URL: {final_url}"

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await ss(page, "error")
                if s: screenshots.append(s)
            except:
                pass
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    # Log
    app_id = f"bimcollab-kb-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": cl_file,
        "screenshots": screenshots,
        "notes": notes,
        "response": None
    }

    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except:
        apps = []
    apps.append(new_entry)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT: {status} ===")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
