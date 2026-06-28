#!/usr/bin/env python3
"""
Apply to IXON Cloud Software Engineer position.
Full form-fill and submission with proxy and ignore_https_errors.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCREENSHOT_DIR = Path('/home/user/Agents/output/screenshots')
RESUME_PATH = Path('/home/user/Agents/profile/Hisham Abboud CV.pdf')
JOB_URL = 'https://ixonbv.recruitee.com/o/embedded-software-engineer'
APPLY_URL = 'https://ixonbv.recruitee.com/o/embedded-software-engineer/c/new'
APPLICATIONS_JSON = Path('/home/user/Agents/data/applications.json')

APPLICANT = {
    'name': 'Hisham Abboud',
    'email': 'hiaham123@hotmail.com',
    'phone': '+31 06 4841 2838',
}

def get_proxy_config():
    proxy_url = os.environ.get('HTTPS_PROXY', '') or os.environ.get('HTTP_PROXY', '')
    match = re.match(r'http://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if match:
        user, password, host, port = match.groups()
        return {'server': f'http://{host}:{port}', 'username': user, 'password': password}
    return None

def ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def screenshot(page, label):
    filename = f'ixon-{label}-{ts()}.png'
    filepath = SCREENSHOT_DIR / filename
    try:
        page.screenshot(path=str(filepath), full_page=True, timeout=30000)
        print(f'Screenshot: {filepath}')
        return str(filepath)
    except Exception as e:
        print(f'Full-page screenshot failed ({e}), trying viewport...')
        try:
            page.screenshot(path=str(filepath), timeout=30000)
            print(f'Viewport screenshot: {filepath}')
            return str(filepath)
        except Exception as e2:
            print(f'Screenshot failed: {e2}')
            return None

def log_application(status, notes, screenshots_list):
    try:
        APPLICATIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
        data = []
        if APPLICATIONS_JSON.exists():
            with open(APPLICATIONS_JSON) as f:
                data = json.load(f)

        # Skip if already successfully applied
        for app in data:
            if app.get('url') == JOB_URL and app.get('status') == 'applied':
                print('Already applied - skipping log update')
                return

        # Remove previous entries for this job
        data = [a for a in data if a.get('url') != JOB_URL]

        entry = {
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
        data.append(entry)

        with open(APPLICATIONS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'Logged: {status}')
    except Exception as e:
        print(f'Logging error: {e}')

def main():
    screenshots = []
    proxy = get_proxy_config()
    print(f'Proxy: {proxy["server"] if proxy else "none"}')

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to the application form
            print(f'\n[1] Navigating to application form: {APPLY_URL}')
            page.goto(APPLY_URL, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(5000)
            print(f'URL: {page.url}')
            print(f'Title: {page.title()}')

            ss = screenshot(page, '01-application-form')
            screenshots.append(ss)

            # Step 2: Fill Full Name
            print('\n[2] Filling Full Name...')
            name_input = page.locator('input[name="candidate.name"]').first
            name_input.wait_for(timeout=5000, state='visible')
            name_input.fill(APPLICANT['name'])
            print(f'  Name: {APPLICANT["name"]}')

            # Step 3: Fill Email
            print('\n[3] Filling Email...')
            email_input = page.locator('input[name="candidate.email"]').first
            email_input.wait_for(timeout=5000, state='visible')
            email_input.fill(APPLICANT['email'])
            print(f'  Email: {APPLICANT["email"]}')

            # Step 4: Fill Phone
            print('\n[4] Filling Phone...')
            phone_input = page.locator('input[name="candidate.phone"]').first
            phone_input.wait_for(timeout=5000, state='visible')
            phone_input.fill(APPLICANT['phone'])
            print(f'  Phone: {APPLICANT["phone"]}')

            # Step 5: Check country (Netherlands should be pre-selected based on page inspection)
            print('\n[5] Checking country field...')
            try:
                country_select = page.locator('select[name*="country" i]').first
                country_select.wait_for(timeout=2000, state='visible')
                country_select.select_option(label='Netherlands')
                print('  Country: Netherlands selected')
            except Exception:
                # Country may be a different type of input or already set
                try:
                    country_input = page.locator('input[name*="country" i]').first
                    country_input.wait_for(timeout=2000, state='visible')
                    val = country_input.input_value()
                    print(f'  Country input value: {val}')
                except Exception:
                    print('  Country field not found (may be pre-filled)')

            # Step 6: Upload CV
            print('\n[6] Uploading CV...')
            if RESUME_PATH.exists():
                cv_input = page.locator('input[name="candidate.cv"]').first
                cv_input.wait_for(timeout=5000)
                cv_input.set_input_files(str(RESUME_PATH))
                print(f'  CV uploaded: {RESUME_PATH.name}')
                page.wait_for_timeout(2000)
            else:
                print(f'  CV not found at: {RESUME_PATH}')

            # Step 7: Screenshot of filled form
            print('\n[7] Taking form screenshot...')
            ss = screenshot(page, '02-form-filled')
            screenshots.append(ss)

            # Step 8: Pre-submit screenshot
            print('\n[8] Pre-submit screenshot...')
            ss = screenshot(page, '03-pre-submit')
            screenshots.append(ss)

            # Step 9: Find and click the Submit/Send button
            print('\n[9] Looking for submit button...')
            all_buttons = page.locator('button').all()
            print(f'  Found {len(all_buttons)} buttons:')
            for btn in all_buttons:
                try:
                    txt = btn.text_content() or ''
                    btype = btn.get_attribute('type') or ''
                    bclass = btn.get_attribute('class') or ''
                    print(f'    "{txt.strip()}" | type={btype} | class={bclass[:50]}')
                except Exception:
                    pass

            # Try to click the submit button
            submitted = False
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Send application")',
                'button:has-text("Verstuur")',
                'button:has-text("Solliciteer")',
                'button:has-text("Save")',
            ]

            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=2000, state='visible')
                    txt = btn.text_content() or ''
                    print(f'  Submit button found: "{txt.strip()}" via {sel}')
                    btn.click()
                    print('  Clicked submit!')
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                print('  No submit button found by selectors')
                # Try finding any button with "submit" in its attributes
                try:
                    submit_btn = page.locator('[data-cy*="submit"], [class*="submit"], [id*="submit"]').first
                    submit_btn.wait_for(timeout=2000, state='visible')
                    txt = submit_btn.text_content() or ''
                    print(f'  Found by data-cy/class: "{txt.strip()}"')
                    submit_btn.click()
                    submitted = True
                except Exception:
                    pass

            # Step 10: Wait and capture confirmation
            print('\n[10] Waiting for confirmation...')
            page.wait_for_timeout(6000)

            ss = screenshot(page, '04-post-submit')
            screenshots.append(ss)

            # Check result
            final_url = page.url
            print(f'\nFinal URL: {final_url}')

            try:
                final_text = page.locator('body').inner_text(timeout=5000)
                print(f'Page text: {final_text[:600]}')
            except Exception:
                final_text = ''

            success_kw = [
                'successfully submitted', 'thank you', 'application received',
                'bedankt', 'success', 'your application has been',
                'we received', 'will be in touch'
            ]
            if any(k in final_text.lower() for k in success_kw):
                print('\nSUCCESS: Application confirmed submitted!')
                log_application('applied', 'Application successfully submitted via Playwright', screenshots)
            elif not submitted:
                print('\nSKIPPED: Submit button not found')
                log_application('skipped', 'Form filled but submit button not located', screenshots)
            else:
                print('\nSubmit clicked - check screenshots for confirmation')
                log_application('applied', 'Submit button clicked - verify in screenshots', screenshots)

        except Exception as e:
            print(f'\nError: {e}')
            import traceback
            traceback.print_exc()
            try:
                ss = screenshot(page, '99-error')
                screenshots.append(ss)
            except Exception:
                pass
            log_application('failed', f'Error: {str(e)[:300]}', screenshots)

        finally:
            browser.close()
            print('\nBrowser closed.')
            valid = [s for s in screenshots if s]
            print(f'\nScreenshots ({len(valid)}):')
            for s in valid:
                print(f'  {s}')

if __name__ == '__main__':
    main()
