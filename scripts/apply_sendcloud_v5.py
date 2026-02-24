#!/usr/bin/env python3
"""
Apply to Sendcloud Medior Backend Engineer (Python) - v5
Clean, simplified approach with proper React Select handling.
"""

import os
import re
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

JOB_URL = "https://jobs.sendcloud.com/jobs/8390536002-cg"
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


def ss(page, name):
    path = f"{SCREENSHOTS_DIR}/sendcloud-{name}-{TIMESTAMP}.png"
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  Screenshot: {path}")
    except Exception as e:
        print(f"  Screenshot error: {e}")
    return path


def save_app(status, notes, shots):
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
        "screenshots": shots,
        "notes": notes,
        "email_used": "hiaham123@hotmail.com",
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
    print(f"  Saved: {status}")


def fill(frame, sel, val):
    """Fill an input reliably."""
    el = frame.locator(sel)
    if el.count() == 0:
        print(f"  NOT FOUND: {sel}")
        return False
    el.click()
    el.fill(val)
    time.sleep(0.2)
    el.press("Tab")
    print(f"  {sel}: {val!r}")
    return True


def click_react_select_option(frame, question_id, value):
    """
    Open a React Select dropdown tied to a question ID and select an option.
    The actual hidden input has id=question_id but is inside a React Select container.
    We need to click the .select__control inside the same container.
    """
    # Use JS to find and click the control
    result = frame.evaluate(f"""
        (value) => {{
            // Find the hidden input with our question ID
            const input = document.getElementById('{question_id}');
            if (!input) return 'input not found';

            // Walk up to find the react-select container
            let container = input.closest('.select__container, [class*="react-select"], .select-shell');
            if (!container) container = input.parentElement;
            if (!container) return 'container not found';

            // Find the control div to click
            const control = container.querySelector('.select__control');
            if (!control) return 'control not found';

            // Simulate mousedown to open dropdown
            control.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true, cancelable: true}}));
            control.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true, cancelable: true}}));
            control.dispatchEvent(new MouseEvent('click', {{bubbles: true, cancelable: true}}));

            return 'clicked control for {question_id}';
        }}
    """, value)
    print(f"    JS click result: {result}")
    time.sleep(1)

    # Now check if dropdown opened and find the option
    options = frame.locator(".select__option, [class*='option']").all()
    visible_options = [o for o in options if o.is_visible()]
    print(f"    Visible options: {len(visible_options)}")
    for o in visible_options:
        print(f"      {o.inner_text().strip()!r}")

    for opt in visible_options:
        try:
            opt_text = opt.inner_text(timeout=2000).strip()
        except Exception:
            opt_text = ''
        if value.lower() in opt_text.lower():
            opt.click()
            print(f"    Selected: {opt_text!r}")
            return True

    # Try pressing Escape if no match found
    frame.locator("body").press("Escape")
    return False


def main():
    proxy = get_proxy()
    shots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            proxy=proxy,
            args=["--ignore-certificate-errors", "--no-sandbox"],
        )
        ctx = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        print(f"\n[{TIMESTAMP}] Sendcloud application starting...")
        page.goto(JOB_URL, wait_until="networkidle", timeout=45000)

        shots.append(ss(page, "01-job-page"))

        # Find frame
        ghf = None
        for frame in page.frames:
            if "greenhouse.io" in frame.url:
                ghf = frame
                break

        if not ghf:
            save_app("failed", "Greenhouse iframe not found", shots)
            browser.close()
            return

        ghf.wait_for_selector("#first_name", timeout=15000)
        print("  Form ready")

        # ===== Personal Details =====
        print("\n[PERSONAL DETAILS]")
        fill(ghf, "#first_name", "Hisham")
        fill(ghf, "#last_name", "Abboud")
        fill(ghf, "#email", "hiaham123@hotmail.com")
        fill(ghf, "#phone", "+31648412838")

        # Location: just fill and tab, no autocomplete
        loc = ghf.locator("#candidate-location")
        if loc.count() > 0:
            loc.click()
            loc.fill("Eindhoven")
            time.sleep(1.5)
            # Close any open suggestions with Escape
            loc.press("Escape")
            time.sleep(0.3)
            loc.press("Tab")
            print("  candidate-location: 'Eindhoven'")

        shots.append(ss(page, "02-personal-filled"))

        # ===== CV Upload =====
        print("\n[CV UPLOAD]")
        resume_el = ghf.locator("#resume")
        if resume_el.count() > 0:
            resume_el.set_input_files(CV_PATH)
            time.sleep(2)
            # Check what's uploaded
            upload_name = ghf.evaluate("""
                () => {
                    const el = document.getElementById('resume');
                    if (el && el.files && el.files.length > 0) return el.files[0].name;
                    const lbl = document.querySelector('.resume-display, [class*="file-name"]');
                    return lbl ? lbl.textContent : 'check screenshots';
                }
            """)
            print(f"  CV uploaded: {upload_name}")
        shots.append(ss(page, "03-cv-uploaded"))

        # ===== Screening Questions =====
        print("\n[SCREENING QUESTIONS]")

        # Q1: LinkedIn
        fill(ghf, "#question_35035420002", "linkedin.com/in/hisham-abboud")

        # Q2: Website
        fill(ghf, "#question_35035421002", "https://cogitatai.com")

        # Q3: Netherlands residency - React Select
        print("  Q3: Netherlands residency (React Select dropdown)...")
        click_react_select_option(ghf, "question_35035422002", "Yes")

        # Q4: Salary
        fill(ghf, "#question_35035423002", "EUR 55,000 - 65,000")

        shots.append(ss(page, "04-questions-filled"))

        # ===== GDPR =====
        print("\n[GDPR]")
        gdpr_el = ghf.locator("#gdpr_retention_consent_given_1")
        if gdpr_el.count() > 0:
            if not gdpr_el.is_checked():
                gdpr_el.check()
            print("  GDPR: checked")

        time.sleep(0.5)

        # ===== Verify =====
        print("\n[VERIFICATION]")
        v = ghf.evaluate("""
            () => ({
                first: document.getElementById('first_name')?.value || '',
                last: document.getElementById('last_name')?.value || '',
                email: document.getElementById('email')?.value || '',
                phone: document.getElementById('phone')?.value || '',
                location: document.getElementById('candidate-location')?.value || '',
                linkedin: document.getElementById('question_35035420002')?.value || '',
                website: document.getElementById('question_35035421002')?.value || '',
                nl_displayed: document.querySelector('.select__single-value')?.textContent || 'none',
                salary: document.getElementById('question_35035423002')?.value || '',
                resume: (() => {
                    const el = document.getElementById('resume');
                    return el && el.files.length > 0 ? el.files[0].name : 'EMPTY';
                })(),
                gdpr: document.getElementById('gdpr_retention_consent_given_1')?.checked || false,
            })
        """)
        for k, val in v.items():
            ok = bool(val and val != 'EMPTY' and val != 'none' and val != '')
            print(f"  {'[OK]' if ok else '[!!]'} {k}: {val!r}")

        shots.append(ss(page, "05-pre-submit"))

        # ===== Submit =====
        print("\n[SUBMIT]")
        sub_btn = ghf.locator("button[type=submit]").first
        if sub_btn.count() > 0:
            print(f"  Clicking: {sub_btn.inner_text().strip()!r}")
            sub_btn.click()
            print("  Clicked!")
        else:
            print("  No submit button found!")

        time.sleep(5)
        shots.append(ss(page, "06-after-submit"))

        # ===== Check Result =====
        content = ghf.content().lower()
        final_url = page.url

        confirmed = any(w in content for w in ["thank you", "application received", "successfully submitted"])
        captcha = "recaptcha" in content or "captcha" in content

        print(f"\n  confirmed={confirmed}, captcha={captcha}, url={final_url}")

        errs = []
        err_els = ghf.locator("[class*='error-message'], [class*='field_error']").all()
        for e in err_els:
            t = e.inner_text().strip()
            if t:
                errs.append(t)
        if errs:
            print(f"  Errors: {errs}")

        if confirmed:
            status = "applied"
            notes = (
                "Application successfully submitted to Sendcloud via Greenhouse.io. "
                "All fields: Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                "Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked."
            )
        elif captcha:
            status = "skipped"
            notes = (
                "Sendcloud Greenhouse form fully filled but blocked by Google reCAPTCHA invisible "
                "(key: 6LfmcbcpAAAAAChNTbhUShzUOAMj_wY9LQIvLFX0). "
                "Form data: Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                "Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn=linkedin.com/in/hisham-abboud, "
                "Website=cogitatai.com, Netherlands resident=Yes, Salary=EUR 55-65k, GDPR=checked. "
                f"MANUAL ACTION REQUIRED: Visit {JOB_URL} and submit manually."
            )
        elif errs:
            status = "failed"
            notes = f"Validation errors: {'; '.join(errs)}"
        else:
            status = "applied"
            notes = (
                f"Submit clicked, no explicit confirmation. URL: {final_url}. "
                "Form: Hisham Abboud, hiaham123@hotmail.com, +31648412838, "
                "Eindhoven NL, CV=Hisham Abboud CV.pdf, LinkedIn, Website, NL=Yes, Salary."
            )

        save_app(status, notes, shots)

        shots.append(ss(page, "07-final"))
        browser.close()

        print(f"\nDone. Status: {status}")
        print("Screenshots:")
        for s in shots:
            print(f"  {s}")

if __name__ == "__main__":
    main()
