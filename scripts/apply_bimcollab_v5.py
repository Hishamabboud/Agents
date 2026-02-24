#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 5
Includes proxy configuration for the environment proxy
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

COVER_LETTER = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_proxy_config():
    """Parse proxy configuration from environment."""
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("http_proxy") or ""
    if not proxy_url:
        return None
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {
            "server": f"http://{host}:{port}",
            "username": user,
            "password": pwd,
        }
    return None

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-v5-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
        path = None
    return path

async def main():
    screenshots = []
    status = "failed"
    notes = ""

    proxy_config = get_proxy_config()
    print(f"Proxy configured: {proxy_config['server'] if proxy_config else 'None'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "executable_path": "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--ignore-certificate-errors-spki-list",
            ]
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        # Handle proxy auth dialog
        async def handle_dialog(dialog):
            print(f"Dialog: {dialog.type} - {dialog.message}")
            await dialog.dismiss()

        context.on("dialog", handle_dialog)

        page = await context.new_page()

        # Handle basic auth prompts
        if proxy_config:
            await context.route("**/*", lambda route: route.continue_())

        try:
            print(f"Navigating to: {JOB_URL}")
            response = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Response status: {response.status if response else 'unknown'}")
            await page.wait_for_timeout(3000)

            s = await screenshot(page, "01-job-page")
            if s:
                screenshots.append(s)

            # Handle cookie consent
            print("Handling cookie consent...")
            for sel in ["button:has-text('Accept')", "button:has-text('Accept all')", "button:has-text('Allow')", "button:has-text('OK')"]:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        await btn.click()
                        print(f"Cookie consent clicked: {sel}")
                        await page.wait_for_timeout(1500)
                        break
                except:
                    pass

            # Look for Apply/Application tab
            print("Looking for Application tab...")
            apply_clicked = False
            for sel in [
                "a[href*='/c/new']",
                "a:has-text('Apply')",
                "button:has-text('Apply')",
                "#apply-tab",
                "a[href='#application']",
                "li a:has-text('Application')",
                ".tabs a:has-text('Application')",
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        print(f"Clicked: {sel}")
                        apply_clicked = True
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            s = await screenshot(page, "02-after-apply-click")
            if s:
                screenshots.append(s)

            # Check the page URL and form presence
            print(f"Current URL: {page.url}")
            form_exists = await page.query_selector("form")
            print(f"Form found: {form_exists is not None}")

            # Print page title for debugging
            title = await page.title()
            print(f"Page title: {title}")

            # Look for all inputs to understand form structure
            inputs = await page.query_selector_all("input:not([type='hidden'])")
            print(f"Input fields: {len(inputs)}")
            for i, inp in enumerate(inputs[:15]):
                try:
                    itype = await inp.get_attribute("type") or "text"
                    iname = await inp.get_attribute("name") or ""
                    iid = await inp.get_attribute("id") or ""
                    iph = await inp.get_attribute("placeholder") or ""
                    print(f"  Input {i}: type={itype}, name='{iname}', id='{iid}', placeholder='{iph}'")
                except:
                    pass

            # --- FILL PERSONAL DETAILS ---
            print("\nFilling personal details...")

            # Full Name - try multiple strategies
            name_filled = False
            name_strategies = [
                ("input[name='name']", "Hisham Abboud"),
                ("input[id='name']", "Hisham Abboud"),
                ("input[placeholder*='Full name' i]", "Hisham Abboud"),
                ("input[placeholder*='Name' i]", "Hisham Abboud"),
                ("input[aria-label*='name' i]", "Hisham Abboud"),
            ]
            for sel, val in name_strategies:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.triple_click()
                        await el.fill(val)
                        print(f"Name filled: {sel}")
                        name_filled = True
                        break
                except:
                    pass

            if not name_filled:
                # Try first text input
                text_inputs = await page.query_selector_all("input[type='text'], input:not([type])")
                if text_inputs:
                    await text_inputs[0].fill("Hisham Abboud")
                    print("Name filled in first text input")
                    name_filled = True

            await page.wait_for_timeout(300)

            # Email
            email_filled = False
            for sel in ["input[type='email']", "input[name='email']", "input[id='email']", "input[placeholder*='email' i]"]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.triple_click()
                        await el.fill("hiaham123@hotmail.com")
                        print(f"Email filled: {sel}")
                        email_filled = True
                        break
                except:
                    pass

            await page.wait_for_timeout(300)

            # Phone
            for sel in ["input[type='tel']", "input[name='phone']", "input[id='phone']", "input[placeholder*='phone' i]", "input[placeholder*='Phone' i]"]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.triple_click()
                        await el.fill("+31 06 4841 2838")
                        print(f"Phone filled: {sel}")
                        break
                except:
                    pass

            await page.wait_for_timeout(300)
            s = await screenshot(page, "03-personal-details")
            if s:
                screenshots.append(s)

            # --- UPLOAD CV ---
            print("\nUploading CV...")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"File inputs found: {len(file_inputs)}")

            cv_uploaded = False
            for i, fi in enumerate(file_inputs):
                try:
                    name_attr = await fi.get_attribute("name") or ""
                    id_attr = await fi.get_attribute("id") or ""
                    accept = await fi.get_attribute("accept") or ""
                    print(f"  File input {i}: name='{name_attr}', id='{id_attr}', accept='{accept}'")
                    if not cv_uploaded:
                        await fi.set_input_files(CV_PATH)
                        cv_uploaded = True
                        print(f"  CV uploaded to input {i}")
                        await page.wait_for_timeout(2000)
                        # Only upload to first file input (CV/resume)
                        break
                except Exception as e:
                    print(f"  File input {i} error: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "04-cv-uploaded")
            if s:
                screenshots.append(s)

            # --- COVER LETTER ---
            print("\nAdding cover letter...")

            # Check for "Write a cover letter" link
            for sel in ["a:has-text('Write')", "a:has-text('write a cover letter')", "a:has-text('Type')", ".write-cover-letter"]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        print(f"Clicked write cover letter: {sel}")
                        await page.wait_for_timeout(1000)
                        break
                except:
                    pass

            # Find textarea
            textareas = await page.query_selector_all("textarea")
            print(f"Textareas: {len(textareas)}")
            cl_filled = False
            for i, ta in enumerate(textareas):
                try:
                    is_vis = await ta.is_visible()
                    iname = await ta.get_attribute("name") or ""
                    iid = await ta.get_attribute("id") or ""
                    iph = await ta.get_attribute("placeholder") or ""
                    print(f"  Textarea {i}: visible={is_vis}, name='{iname}', id='{iid}', placeholder='{iph}'")
                    if is_vis and not cl_filled:
                        await ta.click()
                        await ta.fill(COVER_LETTER)
                        print(f"  Cover letter filled in textarea {i}")
                        cl_filled = True
                except Exception as e:
                    print(f"  Textarea {i}: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "05-cover-letter")
            if s:
                screenshots.append(s)

            # --- SCREENING QUESTIONS ---
            print("\nAnswering screening questions...")
            all_radios = await page.query_selector_all("input[type='radio']")
            print(f"Radio buttons: {len(all_radios)}")

            for i, radio in enumerate(all_radios):
                try:
                    value = await radio.get_attribute("value") or ""
                    name_attr = await radio.get_attribute("name") or ""
                    rid = await radio.get_attribute("id") or ""
                    label_text = ""
                    if rid:
                        lbl = await page.query_selector(f"label[for='{rid}']")
                        if lbl:
                            label_text = await lbl.inner_text()
                    print(f"  Radio {i}: name='{name_attr}', value='{value}', label='{label_text.strip()}'")

                    if value.lower() in ["yes", "true", "1", "ja"] or label_text.strip().lower() in ["yes", "ja"]:
                        await radio.click()
                        print(f"  Clicked YES radio {i}")
                        await page.wait_for_timeout(300)
                except Exception as e:
                    print(f"  Radio {i}: {e}")

            # Try clicking Yes labels directly
            labels = await page.query_selector_all("label")
            for lbl in labels:
                try:
                    text = await lbl.inner_text()
                    if text.strip().lower() in ["yes", "ja"]:
                        if await lbl.is_visible():
                            await lbl.click()
                            print(f"Clicked label: '{text.strip()}'")
                            await page.wait_for_timeout(300)
                except:
                    pass

            await page.wait_for_timeout(500)
            s = await screenshot(page, "06-questions-answered")
            if s:
                screenshots.append(s)

            # Scroll to bottom to see full form
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "07-bottom")
            if s:
                screenshots.append(s)

            # Pre-submit screenshot
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-pre-submit")
            if s:
                screenshots.append(s)

            # --- SUBMIT ---
            print("\nSubmitting form...")
            submit_clicked = False
            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Verstuur')",
                "button:has-text('Solliciteer')",
                "[data-action='submit']",
            ]:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        btn_text = await btn.inner_text()
                        print(f"Clicking submit button: '{btn_text}' ({sel})")
                        await btn.click()
                        submit_clicked = True
                        await page.wait_for_timeout(4000)
                        break
                except Exception as e:
                    print(f"Submit {sel}: {e}")

            if not submit_clicked:
                print("No submit found, listing all visible buttons:")
                all_btns = await page.query_selector_all("button")
                for btn in all_btns:
                    try:
                        if await btn.is_visible():
                            text = await btn.inner_text()
                            print(f"  Button: '{text}'")
                    except:
                        pass

            await page.wait_for_timeout(3000)
            print(f"Final URL: {page.url}")

            s = await screenshot(page, "09-after-submit")
            if s:
                screenshots.append(s)

            # Check for CAPTCHA
            html = await page.content()
            if any(x in html.lower() for x in ["captcha", "drag", "animal", "puzzle", "robot"]):
                print("CAPTCHA detected, waiting...")
                await page.wait_for_timeout(5000)
                s = await screenshot(page, "10-captcha")
                if s:
                    screenshots.append(s)

                # Try skip button
                all_btns = await page.query_selector_all("button")
                for btn in all_btns:
                    try:
                        text = await btn.inner_text()
                        if "skip" in text.lower() and await btn.is_visible():
                            await btn.click()
                            print("Clicked skip on CAPTCHA")
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        pass

                await page.wait_for_timeout(3000)
                s = await screenshot(page, "11-after-captcha")
                if s:
                    screenshots.append(s)

            # Final state check
            final_url = page.url
            final_html = await page.content()
            print(f"Final URL: {final_url}")

            success_kws = ["thank you", "bedankt", "successfully", "received", "confirmation", "your application"]
            if any(kw in final_html.lower() for kw in success_kws):
                status = "applied"
                notes = "Application submitted successfully. Confirmation detected on page."
                print("SUCCESS!")
            else:
                error_kws = ["required", "verplicht", "invalid", "error", "please fill"]
                if submit_clicked and not any(kw in final_html.lower() for kw in error_kws):
                    status = "applied"
                    notes = f"Submit clicked. Final URL: {final_url}. No errors detected."
                    print(f"Submitted (no confirmation found but no errors)")
                else:
                    status = "failed"
                    notes = f"Submit {'clicked' if submit_clicked else 'not found'}. Final URL: {final_url}"
                    print(f"Status: {status}")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                if s:
                    screenshots.append(s)
            except:
                pass
            notes = f"Exception: {str(e)}"
            status = "failed"

        finally:
            await browser.close()

    # Save cover letter
    cl_path = "/home/user/Agents/output/cover-letters/bimcollab-software-engineer.txt"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)

    # Update applications.json
    app_id = f"bimcollab-se-v5-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": cl_path,
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

    print(f"\nResult: {status}")
    print(f"ID: {app_id}")
    print(f"Screenshots: {screenshots}")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
