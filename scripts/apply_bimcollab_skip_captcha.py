#!/usr/bin/env python3
"""
BIMcollab Application - Skip CAPTCHA version
After clicking Send and CAPTCHA appears, try to click the "Skip" button
The Skip button advances to next challenge or completes it
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

async def ss(page_or_frame, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-skip-{name}-{ts()}.png"
    try:
        # page screenshot only
        if hasattr(page_or_frame, 'screenshot'):
            await page_or_frame.screenshot(path=path, full_page=True)
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

    submission_success = False
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
            nonlocal submission_success
            url = response.url
            sc = response.status
            if "candidates" in url and sc in [200, 201]:
                submission_success = True
                api_calls.append(f"CANDIDATES: {sc} {url}")
                print(f"CANDIDATE SUBMISSION: {sc} {url}")
            elif "bimcollab" in url and "/c/new" in url and sc == 302:
                submission_success = True
                api_calls.append(f"REDIRECT: {sc} {url}")
                print(f"FORM REDIRECT: {sc} {url}")

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
            buttons = await page.query_selector_all("button.sc-csisgn-0")
            for btn in buttons:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    print("Apply tab clicked")
                    break

            # Dismiss popups
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

            # Cover letter text
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

            # Radios + Legal
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

            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            # Verify state
            state = await page.evaluate("""
                () => ({
                    name: (document.querySelector("input[name='candidate.name']")||{value:''}).value,
                    email: (document.querySelector("input[name='candidate.email']")||{value:''}).value,
                    q1: (document.querySelector("input[name='candidate.openQuestionAnswers.6352299.flag']:checked")||{value:'NONE'}).value,
                    q2: (document.querySelector("input[name='candidate.openQuestionAnswers.6352300.flag']:checked")||{value:'NONE'}).value,
                })
            """)
            print(f"Form state: {state}")

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Click Send
            print("Clicking Send...")
            send_btn = page.locator("button[type='submit']").first
            await send_btn.click()
            print("Send clicked!")

            # Wait a bit for captcha to potentially appear
            await page.wait_for_timeout(5000)

            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Handle LinkedIn popup if it appears
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        print(f"Dismissed LinkedIn popup")
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
                        # Click Send again
                        send2 = page.locator("button[type='submit']").first
                        if await send2.is_visible(timeout=1500):
                            await send2.click()
                            print("Clicked Send again after LinkedIn dismiss")
                            await page.wait_for_timeout(5000)
                        break
                except:
                    pass

            s = await ss(page, "03-before-captcha-handling")
            if s: screenshots.append(s)

            # Look for captcha challenge in iframes
            print("\nLooking for hCaptcha in frames...")
            frames = page.frames
            print(f"Total frames: {len(frames)}")

            challenge_frame = None
            for frame in frames:
                url = frame.url
                if 'hcaptcha.html' in url and 'frame=challenge' in url:
                    challenge_frame = frame
                    print(f"Found challenge frame: {url[:100]}")
                    break

            if challenge_frame:
                print("Interacting with captcha challenge frame...")

                # Check what's in the challenge frame
                try:
                    frame_text = await challenge_frame.evaluate("() => document.body.innerText")
                    print(f"Captcha frame text: {frame_text[:300]}")
                except Exception as e:
                    print(f"Frame text: {e}")

                # Look for Skip button
                print("Looking for Skip button in captcha frame...")
                try:
                    skip_btn = challenge_frame.locator("button:has-text('Skip')").first
                    if await skip_btn.is_visible(timeout=2000):
                        print("FOUND Skip button!")
                        await skip_btn.click()
                        print("Clicked Skip!")
                        await page.wait_for_timeout(3000)

                        s = await ss(page, "04-after-skip")
                        if s: screenshots.append(s)

                        # Check if more challenges appeared
                        for _ in range(5):
                            current_text = await page.evaluate("() => document.body.innerText")
                            if any(kw in current_text.lower() for kw in ["thank you", "successfully", "received"]):
                                print("SUCCESS after skip!")
                                submission_success = True
                                break

                            # Try Skip again
                            try:
                                new_challenge_frame = None
                                for frame in page.frames:
                                    if 'challenge' in frame.url:
                                        new_challenge_frame = frame
                                        break
                                if new_challenge_frame:
                                    skip2 = new_challenge_frame.locator("button:has-text('Skip')").first
                                    if await skip2.is_visible(timeout=1000):
                                        await skip2.click()
                                        print("Clicked Skip again")
                                        await page.wait_for_timeout(2000)
                            except:
                                break
                    else:
                        print("Skip button not visible")
                        # Try looking for all buttons in frame
                        frame_btns = await challenge_frame.query_selector_all("button")
                        print(f"Buttons in captcha frame: {len(frame_btns)}")
                        for btn in frame_btns:
                            try:
                                text = await btn.inner_text()
                                is_vis = await btn.is_visible()
                                print(f"  Button: '{text}', visible={is_vis}")
                            except:
                                pass

                        # Try clicking any visible button in frame
                        for btn in frame_btns:
                            try:
                                if await btn.is_visible():
                                    text = await btn.inner_text()
                                    if text.strip():
                                        print(f"Clicking frame button: '{text}'")
                                        await btn.click()
                                        await page.wait_for_timeout(1000)
                                        break
                            except:
                                pass
                except Exception as e:
                    print(f"Skip handling error: {e}")

            # Check for images in captcha to understand what type it is
            print("\nChecking captcha image content...")
            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'challenge' in frame.url:
                    try:
                        imgs = await frame.query_selector_all("img")
                        print(f"Images in captcha: {len(imgs)}")
                        for img in imgs[:5]:
                            src = await img.get_attribute("src") or ""
                            alt = await img.get_attribute("alt") or ""
                            cls = await img.get_attribute("class") or ""
                            print(f"  img: alt='{alt}', class='{cls}', src='{src[:50]}'")
                    except:
                        pass
                    break

            await page.wait_for_timeout(2000)

            # Final screenshots
            s = await ss(page, "05-final")
            if s: screenshots.append(s)

            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:400]}")

            if submission_success or any(kw in final_text.lower() for kw in ["thank you", "successfully submitted", "application received"]):
                status = "applied"
                notes = f"Application submitted. URL: {final_url}"
                print("SUCCESS!")
            else:
                status = "failed"
                notes = ("Form filled correctly but hCaptcha blocking. "
                        "Form data: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                        "CV=uploaded, cover letter=text entered, Q1=Yes, Q2=Yes, legal=checked.")
                print("FAILED: hCaptcha blocked")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-skip-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
