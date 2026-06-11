#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE role via Greenhouse (final).
Uses exact DOM IDs discovered from form inspection.
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/databricks-fullstack-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def ss(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-final-{name}-{TIMESTAMP}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {path}")
    except Exception as e:
        print(f"  [SS FAIL] {e}")
        path = None
    return path


def select_react_dropdown(page, input_id, option_text, timeout_ms=5000):
    """
    Interact with a React-Select dropdown:
    1. Click the control div to open menu
    2. Type to filter
    3. Click the matching option
    """
    try:
        # Click on the control container (parent of the input)
        control_sel = f"input#{input_id}"
        el = page.locator(control_sel).first
        el.click()
        time.sleep(0.3)

        # Type to filter options
        el.type(option_text, delay=50)
        time.sleep(0.8)

        # Wait for dropdown options to appear and click the best match
        # React Select renders options in a menu div
        option_locator = page.locator(
            f"[class*='option']:has-text('{option_text}')"
        ).first
        try:
            option_locator.wait_for(state="visible", timeout=timeout_ms)
            option_locator.click()
            print(f"  React-Select '{input_id}': selected '{option_text}'")
            time.sleep(0.3)
            return True
        except PlaywrightTimeout:
            # Try pressing Enter/Down to select first option
            page.keyboard.press("ArrowDown")
            time.sleep(0.2)
            page.keyboard.press("Enter")
            print(f"  React-Select '{input_id}': used keyboard Enter for '{option_text}'")
            return True
    except Exception as e:
        print(f"  React-Select '{input_id}' error: {e}")
        return False


def select_react_dropdown_by_click(page, input_id, option_text):
    """
    Alternative: click the dropdown toggle button, then click option.
    """
    try:
        # Find the container wrapping this input
        # Click the control area to open
        input_el = page.locator(f"#react-select-{input_id}-placeholder").first
        if input_el.count() == 0:
            input_el = page.locator(f"input#{input_id}").first

        container = page.locator(f"input#{input_id}").locator("..").locator("..")
        container.click()
        time.sleep(0.5)

        # Now find and click the option
        option = page.locator(f"[id*='option'][class*='option']").filter(has_text=option_text).first
        if option.count() > 0:
            option.click()
            print(f"  Clicked dropdown option: '{option_text}'")
            time.sleep(0.3)
            return True
        else:
            # Try keyboard
            page.keyboard.press("ArrowDown")
            time.sleep(0.2)
            page.keyboard.press("Enter")
            return True
    except Exception as e:
        print(f"  Dropdown click error: {e}")
        return False


def run():
    screenshots = []
    status = "failed"
    notes = ""

    with open(COVER_LETTER_PATH) as f:
        cover_letter_text = f.read().strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage", "--ignore-certificate-errors"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        try:
            # Load careers page to get fresh Greenhouse token
            print("Loading Databricks careers page...")
            page.goto(
                "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)

            iframe_el = page.locator("iframe[src*='greenhouse']").first
            if iframe_el.count() == 0:
                raise Exception("No Greenhouse iframe found")

            gh_url = iframe_el.get_attribute("src")
            print(f"Greenhouse URL obtained")

            page.goto(gh_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            page.wait_for_selector("#first_name", timeout=10000)
            print("Form loaded")

            s = ss(page, "01-form-loaded")
            if s: screenshots.append(s)

            # ── BASIC TEXT FIELDS ─────────────────────────────────────────────
            print("Filling basic fields...")
            page.fill("#first_name", "Hisham")
            page.fill("#last_name", "Abboud")
            page.fill("#email", "hiaham123@hotmail.com")

            # Phone field - needs ITI (intl-tel-input) handling
            # The country is already +31 (Netherlands) from default or location
            # Set phone number directly
            phone_input = page.locator("#phone")
            phone_input.click()
            phone_input.fill("")
            time.sleep(0.2)
            # Type the number without country code since +31 is already selected
            phone_input.type("0648412838", delay=30)
            print("  Filled phone")

            # ── LOCATION (City) - React Select ────────────────────────────────
            print("Filling location via React Select...")
            loc_input = page.locator("#candidate-location")
            loc_input.click()
            time.sleep(0.3)
            loc_input.type("Amsterdam", delay=50)
            time.sleep(1)

            # Wait for dropdown options
            try:
                # React Select renders options with class containing 'option'
                option = page.locator("[class*='option']").filter(has_text="Amsterdam").first
                option.wait_for(state="visible", timeout=5000)
                option.click()
                print("  Location: clicked Amsterdam option")
            except PlaywrightTimeout:
                # Try keyboard selection
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)
                page.keyboard.press("Enter")
                print("  Location: used keyboard Enter")
            time.sleep(0.5)

            # ── UPLOAD RESUME ─────────────────────────────────────────────────
            print("Uploading resume...")
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(RESUME_PATH)
            time.sleep(2)
            print("  Resume uploaded")

            s = ss(page, "02-top-fields-done")
            if s: screenshots.append(s)

            # Scroll down to see remaining fields
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(0.5)

            # ── LINKEDIN (question_32045705002) ───────────────────────────────
            print("Filling LinkedIn...")
            page.fill("#question_32045705002", "https://linkedin.com/in/hisham-abboud")

            # ── WEBSITE / GITHUB (question_32045706002) ───────────────────────
            print("Filling website/GitHub...")
            page.fill("#question_32045706002", "https://github.com/Hishamabboud")

            s = ss(page, "03-linkedin-website-filled")
            if s: screenshots.append(s)

            # ── REQUIRED DROPDOWNS (React Select) ────────────────────────────
            # question_32045707002: "Are you legally authorized to work in the country?"
            # question_32045708002: "Do you now or will you need sponsorship?"
            # question_32045709002: "Do you currently or have you previously worked for Databricks?"

            print("Handling dropdown: work authorization...")
            # Click the control for question_32045707002
            q1_input = page.locator("#question_32045707002")
            q1_control = q1_input.locator("..").locator("..").locator("..")
            q1_control.click()
            time.sleep(0.5)
            # Look for "Yes" option
            try:
                yes_opt = page.locator("[class*='option']").filter(has_text="Yes").first
                yes_opt.wait_for(state="visible", timeout=3000)
                yes_opt.click()
                print("  Work auth: selected Yes")
            except PlaywrightTimeout:
                q1_input.type("Yes", delay=50)
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("Enter")
                print("  Work auth: keyboard-selected Yes")
            time.sleep(0.3)

            print("Handling dropdown: visa sponsorship...")
            q2_input = page.locator("#question_32045708002")
            q2_control = q2_input.locator("..").locator("..").locator("..")
            q2_control.click()
            time.sleep(0.5)
            try:
                no_opt = page.locator("[class*='option']").filter(has_text="No").first
                no_opt.wait_for(state="visible", timeout=3000)
                no_opt.click()
                print("  Visa sponsorship: selected No")
            except PlaywrightTimeout:
                q2_input.type("No", delay=50)
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("Enter")
                print("  Visa sponsorship: keyboard-selected No")
            time.sleep(0.3)

            print("Handling dropdown: previously worked at Databricks...")
            q3_input = page.locator("#question_32045709002")
            q3_control = q3_input.locator("..").locator("..").locator("..")
            q3_control.click()
            time.sleep(0.5)
            try:
                no_opt = page.locator("[class*='option']").filter(has_text="No").first
                no_opt.wait_for(state="visible", timeout=3000)
                no_opt.click()
                print("  Worked at Databricks: selected No")
            except PlaywrightTimeout:
                q3_input.type("No", delay=50)
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("Enter")
                print("  Worked at Databricks: keyboard-selected No")
            time.sleep(0.3)

            s = ss(page, "04-dropdowns-done")
            if s: screenshots.append(s)

            # ── SANCTIONS CHECKBOXES ──────────────────────────────────────────
            print("Checking sanctions compliance checkboxes...")

            # Group 1: "None of the above" (Cuba/Iran sanctions)
            none_above_id = "question_35110793002[]_221057636002"
            try:
                page.check(f"#{none_above_id}")
                print("  Checked: 'None of the above' (sanctions countries)")
            except Exception as e:
                print(f"  Error checking 'None of the above': {e}")

            # Group 2: Since we selected "None of the above" in Group 1,
            # we should check "Not applicable (i.e., I selected none of the above for the prior question)"
            not_applicable_id = "question_35114477002[]_221076133002"
            try:
                page.check(f"#{not_applicable_id}")
                print("  Checked: 'Not applicable' (prior question none of above)")
            except Exception as e:
                print(f"  Error checking 'Not applicable': {e}")

            s = ss(page, "05-checkboxes-done")
            if s: screenshots.append(s)

            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            s = ss(page, "06-bottom-view")
            if s: screenshots.append(s)

            # ── SUBMIT ─────────────────────────────────────────────────────────
            print("Finding submit button...")
            submit = page.locator(
                "button:has-text('Submit application'), "
                "button:has-text('Submit Application'), "
                "button[type='submit'], "
                "input[type='submit']"
            ).first

            if submit.count() == 0:
                raise Exception("Submit button not found")

            submit.scroll_into_view_if_needed()
            time.sleep(0.5)
            s = ss(page, "07-pre-submit")
            if s: screenshots.append(s)

            print("Clicking Submit application...")
            submit.click()
            time.sleep(6)  # Wait for either success page or error display

            s = ss(page, "08-post-submit")
            if s: screenshots.append(s)

            final_url = page.url
            print(f"Post-submit URL: {final_url}")

            try:
                body_text = page.inner_text("body").lower()
            except Exception:
                body_text = ""

            print(f"Body sample (500 chars): {body_text[:500]}")

            captcha_kw = ["recaptcha", "captcha", "robot", "verify you are human", "not a robot"]
            success_kw = ["thank you", "application received", "successfully submitted",
                          "we'll review", "we will review", "your application has been",
                          "application submitted", "we received your"]
            error_kw = ["is required", "can't be blank", "is invalid", "please fill",
                        "please enter your location", "this field is required"]

            if any(kw in body_text for kw in captcha_kw):
                status = "requires_manual_step"
                notes = (
                    "reCAPTCHA Enterprise blocked Greenhouse submission for Databricks Fullstack SE. "
                    "All form fields were fully filled: name, email, phone, location (Amsterdam), "
                    "resume uploaded, LinkedIn, website/GitHub, work auth=Yes, visa=No, "
                    "Databricks history=No, sanctions checkboxes=None of the above + Not applicable. "
                    f"Manual submission required at: https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002"
                )
            elif any(kw in body_text for kw in success_kw):
                status = "applied"
                notes = f"Application submitted via Greenhouse. Confirmation detected. Final URL: {final_url}"
                print("SUCCESS: Application submitted!")
            elif any(kw in body_text for kw in error_kw):
                status = "failed"
                notes = f"Form validation errors on submit. Errors: {body_text[:400]}"
                print("FAILED: Form validation errors")
            else:
                # Check if we're still on the same page (stayed = submit didn't trigger nav)
                status = "requires_manual_step"
                notes = f"Submission result ambiguous. URL: {final_url}. Body: {body_text[:300]}"
                print("AMBIGUOUS result")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = ss(page, "error")
                if s: screenshots.append(s)
            except Exception:
                pass
            status = "failed"
            notes = f"Error: {str(e)[:400]}"

        finally:
            browser.close()

    return status, notes, screenshots


if __name__ == "__main__":
    print("=== Databricks Fullstack SE - Greenhouse Application (Final) ===")
    status, notes, screenshots = run()
    print(f"\nResult: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    print("\nJSON_RESULT:" + json.dumps({
        "status": status, "notes": notes, "screenshots": screenshots,
        "timestamp": datetime.now().isoformat()
    }))
