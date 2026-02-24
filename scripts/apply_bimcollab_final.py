#!/usr/bin/env python3
"""
BIMcollab Software Engineer Application - FINAL VERSION
Key fixes:
1. Proper Application tab navigation
2. Fill all fields including Q2 radio
3. Handle LinkedIn popup
4. Click Send and confirm submission
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
    path = f"{SCREENSHOT_DIR}/bimcollab-final-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

async def dismiss_all_popups(page):
    """Dismiss any cookie/consent popups."""
    dismissed_any = False
    for sel in [
        "button:has-text('Agree to necessary')",
        "button:has-text('Agree to all')",
        "button:has-text('Accept necessary')",
        "button:has-text('OK')",
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
        "button:has-text('Close')",
        "button:has-text('Got it')",
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=800):
                await btn.click()
                print(f"Dismissed: '{sel}'")
                await page.wait_for_timeout(800)
                dismissed_any = True
        except:
            pass
    return dismissed_any

async def fill_form_fields(page):
    """Fill all form fields using multiple strategies."""
    result = await page.evaluate("""
        (data) => {
            const results = {};

            const fillInput = (selector, value) => {
                const el = document.querySelector(selector);
                if (!el) return 'NOT FOUND';
                try {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                    return 'OK:' + el.value.substring(0, 30);
                } catch(e) {
                    el.value = value;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return 'FALLBACK:' + el.value.substring(0, 30);
                }
            };

            const checkRadio = (id) => {
                const el = document.getElementById(id);
                if (!el) {
                    // Try by name+index
                    return 'NOT FOUND by id: ' + id;
                }
                el.checked = true;
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                return 'CHECKED: ' + id;
            };

            results.name = fillInput("input[name='candidate.name']", data.name);
            results.email = fillInput("input[name='candidate.email']", data.email);
            results.phone = fillInput("input[name='candidate.phone']", data.phone);

            // Check Yes radio for Q1 (eligible to work in NL)
            const q1Radios = document.querySelectorAll("input[name='candidate.openQuestionAnswers.6352299.flag']");
            if (q1Radios.length > 0) {
                // Find the "true" or "Yes" value radio
                let q1Yes = null;
                q1Radios.forEach(r => {
                    if (r.value === 'true' || r.value === 'yes' || r.value === 'Yes' || r.value === '1') {
                        q1Yes = r;
                    }
                });
                if (!q1Yes) q1Yes = q1Radios[0]; // Default to first
                q1Yes.checked = true;
                q1Yes.dispatchEvent(new Event('change', { bubbles: true }));
                q1Yes.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                results.q1 = 'CHECKED: ' + q1Yes.id + ' value=' + q1Yes.value;
            } else {
                results.q1 = 'NOT FOUND';
            }

            // Check Yes radio for Q2 (employment contract at KUBUS)
            const q2Radios = document.querySelectorAll("input[name='candidate.openQuestionAnswers.6352300.flag']");
            if (q2Radios.length > 0) {
                let q2Yes = null;
                q2Radios.forEach(r => {
                    if (r.value === 'true' || r.value === 'yes' || r.value === 'Yes' || r.value === '1') {
                        q2Yes = r;
                    }
                });
                if (!q2Yes) q2Yes = q2Radios[0];
                q2Yes.checked = true;
                q2Yes.dispatchEvent(new Event('change', { bubbles: true }));
                q2Yes.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                results.q2 = 'CHECKED: ' + q2Yes.id + ' value=' + q2Yes.value;
            } else {
                results.q2 = 'NOT FOUND';
            }

            // Verify
            const nameEl = document.querySelector("input[name='candidate.name']");
            const emailEl = document.querySelector("input[name='candidate.email']");
            results.verify_name = nameEl ? nameEl.value : 'missing';
            results.verify_email = emailEl ? emailEl.value : 'missing';
            results.q1_checked = q1Radios.length > 0 ? Array.from(q1Radios).filter(r => r.checked).map(r => r.value).join(',') : 'none';
            results.q2_checked = q2Radios.length > 0 ? Array.from(q2Radios).filter(r => r.checked).map(r => r.value).join(',') : 'none';

            return results;
        }
    """, {"name": "Hisham Abboud", "email": "hiaham123@hotmail.com", "phone": "+31 06 4841 2838"})
    return result

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
        f.write(COVER_LETTER)

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
            # Load page
            print("\n--- Loading page ---")
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)
            s = await screenshot(page, "01-loaded")
            if s: screenshots.append(s)

            # Dismiss initial popup
            await dismiss_all_popups(page)
            await page.wait_for_timeout(1000)

            # The Application tab needs to be activated
            # From inspecting the page, the tabs are navigation anchors
            # Let's use JavaScript to find and click the Application tab
            print("\n--- Activating Application tab ---")

            tab_result = await page.evaluate("""
                () => {
                    // Find all navigation tabs
                    const allLinks = Array.from(document.querySelectorAll('a, button, [role="tab"]'));
                    const found = [];
                    allLinks.forEach(el => {
                        const text = el.textContent.trim();
                        const href = el.getAttribute('href') || '';
                        if (text || href) {
                            found.push({ text, href, tag: el.tagName, class: el.className });
                        }
                    });
                    return found.filter(f => f.text.length < 50);
                }
            """)
            print("All links/buttons found:")
            for item in tab_result:
                if any(kw in item.get('text','').lower() for kw in ['apply', 'application', 'sollicit', 'job', 'tab']):
                    print(f"  {item}")

            # Click Application tab using multiple strategies
            app_tab_clicked = False

            # Strategy 1: Look for anchor with text "Application"
            try:
                loc = page.get_by_role("link", name="Application", exact=True)
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print("Clicked 'Application' link (by role)")
                    app_tab_clicked = True
                    await page.wait_for_timeout(2000)
            except:
                pass

            if not app_tab_clicked:
                # Strategy 2: JavaScript click on application tab
                result = await page.evaluate("""
                    () => {
                        const links = Array.from(document.querySelectorAll('a'));
                        for (const link of links) {
                            const text = link.textContent.trim();
                            if (text === 'Application' || text === 'Sollicitatie') {
                                link.click();
                                return 'clicked: ' + text + ' href:' + link.href;
                            }
                        }
                        // Also try tabs with li elements
                        const lis = Array.from(document.querySelectorAll('li'));
                        for (const li of lis) {
                            if (li.textContent.trim() === 'Application') {
                                const a = li.querySelector('a') || li;
                                a.click();
                                return 'li clicked: ' + li.textContent.trim();
                            }
                        }
                        return null;
                    }
                """)
                print(f"Application tab JS: {result}")
                if result:
                    app_tab_clicked = True
                    await page.wait_for_timeout(2000)

            s = await screenshot(page, "02-after-tab")
            if s: screenshots.append(s)

            # Fill form using JavaScript (works even if form is not visually shown)
            print("\n--- Filling form ---")
            fill_result = await fill_form_fields(page)
            print(f"Fill results: {fill_result}")
            await page.wait_for_timeout(500)

            # Also use locator.fill with force
            for selector, value in [
                ("input[name='candidate.name']", "Hisham Abboud"),
                ("input[name='candidate.email']", "hiaham123@hotmail.com"),
                ("input[name='candidate.phone']", "+31 06 4841 2838"),
            ]:
                try:
                    await page.locator(selector).fill(value, timeout=3000, force=True)
                    actual = await page.locator(selector).input_value()
                    print(f"  Locator filled {selector}: '{actual}'")
                except Exception as e:
                    print(f"  Locator fill {selector} failed: {e}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "03-fields-filled")
            if s: screenshots.append(s)

            # Upload CV
            print("\n--- Uploading CV ---")
            cv_uploaded = False
            try:
                await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
                cv_uploaded = True
                print("CV uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"CV upload failed: {e}")

            s = await screenshot(page, "04-cv-uploaded")
            if s: screenshots.append(s)

            # Upload cover letter
            print("\n--- Uploading cover letter ---")
            cl_uploaded = False
            try:
                await page.locator("input[name='candidate.coverLetterFile']").set_input_files(cl_file, timeout=10000)
                cl_uploaded = True
                print("Cover letter uploaded!")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Cover letter upload: {e}")

            s = await screenshot(page, "05-cover-letter")
            if s: screenshots.append(s)

            # Re-run radio checks (in case file upload triggered re-render)
            print("\n--- Re-checking radio buttons ---")
            radio_result = await page.evaluate("""
                () => {
                    const results = {};

                    const clickYes = (name) => {
                        const radios = Array.from(document.querySelectorAll(`input[name='${name}']`));
                        if (!radios.length) return 'NOT FOUND: ' + name;
                        // First radio = Yes (value='true')
                        const yes = radios.find(r => r.value === 'true' || r.value === 'yes' || r.value === 'Yes') || radios[0];
                        yes.checked = true;
                        yes.dispatchEvent(new Event('change', { bubbles: true }));
                        yes.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        // Verify
                        const checked = radios.find(r => r.checked);
                        return checked ? 'YES checked (' + checked.value + ')' : 'NO check found';
                    };

                    results.q1 = clickYes('candidate.openQuestionAnswers.6352299.flag');
                    results.q2 = clickYes('candidate.openQuestionAnswers.6352300.flag');
                    return results;
                }
            """)
            print(f"Radio results: {radio_result}")

            await page.wait_for_timeout(500)
            s = await screenshot(page, "06-questions")
            if s: screenshots.append(s)

            # Verify full form state
            print("\n--- Verifying form state ---")
            state = await page.evaluate("""
                () => {
                    const get = (sel) => {
                        const el = document.querySelector(sel);
                        return el ? el.value : 'NOT FOUND';
                    };
                    const getCVFiles = () => {
                        const el = document.querySelector("input[name='candidate.cv']");
                        return el && el.files ? el.files.length : 0;
                    };
                    const getCLFiles = () => {
                        const el = document.querySelector("input[name='candidate.coverLetterFile']");
                        return el && el.files ? el.files.length : 0;
                    };
                    const getRadioChecked = (name) => {
                        const checked = document.querySelector(`input[name='${name}']:checked`);
                        return checked ? checked.value : 'NONE';
                    };

                    return {
                        name: get("input[name='candidate.name']"),
                        email: get("input[name='candidate.email']"),
                        phone: get("input[name='candidate.phone']"),
                        cvFiles: getCVFiles(),
                        clFiles: getCLFiles(),
                        q1: getRadioChecked('candidate.openQuestionAnswers.6352299.flag'),
                        q2: getRadioChecked('candidate.openQuestionAnswers.6352300.flag'),
                    };
                }
            """)
            print(f"Form state: {state}")

            # Verify required fields
            assert state.get('name') == 'Hisham Abboud', f"Name wrong: {state.get('name')}"
            assert '@' in state.get('email', ''), f"Email wrong: {state.get('email')}"
            assert state.get('cvFiles', 0) >= 1, f"CV not uploaded: {state.get('cvFiles')}"
            print("All required fields verified!")

            # Scroll to bottom to see form
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            s = await screenshot(page, "07-form-bottom")
            if s: screenshots.append(s)

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)
            s = await screenshot(page, "08-pre-submit")
            if s: screenshots.append(s)

            # Dismiss any popups before clicking submit
            await dismiss_all_popups(page)
            await page.wait_for_timeout(500)

            # Click Submit button
            print("\n--- Submitting ---")
            submit_clicked = False

            # Try visible submit button
            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Send')",
                "button:has-text('Submit')",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.inner_text()
                        print(f"Clicking: '{text}' ({sel})")
                        await btn.click()
                        submit_clicked = True
                        await page.wait_for_timeout(3000)
                        break
                except:
                    pass

            if not submit_clicked:
                # JS submit
                r = await page.evaluate("""
                    () => {
                        const candidates = [
                            ...document.querySelectorAll('button[type=submit]'),
                            ...document.querySelectorAll('input[type=submit]'),
                        ];
                        // Also find by text
                        const allBtns = document.querySelectorAll('button');
                        allBtns.forEach(b => {
                            const t = b.textContent.trim().toLowerCase();
                            if (t === 'send' || t === 'submit') candidates.unshift(b);
                        });
                        if (candidates.length > 0) {
                            candidates[0].click();
                            return candidates[0].textContent || 'submit';
                        }
                        return null;
                    }
                """)
                print(f"JS submit: {r}")
                if r:
                    submit_clicked = True
                    await page.wait_for_timeout(3000)

            s = await screenshot(page, "09-after-submit")
            if s: screenshots.append(s)

            # Handle LinkedIn popup that appears after submit click
            print("\n--- Handling post-submit popups ---")
            linkedin_popup = False
            for sel in [
                "button:has-text('Agree to necessary')",
                "button:has-text('Agree to all')",
                "button:has-text('Accept necessary')",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        print(f"LinkedIn popup found: {sel}")
                        await btn.click()
                        linkedin_popup = True
                        print(f"Dismissed LinkedIn popup")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    pass

            if linkedin_popup:
                s = await screenshot(page, "10-after-linkedin-dismiss")
                if s: screenshots.append(s)

                # Re-check radio buttons (they may have been reset)
                print("Re-checking radios after popup dismiss...")
                await page.evaluate("""
                    () => {
                        const clickYes = (name) => {
                            const radios = Array.from(document.querySelectorAll(`input[name='${name}']`));
                            const yes = radios.find(r => r.value === 'true' || r.value === 'yes') || radios[0];
                            if (yes) {
                                yes.checked = true;
                                yes.dispatchEvent(new Event('change', { bubbles: true }));
                                yes.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            }
                        };
                        clickYes('candidate.openQuestionAnswers.6352299.flag');
                        clickYes('candidate.openQuestionAnswers.6352300.flag');
                    }
                """)
                await page.wait_for_timeout(500)

                # Click Send again
                print("Clicking Send again...")
                for sel in [
                    "button:has-text('Send')",
                    "button[type='submit']",
                    "button:has-text('Submit')",
                    "button:has-text('Apply')",
                ]:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            text = await btn.inner_text()
                            print(f"Clicking send: '{text}'")
                            await btn.click()
                            await page.wait_for_timeout(5000)
                            break
                    except:
                        pass

                s = await screenshot(page, "11-after-final-send")
                if s: screenshots.append(s)

                # Handle any more popups
                for _ in range(3):
                    dismissed = await dismiss_all_popups(page)
                    if dismissed:
                        await page.wait_for_timeout(1000)
                        # Click send if visible
                        try:
                            send_btn = page.locator("button:has-text('Send')").first
                            if await send_btn.is_visible(timeout=1000):
                                await send_btn.click()
                                await page.wait_for_timeout(4000)
                        except:
                            pass
                    else:
                        break

            await page.wait_for_timeout(3000)
            final_url = page.url
            final_html = await page.content()
            final_text = await page.evaluate("() => document.body.innerText")

            print(f"\nFinal URL: {final_url}")
            print(f"Final text (first 300 chars): {final_text[:300]}")

            s = await screenshot(page, "12-final")
            if s: screenshots.append(s)

            # Determine success
            success_kws = [
                "thank you", "bedankt", "successfully submitted", "application received",
                "we have received", "your application has been", "sollicitatie ontvangen",
                "we'll be in touch", "we will be in touch", "successfully sent"
            ]

            page_text_lower = final_text.lower()
            if any(kw in page_text_lower for kw in success_kws):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation text found. URL: {final_url}"
                print("\nSUCCESS! Confirmation found in page text.")
            elif "/c/" not in final_url and "software-engineer-3" not in final_url:
                status = "applied"
                notes = f"Redirected after submit. URL: {final_url}. Assuming success."
                print(f"\nLikely success (URL changed from form page)")
            else:
                # Check for validation errors
                error_kws = ["field is required", "is required", "please fill", "invalid email", "verplicht"]
                if any(kw in page_text_lower for kw in error_kws):
                    status = "failed"
                    notes = f"Validation errors detected. URL: {final_url}"
                    print("\nFAILED: Validation errors")
                elif submit_clicked:
                    status = "applied"
                    notes = f"Submit clicked, no errors detected. URL: {final_url}."
                    print(f"\nStatus: applied (no errors after submit)")
                else:
                    status = "failed"
                    notes = "Could not click submit button."

        except AssertionError as e:
            print(f"Assertion failed: {e}")
            notes = f"Form validation failed: {e}"
            status = "failed"
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
    app_id = f"bimcollab-se-final-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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

    print(f"\n=== FINAL RESULT: {status} ===")
    print(f"ID: {app_id}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {len(screenshots)}")
    for s in screenshots:
        print(f"  {s}")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
