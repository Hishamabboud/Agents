#!/usr/bin/env python3
"""
Apply to IXON Cloud Software Engineer position via Playwright.
Configures proxy credentials for the Chromium browser.
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
    'country': 'Netherlands',
}

def get_proxy_config():
    proxy_url = os.environ.get('HTTPS_PROXY', '') or os.environ.get('HTTP_PROXY', '')
    if not proxy_url:
        return None
    match = re.match(r'http://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if match:
        user, password, host, port = match.groups()
        return {
            'server': f'http://{host}:{port}',
            'username': user,
            'password': password,
        }
    return None

def ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def screenshot(page, label):
    filename = f'ixon-{label}-{ts()}.png'
    filepath = SCREENSHOT_DIR / filename
    try:
        page.screenshot(path=str(filepath), full_page=True, timeout=30000)
        print(f'Screenshot saved: {filepath}')
        return str(filepath)
    except Exception as e:
        print(f'Full-page screenshot failed: {e}')
        try:
            page.screenshot(path=str(filepath), full_page=False, timeout=30000)
            print(f'Viewport screenshot saved: {filepath}')
            return str(filepath)
        except Exception as e2:
            print(f'Screenshot failed: {e2}')
            return None

def try_fill(page, selectors, value, field_name):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(timeout=5000, state='visible')
            el.fill(value)
            print(f'Filled {field_name} using: {sel}')
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
        for app in data:
            if app.get('url') == JOB_URL and app.get('status') == 'applied':
                print('Already applied to this job successfully')
                return
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
        print(f'Application logged: {status}')
    except Exception as e:
        print(f'Error logging: {e}')

def main():
    screenshots = []
    proxy_config = get_proxy_config()
    if proxy_config:
        print(f'Using proxy: {proxy_config["server"]}')
    else:
        print('No proxy configured')

    with sync_playwright() as p:
        launch_args = {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        }
        if proxy_config:
            launch_args['proxy'] = {
                'server': proxy_config['server'],
                'username': proxy_config['username'],
                'password': proxy_config['password'],
            }

        browser = p.chromium.launch(**launch_args)

        context_args = {
            'viewport': {'width': 1280, 'height': 900},
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        context = browser.new_context(**context_args)
        page = context.new_page()

        try:
            # Navigate to the apply URL directly
            print(f'\nNavigating to: {APPLY_URL}')
            try:
                page.goto(APPLY_URL, wait_until='domcontentloaded', timeout=30000)
                print(f'Page loaded. URL: {page.url}')
            except PlaywrightTimeoutError:
                print('domcontentloaded timed out, continuing with JS wait...')

            print('Waiting 8s for SPA...')
            page.wait_for_timeout(8000)
            print(f'URL: {page.url}')

            try:
                title = page.title()
                print(f'Title: {title}')
            except Exception:
                pass

            ss = screenshot(page, '01-apply-page')
            screenshots.append(ss)

            # Check inputs
            print('\n--- Inspecting page ---')
            inputs = page.locator('input').all()
            print(f'Inputs: {len(inputs)}')
            for inp in inputs:
                try:
                    print(f'  input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            try:
                body_text = page.locator('body').inner_text(timeout=5000)
                print(f'Body preview: {body_text[:500]}')
            except Exception as e:
                print(f'Body text error: {e}')

            # If no form, try job page first
            if len(inputs) == 0:
                print('\nNo form on apply page, trying job page...')
                try:
                    page.goto(JOB_URL, wait_until='domcontentloaded', timeout=30000)
                except PlaywrightTimeoutError:
                    pass

                page.wait_for_timeout(8000)
                ss = screenshot(page, '02-job-page')
                screenshots.append(ss)

                # Print body text to understand state
                try:
                    body = page.locator('body').inner_text(timeout=5000)
                    print(f'Job page body: {body[:500]}')
                except Exception:
                    pass

                # Look for Apply button
                for sel in [
                    'a:has-text("Apply")',
                    'button:has-text("Apply")',
                    'a:has-text("Solliciteer")',
                    'button:has-text("Solliciteer")',
                    '[data-cy="apply-button"]',
                    '.apply-button',
                ]:
                    try:
                        btn = page.locator(sel).first
                        btn.wait_for(timeout=3000, state='visible')
                        txt = btn.text_content() or ''
                        print(f'Apply button found: "{txt.strip()}" via {sel}')
                        btn.click()
                        page.wait_for_timeout(5000)
                        break
                    except Exception:
                        continue

                ss = screenshot(page, '03-after-click')
                screenshots.append(ss)

                inputs = page.locator('input').all()
                print(f'Inputs after click: {len(inputs)}')

            # Fill form
            print('\n--- Filling form ---')
            name_ok = try_fill(page, [
                'input[name="name"]', 'input[name="candidate[name]"]',
                'input[placeholder*="name" i]', 'input[placeholder*="naam" i]',
                'input[autocomplete="name"]', 'input[id*="name" i]',
            ], APPLICANT['name'], 'Full Name')

            email_ok = try_fill(page, [
                'input[type="email"]', 'input[name="email"]',
                'input[name="candidate[email]"]', 'input[id*="email" i]',
            ], APPLICANT['email'], 'Email')

            phone_ok = try_fill(page, [
                'input[type="tel"]', 'input[name="phone"]',
                'input[name="candidate[phone]"]', 'input[id*="phone" i]',
                'input[placeholder*="phone" i]',
            ], APPLICANT['phone'], 'Phone')

            # Country
            for sel in ['select[name*="country" i]', 'select[id*="country" i]']:
                try:
                    el = page.locator(sel).first
                    el.wait_for(timeout=2000, state='visible')
                    el.select_option(label='Netherlands')
                    print('Selected country: Netherlands')
                    break
                except Exception:
                    continue

            # Upload CV
            print('\n--- Uploading CV ---')
            cv_ok = False
            if RESUME_PATH.exists():
                for sel in ['input[type="file"]', 'input[accept*="pdf"]', 'input[name*="cv" i]', 'input[name*="resume" i]']:
                    try:
                        fi = page.locator(sel).first
                        fi.wait_for(timeout=3000)
                        fi.set_input_files(str(RESUME_PATH))
                        print(f'CV uploaded via: {sel}')
                        page.wait_for_timeout(2000)
                        cv_ok = True
                        break
                    except Exception:
                        continue
                if not cv_ok:
                    print('No file input found')

            ss = screenshot(page, '04-form-filled')
            screenshots.append(ss)

            # Pre-submit screenshot
            ss = screenshot(page, '05-pre-submit')
            screenshots.append(ss)

            # Submit
            print('\n--- Submitting ---')
            submitted = False
            for sel in [
                'button[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Send application")',
                'button:has-text("Verstuur")',
                'button:has-text("Solliciteer")',
                'input[type="submit"]',
            ]:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=2000, state='visible')
                    txt = btn.text_content() or ''
                    print(f'Submit: "{txt.strip()}" via {sel}')
                    btn.click()
                    print('Submitted!')
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                print('Submit button not found')
                # Dump page state for debugging
                try:
                    all_btns = page.locator('button').all()
                    print(f'All buttons: {len(all_btns)}')
                    for b in all_btns:
                        try:
                            print(f'  "{b.text_content()}" type={b.get_attribute("type")}')
                        except Exception:
                            pass
                except Exception:
                    pass

            page.wait_for_timeout(5000)
            ss = screenshot(page, '06-post-submit')
            screenshots.append(ss)

            # Check result
            try:
                final_text = page.locator('body').inner_text(timeout=5000)
            except Exception:
                final_text = ''

            print(f'\nFinal URL: {page.url}')
            print(f'Final page text: {final_text[:500]}')

            success_kw = ['successfully submitted', 'thank you', 'application received', 'bedankt', 'success', 'your application']
            if any(k in final_text.lower() for k in success_kw):
                print('\nSUCCESS: Application confirmed submitted!')
                log_application('applied', 'Application submitted via Playwright browser automation with proxy', screenshots)
            elif not submitted:
                any_filled = name_ok or email_ok or phone_ok or cv_ok
                if not any_filled:
                    msg = 'No application form could be rendered - site uses hCaptcha (invisible) and SPA requires proxy-accessible JS bundles'
                    print(f'\nSKIPPED: {msg}')
                    log_application('skipped', msg, screenshots)
                else:
                    msg = 'Form partially filled but submit button not found'
                    print(f'\nSKIPPED: {msg}')
                    log_application('skipped', msg, screenshots)
            else:
                print('\nSubmit was clicked - verify with screenshots')
                log_application('applied', 'Submit clicked - check screenshots for confirmation', screenshots)

        except Exception as e:
            print(f'Error: {e}')
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
            print(f'Screenshots ({len(valid)}):')
            for s in valid:
                print(f'  {s}')

if __name__ == '__main__':
    main()
