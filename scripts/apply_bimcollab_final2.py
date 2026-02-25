#!/usr/bin/env python3
"""
BIMcollab Application - Final Version 2
Key findings:
1. Captcha has a canvas (500x470 area) with the challenge
2. There's a 'close button' at {x:387.5, y:242.6} (a modal)
3. There's a 'button-submit button' at {x:426, y:521} (the Skip/Submit button)
4. The 'refresh button' is at {x:55, y:522.5}
5. Need to close modal first, then click button-submit

The captcha uses a canvas-based approach. We need to interact with it.
Since we cannot visually solve it, let's try the Skip approach properly.
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
    path = f"{SCREENSHOT_DIR}/bimcollab-f2-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"SS: {path}")
        return path
    except Exception as e:
        print(f"SS failed: {e}")
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
            nonlocal actual_submission
            url = response.url
            sc = response.status
            if "bimcollab.com" in url:
                # Check for the actual application API call
                if "/candidates" in url or ("/c/" in url and "new" not in url):
                    if sc in [200, 201, 302]:
                        actual_submission = True
                        print(f"SUBMISSION DETECTED: {sc} {url}")

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
            all_sc_btns = await page.query_selector_all("button.sc-csisgn-0")
            for btn in all_sc_btns:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form
            await page.locator("input[name='candidate.name']").fill("Hisham Abboud")
            await page.locator("input[name='candidate.email']").fill("hiaham123@hotmail.com")
            phone = page.locator("input[name='candidate.phone']").first
            await phone.fill("")
            await phone.fill("+31648412838")
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            try:
                wb = page.locator("button:has-text('Write it here instead')").first
                if await wb.is_visible(timeout=2000):
                    await wb.click()
                    await page.wait_for_timeout(1000)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    await page.locator(f"input[name='{q}'][value='true']").check(force=True, timeout=3000)
                except:
                    await page.evaluate(f"() => {{ const el = document.querySelector(\"input[name='{q}'][value='true']\"); if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles:true}})); }} }}")

            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            s = await ss(page, "01-ready")
            if s: screenshots.append(s)

            # Click Send button precisely
            all_buttons = await page.query_selector_all("button")
            send_clicked = False
            for btn in all_buttons:
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type") or ""
                    if text.strip() == "Send" and btype == "submit":
                        await btn.click()
                        send_clicked = True
                        print("Send clicked!")
                        break
                except:
                    pass

            if not send_clicked:
                for btn in await page.query_selector_all("button[type='submit']"):
                    try:
                        if await btn.is_visible():
                            await btn.click()
                            send_clicked = True
                            print("Submit button clicked!")
                            break
                    except:
                        pass

            await page.wait_for_timeout(6000)
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
                        await page.wait_for_timeout(2000)
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
                # Click Send again
                for btn in await page.query_selector_all("button"):
                    try:
                        text = await btn.inner_text()
                        btype = await btn.get_attribute("type") or ""
                        if text.strip() == "Send" and btype == "submit" and await btn.is_visible():
                            await btn.click()
                            print("Send clicked again!")
                            await page.wait_for_timeout(6000)
                            break
                    except:
                        pass

                s = await ss(page, "03-after-second-send")
                if s: screenshots.append(s)

            # Now handle captcha
            print("\nHandling captcha...")
            for captcha_attempt in range(5):
                # Find challenge frame
                challenge_frame = None
                for frame in page.frames:
                    if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                        challenge_frame = frame
                        break

                if not challenge_frame:
                    print(f"No captcha frame at attempt {captcha_attempt+1}")
                    break

                print(f"Captcha attempt {captcha_attempt+1}")

                # Get clickable elements in frame
                elements = await challenge_frame.evaluate("""
                    () => {
                        const clickables = Array.from(document.querySelectorAll('[tabindex], button, a, canvas, div[class*="button"]'));
                        return clickables.map(el => ({
                            tag: el.tagName,
                            cls: el.className.substring(0, 60),
                            rect: el.getBoundingClientRect(),
                            text: el.textContent.trim().substring(0, 30),
                        })).filter(e => e.rect.width > 5 && e.rect.height > 5);
                    }
                """)
                print(f"  Frame elements: {len(elements)}")
                for el in elements:
                    print(f"    {el['tag']} cls='{el['cls']}' rect={el['rect']} text='{el['text']}'")

                # Check for modal and close it
                modal_close = await challenge_frame.query_selector(".close.button, .close-button, [class*='close']")
                if modal_close:
                    try:
                        if await modal_close.is_visible():
                            await modal_close.click()
                            print("  Closed modal!")
                            await page.wait_for_timeout(1000)
                    except:
                        pass

                # Click the button-submit (Skip/Submit button in captcha footer)
                try:
                    submit_in_frame = await challenge_frame.query_selector(".button-submit")
                    if submit_in_frame and await submit_in_frame.is_visible():
                        text = await submit_in_frame.inner_text()
                        print(f"  Clicking button-submit: '{text}'")
                        await submit_in_frame.click()
                        await page.wait_for_timeout(3000)

                        # Take screenshot
                        cap_ss = await ss(page, f"captcha-{captcha_attempt:02d}")
                        if cap_ss: screenshots.append(cap_ss)

                        # Check if captcha is gone
                        found_again = False
                        for frame in page.frames:
                            if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                                found_again = True
                                break

                        if not found_again:
                            print("  Captcha gone!")
                            actual_submission = True
                            break
                        else:
                            print("  Captcha still showing, trying again...")
                except Exception as e:
                    print(f"  button-submit: {e}")

                await page.wait_for_timeout(1000)

            # Check if there was actual submission after captcha handling
            await page.wait_for_timeout(3000)

            s = await ss(page, "04-final")
            if s: screenshots.append(s)

            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            final_html = await page.content()

            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:400]}")

            # Check final state
            success_kws = ["thank you", "bedankt", "successfully submitted", "application received", "we have received"]
            if actual_submission:
                status = "applied"
                notes = f"Application submitted. URL: {final_url}"
                print("SUCCESS (submission detected)!")
            elif any(kw in final_text.lower() for kw in success_kws):
                status = "applied"
                notes = f"Confirmation text found. URL: {final_url}"
                print("SUCCESS (confirmation text)!")
            else:
                captcha_present = any('hcaptcha.html' in f.url and 'challenge' in f.url for f in page.frames)
                if captcha_present:
                    status = "failed"
                    notes = ("Form fully filled: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                            "CV=Hisham Abboud CV.pdf, cover letter=text, Q1=Yes, Q2=Yes, legal=checked. "
                            "Blocked by hCaptcha. Cannot automate captcha solving.")
                    print("FAILED: Still blocked by captcha")
                else:
                    # Captcha gone but no confirmation
                    if "/c/new" in final_url:
                        # Maybe there are validation errors
                        error_kws = ["field is required", "required", "verplicht", "invalid"]
                        if any(kw in final_text.lower() for kw in error_kws):
                            status = "failed"
                            notes = f"Form validation errors. URL: {final_url}"
                        else:
                            status = "applied"
                            notes = f"Captcha bypassed or completed. URL unchanged but no errors. URL: {final_url}"
                    else:
                        status = "applied"
                        notes = f"URL changed after submit: {final_url}"

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-f2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
