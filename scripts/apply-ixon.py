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
    try:
        page.screenshot(path=str(filepath), full_page=True, timeout=20000)
        print(f'Screenshot saved: {filepath}')
        return str(filepath)
    except Exception as e:
        print(f'Full-page screenshot failed ({e}), trying viewport...')
        try:
            page.screenshot(path=str(filepath), timeout=20000)
            print(f'Viewport screenshot saved: {filepath}')
            return str(filepath)
        except Exception as e2:
            print(f'Viewport screenshot also failed: {e2}')
            return None

def try_fill(page, selectors, value, field_name):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(timeout=3000, state='visible')
            el.fill(value)
            print(f'Filled {field_name} using selector: {sel}')
            return True
        except Exception:
            continue
    print(f'Could not fill {field_name}')
    return False

def load_applications():
    if APPLICATIONS_JSON.exists():
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    return []

def log_application(status, notes, screenshots_list):
    try:
        data = load_applications()

        # Check if already applied successfully
        for app in data:
            if app.get('url') == JOB_URL and app.get('status') == 'applied':
                print('Already applied to this job successfully, skipping')
                return

        # Remove previous failed/skipped entries for this job
        data = [a for a in data if a.get('url') != JOB_URL]

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
            'screenshots': [s for s in screenshots_list if s],
            'notes': notes,
            'response': None,
        }
        data.append(app_entry)

        APPLICATIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(APPLICATIONS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'Application logged with status: {status}')
    except Exception as e:
        print(f'Error logging application: {e}')

def main():
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to job page
            print(f'Navigating to: {JOB_URL}')
            try:
                response = page.goto(JOB_URL, wait_until='domcontentloaded', timeout=30000)
                print(f'Page loaded with status: {response.status if response else "unknown"}')
            except PlaywrightTimeoutError:
                print('Navigation timed out, but continuing...')

            # Wait for JS to render
            print('Waiting for JS to render...')
            page.wait_for_timeout(5000)
            print(f'Current URL: {page.url}')

            # Try to wait for the body to have content
            try:
                page.wait_for_selector('body', timeout=10000)
                print('Body is available')
            except Exception as e:
                print(f'Body wait failed: {e}')

            ss = screenshot(page, '01-job-page')
            screenshots.append(ss)

            # Get page title and some content info
            try:
                title = page.title()
                print(f'Page title: {title}')
            except Exception:
                pass

            # Inspect page for form fields
            print('\n--- Page inspection ---')
            inputs = page.locator('input').all()
            print(f'Found {len(inputs)} input(s) on initial page')
            for inp in inputs:
                try:
                    print(f'  Input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            # Check for CAPTCHA
            try:
                page_text = page.inner_text('body')
                print(f'Page text preview: {page_text[:500]}')
            except Exception as e:
                print(f'Could not get body text: {e}')
                page_text = ''

            if 'captcha' in page_text.lower():
                print('CAPTCHA detected - marking as failed')
                ss = screenshot(page, '99-captcha')
                screenshots.append(ss)
                log_application('failed', 'CAPTCHA detected during application', screenshots)
                return

            # Step 2: Look for Apply button
            print('\n--- Looking for Apply button ---')
            apply_clicked = False
            apply_selectors = [
                'a:has-text("Apply")',
                'button:has-text("Apply")',
                '[class*="apply"]',
                'a[href*="apply"]',
                'text=Apply for this job',
                'text=Apply now',
                'a:has-text("Solliciteer")',
                'button:has-text("Solliciteer")',
            ]
            for sel in apply_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=3000, state='visible')
                    btn_text = btn.text_content() or ''
                    print(f'Found apply button "{btn_text.strip()}" with: {sel}')
                    btn.click()
                    page.wait_for_timeout(4000)
                    apply_clicked = True
                    ss = screenshot(page, '02-after-apply-click')
                    screenshots.append(ss)
                    break
                except Exception:
                    continue

            if not apply_clicked:
                print('No apply button found by text, scrolling to look for embedded form...')
                try:
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                except Exception:
                    pass
                page.wait_for_timeout(1000)
                ss = screenshot(page, '02-scrolled')
                screenshots.append(ss)

            print(f'\nCurrent URL after apply attempt: {page.url}')

            # Re-inspect inputs
            inputs = page.locator('input').all()
            print(f'Found {len(inputs)} input(s) after apply attempt')
            for inp in inputs:
                try:
                    print(f'  Input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            # List buttons
            buttons = page.locator('button').all()
            print(f'Found {len(buttons)} button(s)')
            for btn in buttons[:15]:
                try:
                    print(f'  Button: text="{btn.text_content()}" type={btn.get_attribute("type")} class={btn.get_attribute("class")}')
                except Exception:
                    pass

            # List links
            links = page.locator('a').all()
            print(f'Found {len(links)} link(s)')
            for lnk in links[:20]:
                try:
                    href = lnk.get_attribute('href') or ''
                    txt = lnk.text_content() or ''
                    if txt.strip():
                        print(f'  Link: text="{txt.strip()[:50]}" href="{href[:80]}"')
                except Exception:
                    pass

            # Step 3: Fill the form
            print('\n--- Filling form fields ---')

            name_filled = try_fill(page, [
                'input[name="name"]',
                'input[name="full_name"]',
                'input[name="candidate[name]"]',
                'input[placeholder*="name" i]',
                'input[placeholder*="naam" i]',
                'input[autocomplete="name"]',
                'input[id="name"]',
                'input[id*="name" i]',
            ], APPLICANT['name'], 'name')

            email_filled = try_fill(page, [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="candidate[email]"]',
                'input[placeholder*="email" i]',
                'input[id="email"]',
                'input[id*="email" i]',
            ], APPLICANT['email'], 'email')

            phone_filled = try_fill(page, [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="candidate[phone]"]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="telefoon" i]',
                'input[id="phone"]',
                'input[id*="phone" i]',
            ], APPLICANT['phone'], 'phone')

            # Country selection
            for sel in ['select[name="country"]', 'select[id="country"]', 'select[id*="country" i]']:
                try:
                    el = page.locator(sel).first
                    el.wait_for(timeout=2000, state='visible')
                    el.select_option(label='Netherlands')
                    print(f'Selected country using: {sel}')
                    break
                except Exception:
                    continue

            # Step 4: Upload resume
            print('\n--- Uploading resume ---')
            resume_uploaded = False
            if RESUME_PATH.exists():
                for sel in ['input[type="file"]', 'input[accept*="pdf"]', 'input[name="resume"]', 'input[name="cv"]']:
                    try:
                        file_input = page.locator(sel).first
                        file_input.wait_for(timeout=2000)
                        file_input.set_input_files(str(RESUME_PATH))
                        print(f'Resume uploaded using: {sel}')
                        page.wait_for_timeout(2000)
                        resume_uploaded = True
                        break
                    except Exception:
                        continue
                if not resume_uploaded:
                    print('Could not find file input for resume')
            else:
                print(f'Resume not found at: {RESUME_PATH}')

            ss = screenshot(page, '03-form-filled')
            screenshots.append(ss)

            ss = screenshot(page, '04-pre-submit')
            screenshots.append(ss)

            # Step 5: Submit
            print('\n--- Submitting application ---')
            submitted = False
            for sel in [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Send application")',
                'button:has-text("Verstuur")',
                'button:has-text("Solliciteer")',
                '.submit-button',
            ]:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=2000, state='visible')
                    btn_text = btn.text_content() or 'unknown'
                    print(f'Found submit button: "{btn_text.strip()}" with: {sel}')
                    btn.click()
                    print('Clicked submit!')
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                print('Could not find submit button')
                # Try to print form HTML for debugging
                try:
                    form_html = page.locator('form').first.inner_html()
                    print('Form HTML:')
                    print(form_html[:3000])
                except Exception:
                    pass

            page.wait_for_timeout(5000)
            ss = screenshot(page, '06-post-submit')
            screenshots.append(ss)

            # Check confirmation
            try:
                final_text = page.inner_text('body')
            except Exception:
                final_text = ''
            final_url = page.url

            print(f'\nFinal URL: {final_url}')
            print(f'Page text after submit: {final_text[:300]}')

            success_keywords = [
                'successfully submitted', 'thank you', 'application received',
                "we'll be in touch", 'bedankt', 'success', 'your application has been'
            ]
            if any(kw in final_text.lower() for kw in success_keywords):
                print('SUCCESS: Application confirmed submitted!')
                log_application('applied', 'Application submitted successfully via Playwright automation', screenshots)
            elif not submitted:
                form_found = name_filled or email_filled or phone_filled
                if not form_found:
                    print('SKIPPED: No application form found on page')
                    log_application('skipped', 'No application form found - may require account creation or use external system', screenshots)
                else:
                    print('SKIPPED: Form found but could not submit')
                    log_application('skipped', 'Form fields filled but submit button not found', screenshots)
            else:
                print('Submit clicked - checking screenshots for confirmation')
                log_application('applied', 'Submit button clicked - verify confirmation in screenshots', screenshots)

        except Exception as e:
            print(f'Unexpected error: {e}')
            import traceback
            traceback.print_exc()
            try:
                ss = screenshot(page, '99-error')
                screenshots.append(ss)
            except Exception:
                pass
            log_application('failed', f'Error during application: {str(e)[:300]}', screenshots)

        finally:
            browser.close()
            print('\nBrowser closed.')
            valid_screenshots = [s for s in screenshots if s]
            print(f'\nScreenshots taken ({len(valid_screenshots)}):')
            for ss in valid_screenshots:
                print(f'  {ss}')

if __name__ == '__main__':
    main()
