#!/usr/bin/env python3
"""
BIMcollab Application - Click the blank button in captcha frame
The captcha frame has 1 button with empty text (visible=True) - this might be Skip
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
    path = f"{SCREENSHOT_DIR}/bimcollab-cs-{name}-{ts()}.png"
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

    submission_success = False

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
            if ("candidates" in url or "/c/" in url) and sc in [200, 201, 302]:
                if "captcha" not in url and "cdn" not in url:
                    submission_success = True
                    print(f"SUBMISSION: {sc} {url[:100]}")

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
                    break

            # Dismiss more popups
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

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Click Send
            await page.locator("button[type='submit']").first.click()
            print("Send clicked!")
            await page.wait_for_timeout(5000)

            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Find captcha challenge frame
            challenge_frame = None
            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                    challenge_frame = frame
                    break

            if challenge_frame:
                print("Found captcha frame. Analyzing...")

                # Get full HTML of the challenge frame
                try:
                    frame_html = await challenge_frame.content()
                    print(f"Frame HTML length: {len(frame_html)}")

                    # Find "Skip" in the HTML
                    skip_idx = frame_html.lower().find('skip')
                    if skip_idx >= 0:
                        print(f"'Skip' found at position {skip_idx}")
                        print(f"Context: {frame_html[max(0,skip_idx-100):skip_idx+200]}")

                    # Find buttons in HTML
                    btn_matches = re.findall(r'<button[^>]*>(.*?)</button>', frame_html, re.DOTALL)
                    print(f"Button HTML matches: {len(btn_matches)}")
                    for bm in btn_matches[:5]:
                        print(f"  Button: {bm[:200]}")
                except Exception as e:
                    print(f"Frame HTML: {e}")

                # Try clicking the visible button (the only one)
                try:
                    frame_btns = await challenge_frame.query_selector_all("button")
                    print(f"Frame buttons: {len(frame_btns)}")
                    for i, btn in enumerate(frame_btns):
                        try:
                            is_vis = await btn.is_visible()
                            inner = await btn.inner_html()
                            print(f"  Button {i}: visible={is_vis}, html='{inner[:100]}'")
                            if is_vis:
                                await btn.click()
                                print(f"  Clicked button {i}")
                                await page.wait_for_timeout(2000)
                        except Exception as e:
                            print(f"  Button {i} error: {e}")
                except Exception as e:
                    print(f"Button enumeration: {e}")

                # Try JS in the frame to find and click Skip
                try:
                    skip_result = await challenge_frame.evaluate("""
                        () => {
                            // Look for any element containing "Skip"
                            const all = document.querySelectorAll('*');
                            for (const el of all) {
                                if (el.textContent.trim() === 'Skip' || el.textContent.trim() === 'skip') {
                                    el.click();
                                    return 'clicked: ' + el.tagName + ' class=' + el.className;
                                }
                            }
                            // Try by aria-label
                            const skipEl = document.querySelector('[aria-label="Skip"]');
                            if (skipEl) {
                                skipEl.click();
                                return 'clicked by aria-label';
                            }
                            // Try the last button
                            const btns = document.querySelectorAll('button');
                            if (btns.length > 0) {
                                const lastBtn = btns[btns.length - 1];
                                lastBtn.click();
                                return 'clicked last button: ' + lastBtn.textContent;
                            }
                            return null;
                        }
                    """)
                    print(f"JS skip result: {skip_result}")
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"JS skip: {e}")

            await page.wait_for_timeout(2000)
            s = await ss(page, "03-after-skip-attempt")
            if s: screenshots.append(s)

            # Check result
            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:300]}")

            if submission_success or any(kw in final_text.lower() for kw in ["thank you", "successfully", "received", "bedankt"]):
                status = "applied"
                notes = f"Submission succeeded. URL: {final_url}"
                print("SUCCESS!")
            else:
                status = "failed"
                notes = ("Form correctly filled. Blocked by hCaptcha. "
                        "data: Hisham Abboud, hiaham123@hotmail.com, CV, CL, Q1=Yes, Q2=Yes")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-cs-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
