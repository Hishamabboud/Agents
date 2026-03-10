#!/usr/bin/env python3
"""
Apply to ClickHouse - Cloud Software Engineer, Identity and Access Management
Job URL: https://job-boards.greenhouse.io/clickhouse/jobs/5803692004
"""

import os
import json
import time
from datetime import date
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

JOB_URL = "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/clickhouse-cloud-engineer.md"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven, Netherlands",
}

with open(COVER_LETTER_PATH, "r") as f:
    COVER_LETTER_TEXT = f.read()


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"clickhouse-{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")
    return path


def try_fill(page, selectors, value, label="field"):
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.count() > 0:
                el.fill(value)
                print(f"Filled {label}: {value[:50]}")
                return True
        except Exception:
            continue
    print(f"WARNING: Could not find {label}")
    return False


def log_all_inputs(page):
    """Log all form inputs for debugging."""
    print("\n--- Form elements found ---")
    elements = page.locator("input, select, textarea").all()
    for el in elements:
        try:
            tag = el.evaluate("e => e.tagName")
            type_ = el.get_attribute("type") or ""
            name = el.get_attribute("name") or ""
            id_ = el.get_attribute("id") or ""
            placeholder = el.get_attribute("placeholder") or ""
            label_for = ""
            # Try to find associated label
            if id_:
                try:
                    label_el = page.locator(f"label[for='{id_}']")
                    if label_el.count() > 0:
                        label_for = label_el.text_content() or ""
                except Exception:
                    pass
            print(f"  {tag} type={type_} name={name} id={id_} placeholder={placeholder} label={label_for.strip()}")
        except Exception as e:
            print(f"  (could not read element: {e})")
    print("--- End form elements ---\n")


def run():
    result = {
        "status": "failed",
        "screenshots": [],
        "notes": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Navigating to: {JOB_URL}")
            page.goto(JOB_URL, wait_until="networkidle", timeout=60000)
            result["screenshots"].append(screenshot(page, "01-job-page-loaded"))
            print(f"Page title: {page.title()}")
            print(f"URL: {page.url()}")

            # Wait for form
            try:
                page.wait_for_selector("form", timeout=20000)
                print("Form found on page")
            except PlaywrightTimeout:
                print("No form found within timeout")
                result["notes"] = "No form found on page"
                result["screenshots"].append(screenshot(page, "error-no-form"))
                return result

            result["screenshots"].append(screenshot(page, "02-form-visible"))

            # Log all inputs
            log_all_inputs(page)

            # --- Fill basic fields ---
            try_fill(page,
                ["input#first_name", "input[name='job_application[first_name]']", "input[autocomplete='given-name']"],
                CANDIDATE["first_name"], "first name")

            try_fill(page,
                ["input#last_name", "input[name='job_application[last_name]']", "input[autocomplete='family-name']"],
                CANDIDATE["last_name"], "last name")

            try_fill(page,
                ["input#email", "input[name='job_application[email]']", "input[type='email']"],
                CANDIDATE["email"], "email")

            try_fill(page,
                ["input#phone", "input[name='job_application[phone]']", "input[type='tel']"],
                CANDIDATE["phone"], "phone")

            result["screenshots"].append(screenshot(page, "03-basic-fields-filled"))

            # --- Upload Resume ---
            if os.path.exists(RESUME_PDF):
                file_inputs = page.locator("input[type='file']").all()
                if file_inputs:
                    file_inputs[0].set_input_files(RESUME_PDF)
                    print(f"Resume uploaded: {RESUME_PDF}")
                    page.wait_for_timeout(3000)
                    result["screenshots"].append(screenshot(page, "04-resume-uploaded"))
                else:
                    print("WARNING: No file input found for resume upload")
            else:
                print(f"WARNING: Resume PDF not found: {RESUME_PDF}")

            # --- LinkedIn ---
            try_fill(page,
                ["input#job_application_answers_attributes_0_text_value",
                 "input[id*='linkedin']", "input[name*='linkedin']",
                 "input[placeholder*='LinkedIn']", "input[placeholder*='linkedin']"],
                CANDIDATE["linkedin"], "LinkedIn URL")

            # --- Cover Letter (text area) ---
            cover_letter_selectors = [
                "textarea#cover_letter",
                "textarea[name*='cover_letter']",
                "textarea[id*='cover']",
            ]
            filled_cover = False
            for sel in cover_letter_selectors:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        el.fill(COVER_LETTER_TEXT)
                        print("Filled cover letter text area")
                        filled_cover = True
                        break
                except Exception:
                    continue
            if not filled_cover:
                print("Cover letter text area not found (may be file upload only)")

            # --- Handle custom questions ---
            # Look for any text inputs/textareas not yet filled
            textareas = page.locator("textarea").all()
            for ta in textareas:
                try:
                    ta_id = ta.get_attribute("id") or ""
                    ta_name = ta.get_attribute("name") or ""
                    current_val = ta.evaluate("e => e.value")
                    if current_val:
                        continue  # already filled
                    # Find label
                    label_text = ""
                    if ta_id:
                        label_el = page.locator(f"label[for='{ta_id}']")
                        if label_el.count() > 0:
                            label_text = label_el.text_content() or ""
                    print(f"Found unfilled textarea: id={ta_id} name={ta_name} label='{label_text.strip()}'")
                    # Fill with relevant content based on label
                    label_lower = label_text.lower()
                    if "cover" in label_lower or "letter" in label_lower:
                        ta.fill(COVER_LETTER_TEXT)
                        print("  -> Filled as cover letter")
                    elif "auth" in label_lower or "iam" in label_lower or "experience" in label_lower:
                        ta.fill("I have experience with OAuth2/OIDC authentication flows, integrating third-party identity providers, and building secure REST APIs with access control patterns in .NET and Python. I am eager to deepen this expertise in SAML, SCIM, and cloud IAM standards.")
                        print("  -> Filled as auth experience")
                except Exception as e:
                    print(f"  (error processing textarea: {e})")

            # --- Handle visa/work authorization selects ---
            selects = page.locator("select").all()
            for sel in selects:
                try:
                    sel_id = sel.get_attribute("id") or ""
                    sel_name = sel.get_attribute("name") or ""
                    label_text = ""
                    if sel_id:
                        label_el = page.locator(f"label[for='{sel_id}']")
                        if label_el.count() > 0:
                            label_text = label_el.text_content() or ""
                    print(f"Select found: id={sel_id} name={sel_name} label='{label_text.strip()}'")
                    label_lower = label_text.lower()
                    id_lower = (sel_id + " " + sel_name).lower()
                    if "visa" in label_lower or "sponsor" in label_lower or "visa" in id_lower or "sponsor" in id_lower:
                        # Candidate is in Netherlands and does not need sponsorship
                        try:
                            sel.select_option(label="No")
                            print(f"  -> Selected 'No' for visa sponsorship")
                        except Exception:
                            try:
                                sel.select_option(value="0")
                                print(f"  -> Selected value 0 for visa sponsorship")
                            except Exception as e2:
                                print(f"  -> Could not set visa select: {e2}")
                    elif "gender" in label_lower or "race" in label_lower or "veteran" in label_lower or "disability" in label_lower:
                        # EEOC - select "Decline to identify" or "I don't wish to answer"
                        options = sel.locator("option").all()
                        option_texts = []
                        for opt in options:
                            option_texts.append(opt.text_content() or "")
                        print(f"  EEOC options: {option_texts}")
                        # Try to find decline option
                        decline_keywords = ["decline", "prefer not", "don't wish", "not answer", "no answer"]
                        for opt_text in option_texts:
                            if any(kw in opt_text.lower() for kw in decline_keywords):
                                try:
                                    sel.select_option(label=opt_text)
                                    print(f"  -> Selected EEOC decline option: {opt_text}")
                                except Exception:
                                    pass
                                break
                except Exception as e:
                    print(f"  (error processing select: {e})")

            result["screenshots"].append(screenshot(page, "05-all-fields-filled"))

            # --- Final check before submit ---
            log_all_inputs(page)
            result["screenshots"].append(screenshot(page, "06-before-submit"))

            # --- Submit ---
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Submit Application')",
                "button:has-text('Submit')",
                "button:has-text('Apply Now')",
                "button:has-text('Apply')",
            ]

            submit_btn = None
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        submit_btn = btn
                        btn_text = btn.text_content() or btn.get_attribute("value") or "Submit"
                        print(f"Found submit button: '{btn_text}'")
                        break
                except Exception:
                    continue

            if submit_btn:
                print("Submitting application...")
                submit_btn.click()
                page.wait_for_timeout(6000)
                result["screenshots"].append(screenshot(page, "07-after-submit"))

                final_url = page.url()
                final_content = page.content().lower()
                print(f"Final URL: {final_url}")

                success_signals = [
                    "thank you" in final_content,
                    "application received" in final_content,
                    "successfully submitted" in final_content,
                    "we've received" in final_content,
                    "confirmation" in final_url,
                    "success" in final_url,
                    "thank" in final_url,
                ]

                if any(success_signals):
                    print("SUCCESS: Application submitted!")
                    result["status"] = "applied"
                    result["notes"] = "Application submitted successfully via Greenhouse form"
                else:
                    # Check for validation errors
                    errors = page.locator(".error, .alert, [class*='error'], [class*='invalid']").all()
                    error_texts = []
                    for err in errors[:5]:
                        try:
                            t = err.text_content()
                            if t and t.strip():
                                error_texts.append(t.strip())
                        except Exception:
                            pass
                    if error_texts:
                        print(f"VALIDATION ERRORS: {error_texts}")
                        result["notes"] = f"Validation errors: {'; '.join(error_texts)}"
                    else:
                        print("UNCERTAIN: Could not confirm submission. Check screenshots.")
                        result["notes"] = "Submitted but could not confirm success from page content"
                        result["status"] = "applied"  # Assume submitted if no errors

                result["screenshots"].append(screenshot(page, "08-final-state"))
            else:
                print("ERROR: Submit button not found!")
                result["notes"] = "Submit button not found"
                result["screenshots"].append(screenshot(page, "error-no-submit"))

        except PlaywrightTimeout as e:
            print(f"TIMEOUT: {e}")
            result["notes"] = f"Timeout: {e}"
            try:
                result["screenshots"].append(screenshot(page, "error-timeout"))
            except Exception:
                pass
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            result["notes"] = f"Error: {e}"
            try:
                result["screenshots"].append(screenshot(page, "error-exception"))
            except Exception:
                pass
        finally:
            browser.close()

    return result


def update_applications(result):
    """Update the applications.json tracker."""
    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    new_entry = {
        "id": "app-clickhouse-cloud-iam-001",
        "company": "ClickHouse",
        "role": "Cloud Software Engineer - Identity and Access Management",
        "url": JOB_URL,
        "date_applied": str(date.today()),
        "score": 8.0,
        "status": result["status"],
        "resume_file": RESUME_PDF,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshot": result["screenshots"][-1] if result["screenshots"] else "",
        "all_screenshots": result["screenshots"],
        "notes": result["notes"],
        "response": "",
    }

    apps.append(new_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\nApplication logged to {APPLICATIONS_JSON}")
    print(f"Status: {result['status']}")
    return new_entry


if __name__ == "__main__":
    print("=" * 60)
    print("ClickHouse - Cloud Software Engineer IAM Application")
    print("=" * 60)
    result = run()
    entry = update_applications(result)
    print("\n--- SUMMARY ---")
    print(json.dumps(entry, indent=2))
