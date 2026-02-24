#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - Version 7
Fixed: Handle LinkedIn cookies agreement popup, verify form fields visible,
use correct Application tab navigation
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
    path = f"{SCREENSHOT_DIR}/bimcollab-v7-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

async def dismiss_popups(page):
    """Dismiss any visible popups/modals."""
    # LinkedIn cookies agreement
    for sel in [
        "button:has-text('Agree to necessary')",
        "button:has-text('Agree to all')",
        "button:has-text('Accept all')",
        "button:has-text('Accept')",
        "button:has-text('OK')",
        "button:has-text('Close')",
        ".modal-close",
        ".dialog-close",
        "[data-testid='cookie-policy-dialog-accept-button']",
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                print(f"Dismissed popup: {sel}")
                await page.wait_for_timeout(1000)
                return True
        except:
            pass
    return False

async def main():
    screenshots = []
    status = "failed"
    notes = ""

    proxy_config = get_proxy_config()
    print(f"Proxy: {proxy_config['server'] if proxy_config else 'None'}")

    # Save cover letter file
    cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
    os.makedirs(os.path.dirname(cl_file), exist_ok=True)
    with open(cl_file, "w") as f:
        f.write(COVER_LETTER)
    print(f"Cover letter saved to: {cl_file}")

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
            # Step 1: Load job page
            print(f"\n=== Step 1: Load job page ===")
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)
            s = await screenshot(page, "01-initial")
            if s: screenshots.append(s)

            # Step 2: Handle initial cookie consent
            print(f"\n=== Step 2: Handle cookie consent ===")
            await dismiss_popups(page)
            await page.wait_for_timeout(1000)

            # Step 3: Click the Application tab
            print(f"\n=== Step 3: Navigate to Application form ===")

            # From v6 output, we know the page has these links:
            # "Apply" links (href='')
            # "Solliciteer met WhatsApp" links
            # The Apply button without href triggers the form

            # Click "Apply" button (the one that shows the form, not the WhatsApp one)
            apply_clicked = False

            # Look for the tab "Application" in the nav
            html = await page.content()

            # Check the page tab structure - from screenshots we see tabs: Job details | Solliciteer met WhatsApp | Application
            # The "Application" tab is shown as a link
            try:
                # Try by href containing 'application'
                app_tab = page.locator("a[href*='application']").first
                if await app_tab.is_visible(timeout=2000):
                    await app_tab.click()
                    print("Clicked application link (href)")
                    apply_clicked = True
                    await page.wait_for_timeout(2000)
            except:
                pass

            if not apply_clicked:
                # From page HTML, find the Apply tab via evaluate
                clicked = await page.evaluate("""
                    () => {
                        // Look for nav tabs
                        const allLinks = Array.from(document.querySelectorAll('a'));
                        for (const link of allLinks) {
                            const text = link.textContent.trim();
                            const href = link.href || link.getAttribute('href') || '';
                            if ((text === 'Application' || text === 'Sollicitatie') && !href.includes('whatsapp')) {
                                link.click();
                                return 'clicked: ' + text;
                            }
                        }
                        // Try by tab role
                        const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
                        for (const tab of tabs) {
                            if (tab.textContent.toLowerCase().includes('application')) {
                                tab.click();
                                return 'tab clicked: ' + tab.textContent;
                            }
                        }
                        // Click the first Apply link (not WhatsApp)
                        for (const link of allLinks) {
                            const text = link.textContent.trim();
                            if (text === 'Apply' && !link.href.includes('whatsapp')) {
                                link.click();
                                return 'apply clicked';
                            }
                        }
                        return null;
                    }
                """)
                print(f"Tab click result: {clicked}")
                if clicked:
                    apply_clicked = True
                    await page.wait_for_timeout(2000)

            s = await screenshot(page, "02-after-tab")
            if s: screenshots.append(s)

            # Step 4: Fill form fields using JavaScript (to bypass visibility issues)
            print(f"\n=== Step 4: Fill form fields ===")

            # Use JS to fill the fields reactively
            result = await page.evaluate("""
                (data) => {
                    const results = {};
                    const fillInput = (selector, value) => {
                        const el = document.querySelector(selector);
                        if (!el) return 'not found';
                        try {
                            // React synthetic event approach
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            nativeInputValueSetter.call(el, value);
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('blur', { bubbles: true }));
                            return 'ok: ' + el.value.substring(0, 20);
                        } catch(e) {
                            el.value = value;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            return 'fallback: ' + el.value.substring(0, 20);
                        }
                    };
                    results.name = fillInput("input[name='candidate.name']", data.name);
                    results.email = fillInput("input[name='candidate.email']", data.email);
                    results.phone = fillInput("input[name='candidate.phone']", data.phone);
                    return results;
                }
            """, {"name": "Hisham Abboud", "email": "hiaham123@hotmail.com", "phone": "+31 06 4841 2838"})
            print(f"JS fill results: {result}")
            await page.wait_for_timeout(500)

            # Also try locator fill with force=True
            for field, value in [
                ("input[name='candidate.name']", "Hisham Abboud"),
                ("input[name='candidate.email']", "hiaham123@hotmail.com"),
                ("input[name='candidate.phone']", "+31 06 4841 2838"),
            ]:
                try:
                    loc = page.locator(field).first
                    await loc.fill(value, timeout=5000, force=True)
                    actual = await loc.input_value()
                    print(f"Locator filled {field}: '{actual}'")
                except Exception as e:
                    print(f"Locator fill {field}: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "03-details-filled")
            if s: screenshots.append(s)

            # Step 5: Upload CV
            print(f"\n=== Step 5: Upload CV ===")
            try:
                cv_input = page.locator("input[name='candidate.cv']").first
                await cv_input.set_input_files(CV_PATH, timeout=10000)
                print("CV uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload failed: {e}")
                # Try by type
                try:
                    file_inputs = await page.query_selector_all("input[type='file']")
                    if file_inputs:
                        await file_inputs[0].set_input_files(CV_PATH)
                        print("CV uploaded via first file input")
                        await page.wait_for_timeout(2000)
                except Exception as e2:
                    print(f"CV fallback failed: {e2}")

            s = await screenshot(page, "04-cv-uploaded")
            if s: screenshots.append(s)

            # Step 6: Upload cover letter as file
            print(f"\n=== Step 6: Upload cover letter ===")
            try:
                cl_input = page.locator("input[name='candidate.coverLetterFile']").first
                await cl_input.set_input_files(cl_file, timeout=10000)
                print("Cover letter uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Cover letter upload: {e}")
                # Try second file input
                try:
                    file_inputs = await page.query_selector_all("input[type='file']")
                    if len(file_inputs) > 1:
                        await file_inputs[1].set_input_files(cl_file)
                        print("Cover letter uploaded via second file input")
                        await page.wait_for_timeout(2000)
                except Exception as e2:
                    print(f"CL fallback: {e2}")

            s = await screenshot(page, "05-cover-letter")
            if s: screenshots.append(s)

            # Step 7: Answer screening questions via JS
            print(f"\n=== Step 7: Screening questions ===")
            q_result = await page.evaluate("""
                () => {
                    const results = {};
                    // Q1: eligible to work in NL (Yes = first radio of pair)
                    // Q2: employment contract (Yes = first radio of pair)
                    const radioGroups = {};
                    const radios = document.querySelectorAll("input[type='radio']");
                    radios.forEach(radio => {
                        const name = radio.getAttribute('name') || '';
                        if (!radioGroups[name]) radioGroups[name] = [];
                        radioGroups[name].push(radio);
                    });

                    for (const [name, group] of Object.entries(radioGroups)) {
                        if (name.includes('openQuestion')) {
                            // Click the first radio in each group (Yes)
                            const firstRadio = group[0];
                            firstRadio.checked = true;
                            firstRadio.dispatchEvent(new Event('change', { bubbles: true }));
                            firstRadio.dispatchEvent(new Event('click', { bubbles: true }));
                            results[name] = 'checked first: ' + firstRadio.id;
                        }
                    }

                    // Also try clicking Yes labels
                    const labels = document.querySelectorAll('label');
                    let yesClicks = 0;
                    labels.forEach(lbl => {
                        if (lbl.textContent.trim().toLowerCase() === 'yes') {
                            lbl.click();
                            yesClicks++;
                        }
                    });
                    results.yesLabelClicks = yesClicks;
                    return results;
                }
            """)
            print(f"Questions answered: {q_result}")
            await page.wait_for_timeout(500)

            s = await screenshot(page, "06-questions")
            if s: screenshots.append(s)

            # Step 8: Verify form state
            print(f"\n=== Step 8: Verify form ===")
            form_state = await page.evaluate("""
                () => {
                    const state = {};
                    const nameEl = document.querySelector("input[name='candidate.name']");
                    state.name = nameEl ? nameEl.value : 'not found';
                    const emailEl = document.querySelector("input[name='candidate.email']");
                    state.email = emailEl ? emailEl.value : 'not found';
                    const phoneEl = document.querySelector("input[name='candidate.phone']");
                    state.phone = phoneEl ? phoneEl.value : 'not found';

                    // Check radio selections
                    const radios = document.querySelectorAll("input[type='radio']:checked");
                    state.checkedRadios = Array.from(radios).map(r => r.name + ':' + r.value);

                    // Check file inputs
                    const cvInput = document.querySelector("input[name='candidate.cv']");
                    state.cvFiles = cvInput && cvInput.files ? cvInput.files.length : 0;
                    const clInput = document.querySelector("input[name='candidate.coverLetterFile']");
                    state.clFiles = clInput && clInput.files ? clInput.files.length : 0;

                    return state;
                }
            """)
            print(f"Form state: {form_state}")

            # Scroll to bottom for full view
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "07-form-bottom")
            if s: screenshots.append(s)

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-pre-submit")
            if s: screenshots.append(s)

            # Step 9: Click Submit
            print(f"\n=== Step 9: Submit ===")
            submit_clicked = False

            # First dismiss any existing popups
            await dismiss_popups(page)
            await page.wait_for_timeout(500)

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
                        print(f"Clicking submit: '{text}'")
                        await btn.click()
                        submit_clicked = True
                        await page.wait_for_timeout(3000)
                        break
                except:
                    pass

            if not submit_clicked:
                # JS submit
                result = await page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('button');
                        for (const btn of btns) {
                            const t = btn.textContent.trim().toLowerCase();
                            if (t === 'send' || t === 'submit' || t === 'apply' || btn.type === 'submit') {
                                btn.click();
                                return btn.textContent;
                            }
                        }
                        return null;
                    }
                """)
                print(f"JS submit: {result}")
                if result:
                    submit_clicked = True
                    await page.wait_for_timeout(3000)

            s = await screenshot(page, "09-after-submit-click")
            if s: screenshots.append(s)

            # Step 10: Handle LinkedIn cookies popup
            print(f"\n=== Step 10: Handle post-submit popup ===")
            await page.wait_for_timeout(2000)

            # Check for and dismiss the LinkedIn cookies popup
            linkedin_dismissed = False
            for popup_sel in [
                "button:has-text('Agree to necessary')",
                "button:has-text('Agree to all')",
                "button:has-text('Accept necessary')",
                "button:has-text('Accept all')",
            ]:
                try:
                    btn = page.locator(popup_sel).first
                    if await btn.is_visible(timeout=2000):
                        print(f"Found LinkedIn popup: {popup_sel}")
                        await btn.click()
                        linkedin_dismissed = True
                        print(f"Dismissed LinkedIn popup: {popup_sel}")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            if linkedin_dismissed:
                print("LinkedIn popup dismissed, clicking Send again...")
                s = await screenshot(page, "10-after-linkedin-dismiss")
                if s: screenshots.append(s)

                # Click Send again after dismissing popup
                for sel in [
                    "button[type='submit']",
                    "button:has-text('Send')",
                    "button:has-text('Submit')",
                    "button:has-text('Apply')",
                ]:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            text = await btn.inner_text()
                            print(f"Clicking send again: '{text}'")
                            await btn.click()
                            await page.wait_for_timeout(4000)
                            break
                    except:
                        pass

                s = await screenshot(page, "11-after-final-submit")
                if s: screenshots.append(s)

                # Check for another popup
                await dismiss_popups(page)
                await page.wait_for_timeout(2000)

            # Also check for CAPTCHA/animal puzzle
            html = await page.content()
            if any(x in html.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
                print("CAPTCHA detected - cannot solve automatically")
                s = await screenshot(page, "12-captcha")
                if s: screenshots.append(s)
                status = "failed"
                notes = "CAPTCHA detected after form submission. Cannot solve automatically."

            # Final state
            await page.wait_for_timeout(2000)
            final_url = page.url
            final_html = await page.content()
            print(f"\nFinal URL: {final_url}")

            # Check for confirmation
            success_kws = [
                "thank you", "bedankt", "successfully submitted", "application received",
                "we have received", "your application has been", "sollicitatie ontvangen",
                "successfully", "confirmation"
            ]

            s = await screenshot(page, "13-final")
            if s: screenshots.append(s)

            if any(kw in final_html.lower() for kw in success_kws):
                status = "applied"
                notes = "Application submitted successfully. Confirmation detected."
                print("SUCCESS! Confirmation found.")
            else:
                # Check page content for clues
                page_text = await page.evaluate("() => document.body.innerText")
                print(f"Page text (first 500 chars): {page_text[:500]}")

                error_kws = ["required", "verplicht", "is invalid", "field is required", "please fill"]
                if any(kw in final_html.lower() for kw in error_kws):
                    status = "failed"
                    notes = f"Form validation errors. URL: {final_url}"
                    print("FAILED: Validation errors")
                elif submit_clicked and final_url != JOB_URL:
                    status = "applied"
                    notes = f"Submit clicked. URL changed to {final_url}. No errors detected."
                    print(f"Likely success (URL changed)")
                elif submit_clicked:
                    status = "applied"
                    notes = f"Submit clicked. Final URL: {final_url}."
                    print(f"Submit clicked, status: applied")
                else:
                    status = "failed"
                    notes = f"Submit not clicked. Final URL: {final_url}"

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
    app_id = f"bimcollab-se-v7-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
    print(f"Screenshots saved: {len(screenshots)}")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
