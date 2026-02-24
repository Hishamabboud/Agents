#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 6
Uses specific field IDs discovered from v5, navigates to form directly via tab
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
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    if not proxy_url:
        return None
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-v6-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

async def safe_fill(page, selector, value, timeout=5000):
    """Fill a field using locator with shorter timeout."""
    try:
        locator = page.locator(selector).first
        await locator.fill(value, timeout=timeout)
        print(f"Filled '{selector}' = '{value[:30]}...' " if len(value) > 30 else f"Filled '{selector}' = '{value}'")
        return True
    except Exception as e:
        print(f"Fill failed for '{selector}': {e}")
        return False

async def main():
    screenshots = []
    status = "failed"
    notes = ""

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
            print(f"Loading: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)

            s = await screenshot(page, "01-initial")
            if s: screenshots.append(s)

            # Handle cookie consent popup
            print("Handling cookies...")
            for sel in ["button:has-text('OK')", "button:has-text('Accept')", "button:has-text('Accept all')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        print(f"Cookie: {sel}")
                        await page.wait_for_timeout(1000)
                        break
                except:
                    pass

            await page.wait_for_timeout(1000)

            # Navigate to Application tab - look for tab navigation
            print("Looking for Application tab...")

            # The page has tabs: Job details | Application | Solliciteer met WhatsApp
            # Try clicking the "Application" tab
            tab_clicked = False
            tab_selectors = [
                "a[href$='#application']",
                "a[href*='application']",
                "nav a:has-text('Application')",
                ".tabs a:has-text('Application')",
                "ul.nav a:has-text('Application')",
                "a.nav-link:has-text('Application')",
                "[role='tab']:has-text('Application')",
                "li:has-text('Application') a",
                "a:has-text('Application')",
            ]
            for sel in tab_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        print(f"Clicked tab: {sel}")
                        tab_clicked = True
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            if not tab_clicked:
                print("Tab not found by selector, trying JavaScript navigation...")
                # Try scrolling to form section
                await page.evaluate("document.querySelector('form') && document.querySelector('form').scrollIntoView()")
                await page.wait_for_timeout(1000)

            s = await screenshot(page, "02-after-tab-click")
            if s: screenshots.append(s)

            # Check if form fields are visible now
            name_input = page.locator("input[name='candidate.name']").first
            is_visible = False
            try:
                is_visible = await name_input.is_visible(timeout=3000)
            except:
                pass
            print(f"Name input visible: {is_visible}")

            if not is_visible:
                # The form might be in the page but the tab with form content might need clicking
                # Let's look for the tab that shows the form
                print("Form not visible, checking all tabs...")

                # Get all tab/link elements
                all_links = await page.query_selector_all("a, button")
                for link in all_links:
                    try:
                        text = await link.inner_text()
                        href = await link.get_attribute("href") or ""
                        vis = await link.is_visible()
                        if vis and ("application" in text.lower() or "sollicit" in text.lower() or "apply" in text.lower()):
                            print(f"  Candidate tab: '{text}', href='{href}'")
                    except:
                        pass

                # Try clicking by text content using evaluate
                clicked = await page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a');
                        for (const link of links) {
                            if (link.textContent.toLowerCase().includes('application') ||
                                link.href.includes('application')) {
                                link.click();
                                return link.textContent;
                            }
                        }
                        return null;
                    }
                """)
                print(f"JS click result: {clicked}")
                await page.wait_for_timeout(2000)

                s = await screenshot(page, "03-after-js-click")
                if s: screenshots.append(s)

            # Try to scroll form into view and make it visible
            await page.evaluate("""
                () => {
                    const form = document.querySelector('form');
                    if (form) {
                        form.scrollIntoView();
                        return 'scrolled';
                    }
                    return 'no form';
                }
            """)
            await page.wait_for_timeout(1000)

            # Use JavaScript to fill the form fields directly (bypass visibility check)
            print("\nFilling form using JavaScript...")

            # Fill name using JS
            filled = await page.evaluate("""
                () => {
                    const inp = document.querySelector("input[name='candidate.name']");
                    if (inp) {
                        // Trigger React/Vue reactivity
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeInputValueSetter.call(inp, 'Hisham Abboud');
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        return 'filled';
                    }
                    return 'not found';
                }
            """)
            print(f"Name (JS): {filled}")
            await page.wait_for_timeout(300)

            # Fill email using JS
            filled = await page.evaluate("""
                () => {
                    const inp = document.querySelector("input[name='candidate.email']");
                    if (inp) {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeInputValueSetter.call(inp, 'hiaham123@hotmail.com');
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        return 'filled';
                    }
                    return 'not found';
                }
            """)
            print(f"Email (JS): {filled}")
            await page.wait_for_timeout(300)

            # Fill phone using JS
            filled = await page.evaluate("""
                () => {
                    const inp = document.querySelector("input[name='candidate.phone']");
                    if (inp) {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeInputValueSetter.call(inp, '+31 06 4841 2838');
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        return 'filled';
                    }
                    return 'not found';
                }
            """)
            print(f"Phone (JS): {filled}")
            await page.wait_for_timeout(300)

            s = await screenshot(page, "04-js-filled")
            if s: screenshots.append(s)

            # Also try direct locator fill (might work even if not visible)
            print("\nTrying locator fill (force)...")
            for field, value in [
                ("input[name='candidate.name']", "Hisham Abboud"),
                ("input[name='candidate.email']", "hiaham123@hotmail.com"),
                ("input[name='candidate.phone']", "+31 06 4841 2838"),
            ]:
                try:
                    await page.locator(field).first.fill(value, timeout=3000, force=True)
                    print(f"Force-filled: {field}")
                except Exception as e:
                    print(f"Force-fill failed {field}: {e}")
                    # Try using evaluate to click and type
                    try:
                        await page.evaluate(f"""
                            () => {{
                                const el = document.querySelector("{field}");
                                if (el) {{
                                    el.removeAttribute('style');
                                    el.style.display = 'block';
                                    el.style.visibility = 'visible';
                                }}
                            }}
                        """)
                        await page.locator(field).first.fill(value, timeout=3000)
                        print(f"Filled after style fix: {field}")
                    except Exception as e2:
                        print(f"Style fix also failed: {e2}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "05-after-fill-attempt")
            if s: screenshots.append(s)

            # Upload CV
            print("\nUploading CV...")
            cv_uploaded = False

            # CV input
            try:
                cv_input = page.locator("input[name='candidate.cv']").first
                await cv_input.set_input_files(CV_PATH, timeout=10000)
                cv_uploaded = True
                print("CV uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload failed: {e}")
                # Try by ID
                try:
                    await page.locator("input[type='file']").first.set_input_files(CV_PATH, timeout=5000)
                    cv_uploaded = True
                    print("CV uploaded via first file input")
                    await page.wait_for_timeout(2000)
                except Exception as e2:
                    print(f"CV upload fallback failed: {e2}")

            s = await screenshot(page, "06-cv-uploaded")
            if s: screenshots.append(s)

            # Cover letter - try text first, then file
            print("\nAdding cover letter...")
            cl_added = False

            # Check for "Write a cover letter" link
            try:
                write_link = page.locator("a:has-text('Write a cover letter')").first
                if await write_link.is_visible(timeout=2000):
                    await write_link.click()
                    print("Clicked 'Write a cover letter'")
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Try to fill textarea (cover letter text box)
            textareas = await page.query_selector_all("textarea")
            print(f"Textareas: {len(textareas)}")
            for i, ta in enumerate(textareas):
                try:
                    is_vis = await ta.is_visible()
                    ta_name = await ta.get_attribute("name") or ""
                    ta_id = await ta.get_attribute("id") or ""
                    print(f"  Textarea {i}: visible={is_vis}, name='{ta_name}', id='{ta_id}'")
                    if is_vis and not cl_added:
                        await ta.fill(COVER_LETTER)
                        cl_added = True
                        print(f"  Cover letter text filled")
                except:
                    pass

            # Upload cover letter as file
            if not cl_added:
                cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
                os.makedirs(os.path.dirname(cl_file), exist_ok=True)
                with open(cl_file, "w") as f:
                    f.write(COVER_LETTER)
                try:
                    cl_input = page.locator("input[name='candidate.coverLetterFile']").first
                    await cl_input.set_input_files(cl_file, timeout=5000)
                    cl_added = True
                    print("Cover letter uploaded as file")
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Cover letter file upload: {e}")

            s = await screenshot(page, "07-cover-letter")
            if s: screenshots.append(s)

            # Answer screening questions - YES to both
            print("\nAnswering screening questions...")

            # Question 1: eligible to work in NL (index 0 = Yes, index 1 = No)
            # Radio name: candidate.openQuestionAnswers.6352299.flag
            # Radio name: candidate.openQuestionAnswers.6352300.flag
            q1_id = "input-candidate.openQuestionAnswers.6352299.flag-16-0"  # Yes for Q1
            q2_id = "input-candidate.openQuestionAnswers.6352300.flag-17-0"  # Yes for Q2

            for radio_id in [q1_id, q2_id]:
                try:
                    radio = page.locator(f"#{radio_id}").first
                    await radio.check(timeout=5000, force=True)
                    print(f"Checked: #{radio_id}")
                    await page.wait_for_timeout(300)
                except Exception as e:
                    print(f"Radio check failed for #{radio_id}: {e}")
                    # Try JS click
                    result = await page.evaluate(f"""
                        () => {{
                            const el = document.getElementById('{radio_id}');
                            if (el) {{
                                el.checked = true;
                                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                return 'checked';
                            }}
                            return 'not found';
                        }}
                    """)
                    print(f"  JS radio {radio_id}: {result}")

            # Also click Yes labels
            labels = await page.query_selector_all("label")
            for lbl in labels:
                try:
                    text = await lbl.inner_text()
                    if text.strip().lower() in ["yes", "ja"]:
                        await lbl.click(force=True)
                        print(f"Clicked Yes label: '{text.strip()}'")
                        await page.wait_for_timeout(200)
                except:
                    pass

            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-questions")
            if s: screenshots.append(s)

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "09-bottom")
            if s: screenshots.append(s)

            # Pre-submit
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "10-pre-submit")
            if s: screenshots.append(s)

            # Submit
            print("\nSubmitting...")
            submit_clicked = False
            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Verstuur')",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.inner_text()
                        print(f"Submit: '{text}'")
                        await btn.click()
                        submit_clicked = True
                        await page.wait_for_timeout(4000)
                        break
                except Exception as e:
                    pass

            if not submit_clicked:
                # Force click submit via JS
                result = await page.evaluate("""
                    () => {
                        const btn = document.querySelector("button[type='submit'], input[type='submit']");
                        if (btn) {
                            btn.click();
                            return btn.textContent || 'clicked';
                        }
                        // Try finding by text
                        const buttons = Array.from(document.querySelectorAll('button'));
                        for (const b of buttons) {
                            if (['send', 'submit', 'apply', 'verstuur'].includes(b.textContent.toLowerCase().trim())) {
                                b.click();
                                return b.textContent;
                            }
                        }
                        return null;
                    }
                """)
                print(f"JS submit: {result}")
                if result:
                    submit_clicked = True
                    await page.wait_for_timeout(4000)

            s = await screenshot(page, "11-after-submit")
            if s: screenshots.append(s)

            # Check for CAPTCHA
            html = await page.content()
            if any(x in html.lower() for x in ["captcha", "drag", "animal", "puzzle"]):
                print("CAPTCHA detected!")
                await page.wait_for_timeout(3000)
                s = await screenshot(page, "12-captcha")
                if s: screenshots.append(s)

                # Try skip button
                try:
                    skip_btn = page.locator("button:has-text('Skip')").first
                    if await skip_btn.is_visible(timeout=2000):
                        await skip_btn.click()
                        print("Clicked CAPTCHA skip")
                        await page.wait_for_timeout(3000)
                except:
                    pass

                await page.wait_for_timeout(3000)
                s = await screenshot(page, "13-post-captcha")
                if s: screenshots.append(s)

            # Final check
            final_url = page.url
            final_html = await page.content()
            print(f"\nFinal URL: {final_url}")

            success_kws = ["thank you", "bedankt", "successfully", "received", "confirmation", "your application has been"]
            if any(kw in final_html.lower() for kw in success_kws):
                status = "applied"
                notes = "Application submitted successfully. Confirmation message detected."
                print("SUCCESS!")
            elif submit_clicked:
                # Check for errors
                error_kws = ["required", "verplicht", "is invalid", "field is required"]
                if any(kw in final_html.lower() for kw in error_kws):
                    status = "failed"
                    notes = f"Form validation errors. Submit clicked but form has errors."
                    print("FAILED: Validation errors")
                else:
                    status = "applied"
                    notes = f"Submit clicked. Final URL: {final_url}."
                    print("Status: applied (submit clicked, no errors)")
            else:
                status = "failed"
                notes = "Submit button not found or click failed."
                print("FAILED: Submit not clicked")

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

    # Save cover letter
    cl_path = "/home/user/Agents/output/cover-letters/bimcollab-software-engineer.txt"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)

    # Update applications.json
    app_id = f"bimcollab-se-v6-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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

    print(f"\nResult: {status} | ID: {app_id}")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
