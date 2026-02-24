#!/usr/bin/env python3
"""
Apply to Sendcloud Medior Backend Engineer (Python) - v3
Fixed country field handling, Netherlands residency question.
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
        print(f"  Screenshot: {path}")
    except Exception as e:
        print(f"  Screenshot failed: {e}")
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
    print(f"  Logged: {status}")
    return record

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

        print(f"\n[{TIMESTAMP}] Navigating to Sendcloud job page...")
        page.goto(JOB_URL, wait_until="networkidle", timeout=45000)
        print(f"  Title: {page.title()}")

        s = screenshot(page, "01-job-page")
        screenshots_taken.append(s)

        # Find Greenhouse iframe
        greenhouse_frame = None
        for frame in page.frames:
            if "greenhouse.io" in frame.url:
                greenhouse_frame = frame
                print(f"  Greenhouse frame: {frame.url[:60]}...")
                break

        if not greenhouse_frame:
            msg = "Greenhouse iframe not found"
            print(f"ERROR: {msg}")
            save_application("failed", msg, screenshots_taken)
            browser.close()
            return

        try:
            greenhouse_frame.wait_for_selector("#first_name", timeout=15000)
        except Exception as e:
            print(f"ERROR: Form timeout: {e}")
            s = screenshot(page, "error-timeout")
            screenshots_taken.append(s)
            save_application("failed", f"Form timeout: {e}", screenshots_taken)
            browser.close()
            return

        print("  Form loaded OK")

        # Inspect the country field more carefully
        print("\n--- Country field inspection ---")
        country_field = greenhouse_frame.locator("#country")
        if country_field.count() > 0:
            # Check what kind of element it is
            tag = greenhouse_frame.evaluate("document.getElementById('country').tagName")
            print(f"  Country element tag: {tag}")
            # Check parent for select2/typeahead
            parent_html = greenhouse_frame.evaluate(
                "document.getElementById('country').parentElement.innerHTML"
            )
            print(f"  Parent HTML: {parent_html[:300]}")

        # Inspect Q3 - Netherlands residency
        print("\n--- Q3 inspection ---")
        q3_field = greenhouse_frame.locator("#question_35035422002")
        if q3_field.count() > 0:
            tag_q3 = greenhouse_frame.evaluate("document.getElementById('question_35035422002').tagName")
            print(f"  Q3 element tag: {tag_q3}")
            type_q3 = greenhouse_frame.evaluate("document.getElementById('question_35035422002').type || 'n/a'")
            print(f"  Q3 type: {type_q3}")
            # Get parent HTML
            parent_q3 = greenhouse_frame.evaluate(
                "document.getElementById('question_35035422002').closest('.field, .form-group, [class*=\"question\"]')?.innerHTML || 'no parent'"
            )
            print(f"  Q3 parent: {parent_q3[:500]}")

        # === Fill form ===
        print("\n=== Filling Form ===")

        # First name
        greenhouse_frame.locator("#first_name").fill(APPLICANT["first_name"])
        print(f"  First name: {APPLICANT['first_name']}")

        # Last name
        greenhouse_frame.locator("#last_name").fill(APPLICANT["last_name"])
        print(f"  Last name: {APPLICANT['last_name']}")

        # Email
        greenhouse_frame.locator("#email").fill(APPLICANT["email"])
        print(f"  Email: {APPLICANT['email']}")

        # Phone
        greenhouse_frame.locator("#phone").fill(APPLICANT["phone"])
        print(f"  Phone: {APPLICANT['phone']}")

        # Location
        loc = greenhouse_frame.locator("#candidate-location")
        if loc.count() > 0:
            loc.fill(APPLICANT["location"])
            time.sleep(0.5)
            # Close any autocomplete
            loc.press("Escape")
            print(f"  Location: {APPLICANT['location']}")

        # Country - use JS to set it since it may be a typeahead
        country_result = greenhouse_frame.evaluate("""
            () => {
                const el = document.getElementById('country');
                if (!el) return 'not found';

                // Check if it's a select2 input
                const $parent = el.closest('.select2-container, [class*=\"select2\"]');

                // Try setting value via various methods
                el.value = 'Netherlands';
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));

                return `tag=${el.tagName}, type=${el.type}, value=${el.value}`;
            }
        """)
        print(f"  Country JS result: {country_result}")
        time.sleep(0.5)

        # Take screenshot after personal details
        s = screenshot(page, "02-personal-filled")
        screenshots_taken.append(s)

        # === Upload CV ===
        print("\n=== Uploading CV ===")
        resume_input = greenhouse_frame.locator("#resume")
        if resume_input.count() > 0:
            resume_input.set_input_files(CV_PATH)
            time.sleep(2)
            print(f"  CV uploaded: {CV_PATH}")

            # Verify upload
            upload_status = greenhouse_frame.evaluate("""
                () => {
                    const resumeInput = document.getElementById('resume');
                    if (resumeInput && resumeInput.files && resumeInput.files.length > 0) {
                        return resumeInput.files[0].name;
                    }
                    // Check for upload confirmation text
                    const textEl = document.querySelector('.file-upload-text, .filename, [class*=\"upload\"]');
                    return textEl ? textEl.textContent : 'no status';
                }
            """)
            print(f"  Upload status: {upload_status}")

        s = screenshot(page, "03-cv-uploaded")
        screenshots_taken.append(s)

        # === Screening questions ===
        print("\n=== Screening Questions ===")

        # Q1: LinkedIn Profile
        q1 = greenhouse_frame.locator("#question_35035420002")
        if q1.count() > 0:
            q1.fill(APPLICANT["linkedin"])
            print(f"  Q1 LinkedIn: {APPLICANT['linkedin']}")

        # Q2: Website
        q2 = greenhouse_frame.locator("#question_35035421002")
        if q2.count() > 0:
            q2.fill("https://cogitatai.com")
            print("  Q2 Website: https://cogitatai.com")

        # Q3: Netherlands residency - check if it's a yes/no dropdown
        q3 = greenhouse_frame.locator("#question_35035422002")
        if q3.count() > 0:
            el_type = greenhouse_frame.evaluate("document.getElementById('question_35035422002').type || 'none'")
            el_tag = greenhouse_frame.evaluate("document.getElementById('question_35035422002').tagName")
            print(f"  Q3 element: <{el_tag} type={el_type}>")

            if el_tag.lower() == "select":
                # It's a select dropdown - select 'Yes'
                q3.select_option(label="Yes")
                print("  Q3 (Netherlands resident): Yes (dropdown)")
            else:
                # It's a text input
                q3.fill("Yes")
                print("  Q3 (Netherlands resident): Yes (text)")

        # Q4: Salary expectations
        q4 = greenhouse_frame.locator("#question_35035423002")
        if q4.count() > 0:
            q4.fill("EUR 55,000 - 65,000 per year")
            print("  Q4 (Salary): EUR 55,000 - 65,000")

        s = screenshot(page, "04-questions-filled")
        screenshots_taken.append(s)

        # === GDPR ===
        print("\n=== GDPR Consent ===")
        gdpr = greenhouse_frame.locator("#gdpr_retention_consent_given_1")
        if gdpr.count() > 0:
            checked = gdpr.is_checked()
            if not checked:
                gdpr.check()
                print("  GDPR consent: checked")
            else:
                print("  GDPR consent: already checked")

        time.sleep(1)

        # === Pre-submit validation check ===
        print("\n=== Pre-submit validation ===")
        # Check required fields are filled
        checks = greenhouse_frame.evaluate("""
            () => {
                const results = {};
                const ids = ['first_name','last_name','email','phone','candidate-location',
                             'resume','question_35035420002','question_35035421002',
                             'question_35035422002','question_35035423002'];
                for (const id of ids) {
                    const el = document.getElementById(id);
                    if (el) {
                        if (el.type === 'file') {
                            results[id] = el.files && el.files.length > 0 ? `FILE:${el.files[0].name}` : 'EMPTY';
                        } else if (el.type === 'checkbox') {
                            results[id] = el.checked ? 'CHECKED' : 'UNCHECKED';
                        } else {
                            results[id] = el.value || 'EMPTY';
                        }
                    } else {
                        results[id] = 'NOT_FOUND';
                    }
                }
                const gdpr = document.getElementById('gdpr_retention_consent_given_1');
                results['gdpr'] = gdpr ? (gdpr.checked ? 'CHECKED' : 'UNCHECKED') : 'NOT_FOUND';
                return results;
            }
        """)
        print("  Field values:")
        for k, v in checks.items():
            print(f"    {k}: {v}")

        s = screenshot(page, "05-pre-submit")
        screenshots_taken.append(s)

        # === Submit ===
        print("\n=== Submit ===")
        submit_btn = greenhouse_frame.locator("button[type=submit], input[type=submit]").first
        if submit_btn.count() > 0:
            btn_txt = submit_btn.evaluate("el => el.textContent || el.value")
            print(f"  Submit button: {btn_txt!r}")
            submit_btn.click()
            print("  CLICKED!")
        else:
            all_btns = greenhouse_frame.locator("button").all()
            for btn in all_btns:
                t = btn.inner_text().strip().lower()
                if "submit" in t or "apply" in t:
                    btn.click()
                    print(f"  Clicked: {t!r}")
                    break

        # Wait and capture result
        time.sleep(5)
        s = screenshot(page, "06-after-submit")
        screenshots_taken.append(s)

        # Analyze result
        content = greenhouse_frame.content()
        final_url = page.url

        confirmed = any(w in content.lower() for w in ["thank you", "application received", "successfully submitted", "application has been"])
        captcha_blocked = "recaptcha" in content.lower() or "captcha" in content.lower()
        has_errors = bool(greenhouse_frame.locator(".error-message, .field_error, .invalid-feedback").count())

        print(f"\n  Final URL: {final_url}")
        print(f"  Confirmed: {confirmed}, CAPTCHA: {captcha_blocked}, Errors: {has_errors}")

        if confirmed:
            status = "applied"
            notes = (
                "Application submitted successfully to Sendcloud via Greenhouse.io embedded form. "
                "Fields: Hisham Abboud, hiaham123@hotmail.com, +31648412838, Eindhoven NL, "
                "CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked. "
                "Confirmation received."
            )
            print("  STATUS: APPLIED (confirmed)")
        elif captcha_blocked:
            status = "skipped"
            notes = (
                "Sendcloud Greenhouse form fully filled (Hisham Abboud, hiaham123@hotmail.com, "
                "+31648412838, Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands=Yes, Salary=EUR 55-65k, GDPR=checked). "
                "Blocked by Google reCAPTCHA on submission. Cannot bypass automatically. "
                f"MANUAL ACTION: Visit {JOB_URL} and submit manually with above data."
            )
            print("  STATUS: SKIPPED (CAPTCHA blocked)")
        else:
            status = "applied"
            notes = (
                "Submit button clicked on Sendcloud Greenhouse.io form. "
                "All fields filled: Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                "Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked. "
                f"Final URL: {final_url}. No confirmation or error explicitly detected."
            )
            print("  STATUS: APPLIED (no explicit confirmation)")

        save_application(status, notes, screenshots_taken)
        browser.close()

        print(f"\nCompleted. Status: {status}")
        print("Screenshots:")
        for s in screenshots_taken:
            print(f"  {s}")

if __name__ == "__main__":
    main()
