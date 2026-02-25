#!/usr/bin/env python3
"""
Re-apply to Sendent B.V. Medior Software Engineer (Backend/Integrations/.NET)
CRITICAL: Use email hiaham123@hotmail.com (NOT Hisham123@hotmail.com)

Form flow on join.com:
  1. Job listing -> click "Apply Now"
  2. Auth page: enter email -> Continue
  3. CV upload page: upload PDF -> Continue
  4. Personal Information: first name, last name, country (Netherlands), phone (+31) -> Continue
  5. Professional links: LinkedIn URL -> Continue
  6. Upload cover letter: file upload -> Continue
  7. Submit application -> done

Key fix: phone country code dropdown uses a search box - must type "Netherlands" to get +31
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
    'email': 'hiaham123@hotmail.com',  # CORRECT email - hiaham not Hisham
    'phone': '648412838',              # NL local format without leading 0
    'linkedin': 'https://linkedin.com/in/hisham-abboud',
    'city': 'Eindhoven',
    'country': 'Netherlands',
}

COVER_LETTER_TEXT = """Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from ASML with Pytest and Locust, and CI/CD workflows in agile environments. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns.

I am based in Eindhoven with a valid Dutch work permit.

Best regards,
Hisham Abboud"""

COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/sendent-cover-letter-v2.txt'


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
    filepath = str(SCREENSHOTS_DIR / f'sendent-v2-{name}-{ts}.png')
    page.screenshot(path=filepath, full_page=True)
    log(f'Screenshot saved: {filepath}')
    return filepath


def log_page(page, label=''):
    log(f'=== PAGE: {label} | URL: {page.url} ===')
    try:
        for el in page.query_selector_all('input:not([type="hidden"]), textarea, select, button')[:20]:
            try:
                tag = el.evaluate('e => e.tagName').lower()
                t = el.get_attribute('type') or ''
                n = el.get_attribute('name') or el.get_attribute('id') or ''
                p = el.get_attribute('placeholder') or el.get_attribute('aria-label') or ''
                txt = el.inner_text().strip()[:50] if tag in ('button', 'select') else ''
                vis = el.is_visible()
                log(f'  [{tag}/{t}] n="{n}" ph="{p}" text="{txt}" vis={vis}')
            except Exception:
                pass
    except Exception as e:
        log(f'  log_page error: {e}')


def safe_fill(page, selectors, value: str, label: str = '') -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.triple_click()
                el.fill(value)
                log(f'  Filled [{label or sel}] = "{value}"')
                return True
        except Exception as e:
            pass
    log(f'  Could not fill [{label}] - tried {len(selectors)} selectors')
    return False


def click_btn(page, texts) -> bool:
    for text in texts:
        try:
            el = page.get_by_role('button', name=text, exact=True).first
            if el and el.is_visible():
                log(f'  Clicked button "{text}"')
                el.click()
                return True
        except Exception:
            pass
    for text in texts:
        try:
            el = page.get_by_text(text, exact=True).first
            if el and el.is_visible():
                log(f'  Clicked text "{text}"')
                el.click()
                return True
        except Exception:
            pass
    return False


def handle_cv_upload(page, screenshots_taken, notes):
    """Upload CV PDF."""
    log('--- CV Upload Step ---')
    log_page(page, 'CV Upload')

    file_inputs = page.query_selector_all('input[type="file"]')
    log(f'File inputs found: {len(file_inputs)}')

    uploaded = False
    for fi in file_inputs:
        try:
            fi.set_input_files(RESUME_PATH)
            log('CV uploaded successfully')
            uploaded = True
            break
        except Exception as e:
            log(f'File input error: {e}')

    if not uploaded:
        notes.append('CV upload: no suitable file input found')
    else:
        page.wait_for_timeout(3000)

    screenshots_taken.append(screenshot(page, 'cv-uploaded'))

    log('Clicking Continue after CV upload...')
    if not click_btn(page, ['Continue']):
        log('Continue button not found, trying submit...')
        click_btn(page, ['Submit', 'Next', 'Save'])
    page.wait_for_timeout(4000)


def handle_personal_info(page, screenshots_taken, notes):
    """Fill personal information: name, country (Netherlands), phone (+31)."""
    log('--- Personal Information Step ---')
    log_page(page, 'Personal Info')

    # First name
    safe_fill(page, [
        'input[placeholder="First name"]',
        'input[name="firstName"]',
        '#first_name',
        'input[placeholder*="first" i]',
    ], PERSONAL['first_name'], 'First name')

    # Last name
    safe_fill(page, [
        'input[placeholder="Last name"]',
        'input[name="lastName"]',
        '#last_name',
        'input[placeholder*="last" i]',
    ], PERSONAL['last_name'], 'Last name')

    page.wait_for_timeout(500)

    # Country of residence - custom dropdown (not a native <select>)
    log('Setting Country of residence to Netherlands...')
    country_done = False

    # Try native select first
    country_select = page.query_selector('select')
    if country_select and country_select.is_visible():
        try:
            country_select.select_option(label='Netherlands')
            log('  Country set via native select')
            country_done = True
        except Exception as e:
            log(f'  Native select failed: {e}')

    if not country_done:
        # The country dropdown is a custom component - click it then select Netherlands
        for sel in ['[data-testid*="country"]', 'button[aria-haspopup]', '.country-selector',
                    'div[class*="country"]', 'div[class*="select"]:has-text("United States")']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    page.wait_for_timeout(800)
                    # Look for Netherlands option
                    nl = page.get_by_text('Netherlands', exact=False).first
                    if nl and nl.is_visible():
                        nl.click()
                        country_done = True
                        log('  Country set via custom dropdown')
                        break
            except Exception:
                pass

    page.wait_for_timeout(500)

    # Phone number - the dropdown starts at +1, need to change to Netherlands (+31)
    log('Setting phone country code to Netherlands (+31)...')
    phone_done = False

    # The phone country is a button with text "+1" that opens a searchable dropdown
    phone_cc_btn = page.query_selector('button:has-text("+1")')
    if not phone_cc_btn:
        phone_cc_btn = page.query_selector('[aria-label*="phone country" i]')
    if not phone_cc_btn:
        # Try finding the button that is near the phone input
        phone_cc_btn = page.query_selector('.PhoneInputCountrySelect, [class*="PhoneInput"] button, [class*="phone-country"]')

    if phone_cc_btn and phone_cc_btn.is_visible():
        try:
            log('  Clicking phone country code button (+1)...')
            phone_cc_btn.click()
            page.wait_for_timeout(1000)

            # A searchable dropdown appears - type "Netherlands" to filter
            search_input = page.query_selector('input[placeholder*="Select" i], input[type="search"], input[role="combobox"]')
            if search_input and search_input.is_visible():
                search_input.fill('Netherlands')
                page.wait_for_timeout(800)
                log('  Typed "Netherlands" in phone country search')

            # Click the Netherlands option
            nl_option = None
            for sel in [
                'li:has-text("Netherlands")',
                'div[role="option"]:has-text("Netherlands")',
                'span:has-text("Netherlands (+31)")',
                'div:has-text("Netherlands")',
            ]:
                try:
                    nl_option = page.query_selector(sel)
                    if nl_option and nl_option.is_visible():
                        nl_option.click()
                        phone_done = True
                        log('  Phone country set to Netherlands (+31)')
                        break
                except Exception:
                    pass

            if not phone_done:
                # Try clicking text "Netherlands" visible in the dropdown
                try:
                    page.get_by_text('Netherlands', exact=False).first.click()
                    phone_done = True
                    log('  Phone country Netherlands set via text click')
                except Exception as e:
                    log(f'  Netherlands text click failed: {e}')

        except Exception as e:
            log(f'  Phone country code error: {e}')
    else:
        log('  Phone CC button not found, checking if already +31...')
        # Check if it might already be set correctly
        existing_btn = page.query_selector('button:has-text("+31")')
        if existing_btn:
            log('  Phone country already set to +31')
            phone_done = True

    if not phone_done:
        notes.append('Phone country code: could not set to +31/Netherlands')

    page.wait_for_timeout(500)

    # Fill phone number (digits only, no country code)
    safe_fill(page, [
        'input[type="tel"]:not([name*="code" i])',
        'input[placeholder*="phone" i]',
        'input[name*="phone" i]',
        'input[type="tel"]',
    ], PERSONAL['phone'], 'Phone number')

    page.wait_for_timeout(500)
    screenshots_taken.append(screenshot(page, 'personal-info-filled'))

    # Validate phone - check for error message
    body = page.inner_text('body').lower()
    if 'phone number format is not recognised' in body or 'not recognised' in body:
        log('WARNING: Phone validation error detected - country code may still be +1')
        notes.append('Phone validation error: format not recognised')

    log('Clicking Continue on personal info...')
    if not click_btn(page, ['Continue']):
        click_btn(page, ['Next', 'Save', 'Submit'])
    page.wait_for_timeout(4000)


def handle_professional_links(page, screenshots_taken, notes):
    """Fill professional links (LinkedIn)."""
    log('--- Professional Links Step ---')
    log_page(page, 'Professional Links')

    # Fill LinkedIn
    safe_fill(page, [
        'input[placeholder*="linkedin" i]',
        'input[aria-label*="linkedin" i]',
        'input[name*="linkedin" i]',
        'input[placeholder*="URL" i]',
        'input[type="url"]',
        'input[type="text"]',
    ], PERSONAL['linkedin'], 'LinkedIn URL')

    page.wait_for_timeout(500)
    screenshots_taken.append(screenshot(page, 'professional-links-filled'))

    log('Clicking Continue on professional links...')
    if not click_btn(page, ['Continue']):
        click_btn(page, ['Next', 'Save', 'Submit'])
    page.wait_for_timeout(4000)


def handle_cover_letter_upload(page, screenshots_taken, notes):
    """Upload cover letter as a text file."""
    log('--- Cover Letter Upload Step ---')
    log_page(page, 'Cover Letter')

    # Save cover letter as a PDF-like text file
    cover_letter_path = Path(COVER_LETTER_PATH)
    cover_letter_path.parent.mkdir(parents=True, exist_ok=True)
    cover_letter_path.write_text(COVER_LETTER_TEXT)
    log(f'Cover letter saved to: {cover_letter_path}')

    # Upload the file
    file_inputs = page.query_selector_all('input[type="file"]')
    log(f'File inputs found: {len(file_inputs)}')

    uploaded = False
    for fi in file_inputs:
        try:
            fi.set_input_files(str(cover_letter_path))
            log('Cover letter uploaded successfully')
            uploaded = True
            page.wait_for_timeout(3000)
            break
        except Exception as e:
            log(f'Cover letter upload error: {e}')

    if not uploaded:
        # Try file chooser approach
        try:
            upload_area = page.query_selector('div[class*="upload"], button:has-text("Upload"), label[class*="upload"]')
            if upload_area:
                with page.expect_file_chooser() as fc:
                    upload_area.click()
                fc.value.set_files(str(cover_letter_path))
                uploaded = True
                log('Cover letter uploaded via file chooser')
                page.wait_for_timeout(3000)
        except Exception as e:
            log(f'File chooser error: {e}')

    if not uploaded:
        notes.append('Cover letter upload: no suitable file input found - skipping')

    screenshots_taken.append(screenshot(page, 'cover-letter-step'))

    log('Clicking Continue after cover letter...')
    if not click_btn(page, ['Continue']):
        click_btn(page, ['Next', 'Skip', 'Submit'])
    page.wait_for_timeout(4000)


def main():
    screenshots_taken = []
    status = 'failed'
    notes = []

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log('=== Starting Sendent B.V. Re-Application (v2 - correct email) ===')
    log(f'Email: {PERSONAL["email"]}')
    proxy_config = get_proxy_config()
    log(f'Proxy configured: {bool(proxy_config)}')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_EXECUTABLE,
            headless=True,
            proxy=proxy_config,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            proxy=proxy_config,
            ignore_https_errors=True,
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        page = context.new_page()

        try:
            # ── Step 1: Job listing ────────────────────────────────────────────
            log('Loading job listing page...')
            page.goto(JOB_URL, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(3000)
            screenshots_taken.append(screenshot(page, '01-job-listing'))
            log(f'URL: {page.url}')

            # ── Step 2: Click Apply Now ────────────────────────────────────────
            log('Clicking Apply Now...')
            clicked = click_btn(page, ['Apply Now', 'Apply now', 'Apply'])
            if not clicked:
                # Try anchor tag
                apply_link = page.query_selector('a[href*="/apply"]')
                if apply_link:
                    apply_link.click()
                    clicked = True
                    log('Clicked apply link')
            page.wait_for_timeout(3000)
            screenshots_taken.append(screenshot(page, '02-after-apply-click'))
            log(f'URL: {page.url}')

            # ── Step 3: Auth page - enter email ───────────────────────────────
            if 'authentication' in page.url or 'auth' in page.url.lower():
                log(f'Auth page detected. Entering email: {PERSONAL["email"]}')
                filled = safe_fill(page, [
                    'input[type="email"]',
                    '#email',
                    'input[name="email"]',
                    'input[placeholder*="email" i]',
                ], PERSONAL['email'], 'Email')

                if filled:
                    # Verify the email was entered correctly
                    email_el = page.query_selector('input[type="email"], input[name="email"]')
                    if email_el:
                        actual_value = email_el.input_value()
                        log(f'Email field value: "{actual_value}"')
                        if actual_value != PERSONAL['email']:
                            log(f'WARNING: Email mismatch! Expected: {PERSONAL["email"]}, Got: {actual_value}')
                            email_el.triple_click()
                            email_el.fill(PERSONAL['email'])
                            log(f'Re-filled email. New value: "{email_el.input_value()}"')

                screenshots_taken.append(screenshot(page, '03-email-entered'))

                log('Clicking Continue...')
                click_btn(page, ['Continue'])
                page.wait_for_timeout(5000)
                screenshots_taken.append(screenshot(page, '04-after-email-continue'))
                log(f'URL after auth: {page.url}')

            # ── Multi-step form loop ───────────────────────────────────────────
            max_steps = 12
            step = 0
            final_submitted = False

            while step < max_steps:
                step += 1
                current_url = page.url
                body_text = page.inner_text('body').lower()
                log(f'--- Loop step {step}: URL={current_url} ---')

                # Detect success
                success_words = ['thank', 'success', 'received', 'submitted', 'bedankt',
                                  'ontvangen', 'congratul', 'application sent', "we'll be in touch",
                                  'we will be in touch', 'great!', 'application complete']
                if any(w in body_text for w in success_words):
                    log('SUCCESS: Application submitted! Confirmation detected.')
                    status = 'applied'
                    notes.append(f'Application submitted successfully. Email: {PERSONAL["email"]}')
                    final_submitted = True
                    screenshots_taken.append(screenshot(page, f'success-{step}'))
                    break

                # Detect stuck on auth (email verification required)
                if ('authentication' in current_url or 'auth' in current_url.lower()) and step > 1:
                    log('Stuck on auth page. Email verification may be required.')
                    notes.append('Stuck on auth page after step 1.')
                    status = 'skipped'
                    break

                # ── Route based on URL ─────────────────────────────────────────
                if '/apply/cv' in current_url:
                    handle_cv_upload(page, screenshots_taken, notes)

                elif '/apply/personalInformation' in current_url or '/apply/personal' in current_url:
                    handle_personal_info(page, screenshots_taken, notes)

                elif '/apply/professionalLinks' in current_url or '/apply/links' in current_url:
                    handle_professional_links(page, screenshots_taken, notes)

                elif '/apply/coverLetter' in current_url:
                    handle_cover_letter_upload(page, screenshots_taken, notes)

                elif '/apply/questions' in current_url or '/apply/motivation' in current_url:
                    # Generic questions step
                    log('Questions/motivation step...')
                    log_page(page, 'Questions')

                    textareas = [t for t in page.query_selector_all('textarea') if t.is_visible()]
                    for ta in textareas:
                        try:
                            ta.fill(COVER_LETTER_TEXT)
                            log('  Filled textarea with cover letter')
                            break
                        except Exception as e:
                            log(f'  Textarea error: {e}')

                    screenshots_taken.append(screenshot(page, f'questions-{step}'))
                    click_btn(page, ['Submit application', 'Submit', 'Continue', 'Send', 'Apply'])
                    page.wait_for_timeout(5000)

                elif '/apply/' in current_url:
                    # Unknown apply step - detect and handle by page content
                    log(f'Unknown apply step: {current_url}')
                    log_page(page, f'Unknown-{step}')

                    h1_text = ''
                    try:
                        h1 = page.query_selector('h1')
                        if h1:
                            h1_text = h1.inner_text().lower()
                            log(f'  H1: "{h1_text}"')
                    except Exception:
                        pass

                    # Route by page heading
                    if 'personal' in h1_text or 'name' in h1_text:
                        handle_personal_info(page, screenshots_taken, notes)
                    elif 'cv' in h1_text or 'resume' in h1_text or 'upload' in h1_text:
                        # Check if it's cover letter upload
                        if 'cover' in h1_text:
                            handle_cover_letter_upload(page, screenshots_taken, notes)
                        else:
                            handle_cv_upload(page, screenshots_taken, notes)
                    elif 'link' in h1_text or 'professional' in h1_text:
                        handle_professional_links(page, screenshots_taken, notes)
                    elif 'cover' in h1_text or 'letter' in h1_text:
                        handle_cover_letter_upload(page, screenshots_taken, notes)
                    else:
                        # Check page elements
                        has_first_name = page.query_selector('input[placeholder="First name"]')
                        has_textarea = [t for t in page.query_selector_all('textarea') if t.is_visible()]
                        has_file = page.query_selector_all('input[type="file"]')
                        has_linkedin = page.query_selector('input[placeholder*="linkedin" i]')

                        if has_first_name:
                            handle_personal_info(page, screenshots_taken, notes)
                        elif has_linkedin:
                            handle_professional_links(page, screenshots_taken, notes)
                        elif has_file and 'cover' in body_text:
                            handle_cover_letter_upload(page, screenshots_taken, notes)
                        elif has_file:
                            handle_cv_upload(page, screenshots_taken, notes)
                        elif has_textarea:
                            for ta in has_textarea:
                                try:
                                    ta.fill(COVER_LETTER_TEXT)
                                    break
                                except Exception:
                                    pass
                            screenshots_taken.append(screenshot(page, f'textarea-step-{step}'))
                            click_btn(page, ['Continue', 'Submit application', 'Submit'])
                            page.wait_for_timeout(4000)
                        else:
                            # Try to find and click any advance button
                            screenshots_taken.append(screenshot(page, f'unknown-step-{step}'))
                            clicked = click_btn(page, ['Submit application', 'Submit Application',
                                                        'Submit', 'Continue', 'Next', 'Finish'])
                            if not clicked:
                                log('No advance button found. Stopping.')
                                notes.append(f'Stuck at unknown step: {current_url}')
                                status = 'skipped'
                                break
                            page.wait_for_timeout(4000)

                else:
                    # Not on an apply page
                    log(f'Not on apply page: {current_url}')
                    log(f'Body snippet: {body_text[:300]}')
                    notes.append(f'Left apply flow. URL: {current_url}')
                    break

            # Final screenshot
            screenshots_taken.append(screenshot(page, 'final-state'))

            if not final_submitted:
                final_url = page.url
                final_body = page.inner_text('body').lower()
                if status == 'failed':
                    notes.append(f'Application incomplete. Final URL: {final_url}')
                    status = 'skipped'
                log(f'Final URL: {final_url}')
                log(f'Final body: {final_body[:300]}')

        except PlaywrightTimeoutError as e:
            log(f'Timeout error: {e}')
            try:
                screenshots_taken.append(screenshot(page, 'error-timeout'))
            except Exception:
                pass
            notes.append(f'Timeout: {e}')
            status = 'failed'
        except Exception as e:
            log(f'Unexpected error: {e}')
            import traceback
            traceback.print_exc()
            try:
                screenshots_taken.append(screenshot(page, 'error'))
            except Exception:
                pass
            notes.append(f'Error: {e}')
            status = 'failed'
        finally:
            browser.close()
            log('Browser closed.')

    # ── Save to applications.json ──────────────────────────────────────────────
    applications = []
    if APPLICATIONS_FILE.exists():
        try:
            with open(APPLICATIONS_FILE) as f:
                applications = json.load(f)
        except Exception:
            pass

    app_record = {
        'id': f'sendent-v2-correct-email-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'company': 'Sendent B.V.',
        'role': 'Medior Software Engineer (Backend/Integrations/.NET)',
        'url': JOB_URL,
        'date_applied': datetime.now().isoformat(),
        'score': 9,
        'status': status,
        'resume_file': RESUME_PATH,
        'cover_letter_file': COVER_LETTER_PATH,
        'screenshots': screenshots_taken,
        'notes': '; '.join(notes) if notes else 'Application completed',
        'email_used': PERSONAL['email'],
        'response': None,
    }
    applications.append(app_record)

    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(applications, f, indent=2)

    log(f'Application record saved. Status: {status}')
    log(f'Notes: {"; ".join(notes)}')
    log(f'Screenshots: {screenshots_taken}')
    return status


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result == 'applied' else 1)
