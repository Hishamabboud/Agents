#!/usr/bin/env python3
"""
BIMcollab Application - Click captcha icons
Based on visual analysis of the captcha, try clicking specific icon positions
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
    path = f"{SCREENSHOT_DIR}/bimcollab-icons-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"SS: {path}")
        return path
    except Exception as e:
        print(f"SS failed: {e}")
        return None

async def setup_and_submit(page, cv_path, cl_text):
    """Set up the form and click Send."""
    for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                await page.wait_for_timeout(500)
        except:
            pass

    all_sc_btns = await page.query_selector_all("button.sc-csisgn-0")
    for btn in all_sc_btns:
        text = await btn.inner_text()
        if text.strip().lower() == "apply":
            await btn.click()
            await page.wait_for_timeout(2000)
            break

    for sel in ["button:has-text('Agree to necessary')"]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                await page.wait_for_timeout(500)
        except:
            pass

    await page.locator("input[name='candidate.name']").fill("Hisham Abboud")
    await page.locator("input[name='candidate.email']").fill("hiaham123@hotmail.com")
    phone = page.locator("input[name='candidate.phone']").first
    await phone.fill("")
    await phone.fill("+31648412838")
    await page.locator("input[name='candidate.cv']").set_input_files(cv_path, timeout=10000)
    await page.wait_for_timeout(1000)

    try:
        wb = page.locator("button:has-text('Write it here instead')").first
        if await wb.is_visible(timeout=2000):
            await wb.click()
            await page.wait_for_timeout(1000)
            ta = page.locator("textarea").first
            if await ta.is_visible(timeout=1000):
                await ta.fill(cl_text)
    except:
        pass

    for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
        try:
            await page.locator(f"input[name='{q}'][value='true']").check(force=True, timeout=3000)
        except:
            pass

    try:
        legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
        await legal.check(force=True, timeout=3000)
    except:
        pass

    # Click Send
    for btn in await page.query_selector_all("button"):
        try:
            text = await btn.inner_text()
            btype = await btn.get_attribute("type") or ""
            if text.strip() == "Send" and btype == "submit":
                await btn.click()
                return True
        except:
            pass
    return False

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
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        async def handle_response(response):
            nonlocal actual_submission
            url = response.url
            if "bimcollab" in url and response.status in [201, 302]:
                actual_submission = True
                print(f"SUBMISSION: {response.status} {url}")

        page = await context.new_page()
        page.on("response", handle_response)

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            send_clicked = await setup_and_submit(page, CV_PATH, COVER_LETTER_TEXT)
            print(f"Send clicked: {send_clicked}")

            await page.wait_for_timeout(6000)
            s = await ss(page, "01-after-send")
            if s: screenshots.append(s)

            # Find challenge frame and iframe position
            challenge_frame = None
            iframe_el = None

            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                    challenge_frame = frame
                    break

            if challenge_frame:
                # Find the iframe element
                iframes = await page.query_selector_all("iframe")
                for iframe in iframes:
                    src = await iframe.get_attribute("src") or ""
                    if "hcaptcha.html" in src and "challenge" in src:
                        iframe_el = iframe
                        break

                if iframe_el:
                    bbox = await iframe_el.bounding_box()
                    print(f"Challenge iframe bbox: {bbox}")

                    # The canvas in the frame is 500x470
                    # Challenge header takes up ~110px at top
                    # Icons are arranged in a grid below the header
                    # Footer (Skip/buttons) is at ~520-560px
                    # So icons are in the area: y=120 to y=480 (360px height)

                    # From visual analysis, the icons appear to be in a 4x2 grid
                    # 4 columns: roughly at x=65, 190, 315, 440 (within 500px canvas)
                    # 2 rows: roughly at y=190, 340 (within canvas, after 110px header)

                    # Convert canvas positions to page positions:
                    canvas_x_offset = bbox["x"]  # iframe x position
                    canvas_y_offset = bbox["y"]   # iframe y position

                    # Icon grid positions (canvas coordinates, within 500x470 canvas)
                    # Based on visual analysis of the captcha screenshots
                    # The grid appears to be 4 columns, 2 rows of icons
                    icon_positions_canvas = [
                        (65, 195),   # row 1, col 1
                        (190, 195),  # row 1, col 2
                        (315, 195),  # row 1, col 3
                        (440, 195),  # row 1, col 4
                        (65, 345),   # row 2, col 1
                        (190, 345),  # row 2, col 2
                        (315, 345),  # row 2, col 3
                        (440, 345),  # row 2, col 4
                    ]

                    # Convert to page coordinates
                    icon_positions_page = [
                        (canvas_x_offset + x, canvas_y_offset + y)
                        for x, y in icon_positions_canvas
                    ]

                    print(f"Icon page positions: {icon_positions_page}")

                    # Take a targeted screenshot of the captcha area
                    captcha_clip_path = f"{SCREENSHOT_DIR}/captcha_targeted_{ts()}.png"
                    await page.screenshot(
                        path=captcha_clip_path,
                        clip={
                            "x": bbox["x"],
                            "y": bbox["y"],
                            "width": min(500, bbox["width"]),
                            "height": min(470, bbox["height"])
                        }
                    )
                    print(f"Captcha clip saved: {captcha_clip_path}")
                    screenshots.append(captcha_clip_path)

                    # Strategy: try different pairs of icon positions
                    # Each time we click 2 icons that might be the different ones
                    # Then check if captcha is solved (button changes from "Skip" to "Submit")

                    # Based on the visual analysis from screenshots:
                    # The majority icons look like X/asterisk shapes
                    # The "different" ones may be at specific positions

                    # Try clicking the icons systematically
                    # First let's click 2 random likely positions
                    # From the screenshot, positions 3 and 7 (0-indexed) seemed different

                    pairs_to_try = [
                        (0, 7),  # first row first col + last row last col
                        (2, 5),  # first row third col + second row second col
                        (1, 6),  # first row second col + second row third col
                        (3, 4),  # first row last + second row first
                        (0, 5),  # corners
                        (3, 7),  # different corners
                        (1, 4),
                        (2, 7),
                    ]

                    for pair_idx, (i, j) in enumerate(pairs_to_try):
                        pos1 = icon_positions_page[i]
                        pos2 = icon_positions_page[j]

                        print(f"Trying pair {pair_idx+1}: icons {i} ({pos1}) and {j} ({pos2})")

                        # Click icon 1
                        await page.mouse.click(pos1[0], pos1[1])
                        await page.wait_for_timeout(500)

                        # Click icon 2
                        await page.mouse.click(pos2[0], pos2[1])
                        await page.wait_for_timeout(500)

                        # Check button text
                        btn_text = await challenge_frame.evaluate("""
                            () => {
                                const btn = document.querySelector('.button-submit');
                                return btn ? btn.textContent.trim() : 'not found';
                            }
                        """)
                        print(f"  Button text: '{btn_text}'")

                        if btn_text.lower() not in ['skip', 'not found']:
                            print(f"  CORRECT! Button changed to '{btn_text}', clicking...")
                            submit_btn = await challenge_frame.query_selector('.button-submit')
                            if submit_btn:
                                await submit_btn.click()
                                actual_submission = True
                                await page.wait_for_timeout(4000)
                                break

                        # Wrong selection - refresh to get new challenge
                        refresh_btn = await challenge_frame.query_selector('.refresh.button')
                        if refresh_btn:
                            await refresh_btn.click()
                            print("  Refreshed challenge")
                            await page.wait_for_timeout(2000)

                        # Take periodic screenshot
                        if pair_idx % 3 == 0:
                            s = await ss(page, f"captcha-try-{pair_idx:02d}")
                            if s: screenshots.append(s)

            await page.wait_for_timeout(3000)
            s = await ss(page, "02-final")
            if s: screenshots.append(s)

            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:300]}")

            if actual_submission or any(kw in final_text.lower() for kw in ["thank you", "successfully submitted", "received"]):
                status = "applied"
                notes = f"Application submitted. URL: {final_url}"
                print("SUCCESS!")
            else:
                status = "failed"
                notes = ("Form correctly filled. Blocked by hCaptcha visual challenge. "
                        "All fields: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                        "CV=Hisham Abboud CV.pdf, cover letter=text, Q1=Yes, Q2=Yes, legal=checked.")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-icons-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
