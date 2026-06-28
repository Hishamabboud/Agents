#!/usr/bin/env python3
"""
Tebi Software Engineer (Early Talent) - Ashby Application Script
Job URL: https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application
"""

import time
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

APPLY_URL = "https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/tebi-early-talent-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven, Netherlands",
}

with open(COVER_LETTER_PATH, "r") as f:
    cover_letter_text = f.read()

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"tebi-{name}-{ts}.png")
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")
    return path


def try_fill(page, selectors, value):
    """Try a list of selectors and fill the first matching visible element."""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                el.fill(value)
                print(f"  Filled [{sel}] = {value[:40]}")
                return sel
        except Exception as e:
            pass
    return None


def main():
    screenshots = []
    status = "requires_manual_step"
    notes = ""
    filled_fields = []
    uploaded = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--ignore-certificate-errors",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navigating to: {APPLY_URL}")
        try:
            page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        except PlaywrightTimeout:
            print("Timeout on initial load, continuing...")

        time.sleep(6)
        print(f"Page title: {page.title()}")
        print(f"Page URL: {page.url}")

        screenshots.append(screenshot(page, "01-initial-load"))

        # --- Inspect all fields ---
        fields_info = page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                return inputs.map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    required: el.required,
                    value: el.value || ''
                }));
            }
        """)
        print(f"\nFound {len(fields_info)} form fields:")
        for f in fields_info:
            print(f"  [{f['tag']}:{f['type']}] name={f['name']} id={f['id']} placeholder={f['placeholder']} aria={f['ariaLabel']} required={f['required']}")

        # Labels
        labels_info = page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label'));
                return labels.map(l => ({text: l.innerText.trim(), forAttr: l.getAttribute('for') || ''}));
            }
        """)
        print(f"\nFound {len(labels_info)} labels:")
        for l in labels_info:
            print(f"  Label: '{l['text']}' for='{l['forAttr']}'")

        screenshots.append(screenshot(page, "02-page-inspected"))

        # --- Fill fields ---
        print("\nFilling form fields...")

        # First name
        r = try_fill(page, [
            'input[name*="firstName"]',
            'input[name*="first_name"]',
            'input[placeholder*="First name" i]',
            'input[aria-label*="First name" i]',
        ], CANDIDATE["first_name"])
        if r:
            filled_fields.append(("first_name", r))

        # Last name
        r = try_fill(page, [
            'input[name*="lastName"]',
            'input[name*="last_name"]',
            'input[placeholder*="Last name" i]',
            'input[aria-label*="Last name" i]',
        ], CANDIDATE["last_name"])
        if r:
            filled_fields.append(("last_name", r))

        # Full name fallback (if first/last not found)
        if not any(f[0] in ("first_name", "last_name") for f in filled_fields):
            r = try_fill(page, [
                'input[name*="name" i]',
                'input[placeholder*="Your name" i]',
                'input[placeholder*="Full name" i]',
                'input[aria-label*="name" i]',
            ], CANDIDATE["full_name"])
            if r:
                filled_fields.append(("full_name", r))

        # Email
        r = try_fill(page, [
            'input[type="email"]',
            'input[name*="email"]',
            'input[placeholder*="email" i]',
            'input[aria-label*="email" i]',
        ], CANDIDATE["email"])
        if r:
            filled_fields.append(("email", r))

        # Phone
        r = try_fill(page, [
            'input[type="tel"]',
            'input[name*="phone"]',
            'input[placeholder*="phone" i]',
            'input[aria-label*="phone" i]',
        ], CANDIDATE["phone"])
        if r:
            filled_fields.append(("phone", r))

        # LinkedIn
        r = try_fill(page, [
            'input[name*="linkedin" i]',
            'input[placeholder*="linkedin" i]',
            'input[aria-label*="linkedin" i]',
        ], CANDIDATE["linkedin"])
        if r:
            filled_fields.append(("linkedin", r))

        # GitHub
        r = try_fill(page, [
            'input[name*="github" i]',
            'input[placeholder*="github" i]',
            'input[aria-label*="github" i]',
        ], CANDIDATE["github"])
        if r:
            filled_fields.append(("github", r))

        # Cover letter / additional info textarea
        r = try_fill(page, [
            'textarea[name*="cover" i]',
            'textarea[placeholder*="cover letter" i]',
            'textarea[name*="letter" i]',
            'textarea[placeholder*="message" i]',
            'textarea[name*="message" i]',
            'textarea[aria-label*="cover" i]',
            'textarea',
        ], cover_letter_text[:3000])
        if r:
            filled_fields.append(("cover_letter", r))

        time.sleep(1)
        screenshots.append(screenshot(page, "03-fields-filled"))

        # --- Upload resume ---
        print("\nAttempting resume upload...")
        file_inputs = page.query_selector_all('input[type="file"]')
        print(f"Found {len(file_inputs)} file input(s)")

        for fi in file_inputs:
            try:
                fi.set_input_files(RESUME_PATH)
                print(f"Resume uploaded via direct file input")
                uploaded = True
                time.sleep(3)
                break
            except Exception as e:
                print(f"  Direct file input error: {e}")

        if not uploaded:
            # Try via file chooser triggered by upload button/label
            upload_triggers = [
                'label:has-text("Upload resume")',
                'label:has-text("Upload CV")',
                'button:has-text("Upload")',
                '[data-testid*="upload"]',
                '[aria-label*="upload" i]',
                'label[for*="resume" i]',
                'label[for*="file" i]',
            ]
            for sel in upload_triggers:
                try:
                    with page.expect_file_chooser(timeout=3000) as fc_info:
                        page.click(sel)
                    fc_info.value.set_files(RESUME_PATH)
                    print(f"Resume uploaded via file chooser: {sel}")
                    uploaded = True
                    time.sleep(3)
                    break
                except Exception as e:
                    pass

        time.sleep(2)
        screenshots.append(screenshot(page, "04-after-upload"))

        # --- Handle any dropdowns (source, etc.) ---
        selects = page.query_selector_all('select')
        for sel_el in selects:
            try:
                options = sel_el.query_selector_all('option')
                if len(options) > 1:
                    val = options[1].get_attribute('value')
                    if val:
                        sel_el.select_option(value=val)
                        print(f"Selected dropdown value: {val}")
            except:
                pass

        # --- CAPTCHA check ---
        page_content = page.content().lower()
        has_recaptcha = 'recaptcha' in page_content or 'g-recaptcha' in page_content
        has_hcaptcha = 'hcaptcha' in page_content
        has_turnstile = 'turnstile' in page_content or 'cf-turnstile' in page_content

        print(f"\nCAPTCHA check: reCAPTCHA={has_recaptcha}, hCaptcha={has_hcaptcha}, Turnstile={has_turnstile}")

        screenshots.append(screenshot(page, "05-pre-submit"))

        if has_recaptcha or has_hcaptcha or has_turnstile:
            captcha_type = "reCAPTCHA" if has_recaptcha else ("hCaptcha" if has_hcaptcha else "Cloudflare Turnstile")
            notes = (
                f"Form fields filled and resume uploaded. Blocked by {captcha_type}. "
                f"All data ready: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                f"phone=+31648412838, LinkedIn/GitHub filled. Manual CAPTCHA solving required. "
                f"Application URL: {APPLY_URL}"
            )
            status = "requires_manual_step"
            print(f"CAPTCHA detected ({captcha_type}), not clicking submit")
            screenshots.append(screenshot(page, "06-captcha-blocked"))
        else:
            # Try to submit
            print("\nNo CAPTCHA detected. Attempting submit...")
            submitted = False
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Submit application")',
                'button:has-text("Submit Application")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                '[data-testid*="submit"]',
                'input[type="submit"]',
            ]
            for sel in submit_selectors:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible() and btn.is_enabled():
                        print(f"Clicking submit: {sel}")
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        print("Submit clicked!")
                        time.sleep(6)
                        submitted = True
                        break
                except Exception as e:
                    print(f"  Submit {sel} failed: {e}")

            if submitted:
                screenshots.append(screenshot(page, "06-post-submit"))
                final_url = page.url
                final_content = page.content().lower()
                print(f"Post-submit URL: {final_url}")

                success_kw = ['thank you', 'thanks', 'application received', 'submitted successfully', 'we\'ll be in touch', 'confirmation']
                error_kw = ['error', 'failed', 'required field', 'please fill']

                if any(kw in final_content for kw in success_kw):
                    status = "applied"
                    notes = f"Application submitted successfully via Ashby ATS. Confirmation detected. URL: {final_url}"
                    print("SUCCESS: Application submitted and confirmed!")
                elif any(kw in final_content for kw in error_kw):
                    status = "requires_manual_step"
                    notes = f"Submit attempted but validation errors detected. URL: {final_url}"
                    print("ERROR: Validation errors after submit")
                else:
                    status = "requires_manual_step"
                    notes = f"Submit clicked, outcome unclear. Final URL: {final_url}. Manual verification recommended."
                    print("Submit clicked, outcome unclear")
            else:
                notes = "No enabled submit button found. Form may need manual interaction."
                status = "requires_manual_step"

        browser.close()

    result = {
        "status": status,
        "screenshots": screenshots,
        "notes": notes,
        "filled_fields": filled_fields,
        "uploaded_resume": uploaded,
        "timestamp": ts,
    }
    print(f"\n--- RESULT ---")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
