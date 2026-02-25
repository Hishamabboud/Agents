#!/usr/bin/env python3
"""
OWOW Backend Developer Application via Breezy HR
Company: OWOW, Eindhoven
Role: Backend Developer
URL: https://owow.breezy.hr/p/c661f142975701-backend-developer/apply
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
JOB_URL = "https://owow.breezy.hr/p/c661f142975701-backend-developer"
APPLY_URL = "https://owow.breezy.hr/p/c661f142975701-backend-developer/apply"

COVER_LETTER = """Dear OWOW Hiring Team,

I am excited to apply for the Backend Developer position at OWOW in Eindhoven. OWOW's reputation for building innovative digital products and its creative, purpose-driven studio model make it an environment where I would thrive and contribute meaningfully.

In my current role as Software Service Engineer at Actemium (VINCI Energies), I build and maintain backend systems using .NET, C#, Python/Flask, and JavaScript, developing REST API integrations and database optimizations for industrial clients. Prior to this, I completed an internship at ASML as a Python Developer, where I built high-performance test suites using Locust and Pytest in an agile Azure/Kubernetes environment.

My background in Node.js, REST APIs, PostgreSQL, and cloud infrastructure aligns well with your tech stack. I hold a BSc in Software Engineering from Fontys University of Applied Sciences in Eindhoven and am based locally, making me available for hybrid collaboration at your studio.

I am eager to bring my backend expertise and problem-solving mindset to OWOW's product team.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
linkedin.com/in/hisham-abboud"""


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


async def take_screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/owow-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None


async def main():
    screenshots = []
    status = "failed"
    notes = ""

    # Save cover letter
    cl_path = "/home/user/Agents/output/cover-letters/owow-backend-developer.txt"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)
    print(f"Cover letter saved: {cl_path}")

    proxy_config = get_proxy_config()
    print(f"Proxy: {proxy_config['server'] if proxy_config else 'None'}")

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
        page = await context.new_page()

        try:
            # Step 1: Navigate directly to the apply page
            print(f"Loading: {APPLY_URL}")
            await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            s = await take_screenshot(page, "01-apply-page-loaded")
            if s:
                screenshots.append(s)

            current_url = page.url
            print(f"Current URL: {current_url}")

            # Check page content
            html = await page.content()
            print(f"Page title: {await page.title()}")

            # Step 2: Handle any cookie banners
            for sel in [
                "button:has-text('Accept')",
                "button:has-text('OK')",
                "button:has-text('Agree')",
                "button:has-text('Accept all')",
                "#accept-cookies",
                ".cookie-accept",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1500):
                        await btn.click()
                        print(f"Cookie banner dismissed: {sel}")
                        await page.wait_for_timeout(1000)
                        break
                except:
                    pass

            # Step 3: Inspect the form structure
            print("\nInspecting form fields...")
            inputs = await page.query_selector_all("input, textarea, select")
            for i, inp in enumerate(inputs):
                try:
                    inp_type = await inp.get_attribute("type") or "text"
                    inp_name = await inp.get_attribute("name") or ""
                    inp_id = await inp.get_attribute("id") or ""
                    inp_placeholder = await inp.get_attribute("placeholder") or ""
                    inp_vis = await inp.is_visible()
                    print(f"  [{i}] type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}, visible={inp_vis}")
                except:
                    pass

            # Step 4: Fill in the form fields
            print("\nFilling form fields...")

            # Method 1: Try Playwright locators first
            # Name field
            name_filled = False
            for sel in [
                "input[name='name']",
                "input[name='candidate.name']",
                "input[name='full_name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "#name",
                "#full_name",
                "#candidate_name",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        await loc.fill("Hisham Abboud")
                        print(f"Name filled via: {sel}")
                        name_filled = True
                        break
                except:
                    pass

            if not name_filled:
                # Try JS approach
                result = await page.evaluate("""
                    () => {
                        const selectors = [
                            "input[name='name']",
                            "input[name='candidate.name']",
                            "input[name='full_name']",
                            "input[placeholder*='name']",
                            "input[placeholder*='Name']",
                        ];
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el) {
                                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                setter.call(el, 'Hisham Abboud');
                                el.dispatchEvent(new Event('input', {bubbles: true}));
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                                return 'filled: ' + sel;
                            }
                        }
                        // fallback: first text input
                        const inputs = document.querySelectorAll("input[type='text'], input:not([type])");
                        if (inputs.length > 0) {
                            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            setter.call(inputs[0], 'Hisham Abboud');
                            inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                            inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
                            return 'filled first text input';
                        }
                        return 'not found';
                    }
                """)
                print(f"Name (JS): {result}")

            await page.wait_for_timeout(300)

            # Email field
            email_filled = False
            for sel in [
                "input[name='email']",
                "input[name='candidate.email']",
                "input[type='email']",
                "input[placeholder*='email' i]",
                "#email",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        await loc.fill("hiaham123@hotmail.com")
                        print(f"Email filled via: {sel}")
                        email_filled = True
                        break
                except:
                    pass

            if not email_filled:
                result = await page.evaluate("""
                    () => {
                        const el = document.querySelector("input[type='email'], input[name='email'], input[name='candidate.email']");
                        if (el) {
                            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            setter.call(el, 'hiaham123@hotmail.com');
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            return 'filled';
                        }
                        return 'not found';
                    }
                """)
                print(f"Email (JS): {result}")

            await page.wait_for_timeout(300)

            # Phone field
            phone_filled = False
            for sel in [
                "input[name='phone']",
                "input[name='candidate.phone']",
                "input[type='tel']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]",
                "#phone",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        await loc.fill("+31648412838")
                        print(f"Phone filled via: {sel}")
                        phone_filled = True
                        break
                except:
                    pass

            if not phone_filled:
                result = await page.evaluate("""
                    () => {
                        const el = document.querySelector("input[type='tel'], input[name='phone'], input[name='candidate.phone']");
                        if (el) {
                            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            setter.call(el, '+31648412838');
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            return 'filled';
                        }
                        return 'not found';
                    }
                """)
                print(f"Phone (JS): {result}")

            await page.wait_for_timeout(300)

            # LinkedIn URL field
            for sel in [
                "input[name='linkedin']",
                "input[name='candidate.linkedin']",
                "input[placeholder*='linkedin' i]",
                "input[name*='linkedin' i]",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2000):
                        await loc.fill("linkedin.com/in/hisham-abboud")
                        print(f"LinkedIn filled via: {sel}")
                        break
                except:
                    pass

            await page.wait_for_timeout(300)

            s = await take_screenshot(page, "02-form-fields-filled")
            if s:
                screenshots.append(s)

            # Step 5: Upload CV
            print("\nUploading CV...")
            cv_uploaded = False

            # Breezy HR typically uses input[name='resume'] or input[name='candidate.cv']
            for sel in [
                "input[name='resume']",
                "input[name='candidate.cv']",
                "input[name='cv']",
                "input[accept*='pdf']",
                "input[type='file']",
            ]:
                try:
                    file_input = page.locator(sel).first
                    await file_input.set_input_files(CV_PATH, timeout=10000)
                    print(f"CV uploaded via: {sel}")
                    cv_uploaded = True
                    await page.wait_for_timeout(3000)
                    break
                except Exception as e:
                    print(f"CV upload attempt ({sel}) failed: {e}")

            if not cv_uploaded:
                print("Warning: CV upload failed")

            s = await take_screenshot(page, "03-cv-uploaded")
            if s:
                screenshots.append(s)

            # Step 6: Fill cover letter if there's a textarea
            print("\nChecking for cover letter / motivation field...")
            textareas = await page.query_selector_all("textarea")
            print(f"Found {len(textareas)} textarea(s)")

            cl_filled = False
            for i, ta in enumerate(textareas):
                try:
                    ta_vis = await ta.is_visible()
                    ta_name = await ta.get_attribute("name") or ""
                    ta_id = await ta.get_attribute("id") or ""
                    ta_placeholder = await ta.get_attribute("placeholder") or ""
                    print(f"  Textarea {i}: visible={ta_vis}, name={ta_name}, id={ta_id}, placeholder={ta_placeholder}")
                    if ta_vis:
                        await ta.fill(COVER_LETTER)
                        print(f"  Cover letter filled in textarea {i}")
                        cl_filled = True
                        await page.wait_for_timeout(500)
                        # Only fill first visible textarea unless name suggests cover letter
                        if "cover" not in ta_name.lower() and "motivation" not in ta_name.lower():
                            break
                except Exception as e:
                    print(f"  Textarea {i} error: {e}")

            if not cl_filled:
                # Check for "Write a cover letter" link in Breezy
                for sel in [
                    "a:has-text('Write a cover letter')",
                    "button:has-text('Write a cover letter')",
                    "a:has-text('cover letter')",
                    "a:has-text('motivation')",
                ]:
                    try:
                        link = page.locator(sel).first
                        if await link.is_visible(timeout=2000):
                            await link.click()
                            print(f"Clicked: {sel}")
                            await page.wait_for_timeout(1500)
                            # Now look for textarea again
                            ta = page.locator("textarea").first
                            if await ta.is_visible(timeout=3000):
                                await ta.fill(COVER_LETTER)
                                cl_filled = True
                                print("Cover letter filled after clicking link")
                            break
                    except:
                        pass

            await page.wait_for_timeout(500)
            s = await take_screenshot(page, "04-cover-letter")
            if s:
                screenshots.append(s)

            # Step 7: Answer any screening/custom questions
            print("\nAnswering screening questions...")

            # Look for radio buttons (Yes/No questions)
            radios = await page.query_selector_all("input[type='radio']")
            print(f"Found {len(radios)} radio button(s)")
            for radio in radios:
                try:
                    radio_val = await radio.get_attribute("value") or ""
                    radio_name = await radio.get_attribute("name") or ""
                    radio_vis = await radio.is_visible()
                    print(f"  Radio: name={radio_name}, value={radio_val}, visible={radio_vis}")
                    # Click "Yes" or "true" radios
                    if radio_val.lower() in ["yes", "true", "1", "ja"] and radio_vis:
                        await radio.check(force=True)
                        print(f"  Checked radio: {radio_name}={radio_val}")
                        await page.wait_for_timeout(200)
                except Exception as e:
                    print(f"  Radio error: {e}")

            # Look for select dropdowns
            selects = await page.query_selector_all("select")
            print(f"Found {len(selects)} select(s)")
            for sel_el in selects:
                try:
                    sel_name = await sel_el.get_attribute("name") or ""
                    sel_vis = await sel_el.is_visible()
                    options = await sel_el.query_selector_all("option")
                    opt_texts = []
                    for opt in options:
                        opt_val = await opt.get_attribute("value") or ""
                        opt_text = await opt.inner_text()
                        opt_texts.append(f"{opt_val}:{opt_text}")
                    print(f"  Select: name={sel_name}, visible={sel_vis}, options={opt_texts[:5]}")
                except Exception as e:
                    print(f"  Select error: {e}")

            await page.wait_for_timeout(500)
            s = await take_screenshot(page, "05-questions-answered")
            if s:
                screenshots.append(s)

            # Step 8: Scroll to bottom to see all elements
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await take_screenshot(page, "06-form-bottom")
            if s:
                screenshots.append(s)

            # Step 9: Pre-submit screenshot
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await take_screenshot(page, "07-pre-submit")
            if s:
                screenshots.append(s)

            # Step 10: Submit the form
            print("\nSubmitting application...")
            submit_clicked = False

            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Send')",
                "button:has-text('Apply now')",
                "button:has-text('Submit application')",
                ".btn-submit",
                ".apply-btn",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        btn_text = await btn.inner_text()
                        print(f"Submit button found: '{btn_text}' via {sel}")
                        await btn.click()
                        submit_clicked = True
                        print("Submit clicked!")
                        await page.wait_for_timeout(5000)
                        break
                except Exception as e:
                    pass

            if not submit_clicked:
                # JS fallback
                result = await page.evaluate("""
                    () => {
                        const candidates = [
                            document.querySelector("button[type='submit']"),
                            document.querySelector("input[type='submit']"),
                            ...Array.from(document.querySelectorAll('button')).filter(b =>
                                ['submit', 'apply', 'send', 'apply now'].includes(b.textContent.toLowerCase().trim())
                            ),
                        ].filter(Boolean);
                        if (candidates.length > 0) {
                            candidates[0].click();
                            return candidates[0].textContent || 'clicked';
                        }
                        return 'not found';
                    }
                """)
                print(f"JS submit: {result}")
                if result and result != 'not found':
                    submit_clicked = True
                    await page.wait_for_timeout(5000)

            s = await take_screenshot(page, "08-after-submit")
            if s:
                screenshots.append(s)

            # Step 11: Check for CAPTCHA
            html_after = await page.content()
            if any(x in html_after.lower() for x in ["hcaptcha", "recaptcha", "captcha", "robot"]):
                print("CAPTCHA detected!")
                await page.wait_for_timeout(3000)
                s = await take_screenshot(page, "09-captcha-detected")
                if s:
                    screenshots.append(s)
                status = "skipped"
                notes = "Form filled successfully but CAPTCHA blocked automated submission. Manual completion required."
                print("Marking as skipped due to CAPTCHA.")
                await browser.close()

                # Save to applications.json
                _save_application(status, notes, screenshots, cl_path)
                return False

            # Step 12: Check for success
            final_url = page.url
            final_html = await page.content()
            print(f"\nFinal URL: {final_url}")

            success_keywords = [
                "thank you", "bedankt", "successfully", "received your application",
                "confirmation", "your application has been", "we'll be in touch",
                "application submitted", "bedankt voor je sollicitatie",
            ]
            error_keywords = [
                "required field", "is required", "verplicht", "error",
                "invalid", "please fill", "please enter",
            ]

            html_lower = final_html.lower()
            if any(kw in html_lower for kw in success_keywords):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected at {final_url}."
                print("SUCCESS! Application submitted.")
            elif any(kw in html_lower for kw in error_keywords):
                status = "failed"
                notes = f"Form validation errors detected. Final URL: {final_url}."
                print("FAILED: Validation errors.")
            elif submit_clicked:
                status = "applied"
                notes = f"Submit button clicked. No explicit error detected. Final URL: {final_url}."
                print("Status: applied (submit clicked, no errors detected)")
            else:
                status = "failed"
                notes = "Could not click submit button."
                print("FAILED: Submit not clicked.")

            s = await take_screenshot(page, "10-final-state")
            if s:
                screenshots.append(s)

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await take_screenshot(page, "error")
                if s:
                    screenshots.append(s)
            except:
                pass
            notes = f"Exception: {str(e)}"
            status = "failed"
        finally:
            await browser.close()

    _save_application(status, notes, screenshots, cl_path)
    return status == "applied"


def _save_application(status, notes, screenshots, cl_path):
    app_id = f"owow-backend-developer-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "OWOW",
        "role": "Backend Developer",
        "url": JOB_URL,
        "application_url": APPLY_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.0,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": cl_path,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": "hiaham123@hotmail.com",
    }

    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except:
        apps = []
    apps.append(new_entry)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\nApplication logged: {app_id} | Status: {status}")
    print(f"Applications file: {APPLICATIONS_JSON}")


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
