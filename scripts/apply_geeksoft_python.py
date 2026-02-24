#!/usr/bin/env python3
"""
Apply to GeekSoft Consulting - Python Developer position
via ZohoRecruit career site.
Job URL: https://geeksoftconsulting.zohorecruit.eu/jobs/Current-Openings/1321000014924545
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path('/home/user/Agents')
SCREENSHOT_DIR = BASE_DIR / 'output' / 'screenshots'
APPLICATIONS_FILE = BASE_DIR / 'data' / 'applications.json'
CV_FILE = BASE_DIR / 'profile' / 'Hisham Abboud CV.pdf'

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
JOB_URL = 'https://geeksoftconsulting.zohorecruit.eu/jobs/Current-Openings/1321000014924545'

APPLICANT = {
    'first_name': 'Hisham',
    'last_name': 'Abboud',
    'name': 'Hisham Abboud',
    'email': 'hiaham123@hotmail.com',
    'phone': '+31648412838',
    'linkedin': 'linkedin.com/in/hisham-abboud',
    'location': 'Eindhoven, Netherlands',
}

COVER_LETTER = """Dear GeekSoft Consulting Hiring Team,

I am writing to express my strong interest in the Python Developer position at GeekSoft Consulting. As a software engineer with hands-on Python experience in both professional and personal projects, I am excited about the opportunity to contribute to your team.

During my internship at ASML, I developed and maintained Python-based test frameworks using Locust and Pytest, working in a high-tech manufacturing environment with strict quality standards. At Actemium, I am currently building production Python/Flask applications, giving me practical experience with backend development and CI/CD practices.

I also built CogitatAI, a personal AI project with a Python/Flask backend, demonstrating my ability to design and implement scalable Python solutions independently.

My BSc in Software Engineering from Fontys University, combined with my experience in Agile methodologies, Git workflows, and modern DevOps practices, makes me well-suited for the fast-paced environment you describe.

I am based in Eindhoven and am enthusiastic about joining GeekSoft Consulting. I look forward to discussing how my Python skills and engineering background can contribute to your projects.

Kind regards,
Hisham Abboud
hiaham123@hotmail.com
+31648412838
linkedin.com/in/hisham-abboud"""


def take_screenshot(page, name: str) -> str:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"geeksoft-{name}-{TIMESTAMP}.png"
    path = str(SCREENSHOT_DIR / filename)
    try:
        page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
    except Exception as e:
        print(f"Screenshot failed ({name}): {e}")
        path = ''
    return path


def save_application(status: str, screenshots: list, notes: str, url: str = JOB_URL):
    APPLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if APPLICATIONS_FILE.exists():
        with open(APPLICATIONS_FILE) as f:
            apps = json.load(f)
    else:
        apps = []

    app_id = f"geeksoft-python-dev-{TIMESTAMP}"
    entry = {
        "id": app_id,
        "company": "GeekSoft Consulting",
        "role": "Python Developer",
        "url": JOB_URL,
        "application_url": url,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": str(CV_FILE),
        "cover_letter_file": None,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": APPLICANT['email'],
    }
    apps.append(entry)
    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(apps, f, indent=2)
    print(f"Application logged: {status} -> {APPLICATIONS_FILE}")
    return app_id


def run():
    print(f"Starting GeekSoft Python Developer application...")
    print(f"CV: {CV_FILE}")
    print(f"Email: {APPLICANT['email']}")
    print(f"Job URL: {JOB_URL}")

    screenshots = []
    notes_parts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
        )
        page = context.new_page()

        # Remove webdriver flag
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        try:
            print(f"Navigating to job listing: {JOB_URL}")
            page.goto(JOB_URL, wait_until='networkidle', timeout=30000)
            time.sleep(2)

            current_url = page.url
            title = page.title()
            print(f"Page loaded: {title} | URL: {current_url}")
            ss = take_screenshot(page, '01-job-listing')
            screenshots.append(ss)
            notes_parts.append(f"Job page loaded: {title}")

            # Look for "I'm interested" / Apply button
            apply_button = None
            apply_selectors = [
                "text=I'm interested",
                "text=Apply Now",
                "text=Apply",
                "text=Solliciteer",
                "[class*='apply']",
                "button[class*='apply']",
                ".zr-apply-btn",
                ".apply-btn",
                "[data-action='apply']",
            ]

            for selector in apply_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible(timeout=2000):
                        apply_button = btn
                        print(f"Found apply button: {selector}")
                        break
                except Exception:
                    continue

            if not apply_button:
                # Try by text content
                try:
                    apply_button = page.get_by_text("I'm interested", exact=False).first
                    apply_button.is_visible(timeout=2000)
                    print("Found apply button via text")
                except Exception:
                    pass

            if apply_button:
                print("Clicking apply button...")
                apply_button.click()
                time.sleep(3)
                ss = take_screenshot(page, '02-after-apply-click')
                screenshots.append(ss)
                current_url = page.url
                print(f"After click URL: {current_url}")
                notes_parts.append(f"Apply button clicked. URL: {current_url}")
            else:
                print("No apply button found - trying direct navigation to apply form")
                notes_parts.append("No apply button found, attempting direct form navigation")

            # Check if we're now on an application form
            # ZohoRecruit application forms are usually in iframes or on a new page
            time.sleep(2)

            # Check for iframe
            frames = page.frames
            print(f"Frames on page: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")

            # Try to fill the form - ZohoRecruit form fields
            form_filled = False

            # First check if there's a modal or form directly on page
            # ZohoRecruit typically opens a form with fields like firstname, lastname, email, phone, resume
            field_selectors = {
                'firstname': ['[name="firstname"]', '[id*="first"]', 'input[placeholder*="First"]', 'input[placeholder*="first"]'],
                'lastname': ['[name="lastname"]', '[id*="last"]', 'input[placeholder*="Last"]', 'input[placeholder*="last"]'],
                'email': ['[name="email"]', '[type="email"]', 'input[placeholder*="Email"]', 'input[placeholder*="email"]'],
                'phone': ['[name="phone"]', '[name="mobile"]', 'input[placeholder*="Phone"]', 'input[placeholder*="phone"]'],
            }

            for field_name, selectors in field_selectors.items():
                for selector in selectors:
                    try:
                        el = page.locator(selector).first
                        if el.count() > 0 and el.is_visible(timeout=2000):
                            value = APPLICANT.get(field_name, '')
                            if field_name == 'firstname':
                                value = APPLICANT['first_name']
                            elif field_name == 'lastname':
                                value = APPLICANT['last_name']
                            el.fill(value)
                            print(f"Filled {field_name}: {value}")
                            form_filled = True
                            break
                    except Exception:
                        continue

            if form_filled:
                ss = take_screenshot(page, '03-form-filling')
                screenshots.append(ss)

            # ZohoRecruit SPA - let's check if we're in the portal
            # Check for candidate form page
            current_url = page.url
            if 'portal.html' in current_url or 'apply' in current_url.lower():
                print(f"On application form page: {current_url}")
                # Try to fill form in the current page/frame
                time.sleep(2)

            # Re-check all frames after clicking apply
            frames = page.frames
            application_frame = None
            for frame in frames:
                frame_url = frame.url
                if 'recruit' in frame_url.lower() or 'apply' in frame_url.lower() or 'candidate' in frame_url.lower():
                    print(f"Found application frame: {frame_url}")
                    application_frame = frame
                    break

            # If we found a form frame, fill it
            working_context = application_frame if application_frame else page

            # Try to find and fill form fields
            try:
                # Look for name fields
                firstname_filled = False
                lastname_filled = False
                email_filled = False
                phone_filled = False
                cv_uploaded = False

                # First name variations
                for selector in ['input[name*="first"]', 'input[placeholder*="First"]', 'input[id*="first"]',
                                  'input[name="First_Name"]', '#First_Name', 'input[name="Candidate_Name"]']:
                    try:
                        el = working_context.locator(selector).first
                        if el.is_visible(timeout=2000):
                            el.fill(APPLICANT['first_name'])
                            firstname_filled = True
                            print(f"First name filled via {selector}")
                            break
                    except Exception:
                        pass

                # Last name
                for selector in ['input[name*="last"]', 'input[placeholder*="Last"]', 'input[id*="last"]',
                                  'input[name="Last_Name"]', '#Last_Name']:
                    try:
                        el = working_context.locator(selector).first
                        if el.is_visible(timeout=2000):
                            el.fill(APPLICANT['last_name'])
                            lastname_filled = True
                            print(f"Last name filled via {selector}")
                            break
                    except Exception:
                        pass

                # Email
                for selector in ['input[type="email"]', 'input[name*="email"]', 'input[name="Email"]',
                                  'input[placeholder*="Email"]', '#Email']:
                    try:
                        el = working_context.locator(selector).first
                        if el.is_visible(timeout=2000):
                            el.fill(APPLICANT['email'])
                            email_filled = True
                            print(f"Email filled via {selector}")
                            break
                    except Exception:
                        pass

                # Phone
                for selector in ['input[type="tel"]', 'input[name*="phone"]', 'input[name*="mobile"]',
                                  'input[placeholder*="Phone"]', '#Mobile', '#Phone']:
                    try:
                        el = working_context.locator(selector).first
                        if el.is_visible(timeout=2000):
                            el.fill(APPLICANT['phone'])
                            phone_filled = True
                            print(f"Phone filled via {selector}")
                            break
                    except Exception:
                        pass

                notes_parts.append(f"Fields: firstname={firstname_filled}, lastname={lastname_filled}, email={email_filled}, phone={phone_filled}")

                # Upload CV
                for selector in ['input[type="file"]', 'input[name*="resume"]', 'input[name*="cv"]',
                                  'input[accept*="pdf"]', '.resume-upload input']:
                    try:
                        el = working_context.locator(selector).first
                        if el.count() > 0:
                            el.set_input_files(str(CV_FILE))
                            cv_uploaded = True
                            print(f"CV uploaded via {selector}")
                            time.sleep(2)
                            break
                    except Exception:
                        pass

                notes_parts.append(f"CV uploaded: {cv_uploaded}")

                ss = take_screenshot(page, '04-form-filled')
                screenshots.append(ss)

            except Exception as e:
                print(f"Error filling form: {e}")
                notes_parts.append(f"Error filling form: {e}")
                ss = take_screenshot(page, '04-error')
                screenshots.append(ss)

            # Check current page state
            print(f"\nCurrent URL after form attempt: {page.url}")
            print(f"Page title: {page.title()}")

            # Check if form is visible on the page at all
            body_text = page.inner_text('body')[:500] if page.locator('body').count() > 0 else ''
            print(f"Body text preview: {body_text[:200]}")
            notes_parts.append(f"Page state: URL={page.url}, title={page.title()}")

        except PlaywrightTimeoutError as e:
            print(f"Timeout error: {e}")
            notes_parts.append(f"Timeout: {e}")
            ss = take_screenshot(page, 'timeout-error')
            screenshots.append(ss)
        except Exception as e:
            print(f"Unexpected error: {e}")
            notes_parts.append(f"Error: {e}")
            try:
                ss = take_screenshot(page, 'error')
                screenshots.append(ss)
            except Exception:
                pass
        finally:
            browser.close()

    status = "applied" if any("Form" in n for n in notes_parts) else "in_progress"
    app_id = save_application(
        status="in_progress",
        screenshots=[s for s in screenshots if s],
        notes=" | ".join(notes_parts),
        url=JOB_URL
    )
    print(f"\nApplication ID: {app_id}")
    return app_id


if __name__ == '__main__':
    run()
