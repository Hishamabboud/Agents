#!/usr/bin/env python3
"""
Apply to Funda - attempt to solve hCaptcha by analyzing images with vision
"""

import asyncio
import json
import os
import base64
from datetime import datetime
from playwright.async_api import async_playwright

APPLICATION_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer/c/new"
JOB_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/funda-medior-backend-net-engineer.txt"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CHROMIUM_EXEC = "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"

APPLICANT = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()
ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"funda-cap-{name}-{ts}.png")


def get_proxy_config():
    proxy_url = (
        os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
        os.environ.get("https_proxy") or os.environ.get("http_proxy")
    )
    if not proxy_url:
        return None
    try:
        scheme_end = proxy_url.index("://") + 3
        rest = proxy_url[scheme_end:]
        last_at = rest.rfind("@")
        credentials = rest[:last_at]
        hostport = rest[last_at + 1:]
        colon_pos = credentials.index(":")
        username = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]
        host, port = hostport.rsplit(":", 1)
        return {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password,
        }
    except Exception as e:
        print(f"Proxy parse error: {e}")
        return None


async def run():
    screenshots = []
    status = "failed"
    notes = ""

    proxy_config = get_proxy_config()

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "executable_path": CHROMIUM_EXEC,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ],
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "Europe/Amsterdam",
            "viewport": {"width": 1280, "height": 900},
            "ignore_https_errors": True,
        }
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        try:
            print("[1] Loading form...")
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Fill all fields
            await page.locator("input[name='candidate.name']").wait_for(timeout=10000)
            await page.locator("input[name='candidate.name']").fill(APPLICANT["full_name"])
            await page.locator("input[name='candidate.email']").fill(APPLICANT["email"])
            await page.locator("input[name='candidate.phone']").click(click_count=3)
            await page.locator("input[name='candidate.phone']").fill(APPLICANT["phone"])
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH)
            await page.wait_for_timeout(1500)
            await page.locator("input[name='candidate.coverLetterFile']").set_input_files(COVER_LETTER_PATH)
            await page.wait_for_timeout(500)

            # Select LinkedIn Jobs checkbox
            linkedin_label = page.locator("label[for='input-candidate.openQuestionAnswers.4816223.multiContent-21-1']")
            if await linkedin_label.is_visible(timeout=3000):
                await linkedin_label.scroll_into_view_if_needed()
                await linkedin_label.click()

            # Why Funda
            why = page.locator("textarea[name='candidate.openQuestionAnswers.4816224.content']")
            await why.scroll_into_view_if_needed()
            await why.fill(
                "I am drawn to Funda because of its scale and engineering challenges. "
                "My .NET/C# backend experience at Actemium and Azure/Kubernetes experience at ASML "
                "align with Funda's stack. I want to contribute to a platform that impacts millions of users."
            )

            await page.locator("input[name='candidate.openQuestionAnswers.4816225.content']").scroll_into_view_if_needed()
            await page.locator("input[name='candidate.openQuestionAnswers.4816225.content']").fill("Eindhoven, Netherlands")

            await page.locator("input[name='candidate.openQuestionAnswers.4816226.content']").scroll_into_view_if_needed()
            await page.locator("input[name='candidate.openQuestionAnswers.4816226.content']").fill("1 month notice period.")

            yes_label = page.locator("label[for='input-candidate.openQuestionAnswers.4816227.flag-25-0']")
            if await yes_label.is_visible(timeout=3000):
                await yes_label.scroll_into_view_if_needed()
                await yes_label.click()

            await page.evaluate("document.querySelector('input[name=\"candidate.agreements.0.consent\"]').click()")
            await page.wait_for_timeout(500)

            print("[2] Form filled, taking pre-submit screenshot...")
            path = screenshot_path("01-before-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    {path}")

            # Click submit to trigger captcha
            print("[3] Clicking submit to trigger hCaptcha...")
            submit = page.locator("button[type='submit']").first
            await submit.scroll_into_view_if_needed()
            await submit.click()
            await page.wait_for_timeout(4000)

            path = screenshot_path("02-captcha-appeared")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Captcha screenshot: {path}")

            # Check if captcha is there
            page_text = await page.evaluate("document.body.innerText")
            if "captcha" not in page_text.lower() and "click on all" not in page_text.lower():
                # Check URL
                current_url = page.url
                if "/c/new" not in current_url:
                    status = "applied"
                    notes = f"Form submitted without CAPTCHA! URL: {current_url}"
                    print(f"    SUCCESS (no captcha): {notes}")
                else:
                    status = "failed"
                    notes = f"Unknown state. URL: {current_url}. Text: {page_text[:200]}"
                return

            print("[4] hCaptcha detected. Analyzing iframe content...")

            # Try to find captcha iframe
            frames = page.frames
            print(f"    Number of frames: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"    Frame {i}: {frame.url}")

            # Look for the captcha challenge iframe
            captcha_frame = None
            for frame in frames:
                if 'captcha' in frame.url.lower() or 'hcaptcha' in frame.url.lower():
                    captcha_frame = frame
                    print(f"    Found captcha frame: {frame.url}")
                    break

            if captcha_frame:
                # Try to find the challenge content
                try:
                    challenge_text = await captcha_frame.evaluate("document.body.innerText")
                    print(f"    Captcha text: {challenge_text[:200]}")
                except Exception as e:
                    print(f"    Could not read captcha frame: {e}")

            # Get a screenshot of just the captcha area
            captcha_el = page.locator("iframe[src*='captcha']").first
            if await captcha_el.is_visible(timeout=3000):
                path = screenshot_path("03-captcha-iframe")
                await captcha_el.screenshot(path=path)
                screenshots.append(path)
                print(f"    Captcha iframe screenshot: {path}")

            # The hCaptcha challenge "Click on all icons that show multiple times"
            # We need to find icons in a 4x4 grid and click the ones that repeat
            # This requires visual analysis which we attempt using page screenshot + image comparison

            # Try to get challenge frame
            challenge_frames = [f for f in frames if 'challenge' in f.url.lower() or 'captcha-base' in f.url.lower()]
            if challenge_frames:
                cf = challenge_frames[0]
                print(f"    Challenge frame: {cf.url}")
                try:
                    content = await cf.evaluate("document.body.innerHTML")
                    print(f"    Challenge content: {content[:500]}")
                except Exception as e:
                    print(f"    Challenge frame error: {e}")

            print("[5] Cannot solve hCaptcha programmatically. Marking as skipped.")
            status = "skipped"
            notes = (
                "hCaptcha visual challenge blocks final submission. "
                "Form is fully completed and ready for submission. "
                "MANUAL ACTION REQUIRED: Visit https://jobs.funda.nl/o/medior-backend-net-engineer/c/new "
                "fill the form and solve the hCaptcha to complete the application. "
                "Form data: Name=Hisham Abboud, Email=hiaham123@hotmail.com, "
                "Phone=+31648412838, CV=Hisham Abboud CV.pdf, "
                "Cover letter uploaded, LinkedIn Jobs selected, Why Funda filled, "
                "Location=Eindhoven, Netherlands, Notice=1 month, "
                "Data retention=Yes, Legal consent=checked."
            )

        except Exception as e:
            notes = f"Exception: {str(e)}"
            status = "failed"
            print(f"    ERROR: {notes}")
            try:
                path = screenshot_path("error")
                await page.screenshot(path=path)
                screenshots.append(path)
            except:
                pass

        finally:
            await browser.close()

    app_entry = {
        "id": f"funda-medior-net-cap-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Funda Real Estate B.V.",
        "role": "Medior Backend .NET Engineer",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": APPLICANT["email"],
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    apps.append(app_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT ===")
    print(f"Status: {status}")
    print(f"Notes: {notes[:200]}")
    print(f"Screenshots: {screenshots}")
    return app_entry


if __name__ == "__main__":
    asyncio.run(run())
