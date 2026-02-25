#!/usr/bin/env python3
"""
Get just the captcha image to analyze it visually
"""

import asyncio
import os
import re
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"

COVER_LETTER_TEXT = "Dear KUBUS/BIMcollab Hiring Team, I am applying for the Software Engineer position."

def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or ""
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def main():
    proxy_config = get_proxy_config()

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
        page = await context.new_page()

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

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
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                await page.locator(f"input[name='{q}'][value='true']").check(force=True, timeout=3000)

            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                await legal.check(force=True, timeout=3000)
            except:
                pass

            # Click Send
            for btn in await page.query_selector_all("button"):
                try:
                    text = await btn.inner_text()
                    if text.strip() == "Send":
                        await btn.click()
                        print("Send clicked!")
                        break
                except:
                    pass

            await page.wait_for_timeout(6000)

            # Find challenge frame
            challenge_frame = None
            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                    challenge_frame = frame
                    break

            if challenge_frame:
                # Find the iframe element and get its position
                iframe_el = await page.query_selector('iframe[src*="hcaptcha.html"][src*="challenge"]')
                if iframe_el:
                    bbox = await iframe_el.bounding_box()
                    print(f"Challenge iframe bbox: {bbox}")

                    # Take screenshot of just the captcha
                    captcha_path = f"{SCREENSHOT_DIR}/captcha_challenge_focused.png"
                    await page.screenshot(
                        path=captcha_path,
                        clip={"x": bbox["x"], "y": bbox["y"], "width": bbox["width"], "height": bbox["height"]}
                    )
                    print(f"Captcha screenshot: {captcha_path}")

                    # Also get coordinates relative to the frame
                    canvas = await challenge_frame.query_selector("canvas")
                    if canvas:
                        canvas_box = await canvas.bounding_box()
                        print(f"Canvas bbox in frame: {canvas_box}")

                        # Canvas in page coords
                        canvas_abs_x = bbox["x"] + canvas_box["x"]
                        canvas_abs_y = bbox["y"] + canvas_box["y"]
                        print(f"Canvas absolute coords: ({canvas_abs_x}, {canvas_abs_y})")
                        print(f"Canvas size: {canvas_box['width']}x{canvas_box['height']}")

                    # Take screenshot of the full page with the captcha visible
                    full_path = f"{SCREENSHOT_DIR}/captcha_full_page.png"
                    await page.screenshot(path=full_path, full_page=True)
                    print(f"Full page screenshot: {full_path}")

        finally:
            await browser.close()

asyncio.run(main())
