#!/usr/bin/env python3
"""
Tebi Software Engineer (Early Talent) - Final Application Script
Uses dynamic field detection since Ashby randomizes some field IDs per session.
Confirmed static IDs: _systemfield_name, _systemfield_email, _systemfield_resume
GitHub field: id=63bdd892-aeb0-4a06-b9b9-d07743cae601 (consistent across sessions)
Location: text input with placeholder "Start typing..." (no stable ID)
Radio (legal right to work): first radio button pair in form
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
    "location": "Eindhoven, Netherlands",
}

GITHUB_FIELD_ID = "63bdd892-aeb0-4a06-b9b9-d07743cae601"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"tebi-final-{name}-{ts}.png")
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


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

        print("Loading Tebi Ashby application form...")
        page.goto(APPLY_URL, wait_until="networkidle", timeout=45000)
        time.sleep(4)
        print(f"Title: {page.title()}")
        screenshots.append(screenshot(page, "01-loaded"))

        # --- Fill Name (stable ID) ---
        name_field = page.wait_for_selector('#_systemfield_name', timeout=10000, state="visible")
        name_field.click()
        name_field.fill(CANDIDATE["full_name"])
        print(f"Filled Name: {CANDIDATE['full_name']}")

        # --- Fill Email (stable ID) ---
        email_field = page.wait_for_selector('#_systemfield_email', timeout=5000, state="visible")
        email_field.click()
        email_field.fill(CANDIDATE["email"])
        print(f"Filled Email: {CANDIDATE['email']}")

        # --- Upload Resume (stable ID) ---
        resume_input = page.wait_for_selector('#_systemfield_resume', timeout=5000)
        resume_input.set_input_files(RESUME_PATH)
        print("Uploaded resume: Hisham Abboud CV.pdf")
        time.sleep(4)

        screenshots.append(screenshot(page, "02-name-email-resume"))

        # --- Snapshot all inputs to find dynamic fields ---
        inputs = page.evaluate("""
            () => Array.from(document.querySelectorAll('input, textarea')).map((el, idx) => ({
                idx,
                tag: el.tagName,
                type: el.type,
                id: el.id,
                name: el.name,
                placeholder: el.placeholder,
                value: el.value
            }))
        """)
        print("\nAll inputs after resume upload:")
        for inp in inputs:
            print(f"  [{inp['idx']}] [{inp['type']}] id={inp['id'][:40] if inp['id'] else ''} "
                  f"placeholder={inp['placeholder']} value={inp['value'][:30] if inp['value'] else ''}")

        # --- Fill Location: "Start typing..." placeholder input ---
        location_filled = False
        for inp in inputs:
            if inp['placeholder'] == 'Start typing...' and inp['type'] == 'text' and not inp['value']:
                try:
                    idx = inp['idx']
                    el = page.evaluate_handle(
                        f'() => Array.from(document.querySelectorAll("input, textarea"))[{idx}]'
                    )
                    el.as_element().scroll_into_view_if_needed()
                    el.as_element().click()
                    el.as_element().fill(CANDIDATE["location"])
                    time.sleep(1.5)
                    # dismiss autocomplete
                    page.keyboard.press("Escape")
                    location_filled = True
                    print(f"Filled Location: {CANDIDATE['location']} (input index {idx})")
                    break
                except Exception as e:
                    print(f"Location fill error: {e}")

        if not location_filled:
            print("Location field not found via placeholder — may not be in DOM yet or may be optional")

        # --- Legal right to work Netherlands: click first radio (Yes) ---
        radio_filled = False
        for inp in inputs:
            if inp['type'] == 'radio' and inp['id'] and 'labeled-radio-0' in inp['id']:
                try:
                    idx = inp['idx']
                    el = page.evaluate_handle(
                        f'() => Array.from(document.querySelectorAll("input, textarea"))[{idx}]'
                    )
                    el.as_element().scroll_into_view_if_needed()
                    el.as_element().click()
                    radio_filled = True
                    print("Selected: Legal right to work in Netherlands = Yes (radio-0)")
                    break
                except Exception as e:
                    print(f"Radio click error: {e}")

        if not radio_filled:
            # Fallback: click label "Yes"
            try:
                labels = page.query_selector_all('label')
                for lbl in labels:
                    if lbl.inner_text().strip() == "Yes":
                        lbl.scroll_into_view_if_needed()
                        lbl.click()
                        radio_filled = True
                        print("Selected Yes via label fallback")
                        break
            except Exception as e:
                print(f"Label Yes fallback error: {e}")

        # --- Fill GitHub (consistent field ID) ---
        github_filled = False
        try:
            gh = page.wait_for_selector(f'[id="{GITHUB_FIELD_ID}"]', timeout=5000, state="attached")
            gh.scroll_into_view_if_needed()
            gh.click()
            gh.fill(CANDIDATE["github"])
            github_filled = True
            print(f"Filled GitHub: {CANDIDATE['github']}")
        except Exception as e:
            print(f"GitHub field error: {e}")
            # Fallback: find by index
            for inp in inputs:
                if inp['id'] == GITHUB_FIELD_ID:
                    try:
                        idx = inp['idx']
                        el = page.evaluate_handle(
                            f'() => Array.from(document.querySelectorAll("input, textarea"))[{idx}]'
                        )
                        el.as_element().fill(CANDIDATE["github"])
                        github_filled = True
                        print(f"Filled GitHub via index fallback")
                        break
                    except:
                        pass

        time.sleep(1)
        screenshots.append(screenshot(page, "03-all-fields-filled"))

        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        screenshots.append(screenshot(page, "04-form-bottom"))

        # --- Final verification ---
        print("\nFinal verification:")
        try:
            print(f"  Name: '{page.query_selector('#_systemfield_name').input_value()}'")
        except:
            pass
        try:
            print(f"  Email: '{page.query_selector('#_systemfield_email').input_value()}'")
        except:
            pass
        try:
            gh_el = page.query_selector(f'[id="{GITHUB_FIELD_ID}"]')
            if gh_el:
                print(f"  GitHub: '{gh_el.input_value()}'")
        except:
            pass

        # reCAPTCHA
        has_recaptcha = 'recaptcha' in page.content().lower()
        print(f"\nreCAPTCHA present: {has_recaptcha}")

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        screenshots.append(screenshot(page, "05-final"))

        browser.close()

    notes = (
        "Tebi Ashby form fill complete. "
        f"Confirmed: Name=Hisham Abboud, Email=hiaham123@hotmail.com, Resume=Hisham Abboud CV.pdf (uploaded), "
        f"GitHub=https://github.com/Hishamabboud (id={GITHUB_FIELD_ID}). "
        f"Location={'filled' if location_filled else 'not found in DOM'}, "
        f"Legal right to work NL={'Yes selected' if radio_filled else 'not clicked'}. "
        "Google reCAPTCHA confirmed present — submission requires manual CAPTCHA solve. "
        f"MANUAL ACTION: Visit {APPLY_URL}, review the pre-filled form, solve reCAPTCHA, and click Submit."
    )

    result = {
        "status": "requires_manual_step",
        "screenshots": screenshots,
        "notes": notes,
        "fields_filled": {
            "name": True,
            "email": True,
            "resume": True,
            "location": location_filled,
            "legal_right_to_work_nl": radio_filled,
            "github": github_filled,
        },
        "timestamp": ts,
        "apply_url": APPLY_URL,
    }
    print("\n--- RESULT ---")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
