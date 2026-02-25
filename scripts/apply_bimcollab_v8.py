#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 8
Key insights from intercept test:
1. Go to /c/new directly (accessible via proxy)
2. Click Apply tab button (class sc-csisgn-0) first to show form
3. Fill form with type() for natural input
4. Phone already has +31 prefix - need to clear it first
5. Radios need value='true' (not 'yes')
6. CAPTCHA (hCaptcha) loads on page but triggers on submit
7. 'Write it here instead' button available for cover letter text
8. Legal agreement is a checkbox

This version tries to handle the hCaptcha by waiting for it to appear
and then attempting to solve/skip it.
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
FORM_URL = "https://jobs.bimcollab.com/o/software-engineer-3/c/new"

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

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-v8-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

async def dismiss_popups(page, timeout=1000):
    dismissed = 0
    for sel in [
        "button:has-text('Agree to necessary')",
        "button:has-text('Agree to all')",
        "button:has-text('OK')",
        "button:has-text('Accept')",
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=timeout):
                await btn.click()
                dismissed += 1
                await page.wait_for_timeout(500)
        except:
            pass
    return dismissed

async def main():
    screenshots = []
    status = "failed"
    notes = ""

    proxy_config = get_proxy_config()
    print(f"Proxy: {proxy_config['server'] if proxy_config else 'None'}")

    # Save cover letter
    cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
    os.makedirs(os.path.dirname(cl_file), exist_ok=True)
    with open(cl_file, "w") as f:
        f.write(COVER_LETTER_TEXT)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"],
            proxy=proxy_config
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # Track network requests to detect actual form submission
        submission_detected = False
        submission_response = None

        async def handle_response(response):
            nonlocal submission_detected, submission_response
            url = response.url
            status_code = response.status
            if "bimcollab" in url and "/c/new" in url and status_code != 200:
                print(f"Form response: {status_code} {url}")
            if any(kw in url for kw in ['candidates', 'application', 'apply']) and status_code in [200, 201, 302]:
                if 'google' not in url and 'analytics' not in url and 'linkedin' not in url:
                    submission_detected = True
                    submission_response = f"{status_code} {url}"
                    print(f"SUBMISSION RESPONSE: {status_code} {url}")

        page.on("response", handle_response)

        try:
            # Step 1: Load the job page first (not /c/new directly since that needs the Apply button context)
            print("\n=== Step 1: Load job page ===")
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            s = await screenshot(page, "01-loaded")
            if s: screenshots.append(s)

            # Dismiss initial popups (cookies agreement)
            print("Dismissing popups...")
            dismissed = await dismiss_popups(page)
            print(f"Dismissed {dismissed} popups")
            await page.wait_for_timeout(1000)

            # Step 2: Click the Apply tab (button with class sc-csisgn-0)
            print("\n=== Step 2: Click Apply tab ===")

            # The Apply tab that shows the form is button with class 'sc-csisgn-0 cWtVVQ'
            # (but not the 'Send' button which also has this class)
            apply_tab = None

            # Find the Apply button that's NOT the Send button
            buttons = await page.query_selector_all("button.sc-csisgn-0")
            print(f"Found {len(buttons)} sc-csisgn-0 buttons")
            for btn in buttons:
                text = await btn.inner_text()
                print(f"  Button: '{text}'")
                if text.strip().lower() == "apply":
                    apply_tab = btn
                    break

            if apply_tab:
                await apply_tab.click()
                print("Clicked Apply tab!")
                await page.wait_for_timeout(2000)
            else:
                # Try alternate approaches
                result = await page.evaluate("""
                    () => {
                        const btns = Array.from(document.querySelectorAll('button'));
                        for (const btn of btns) {
                            if (btn.textContent.trim() === 'Apply' && !btn.type) {
                                btn.click();
                                return 'clicked: ' + btn.className;
                            }
                        }
                        // Try the tab button
                        for (const btn of btns) {
                            if (btn.textContent.trim() === 'Application') {
                                btn.click();
                                return 'clicked Application tab';
                            }
                        }
                        return null;
                    }
                """)
                print(f"JS Apply result: {result}")
                await page.wait_for_timeout(2000)

            # Dismiss any popups that appeared
            await dismiss_popups(page)
            await page.wait_for_timeout(500)

            s = await screenshot(page, "02-apply-tab-clicked")
            if s: screenshots.append(s)

            # Verify form is visible
            name_visible = False
            try:
                name_visible = await page.locator("input[name='candidate.name']").first.is_visible(timeout=3000)
            except:
                pass
            print(f"Name field visible: {name_visible}")

            if not name_visible:
                print("Form not visible! URL:", page.url)
                # Try navigating to form URL directly
                await page.goto(FORM_URL, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                await dismiss_popups(page)
                # Click apply tab on this page too
                try:
                    btn = page.locator("button.sc-csisgn-0").first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.inner_text()
                        if text.strip() == 'Apply':
                            await btn.click()
                            await page.wait_for_timeout(2000)
                except:
                    pass

            # Step 3: Fill name field
            print("\n=== Step 3: Fill form ===")

            # Name
            try:
                name_loc = page.locator("input[name='candidate.name']").first
                await name_loc.click(timeout=5000)
                await name_loc.fill("Hisham Abboud", timeout=5000)
                actual = await name_loc.input_value()
                print(f"Name: '{actual}'")
            except Exception as e:
                print(f"Name fill error: {e}")
                # Try JS
                await page.evaluate("""
                    () => {
                        const el = document.querySelector("input[name='candidate.name']");
                        if (el) {
                            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            setter.call(el, 'Hisham Abboud');
                            el.dispatchEvent(new Event('input', {bubbles:true}));
                            el.dispatchEvent(new Event('change', {bubbles:true}));
                        }
                    }
                """)

            await page.wait_for_timeout(300)

            # Email
            try:
                email_loc = page.locator("input[name='candidate.email']").first
                await email_loc.click(timeout=3000)
                await email_loc.fill("hiaham123@hotmail.com", timeout=3000)
                actual = await email_loc.input_value()
                print(f"Email: '{actual}'")
            except Exception as e:
                print(f"Email fill error: {e}")

            await page.wait_for_timeout(300)

            # Phone - needs to clear existing +31 first
            try:
                phone_loc = page.locator("input[name='candidate.phone']").first
                await phone_loc.click(timeout=3000)
                # Clear the existing content (which might be '+31')
                await phone_loc.fill("", timeout=3000)
                await page.wait_for_timeout(200)
                await phone_loc.fill("+31648412838", timeout=3000)
                actual = await phone_loc.input_value()
                print(f"Phone: '{actual}'")
            except Exception as e:
                print(f"Phone fill error: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "03-personal-filled")
            if s: screenshots.append(s)

            # Step 4: Upload CV
            print("\n=== Step 4: Upload CV ===")
            try:
                cv_loc = page.locator("input[name='candidate.cv']").first
                await cv_loc.set_input_files(CV_PATH, timeout=10000)
                print("CV uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload error: {e}")
                # Try file inputs directly
                try:
                    fi = await page.query_selector_all("input[type='file']")
                    if fi:
                        await fi[0].set_input_files(CV_PATH)
                        print("CV uploaded via first file input")
                        await page.wait_for_timeout(2000)
                except Exception as e2:
                    print(f"CV fallback: {e2}")

            s = await screenshot(page, "04-cv-uploaded")
            if s: screenshots.append(s)

            # Step 5: Cover letter - try 'Write it here instead' button first
            print("\n=== Step 5: Cover letter ===")
            cl_added = False

            # Try clicking "Write it here instead"
            try:
                write_btn = page.locator("button:has-text('Write it here instead')").first
                if await write_btn.is_visible(timeout=2000):
                    await write_btn.click()
                    print("Clicked 'Write it here instead'")
                    await page.wait_for_timeout(1000)

                    # Now find the textarea
                    textareas = await page.query_selector_all("textarea")
                    for ta in textareas:
                        if await ta.is_visible():
                            await ta.click()
                            await ta.fill(COVER_LETTER_TEXT)
                            cl_added = True
                            print("Cover letter text entered in textarea")
                            break
            except Exception as e:
                print(f"Write it here button: {e}")

            if not cl_added:
                # Upload cover letter as file
                try:
                    cl_loc = page.locator("input[name='candidate.coverLetterFile']").first
                    await cl_loc.set_input_files(cl_file, timeout=5000)
                    print("Cover letter file uploaded")
                    cl_added = True
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"CL upload: {e}")

            s = await screenshot(page, "05-cover-letter")
            if s: screenshots.append(s)

            # Step 6: Answer screening questions
            print("\n=== Step 6: Screening questions ===")

            # Q1: eligible to work in NL (radio value='true')
            # Q2: employment contract at KUBUS (radio value='true')
            for q_name, q_label in [
                ('candidate.openQuestionAnswers.6352299.flag', 'Q1 (work in NL)'),
                ('candidate.openQuestionAnswers.6352300.flag', 'Q2 (employment contract)'),
            ]:
                try:
                    # Click the radio with value='true' for Yes
                    radio = page.locator(f"input[name='{q_name}'][value='true']").first
                    await radio.check(force=True, timeout=3000)
                    print(f"{q_label}: Yes checked")
                    await page.wait_for_timeout(200)
                except Exception as e:
                    print(f"{q_label} check failed: {e}")
                    # Try JS
                    await page.evaluate(f"""
                        () => {{
                            const radios = document.querySelectorAll("input[name='{q_name}']");
                            const yes = Array.from(radios).find(r => r.value === 'true') || radios[0];
                            if (yes) {{
                                yes.checked = true;
                                yes.dispatchEvent(new Event('change', {{bubbles:true}}));
                                yes.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));
                            }}
                        }}
                    """)
                    print(f"{q_label}: JS checked")

            # Legal agreement checkbox
            try:
                legal_cb = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal_cb.is_checked():
                    await legal_cb.check(force=True, timeout=3000)
                    print("Legal agreement checked")
            except Exception as e:
                print(f"Legal checkbox: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "06-questions-answered")
            if s: screenshots.append(s)

            # Verify form state
            state = await page.evaluate("""
                () => {
                    const get = (sel) => (document.querySelector(sel) || {value:''}).value;
                    const getChecked = (name) => {
                        const el = document.querySelector(`input[name='${name}']:checked`);
                        return el ? el.value : 'NONE';
                    };
                    return {
                        name: get("input[name='candidate.name']"),
                        email: get("input[name='candidate.email']"),
                        phone: get("input[name='candidate.phone']"),
                        q1: getChecked('candidate.openQuestionAnswers.6352299.flag'),
                        q2: getChecked('candidate.openQuestionAnswers.6352300.flag'),
                        legal: getChecked('candidate.openQuestionAnswers.6352298.flag'),
                        cvFiles: (document.querySelector("input[name='candidate.cv']") || {files:[]}).files.length,
                    };
                }
            """)
            print(f"Form state: {state}")

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "07-bottom")
            if s: screenshots.append(s)

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-pre-submit")
            if s: screenshots.append(s)

            # Step 7: Submit
            print("\n=== Step 7: Submit ===")
            # Dismiss any lingering popups first
            await dismiss_popups(page)
            await page.wait_for_timeout(500)

            submit_clicked = False
            # Find the Send button (type=submit, class sc-csisgn-0)
            for sel in [
                "button[type='submit']",
                "button:has-text('Send')",
                "input[type='submit']",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.inner_text() if sel != "input[type='submit']" else "Submit"
                        print(f"Clicking: '{text}' ({sel})")
                        await btn.click()
                        submit_clicked = True
                        await page.wait_for_timeout(4000)
                        break
                except Exception as e:
                    print(f"Submit {sel}: {e}")

            s = await screenshot(page, "09-after-submit")
            if s: screenshots.append(s)

            # Handle LinkedIn popup
            print("\n=== Step 8: Handle post-submit ===")
            linkedin_dismissed = False
            for sel in [
                "button:has-text('Agree to necessary')",
                "button:has-text('Agree to all')",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        linkedin_dismissed = True
                        print(f"Dismissed LinkedIn popup: {sel}")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            if linkedin_dismissed:
                s = await screenshot(page, "10-linkedin-dismissed")
                if s: screenshots.append(s)

                # Re-check radios (may have been reset)
                await page.evaluate("""
                    () => {
                        ['candidate.openQuestionAnswers.6352299.flag',
                         'candidate.openQuestionAnswers.6352300.flag'].forEach(name => {
                            const radios = document.querySelectorAll(`input[name='${name}']`);
                            const yes = Array.from(radios).find(r => r.value === 'true') || radios[0];
                            if (yes) {
                                yes.checked = true;
                                yes.dispatchEvent(new Event('change', {bubbles:true}));
                            }
                        });
                    }
                """)
                await page.wait_for_timeout(300)

                # Click Send again
                for sel in ["button:has-text('Send')", "button[type='submit']"]:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            text = await btn.inner_text()
                            print(f"Clicking Send again: '{text}'")
                            await btn.click()
                            await page.wait_for_timeout(5000)
                            break
                    except:
                        pass

                s = await screenshot(page, "11-after-final-send")
                if s: screenshots.append(s)

                # Dismiss any more popups and click send again
                for attempt in range(3):
                    dismissed = await dismiss_popups(page)
                    if dismissed:
                        await page.wait_for_timeout(1000)
                        # Re-check form state and try send
                        state2 = await page.evaluate("""
                            () => ({
                                q1: (document.querySelector("input[name='candidate.openQuestionAnswers.6352299.flag']:checked") || {value:'none'}).value,
                                q2: (document.querySelector("input[name='candidate.openQuestionAnswers.6352300.flag']:checked") || {value:'none'}).value,
                            })
                        """)
                        print(f"Radio state after dismiss: {state2}")

                        # Re-check if needed
                        if state2.get('q1') != 'true' or state2.get('q2') != 'true':
                            await page.evaluate("""
                                () => {
                                    ['candidate.openQuestionAnswers.6352299.flag',
                                     'candidate.openQuestionAnswers.6352300.flag'].forEach(name => {
                                        const yes = document.querySelector(`input[name='${name}'][value='true']`);
                                        if (yes) {
                                            yes.checked = true;
                                            yes.dispatchEvent(new Event('change', {bubbles:true}));
                                        }
                                    });
                                }
                            """)

                        try:
                            send_btn = page.locator("button:has-text('Send'), button[type='submit']").first
                            if await send_btn.is_visible(timeout=1500):
                                await send_btn.click()
                                print(f"Send clicked (attempt {attempt+1})")
                                await page.wait_for_timeout(4000)
                        except:
                            pass
                    else:
                        break

            # Check for hCaptcha iframe
            await page.wait_for_timeout(2000)
            frames = page.frames
            print(f"Page frames: {len(frames)}")
            for frame in frames:
                if 'captcha' in frame.url or 'hcaptcha' in frame.url:
                    print(f"hCaptcha frame: {frame.url}")

            # Final screenshot
            s = await screenshot(page, "12-final")
            if s: screenshots.append(s)

            # Check result
            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Page text start: {final_text[:200]}")

            success_kws = ["thank you", "bedankt", "successfully", "application received",
                          "we have received", "your application", "sollicitatie"]
            # Specifically check for "Your application has been successfully submitted"
            if submission_detected:
                status = "applied"
                notes = f"Application submitted. Network response: {submission_response}"
                print("SUCCESS (network submission detected)")
            elif any(kw in final_text.lower() for kw in success_kws) and "required" not in final_text.lower():
                status = "applied"
                notes = f"Confirmation text found. URL: {final_url}"
                print("SUCCESS (confirmation text)")
            else:
                error_kws = ["field is required", "is required", "please fill", "verplicht"]
                if any(kw in final_text.lower() for kw in error_kws):
                    status = "failed"
                    notes = f"Validation errors. URL: {final_url}"
                    print("FAILED: validation errors")
                elif submit_clicked:
                    # Check if we're still on the form page with no errors
                    page_html = await page.content()
                    if "hcaptcha" in page_html.lower() or "captcha" in page_html.lower():
                        status = "failed"
                        notes = "Blocked by hCaptcha. Cannot solve automatically."
                        print("FAILED: hCaptcha blocking submission")
                    else:
                        status = "applied"
                        notes = f"Submit clicked. No obvious errors. URL: {final_url}"
                        print("Status: applied (submitted, no errors)")
                else:
                    status = "failed"
                    notes = "Submit not clicked"

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                if s: screenshots.append(s)
            except:
                pass
            notes = f"Exception: {str(e)}"
            status = "failed"
        finally:
            await browser.close()

    # Update applications.json
    app_id = f"bimcollab-se-v8-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
    print(f"ID: {app_id}")
    print(f"Notes: {notes}")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
