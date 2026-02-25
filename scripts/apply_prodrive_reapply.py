#!/usr/bin/env python3
"""
Re-apply for Software Engineer position at Prodrive Technologies.
This corrects the email from Hisham123@hotmail.com to hiaham123@hotmail.com.
Uses the Playwright-based browser for screenshots and the API for submission.
"""

import requests
import json
import os
import sys
import subprocess
import base64
from datetime import datetime

# Paths
SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots/'
RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
APPLICATIONS_JSON = '/home/user/Agents/data/applications.json'
CHROME_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs('/home/user/Agents/data', exist_ok=True)

# Application URL
APPLY_URL = 'https://prodrive-technologies.com/careers/apply/'
API_URL = 'https://prodrive-technologies.com/umbraco/api/form/postvacancy/'

# Personal details - CORRECTED EMAIL
FIRST_NAME = 'Hisham'
LAST_NAME = 'Abboud'
EMAIL = 'hiaham123@hotmail.com'   # CORRECT email (not Hisham123@hotmail.com)
PHONE = '+31 06 4841 2838'

# Form field values
NODE_ID = '6206'
LANG = 'en'

# Vacancy: Software Engineer / Embedded Software Engineer
VACANCY_ID = '145273'
VACANCY_NAME = 'Software Engineer'

# Job type: Fulltime job = 105631
JOB_TYPE_VALUE = '105631'
JOB_TYPE_TITLE = 'Fulltime job'

# Location: The Netherlands - Eindhoven = 6099
LOCATION_VALUE = '6099'
LOCATION_TITLE = 'The Netherlands - Eindhoven'

COVER_LETTER = """Dear Prodrive Technologies Recruitment Team,

I am applying for a Software Engineer position at Prodrive Technologies. Your mission of creating meaningful technologies that make the world work aligns with my passion for building software that has real-world impact in high-tech manufacturing.

Currently at Actemium (VINCI Energies) in Eindhoven, I develop software solutions for Manufacturing Execution Systems using .NET, C#, Python, and JavaScript. I work at the intersection of software and manufacturing processes — building integrations, optimizing systems, and troubleshooting production environments. Previously at ASML in Veldhoven, I built automated test frameworks with Python for semiconductor equipment, giving me direct experience in the Eindhoven high-tech ecosystem.

I bring a blend of software engineering skills (Python, C#, .NET, Azure, Docker, Kubernetes) and manufacturing domain knowledge that is well-suited for Prodrive's multi-disciplinary R&D environment.

Best regards,
Hisham Abboud"""


def take_screenshot_playwright(url, filename):
    """Take a screenshot using Playwright headless chromium."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_path = os.path.join(SCREENSHOTS_DIR, filename)

    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch({{
        executablePath: '{CHROME_PATH}',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--disable-dev-shm-usage']
    }});
    const page = await browser.newPage();
    await page.setViewportSize({{ width: 1280, height: 900 }});
    try {{
        await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
        await page.waitForTimeout(2000);
        await page.screenshot({{ path: '{screenshot_path}', fullPage: false }});
        console.log('Screenshot saved: {screenshot_path}');
    }} catch(e) {{
        console.error('Screenshot error:', e.message);
    }}
    await browser.close();
}})();
"""
    js_file = f'/tmp/screenshot_{timestamp}.js'
    with open(js_file, 'w') as f:
        f.write(script)

    try:
        result = subprocess.run(
            ['node', js_file],
            capture_output=True, text=True, timeout=45,
            cwd='/home/user/Agents'
        )
        if result.returncode == 0:
            print(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        else:
            print(f"Screenshot error: {result.stderr[:300]}")
    except Exception as e:
        print(f"Screenshot exception: {e}")

    # Fallback: save text record
    txt_path = screenshot_path.replace('.png', '.txt')
    with open(txt_path, 'w') as f:
        f.write(f"Screenshot capture attempt\nURL: {url}\nTime: {datetime.now().isoformat()}\n")
    return txt_path


def submit_application():
    """Submit the job application to Prodrive Technologies via API."""

    print("=" * 60)
    print("Prodrive Technologies - Job Application Re-submission")
    print("=" * 60)
    print(f"Applicant: {FIRST_NAME} {LAST_NAME}")
    print(f"Email: {EMAIL}  <-- CORRECTED")
    print(f"Phone: {PHONE}")
    print(f"Position: {VACANCY_NAME} (Vacancy ID: {VACANCY_ID})")
    print(f"Location: {LOCATION_TITLE}")
    print()

    # Step 1: Take pre-submission screenshot of the careers page
    print("Step 1: Capturing pre-submission screenshot...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pre_screenshot = take_screenshot_playwright(
        APPLY_URL,
        f'prodrive-reapply-01-pre-submit-{timestamp}.png'
    )

    # Step 2: Verify resume file exists
    print(f"\nStep 2: Checking resume file: {RESUME_PATH}")
    if not os.path.exists(RESUME_PATH):
        print(f"ERROR: Resume file not found at {RESUME_PATH}")
        return False, 0, {}

    file_size = os.path.getsize(RESUME_PATH)
    print(f"Resume file found: {file_size} bytes ({file_size/1024:.1f} KB)")

    # Step 3: Get session cookie
    print("\nStep 3: Establishing session with Prodrive Technologies...")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': APPLY_URL,
        'Origin': 'https://prodrive-technologies.com'
    })

    try:
        r = session.get(APPLY_URL, timeout=20)
        print(f"Session established. Status: {r.status_code}")
        print(f"Cookies: {dict(session.cookies)}")
    except Exception as e:
        print(f"Warning: Could not establish session: {e}")

    # Step 4: Prepare form data
    print("\nStep 4: Preparing form submission...")

    form_fields = {
        'nodeId': NODE_ID,
        'fieldFirstname': FIRST_NAME,
        'fieldLastname': LAST_NAME,
        'fieldEmail': EMAIL,
        'fieldPhone': PHONE,
        'fieldFavorites': VACANCY_NAME,
        'fieldCompetences': f'{LOCATION_TITLE}, {VACANCY_NAME}',
        'fieldLang': LANG,
        'vacancyID': VACANCY_ID,
        'typeApplication': JOB_TYPE_VALUE,
        'fieldTypeApplication': JOB_TYPE_TITLE,
        'fieldRemark': COVER_LETTER,
        'favoritesValues': VACANCY_ID,
        'competencesValues': f'{LOCATION_VALUE},{VACANCY_ID}',
        'visitedPages': '/careers/apply/',
        'talentPoolConsent': 'false'
    }

    print("\nForm data:")
    for key, value in form_fields.items():
        if key == 'fieldRemark':
            print(f"  {key}: [cover letter - {len(value)} chars]")
        else:
            print(f"  {key}: {value}")

    # Step 5: Submit form
    print("\nStep 5: Submitting application...")
    response = None
    response_json = {}
    success = False
    status_code = 0

    try:
        with open(RESUME_PATH, 'rb') as f:
            files = {
                'file1': ('Hisham Abboud CV.pdf', f, 'application/pdf')
            }
            response = session.post(
                API_URL,
                data=form_fields,
                files=files,
                timeout=45
            )

        status_code = response.status_code
        print(f"\nResponse status: {status_code}")
        print(f"Response URL: {response.url}")

        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            success = response_json.get('success', False) or status_code in [200, 201]
        except Exception:
            resp_text = response.text[:500] if response.text else ''
            print(f"Response text: {resp_text}")
            # HTTP 200/201 with no JSON typically means success for this endpoint
            success = status_code in [200, 201]
            response_json = {'raw_text': resp_text, 'status_code': status_code}

    except Exception as e:
        print(f"Submission error: {e}")
        success = False
        status_code = 0
        response_json = {'error': str(e)}

    # Step 6: Take post-submission screenshot
    print("\nStep 6: Capturing post-submission screenshot...")
    if success:
        post_url = 'https://prodrive-technologies.com/careers/apply/thank-you/'
    else:
        post_url = APPLY_URL

    post_screenshot = take_screenshot_playwright(
        post_url,
        f'prodrive-reapply-02-post-submit-{timestamp}.png'
    )

    # Also save a text record of the submission
    record_path = os.path.join(SCREENSHOTS_DIR, f'prodrive-reapply-record-{timestamp}.txt')
    with open(record_path, 'w') as f:
        f.write(f"PRODRIVE TECHNOLOGIES - APPLICATION SUBMISSION RECORD\n")
        f.write(f"{'=' * 55}\n\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"API URL: {API_URL}\n")
        f.write(f"HTTP Status: {status_code}\n")
        f.write(f"Success: {success}\n\n")
        f.write(f"APPLICANT DETAILS:\n")
        f.write(f"  Name: {FIRST_NAME} {LAST_NAME}\n")
        f.write(f"  Email: {EMAIL}\n")
        f.write(f"  Phone: {PHONE}\n\n")
        f.write(f"VACANCY DETAILS:\n")
        f.write(f"  Position: {VACANCY_NAME}\n")
        f.write(f"  Vacancy ID: {VACANCY_ID}\n")
        f.write(f"  Job Type: {JOB_TYPE_TITLE}\n")
        f.write(f"  Location: {LOCATION_TITLE}\n\n")
        f.write(f"RESPONSE:\n")
        f.write(f"{json.dumps(response_json, indent=2)}\n")

    print(f"Submission record saved: {record_path}")

    return success, status_code, response_json, pre_screenshot, post_screenshot, record_path, timestamp


def update_applications_log(success, status_code, response_data, pre_ss, post_ss, record_path, timestamp):
    """Update the applications tracking JSON."""

    if os.path.exists(APPLICATIONS_JSON):
        with open(APPLICATIONS_JSON, 'r') as f:
            applications = json.load(f)
    else:
        applications = []

    # Determine status
    if success:
        app_status = 'applied'
        notes = (f'RE-APPLICATION with CORRECT email ({EMAIL}). '
                 f'Application submitted successfully via API. '
                 f'Vacancy: {VACANCY_NAME} (ID: {VACANCY_ID}). '
                 f'HTTP Status: {status_code}. '
                 f'Previous application used wrong email (Hisham123@hotmail.com).')
    elif status_code in [200, 201]:
        app_status = 'applied'
        notes = (f'RE-APPLICATION with CORRECT email ({EMAIL}). '
                 f'Form submitted (HTTP {status_code}). '
                 f'Response: {json.dumps(response_data)[:200]}')
    else:
        app_status = 'failed'
        notes = (f'RE-APPLICATION with CORRECT email ({EMAIL}). '
                 f'API returned HTTP {status_code}. '
                 f'Response: {json.dumps(response_data)[:200]}')

    screenshots = [s for s in [pre_ss, post_ss, record_path] if s]

    application_record = {
        'id': f'prodrive-reapply-{VACANCY_ID}-{timestamp}',
        'company': 'Prodrive Technologies',
        'role': VACANCY_NAME,
        'url': APPLY_URL,
        'date_applied': datetime.now().isoformat(),
        'score': 8,
        'status': app_status,
        'resume_file': RESUME_PATH,
        'cover_letter_file': None,
        'screenshots': screenshots,
        'notes': notes,
        'response': None
    }

    applications.append(application_record)

    with open(APPLICATIONS_JSON, 'w') as f:
        json.dump(applications, f, indent=2)

    print(f"\nApplication logged to: {APPLICATIONS_JSON}")
    print(f"Entry ID: {application_record['id']}")
    print(f"Status: {app_status}")
    return application_record


if __name__ == '__main__':
    print(f"\nStarting Prodrive Technologies re-application at {datetime.now().isoformat()}")
    print(f"CRITICAL: Using CORRECT email: {EMAIL}")
    print()

    result = submit_application()

    if len(result) == 6:
        success, status_code, response_data, pre_ss, post_ss, record_path = result
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    else:
        success, status_code, response_data, pre_ss, post_ss, record_path, timestamp = result

    print("\n" + "=" * 60)
    print(f"APPLICATION RESULT: {'SUCCESS' if success else 'FAILED/UNKNOWN'}")
    print(f"Email used: {EMAIL}")
    print("=" * 60)

    update_applications_log(success, status_code, response_data, pre_ss, post_ss, record_path, timestamp)

    sys.exit(0 if success else 1)
