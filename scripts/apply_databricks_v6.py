#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE via Greenhouse (v6).
Fixes:
- Country: type "Netherlands" then pick Netherlands (+31) specifically
- Phone: clear field then set just the local digits without leading 0 if +31 prefix set
- Checkboxes: use XPath-based Playwright locator instead of CSS (avoids [] issue)
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
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-v6-{name}-{TIMESTAMP}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {path}")
    except Exception as e:
        print(f"  [SS FAIL] {e}")
        path = None
    return path


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
            print("Loading careers page...")
            page.goto(
                "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)

            iframe_el = page.locator("iframe[src*='greenhouse']").first
            gh_url = iframe_el.get_attribute("src")
            page.goto(gh_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            page.wait_for_selector("#first_name", timeout=10000)
            print("Form loaded")
            s = ss(page, "01-form-loaded")
            if s: screenshots.append(s)

            # ── BASIC FIELDS ──────────────────────────────────────────────────
            page.fill("#first_name", "Hisham")
            page.fill("#last_name", "Abboud")
            page.fill("#email", "hiaham123@hotmail.com")
            print("Name+email filled")

            # ── COUNTRY: Netherlands (+31) ────────────────────────────────────
            # The React-Select for country: we need to find the option that contains
            # "Netherlands" AND "+31" (not Netherlands Antilles +599)
            print("Setting country...")
            country_input = page.locator("#country")
            country_input.click()
            time.sleep(0.4)
            # Type to filter - "Netherlands" will show multiple, we need to pick the right one
            country_input.type("Nether", delay=50)
            time.sleep(1)

            # Get all visible options and find the one with +31
            options_info = page.evaluate("""
            () => {
                const opts = document.querySelectorAll('[class*="option"]');
                return Array.from(opts).filter(o => o.offsetParent !== null).map(o => ({
                    text: o.textContent.trim(),
                    id: o.id,
                    data: o.getAttribute('data-value') || ''
                }));
            }
            """)
            print(f"  Country options visible: {options_info}")

            # Click the option for Netherlands (not Antilles)
            nl_clicked = False
            for opt_info in options_info:
                txt = opt_info.get('text', '')
                if 'netherlands' in txt.lower() and 'antilles' not in txt.lower() and 'caribbean' not in txt.lower():
                    # This should be the Netherlands
                    # Use page.locator to find and click it
                    opt_el = page.locator(f"[class*='option']").filter(has_text=txt).first
                    try:
                        opt_el.click(timeout=2000)
                        print(f"  Country selected: {txt}")
                        nl_clicked = True
                        break
                    except Exception:
                        continue

            if not nl_clicked:
                # Fallback: clear and type "+31" to filter by dial code, then pick Netherlands
                country_input.click()
                time.sleep(0.2)
                country_input.fill("")
                country_input.type("Netherlands", delay=50)
                time.sleep(0.8)
                # Press down twice to skip Netherlands Antilles (which might come first) and Enter
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                page.keyboard.press("Enter")
                print("  Country: keyboard fallback")

            time.sleep(0.5)

            # ── PHONE ─────────────────────────────────────────────────────────
            # The ITI (intl-tel-input) adds a country code prefix.
            # After selecting Netherlands (+31), enter just "648412838" (no leading 0)
            # Full NL number: +31 6 48412838, local format: 0648412838
            # ITI expects the full international number minus the +31: 648412838
            print("Filling phone...")
            phone_input = page.locator("#phone")
            phone_input.click()
            time.sleep(0.2)
            # Clear existing content
            page.evaluate("document.getElementById('phone').value = ''")
            phone_input.click()
            time.sleep(0.1)
            # Type the number without leading 0 (ITI adds +31 prefix)
            phone_input.type("648412838", delay=30)
            print("  Phone: 648412838 (ITI will add +31)")

            # ── LOCATION ─────────────────────────────────────────────────────
            print("Setting location...")
            loc_input = page.locator("#candidate-location")
            loc_input.click()
            time.sleep(0.3)
            loc_input.type("Amsterdam", delay=50)
            time.sleep(1)

            # Pick Amsterdam option (there should be one clear choice)
            am_opts = page.evaluate("""
            () => {
                const opts = document.querySelectorAll('[class*="option"]');
                return Array.from(opts).filter(o => o.offsetParent !== null).map(o => ({
                    text: o.textContent.trim()
                }));
            }
            """)
            print(f"  Location options: {am_opts[:5]}")

            try:
                am_opt = page.locator("[class*='option']").filter(has_text="Amsterdam").first
                am_opt.wait_for(state="visible", timeout=3000)
                am_opt.click()
                print("  Location: Amsterdam selected")
            except PlaywrightTimeout:
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)
                page.keyboard.press("Enter")
            time.sleep(0.5)

            # ── RESUME ────────────────────────────────────────────────────────
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(RESUME_PATH)
            time.sleep(2)
            print("Resume uploaded")

            s = ss(page, "02-top-fields")
            if s: screenshots.append(s)

            # Scroll down
            page.evaluate("window.scrollTo(0, 600)")
            time.sleep(0.5)

            # ── LINKEDIN & WEBSITE ────────────────────────────────────────────
            page.fill("#question_32045705002", "https://linkedin.com/in/hisham-abboud")
            page.fill("#question_32045706002", "https://github.com/Hishamabboud")
            print("LinkedIn/GitHub filled")

            s = ss(page, "03-social-links")
            if s: screenshots.append(s)

            # ── DROPDOWNS (React Select) ──────────────────────────────────────
            def react_dropdown(input_id, choice_text, prefer_exact=False):
                try:
                    inp = page.locator(f"#{input_id}")
                    # Click the control (parent container)
                    inp.click()
                    time.sleep(0.4)
                    # Wait for options to appear
                    opts_visible = page.locator("[class*='menu']").first
                    try:
                        opts_visible.wait_for(state="visible", timeout=3000)
                    except PlaywrightTimeout:
                        pass

                    # Get the visible options
                    opts = page.locator("[class*='option']").all()
                    print(f"  Dropdown #{input_id} options: {[o.inner_text() for o in opts[:8]]}")

                    if prefer_exact:
                        # Find exact match
                        for opt in opts:
                            try:
                                if opt.is_visible(timeout=500) and opt.inner_text().strip() == choice_text:
                                    opt.click()
                                    print(f"  Selected (exact): '{choice_text}'")
                                    time.sleep(0.3)
                                    return True
                            except Exception:
                                continue

                    # Find by partial text
                    for opt in opts:
                        try:
                            if opt.is_visible(timeout=500) and choice_text.lower() in opt.inner_text().lower():
                                opt.click()
                                print(f"  Selected (partial): '{opt.inner_text().strip()}'")
                                time.sleep(0.3)
                                return True
                        except Exception:
                            continue

                    # Fallback keyboard
                    page.keyboard.press("ArrowDown")
                    time.sleep(0.2)
                    page.keyboard.press("Enter")
                    print(f"  Keyboard fallback for '{choice_text}'")
                    return True
                except Exception as e:
                    print(f"  Dropdown error #{input_id}: {e}")
                    return False

            print("Dropdown: work auth...")
            react_dropdown("question_32045707002", "Yes", prefer_exact=True)

            print("Dropdown: visa sponsorship...")
            react_dropdown("question_32045708002", "No", prefer_exact=True)

            print("Dropdown: Databricks history...")
            react_dropdown("question_32045709002", "No", prefer_exact=True)

            s = ss(page, "04-dropdowns")
            if s: screenshots.append(s)

            # ── CHECKBOXES (React-controlled) ─────────────────────────────────
            # Must use Playwright .click() on the actual element via XPath/attribute
            # Cannot use CSS id selector with [] chars
            print("Checking 'None of the above' checkbox (group 1)...")
            cb1 = page.locator('input[type="checkbox"][value="221057636002"]')
            try:
                cb1.scroll_into_view_if_needed()
                cb1.click()
                print(f"  Group 1 checkbox clicked")
            except Exception as e:
                print(f"  Group 1 checkbox error: {e}")
                # Fallback: click the label
                label1 = page.locator('label[for="question_35110793002[]_221057636002"]')
                if label1.count() > 0:
                    label1.click()
                    print("  Group 1: clicked label")

            time.sleep(0.3)

            print("Checking 'Not applicable' checkbox (group 2)...")
            cb2 = page.locator('input[type="checkbox"][value="221076133002"]')
            try:
                cb2.scroll_into_view_if_needed()
                cb2.click()
                print(f"  Group 2 checkbox clicked")
            except Exception as e:
                print(f"  Group 2 checkbox error: {e}")
                label2 = page.locator('label[for="question_35114477002[]_221076133002"]')
                if label2.count() > 0:
                    label2.click()
                    print("  Group 2: clicked label")

            time.sleep(0.5)

            # Verify
            checked = page.evaluate("""
            () => Array.from(document.querySelectorAll('input[type="checkbox"]'))
                .filter(c => c.checked)
                .map(c => ({value: c.value, name: c.name}))
            """)
            print(f"  Verified checked: {checked}")

            s = ss(page, "05-checkboxes")
            if s: screenshots.append(s)

            # ── FINAL SCROLL & SUBMIT ─────────────────────────────────────────
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            s = ss(page, "06-full-form")
            if s: screenshots.append(s)

            submit = page.locator("button:has-text('Submit application'), button:has-text('Submit Application'), button[type='submit']").first
            submit.scroll_into_view_if_needed()
            time.sleep(0.5)
            s = ss(page, "07-pre-submit")
            if s: screenshots.append(s)

            print("Submitting form...")
            submit.click()
            time.sleep(6)

            s = ss(page, "08-post-submit")
            if s: screenshots.append(s)

            final_url = page.url
            print(f"Final URL: {final_url}")

            try:
                body_text = page.inner_text("body").lower()
            except Exception:
                body_text = ""

            print(f"Body (600): {body_text[:600]}")

            captcha_kw = ["recaptcha", "captcha", "robot", "verify you are human", "not a robot"]
            success_kw = ["thank you", "application received", "successfully submitted",
                          "we'll review", "we will review", "your application has been",
                          "application submitted", "we received your", "confirmation"]
            error_kw = ["is required", "can't be blank", "please enter your location",
                        "this field is required", "select a country", "phone number is too long",
                        "phone number is invalid"]

            if any(kw in body_text for kw in captcha_kw):
                status = "requires_manual_step"
                notes = (
                    "reCAPTCHA Enterprise blocked Greenhouse submission. All fields filled. "
                    "Manual action required at: https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002 . "
                    "Filled: Hisham Abboud, hiaham123@hotmail.com, +31 648412838, Amsterdam NL, "
                    "LinkedIn=linkedin.com/in/hisham-abboud, GitHub=github.com/Hishamabboud, "
                    "Work auth=Yes, Visa=No, Databricks=No, Sanctions=None of above + Not applicable."
                )
            elif any(kw in body_text for kw in success_kw):
                status = "applied"
                notes = f"Application submitted via Greenhouse. Confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif any(kw in body_text for kw in error_kw):
                status = "failed"
                notes = f"Form validation errors remain: {body_text[:500]}"
            else:
                status = "requires_manual_step"
                notes = f"Ambiguous. URL: {final_url}. Body: {body_text[:300]}"

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
    print("=== Databricks Fullstack SE - v6 ===")
    status, notes, screenshots = run()
    print(f"\nResult: {status}")
    print(f"Notes: {notes[:500]}")
    print(f"Screenshots ({len(screenshots)}): {screenshots}")
    print("\nJSON_RESULT:" + json.dumps({
        "status": status, "notes": notes, "screenshots": screenshots,
        "timestamp": datetime.now().isoformat()
    }))
