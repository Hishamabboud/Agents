#!/usr/bin/env python3
"""
Fortanix job application via Playwright.
Target: Senior Software Engineer - Backend Microservices, Rust (Netherlands)
Apply URL: https://apply.workable.com/fortanix/j/DFCBABCC33/apply/

Known form structure (from previous run):
  - inputs: firstname, lastname, email, phone, address, city, postcode, country, file
  - textareas: summary, cover_letter, QA_11110678..QA_11110683 (screening questions)
  - Screening Qs visible: microservices experience, Rust proficiency (1-10)

Cookie modal issue: clicking 'Cookie settings' link opens a modal.
Fix: only click the main banner 'Accept all', never 'Cookie settings'.
"""

import asyncio
import os
import re
import json
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

JOB_TITLE = "Senior Software Engineer - Backend Microservices, Rust (Netherlands)"
JOB_SHORTCODE = "DFCBABCC33"
JOB_URL = "https://apply.workable.com/fortanix/j/DFCBABCC33/"
APPLY_URL = "https://apply.workable.com/fortanix/j/DFCBABCC33/apply/"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "address": "Eindhoven",
    "city": "Eindhoven",
    "postcode": "5600",
    "country": "Netherlands",
}

# Answers to known screening questions for this role
# QA_11110678..QA_11110683 - order from form:
# "How many years of experience do you have working on microservices architecture and distributed systems?"
# "On a scale of 1-10, how proficient are you with Rust?"
# + other questions
SCREENING_ANSWERS = {
    "QA_11110678": "I have 3+ years of experience working with microservices architecture and distributed systems, including REST APIs, message queues, and cloud deployments via Azure and Kubernetes.",
    "QA_11110679": "I have 3+ years of experience in backend development using .NET/C# and Python, including API design, database integration, and cloud-based deployments.",
    "QA_11110680": "I am based in Eindhoven, Netherlands and available to work hybrid on-site at High Tech Campus.",
    "QA_11110681": "Yes, I am authorized to work in the Netherlands as an EU resident.",
    "QA_11110682": "3 on a scale of 1-10 - I have worked with Rust in personal projects and am actively improving my proficiency.",
    "QA_11110683": "I am available to start within 4 weeks and am flexible on timing.",
}

COVER_LETTER = """Dear Hiring Team at Fortanix,

I am writing to express my enthusiasm for the Software Engineer position at Fortanix in Eindhoven. As a Software Service Engineer at Actemium (VINCI Energies) with a background in full-stack development using .NET, C#, Python, and JavaScript, I am excited by the opportunity to contribute to Fortanix's mission of securing data in the cloud and beyond.

My experience includes building and maintaining industrial applications, developing REST APIs, working with cloud infrastructure (Azure, Kubernetes), and contributing to security-focused projects, including a GDPR data anonymization solution during my graduation project at Fontys ICT Cyber Security Research Group.

Fortanix's work on confidential computing and data security aligns strongly with my professional interests and background. I am based in Eindhoven and would welcome the chance to join the team at High Tech Campus.

Thank you for your consideration. I look forward to the opportunity to discuss how I can contribute.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
"""

def get_proxy_config():
    proxy_url = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or
                 os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    if not proxy_url:
        return None, None, None
    m = re.match(r'https?://([^:@]+):([^@]+)@([^/]+)', proxy_url)
    if m:
        user, pwd, server = m.groups()
        return f"http://{server}", user, pwd
    m2 = re.match(r'https?://([^/]+)', proxy_url)
    if m2:
        return f"http://{m2.group(1)}", None, None
    return None, None, None

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"fortanix-{name}-{ts()}.png")
    try:
        await page.screenshot(path=path, full_page=False, timeout=15000)
        print(f"  Screenshot: {path}")
        return path
    except Exception as e:
        print(f"  Screenshot failed ({name}): {e}")
        return ""

async def update_app(status, notes, shot="", cl="", job_title="", job_url=""):
    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)
    for app in apps:
        if app.get("company", "").lower() == "fortanix":
            app["status"] = status
            app["date_applied"] = datetime.now().strftime("%Y-%m-%d")
            app["notes"] = notes
            if shot:
                app["screenshot"] = shot
            if cl:
                app["cover_letter_file"] = cl
            if job_title:
                app["role"] = job_title
            if job_url:
                app["url"] = job_url
            app["resume_file"] = "profile/Hisham Abboud CV.pdf"
            break
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"  Tracker: '{status}'")

async def close_all_modals(page):
    """
    Close any open modals/dialogs by:
    1. Clicking 'Accept all' in cookie modal (NOT 'Cookie settings')
    2. Clicking X button on any other modal
    3. Removing backdrop elements via JS
    """
    closed = 0

    # Close cookie About Cookies modal by clicking 'Accept all' inside it
    for sel in [
        "[data-role='modal-wrapper'] button:has-text('Accept all')",
        "[data-role='dialog-content'] button:has-text('Accept all')",
        "button:has-text('Accept all')",
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                txt = await el.inner_text()
                print(f"  Closing cookie modal via '{txt.strip()}'")
                await el.click(timeout=5000)
                await asyncio.sleep(1)
                closed += 1
                break
        except Exception as e:
            pass

    # Close any remaining modals via X button
    for sel in [
        "[data-role='modal-wrapper'] button[aria-label='Close']",
        "[data-role='modal-wrapper'] button:has-text('×')",
        "[data-role='dialog-content'] button[aria-label='Close']",
        "button[aria-label='close']",
        "button[aria-label='Close']",
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                print(f"  Closing modal via X button")
                await el.click(timeout=3000)
                await asyncio.sleep(1)
                closed += 1
        except:
            pass

    # Remove all modal/backdrop DOM elements
    removed = await page.evaluate("""
        () => {
            let count = 0;
            const selectors = [
                '[data-role="modal-wrapper"]',
                '[data-role="backdrop"]',
                '[data-evergreen-dialog-backdrop]',
                '[data-ui="backdrop"]',
            ];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    el.style.display = 'none';
                    el.style.pointerEvents = 'none';
                    // Don't remove from DOM to avoid React errors - just hide
                    count++;
                });
            });
            return count;
        }
    """)
    if removed > 0:
        print(f"  Hidden {removed} modal/backdrop elements via JS")

    return closed

async def accept_cookies_main_banner(page):
    """Accept cookies via the main bottom banner (not Cookie settings link)."""
    # The banner has: 'Cookies settings' link + 'Accept all' + 'Decline all' buttons
    # We MUST click 'Accept all' button, not the 'Cookies settings' link
    for sel in [
        # Target the button specifically, not links
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('Accept cookies')",
    ]:
        try:
            els = await page.query_selector_all(sel)
            for el in els:
                if await el.is_visible():
                    # Verify it's in the main cookie banner, not inside a modal
                    parent_modal = await el.evaluate_handle(
                        "el => el.closest('[data-role=\"modal-wrapper\"]')"
                    )
                    is_in_modal = await parent_modal.evaluate("el => el !== null")
                    txt = await el.inner_text()
                    print(f"  Cookie banner button: '{txt.strip()}' (in_modal={is_in_modal})")
                    await el.click(timeout=5000)
                    await asyncio.sleep(1)
                    return True
        except Exception as e:
            pass
    return False

async def fill_input(page, name_or_sel, value):
    """Fill an input by name attribute or selector."""
    for sel in [
        f"input[name='{name_or_sel}']",
        f"textarea[name='{name_or_sel}']",
        name_or_sel,
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(value)
                actual = await el.input_value()
                if actual:
                    return True
        except:
            pass
    return False

async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    # Save cover letter
    cl_path = "/home/user/Agents/output/cover-letters/fortanix-software-engineer.md"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)
    print(f"Cover letter saved: {cl_path}")

    proxy_server, proxy_user, proxy_pass = get_proxy_config()
    print(f"Proxy: {proxy_server}")

    proxy_cfg = None
    if proxy_server:
        proxy_cfg = {"server": proxy_server}
        if proxy_user:
            proxy_cfg["username"] = proxy_user
        if proxy_pass:
            proxy_cfg["password"] = proxy_pass

    last_shot = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_cfg,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            proxy=proxy_cfg,
        )
        page = await ctx.new_page()

        try:
            # === Step 1: Navigate directly to the Apply page ===
            print(f"\n=== Step 1: Navigate to Apply page ===")
            resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"  Status: {resp.status if resp else 'N/A'}")
            await asyncio.sleep(5)
            last_shot = await screenshot(page, "01-apply-page-loaded")
            print(f"  Title: {await page.title()}")
            print(f"  URL: {page.url}")

            # === Step 2: Accept the cookie banner ===
            print(f"\n=== Step 2: Accept cookie banner ===")
            # First check and close any modal
            await close_all_modals(page)
            await asyncio.sleep(1)
            # Accept the main banner
            accepted = await accept_cookies_main_banner(page)
            print(f"  Cookie banner accepted: {accepted}")
            await asyncio.sleep(1)
            last_shot = await screenshot(page, "02-cookies-accepted")

            # === Step 3: Inspect the form to understand fields ===
            print(f"\n=== Step 3: Inspect form ===")
            inputs = await page.query_selector_all("input:not([type='file'])")
            textareas = await page.query_selector_all("textarea")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"  Text inputs: {len(inputs)}, Textareas: {len(textareas)}, File inputs: {len(file_inputs)}")

            # Get labels for textareas (screening questions)
            print("  Textarea fields:")
            for ta in textareas:
                n = await ta.get_attribute("name") or ""
                i = await ta.get_attribute("id") or ""
                # Try to find associated label
                label_text = ""
                if i:
                    try:
                        label = await page.query_selector(f"label[for='{i}']")
                        if label:
                            label_text = await label.inner_text()
                    except:
                        pass
                # Try to find parent label or preceding text
                if not label_text:
                    try:
                        label_text = await ta.evaluate("""
                            el => {
                                // Look for preceding sibling or parent with text
                                let prev = el.previousElementSibling;
                                if (prev) return prev.innerText.trim();
                                let parent = el.parentElement;
                                if (parent) {
                                    let label = parent.querySelector('label');
                                    if (label) return label.innerText.trim();
                                    // Look for text nodes
                                    let text = parent.innerText.replace(el.innerText, '').trim();
                                    return text.slice(0, 100);
                                }
                                return '';
                            }
                        """)
                    except:
                        pass
                print(f"    textarea[name={n}] label='{label_text[:80]}'")

            # === Step 4: Fill personal info fields ===
            print(f"\n=== Step 4: Fill personal information ===")
            fields_filled = {}

            field_data = [
                ("firstname", APPLICANT["first_name"]),
                ("lastname", APPLICANT["last_name"]),
                ("email", APPLICANT["email"]),
                ("phone", APPLICANT["phone"]),
                ("address", APPLICANT["address"]),
                ("city", APPLICANT["city"]),
                ("postcode", APPLICANT["postcode"]),
                ("country", APPLICANT["country"]),
                ("summary", "Software Engineer with 3+ years experience in .NET, C#, Python, REST APIs, and cloud infrastructure."),
                ("cover_letter", COVER_LETTER),
            ]

            for field_name, value in field_data:
                ok = await fill_input(page, field_name, value)
                if ok:
                    print(f"  Filled '{field_name}': '{value[:50]}'")
                    fields_filled[field_name] = True
                else:
                    print(f"  Could not fill '{field_name}'")

            # Fill phone via tel input if needed
            if "phone" not in fields_filled:
                ok = await fill_input(page, "input[type='tel']", APPLICANT["phone"])
                if ok:
                    print(f"  Filled phone via type=tel")
                    fields_filled["phone"] = True

            # === Step 5: Fill screening questions ===
            print(f"\n=== Step 5: Fill screening questions ===")
            for qa_name, answer in SCREENING_ANSWERS.items():
                ok = await fill_input(page, qa_name, answer)
                if ok:
                    print(f"  Filled {qa_name}: '{answer[:60]}'")
                    fields_filled[qa_name] = True
                else:
                    print(f"  Could not fill {qa_name}")

            print(f"  Total fields filled: {len(fields_filled)}")
            last_shot = await screenshot(page, "03-form-filled")

            # === Step 6: Upload resume ===
            print(f"\n=== Step 6: Upload resume ===")
            if file_inputs and os.path.exists(RESUME_PDF):
                try:
                    await file_inputs[0].set_input_files(RESUME_PDF)
                    print(f"  Resume uploaded: {RESUME_PDF}")
                    await asyncio.sleep(3)
                    last_shot = await screenshot(page, "04-resume-uploaded")
                except Exception as e:
                    print(f"  Upload error: {e}")
            else:
                print(f"  File inputs: {len(file_inputs)}, Resume exists: {os.path.exists(RESUME_PDF)}")

            # === Step 7: Scroll to bottom and take pre-submit screenshot ===
            print(f"\n=== Step 7: Pre-submit ===")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            last_shot = await screenshot(page, "05-pre-submit")

            # Check visible body text to understand form state
            body_text = await page.evaluate("document.body.innerText")
            print(f"  Body text (last 600): {body_text[-600:]}")

            # === Step 8: Close any modal that may be blocking ===
            print(f"\n=== Step 8: Ensure no modals blocking ===")
            modals_closed = await close_all_modals(page)
            print(f"  Modals closed: {modals_closed}")
            await asyncio.sleep(1)

            # === Step 9: Find and click submit button ===
            print(f"\n=== Step 9: Submit application ===")
            submit_btn = None
            for sel in [
                "button[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "input[type='submit']",
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        vis = await el.is_visible()
                        en = await el.is_enabled()
                        txt = await el.inner_text()
                        print(f"  Submit candidate: '{txt.strip()}' visible={vis} enabled={en}")
                        if vis and en:
                            submit_btn = el
                            break
                except:
                    pass

            if submit_btn and len(fields_filled) > 2:
                # Use JS click to bypass any invisible overlay
                print("  Submitting via JS click...")
                try:
                    submitted = await page.evaluate("""
                        () => {
                            const btn = document.querySelector('button[type="submit"]');
                            if (btn) {
                                btn.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    print(f"  JS submit result: {submitted}")
                    await asyncio.sleep(7)
                    last_shot = await screenshot(page, "06-post-submit")
                    final_url = page.url
                    body = await page.evaluate("document.body.innerText")
                    print(f"  Post-submit URL: {final_url}")
                    print(f"  Post-submit body (400): {body[:400]}")

                    if any(w in body.lower() for w in ["thank", "success", "submitted", "received", "confirmation", "application has been"]):
                        await update_app("applied",
                            f"Application submitted successfully to '{JOB_TITLE}'. "
                            f"Confirmation detected. URL: {final_url}",
                            last_shot, cl_path, JOB_TITLE, JOB_URL)
                    elif any(w in body.lower() for w in ["error", "required", "invalid", "missing"]):
                        await update_app("failed",
                            f"Submit attempted but validation errors. Body: {body[:300]}. URL: {final_url}",
                            last_shot, cl_path, JOB_TITLE, JOB_URL)
                    else:
                        await update_app("applied",
                            f"Submit button clicked for '{JOB_TITLE}'. "
                            f"No explicit confirmation/error detected. URL: {final_url}",
                            last_shot, cl_path, JOB_TITLE, JOB_URL)
                except Exception as e:
                    print(f"  Submit error: {e}")
                    last_shot = await screenshot(page, "06-submit-error")
                    await update_app("failed",
                        f"Submit error: {e}. Fields filled: {len(fields_filled)}",
                        last_shot, cl_path, JOB_TITLE, JOB_URL)
            else:
                notes = (f"Submit not attempted: {len(fields_filled)} fields filled, "
                         f"submit_btn={'found' if submit_btn else 'not found'}. "
                         f"URL: {page.url}")
                print(f"  {notes}")
                await update_app("partial", notes, last_shot, cl_path, JOB_TITLE, JOB_URL)

        except Exception as e:
            import traceback
            print(f"\nError: {e}")
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                if s:
                    last_shot = s
            except:
                pass
            await update_app("failed", f"Error: {str(e)}", last_shot, cl_path, JOB_TITLE, JOB_URL)
        finally:
            await browser.close()
            print(f"\nDone. Last screenshot: {last_shot}")

if __name__ == "__main__":
    asyncio.run(main())
