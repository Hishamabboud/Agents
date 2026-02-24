#!/usr/bin/env python3
"""
Complete Sendent B.V. application AFTER clicking the magic link from email.

HOW TO USE:
1. Check hiaham123@hotmail.com inbox for an email from join.com
2. Copy the magic link URL from that email
3. Run: python3 apply_sendent_after_magic_link.py "https://join.com/magic-link-url-here"
   OR: set the MAGIC_LINK env var and run without args

The script will:
- Navigate to the magic link URL to authenticate
- Complete all form steps (CV upload, personal info, professional links, cover letter)
- Submit the application
- Save screenshots and update applications.json
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCREENSHOTS_DIR = Path('/home/user/Agents/output/screenshots')
DATA_DIR = Path('/home/user/Agents/data')
RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
JOB_URL = 'https://join.com/companies/sendentcom/15650046-medior-software-engineer-backend-integrations-net'
APPLICATIONS_FILE = DATA_DIR / 'applications.json'
CHROME_EXECUTABLE = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/sendent-cover-letter-v2.txt'

PERSONAL = {
    'first_name': 'Hisham',
    'last_name': 'Abboud',
    'email': 'hiaham123@hotmail.com',
    'phone': '648412838',
    'linkedin': 'https://linkedin.com/in/hisham-abboud',
}

COVER_LETTER_TEXT = """Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from ASML with Pytest and Locust, and CI/CD workflows in agile environments. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns.

I am based in Eindhoven with a valid Dutch work permit.

Best regards,
Hisham Abboud"""


def get_proxy_config():
    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY') or ''
    if not proxy_url:
        return None
    match = re.match(r'(https?://)([^:]+):([^@]+)@(.+)', proxy_url)
    if match:
        _, username, password, hostport = match.groups()
        return {'server': f'http://{hostport}', 'username': username, 'password': password}
    return {'server': proxy_url}


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def ss(page, name):
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = str(SCREENSHOTS_DIR / f'sendent-magic-{name}-{ts}.png')
    page.screenshot(path=path, full_page=True)
    log(f'Screenshot: {path}')
    return path


def click_btn(page, texts):
    for text in texts:
        try:
            btn = page.get_by_role('button', name=text, exact=True).first
            if btn and btn.is_visible():
                log(f'  Clicked button: "{text}"')
                btn.click()
                return True
        except Exception:
            pass
    return False


def main(magic_link_url=None):
    if not magic_link_url:
        magic_link_url = os.environ.get('MAGIC_LINK', '')
    if not magic_link_url:
        magic_link_url = sys.argv[1] if len(sys.argv) > 1 else ''
    if not magic_link_url:
        print("ERROR: Please provide the magic link URL as argument or MAGIC_LINK env var")
        print("Usage: python3 apply_sendent_after_magic_link.py 'https://join.com/...'")
        sys.exit(1)

    log(f'Magic link: {magic_link_url[:80]}...')

    screenshots = []
    status = 'failed'
    notes = []

    # Save cover letter
    Path(COVER_LETTER_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(COVER_LETTER_PATH).write_text(COVER_LETTER_TEXT)

    proxy_config = get_proxy_config()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_EXECUTABLE,
            headless=True,
            proxy=proxy_config,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                  '--ignore-certificate-errors', '--disable-blink-features=AutomationControlled']
        )
        ctx = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            proxy=proxy_config,
            ignore_https_errors=True,
        )
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = ctx.new_page()

        try:
            # Navigate to magic link
            log('Navigating to magic link...')
            page.goto(magic_link_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(4000)
            screenshots.append(ss(page, '01-after-magic-link'))
            log(f'URL after magic link: {page.url}')

            # Multi-step form loop
            max_steps = 15
            step = 0
            submitted = False

            while step < max_steps:
                step += 1
                url = page.url
                body = page.inner_text('body').lower()
                log(f'Step {step}: {url}')

                # Success check
                if any(w in body for w in ['thank', 'success', 'received', 'submitted', 'application sent', 'congratul']):
                    log('SUCCESS: Application submitted!')
                    status = 'applied'
                    notes.append('Application submitted successfully')
                    submitted = True
                    screenshots.append(ss(page, 'success'))
                    break

                # Route by URL
                if '/apply/cv' in url:
                    log('CV upload step...')
                    for fi in page.query_selector_all('input[type="file"]'):
                        try:
                            fi.set_input_files(RESUME_PATH)
                            log('  CV uploaded')
                            page.wait_for_timeout(3000)
                            break
                        except Exception as e:
                            log(f'  CV upload error: {e}')
                    screenshots.append(ss(page, f'cv-{step}'))
                    click_btn(page, ['Continue'])
                    page.wait_for_timeout(4000)

                elif '/apply/personalInformation' in url:
                    log('Personal info step...')

                    # Fill first name
                    fn = page.query_selector('input[placeholder="First name"]')
                    if fn:
                        fn.triple_click()
                        fn.fill(PERSONAL['first_name'])
                        log('  Filled first name')

                    # Fill last name
                    ln = page.query_selector('input[placeholder="Last name"]')
                    if ln:
                        ln.triple_click()
                        ln.fill(PERSONAL['last_name'])
                        log('  Filled last name')

                    page.wait_for_timeout(500)

                    # Country dropdown - try native select first
                    native_sel = page.query_selector('select')
                    if native_sel and native_sel.is_visible():
                        try:
                            native_sel.select_option(label='Netherlands')
                            log('  Country set via native select')
                        except Exception:
                            pass
                    else:
                        # Custom dropdown - click and search
                        # Find and click the country dropdown
                        country_dropdown = None
                        for sel in ['[data-testid*="country"]',
                                     'div[class*="Select"]:has-text("United States")',
                                     'div[class*="select"]:has-text("United States")',
                                     'button[class*="select"]']:
                            try:
                                el = page.query_selector(sel)
                                if el and el.is_visible():
                                    country_dropdown = el
                                    break
                            except Exception:
                                pass

                        # If not found, try clicking the element showing "United States"
                        if not country_dropdown:
                            try:
                                country_dropdown = page.get_by_text('United States').first
                            except Exception:
                                pass

                        if country_dropdown:
                            try:
                                country_dropdown.click()
                                page.wait_for_timeout(800)
                                # Try to type in search box
                                search = page.query_selector('input[placeholder*="Select"]')
                                if search:
                                    search.fill('Netherlands')
                                    page.wait_for_timeout(500)
                                # Click Netherlands
                                page.get_by_text('Netherlands', exact=False).first.click()
                                log('  Country set to Netherlands')
                            except Exception as e:
                                log(f'  Country dropdown error: {e}')

                    page.wait_for_timeout(500)

                    # Phone country code - click +1 button and select Netherlands
                    phone_cc = page.query_selector('button:has-text("+1")')
                    if phone_cc and phone_cc.is_visible():
                        try:
                            phone_cc.click()
                            page.wait_for_timeout(800)
                            # Type in search box
                            search = page.query_selector('input[type="search"], input[placeholder*="Select"]')
                            if search:
                                search.fill('Netherlands')
                                page.wait_for_timeout(600)
                            # Click Netherlands option
                            for sel in ['li:has-text("Netherlands")', 'div[role="option"]:has-text("Netherlands")']:
                                try:
                                    opt = page.query_selector(sel)
                                    if opt and opt.is_visible():
                                        opt.click()
                                        log('  Phone country: Netherlands (+31)')
                                        break
                                except Exception:
                                    pass
                        except Exception as e:
                            log(f'  Phone CC error: {e}')
                    elif page.query_selector('button:has-text("+31")'):
                        log('  Phone country already +31')

                    page.wait_for_timeout(500)

                    # Fill phone number
                    phone_input = page.query_selector('input[type="tel"]:not([name*="code"])')
                    if not phone_input:
                        phone_input = page.query_selector('input[type="tel"]')
                    if phone_input and phone_input.is_visible():
                        phone_input.triple_click()
                        phone_input.fill(PERSONAL['phone'])
                        log(f'  Phone filled: {PERSONAL["phone"]}')

                    page.wait_for_timeout(500)
                    screenshots.append(ss(page, f'personal-info-{step}'))
                    click_btn(page, ['Continue'])
                    page.wait_for_timeout(4000)

                elif '/apply/professionalLinks' in url or '/apply/links' in url:
                    log('Professional links step...')
                    linkedin_input = page.query_selector('input[placeholder*="URL"], input[placeholder*="linkedin" i], input[type="url"]')
                    if linkedin_input and linkedin_input.is_visible():
                        linkedin_input.triple_click()
                        linkedin_input.fill(PERSONAL['linkedin'])
                        log(f'  LinkedIn filled: {PERSONAL["linkedin"]}')
                    screenshots.append(ss(page, f'links-{step}'))
                    click_btn(page, ['Continue'])
                    page.wait_for_timeout(4000)

                elif '/apply/coverLetter' in url:
                    log('Cover letter upload step...')
                    for fi in page.query_selector_all('input[type="file"]'):
                        try:
                            fi.set_input_files(COVER_LETTER_PATH)
                            log('  Cover letter uploaded')
                            page.wait_for_timeout(3000)
                            break
                        except Exception as e:
                            log(f'  CL upload error: {e}')
                    screenshots.append(ss(page, f'cover-letter-{step}'))
                    click_btn(page, ['Continue'])
                    page.wait_for_timeout(4000)

                elif '/apply/' in url:
                    # Unknown step
                    log(f'Unknown step at: {url}')
                    try:
                        h1 = page.query_selector('h1')
                        if h1:
                            log(f'  H1: {h1.inner_text()}')
                    except Exception:
                        pass

                    screenshots.append(ss(page, f'unknown-{step}'))

                    # Try submit or continue
                    for btn_text in ['Submit application', 'Submit', 'Continue', 'Next']:
                        btn = page.query_selector(f'button:has-text("{btn_text}")')
                        if btn and btn.is_visible():
                            log(f'  Clicking: {btn_text}')
                            btn.click()
                            page.wait_for_timeout(4000)
                            break
                    else:
                        log('No button found on unknown step. Stopping.')
                        status = 'skipped'
                        notes.append(f'Stuck at unknown step: {url}')
                        break

                else:
                    log(f'Not on apply page: {url}')
                    notes.append(f'Left apply flow: {url}')
                    break

            screenshots.append(ss(page, 'final'))
            if not submitted and status == 'failed':
                status = 'skipped'
                notes.append(f'Application incomplete. Final URL: {page.url}')

        except Exception as e:
            log(f'Error: {e}')
            import traceback
            traceback.print_exc()
            try:
                screenshots.append(ss(page, 'error'))
            except Exception:
                pass
            notes.append(f'Error: {e}')
        finally:
            browser.close()

    # Save to applications.json
    applications = []
    if APPLICATIONS_FILE.exists():
        with open(APPLICATIONS_FILE) as f:
            applications = json.load(f)

    record = {
        'id': f'sendent-magic-link-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'company': 'Sendent B.V.',
        'role': 'Medior Software Engineer (Backend/Integrations/.NET)',
        'url': JOB_URL,
        'date_applied': datetime.now().isoformat(),
        'score': 9,
        'status': status,
        'resume_file': RESUME_PATH,
        'cover_letter_file': COVER_LETTER_PATH,
        'screenshots': screenshots,
        'notes': '; '.join(notes) if notes else 'Magic link flow completed',
        'email_used': PERSONAL['email'],
        'response': None,
    }
    applications.append(record)

    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(applications, f, indent=2)

    log(f'Status: {status}')
    log(f'Notes: {"; ".join(notes)}')
    return status


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result == 'applied' else 1)
