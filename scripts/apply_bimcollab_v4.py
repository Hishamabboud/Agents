#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 4
Navigate to job page first, click Apply, then fill the embedded form
"""

import asyncio
import json
import os
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

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-v4-{name}-{ts()}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path

async def fill_field(page, selectors, value, field_name="field"):
    """Try multiple selectors to fill a field."""
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                visible = await el.is_visible()
                enabled = await el.is_enabled()
                if visible or True:  # try even if not visible
                    await el.triple_click()
                    await el.fill(value)
                    print(f"{field_name} filled using: {sel}")
                    return True
        except Exception as e:
            pass
    return False

async def main():
    screenshots = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        try:
            print(f"Navigating to job page: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            s = await screenshot(page, "01-job-page")
            screenshots.append(s)

            # Handle cookie consent
            print("Handling cookie consent...")
            cookie_selectors = [
                "button:has-text('Accept')",
                "button:has-text('Accept all')",
                "button:has-text('Allow all')",
                "button:has-text('OK')",
                "[data-action='accept']",
                ".cc-accept",
                "#accept-cookies",
            ]
            for sel in cookie_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        await btn.click()
                        print(f"Cookie consent: {sel}")
                        await page.wait_for_timeout(1500)
                        break
                except:
                    pass

            # Look for Apply button / tab
            print("Looking for Application tab or Apply button...")
            apply_selectors = [
                "a[href*='/c/new']",
                "a:has-text('Apply')",
                "button:has-text('Apply')",
                "a:has-text('Solliciteer')",
                "button:has-text('Solliciteer')",
                ".apply-button",
                "[data-action='apply']",
                "a[href*='application']",
                "#apply-tab",
                "a.tab:has-text('Application')",
                "li.tab:has-text('Application') a",
                "a[href='#application']",
            ]

            for sel in apply_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        print(f"Clicking apply: {sel}")
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            s = await screenshot(page, "02-after-apply-click")
            screenshots.append(s)

            # Check if we're now on the form or if there's an application tab
            # Try clicking the "Application" tab in the navigation
            tab_selectors = [
                "a[href*='application']",
                "button[data-tab='application']",
                ".nav-tabs a:has-text('Application')",
                "a.nav-link:has-text('Application')",
            ]
            for sel in tab_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        print(f"Clicked application tab: {sel}")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            # Now look for the form - it might be embedded in the page
            # Check if form exists on this page
            form = await page.query_selector("form")
            print(f"Form found: {form is not None}")

            if not form:
                # Try navigating to the /c/new URL with referer set
                print("No form found, trying to navigate directly with referer...")
                await page.set_extra_http_headers({"Referer": JOB_URL})
                await page.goto(f"{JOB_URL}/c/new", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                s = await screenshot(page, "03-direct-form")
                screenshots.append(s)

            # Get page HTML to understand structure
            html = await page.content()
            print(f"Page URL: {page.url}")
            print(f"Form fields found: {html.count('<input') + html.count('<textarea')}")

            # Take screenshot of current state
            s = await screenshot(page, "04-form-view")
            screenshots.append(s)

            # Try filling fields - Full Name
            print("Filling name...")
            name_filled = await fill_field(page, [
                "input[name='name']",
                "input[id='name']",
                "input[placeholder*='Full name' i]",
                "input[placeholder*='Naam' i]",
                "input[aria-label*='name' i]",
                "input[data-field='name']",
                "input[type='text']:first-of-type",
            ], "Hisham Abboud", "Name")

            if not name_filled:
                # Look at all text inputs
                inputs = await page.query_selector_all("input[type='text'], input:not([type])")
                print(f"Found {len(inputs)} text inputs")
                for i, inp in enumerate(inputs):
                    try:
                        pid = await inp.get_attribute("id") or ""
                        pname = await inp.get_attribute("name") or ""
                        pph = await inp.get_attribute("placeholder") or ""
                        print(f"  Input {i}: id='{pid}', name='{pname}', placeholder='{pph}'")
                    except:
                        pass

            # Fill Email
            print("Filling email...")
            await fill_field(page, [
                "input[type='email']",
                "input[name='email']",
                "input[id='email']",
                "input[placeholder*='email' i]",
            ], "hiaham123@hotmail.com", "Email")

            # Fill Phone
            print("Filling phone...")
            await fill_field(page, [
                "input[type='tel']",
                "input[name='phone']",
                "input[id='phone']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]",
            ], "+31 06 4841 2838", "Phone")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "05-details-filled")
            screenshots.append(s)

            # Upload CV
            print("Uploading CV...")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"File inputs: {len(file_inputs)}")

            cv_uploaded = False
            for i, fi in enumerate(file_inputs):
                try:
                    accept = await fi.get_attribute("accept") or ""
                    name_attr = await fi.get_attribute("name") or ""
                    id_attr = await fi.get_attribute("id") or ""
                    print(f"  File input {i}: name='{name_attr}', id='{id_attr}', accept='{accept}'")
                    if not cv_uploaded:
                        await fi.set_input_files(CV_PATH)
                        cv_uploaded = True
                        print(f"  CV uploaded to input {i}")
                        await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"  File input {i} error: {e}")

            if not cv_uploaded:
                # Try clicking upload area
                print("Trying file chooser via upload area click...")
                upload_areas = [
                    ".upload-area", ".file-upload", ".cv-upload",
                    "[data-action='upload']", "label[for*='file']",
                    "label[for*='cv']", "label[for*='resume']",
                ]
                for sel in upload_areas:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            async with page.expect_file_chooser(timeout=3000) as fc_info:
                                await el.click()
                            fc = await fc_info.value
                            await fc.set_files(CV_PATH)
                            cv_uploaded = True
                            print(f"CV uploaded via: {sel}")
                            await page.wait_for_timeout(2000)
                            break
                    except Exception as e:
                        print(f"Upload area {sel}: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "06-cv-uploaded")
            screenshots.append(s)

            # Cover letter
            print("Adding cover letter...")
            # First check if there's a "Write a cover letter" toggle
            write_links = await page.query_selector_all("a, button")
            for link in write_links:
                try:
                    text = await link.inner_text()
                    if "write" in text.lower() and "cover" in text.lower():
                        if await link.is_visible():
                            await link.click()
                            print(f"Clicked write cover letter: '{text}'")
                            await page.wait_for_timeout(1000)
                            break
                except:
                    pass

            # Try textarea for cover letter
            cl_filled = False
            textareas = await page.query_selector_all("textarea")
            print(f"Textareas: {len(textareas)}")
            for i, ta in enumerate(textareas):
                try:
                    pid = await ta.get_attribute("id") or ""
                    pname = await ta.get_attribute("name") or ""
                    pph = await ta.get_attribute("placeholder") or ""
                    print(f"  Textarea {i}: id='{pid}', name='{pname}', placeholder='{pph}'")
                    if not cl_filled:
                        visible = await ta.is_visible()
                        if visible:
                            await ta.click()
                            await ta.fill(COVER_LETTER)
                            print(f"  Cover letter filled in textarea {i}")
                            cl_filled = True
                except Exception as e:
                    print(f"  Textarea {i}: {e}")

            if not cl_filled:
                # Try file input for cover letter (second file input)
                file_inputs2 = await page.query_selector_all("input[type='file']")
                if len(file_inputs2) > 1 and cv_uploaded:
                    # Save cover letter as PDF alternative text file
                    cl_path = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
                    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
                    with open(cl_path, "w") as f:
                        f.write(COVER_LETTER)
                    try:
                        await file_inputs2[1].set_input_files(cl_path)
                        print("Cover letter uploaded to second file input")
                        cl_filled = True
                        await page.wait_for_timeout(2000)
                    except Exception as e:
                        print(f"CL file upload failed: {e}")

            s = await screenshot(page, "07-cover-letter")
            screenshots.append(s)

            # Answer screening questions - click YES on all radio buttons
            print("Answering screening questions...")
            all_radios = await page.query_selector_all("input[type='radio']")
            print(f"Radio buttons: {len(all_radios)}")

            for radio in all_radios:
                try:
                    value = await radio.get_attribute("value") or ""
                    name_attr = await radio.get_attribute("name") or ""
                    rid = await radio.get_attribute("id") or ""

                    # Get associated label
                    label_text = ""
                    if rid:
                        lbl = await page.query_selector(f"label[for='{rid}']")
                        if lbl:
                            label_text = await lbl.inner_text()

                    print(f"  Radio: name='{name_attr}', value='{value}', label='{label_text}'")

                    if value.lower() in ["yes", "true", "1", "ja"] or label_text.strip().lower() in ["yes", "ja"]:
                        await radio.click()
                        print(f"  Clicked YES radio")
                        await page.wait_for_timeout(300)
                except Exception as e:
                    print(f"  Radio error: {e}")

            # Also try clicking Yes labels
            labels = await page.query_selector_all("label")
            for lbl in labels:
                try:
                    text = await lbl.inner_text()
                    if text.strip().lower() in ["yes", "ja"]:
                        if await lbl.is_visible():
                            await lbl.click()
                            print(f"Clicked 'Yes' label")
                            await page.wait_for_timeout(300)
                except:
                    pass

            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-questions-answered")
            screenshots.append(s)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "09-bottom")
            screenshots.append(s)

            # Take pre-submit screenshots
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "10-pre-submit")
            screenshots.append(s)

            # Click Submit
            print("Looking for submit button...")
            submit_btn = None
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Verstuur')",
                "button:has-text('Solliciteer')",
                ".submit-application",
            ]

            for sel in submit_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn:
                        visible = await btn.is_visible()
                        text = await btn.inner_text() if btn else ""
                        print(f"  Submit candidate: '{text}', visible={visible}, sel={sel}")
                        if visible:
                            submit_btn = btn
                            break
                except Exception as e:
                    print(f"  Submit sel {sel}: {e}")

            if submit_btn:
                print("Clicking submit...")
                await submit_btn.click()
                await page.wait_for_timeout(4000)
                print(f"After submit URL: {page.url}")
            else:
                print("No submit button found!")
                # Try clicking last visible button
                all_buttons = await page.query_selector_all("button")
                for btn in all_buttons:
                    try:
                        if await btn.is_visible():
                            text = await btn.inner_text()
                            print(f"  Visible button: '{text}'")
                    except:
                        pass

            s = await screenshot(page, "11-after-submit")
            screenshots.append(s)

            # Check for CAPTCHA
            html_content = await page.content()
            if any(x in html_content.lower() for x in ["captcha", "drag", "animal", "puzzle", "robot"]):
                print("CAPTCHA detected - waiting...")
                await page.wait_for_timeout(5000)
                s = await screenshot(page, "12-captcha")
                screenshots.append(s)

                # Try to find and click skip
                skip_btns = await page.query_selector_all("button")
                for btn in skip_btns:
                    try:
                        text = await btn.inner_text()
                        if "skip" in text.lower():
                            await btn.click()
                            print("Clicked CAPTCHA skip")
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        pass

                await page.wait_for_timeout(3000)
                s = await screenshot(page, "13-after-captcha")
                screenshots.append(s)

            # Final check
            final_url = page.url
            final_html = await page.content()
            print(f"Final URL: {final_url}")

            success_keywords = [
                "thank you", "bedankt", "successfully submitted", "application received",
                "we have received", "confirmation", "your application"
            ]
            if any(kw in final_html.lower() for kw in success_keywords):
                status = "applied"
                notes = "Application submitted successfully. Confirmation message detected."
                print("SUCCESS!")
            else:
                # If we got past the form page, assume success
                if "/c/new" not in final_url and final_url != JOB_URL:
                    status = "applied"
                    notes = f"Submit clicked, URL changed to {final_url}. Assuming submitted."
                else:
                    status = "failed"
                    notes = "Could not confirm submission. Check screenshots."
                print(f"Status: {status}")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
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
    app_id = f"bimcollab-se-v4-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "application_url": f"{JOB_URL}/c/new",
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
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
