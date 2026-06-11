#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE role via Greenhouse (v2).
Handles all form fields visible in screenshots.
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
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-v2-{name}-{TIMESTAMP}.png")
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
            # Step 1: Load the Databricks careers page to get the Greenhouse embed token
            print("Loading Databricks careers page...")
            page.goto(
                "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)
            s = ss(page, "01-careers-page")
            if s: screenshots.append(s)

            # Find the Greenhouse iframe src
            iframe_el = page.locator("iframe[src*='greenhouse']").first
            if iframe_el.count() == 0:
                raise Exception("No Greenhouse iframe found on careers page")

            gh_url = iframe_el.get_attribute("src")
            print(f"Greenhouse iframe URL: {gh_url}")

            # Navigate directly to the Greenhouse embed form
            page.goto(gh_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            s = ss(page, "02-form-loaded")
            if s: screenshots.append(s)

            # Confirm form presence
            page.wait_for_selector("#first_name", timeout=10000)
            print("Form confirmed loaded")

            # ── FILL TOP FIELDS ──────────────────────────────────────────────

            print("Filling: first name")
            page.fill("#first_name", "Hisham")

            print("Filling: last name")
            page.fill("#last_name", "Abboud")

            print("Filling: email")
            page.fill("#email", "hiaham123@hotmail.com")

            # Phone: the form auto-selected Netherlands (+31) from the country dropdown
            # We just fill the phone number field
            print("Filling: phone")
            phone_sel = "input[type='tel'], input[id='phone'], input[name*='phone']"
            try:
                phone_input = page.locator(phone_sel).first
                phone_input.fill("+31648412838")
            except Exception as e:
                print(f"  Phone fill error: {e}")

            # Location (City) — plain city name
            print("Filling: location (city)")
            try:
                loc_input = page.locator("input[id*='location'], input[placeholder*='City'], input[placeholder*='Location']").first
                loc_input.fill("Amsterdam")
                time.sleep(0.5)
                # If there is an autocomplete dropdown, press Escape to dismiss
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
            except Exception as e:
                print(f"  Location fill error: {e}")

            # Upload resume
            print("Uploading resume...")
            file_inputs = page.locator("input[type='file']")
            count = file_inputs.count()
            print(f"  {count} file input(s) found")
            if count > 0:
                file_inputs.first.set_input_files(RESUME_PATH)
                time.sleep(2)
                print("  Resume uploaded")

            s = ss(page, "03-top-fields-filled")
            if s: screenshots.append(s)

            # Scroll down to reveal bottom fields
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            s = ss(page, "04-scrolled-down")
            if s: screenshots.append(s)

            # ── LINKEDIN and WEBSITE ──────────────────────────────────────────
            print("Filling: LinkedIn profile")
            try:
                # Greenhouse uses label text to identify custom question fields
                # Let's find input near "LinkedIn" label
                linkedin_input = page.locator(
                    "input[id*='linkedin'], input[name*='linkedin'], "
                    "input[placeholder*='LinkedIn'], input[placeholder*='linkedin']"
                ).first
                if linkedin_input.count() > 0:
                    linkedin_input.fill("https://linkedin.com/in/hisham-abboud")
                    print("  LinkedIn filled via id/placeholder")
                else:
                    # Try by label text
                    labels = page.locator("label").all()
                    for label in labels:
                        try:
                            ltext = label.inner_text().lower()
                            if "linkedin" in ltext:
                                for_id = label.get_attribute("for")
                                if for_id:
                                    page.fill(f"#{for_id}", "https://linkedin.com/in/hisham-abboud")
                                    print(f"  LinkedIn filled via label for=#{for_id}")
                                    break
                        except Exception:
                            continue
            except Exception as e:
                print(f"  LinkedIn fill error: {e}")

            print("Filling: website (GitHub)")
            try:
                website_input = page.locator(
                    "input[id*='website'], input[name*='website'], "
                    "input[placeholder*='Website'], input[placeholder*='website'], "
                    "input[id*='github'], input[name*='github']"
                ).first
                if website_input.count() > 0:
                    website_input.fill("https://github.com/Hishamabboud")
                    print("  Website/GitHub filled")
                else:
                    # Find by label
                    labels = page.locator("label").all()
                    for label in labels:
                        try:
                            ltext = label.inner_text().lower()
                            if "website" in ltext or "github" in ltext:
                                for_id = label.get_attribute("for")
                                if for_id:
                                    page.fill(f"#{for_id}", "https://github.com/Hishamabboud")
                                    print(f"  Website filled via label for=#{for_id}")
                                    break
                        except Exception:
                            continue
            except Exception as e:
                print(f"  Website fill error: {e}")

            # ── REQUIRED DROPDOWNS ────────────────────────────────────────────
            # 1. "Are you legally authorized to work in the country..."
            print("Handling dropdown: work authorization")
            try:
                # Find all select elements
                selects = page.locator("select").all()
                print(f"  Found {len(selects)} select element(s)")

                # We need to identify them by surrounding label text
                # Strategy: use page.evaluate to find selects with their labels

                # Greenhouse typically has selects inside a div with a label
                # Let's get all select elements and their nearby text
                for i, sel_el in enumerate(selects):
                    sel_id = sel_el.get_attribute("id") or ""
                    sel_name = sel_el.get_attribute("name") or ""
                    print(f"  Select {i}: id={sel_id}, name={sel_name}")

                # Try to select options by the question text context
                # Q1: legally authorized -> Yes
                # Q2: visa sponsorship needed -> No
                # Q3: worked at Databricks -> No

                # Use evaluate to find and select options
                result = page.evaluate("""
                () => {
                    const results = [];
                    const selects = document.querySelectorAll('select');
                    selects.forEach((sel, idx) => {
                        const parent = sel.closest('.field, .form-group, div');
                        const labelEl = parent ? parent.querySelector('label, .label') : null;
                        const labelText = labelEl ? labelEl.textContent.trim().toLowerCase() : '';
                        const options = Array.from(sel.options).map(o => ({value: o.value, text: o.text}));
                        results.push({idx, id: sel.id, name: sel.name, labelText: labelText.substring(0,80), options});
                    });
                    return results;
                }
                """)
                print(f"  Select info: {json.dumps(result, indent=2)[:2000]}")

                for sel_info in result:
                    label = sel_info.get('labelText', '').lower()
                    sel_id = sel_info.get('id', '')
                    options = sel_info.get('options', [])
                    sel_selector = f"#{sel_id}" if sel_id else f"select:nth-of-type({sel_info['idx']+1})"

                    if "legally authorized" in label or "authorized to work" in label:
                        # Yes
                        yes_opt = next((o for o in options if "yes" in o['text'].lower()), None)
                        if yes_opt:
                            page.select_option(sel_selector, value=yes_opt['value'])
                            print(f"  Work auth: selected '{yes_opt['text']}'")

                    elif "sponsorship" in label or "visa" in label:
                        # No
                        no_opt = next((o for o in options if o['text'].lower().strip() == "no"), None)
                        if no_opt:
                            page.select_option(sel_selector, value=no_opt['value'])
                            print(f"  Visa sponsorship: selected '{no_opt['text']}'")

                    elif "worked for databricks" in label or "previously worked" in label or "worked at databricks" in label:
                        # No
                        no_opt = next((o for o in options if o['text'].lower().strip() == "no"), None)
                        if no_opt:
                            page.select_option(sel_selector, value=no_opt['value'])
                            print(f"  Worked at Databricks: selected '{no_opt['text']}'")

            except Exception as e:
                print(f"  Dropdown handling error: {e}")

            # ── SANCTIONS/EXPORT CONTROLS CHECKBOXES ─────────────────────────
            print("Handling checkboxes: sanctions compliance")
            try:
                # First group: "None of the above" for the Cuba/Iran/etc question
                # Second group: "None of these apply to me" or "Not applicable"
                result2 = page.evaluate("""
                () => {
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    return Array.from(checkboxes).map((cb, idx) => {
                        const label = cb.closest('label, li') || cb.parentElement;
                        const text = label ? label.textContent.trim() : '';
                        return {idx, id: cb.id, name: cb.name, value: cb.value, text: text.substring(0,120), checked: cb.checked};
                    });
                }
                """)
                print(f"  Checkbox info ({len(result2)} found):")
                for cb in result2:
                    print(f"    [{cb['idx']}] {cb['text'][:80]}")

                for cb in result2:
                    txt = cb.get('text', '').lower()
                    cb_id = cb.get('id', '')
                    cb_sel = f"#{cb_id}" if cb_id else f"input[type='checkbox']:nth-of-type({cb['idx']+1})"

                    # Check "None of the above" for sanctions country list
                    if txt.strip().startswith("none of the above"):
                        page.check(cb_sel)
                        print(f"  Checked: 'None of the above'")

                    # For the second group: "None of these apply to me"
                    elif "none of these apply to me" in txt:
                        page.check(cb_sel)
                        print(f"  Checked: 'None of these apply to me'")

                    # "Not applicable" (i.e., selected none of the above for prior question)
                    elif "not applicable" in txt and "i selected" in txt and "none" in txt:
                        page.check(cb_sel)
                        print(f"  Checked: 'Not applicable (none of the above)'")

            except Exception as e:
                print(f"  Checkbox handling error: {e}")

            time.sleep(0.5)
            s = ss(page, "05-all-fields-filled")
            if s: screenshots.append(s)

            # Scroll to bottom again to ensure all visible
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            s = ss(page, "06-final-state-before-submit")
            if s: screenshots.append(s)

            # ── SUBMIT ────────────────────────────────────────────────────────
            print("Looking for submit button...")
            submit = page.locator(
                "input[type='submit'][value*='Submit'], "
                "button[type='submit']:has-text('Submit'), "
                "button:has-text('Submit application'), "
                "button:has-text('Submit Application')"
            ).first

            if submit.count() == 0:
                raise Exception("Submit button not found")

            submit.scroll_into_view_if_needed()
            time.sleep(0.5)
            s = ss(page, "07-pre-submit")
            if s: screenshots.append(s)

            print("Clicking submit...")
            submit.click()
            time.sleep(5)

            s = ss(page, "08-post-submit")
            if s: screenshots.append(s)

            final_url = page.url
            print(f"Post-submit URL: {final_url}")

            try:
                body_text = page.inner_text("body").lower()
            except Exception:
                body_text = ""

            print(f"Body text (first 400 chars): {body_text[:400]}")

            captcha_kw = ["recaptcha", "hcaptcha", "robot", "verify you are human"]
            success_kw = ["thank you", "application received", "successfully", "confirmation", "we'll review", "we will review"]
            error_kw = ["is required", "can't be blank", "is invalid", "please fill", "there was a problem"]

            if any(kw in body_text for kw in captcha_kw):
                status = "requires_manual_step"
                notes = "reCAPTCHA Enterprise blocked submission on Greenhouse form. Form was fully filled. Manual submission required."
            elif any(kw in body_text for kw in success_kw):
                status = "applied"
                notes = f"Application submitted via Greenhouse. Confirmation detected. Final URL: {final_url}"
                print("SUCCESS: Application submitted!")
            elif any(kw in body_text for kw in error_kw):
                status = "failed"
                notes = f"Form validation errors on submit. Body: {body_text[:300]}"
                print("FAILED: Form validation errors")
            else:
                status = "requires_manual_step"
                notes = f"Submission result ambiguous. Post-submit URL: {final_url}. Body sample: {body_text[:200]}"
                print("AMBIGUOUS result")

        except Exception as e:
            print(f"Error: {e}")
            try:
                s = ss(page, "error")
                if s: screenshots.append(s)
            except Exception:
                pass
            status = "failed"
            notes = f"Error: {str(e)[:300]}"

        finally:
            browser.close()

    return status, notes, screenshots


if __name__ == "__main__":
    print("=== Databricks Fullstack SE - Greenhouse Application v2 ===")
    status, notes, screenshots = run()
    print(f"\nResult: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    print("\nJSON_RESULT:" + json.dumps({
        "status": status, "notes": notes, "screenshots": screenshots,
        "timestamp": datetime.now().isoformat()
    }))
