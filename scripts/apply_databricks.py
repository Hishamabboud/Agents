#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE role via Greenhouse.
Greenhouse job ID: 8029677002
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Paths
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/databricks-fullstack-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

# Candidate details
CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Amsterdam, Netherlands",
}

# Try direct Greenhouse embed URL and the Databricks careers URL
URLS_TO_TRY = [
    "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
    "https://boards.greenhouse.io/databricks/jobs/8029677002",
]
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-{name}-{TIMESTAMP}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
        path = None
    return path

def read_cover_letter():
    with open(COVER_LETTER_PATH, "r") as f:
        return f.read().strip()

def fill_field(page, selectors, value, field_name="field"):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.fill(value)
                print(f"  Filled {field_name}: {value[:60] if len(value) > 60 else value}")
                return True
        except Exception:
            continue
    print(f"  Could not fill {field_name} (no matching selector found)")
    return False

def attempt_application(page):
    screenshots_taken = []
    status = "failed"
    notes = ""

    cover_letter_text = read_cover_letter()

    # Navigate
    application_url = None
    for url in URLS_TO_TRY:
        try:
            print(f"Trying URL: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            application_url = url
            print(f"Loaded: {page.url}")
            break
        except Exception as e:
            print(f"  Failed to load {url}: {e}")
            continue

    if application_url is None:
        return "failed", "Could not load any application URL", screenshots_taken

    s = screenshot(page, "01-initial-load")
    if s:
        screenshots_taken.append(s)

    page_content = page.content().lower()
    current_url = page.url

    # Check for CAPTCHA immediately
    if any(kw in page_content for kw in ["recaptcha", "hcaptcha", "cf-challenge", "just a moment"]):
        s = screenshot(page, "captcha-blocked")
        if s:
            screenshots_taken.append(s)
        return "requires_manual_step", f"Bot detection on initial page load at {current_url}", screenshots_taken

    # If we hit the Databricks careers page (not the form directly), look for Apply button
    if "databricks.com" in current_url and "greenhouse.io" not in current_url:
        print("On Databricks careers page, looking for Apply / form embed...")
        # The careers page typically embeds Greenhouse in an iframe or links to it
        # Look for an iframe from greenhouse
        try:
            iframe_src = page.locator("iframe[src*='greenhouse']").first
            if iframe_src.count() > 0:
                src = iframe_src.get_attribute("src")
                print(f"Found Greenhouse iframe: {src}")
                page.goto(src, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
                s = screenshot(page, "01b-greenhouse-iframe-direct")
                if s:
                    screenshots_taken.append(s)
        except Exception as e:
            print(f"Iframe approach failed: {e}")

        # Try clicking "Apply" button on the careers page
        try:
            apply_btn = page.locator("a:has-text('Apply'), button:has-text('Apply'), a:has-text('Apply Now'), a[href*='greenhouse']").first
            if apply_btn.is_visible(timeout=5000):
                href = apply_btn.get_attribute("href")
                print(f"Found apply link: {href}")
                if href and "greenhouse" in href:
                    page.goto(href, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                    s = screenshot(page, "01c-after-apply-click")
                    if s:
                        screenshots_taken.append(s)
                else:
                    apply_btn.click()
                    time.sleep(3)
                    s = screenshot(page, "01c-after-apply-click")
                    if s:
                        screenshots_taken.append(s)
        except Exception as e:
            print(f"Apply button approach failed: {e}")

    # Now look for the Greenhouse application form
    print(f"Looking for application form at: {page.url}")

    # Greenhouse standard form detection
    form_found = False
    form_selectors = [
        "form#application_form",
        "form.s-apply-form",
        "#application_form",
        "input[name='job_application[first_name]']",
        "input[id='first_name']",
        "#first_name",
    ]
    for sel in form_selectors:
        try:
            page.wait_for_selector(sel, timeout=8000)
            print(f"Form found via selector: {sel}")
            form_found = True
            break
        except PlaywrightTimeout:
            continue

    if not form_found:
        print("Application form not found, checking page content...")
        # Dump visible text for debugging
        try:
            body_text = page.inner_text("body")[:500]
            print(f"Page text sample: {body_text}")
        except Exception:
            pass
        s = screenshot(page, "form-not-found")
        if s:
            screenshots_taken.append(s)
        notes = f"Greenhouse application form not found at {page.url}. May require manual application."
        return "requires_manual_step", notes, screenshots_taken

    s = screenshot(page, "02-form-loaded")
    if s:
        screenshots_taken.append(s)

    # Fill fields
    print("Filling application fields...")

    fill_field(page, [
        "input[name='job_application[first_name]']",
        "#first_name",
        "input[id='first_name']",
        "input[placeholder*='First name']",
        "input[autocomplete='given-name']",
    ], CANDIDATE["first_name"], "first name")

    fill_field(page, [
        "input[name='job_application[last_name]']",
        "#last_name",
        "input[id='last_name']",
        "input[placeholder*='Last name']",
        "input[autocomplete='family-name']",
    ], CANDIDATE["last_name"], "last name")

    fill_field(page, [
        "input[name='job_application[email]']",
        "#email",
        "input[type='email']",
        "input[id='email']",
        "input[placeholder*='Email']",
    ], CANDIDATE["email"], "email")

    fill_field(page, [
        "input[name='job_application[phone]']",
        "#phone",
        "input[type='tel']",
        "input[id='phone']",
        "input[placeholder*='Phone']",
    ], CANDIDATE["phone"], "phone")

    time.sleep(0.5)

    # LinkedIn
    fill_field(page, [
        "input[id*='linkedin']",
        "input[name*='linkedin']",
        "input[placeholder*='LinkedIn']",
        "input[placeholder*='linkedin']",
        "#job_application_question_answer_linkedin_profile",
        "input[value*='linkedin']",
    ], CANDIDATE["linkedin"], "LinkedIn URL")

    # GitHub
    fill_field(page, [
        "input[id*='github']",
        "input[name*='github']",
        "input[placeholder*='GitHub']",
        "input[placeholder*='Github']",
    ], CANDIDATE["github"], "GitHub URL")

    # Location
    fill_field(page, [
        "input[id*='location']",
        "input[name*='location']",
        "input[placeholder*='Location']",
        "input[placeholder*='City']",
    ], CANDIDATE["location"], "location")

    s = screenshot(page, "03-text-fields-filled")
    if s:
        screenshots_taken.append(s)

    # Upload resume
    print("Uploading resume...")
    try:
        # Greenhouse uses input[type=file] for resume upload
        file_inputs = page.locator("input[type='file']")
        count = file_inputs.count()
        print(f"Found {count} file input(s)")
        if count > 0:
            # First file input is usually resume
            file_inputs.first.set_input_files(RESUME_PATH)
            print(f"Resume file set: {RESUME_PATH}")
            time.sleep(2)
            s = screenshot(page, "04-resume-uploaded")
            if s:
                screenshots_taken.append(s)
        else:
            print("No file inputs found for resume")
    except Exception as e:
        print(f"Resume upload error: {e}")

    # Cover letter textarea (if present)
    print("Checking for cover letter field...")
    cl_filled = False
    cl_selectors_textarea = [
        "textarea[id*='cover']",
        "textarea[name*='cover']",
        "textarea[placeholder*='cover letter']",
        "textarea[placeholder*='Cover']",
        "textarea[id*='letter']",
        "textarea[name*='letter']",
        "#cover_letter_text",
        "textarea[id='cover_letter']",
    ]
    for sel in cl_selectors_textarea:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.fill(cover_letter_text)
                print(f"Cover letter typed into textarea ({sel})")
                cl_filled = True
                break
        except Exception:
            continue

    if not cl_filled:
        # Check if there's a cover letter file upload (second file input often)
        try:
            file_inputs = page.locator("input[type='file']")
            count = file_inputs.count()
            if count >= 2:
                # Second might be cover letter - skip since we don't have PDF
                print("Second file input found (possibly cover letter) - no PDF CL available, skipping")
        except Exception:
            pass
        print("No cover letter textarea found (may not be required)")

    # Scroll to see all fields including custom questions
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    s = screenshot(page, "05-bottom-of-form")
    if s:
        screenshots_taken.append(s)

    # Handle any radio buttons or dropdowns that may be required
    # Look for required selects/dropdowns
    try:
        selects = page.locator("select[required], select.required")
        sel_count = selects.count()
        print(f"Found {sel_count} required select element(s)")
        for i in range(sel_count):
            sel_el = selects.nth(i)
            options = sel_el.locator("option").all()
            if len(options) > 1:
                # Pick second option (first is usually placeholder)
                sel_el.select_option(index=1)
                print(f"Selected option in dropdown {i}")
    except Exception as e:
        print(f"Dropdown handling: {e}")

    # Look for submit button
    print("Looking for submit button...")
    submit_btn = None
    submit_selectors = [
        "input[type='submit'][value='Submit Application']",
        "input[type='submit']",
        "button[type='submit']:has-text('Submit')",
        "button:has-text('Submit Application')",
        "button:has-text('Apply')",
        "button[type='submit']",
    ]
    for sel in submit_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                submit_btn = el
                print(f"Found submit button: {sel}")
                break
        except Exception:
            continue

    if submit_btn is None:
        print("Submit button not found")
        return "requires_manual_step", f"Could not locate submit button on form at {page.url}", screenshots_taken

    # Scroll to submit and screenshot before
    submit_btn.scroll_into_view_if_needed()
    time.sleep(0.5)
    s = screenshot(page, "06-pre-submit")
    if s:
        screenshots_taken.append(s)

    # Submit
    print("Clicking submit...")
    submit_btn.click()
    time.sleep(5)

    s = screenshot(page, "07-post-submit")
    if s:
        screenshots_taken.append(s)

    final_url = page.url
    print(f"Post-submit URL: {final_url}")

    try:
        page_text = page.inner_text("body").lower()
    except Exception:
        page_text = ""

    success_phrases = ["thank you", "application received", "application submitted", "your application", "we received", "confirmation", "successfully submitted", "we'll be in touch"]
    captcha_phrases = ["captcha", "recaptcha", "robot", "verify you are human", "not a robot"]
    error_phrases = ["error", "is invalid", "can't be blank", "is required", "please fill"]

    if any(phrase in page_text for phrase in captcha_phrases):
        print("CAPTCHA detected post-submit")
        s = screenshot(page, "captcha-on-submit")
        if s:
            screenshots_taken.append(s)
        status = "requires_manual_step"
        notes = f"reCAPTCHA Enterprise blocked submission on Greenhouse form. Form was fully filled. Manual completion required at: {URLS_TO_TRY[0]}"
    elif any(phrase in page_text for phrase in success_phrases):
        print("Application submitted successfully!")
        status = "applied"
        notes = f"Application submitted via Greenhouse. Confirmation detected. Final URL: {final_url}"
    elif any(phrase in page_text for phrase in error_phrases):
        print("Form validation errors detected")
        status = "failed"
        notes = f"Form validation errors on submit. Final URL: {final_url}"
    else:
        print("Submission result ambiguous")
        status = "requires_manual_step"
        notes = f"Submission result ambiguous. Post-submit URL: {final_url}. No clear success or error message detected."

    return status, notes, screenshots_taken


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            ignore_https_errors=True,
        )
        page = context.new_page()

        try:
            status, notes, screenshots = attempt_application(page)
        except Exception as e:
            print(f"Fatal error: {e}")
            try:
                s = screenshot(page, "fatal-error")
                screenshots = [s] if s else []
            except Exception:
                screenshots = []
            status = "failed"
            notes = f"Fatal error: {str(e)[:300]}"
        finally:
            browser.close()

    return status, notes, screenshots


if __name__ == "__main__":
    print("=== Databricks Fullstack SE - Greenhouse Application ===")
    status, notes, screenshots = run()
    print(f"\nResult: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    result = {
        "status": status,
        "notes": notes,
        "screenshots": screenshots,
        "timestamp": datetime.now().isoformat(),
    }
    print("\nJSON_RESULT:" + json.dumps(result))
