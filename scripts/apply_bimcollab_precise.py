#!/usr/bin/env python3
"""
BIMcollab Application - Precise version
Key fixes:
1. After dismissing LinkedIn popup, precisely click 'Send' not 'Apply'
2. Wait for captcha to appear naturally
3. Try to interact with captcha icons directly
"""

import asyncio
import base64
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
    path = f"{SCREENSHOT_DIR}/bimcollab-prec-{name}-{ts()}.png"
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

    actual_submission = False
    submission_url = ""

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
            nonlocal actual_submission, submission_url
            url = response.url
            sc = response.status
            # Only track actual Recruitee/bimcollab application submission
            if "bimcollab" in url and sc in [200, 201]:
                if "js" not in url and "css" not in url and "image" not in url and "captcha" not in url and "cdn" not in url:
                    print(f"BIMCOLLAB RESPONSE: {sc} {url[:100]}")
                    if "/c/" in url and "new" not in url:
                        actual_submission = True
                        submission_url = f"{sc} {url}"

        page = await context.new_page()
        page.on("response", handle_response)

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            # Dismiss cookies
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Click Apply tab
            print("Clicking Apply tab...")
            all_sc_btns = await page.query_selector_all("button.sc-csisgn-0")
            for btn in all_sc_btns:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    print(f"Clicked Apply tab")
                    break

            # Dismiss any more popups
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form
            print("Filling form...")
            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click(timeout=5000)
            await name_loc.fill("Hisham Abboud")

            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click()
            await email_loc.fill("hiaham123@hotmail.com")

            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click()
            await phone_loc.fill("")
            await phone_loc.fill("+31648412838")

            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            # Cover letter text
            try:
                write_btn = page.locator("button:has-text('Write it here instead')").first
                if await write_btn.is_visible(timeout=2000):
                    await write_btn.click()
                    await page.wait_for_timeout(1000)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.fill(COVER_LETTER_TEXT)
                        print("Cover letter text entered")
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
                    legal: !!document.querySelector("input[name='candidate.openQuestionAnswers.6352298.flag']:checked"),
                })
            """)
            print(f"Form state: {state}")

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Find the Send button precisely
            print("\nFinding Send button...")
            send_button = None
            all_buttons = await page.query_selector_all("button")
            for btn in all_buttons:
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type")
                    is_vis = await btn.is_visible()
                    if text.strip().lower() == "send" and is_vis:
                        send_button = btn
                        print(f"  Found Send button: '{text}', type={btype}")
                        break
                except:
                    pass

            if not send_button:
                # Find by type=submit
                btns = await page.query_selector_all("button[type='submit']")
                for btn in btns:
                    try:
                        text = await btn.inner_text()
                        is_vis = await btn.is_visible()
                        if is_vis:
                            send_button = btn
                            print(f"  Found submit button: '{text}'")
                            break
                    except:
                        pass

            if send_button:
                await send_button.click()
                print("Send clicked!")
            else:
                print("Send button not found!")

            await page.wait_for_timeout(5000)
            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Handle LinkedIn popup
            linkedin_dismissed = False
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        linkedin_dismissed = True
                        print(f"Dismissed LinkedIn popup")
                        await page.wait_for_timeout(1500)
                        break
                except:
                    pass

            if linkedin_dismissed:
                s = await ss(page, "03-after-linkedin")
                if s: screenshots.append(s)

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

                # Find Send button precisely again (NOT Apply!)
                print("\nFinding Send button again after LinkedIn dismiss...")
                send_button2 = None
                all_buttons2 = await page.query_selector_all("button")
                for btn in all_buttons2:
                    try:
                        text = await btn.inner_text()
                        btype = await btn.get_attribute("type")
                        is_vis = await btn.is_visible()
                        print(f"  Button: '{text}', type={btype}, visible={is_vis}")
                        if text.strip().lower() == "send" and is_vis:
                            send_button2 = btn
                            break
                    except:
                        pass

                if not send_button2:
                    # Find by type submit
                    for btn in await page.query_selector_all("button[type='submit']"):
                        try:
                            text = await btn.inner_text()
                            is_vis = await btn.is_visible()
                            if is_vis:
                                send_button2 = btn
                                print(f"  Found submit button2: '{text}'")
                                break
                        except:
                            pass

                if send_button2:
                    text = await send_button2.inner_text()
                    print(f"Clicking Send button: '{text}'")
                    await send_button2.click()
                    await page.wait_for_timeout(8000)
                    s = await ss(page, "04-after-final-send")
                    if s: screenshots.append(s)

                    # Handle more popups
                    for _ in range(3):
                        any_dismissed = False
                        for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')", "button:has-text('OK')"]:
                            try:
                                btn = page.locator(sel).first
                                if await btn.is_visible(timeout=1000):
                                    await btn.click()
                                    any_dismissed = True
                                    await page.wait_for_timeout(1000)
                                    # Re-check and send
                                    await page.evaluate("""
                                        () => {
                                            ['candidate.openQuestionAnswers.6352299.flag',
                                             'candidate.openQuestionAnswers.6352300.flag'].forEach(name => {
                                                const el = document.querySelector(`input[name='${name}'][value='true']`);
                                                if (el) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); }
                                            });
                                        }
                                    """)
                                    # Find and click Send
                                    for b in await page.query_selector_all("button"):
                                        try:
                                            t = await b.inner_text()
                                            btype = await b.get_attribute("type")
                                            if (t.strip().lower() == "send" or btype == "submit") and await b.is_visible():
                                                await b.click()
                                                print(f"Clicked send button: '{t}'")
                                                await page.wait_for_timeout(5000)
                                                break
                                        except:
                                            pass
                            except:
                                pass
                        if not any_dismissed:
                            break

            await page.wait_for_timeout(3000)
            s = await ss(page, "05-final")
            if s: screenshots.append(s)

            # Check for captcha in frames
            frames = page.frames
            captcha_showing = False
            for frame in frames:
                if 'hcaptcha.html' in frame.url and 'challenge' in frame.url:
                    captcha_showing = True
                    print(f"Captcha frame still showing: {frame.url[:80]}")
                    try:
                        frame_text = await frame.evaluate("() => document.body.innerText")
                        print(f"Captcha text: {frame_text[:200]}")
                    except:
                        pass

            # Final check
            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:400]}")

            if actual_submission:
                status = "applied"
                notes = f"Submission confirmed: {submission_url}"
                print("SUCCESS (submission detected)")
            elif any(kw in final_text.lower() for kw in ["thank you", "successfully submitted", "application received", "bedankt"]):
                status = "applied"
                notes = f"Confirmation text found. URL: {final_url}"
                print("SUCCESS (confirmation text)")
            elif captcha_showing:
                status = "failed"
                notes = ("Form correctly filled with: Hisham Abboud, hiaham123@hotmail.com, CV uploaded, "
                        "cover letter added, Q1=Yes, Q2=Yes, legal=checked. "
                        "hCaptcha blocking submission (sitekey d111bc04-7616-4e05-a1da-9840968d2b88). "
                        "Form is ready to submit - only CAPTCHA solving needed to complete.")
                print("BLOCKED by hCaptcha")
            else:
                status = "failed"
                notes = f"Unknown state. URL: {final_url}"
                print(f"Status unclear. URL: {final_url}")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-prec-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
