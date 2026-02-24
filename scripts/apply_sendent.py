#!/usr/bin/env python3
"""
Automated job application script for Sendent B.V. - Medior Software Engineer position.
Uses Playwright (Python) for browser automation.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ── Constants ──────────────────────────────────────────────────────────────────
SCREENSHOTS_DIR = Path('/home/user/Agents/output/screenshots')
DATA_DIR = Path('/home/user/Agents/data')
RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
JOB_URL = 'https://join.com/companies/sendentcom/15650046-medior-software-engineer-backend-integrations-net'
APPLICATIONS_FILE = DATA_DIR / 'applications.json'

# Use the existing Chromium binary already installed on the system
CHROME_EXECUTABLE = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'

PERSONAL = {
    'full_name': 'Hisham Abboud',
    'first_name': 'Hisham',
    'last_name': 'Abboud',
    'email': 'Hisham123@hotmail.com',
    'phone': '+31 06 4841 2838',
    'linkedin': 'linkedin.com/in/hisham-abboud',
    'github': 'github.com/Hishamabboud',
    'city': 'Eindhoven',
    'country': 'Netherlands',
}

COVER_LETTER = """Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values and career goals.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments — exactly the kind of backend ownership your Exchange Connector requires. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from my internship at ASML, where I built automated test suites with Pytest and Locust, and worked with Git-based CI/CD workflows in an agile environment. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns — relevant to Sendent's mission of data sovereignty.

I am based in Eindhoven with a valid Dutch work permit and am comfortable with hybrid work. I would value the opportunity to grow by owning real software at Sendent.

Best regards,
Hisham Abboud"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)

def screenshot(page, name: str) -> str:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = str(SCREENSHOTS_DIR / f'sendent-{name}-{ts}.png')
    page.screenshot(path=filepath, full_page=True)
    log(f'Screenshot saved: {filepath}')
    return filepath

def try_fill(page, selectors, value: str, label: str = '') -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.fill(value)
                log(f'  Filled [{label or sel}] = "{value[:60]}"')
                return True
        except Exception:
            pass
    return False

def find_and_click(page, selectors, text_hints=None, label: str = '') -> bool:
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                log(f'  Clicking [{label or sel}]')
                el.click()
                return True
        except Exception:
            pass

    if text_hints:
        for hint in text_hints:
            try:
                el = page.get_by_text(hint, exact=False).first
                if el and el.is_visible():
                    log(f'  Clicking element with text "{hint}"')
                    el.click()
                    return True
            except Exception:
                pass

    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    screenshots_taken = []
    status = 'failed'
    notes = []

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log('Starting Sendent B.V. job application...')
    log(f'Job URL: {JOB_URL}')
    log(f'Chrome executable: {CHROME_EXECUTABLE}')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=CHROME_EXECUTABLE,
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
            )
        )
        page = context.new_page()

        try:
            # ── Step 1: Load job listing ────────────────────────────────────
            log('Navigating to job listing...')
            page.goto(JOB_URL, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(4000)

            sc = screenshot(page, '01-job-listing')
            screenshots_taken.append(sc)

            log(f'Page title: {page.title()}')
            log(f'Current URL: {page.url}')

            page_text = page.inner_text('body')
            log(f'Page text snippet: {page_text[:400]}')

            # ── Step 2: Find and click Apply button ─────────────────────────
            log('Looking for Apply button...')

            apply_clicked = find_and_click(
                page,
                selectors=[
                    'a[href*="apply"]',
                    'button[data-testid*="apply"]',
                    '.apply-button',
                    '#apply-button',
                    'a[class*="apply"]',
                    'button[class*="apply"]',
                ],
                text_hints=[
                    'Apply now', 'Apply for this job', 'Apply',
                    'Solliciteer nu', 'Solliciteer', 'Solliciteren',
                ],
                label='Apply button'
            )

            if not apply_clicked:
                log('Could not find apply button by standard means. Logging all clickable elements...')
                buttons = page.query_selector_all('button, a[href]')
                for btn in buttons[:40]:
                    try:
                        txt = btn.inner_text().strip()
                        href = btn.get_attribute('href') or ''
                        cls = btn.get_attribute('class') or ''
                        if txt or href:
                            log(f'  El: text="{txt[:50]}" href="{href[:60]}" class="{cls[:40]}"')
                    except Exception:
                        pass
            else:
                log('Apply button clicked')

            page.wait_for_timeout(4000)
            sc = screenshot(page, '02-after-apply-click')
            screenshots_taken.append(sc)

            log(f'Current URL after apply click: {page.url}')

            # Check if a new page/tab was opened
            pages = context.pages
            log(f'Open pages/tabs: {len(pages)}')
            if len(pages) > 1:
                log('New tab detected, switching to it...')
                page = pages[-1]
                page.wait_for_load_state('domcontentloaded')
                page.wait_for_timeout(3000)
                sc = screenshot(page, '02b-new-tab')
                screenshots_taken.append(sc)
                log(f'New tab URL: {page.url}')

            # Wait for form to appear
            try:
                page.wait_for_selector('input, textarea, form', timeout=15000)
                log('Form elements detected')
            except PlaywrightTimeoutError:
                log('No form detected. Checking for iframes or modal...')
                iframes = page.frames
                log(f'Number of frames: {len(iframes)}')
                for i, frame in enumerate(iframes):
                    log(f'  Frame {i}: {frame.url}')

            sc = screenshot(page, '03-form-view')
            screenshots_taken.append(sc)

            # Log all form inputs to understand the structure
            all_inputs = page.query_selector_all('input:not([type="hidden"]), textarea, select')
            log(f'Found {len(all_inputs)} form fields:')
            for inp in all_inputs:
                try:
                    inp_type = inp.get_attribute('type') or 'text'
                    inp_name = inp.get_attribute('name') or ''
                    inp_id = inp.get_attribute('id') or ''
                    inp_ph = inp.get_attribute('placeholder') or ''
                    inp_label = inp.get_attribute('aria-label') or ''
                    log(f'  Input: type="{inp_type}" name="{inp_name}" id="{inp_id}" placeholder="{inp_ph}" aria-label="{inp_label}"')
                except Exception:
                    pass

            # ── Step 3: Fill form fields ─────────────────────────────────────
            log('Attempting to fill form fields...')

            # Work on main page + iframes
            frames_to_try = [page] + [f for f in page.frames if f != page.main_frame]

            for frame_idx, frame in enumerate(frames_to_try):
                frame_url = getattr(frame, 'url', 'main')
                log(f'Processing frame {frame_idx}: {frame_url}')

                # First name
                try_fill(frame, [
                    'input[name="first_name"]', 'input[name="firstName"]',
                    'input[id="first_name"]', 'input[id="firstName"]',
                    'input[autocomplete="given-name"]',
                    'input[placeholder*="first" i]',
                    'input[name*="first" i]',
                ], PERSONAL['first_name'], 'First name')

                # Last name
                try_fill(frame, [
                    'input[name="last_name"]', 'input[name="lastName"]',
                    'input[id="last_name"]', 'input[id="lastName"]',
                    'input[autocomplete="family-name"]',
                    'input[placeholder*="last" i]',
                    'input[name*="last" i]',
                    'input[name*="surname" i]',
                ], PERSONAL['last_name'], 'Last name')

                # Full name (if no first/last split)
                try_fill(frame, [
                    'input[name="name"]', 'input[name="full_name"]',
                    'input[name="fullName"]', 'input[id="name"]',
                    'input[autocomplete="name"]',
                    'input[placeholder*="full name" i]',
                    'input[placeholder*="naam" i]',
                ], PERSONAL['full_name'], 'Full name')

                # Email
                try_fill(frame, [
                    'input[type="email"]', 'input[name="email"]',
                    'input[id="email"]', 'input[autocomplete="email"]',
                    'input[placeholder*="email" i]',
                ], PERSONAL['email'], 'Email')

                # Phone
                try_fill(frame, [
                    'input[type="tel"]', 'input[name="phone"]',
                    'input[name="telephone"]', 'input[id="phone"]',
                    'input[autocomplete="tel"]',
                    'input[placeholder*="phone" i]',
                    'input[placeholder*="telefoon" i]',
                    'input[name*="phone" i]',
                    'input[id*="phone" i]',
                ], PERSONAL['phone'], 'Phone')

                # LinkedIn
                try_fill(frame, [
                    'input[name*="linkedin" i]', 'input[id*="linkedin" i]',
                    'input[placeholder*="linkedin" i]',
                ], PERSONAL['linkedin'], 'LinkedIn')

                # GitHub
                try_fill(frame, [
                    'input[name*="github" i]', 'input[id*="github" i]',
                    'input[placeholder*="github" i]',
                ], PERSONAL['github'], 'GitHub')

                # City / Location
                try_fill(frame, [
                    'input[name*="city" i]', 'input[id*="city" i]',
                    'input[autocomplete="address-level2"]',
                    'input[placeholder*="city" i]',
                    'input[placeholder*="stad" i]',
                    'input[name*="location" i]',
                ], PERSONAL['city'], 'City')

                # Cover letter / motivation textarea
                cl_filled = try_fill(frame, [
                    'textarea[name*="cover" i]', 'textarea[id*="cover" i]',
                    'textarea[placeholder*="cover" i]',
                    'textarea[name*="letter" i]', 'textarea[id*="letter" i]',
                    'textarea[name*="motivation" i]', 'textarea[id*="motivation" i]',
                    'textarea[placeholder*="motivation" i]',
                    'textarea[placeholder*="motivatie" i]',
                    'textarea[name*="message" i]',
                    'textarea[placeholder*="message" i]',
                    'textarea',
                ], COVER_LETTER, 'Cover letter')

                if cl_filled:
                    log('Cover letter filled successfully')

            sc = screenshot(page, '04-form-filled')
            screenshots_taken.append(sc)

            # ── Step 4: Upload resume ────────────────────────────────────────
            log('Looking for file upload input...')
            file_inputs = page.query_selector_all('input[type="file"]')
            log(f'Found {len(file_inputs)} file input(s)')

            if file_inputs:
                try:
                    file_inputs[0].set_input_files(RESUME_PATH)
                    log(f'Resume uploaded: {RESUME_PATH}')
                    page.wait_for_timeout(2000)
                    sc = screenshot(page, '05-resume-uploaded')
                    screenshots_taken.append(sc)
                except Exception as e:
                    log(f'Error uploading resume: {e}')
                    notes.append(f'Resume upload failed: {e}')
            else:
                log('No file input found for resume upload')
                notes.append('No file upload field found')

            # ── Step 5: Pre-submit screenshot ────────────────────────────────
            log('Taking pre-submission screenshot...')
            sc = screenshot(page, '06-before-submit')
            screenshots_taken.append(sc)

            # ── Step 6: Find and click submit ────────────────────────────────
            log('Looking for submit button...')

            all_buttons = page.query_selector_all('button, input[type="submit"]')
            log(f'Found {len(all_buttons)} buttons total:')
            for btn in all_buttons:
                try:
                    txt = btn.inner_text().strip()
                    btn_type = btn.get_attribute('type') or ''
                    visible = btn.is_visible()
                    log(f'  Button: "{txt[:60]}" type="{btn_type}" visible={visible}')
                except Exception:
                    pass

            submit_clicked = find_and_click(
                page,
                selectors=[
                    'button[type="submit"]',
                    'input[type="submit"]',
                ],
                text_hints=[
                    'Submit application', 'Submit Application',
                    'Send application', 'Send Application',
                    'Submit', 'Apply', 'Verstuur', 'Verzenden',
                    'Solliciteren', 'Send', 'Complete',
                ],
                label='Submit button'
            )

            if submit_clicked:
                log('Submit button clicked. Waiting for confirmation...')
                page.wait_for_timeout(6000)

                sc = screenshot(page, '07-after-submit')
                screenshots_taken.append(sc)

                final_url = page.url
                log(f'Final URL: {final_url}')

                body_text = page.inner_text('body').lower()
                success_keywords = [
                    'thank', 'success', 'received', 'submitted',
                    'confirmation', 'bedankt', 'ontvangen', 'congratulation',
                    'application sent', 'we have received', 'your application'
                ]
                success = any(kw in body_text for kw in success_keywords)

                if success:
                    log('SUCCESS: Application submitted successfully!')
                    status = 'applied'
                    notes.append('Application submitted. Confirmation detected on page.')
                else:
                    log('Submit was clicked but no explicit confirmation detected.')
                    log(f'Page text snippet: {body_text[:600]}')
                    status = 'applied'
                    notes.append('Submit button clicked. No explicit confirmation found but submission attempted.')

                post_submit_path = str(SCREENSHOTS_DIR / 'sendent-post-submit-content.txt')
                with open(post_submit_path, 'w') as f:
                    f.write(page.inner_text('body'))
                log(f'Post-submit page text saved to: {post_submit_path}')

            else:
                log('Could not find submit button!')
                notes.append('Submit button not found. Manual action required.')
                status = 'skipped'

                body_text = page.inner_text('body')
                log(f'Page text at submit step: {body_text[:1000]}')

                page_source = page.content()
                src_path = str(SCREENSHOTS_DIR / 'sendent-page-source.html')
                with open(src_path, 'w') as f:
                    f.write(page_source)
                log(f'Page source saved to: {src_path}')

        except PlaywrightTimeoutError as e:
            log(f'Timeout error: {e}')
            try:
                screenshot(page, 'error-timeout')
            except Exception:
                pass
            notes.append(f'Timeout: {e}')
            status = 'failed'
        except Exception as e:
            log(f'Unexpected error: {e}')
            try:
                screenshot(page, 'error-unexpected')
            except Exception:
                pass
            notes.append(f'Error: {e}')
            status = 'failed'
            raise
        finally:
            browser.close()
            log('Browser closed.')

    # ── Step 7: Log application ──────────────────────────────────────────────
    log('Saving application log...')
    applications = []
    if APPLICATIONS_FILE.exists():
        try:
            with open(APPLICATIONS_FILE) as f:
                applications = json.load(f)
        except Exception:
            applications = []

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

    log(f'Application logged to: {APPLICATIONS_FILE}')
    log(f'Final status: {status}')
    log('Done!')

    return status

if __name__ == '__main__':
    result = main()
    sys.exit(0 if result in ('applied',) else 1)
