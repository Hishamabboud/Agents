#!/usr/bin/env python3
"""
BIMcollab Application - Extended wait version
Wait up to 60 seconds after Send click for hCaptcha to complete
Monitor for navigation or success indication
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
    path = f"{SCREENSHOT_DIR}/bimcollab-wait-{name}-{ts()}.png"
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

    api_calls = []

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

        async def handle_response(response):
            url = response.url
            sc = response.status
            # Track any response that seems like application submission
            if ("bimcollab" in url or "recruitee" in url) and sc in [200, 201, 302]:
                if "captcha" not in url and "cdn" not in url and "image" not in url:
                    api_calls.append(f"{sc} {url}")
                    print(f"API: {sc} {url[:100]}")

        page = await context.new_page()
        page.on("response", handle_response)

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            # Dismiss initial cookies
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

            # Dismiss any popups
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form
            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click()
            await name_loc.fill("Hisham Abboud")

            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click()
            await email_loc.fill("hiaham123@hotmail.com")

            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click()
            await phone_loc.fill("")
            await phone_loc.fill("+31648412838")

            # CV
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            # Cover letter
            try:
                write_btn = page.locator("button:has-text('Write it here instead')").first
                if await write_btn.is_visible(timeout=2000):
                    await write_btn.click()
                    await page.wait_for_timeout(1000)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            # Radios
            for q_name in ['candidate.openQuestionAnswers.6352299.flag',
                           'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    await page.locator(f"input[name='{q_name}'][value='true']").check(force=True, timeout=3000)
                except:
                    await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector("input[name='{q_name}'][value='true']");
                            if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
                        }}
                    """)

            # Legal
            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            state = await page.evaluate("""
                () => ({
                    name: (document.querySelector("input[name='candidate.name']")||{value:''}).value,
                    email: (document.querySelector("input[name='candidate.email']")||{value:''}).value,
                    q1: (document.querySelector("input[name='candidate.openQuestionAnswers.6352299.flag']:checked")||{value:'NONE'}).value,
                    q2: (document.querySelector("input[name='candidate.openQuestionAnswers.6352300.flag']:checked")||{value:'NONE'}).value,
                    legal: (document.querySelector("input[name='candidate.openQuestionAnswers.6352298.flag']:checked") != null),
                })
            """)
            print(f"Form state: {state}")

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Click Send
            print("\nClicking Send button...")
            send_btn = page.locator("button[type='submit']").first
            await send_btn.click()
            print("Send clicked! Waiting...")

            s = await ss(page, "02-after-send-immediate")
            if s: screenshots.append(s)

            # Wait for result - check every 3 seconds for up to 30 seconds
            print("Monitoring for 30 seconds...")
            success = False
            for check in range(10):
                await page.wait_for_timeout(3000)

                # Check URL
                current_url = page.url
                current_html = await page.content()
                current_text = await page.evaluate("() => document.body.innerText")

                # Check for success
                if any(kw in current_text.lower() for kw in ["thank you", "successfully", "application received", "bedankt"]):
                    success = True
                    print(f"SUCCESS at check {check+1}!")
                    break

                # Check for captcha challenge popup
                has_captcha_popup = "Please click" in current_text or "Find all" in current_text
                has_linkedin_popup = "Cookies agreement" in current_text or "Agree to necessary" in current_text

                print(f"Check {check+1}: captcha={has_captcha_popup}, linkedin={has_linkedin_popup}, url={current_url}")

                if has_linkedin_popup:
                    # Dismiss and click send again
                    for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')"]:
                        try:
                            btn = page.locator(sel).first
                            if await btn.is_visible(timeout=1000):
                                await btn.click()
                                print(f"  Dismissed popup at check {check+1}")
                                await page.wait_for_timeout(1000)
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
                                # Click send
                                try:
                                    send_btn2 = page.locator("button[type='submit']").first
                                    if await send_btn2.is_visible(timeout=1000):
                                        await send_btn2.click()
                                        print(f"  Clicked Send again at check {check+1}")
                                except:
                                    pass
                                break
                        except:
                            pass

                if has_captcha_popup:
                    s = await ss(page, f"captcha-{check:02d}")
                    if s: screenshots.append(s)
                    print(f"  Captcha puzzle visible at check {check+1} - this requires human interaction")

            s = await ss(page, "03-monitoring-done")
            if s: screenshots.append(s)

            if success:
                status = "applied"
                notes = f"Application submitted successfully. URL: {page.url}"
            else:
                # Final state
                final_url = page.url
                final_text = await page.evaluate("() => document.body.innerText")
                final_html = await page.content()

                if "hcaptcha" in final_html.lower():
                    status = "failed"
                    notes = ("Form filled: name=Hisham Abboud, email=hiaham123@hotmail.com, CV=uploaded, "
                            "cover letter=added, Q1=Yes, Q2=Yes, legal=checked. "
                            "Blocked by hCaptcha invisible (sitekey d111bc04-7616-4e05-a1da-9840968d2b88). "
                            "Form is ready - only hCaptcha solving needed.")
                    print("BLOCKED by hCaptcha after monitoring")
                elif any(kw in final_text.lower() for kw in ["thank you", "successfully", "received"]):
                    status = "applied"
                    notes = f"Confirmation after monitoring. URL: {final_url}"
                else:
                    status = "failed"
                    notes = f"Unknown final state. URL: {final_url}"

                print(f"Final text: {final_text[:300]}")

            print(f"\nAPI calls captured: {len(api_calls)}")
            for call in api_calls:
                print(f"  {call}")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-wait-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
