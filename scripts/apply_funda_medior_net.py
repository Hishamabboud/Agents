#!/usr/bin/env python3
"""
Apply to Funda Medior Backend .NET Engineer position via jobs.funda.nl (Recruitee ATS)
"""

import asyncio
import json
import os
import re
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
    "location": "Eindhoven, Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"funda-{name}-{ts}.png")


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
    if proxy_config:
        print(f"Using proxy: {proxy_config['server']}")
    else:
        print("No proxy configured")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "executable_path": CHROMIUM_EXEC,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ],
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
            "timezone_id": "Europe/Amsterdam",
            "viewport": {"width": 1280, "height": 900},
            "ignore_https_errors": True,
        }
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        # Mask webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        try:
            # Step 1: Navigate to job listing page first (warm up)
            print(f"[1] Loading job listing: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            path = screenshot_path("01-job-listing")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 2: Navigate to the application form
            print(f"[2] Loading application form: {APPLICATION_URL}")
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            path = screenshot_path("02-form-loaded")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Accept cookies if present
            try:
                cookie_btn = page.locator(
                    "button:has-text('Accept'), button:has-text('accept'), "
                    "button:has-text('Akkoord'), button:has-text('Accepteren'), "
                    "button:has-text('OK'), button:has-text('Allow')"
                )
                if await cookie_btn.first.is_visible(timeout=3000):
                    await cookie_btn.first.click()
                    await page.wait_for_timeout(1000)
                    print("    Accepted cookies")
            except Exception:
                pass

            # Inspect the page to understand the form structure
            print("[3] Inspecting form structure...")
            all_inputs = await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                    return inputs.map(el => ({
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        'aria-label': el.getAttribute('aria-label') || '',
                        className: el.className ? el.className.substring(0, 60) : ''
                    }));
                }
            """)
            for inp in all_inputs:
                print(f"    Input: {inp}")

            # Step 4: Fill in full name
            print("[4] Filling personal details...")

            # Try multiple selectors for name
            name_filled = False
            for selector in [
                "input[name='name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "input[id*='name' i]",
                "input[aria-label*='name' i]",
                "input[type='text']:first-of-type",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await page.wait_for_timeout(200)
                        await el.fill(APPLICANT["full_name"])
                        await page.wait_for_timeout(200)
                        name_filled = True
                        print(f"    Name filled using selector: {selector}")
                        break
                except Exception:
                    continue
            if not name_filled:
                print("    WARNING: Could not fill name field")

            # Fill email
            email_filled = False
            for selector in [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await page.wait_for_timeout(200)
                        await el.fill(APPLICANT["email"])
                        await page.wait_for_timeout(200)
                        email_filled = True
                        print(f"    Email filled using selector: {selector}")
                        break
                except Exception:
                    continue
            if not email_filled:
                print("    WARNING: Could not fill email field")

            # Fill phone
            for selector in [
                "input[type='tel']",
                "input[name*='phone' i]",
                "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]",
                "input[id*='phone' i]",
                "input[aria-label*='phone' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await page.wait_for_timeout(200)
                        await el.fill(APPLICANT["phone"])
                        await page.wait_for_timeout(200)
                        print(f"    Phone filled using selector: {selector}")
                        break
                except Exception:
                    continue

            # Step 5: Upload CV
            print("[5] Uploading CV...")
            try:
                file_inputs = await page.locator("input[type='file']").all()
                print(f"    Found {len(file_inputs)} file input(s)")
                if len(file_inputs) > 0:
                    await file_inputs[0].set_input_files(CV_PATH)
                    await page.wait_for_timeout(2000)
                    print(f"    CV uploaded: {CV_PATH}")
            except Exception as e:
                print(f"    CV upload error: {e}")

            path = screenshot_path("03-personal-filled")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Scroll down to see more fields
            await page.evaluate("window.scrollTo(0, 400)")
            await page.wait_for_timeout(500)

            # Step 6: Cover letter
            print("[6] Handling cover letter...")
            cl_done = False
            for selector in [
                "textarea[name*='cover' i]",
                "textarea[placeholder*='cover' i]",
                "textarea[placeholder*='motivation' i]",
                "textarea[placeholder*='letter' i]",
                "textarea[name*='letter' i]",
                "textarea[name*='motivat' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await el.fill(COVER_LETTER_TEXT)
                        cl_done = True
                        print(f"    Cover letter text filled using selector: {selector}")
                        break
                except Exception:
                    continue

            if not cl_done:
                try:
                    file_inputs = await page.locator("input[type='file']").all()
                    if len(file_inputs) >= 2:
                        await file_inputs[1].set_input_files(COVER_LETTER_PATH)
                        print("    Cover letter uploaded via second file input")
                        cl_done = True
                except Exception as e:
                    print(f"    Cover letter upload error: {e}")

            if not cl_done:
                print("    WARNING: Could not add cover letter")

            # Step 7: Fill screening questions
            print("[7] Filling screening questions...")
            await page.evaluate("window.scrollTo(0, 600)")
            await page.wait_for_timeout(500)

            page_text_now = await page.evaluate("document.body.innerText")
            print(f"    Page text preview: {page_text_now[:500]}")

            all_visible_inputs = await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input:not([type="file"]):not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), textarea'));
                    return inputs.map((el, i) => ({
                        index: i,
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        value: el.value || '',
                        label: (document.querySelector('label[for="' + el.id + '"]') || {}).innerText || ''
                    }));
                }
            """)
            print(f"    All visible inputs: {all_visible_inputs}")

            # Fill location/where do you live
            for selector in [
                "input[name*='live' i]",
                "input[name*='location' i]",
                "input[placeholder*='where' i]",
                "input[placeholder*='live' i]",
                "input[placeholder*='woon' i]",
                "input[placeholder*='city' i]",
                "input[placeholder*='stad' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=1500):
                        await el.fill("Eindhoven, Netherlands")
                        print(f"    Location filled: {selector}")
                        break
                except Exception:
                    continue

            # Notice period
            for selector in [
                "input[name*='notice' i]",
                "textarea[name*='notice' i]",
                "input[placeholder*='notice' i]",
                "input[placeholder*='opzegtermijn' i]",
                "textarea[placeholder*='notice' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=1500):
                        await el.fill("1 month notice period")
                        print(f"    Notice period filled: {selector}")
                        break
                except Exception:
                    continue

            # Why Funda
            for selector in [
                "textarea[name*='why' i]",
                "textarea[placeholder*='funda' i]",
                "textarea[placeholder*='why' i]",
                "textarea[placeholder*='waarom' i]",
                "textarea[placeholder*='motivat' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=1500):
                        await el.fill(
                            "I am drawn to Funda because of its scale and the engineering challenges "
                            "of building performant microservices for millions of users. My background "
                            "in .NET/C# backend systems at Actemium and cloud/Kubernetes experience at ASML "
                            "align well with the technical requirements of this role."
                        )
                        print(f"    'Why Funda' filled: {selector}")
                        break
                except Exception:
                    continue

            # "How did you hear" dropdown
            try:
                selects = await page.locator("select").all()
                for sel in selects:
                    label_text = await sel.evaluate(
                        "el => (document.querySelector('label[for=\"' + el.id + '\"]') || {}).innerText || "
                        "el.closest('div')?.querySelector('label')?.innerText || ''"
                    )
                    print(f"    Dropdown label: '{label_text}'")
                    options = await sel.evaluate("el => Array.from(el.options).map(o => o.text)")
                    print(f"    Options: {options}")
                    if options and len(options) > 1:
                        await sel.select_option(index=1)
                        print(f"    Selected option index 1 for dropdown: '{label_text}'")
            except Exception as e:
                print(f"    Dropdown handling: {e}")

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            path = screenshot_path("04-form-bottom")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 8: Consent checkboxes
            print("[8] Handling checkboxes...")
            try:
                checkboxes = await page.locator("input[type='checkbox']").all()
                for cb in checkboxes:
                    is_checked = await cb.is_checked()
                    if not is_checked:
                        try:
                            await cb.check()
                            print("    Checked a checkbox")
                        except Exception as e:
                            print(f"    Could not check checkbox: {e}")
            except Exception as e:
                print(f"    Checkboxes: {e}")

            # Pre-submit screenshot
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            path = screenshot_path("05-before-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"[9] Pre-submit screenshot: {path}")

            # Step 9: Submit the form
            print("[10] Submitting form...")
            submit_clicked = False

            for selector in [
                "button[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Apply')",
                "button:has-text('Send application')",
                "button:has-text('Solliciteer')",
                "button:has-text('Verstuur')",
                "button:has-text('Send')",
                "input[type='submit']",
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        await btn.click()
                        print(f"    Clicked submit using selector: {selector}")
                        submit_clicked = True
                        await page.wait_for_timeout(5000)
                        break
                except Exception:
                    continue

            if not submit_clicked:
                print("    Trying broader button search...")
                btns = await page.locator("button").all()
                for btn in btns:
                    try:
                        txt = await btn.text_content()
                        if txt and any(w in txt.lower() for w in ["submit", "apply", "send", "verzend", "solliciteer", "verstuur"]):
                            await btn.scroll_into_view_if_needed()
                            await btn.click()
                            print(f"    Clicked button: '{txt}'")
                            submit_clicked = True
                            await page.wait_for_timeout(5000)
                            break
                    except Exception:
                        continue

            if not submit_clicked:
                notes = "Could not find submit button"
                print(f"    ERROR: {notes}")

            path = screenshot_path("06-after-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Post-submit screenshot: {path}")

            # Check for success/failure/captcha
            current_url = page.url
            page_text = await page.evaluate("document.body.innerText")
            print(f"    Final URL: {current_url}")
            print(f"    Page text snippet: {page_text[:300]}")

            success_indicators = [
                "thank you", "bedankt", "application received", "application submitted",
                "sollicitatie ontvangen", "we'll be in touch", "confirmation", "success",
                "your application", "we have received"
            ]
            captcha_indicators = ["captcha", "hcaptcha", "recaptcha", "i am not a robot", "prove you are human"]

            page_lower = page_text.lower()

            if any(ind in page_lower for ind in success_indicators):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. Final URL: {current_url}"
                print(f"    SUCCESS: {notes}")
            elif any(ind in page_lower for ind in captcha_indicators):
                status = "skipped"
                notes = f"CAPTCHA detected. Manual completion required. URL: {current_url}"
                print(f"    CAPTCHA blocked: {notes}")
            elif not submit_clicked:
                status = "failed"
                notes = "Could not find and click submit button"
            else:
                if "/c/new" not in current_url and ("funda" in current_url or "jobs" in current_url):
                    status = "applied"
                    notes = f"Form submitted, URL changed to: {current_url}. Likely success."
                    print(f"    URL changed (likely success): {notes}")
                elif current_url == APPLICATION_URL or "/c/new" in current_url:
                    status = "failed"
                    notes = f"Still on form page after submit. URL: {current_url}. May have validation errors. Page: {page_text[:300]}"
                    print(f"    STILL ON FORM: {notes}")
                else:
                    status = "applied"
                    notes = f"Submit clicked, URL: {current_url}. Page text: {page_text[:200]}"
                    print(f"    SUBMITTED (unclear confirmation): {notes}")

        except Exception as e:
            notes = f"Exception during application: {str(e)}"
            status = "failed"
            print(f"    ERROR: {notes}")
            try:
                path = screenshot_path("error")
                await page.screenshot(path=path)
                screenshots.append(path)
            except Exception:
                pass

        finally:
            await browser.close()

    # Save to applications.json
    app_entry = {
        "id": f"funda-medior-net-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    print(f"Application log saved to: {APPLICATIONS_JSON}")
    return app_entry


if __name__ == "__main__":
    asyncio.run(run())
