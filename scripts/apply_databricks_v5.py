#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE via Greenhouse (v5).
Fixes: Country React Select + checkbox IDs with [] chars.
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
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-v5-{name}-{TIMESTAMP}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {path}")
    except Exception as e:
        print(f"  [SS FAIL] {e}")
        path = None
    return path


def react_select(page, input_id, option_text):
    """Click a React-Select control and pick an option by text."""
    try:
        inp = page.locator(f"#{input_id}")
        # Click the parent control div to open the menu
        control = inp.locator("xpath=../../../..")  # up to .select-shell
        control.click()
        time.sleep(0.4)

        # Wait for options list
        opt = page.locator("[class*='option']").filter(has_text=option_text).first
        try:
            opt.wait_for(state="visible", timeout=3000)
            opt.click()
            print(f"  ReactSelect #{input_id}: '{option_text}'")
            time.sleep(0.3)
            return True
        except PlaywrightTimeout:
            # Fallback: type and Enter
            inp.type(option_text, delay=40)
            time.sleep(0.5)
            page.keyboard.press("ArrowDown")
            time.sleep(0.2)
            page.keyboard.press("Enter")
            print(f"  ReactSelect #{input_id}: keyboard '{option_text}'")
            return True
    except Exception as e:
        print(f"  ReactSelect error #{input_id}: {e}")
        return False


def check_by_value(page, name_attr, value):
    """Check a checkbox by name + value using JS (bypasses [] CSS issue)."""
    result = page.evaluate(f"""
    () => {{
        const cb = document.querySelector('input[type="checkbox"][name="{name_attr}"][value="{value}"]');
        if (cb) {{
            cb.checked = true;
            cb.dispatchEvent(new Event('change', {{bubbles: true}}));
            cb.dispatchEvent(new Event('input', {{bubbles: true}}));
            cb.click();
            return 'checked';
        }}
        return 'not_found';
    }}
    """)
    print(f"  Checkbox name={name_attr} value={value}: {result}")
    return result == "checked"


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
            # Get fresh Greenhouse token via careers page
            print("Loading careers page...")
            page.goto(
                "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)

            iframe_el = page.locator("iframe[src*='greenhouse']").first
            gh_url = iframe_el.get_attribute("src")
            print("Got Greenhouse URL")

            page.goto(gh_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            page.wait_for_selector("#first_name", timeout=10000)
            print("Form loaded")
            s = ss(page, "01-form-loaded")
            if s: screenshots.append(s)

            # ── BASIC TEXT FIELDS ─────────────────────────────────────────────
            page.fill("#first_name", "Hisham")
            page.fill("#last_name", "Abboud")
            page.fill("#email", "hiaham123@hotmail.com")
            print("Basic fields filled")

            # ── COUNTRY dropdown (React Select, id=country) ───────────────────
            print("Setting country to Netherlands...")
            country_input = page.locator("#country")
            country_input.click()
            time.sleep(0.4)
            country_input.type("Netherlands", delay=40)
            time.sleep(0.8)
            try:
                nl_opt = page.locator("[class*='option']").filter(has_text="Netherlands").first
                nl_opt.wait_for(state="visible", timeout=4000)
                nl_opt.click()
                print("  Country: Netherlands selected")
            except PlaywrightTimeout:
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("Enter")
                print("  Country: keyboard Enter")
            time.sleep(0.5)

            # ── PHONE ─────────────────────────────────────────────────────────
            phone_input = page.locator("#phone")
            phone_input.click()
            time.sleep(0.2)
            # Clear existing value and type Dutch mobile number
            phone_input.fill("")
            phone_input.type("0648412838", delay=30)
            print("Phone filled: 0648412838")

            # ── LOCATION (React Select id=candidate-location) ─────────────────
            print("Setting location: Amsterdam...")
            loc_input = page.locator("#candidate-location")
            loc_input.click()
            time.sleep(0.3)
            loc_input.type("Amsterdam", delay=50)
            time.sleep(1)
            try:
                am_opt = page.locator("[class*='option']").filter(has_text="Amsterdam").first
                am_opt.wait_for(state="visible", timeout=4000)
                am_opt.click()
                print("  Location: Amsterdam selected")
            except PlaywrightTimeout:
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)
                page.keyboard.press("Enter")
                print("  Location: keyboard Enter")
            time.sleep(0.5)

            # ── RESUME UPLOAD ─────────────────────────────────────────────────
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(RESUME_PATH)
            time.sleep(2)
            print("Resume uploaded")

            s = ss(page, "02-top-fields-done")
            if s: screenshots.append(s)

            # Scroll to see bottom fields
            page.evaluate("window.scrollTo(0, 600)")
            time.sleep(0.5)

            # ── LINKEDIN & WEBSITE ────────────────────────────────────────────
            page.fill("#question_32045705002", "https://linkedin.com/in/hisham-abboud")
            page.fill("#question_32045706002", "https://github.com/Hishamabboud")
            print("LinkedIn and GitHub filled")

            s = ss(page, "03-linkedin-github-filled")
            if s: screenshots.append(s)

            # ── WORK AUTH / VISA / DATABRICKS DROPDOWNS ──────────────────────
            print("Work authorization dropdown...")
            react_select(page, "question_32045707002", "Yes")

            print("Visa sponsorship dropdown...")
            react_select(page, "question_32045708002", "No")

            print("Worked at Databricks dropdown...")
            react_select(page, "question_32045709002", "No")

            s = ss(page, "04-dropdowns-done")
            if s: screenshots.append(s)

            # ── SANCTIONS CHECKBOXES (use JS, not CSS selector) ───────────────
            print("Checking sanctions compliance checkboxes...")

            # Group 1: "None of the above" (value 221057636002)
            check_by_value(page, "question_35110793002[]", "221057636002")

            # Group 2: Since we selected "None of the above" in group 1,
            # we should select "Not applicable (i.e., I selected none of the above...)"
            # value 221076133002
            check_by_value(page, "question_35114477002[]", "221076133002")

            time.sleep(0.5)
            s = ss(page, "05-checkboxes-done")
            if s: screenshots.append(s)

            # Verify checkbox states
            cb_state = page.evaluate("""
            () => {
                const checked = [];
                document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
                    checked.push({name: cb.name, value: cb.value});
                });
                return checked;
            }
            """)
            print(f"Checked checkboxes: {cb_state}")

            # ── FINAL SCROLL & PRE-SUBMIT SCREENSHOT ─────────────────────────
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            s = ss(page, "06-full-form-final")
            if s: screenshots.append(s)

            # Find submit
            submit = page.locator(
                "button:has-text('Submit application'), "
                "button:has-text('Submit Application'), "
                "button[type='submit']"
            ).first
            submit.scroll_into_view_if_needed()
            time.sleep(0.5)
            s = ss(page, "07-pre-submit")
            if s: screenshots.append(s)

            print("Submitting...")
            submit.click()
            time.sleep(6)

            s = ss(page, "08-post-submit")
            if s: screenshots.append(s)

            final_url = page.url
            print(f"Post-submit URL: {final_url}")

            try:
                body_text = page.inner_text("body").lower()
            except Exception:
                body_text = ""

            print(f"Body (500): {body_text[:500]}")

            captcha_kw = ["recaptcha", "captcha", "robot", "verify you are human"]
            success_kw = ["thank you", "application received", "successfully submitted",
                          "we'll review", "we will review", "your application has been",
                          "application submitted", "we received your"]
            error_kw = ["is required", "can't be blank", "please enter your location",
                        "this field is required", "select a country"]

            if any(kw in body_text for kw in captcha_kw):
                status = "requires_manual_step"
                notes = (
                    "reCAPTCHA Enterprise blocked Greenhouse form submission for Databricks Fullstack SE. "
                    "All fields were fully filled: First=Hisham, Last=Abboud, Email=hiaham123@hotmail.com, "
                    "Country=Netherlands, Phone=0648412838, Location=Amsterdam, Resume=Hisham Abboud CV.pdf, "
                    "LinkedIn=https://linkedin.com/in/hisham-abboud, Website=https://github.com/Hishamabboud, "
                    "Work auth=Yes, Visa=No, Databricks history=No, Sanctions=None of above+Not applicable. "
                    "Manual submission required at: https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002"
                )
            elif any(kw in body_text for kw in success_kw):
                status = "applied"
                notes = f"Application submitted via Greenhouse. Confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif any(kw in body_text for kw in error_kw):
                status = "failed"
                notes = f"Form validation errors: {body_text[:400]}"
                print("Form errors remain")
            else:
                status = "requires_manual_step"
                notes = f"Ambiguous result. URL: {final_url}. Body: {body_text[:300]}"

        except Exception as e:
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
    print("=== Databricks Fullstack SE - Greenhouse v5 ===")
    status, notes, screenshots = run()
    print(f"\nResult: {status}")
    print(f"Notes: {notes[:500]}")
    print(f"Screenshots ({len(screenshots)}): {screenshots}")
    print("\nJSON_RESULT:" + json.dumps({
        "status": status, "notes": notes, "screenshots": screenshots,
        "timestamp": datetime.now().isoformat()
    }))
