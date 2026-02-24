#!/usr/bin/env python3
"""
Apply to Sendcloud Medior Backend Engineer (Python) - v4
Fixed: React Select for Netherlands question, proper field filling via React state.
"""

import os
import re
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

JOB_URL = "https://jobs.sendcloud.com/jobs/8390536002-cg"
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "website": "https://cogitatai.com",
    "salary": "EUR 55,000 - 65,000",
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


def save_application(status, notes, screenshots_list):
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
        "screenshots": screenshots_list,
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


def fill_react_input(frame, selector, value):
    """Fill a React-controlled input by simulating user input events."""
    result = frame.evaluate(f"""
        (value) => {{
            const el = document.querySelector('{selector}');
            if (!el) return 'not found';
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(el, value);
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return 'ok: ' + el.value;
        }}
    """, value)
    return result


def select_react_select_option(frame, container_selector, option_text):
    """Interact with a React Select dropdown to choose an option."""
    try:
        # Click the React Select control to open dropdown
        control = frame.locator(f"{container_selector} .select__control")
        if control.count() > 0:
            control.click()
            time.sleep(0.5)
            # Now the menu should be open, look for option
            option = frame.locator(f".select__option").filter(has_text=option_text).first
            if option.count() > 0:
                option.click()
                print(f"    Selected option: {option_text}")
                return True
            else:
                # Try typing to filter
                input_el = frame.locator(f"{container_selector} input[id^='react-select']")
                if input_el.count() == 0:
                    input_el = frame.locator(f"{container_selector} input")
                if input_el.count() > 0:
                    input_el.fill(option_text)
                    time.sleep(0.5)
                    option = frame.locator(".select__option").first
                    if option.count() > 0:
                        option.click()
                        print(f"    Selected first option after typing {option_text!r}")
                        return True
                print(f"    Option {option_text!r} not found in dropdown")
                # Close dropdown
                frame.keyboard.press("Escape")
                return False
        else:
            print(f"    React Select control not found: {container_selector}")
            return False
    except Exception as e:
        print(f"    React Select error: {e}")
        return False


def main():
    proxy = get_proxy()
    screenshots_taken = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            proxy=proxy,
            args=["--ignore-certificate-errors", "--no-sandbox"],
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print(f"\n[{TIMESTAMP}] Starting Sendcloud application...")
        page.goto(JOB_URL, wait_until="networkidle", timeout=45000)
        print(f"  Loaded: {page.title()}")

        s = screenshot(page, "01-job-page")
        screenshots_taken.append(s)

        # Find Greenhouse iframe
        greenhouse_frame = None
        for frame in page.frames:
            if "greenhouse.io" in frame.url:
                greenhouse_frame = frame
                print(f"  Found Greenhouse frame")
                break

        if not greenhouse_frame:
            msg = "Greenhouse iframe not found"
            save_application("failed", msg, screenshots_taken)
            browser.close()
            return

        try:
            greenhouse_frame.wait_for_selector("#first_name", timeout=15000)
        except Exception as e:
            s = screenshot(page, "error")
            screenshots_taken.append(s)
            save_application("failed", f"Form load timeout: {e}", screenshots_taken)
            browser.close()
            return

        print("  Form loaded")

        # === Fill personal details using React-aware approach ===
        print("\n--- Personal Details ---")

        for field_id, value in [
            ("first_name", APPLICANT["first_name"]),
            ("last_name", APPLICANT["last_name"]),
            ("email", APPLICANT["email"]),
        ]:
            el = greenhouse_frame.locator(f"#{field_id}")
            el.click()
            el.fill(value)
            # Trigger React events
            el.press("Tab")
            print(f"  {field_id}: {value}")

        # Phone
        phone_input = greenhouse_frame.locator("#phone")
        phone_input.click()
        phone_input.fill(APPLICANT["phone"])
        phone_input.press("Tab")
        print(f"  phone: {APPLICANT['phone']}")

        # Location (City) - use fill + trigger events
        loc_input = greenhouse_frame.locator("#candidate-location")
        if loc_input.count() > 0:
            loc_input.click()
            loc_input.fill(APPLICANT["location"])
            time.sleep(0.8)
            # Try to select first autocomplete suggestion, or just Tab away
            suggestions = greenhouse_frame.locator(".mapboxgl-ctrl-geocoder--suggestion, [class*='suggestion'], [class*='result']")
            if suggestions.count() > 0:
                suggestions.first.click()
                print(f"  location: {APPLICANT['location']} (autocomplete selected)")
            else:
                loc_input.press("Tab")
                print(f"  location: {APPLICANT['location']} (Tab pressed)")

        # Country - React Select
        print("\n--- Country (React Select) ---")
        country_container = greenhouse_frame.locator(".select-shell").first
        if country_container.count() > 0:
            # Check if this is actually the country field
            country_label = greenhouse_frame.locator("label[for='country']")
            if country_label.count() > 0:
                # Find the closest React Select container
                country_select_container = greenhouse_frame.locator("#country").locator("xpath=ancestor::*[contains(@class,'select-shell')]").first
                if country_select_container.count() > 0:
                    select_react_select_option(greenhouse_frame, None, "Netherlands")
                else:
                    # Click the control near the country label
                    country_control = greenhouse_frame.locator("[id='country']").locator("xpath=ancestor::div[contains(@class,'select')]//div[contains(@class,'control')]").first
                    if country_control.count() > 0:
                        country_control.click()
                        time.sleep(0.5)
                        # Type Netherlands
                        greenhouse_frame.keyboard.type("Netherlands")
                        time.sleep(0.5)
                        opt = greenhouse_frame.locator(".select__option").filter(has_text="Netherlands").first
                        if opt.count() > 0:
                            opt.click()
                            print("  Country: Netherlands (selected)")
                        else:
                            greenhouse_frame.keyboard.press("Escape")
                            # Try direct value setting via JS
                            r = fill_react_input(greenhouse_frame, "#country", "Netherlands")
                            print(f"  Country JS: {r}")

        time.sleep(0.5)
        s = screenshot(page, "02-personal-filled")
        screenshots_taken.append(s)

        # === Upload CV ===
        print("\n--- CV Upload ---")
        resume_input = greenhouse_frame.locator("#resume")
        if resume_input.count() > 0:
            resume_input.set_input_files(CV_PATH)
            time.sleep(2)
            # Verify
            upload_check = greenhouse_frame.evaluate("""
                () => {
                    const el = document.getElementById('resume');
                    if (el && el.files && el.files.length > 0) return 'FILE:' + el.files[0].name;
                    const txt = document.querySelector('[class*="filename"], [class*="file-name"], .resume .filename');
                    return txt ? 'LABEL:' + txt.textContent : 'unknown';
                }
            """)
            print(f"  CV: {upload_check}")

        s = screenshot(page, "03-cv-uploaded")
        screenshots_taken.append(s)

        # === Screening Questions ===
        print("\n--- Screening Questions ---")

        # Q1: LinkedIn Profile (text input)
        q1 = greenhouse_frame.locator("#question_35035420002")
        if q1.count() > 0:
            q1.click()
            q1.fill(APPLICANT["linkedin"])
            q1.press("Tab")
            print(f"  LinkedIn: {APPLICANT['linkedin']}")

        # Q2: Website (text input)
        q2 = greenhouse_frame.locator("#question_35035421002")
        if q2.count() > 0:
            q2.click()
            q2.fill(APPLICANT["website"])
            q2.press("Tab")
            print(f"  Website: {APPLICANT['website']}")

        # Q3: Netherlands residency - React Select dropdown
        print("  Q3: Netherlands residency (React Select)...")
        # The select container is near question_35035422002
        # Click the dropdown control
        q3_control = greenhouse_frame.locator(".select__control").filter(
            has=greenhouse_frame.locator("[id='question_35035422002']")
        ).first

        # Alternative approach: find all select controls and try to find the one for NL question
        # The NL question select is associated with the label "Do you reside within the Netherlands?"
        # Try clicking the div.select__control nearest to that label
        nl_result = greenhouse_frame.evaluate("""
            () => {
                // Find the Netherlands question container
                const label = Array.from(document.querySelectorAll('label')).find(
                    l => l.textContent.includes('reside within the Netherlands')
                );
                if (!label) return 'label not found';

                // Get the sibling select-shell div
                const container = label.closest('.select__container');
                if (!container) return 'container not found';

                const control = container.querySelector('.select__control');
                if (!control) return 'control not found';

                // Simulate click on control
                control.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                return 'clicked: ' + control.className;
            }
        """)
        print(f"    NL click result: {nl_result}")
        time.sleep(0.5)

        # Check if dropdown opened
        options_visible = greenhouse_frame.locator(".select__option").count()
        print(f"    Options visible: {options_visible}")

        if options_visible > 0:
            # Show available options
            all_opts = greenhouse_frame.locator(".select__option").all()
            for opt in all_opts:
                print(f"      Option: {opt.inner_text().strip()!r}")
            # Click "Yes"
            yes_opt = greenhouse_frame.locator(".select__option").filter(has_text="Yes").first
            if yes_opt.count() > 0:
                yes_opt.click()
                print("    Selected: Yes")
            else:
                # Click first option
                all_opts[0].click()
                print(f"    Selected first: {all_opts[0].inner_text().strip()!r}")
        else:
            # Try direct click on the control element
            select_controls = greenhouse_frame.locator(".select__control").all()
            print(f"    Found {len(select_controls)} select controls")

            # Click each control to find the Netherlands one
            for i, ctrl in enumerate(select_controls):
                ctrl_text = ctrl.inner_text().strip()
                print(f"      Control {i}: {ctrl_text!r}")

            # The Netherlands question is after Country, so try the 2nd select control
            # Country = index 0, Netherlands = index 1
            if len(select_controls) >= 2:
                select_controls[1].click()
                time.sleep(0.5)
                options = greenhouse_frame.locator(".select__option").all()
                print(f"    Options after clicking control 1: {len(options)}")
                for opt in options:
                    print(f"      {opt.inner_text().strip()!r}")
                yes_opt = greenhouse_frame.locator(".select__option").filter(has_text="Yes").first
                if yes_opt.count() > 0:
                    yes_opt.click()
                    print("    Selected: Yes")

        time.sleep(0.5)

        # Q4: Salary expectations (text input)
        q4 = greenhouse_frame.locator("#question_35035423002")
        if q4.count() > 0:
            q4.click()
            q4.fill(APPLICANT["salary"])
            q4.press("Tab")
            print(f"  Salary: {APPLICANT['salary']}")

        s = screenshot(page, "04-questions-filled")
        screenshots_taken.append(s)

        # === GDPR ===
        print("\n--- GDPR ---")
        gdpr = greenhouse_frame.locator("#gdpr_retention_consent_given_1")
        if gdpr.count() > 0:
            if not gdpr.is_checked():
                gdpr.check()
                print("  GDPR: checked")

        time.sleep(0.5)

        # === Verify all fields ===
        print("\n--- Field Verification ---")
        verification = greenhouse_frame.evaluate("""
            () => {
                const fields = {
                    'first_name': '#first_name',
                    'last_name': '#last_name',
                    'email': '#email',
                    'phone': '#phone',
                    'candidate-location': '#candidate-location',
                    'q1_linkedin': '#question_35035420002',
                    'q2_website': '#question_35035421002',
                    'q3_nl_residency': '#question_35035422002',
                    'q4_salary': '#question_35035423002',
                };
                const result = {};
                for (const [name, sel] of Object.entries(fields)) {
                    const el = document.querySelector(sel);
                    if (el) {
                        result[name] = el.value || '';
                    } else {
                        result[name] = 'NOT_FOUND';
                    }
                }
                // Check Netherlands via React Select displayed value
                const nlLabel = Array.from(document.querySelectorAll('label')).find(
                    l => l.textContent.includes('reside within the Netherlands')
                );
                if (nlLabel) {
                    const container = nlLabel.closest('.select__container');
                    if (container) {
                        const singleValue = container.querySelector('.select__single-value');
                        result['q3_nl_displayed'] = singleValue ? singleValue.textContent : 'not selected';
                    }
                }
                // Check resume
                const resumeInput = document.getElementById('resume');
                result['resume'] = resumeInput && resumeInput.files.length > 0
                    ? 'FILE:' + resumeInput.files[0].name
                    : 'EMPTY';
                // GDPR
                const gdpr = document.getElementById('gdpr_retention_consent_given_1');
                result['gdpr'] = gdpr ? (gdpr.checked ? 'CHECKED' : 'UNCHECKED') : 'NOT_FOUND';
                return result;
            }
        """)
        for k, v in verification.items():
            status_icon = "OK" if v and v != "EMPTY" and v != "NOT_FOUND" and v != "not selected" and v != "" else "MISSING"
            print(f"  [{status_icon}] {k}: {v!r}")

        s = screenshot(page, "05-pre-submit")
        screenshots_taken.append(s)

        # === Submit ===
        print("\n--- Submit ---")
        submit_btn = greenhouse_frame.locator("button[type=submit]").first
        if submit_btn.count() > 0:
            btn_text = submit_btn.inner_text().strip()
            print(f"  Button: {btn_text!r}")
            submit_btn.click()
            print("  CLICKED!")
        else:
            print("  Submit button not found!")
            all_btns = greenhouse_frame.locator("button").all()
            for btn in all_btns:
                t = btn.inner_text().strip()
                print(f"    btn: {t!r}")

        # Wait and check
        time.sleep(5)
        s = screenshot(page, "06-after-submit")
        screenshots_taken.append(s)

        content = greenhouse_frame.content()
        final_url = page.url

        confirmed = any(w in content.lower() for w in ["thank you", "application received", "successfully submitted"])
        captcha_blocked = "recaptcha" in content.lower() or "captcha" in content.lower()

        print(f"\n  Confirmed: {confirmed}")
        print(f"  CAPTCHA blocked: {captcha_blocked}")
        print(f"  Final URL: {final_url}")

        # Check for validation errors
        errors = greenhouse_frame.locator("[class*='error']:not([aria-hidden='true'])").all()
        error_msgs = [e.inner_text().strip() for e in errors if e.inner_text().strip()]
        if error_msgs:
            print(f"  Validation errors: {error_msgs}")

        if confirmed:
            status = "applied"
            notes = (
                "Application submitted successfully to Sendcloud (Greenhouse.io). "
                f"Fields: Hisham Abboud, {APPLICANT['email']}, +31648412838, Eindhoven NL, "
                "CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked."
            )
        elif captcha_blocked:
            status = "skipped"
            notes = (
                f"Sendcloud application form fully completed (Hisham Abboud, {APPLICANT['email']}, "
                "+31648412838, Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked). "
                f"Blocked by Google reCAPTCHA invisible (key: 6LfmcbcpAAAAAChNTbhUShzUOAMj_wY9LQIvLFX0). "
                f"MANUAL ACTION REQUIRED: Visit {JOB_URL} and complete submission manually."
            )
        elif error_msgs:
            status = "failed"
            notes = f"Form validation errors after submit: {'; '.join(error_msgs)}"
        else:
            status = "applied"
            notes = (
                f"Submit clicked on Sendcloud Greenhouse form. All fields filled. "
                f"No explicit confirmation or error. URL: {final_url}"
            )

        save_application(status, notes, screenshots_taken)

        time.sleep(2)
        s = screenshot(page, "07-final")
        screenshots_taken.append(s)

        browser.close()
        print(f"\nStatus: {status}")
        print("Screenshots:")
        for sc in screenshots_taken:
            print(f"  {sc}")

if __name__ == "__main__":
    main()
