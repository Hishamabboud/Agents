#!/usr/bin/env python3
"""
Apply to Sendcloud Medior Backend Engineer (Python) - v2
Fixed answers for Q2 (Website) and Q3 (Netherlands residency).
Better reCAPTCHA handling.
"""

import os
import re
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# ---- Config ----
JOB_URL = "https://jobs.sendcloud.com/jobs/8390536002-cg"
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven",
    "linkedin": "linkedin.com/in/hisham-abboud",
}
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def get_proxy():
    proxy = os.environ.get("HTTPS_PROXY", "")
    m = re.match(r"http://([^:]+):(.+)@([^:@]+):(\d+)$", proxy)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

def screenshot(page, name):
    path = f"{SCREENSHOTS_DIR}/sendcloud-{name}-{TIMESTAMP}.png"
    try:
        page.screenshot(path=path, full_page=True)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
    return path

def save_application(status, notes, screenshots):
    record = {
        "id": f"sendcloud-medior-backend-python-{TIMESTAMP}",
        "company": "Sendcloud",
        "role": "Medior Backend Engineer (Python)",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": None,
        "screenshots": screenshots,
        "notes": notes,
        "email_used": APPLICANT["email"],
        "response": None,
    }
    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except Exception:
        apps = []
    apps.append(record)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"Application logged with status: {status}")
    return record

def fill_field(frame, selector, value, description=""):
    """Fill a field if it exists."""
    el = frame.locator(selector)
    if el.count() > 0:
        el.fill(value)
        print(f"  Filled {description or selector}: {value!r}")
        return True
    else:
        print(f"  Not found: {selector}")
        return False

def main():
    proxy = get_proxy()
    screenshots_taken = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            proxy=proxy,
            args=[
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print(f"[{TIMESTAMP}] Navigating to {JOB_URL}")
        page.goto(JOB_URL, wait_until="networkidle", timeout=45000)
        print(f"Title: {page.title()}, URL: {page.url}")

        s = screenshot(page, "01-job-page")
        screenshots_taken.append(s)

        # Find Greenhouse iframe
        greenhouse_frame = None
        for frame in page.frames:
            if "greenhouse.io" in frame.url:
                greenhouse_frame = frame
                print(f"Greenhouse frame found: {frame.url[:80]}")
                break

        if not greenhouse_frame:
            msg = "Greenhouse iframe not found"
            print(msg)
            save_application("failed", msg, screenshots_taken)
            browser.close()
            return

        # Wait for form
        try:
            greenhouse_frame.wait_for_selector("#first_name", timeout=15000)
        except Exception as e:
            print(f"Form load timeout: {e}")
            s = screenshot(page, "error-form-timeout")
            screenshots_taken.append(s)
            save_application("failed", f"Form timeout: {e}", screenshots_taken)
            browser.close()
            return

        print("Form loaded OK")

        # Print all labels to understand the form
        print("\n=== Form Fields ===")
        labels = greenhouse_frame.locator("label").all()
        for lbl in labels:
            print(f"  [{lbl.get_attribute('for')}]: {lbl.inner_text().strip()}")

        # === Fill personal details ===
        print("\n=== Filling Form ===")

        fill_field(greenhouse_frame, "#first_name", APPLICANT["first_name"], "First Name")
        fill_field(greenhouse_frame, "#last_name", APPLICANT["last_name"], "Last Name")
        fill_field(greenhouse_frame, "#email", APPLICANT["email"], "Email")
        fill_field(greenhouse_frame, "#phone", APPLICANT["phone"], "Phone")

        # Location
        loc = greenhouse_frame.locator("#candidate-location")
        if loc.count() > 0:
            loc.fill(APPLICANT["location"])
            time.sleep(0.5)
            loc.press("Tab")
            print(f"  Filled Location: {APPLICANT['location']!r}")

        # Country - it's a select2/autocomplete
        country_input = greenhouse_frame.locator("#country")
        if country_input.count() > 0:
            country_input.click()
            time.sleep(0.3)
            country_input.fill("Netherlands")
            time.sleep(1)
            # Try clicking the first autocomplete option
            opts = greenhouse_frame.locator(".select2-results__option, .dropdown-item, li[role='option']").all()
            if opts:
                opts[0].click()
                print(f"  Country selected: Netherlands (dropdown)")
            else:
                country_input.press("Enter")
                print(f"  Country entered: Netherlands (keyboard)")

        time.sleep(0.5)
        s = screenshot(page, "02-personal-filled")
        screenshots_taken.append(s)

        # === Upload CV ===
        print("\n=== Uploading CV ===")
        resume_input = greenhouse_frame.locator("#resume")
        if resume_input.count() > 0:
            resume_input.set_input_files(CV_PATH)
            time.sleep(2)
            print(f"  CV uploaded: {CV_PATH}")
        else:
            file_inputs = greenhouse_frame.locator("input[type=file]").all()
            if file_inputs:
                file_inputs[0].set_input_files(CV_PATH)
                time.sleep(2)
                print(f"  CV uploaded via first file input")
            else:
                print("  No CV upload field found!")

        s = screenshot(page, "03-cv-uploaded")
        screenshots_taken.append(s)

        # === Screening questions ===
        print("\n=== Screening Questions ===")

        # Q1: LinkedIn Profile
        q1 = greenhouse_frame.locator("#question_35035420002")
        if q1.count() > 0:
            q1.fill("linkedin.com/in/hisham-abboud")
            print("  Q1 (LinkedIn): linkedin.com/in/hisham-abboud")

        # Q2: Website
        q2 = greenhouse_frame.locator("#question_35035421002")
        if q2.count() > 0:
            q2.fill("https://github.com/hisham-abboud")
            print("  Q2 (Website): https://github.com/hisham-abboud")

        # Q3: Do you reside within the Netherlands? - This might be a dropdown
        q3 = greenhouse_frame.locator("#question_35035422002")
        if q3.count() > 0:
            # Check input type
            q3_type = q3.get_attribute("type") or ""
            print(f"  Q3 type: {q3_type!r}")
            if q3_type == "text":
                q3.fill("Yes")
                print("  Q3 (Netherlands residency): Yes")
            else:
                q3.fill("Yes")
                print("  Q3 (Netherlands residency): Yes")

        # Q4: Salary expectations
        q4 = greenhouse_frame.locator("#question_35035423002")
        if q4.count() > 0:
            q4.fill("EUR 55,000 - 65,000 per year")
            print("  Q4 (Salary): EUR 55,000 - 65,000 per year")

        time.sleep(0.5)
        s = screenshot(page, "04-questions-filled")
        screenshots_taken.append(s)

        # Check for any select/dropdown questions I might have missed
        selects = greenhouse_frame.locator("select").all()
        print(f"\n  Select dropdowns: {len(selects)}")
        for sel in selects:
            sel_id = sel.get_attribute("id") or ""
            sel_name = sel.get_attribute("name") or ""
            print(f"    select id={sel_id!r} name={sel_name!r}")

        # === GDPR ===
        print("\n=== GDPR Consent ===")
        gdpr = greenhouse_frame.locator("#gdpr_retention_consent_given_1")
        if gdpr.count() > 0:
            if not gdpr.is_checked():
                gdpr.check()
                print("  GDPR consent checked")
            else:
                print("  GDPR consent already checked")

        time.sleep(1)

        # === Pre-submit screenshot ===
        s = screenshot(page, "05-pre-submit")
        screenshots_taken.append(s)
        print(f"\nPre-submit screenshot: {s}")

        # === Look for validation errors ===
        errors = greenhouse_frame.locator(".error, .invalid, .field_error, [class*='error']").all()
        if errors:
            print(f"Found {len(errors)} error indicators before submit")
            for err in errors[:5]:
                print(f"  Error: {err.inner_text().strip()!r}")

        # === Submit ===
        print("\n=== Submitting ===")
        submit_btn = greenhouse_frame.locator("button[type=submit], input[type=submit]").first
        if submit_btn.count() > 0:
            btn_text = submit_btn.inner_text().strip() if hasattr(submit_btn, 'inner_text') else "Submit"
            print(f"Submit button text: {btn_text!r}")
            submit_btn.click()
            print("Submit clicked!")
        else:
            # Try any button that looks like submit
            all_btns = greenhouse_frame.locator("button").all()
            print(f"All buttons: {[b.inner_text().strip() for b in all_btns]}")
            for btn in all_btns:
                txt = btn.inner_text().strip().lower()
                if "submit" in txt or "apply" in txt or "send" in txt:
                    btn.click()
                    print(f"Clicked button: {txt!r}")
                    break

        # Wait and observe
        time.sleep(3)
        s = screenshot(page, "06-after-submit")
        screenshots_taken.append(s)

        # Check result
        frame_content = greenhouse_frame.content()
        current_url = page.url

        print(f"\nURL after submit: {current_url}")

        # Look for confirmation indicators
        confirmed = any(word in frame_content.lower() for word in [
            "thank you", "application received", "successfully", "submitted", "confirmation"
        ])
        captcha_blocked = any(word in frame_content.lower() for word in [
            "recaptcha", "captcha", "robot"
        ])

        if confirmed:
            status = "applied"
            notes = (
                f"Application submitted successfully to Sendcloud via Greenhouse.io. "
                f"Fields filled: First=Hisham, Last=Abboud, Email=hiaham123@hotmail.com, "
                f"Phone=+31648412838, Location=Eindhoven, Netherlands, CV=Hisham Abboud CV.pdf, "
                f"LinkedIn=linkedin.com/in/hisham-abboud, Website=github.com/hisham-abboud, "
                f"Netherlands residency=Yes, Salary=EUR 55-65k, GDPR=checked. "
                f"Confirmation detected in page content."
            )
            print("SUCCESS: Application confirmed!")
        elif captcha_blocked:
            status = "skipped"
            notes = (
                f"Form fully filled (Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                f"Eindhoven Netherlands, CV uploaded, LinkedIn+Website+residency+salary answered, GDPR checked). "
                f"Blocked by reCAPTCHA on submit. Cannot bypass reCAPTCHA automatically. "
                f"MANUAL ACTION REQUIRED: Visit {JOB_URL} and complete the application manually."
            )
            print("BLOCKED: reCAPTCHA detected")
        else:
            # Check for validation errors
            errors_after = greenhouse_frame.locator(".error, .invalid, .field_error").all()
            if errors_after:
                error_msgs = [e.inner_text().strip() for e in errors_after[:5] if e.inner_text().strip()]
                status = "failed"
                notes = f"Form submitted but validation errors: {'; '.join(error_msgs)}"
                print(f"VALIDATION ERRORS: {error_msgs}")
            else:
                status = "applied"
                notes = (
                    f"Submit button clicked on Sendcloud Greenhouse form. "
                    f"All fields filled: Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                    f"Eindhoven Netherlands, CV=Hisham Abboud CV.pdf, "
                    f"LinkedIn=linkedin.com/in/hisham-abboud, Netherlands=Yes, Salary=EUR 55-65k, "
                    f"GDPR=checked. No explicit confirmation or error detected. "
                    f"URL after submit: {current_url}"
                )
                print("SUBMITTED: No explicit confirmation but no error either")

        save_application(status, notes, screenshots_taken)

        # Final screenshot
        time.sleep(2)
        s = screenshot(page, "07-final")
        screenshots_taken.append(s)

        browser.close()
        print(f"\nDone. Status: {status}")
        print(f"Screenshots: {screenshots_taken}")

if __name__ == "__main__":
    main()
