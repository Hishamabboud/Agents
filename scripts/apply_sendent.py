#!/usr/bin/env python3
"""
Automated job application script for Sendent B.V. - Medior Software Engineer position.
Uses Playwright (Python) for browser automation.

Multi-step Join.com application flow:
  1. Job listing page -> click "Apply Now"
  2. Auth page: enter email -> Continue
  3. CV upload page: upload PDF -> Continue
  4. Personal Information: first/last name, country, phone -> Continue
  5. Additional questions (cover letter, links, etc.) -> Continue/Submit
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ── Constants ──────────────────────────────────────────────────────────────────
SCREENSHOTS_DIR = Path('/home/user/Agents/output/screenshots')
DATA_DIR = Path('/home/user/Agents/data')
RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
JOB_URL = 'https://join.com/companies/sendentcom/15650046-medior-software-engineer-backend-integrations-net'
APPLICATIONS_FILE = DATA_DIR / 'applications.json'
CHROME_EXECUTABLE = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'

PERSONAL = {
    'full_name': 'Hisham Abboud',
    'first_name': 'Hisham',
    'last_name': 'Abboud',
    'email': 'Hisham123@hotmail.com',
    'phone': '0648412838',   # local NL format for phone input field
    'phone_full': '+31 06 4841 2838',
    'linkedin': 'linkedin.com/in/hisham-abboud',
    'github': 'github.com/Hishamabboud',
    'city': 'Eindhoven',
    'country': 'Netherlands',
}

COVER_LETTER = """Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values and career goals.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments -- exactly the kind of backend ownership your Exchange Connector requires. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from my internship at ASML, where I built automated test suites with Pytest and Locust, and worked with Git-based CI/CD workflows in an agile environment. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns -- relevant to Sendent's mission of data sovereignty.

I am based in Eindhoven with a valid Dutch work permit and am comfortable with hybrid work. I would value the opportunity to grow by owning real software at Sendent.

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


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def screenshot(page, name: str) -> str:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = str(SCREENSHOTS_DIR / f'sendent-{name}-{ts}.png')
    page.screenshot(path=filepath, full_page=True)
    log(f'Screenshot: {filepath}')
    return filepath


def fill(page, selectors, value: str, label: str = '') -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.fill(value)
                log(f'  Filled [{label or sel}]')
                return True
        except Exception:
            pass
    return False


def click_text(page, texts) -> bool:
    for text in texts:
        try:
            el = page.get_by_text(text, exact=True).first
            if el and el.is_visible():
                log(f'  Clicked "{text}"')
                el.click()
                return True
        except Exception:
            pass
    for text in texts:
        try:
            el = page.get_by_role('button', name=text).first
            if el and el.is_visible():
                log(f'  Clicked button "{text}"')
                el.click()
                return True
        except Exception:
            pass
    return False


def log_page(page, label=''):
    log(f'=== {label} | URL: {page.url} ===')
    for el in page.query_selector_all('input:not([type="hidden"]), textarea, select, button')[:15]:
        try:
            tag = el.evaluate('e => e.tagName').lower()
            t = el.get_attribute('type') or ''
            n = el.get_attribute('name') or el.get_attribute('id') or ''
            p = el.get_attribute('placeholder') or el.get_attribute('aria-label') or ''
            txt = el.inner_text().strip()[:50] if tag in ('button', 'select') else ''
            vis = el.is_visible()
            log(f'  [{tag}/{t}] "{n}" ph="{p}" text="{txt}" vis={vis}')
        except Exception:
            pass


def wait_and_screenshot(page, name, wait_ms=2000):
    page.wait_for_timeout(wait_ms)
    return screenshot(page, name)


def handle_step_cv(page, screenshots_taken, notes):
    """Handle CV upload step."""
    log('CV upload step...')
    log_page(page, 'CV upload')

    file_inputs = page.query_selector_all('input[type="file"]')
    log(f'File inputs: {len(file_inputs)}')

    uploaded = False
    for fi in file_inputs:
        if fi.is_visible():
            try:
                fi.set_input_files(RESUME_PATH)
                log(f'CV uploaded via visible input')
                uploaded = True
                break
            except Exception as e:
                log(f'Visible file input error: {e}')

    if not uploaded:
        for fi in file_inputs:
            try:
                fi.set_input_files(RESUME_PATH)
                log('CV uploaded via hidden input')
                uploaded = True
                break
            except Exception as e:
                log(f'Hidden file input error: {e}')

    if not uploaded:
        notes.append('CV upload failed - no suitable file input found')
    else:
        page.wait_for_timeout(3000)

    sc = wait_and_screenshot(page, 'cv-uploaded', 1000)
    screenshots_taken.append(sc)

    log('Clicking Continue on CV page...')
    click_text(page, ['Continue'])
    page.wait_for_timeout(4000)


def handle_step_personal_info(page, screenshots_taken, notes):
    """Handle personal information step."""
    log('Personal information step...')
    log_page(page, 'Personal Info')

    # First name
    fill(page, ['input[placeholder="First name"]', '#first_name', 'input[name="firstName"]',
                  'input[placeholder*="first" i]'],
         PERSONAL['first_name'], 'First name')

    # Last name
    fill(page, ['input[placeholder="Last name"]', '#last_name', 'input[name="lastName"]',
                  'input[placeholder*="last" i]'],
         PERSONAL['last_name'], 'Last name')

    # Country of residence - try to select Netherlands
    country_sel = page.query_selector('select')
    if country_sel and country_sel.is_visible():
        try:
            country_sel.select_option(label='Netherlands')
            log('  Selected country: Netherlands')
        except Exception:
            try:
                country_sel.select_option(value='NL')
                log('  Selected country by value: NL')
            except Exception as e:
                log(f'  Could not select Netherlands: {e}')
                notes.append('Could not select Netherlands from country dropdown')

    # Phone number - the field has a country code dropdown (+1 by default)
    # First try to change the country code to Netherlands (+31)
    phone_dropdown = page.query_selector('button:has-text("+1"), [aria-label*="phone country" i], .PhoneInputCountry')
    if phone_dropdown:
        try:
            phone_dropdown.click()
            page.wait_for_timeout(500)
            # Look for Netherlands option
            nl_option = page.get_by_text('Netherlands', exact=True).first
            if nl_option and nl_option.is_visible():
                nl_option.click()
                page.wait_for_timeout(500)
                log('  Phone country set to Netherlands')
        except Exception as e:
            log(f'  Phone country dropdown error: {e}')

    # Fill the phone number input (digits only after country code)
    phone_filled = fill(page, [
        'input[type="tel"]:not([name*="code" i])',
        'input[placeholder*="phone" i]',
        'input[name*="phone" i]',
        'input[type="tel"]',
    ], '0648412838', 'Phone')

    if not phone_filled:
        log('  Could not fill phone field')
        notes.append('Phone field not found')

    sc = wait_and_screenshot(page, 'personal-info-filled', 500)
    screenshots_taken.append(sc)

    log('Clicking Continue on personal info page...')
    click_text(page, ['Continue'])
    page.wait_for_timeout(4000)


def handle_step_questions(page, screenshots_taken, notes):
    """Handle additional questions / motivation step."""
    log('Questions/motivation step...')
    log_page(page, 'Questions')

    body = page.inner_text('body').lower()
    log(f'Page body: {body[:500]}')

    # Fill any text areas (cover letter / motivation)
    textareas = page.query_selector_all('textarea:not([name*="recaptcha" i])')
    log(f'Textareas found: {len(textareas)}')
    for ta in textareas:
        try:
            if ta.is_visible():
                ta.fill(COVER_LETTER)
                log('  Filled textarea with cover letter')
                break
        except Exception as e:
            log(f'  Textarea fill error: {e}')

    # Fill any text inputs for URLs (LinkedIn, GitHub, portfolio)
    all_inputs = page.query_selector_all('input[type="text"], input[type="url"]')
    for inp in all_inputs:
        try:
            ph = (inp.get_attribute('placeholder') or '').lower()
            name = (inp.get_attribute('name') or '').lower()
            label = (inp.get_attribute('aria-label') or '').lower()
            combined = ph + name + label
            if inp.is_visible():
                if 'linkedin' in combined:
                    inp.fill(PERSONAL['linkedin'])
                    log('  Filled LinkedIn')
                elif 'github' in combined:
                    inp.fill(PERSONAL['github'])
                    log('  Filled GitHub')
                elif 'portfolio' in combined or 'website' in combined:
                    inp.fill(f'https://{PERSONAL["github"]}')
                    log('  Filled portfolio/website')
        except Exception:
            pass

    sc = wait_and_screenshot(page, 'questions-filled', 500)
    screenshots_taken.append(sc)

    log('Clicking Continue/Submit on questions page...')
    click_text(page, ['Submit application', 'Submit Application', 'Submit', 'Continue', 'Send', 'Apply'])
    page.wait_for_timeout(5000)


def main():
    screenshots_taken = []
    status = 'failed'
    notes = []

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log('Starting Sendent B.V. application...')
    proxy_config = get_proxy_config()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_EXECUTABLE,
            headless=True,
            proxy=proxy_config,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage', '--ignore-certificate-errors']
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            proxy=proxy_config,
            ignore_https_errors=True,
        )
        page = context.new_page()

        try:
            # ── Step 1: Job listing ────────────────────────────────────────
            log('Loading job listing...')
            page.goto(JOB_URL, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)
            sc = screenshot(page, '01-job-listing')
            screenshots_taken.append(sc)

            # ── Step 2: Click Apply Now ────────────────────────────────────
            log('Clicking Apply Now...')
            click_text(page, ['Apply Now', 'Apply now', 'Apply'])
            page.wait_for_timeout(3000)
            sc = screenshot(page, '02-apply-clicked')
            screenshots_taken.append(sc)

            # ── Step 3: Authentication - enter email ───────────────────────
            if 'authentication' in page.url:
                log('Auth page: entering email...')
                fill(page, ['input[type="email"]', '#email', 'input[name="email"]',
                              'input[placeholder*="email" i]'],
                     PERSONAL['email'], 'Email')
                sc = screenshot(page, '03-email-entered')
                screenshots_taken.append(sc)

                log('Clicking Continue...')
                click_text(page, ['Continue'])
                page.wait_for_timeout(5000)
                sc = screenshot(page, '04-after-email-continue')
                screenshots_taken.append(sc)
                log(f'After auth URL: {page.url}')

            # ── Multi-step form loop ───────────────────────────────────────
            max_steps = 10
            step = 0
            final_submitted = False

            while step < max_steps:
                step += 1
                current_url = page.url
                body = page.inner_text('body').lower()
                log(f'Step {step}: URL={current_url}')

                # Detect success
                success_words = ['thank', 'success', 'received', 'submitted', 'bedankt',
                                  'ontvangen', 'congratul', 'application sent', 'great!',
                                  'we will be in touch']
                if any(w in body for w in success_words):
                    log('Application submitted successfully!')
                    status = 'applied'
                    notes.append('Application submitted with confirmation detected.')
                    final_submitted = True
                    sc = screenshot(page, f'success-{step}')
                    screenshots_taken.append(sc)
                    break

                # Detect stuck on auth
                if 'authentication' in current_url and step > 1:
                    log('Still on auth page after step 1 - likely needs email verification')
                    notes.append('Stuck on auth page. Email verification may be required.')
                    status = 'skipped'
                    break

                # CV upload step
                if '/apply/cv' in current_url:
                    handle_step_cv(page, screenshots_taken, notes)
                    continue

                # Personal information step
                elif '/apply/personalInformation' in current_url or '/apply/personal' in current_url:
                    handle_step_personal_info(page, screenshots_taken, notes)
                    continue

                # Additional questions / motivation
                elif '/apply/questions' in current_url or '/apply/motivation' in current_url or '/apply/coverLetter' in current_url:
                    handle_step_questions(page, screenshots_taken, notes)
                    continue

                # Unknown apply step - try to detect and handle
                elif '/apply/' in current_url:
                    log(f'Unknown apply step. Body: {body[:300]}')
                    log_page(page, f'Unknown step {step}')

                    # Handle personal info fields if present
                    has_first = page.query_selector('input[placeholder="First name"]')
                    has_last = page.query_selector('input[placeholder="Last name"]')
                    if has_first or has_last:
                        log('Detected personal info fields, filling...')
                        handle_step_personal_info(page, screenshots_taken, notes)
                        continue

                    # Handle textarea (questions/motivation)
                    textareas = [t for t in page.query_selector_all('textarea:not([name*="recaptcha" i])') if t.is_visible()]
                    if textareas:
                        log('Detected text area, treating as questions step...')
                        handle_step_questions(page, screenshots_taken, notes)
                        continue

                    # Handle file upload
                    file_inputs = page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        log('Detected file input, treating as CV step...')
                        handle_step_cv(page, screenshots_taken, notes)
                        continue

                    # Take screenshot and try clicking Continue or Submit
                    sc = screenshot(page, f'unknown-step-{step}')
                    screenshots_taken.append(sc)

                    buttons = page.query_selector_all('button')
                    log(f'Buttons on unknown step:')
                    for btn in buttons:
                        try:
                            txt = btn.inner_text().strip()
                            vis = btn.is_visible()
                            log(f'  "{txt}" vis={vis}')
                        except Exception:
                            pass

                    clicked = click_text(page, ['Submit application', 'Submit Application',
                                                 'Submit', 'Continue', 'Send', 'Apply',
                                                 'Finish', 'Complete'])
                    if not clicked:
                        log('No button found to click on unknown step. Stopping.')
                        notes.append(f'Could not advance past step: {current_url}')
                        status = 'skipped'
                        break
                    page.wait_for_timeout(4000)

                else:
                    log(f'Not on an apply page: {current_url}')
                    log(f'Body: {body[:400]}')
                    notes.append(f'Exited apply flow. Final URL: {current_url}')
                    break

            # Take final screenshot
            sc = screenshot(page, 'final-state')
            screenshots_taken.append(sc)

            if not final_submitted and status == 'failed':
                log('Application did not complete. Last URL: ' + page.url)
                notes.append(f'Application incomplete. Last URL: {page.url}')
                status = 'skipped'

        except PlaywrightTimeoutError as e:
            log(f'Timeout: {e}')
            try:
                screenshot(page, 'error-timeout')
            except Exception:
                pass
            notes.append(f'Timeout: {e}')
            status = 'failed'
        except Exception as e:
            log(f'Error: {e}')
            import traceback
            traceback.print_exc()
            try:
                screenshot(page, 'error')
            except Exception:
                pass
            notes.append(f'Error: {e}')
            status = 'failed'
        finally:
            browser.close()
            log('Browser closed.')

    # Log application
    applications = []
    if APPLICATIONS_FILE.exists():
        try:
            with open(APPLICATIONS_FILE) as f:
                applications = json.load(f)
        except Exception:
            pass

    app_record = {
        'id': f'sendent-medior-be-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'company': 'Sendent B.V.',
        'role': 'Medior Software Engineer (Backend/Integrations/.NET)',
        'url': JOB_URL,
        'date_applied': datetime.now().isoformat(),
        'score': 9,
        'status': status,
        'resume_file': RESUME_PATH,
        'cover_letter_file': None,
        'screenshots': screenshots_taken,
        'notes': '; '.join(notes) if notes else 'None',
        'response': None,
    }
    applications.append(app_record)

    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(applications, f, indent=2)

    log(f'Logged. Status: {status}')
    return status


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result == 'applied' else 1)
