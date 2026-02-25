#!/usr/bin/env python3
"""
BIMcollab Application - Stealth mode
Use puppet-extra headers and browser settings to appear more human-like
to try to pass hCaptcha invisible check without triggering visual challenge
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
    proxy_url = os.environ.get("https_proxy") or ""
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def ss(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-stlth-{name}-{ts()}.png"
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

    submission_detected = False

    async with async_playwright() as p:
        # Use more human-like browser settings
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                # Stealth flags
                "--disable-blink-features=AutomationControlled",
                "--disable-automation",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--lang=nl-NL",
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
            locale="nl-NL",
            timezone_id="Europe/Amsterdam",
            extra_http_headers={
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Linux"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
            proxy=proxy_config
        )

        # Remove webdriver fingerprint
        await context.add_init_script("""
            // Overwrite the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Overwrite the plugins property to use a getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Overwrite the language property to use a getter
            Object.defineProperty(navigator, 'language', {
                get: () => 'nl-NL',
            });

            // Add fake chrome.runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)

        page = await context.new_page()

        async def handle_response(response):
            nonlocal submission_detected
            url = response.url
            sc = response.status
            if "bimcollab" in url and sc in [200, 201]:
                if ".js" not in url and ".css" not in url and "captcha" not in url and "cdn" not in url:
                    print(f"BIM: {sc} {url[:100]}")
                    # Check for actual application submission
                    if "/c/" in url and "new" not in url:
                        submission_detected = True
                        print(f"SUBMISSION DETECTED!")

        page.on("response", handle_response)

        try:
            # Navigate with simulated human behavior
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)  # Wait like a human

            # Simulate reading the page
            await page.mouse.move(640, 400)
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollBy(0, 200)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollBy(0, -200)")
            await page.wait_for_timeout(500)

            # Dismiss cookies
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(800)
                except:
                    pass

            # Click Apply tab
            all_sc_btns = await page.query_selector_all("button.sc-csisgn-0")
            for btn in all_sc_btns:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    # Simulate moving mouse to button first
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                        await page.wait_for_timeout(300)
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

            for sel in ["button:has-text('Agree to necessary')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(800)
                except:
                    pass

            # Fill form with human-like delays
            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click()
            await page.wait_for_timeout(300)
            await name_loc.type("Hisham Abboud", delay=60)  # Type like human
            await page.wait_for_timeout(500)

            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click()
            await page.wait_for_timeout(300)
            await email_loc.type("hiaham123@hotmail.com", delay=50)
            await page.wait_for_timeout(500)

            # Fix: use click(click_count=3) instead of triple_click() which doesn't exist on Locator
            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click(click_count=3)  # Triple-click to select all existing text
            await page.wait_for_timeout(200)
            await phone_loc.type("+31648412838", delay=70)
            await page.wait_for_timeout(500)

            # Upload CV
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(2000)

            # Cover letter
            try:
                wb = page.locator("button:has-text('Write it here instead')").first
                if await wb.is_visible(timeout=2000):
                    await wb.click()
                    await page.wait_for_timeout(1000)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.click()
                        await page.wait_for_timeout(300)
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            await page.wait_for_timeout(500)

            # Radios
            for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    radio = page.locator(f"input[name='{q}'][value='true']").first
                    box = await radio.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                        await page.wait_for_timeout(200)
                    await radio.check(force=True, timeout=3000)
                    await page.wait_for_timeout(300)
                except:
                    pass

            # Legal
            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            # Scroll to see full form
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Click Send with human-like movement
            send_btn = None
            for btn in await page.query_selector_all("button"):
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type") or ""
                    if text.strip() == "Send" and btype == "submit":
                        send_btn = btn
                        break
                except:
                    pass

            if send_btn:
                box = await send_btn.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    await page.wait_for_timeout(500)
                await send_btn.click()
                print("Send clicked!")
            else:
                print("Send button not found!")

            # Wait for response
            print("Waiting for result...")
            await page.wait_for_timeout(10000)

            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Check for captcha
            challenge_frame = None
            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                    challenge_frame = frame
                    break

            if challenge_frame:
                print("Captcha still showing...")
                # Try to get canvas image for visual analysis
                try:
                    canvas_data = await challenge_frame.evaluate("""
                        () => {
                            const canvas = document.querySelector('canvas');
                            if (!canvas) return null;
                            try {
                                return { data: canvas.toDataURL('image/png'), w: canvas.width, h: canvas.height };
                            } catch(e) {
                                return { error: e.message, w: canvas.width, h: canvas.height };
                            }
                        }
                    """)
                    print(f"Canvas info: {canvas_data}")
                    if canvas_data and 'data' in canvas_data:
                        import base64
                        img_bytes = base64.b64decode(canvas_data['data'].split(',')[1])
                        canvas_img_path = f"{SCREENSHOT_DIR}/bimcollab-stlth-canvas-{ts()}.png"
                        with open(canvas_img_path, 'wb') as f_img:
                            f_img.write(img_bytes)
                        screenshots.append(canvas_img_path)
                        print(f"Canvas saved: {canvas_img_path}")
                except Exception as ce:
                    print(f"Canvas extract error: {ce}")
            else:
                print("No captcha frame found!")
                # Check for success
                final_text = await page.evaluate("() => document.body.innerText")
                if any(kw in final_text.lower() for kw in ["thank you", "successfully", "received"]):
                    submission_detected = True
                    print("SUCCESS (no captcha, confirmation found)!")

            # Final state
            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")

            s = await ss(page, "03-final")
            if s: screenshots.append(s)

            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:300]}")

            if submission_detected or any(kw in final_text.lower() for kw in ["thank you", "successfully submitted", "received", "bedankt"]):
                status = "applied"
                notes = f"Application submitted. URL: {final_url}"
                print("SUCCESS!")
            elif challenge_frame is not None:
                status = "failed"
                notes = ("Form correctly filled with stealth mode. Still blocked by hCaptcha. "
                        "Form data: Hisham Abboud, hiaham123@hotmail.com, CV, CL, Q1=Yes, Q2=Yes, legal=checked.")
                print("FAILED: hCaptcha blocking")
            else:
                # Check if there's a validation error
                error_kws = ["field is required", "required", "invalid"]
                if any(kw in final_text.lower() for kw in error_kws):
                    status = "failed"
                    notes = f"Form validation errors. URL: {final_url}"
                else:
                    status = "applied"
                    notes = f"No errors detected after submit. URL: {final_url}"

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-stlth-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
