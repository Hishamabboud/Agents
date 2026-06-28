#!/usr/bin/env python3
"""
Apply to IXON Cloud Software Engineer position via Playwright.
Uses the /o/{slug}/apply direct URL and intercepts font requests to avoid timeout.
"""

import os
import json
import time
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

def ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def screenshot(page, label):
    filename = f'ixon-{label}-{ts()}.png'
    filepath = SCREENSHOT_DIR / filename
    # Use CDP to take a screenshot, bypassing font wait
    try:
        # Try using CDP directly to avoid font loading wait
        cdp_session = page.context.new_cdp_session(page)
        result = cdp_session.send('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True})
        import base64
        img_data = base64.b64decode(result['data'])
        with open(str(filepath), 'wb') as f:
            f.write(img_data)
        cdp_session.detach()
        print(f'CDP Screenshot saved: {filepath}')
        return str(filepath)
    except Exception as e:
        print(f'CDP screenshot failed: {e}')
        # Fallback to regular screenshot with longer timeout
        try:
            page.screenshot(path=str(filepath), full_page=False, timeout=30000)
            print(f'Screenshot saved: {filepath}')
            return str(filepath)
        except Exception as e2:
            print(f'Screenshot also failed: {e2}')
            return None

def try_fill(page, selectors, value, field_name):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(timeout=5000, state='attached')
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

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--blink-settings=imagesEnabled=false',
            ],
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        # Intercept font requests and return empty response to prevent font loading wait
        def handle_route(route):
            url = route.request.url
            # Block external fonts and analytics that cause hangs
            if any(domain in url for domain in [
                'fonts.googleapis.com',
                'fonts.gstatic.com',
                'recruiteecdn.com/fonts',
                'captcha-assets.recruiteecdn.com',
                'careers-analytics.recruitee.com',
            ]):
                route.abort()
            else:
                route.continue_()

        context.route('**/*', handle_route)

        page = context.new_page()

        # Inject CSS to override font-face declarations (prevents font load waiting)
        page.add_init_script("""
            // Override font-face to use system fonts immediately
            const style = document.createElement('style');
            style.textContent = '* { font-family: Arial, sans-serif !important; }';
            document.head && document.head.appendChild(style);
        """)

        try:
            # Navigate to the /c/new application URL directly
            print(f'Navigating to apply URL: {APPLY_URL}')
            try:
                page.goto(APPLY_URL, wait_until='domcontentloaded', timeout=30000)
                print(f'Page loaded. URL: {page.url}')
            except PlaywrightTimeoutError:
                print('domcontentloaded timed out, waiting for JS...')

            # Wait for JS SPA to render
            print('Waiting 8s for SPA to render...')
            page.wait_for_timeout(8000)

            print(f'Current URL: {page.url}')
            try:
                title = page.title()
                print(f'Page title: {title}')
            except Exception:
                pass

            ss = screenshot(page, '01-apply-page')
            screenshots.append(ss)

            # Check what inputs are available
            print('\n--- Inspecting form ---')
            inputs = page.locator('input').all()
            print(f'Inputs found: {len(inputs)}')
            for inp in inputs:
                try:
                    print(f'  input: type={inp.get_attribute("type")} name={inp.get_attribute("name")} id={inp.get_attribute("id")} placeholder={inp.get_attribute("placeholder")}')
                except Exception:
                    pass

            textareas = page.locator('textarea').all()
            print(f'Textareas found: {len(textareas)}')

            buttons = page.locator('button').all()
            print(f'Buttons found: {len(buttons)}')
            for btn in buttons[:10]:
                try:
                    print(f'  button: text="{btn.text_content()}" type={btn.get_attribute("type")}')
                except Exception:
                    pass

            # Check page body text
            try:
                body_text = page.locator('body').inner_text(timeout=5000)
                print(f'Body text preview: {body_text[:400]}')
            except Exception as e:
                print(f'Could not get body text: {e}')

            # If no form visible, try going to job page and clicking Apply
            if len(inputs) == 0:
                print('\nNo form found at /c/new, trying job page with Apply click...')
                try:
                    page.goto(JOB_URL, wait_until='domcontentloaded', timeout=30000)
                except PlaywrightTimeoutError:
                    print('Job page load timed out')

                page.wait_for_timeout(8000)
                ss = screenshot(page, '02-job-page')
                screenshots.append(ss)

                # Look for Apply button
                for sel in ['a:has-text("Apply")', 'button:has-text("Apply")', '[data-cy*="apply"]', 'text=Apply now']:
                    try:
                        btn = page.locator(sel).first
                        btn.wait_for(timeout=3000, state='visible')
                        print(f'Found Apply button with: {sel}')
                        btn.click()
                        page.wait_for_timeout(5000)
                        break
                    except Exception:
                        continue

                ss = screenshot(page, '03-after-apply-click')
                screenshots.append(ss)

                inputs = page.locator('input').all()
                print(f'Inputs after Apply click: {len(inputs)}')

            # Fill the form
            print('\n--- Filling form fields ---')

            name_filled = try_fill(page, [
                'input[name="name"]',
                'input[name="candidate[name]"]',
                'input[placeholder*="name" i]',
                'input[placeholder*="naam" i]',
                'input[id*="name" i]',
                'input[autocomplete="name"]',
            ], APPLICANT['name'], 'Full Name')

            email_filled = try_fill(page, [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="candidate[email]"]',
                'input[id*="email" i]',
            ], APPLICANT['email'], 'Email')

            phone_filled = try_fill(page, [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="candidate[phone]"]',
                'input[id*="phone" i]',
                'input[placeholder*="phone" i]',
            ], APPLICANT['phone'], 'Phone')

            # Country
            for sel in ['select[name*="country" i]', 'select[id*="country" i]']:
                try:
                    el = page.locator(sel).first
                    el.wait_for(timeout=2000, state='visible')
                    el.select_option(label='Netherlands')
                    print(f'Selected country using: {sel}')
                    break
                except Exception:
                    continue

            # Upload CV
            print('\n--- Uploading CV ---')
            cv_uploaded = False
            if RESUME_PATH.exists():
                for sel in ['input[type="file"]', 'input[accept*="pdf"]', 'input[name*="cv" i]', 'input[name*="resume" i]']:
                    try:
                        fi = page.locator(sel).first
                        fi.wait_for(timeout=3000)
                        fi.set_input_files(str(RESUME_PATH))
                        print(f'CV uploaded using: {sel}')
                        page.wait_for_timeout(2000)
                        cv_uploaded = True
                        break
                    except Exception:
                        continue
                if not cv_uploaded:
                    print('Could not find file input')
            else:
                print(f'CV not found at: {RESUME_PATH}')

            ss = screenshot(page, '04-form-filled')
            screenshots.append(ss)
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
                'input[type="submit"]',
            ]:
                try:
                    btn = page.locator(sel).first
                    btn.wait_for(timeout=2000, state='visible')
                    btn_text = btn.text_content() or ''
                    print(f'Submit button found: "{btn_text.strip()}" via {sel}')
                    btn.click()
                    print('Clicked submit!')
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                print('No submit button found')
                # Print form HTML for debugging
                try:
                    forms = page.locator('form').all()
                    for i, form in enumerate(forms[:3]):
                        print(f'Form {i} HTML:')
                        print(form.inner_html(timeout=5000)[:1000])
                except Exception:
                    pass

            page.wait_for_timeout(5000)
            ss = screenshot(page, '06-post-submit')
            screenshots.append(ss)

            # Check confirmation
            try:
                final_text = page.locator('body').inner_text(timeout=5000)
            except Exception:
                final_text = ''
            final_url = page.url

            print(f'\nFinal URL: {final_url}')
            print(f'Page text after submit: {final_text[:400]}')

            success_kw = ['successfully submitted', 'thank you', 'application received', 'bedankt', 'success']
            if any(k in final_text.lower() for k in success_kw):
                print('SUCCESS: Confirmed submitted!')
                log_application('applied', 'Application submitted via Playwright', screenshots)
            elif not submitted:
                any_filled = name_filled or email_filled or phone_filled or cv_uploaded
                if not any_filled:
                    print('SKIPPED: No form found - may require JS or CAPTCHA')
                    log_application('skipped', 'No application form could be rendered - hCaptcha (invisible) and SPA require browser JS', screenshots)
                else:
                    print('SKIPPED: Form partially filled but no submit button')
                    log_application('skipped', 'Form found and filled but submit button not located', screenshots)
            else:
                print('Status unclear - submit was clicked, check screenshots')
                log_application('applied', 'Submit clicked - verify in screenshots', screenshots)

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
