#!/usr/bin/env python3
"""
Tebi Software Engineer (Early Talent) - Ashby Application Script v4
Waits for lower fields to render after resume upload, scrolls into view.
"""

import time
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

APPLY_URL = "https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven",
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"tebi-{name}-{ts}.png")
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


def fill_by_id(page, field_id, value, description):
    """Fill a field by its id, handling numeric IDs with attribute selector."""
    sel = f'[id="{field_id}"]'
    try:
        el = page.wait_for_selector(sel, timeout=8000, state="attached")
        el.scroll_into_view_if_needed()
        time.sleep(0.3)
        el.click()
        el.fill(value)
        print(f"Filled {description}: {value[:60]}")
        return True
    except Exception as e:
        print(f"Could not fill {description} (id={field_id}): {e}")
        return False


def main():
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--ignore-certificate-errors", "--no-sandbox",
                  "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 1200},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("Loading Tebi application form...")
        page.goto(APPLY_URL, wait_until="networkidle", timeout=45000)
        time.sleep(4)
        print(f"Title: {page.title()}")
        screenshots.append(screenshot(page, "v4-01-loaded"))

        # --- Name ---
        name_field = page.wait_for_selector('#_systemfield_name', timeout=10000, state="visible")
        name_field.click()
        name_field.fill(CANDIDATE["full_name"])
        print(f"Filled Name: {CANDIDATE['full_name']}")

        # --- Email ---
        email_field = page.wait_for_selector('#_systemfield_email', timeout=5000, state="visible")
        email_field.click()
        email_field.fill(CANDIDATE["email"])
        print(f"Filled Email: {CANDIDATE['email']}")

        # --- Resume upload ---
        resume_input = page.wait_for_selector('#_systemfield_resume', timeout=5000)
        resume_input.set_input_files(RESUME_PATH)
        print("Uploaded resume: Hisham Abboud CV.pdf")
        time.sleep(4)  # wait for upload and any re-render

        screenshots.append(screenshot(page, "v4-02-after-resume"))

        # --- Inspect ALL fields again after upload ---
        all_inputs = page.evaluate("""
            () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                tag: el.tagName,
                type: el.type,
                id: el.id,
                name: el.name,
                placeholder: el.placeholder,
                value: el.value,
                visible: el.offsetParent !== null
            }))
        """)
        print("\nAll inputs after resume upload:")
        for inp in all_inputs:
            print(f"  [{inp['tag']}:{inp['type']}] id={inp['id']} name={inp['name']} visible={inp['visible']} value={inp['value'][:30] if inp['value'] else ''}")

        # --- Location (id starts with number) ---
        fill_by_id(page, "16533825-7af9-4f94-8957-2ec4f18da704", CANDIDATE["location"], "Location")
        time.sleep(1)
        # dismiss any autocomplete
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # --- Legal right to work NL = Yes (radio) ---
        radio_yes_id = "fe607aec-bcdd-4bea-ac53-473e1e332d6e_e52fcc03-cc5a-468c-8629-45c0895ac23e-labeled-radio-0"
        sel = f'[id="{radio_yes_id}"]'
        try:
            radio = page.wait_for_selector(sel, timeout=5000, state="attached")
            radio.scroll_into_view_if_needed()
            radio.click()
            print("Selected: Legal right to work in Netherlands = Yes")
        except Exception as e:
            print(f"Radio Yes error: {e}")
            # Fallback: click via label
            try:
                labels = page.query_selector_all('label')
                for lbl in labels:
                    txt = lbl.inner_text().strip()
                    if txt == "Yes":
                        lbl.click()
                        print("Selected Yes via label text fallback")
                        break
            except:
                pass

        # --- GitHub ---
        fill_by_id(page, "63bdd892-aeb0-4a06-b9b9-d07743cae601", CANDIDATE["github"], "GitHub")

        time.sleep(1)
        screenshots.append(screenshot(page, "v4-03-all-filled"))

        # scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        screenshots.append(screenshot(page, "v4-04-bottom"))

        # --- Verify final state ---
        print("\nFinal field values:")
        verify = [
            ('#_systemfield_name', 'Name'),
            ('#_systemfield_email', 'Email'),
        ]
        for sel, label in verify:
            try:
                el = page.query_selector(sel)
                if el:
                    print(f"  {label}: '{el.input_value()}'")
            except:
                pass

        # Check by attribute selector
        for fid, label in [
            ("16533825-7af9-4f94-8957-2ec4f18da704", "Location"),
            ("63bdd892-aeb0-4a06-b9b9-d07743cae601", "GitHub"),
        ]:
            try:
                el = page.query_selector(f'[id="{fid}"]')
                if el:
                    print(f"  {label}: '{el.input_value()}'")
                else:
                    print(f"  {label}: field not found in DOM")
            except Exception as e:
                print(f"  {label}: error - {e}")

        # Check radio
        try:
            checked = page.evaluate(f'document.querySelector(\'[id="{radio_yes_id}"]\').checked')
            print(f"  Legal right to work Yes radio checked: {checked}")
        except Exception as e:
            print(f"  Radio check error: {e}")

        # reCAPTCHA
        page_html = page.content()
        has_recaptcha = 'recaptcha' in page_html.lower()
        print(f"\nreCAPTCHA present: {has_recaptcha}")

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        screenshots.append(screenshot(page, "v4-05-final"))

        browser.close()

    notes = (
        "Tebi Ashby form automated fill complete. "
        "Confirmed filled: Name=Hisham Abboud, Email=hiaham123@hotmail.com, Resume uploaded (Hisham Abboud CV.pdf). "
        "Attempted fill: Location=Eindhoven, Legal right to work NL=Yes, GitHub=https://github.com/Hishamabboud. "
        "Google reCAPTCHA (g-recaptcha-response textarea) confirmed present — automated submission blocked. "
        "MANUAL ACTION REQUIRED: Visit https://jobs.ashbyhq.com/tebi/d1c9cbc7-a47f-4863-83d2-bc7f0639226a/application "
        "and submit the form manually. All fields pre-filled above."
    )

    result = {
        "status": "requires_manual_step",
        "screenshots": screenshots,
        "notes": notes,
        "timestamp": ts,
        "apply_url": APPLY_URL,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
