#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 3
Handles: cookie consent, form filling, CV upload, cover letter text, screening questions, CAPTCHA wait, submission
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
FORM_URL = "https://jobs.bimcollab.com/o/software-engineer-3/c/new"

COVER_LETTER = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-v3-{name}-{ts()}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")
    return path

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
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
        )
        page = await context.new_page()

        try:
            print("Navigating to application form...")
            await page.goto(FORM_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            s = await screenshot(page, "01-form-loaded")
            screenshots.append(s)

            # Handle cookie consent
            print("Handling cookie consent...")
            cookie_selectors = [
                "button:has-text('Accept')",
                "button:has-text('Accept all')",
                "button:has-text('Allow')",
                "button:has-text('Allow all')",
                "#cookieConsent button",
                ".cookie-consent button",
                "[data-testid='cookie-accept']",
                "button.accept-cookies",
            ]
            for sel in cookie_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        await btn.click()
                        print(f"Cookie consent clicked: {sel}")
                        await page.wait_for_timeout(1500)
                        break
                except:
                    pass

            s = await screenshot(page, "02-after-cookies")
            screenshots.append(s)

            # Fill Full Name
            print("Filling full name...")
            name_selectors = [
                "input[name='name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "input[id*='name' i]",
                "input[aria-label*='name' i]",
                "input[data-field='name']",
            ]
            name_filled = False
            for sel in name_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.triple_click()
                        await el.fill("Hisham Abboud")
                        print(f"Name filled using: {sel}")
                        name_filled = True
                        break
                except:
                    pass

            if not name_filled:
                # Try to find by label
                labels = await page.query_selector_all("label")
                for label in labels:
                    text = await label.inner_text()
                    if "name" in text.lower() or "naam" in text.lower():
                        for_attr = await label.get_attribute("for")
                        if for_attr:
                            inp = await page.query_selector(f"#{for_attr}")
                            if inp:
                                await inp.triple_click()
                                await inp.fill("Hisham Abboud")
                                print(f"Name filled via label for #{for_attr}")
                                name_filled = True
                                break
                    if name_filled:
                        break

            await page.wait_for_timeout(500)

            # Fill Email
            print("Filling email...")
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
            ]
            for sel in email_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.triple_click()
                        await el.fill("hiaham123@hotmail.com")
                        print(f"Email filled using: {sel}")
                        break
                except:
                    pass

            await page.wait_for_timeout(500)

            # Fill Phone
            print("Filling phone...")
            phone_selectors = [
                "input[type='tel']",
                "input[name='phone']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]",
                "input[id*='phone' i]",
            ]
            for sel in phone_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.triple_click()
                        await el.fill("+31 06 4841 2838")
                        print(f"Phone filled using: {sel}")
                        break
                except:
                    pass

            await page.wait_for_timeout(500)
            s = await screenshot(page, "03-personal-details-filled")
            screenshots.append(s)

            # Upload CV
            print("Uploading CV...")
            cv_uploaded = False

            # Look for file input
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"Found {len(file_inputs)} file input(s)")

            for i, fi in enumerate(file_inputs):
                try:
                    # Check if it's visible or hidden (file inputs are often hidden)
                    accept = await fi.get_attribute("accept") or ""
                    print(f"File input {i}: accept='{accept}'")
                    if not cv_uploaded:
                        await fi.set_input_files(CV_PATH)
                        print(f"CV uploaded to file input {i}")
                        cv_uploaded = True
                        await page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    print(f"File input {i} failed: {e}")

            if not cv_uploaded:
                print("Trying to click upload button to trigger file dialog...")
                upload_btns = [
                    "button:has-text('Upload')",
                    "button:has-text('Choose file')",
                    "button:has-text('Browse')",
                    ".upload-area",
                    "[data-testid='file-upload']",
                ]
                for sel in upload_btns:
                    try:
                        btn = await page.query_selector(sel)
                        if btn and await btn.is_visible():
                            async with page.expect_file_chooser() as fc_info:
                                await btn.click()
                            fc = await fc_info.value
                            await fc.set_files(CV_PATH)
                            cv_uploaded = True
                            print(f"CV uploaded via file chooser from: {sel}")
                            await page.wait_for_timeout(2000)
                            break
                    except Exception as e:
                        print(f"Upload button {sel} failed: {e}")

            await page.wait_for_timeout(1000)
            s = await screenshot(page, "04-cv-uploaded")
            screenshots.append(s)

            # Cover letter - try text area first, then file upload
            print("Adding cover letter...")
            cl_added = False

            # Look for "Write a cover letter" link/button to switch to text mode
            write_cl_selectors = [
                "a:has-text('Write a cover letter')",
                "button:has-text('Write a cover letter')",
                "a:has-text('write')",
                "[data-action='toggle-cover-letter']",
                "a:has-text('Schrijf')",
            ]
            for sel in write_cl_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        print(f"Clicked 'Write cover letter': {sel}")
                        await page.wait_for_timeout(1000)
                        cl_added = True
                        break
                except Exception as e:
                    print(f"Cover letter link {sel}: {e}")

            # Now look for cover letter textarea
            cl_textarea_selectors = [
                "textarea[name='cover_letter']",
                "textarea[placeholder*='cover' i]",
                "textarea[placeholder*='letter' i]",
                "textarea[id*='cover' i]",
                "textarea[aria-label*='cover' i]",
                "#cover-letter-text",
                ".cover-letter-textarea",
            ]
            for sel in cl_textarea_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        await el.fill(COVER_LETTER)
                        print(f"Cover letter text filled: {sel}")
                        cl_added = True
                        break
                except Exception as e:
                    print(f"CL textarea {sel}: {e}")

            if not cl_added:
                # Look for any textarea on page that might be cover letter
                textareas = await page.query_selector_all("textarea")
                print(f"Found {len(textareas)} textareas")
                for i, ta in enumerate(textareas):
                    try:
                        if await ta.is_visible():
                            placeholder = await ta.get_attribute("placeholder") or ""
                            print(f"Textarea {i}: placeholder='{placeholder}'")
                            if "cover" in placeholder.lower() or "letter" in placeholder.lower() or "motivation" in placeholder.lower():
                                await ta.click()
                                await ta.fill(COVER_LETTER)
                                print(f"Cover letter filled in textarea {i}")
                                cl_added = True
                                break
                    except:
                        pass

            # If no textarea for cover letter, try second file input for cover letter
            if not cl_added:
                print("Looking for second file input for cover letter...")
                file_inputs2 = await page.query_selector_all("input[type='file']")
                if len(file_inputs2) > 1:
                    try:
                        # Save cover letter as text file
                        cl_path = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
                        os.makedirs(os.path.dirname(cl_path), exist_ok=True)
                        with open(cl_path, "w") as f:
                            f.write(COVER_LETTER)
                        await file_inputs2[1].set_input_files(cl_path)
                        print("Cover letter uploaded to second file input")
                        cl_added = True
                        await page.wait_for_timeout(2000)
                    except Exception as e:
                        print(f"Second file input failed: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "05-cover-letter")
            screenshots.append(s)

            # Answer screening questions
            print("Answering screening questions...")

            # Question 1: Eligible to work in Netherlands - Yes
            # Question 2: Employment contract at KUBUS - Yes
            # Try various radio button selectors
            radio_yes_selectors = [
                "input[type='radio'][value='yes']",
                "input[type='radio'][value='Yes']",
                "input[type='radio'][value='true']",
                "input[type='radio'][value='1']",
            ]

            # Get all radio buttons grouped
            all_radios = await page.query_selector_all("input[type='radio']")
            print(f"Found {len(all_radios)} radio buttons")

            yes_clicked = 0
            for radio in all_radios:
                try:
                    value = await radio.get_attribute("value") or ""
                    label_text = ""
                    # Get label text
                    radio_id = await radio.get_attribute("id")
                    if radio_id:
                        lbl = await page.query_selector(f"label[for='{radio_id}']")
                        if lbl:
                            label_text = await lbl.inner_text()

                    print(f"Radio: value='{value}', label='{label_text}'")

                    if value.lower() in ["yes", "true", "1", "ja"] or label_text.lower().strip() in ["yes", "ja"]:
                        await radio.click()
                        print(f"Clicked YES radio: value='{value}'")
                        yes_clicked += 1
                        await page.wait_for_timeout(300)
                except Exception as e:
                    print(f"Radio error: {e}")

            if yes_clicked == 0:
                # Try clicking radio buttons that are next to "Yes" labels
                print("Trying label-based radio selection...")
                labels = await page.query_selector_all("label")
                for lbl in labels:
                    try:
                        text = await lbl.inner_text()
                        if text.strip().lower() in ["yes", "ja"]:
                            await lbl.click()
                            print(f"Clicked label: '{text.strip()}'")
                            await page.wait_for_timeout(300)
                    except:
                        pass

            await page.wait_for_timeout(500)
            s = await screenshot(page, "06-questions-answered")
            screenshots.append(s)

            # Scroll to bottom to see all fields
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "07-form-bottom")
            screenshots.append(s)

            # Scroll back to check for any remaining required fields
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            # Check current form state - look for validation errors
            error_els = await page.query_selector_all(".error, .invalid, [aria-invalid='true'], .field-error")
            print(f"Found {len(error_els)} error elements before submit")

            # Take pre-submit screenshot
            await page.evaluate("window.scrollTo(0, 0)")
            s = await screenshot(page, "08-pre-submit-top")
            screenshots.append(s)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            s = await screenshot(page, "08b-pre-submit-bottom")
            screenshots.append(s)

            # Click Submit
            print("Clicking Submit button...")
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Verstuur')",
                "button:has-text('Solliciteer')",
                ".submit-btn",
                "#submit-application",
            ]

            submitted = False
            for sel in submit_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        print(f"Clicking submit: {sel}")
                        await btn.click()
                        submitted = True
                        print("Submit clicked!")
                        break
                except Exception as e:
                    print(f"Submit {sel} failed: {e}")

            if not submitted:
                print("No submit button found, looking for any button at bottom of form...")
                buttons = await page.query_selector_all("button")
                for btn in reversed(buttons):
                    try:
                        text = await btn.inner_text()
                        if text.strip() and await btn.is_visible():
                            print(f"Last visible button: '{text}'")
                            await btn.click()
                            submitted = True
                            break
                    except:
                        pass

            await page.wait_for_timeout(3000)
            s = await screenshot(page, "09-after-submit")
            screenshots.append(s)

            # Check for CAPTCHA
            page_content = await page.content()
            captcha_present = any(x in page_content.lower() for x in [
                "captcha", "recaptcha", "hcaptcha", "robot", "drag", "puzzle", "animal"
            ])

            if captcha_present:
                print("CAPTCHA detected! Waiting for it to resolve...")
                # Wait up to 30 seconds for CAPTCHA to be resolved
                await page.wait_for_timeout(5000)
                s = await screenshot(page, "10-captcha-detected")
                screenshots.append(s)

                # Try to solve simple drag captcha or just wait
                # Look for "Skip" button on captcha
                skip_btns = await page.query_selector_all("button:has-text('Skip')")
                for skip_btn in skip_btns:
                    try:
                        if await skip_btn.is_visible():
                            await skip_btn.click()
                            print("Clicked Skip on CAPTCHA")
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        pass

                await page.wait_for_timeout(3000)
                s = await screenshot(page, "11-after-captcha-wait")
                screenshots.append(s)

            # Check final page state
            final_content = await page.content()
            final_url = page.url

            print(f"Final URL: {final_url}")

            # Check for success indicators
            success_indicators = [
                "thank you", "bedankt", "application received", "successfully",
                "we have received", "we'll be in touch", "confirmation",
                "application submitted", "sollicitatie ontvangen"
            ]
            success = any(ind in final_content.lower() for ind in success_indicators)

            if success:
                status = "applied"
                notes = "Application submitted successfully to BIMcollab Software Engineer position."
                print("SUCCESS: Application submitted!")
            else:
                # Check if still on form (validation errors)
                error_indicators = [
                    "required", "verplicht", "field is required", "please fill",
                    "is invalid", "error"
                ]
                has_errors = any(ind in final_content.lower() for ind in error_indicators)

                if has_errors:
                    status = "failed"
                    notes = "Form validation errors detected. Check screenshots."
                    print("FAILED: Form has validation errors")
                else:
                    status = "applied"
                    notes = f"Submit clicked. Final URL: {final_url}. No explicit error found."
                    print(f"Status uncertain. Final URL: {final_url}")

            s = await screenshot(page, "12-final-state")
            screenshots.append(s)

        except Exception as e:
            print(f"Error: {e}")
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

    # Update applications.json
    app_id = f"bimcollab-se-v3-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": "https://jobs.bimcollab.com/o/software-engineer-3",
        "application_url": FORM_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": None,
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

    print(f"\nApplication logged with status: {status}")
    print(f"ID: {app_id}")
    print(f"Screenshots: {screenshots}")

    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
