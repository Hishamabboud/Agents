#!/usr/bin/env python3
"""
Apply to IXON Cloud Software Engineer position via Playwright browser automation.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCREENSHOT_DIR = Path('/home/user/Agents/output/screenshots')
RESUME_PATH = Path('/home/user/Agents/profile/Hisham Abboud CV.pdf')
JOB_URL = 'https://ixonbv.recruitee.com/o/embedded-software-engineer'
APPLICATIONS_JSON = Path('/home/user/Agents/data/applications.json')

APPLICANT = {
    'name': 'Hisham Abboud',
    'email': 'hiaham123@hotmail.com',
    'phone': '+31 06 4841 2838',
    'location': 'Eindhoven, Netherlands',
}

def ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def screenshot(page, label):
    filename = f'ixon-{label}-{ts()}.png'
    filepath = SCREENSHOT_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    print(f'Screenshot saved: {filepath}')
    return str(filepath)

def try_fill(page, selectors, value, field_name):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(timeout=3000)
            el.fill(value)
            print(f'Filled {field_name} using selector: {sel}')
            return True
        except Exception:
            continue
    print(f'Could not fill {field_name}')
    return False

def log_application(status, notes, screenshots):
    try:
        if APPLICATIONS_JSON.exists():
            with open(APPLICATIONS_JSON) as f:
                data = json.load(f)
        else:
            data = []

        # Check if already applied
        for app in data:
            if app.get('url') == JOB_URL:
                print('Already applied to this job, skipping log update')
                return

        app_entry = {
            'id': f'ixon-software-engineer-{ts()}',
            'company': 'IXON Cloud',
            'role': 'Software Engineer',
            'url': JOB_URL,
            'date_applied': datetime.now().isoformat(),
            'score': 7.7,
            'status': status,
            'resume_file': str(RESUME_PATH),
            'cover_letter_file': None,
            'screenshots': screenshots,
            'notes': notes,
            'response': None,
        }
        data.append(app_entry)

        APPLICATIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(APPLICATIONS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'Application logged: {status}')
    except Exception as e:
        print(f'Error logging application: {e}')

def main():
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to job page
            print(f'Navigating to: {JOB_URL}')
            page.goto(JOB_URL, wait_until='networkidle', timeout=30000)
            ss = screenshot(page, '01-job-page')
            screenshots.append(ss)

            # Inspect page for form fields
            print('\n--- Page inspection ---')
            inputs = page.locator('input').all()
            print(f'Found {len(inputs)} input(s) on initial page')
            for inp in inputs:
                try:
                    print(f'  Input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            # Step 2: Look for Apply button and click it
            print('\n--- Looking for Apply button ---')
            apply_clicked = False
            apply_selectors = [
                'a:has-text("Apply")',
                'button:has-text("Apply")',
                'a[href*="apply"]',
                '.apply-button',
                '[data-qa="apply-button"]',
                'text=Apply for this job',
                'text=Apply now',
            ]
            for sel in apply_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=3000)
                    print(f'Found apply button with: {sel}')
                    btn.click()
                    page.wait_for_timeout(2000)
                    apply_clicked = True
                    ss = screenshot(page, '02-after-apply-click')
                    screenshots.append(ss)
                    break
                except Exception:
                    continue

            if not apply_clicked:
                print('No apply button found, form may be embedded on page')
                # Scroll to bottom to see embedded form
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                ss = screenshot(page, '02-scrolled')
                screenshots.append(ss)

            print(f'\nCurrent URL: {page.url}')

            # Re-inspect inputs after clicking apply
            inputs = page.locator('input').all()
            print(f'Found {len(inputs)} input(s) after apply click')
            for inp in inputs:
                try:
                    print(f'  Input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            # Check for CAPTCHA
            page_content = page.content()
            if 'captcha' in page_content.lower() or 'recaptcha' in page_content.lower():
                print('CAPTCHA detected - marking as failed')
                ss = screenshot(page, '99-captcha')
                screenshots.append(ss)
                log_application('failed', 'CAPTCHA detected during application', screenshots)
                return

            # Check if we need to create an account
            if 'sign up' in page_content.lower() or 'create account' in page_content.lower() or 'register' in page_content.lower():
                print('Account creation required - checking if it blocks application')

            # Step 3: Fill the form
            print('\n--- Filling form fields ---')

            # Name
            try_fill(page, [
                'input[name="name"]',
                'input[name="full_name"]',
                'input[name="candidate[name]"]',
                'input[placeholder*="name" i]',
                'input[autocomplete="name"]',
                'input[id="name"]',
                'input[id*="name" i]',
            ], APPLICANT['name'], 'name')

            # Email
            try_fill(page, [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="candidate[email]"]',
                'input[placeholder*="email" i]',
                'input[id="email"]',
                'input[id*="email" i]',
            ], APPLICANT['email'], 'email')

            # Phone
            try_fill(page, [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="candidate[phone]"]',
                'input[placeholder*="phone" i]',
                'input[id="phone"]',
                'input[id*="phone" i]',
            ], APPLICANT['phone'], 'phone')

            # Country selection
            country_selectors = [
                'select[name="country"]',
                'select[id="country"]',
                'select[name="candidate[country]"]',
                'select[id*="country" i]',
            ]
            for sel in country_selectors:
                try:
                    el = page.locator(sel).first
                    el.wait_for(timeout=2000)
                    el.select_option(label='Netherlands')
                    print(f'Selected country using: {sel}')
                    break
                except Exception:
                    continue

            # Step 4: Upload resume
            print('\n--- Uploading resume ---')
            if RESUME_PATH.exists():
                file_input_selectors = [
                    'input[type="file"]',
                    'input[accept*="pdf"]',
                    'input[name="resume"]',
                    'input[name="cv"]',
                    'input[name="candidate[resume]"]',
                ]
                for sel in file_input_selectors:
                    try:
                        file_input = page.locator(sel).first
                        file_input.wait_for(timeout=2000)
                        file_input.set_input_files(str(RESUME_PATH))
                        print(f'Resume uploaded using: {sel}')
                        page.wait_for_timeout(2000)
                        break
                    except Exception:
                        continue
            else:
                print(f'Resume not found at: {RESUME_PATH}')

            ss = screenshot(page, '03-form-filled-with-resume')
            screenshots.append(ss)

            # Step 5: Screenshot before submit
            ss = screenshot(page, '04-pre-submit')
            screenshots.append(ss)

            # Step 6: Find and click submit button
            print('\n--- Submitting application ---')
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Send application")',
                '.submit-button',
                '[data-qa="submit"]',
            ]

            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=2000)
                    btn_text = btn.text_content() or 'unknown'
                    print(f'Found submit button: "{btn_text.strip()}" with selector: {sel}')
                    btn.click()
                    print('Clicked submit button!')
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                print('Could not find submit button')
                ss = screenshot(page, '05-no-submit-button')
                screenshots.append(ss)

            # Wait for response
            page.wait_for_timeout(4000)
            ss = screenshot(page, '06-post-submit')
            screenshots.append(ss)

            # Step 7: Check for confirmation
            final_content = page.content()
            final_url = page.url

            print(f'\nFinal URL: {final_url}')

            if any(kw in final_content.lower() for kw in ['successfully submitted', 'thank you', 'application received', 'we\'ll be in touch', 'bedankt']):
                print('SUCCESS: Application confirmed submitted!')
                log_application('applied', 'Application submitted successfully via Playwright automation', screenshots)
            elif not submitted:
                print('SKIPPED: Could not find the submit button')
                log_application('skipped', 'Could not find submit button on form', screenshots)
            else:
                print('Status unclear - may have been submitted, check screenshots')
                log_application('applied', 'Submit button clicked, confirmation unclear - check screenshots', screenshots)

        except PlaywrightTimeoutError as e:
            print(f'Timeout error: {e}')
            try:
                ss = screenshot(page, '99-timeout-error')
                screenshots.append(ss)
            except Exception:
                pass
            log_application('failed', f'Timeout during application: {str(e)[:200]}', screenshots)

        except Exception as e:
            print(f'Unexpected error: {e}')
            try:
                ss = screenshot(page, '99-unexpected-error')
                screenshots.append(ss)
            except Exception:
                pass
            log_application('failed', f'Unexpected error: {str(e)[:200]}', screenshots)

        finally:
            browser.close()
            print('\nBrowser closed.')
            print(f'\nScreenshots taken:')
            for ss in screenshots:
                print(f'  {ss}')

if __name__ == '__main__':
    main()
