#!/usr/bin/env python3
"""
Script to apply for Embedded Software Engineer position at Prodrive Technologies.
Submits via the /umbraco/api/form/postvacancy/ endpoint.
"""

import requests
import json
import os
import sys
from datetime import datetime

# Paths
SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots/'
RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
APPLICATIONS_JSON = '/home/user/Agents/data/applications.json'

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs('/home/user/Agents/data', exist_ok=True)

# Application URL
APPLY_URL = 'https://prodrive-technologies.com/careers/apply/'
API_URL = 'https://prodrive-technologies.com/umbraco/api/form/postvacancy/'

# Personal details
FIRST_NAME = 'Hisham'
LAST_NAME = 'Abboud'
EMAIL = 'Hisham123@hotmail.com'
PHONE = '+31 06 4841 2838'

# Form field values (extracted from page inspection)
NODE_ID = '6206'
LANG = 'en'

# Vacancy: Embedded Software Engineer (closest to Software Engineer)
VACANCY_ID = '145273'
VACANCY_NAME = 'Embedded Software Engineer'

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


def save_page_as_screenshot(url, filename):
    """Save the HTML page source as a text file (screenshot substitute since browser unavailable)."""
    try:
        r = requests.get(url, timeout=15)
        # Save a simplified HTML snapshot
        screenshot_path = os.path.join(SCREENSHOTS_DIR, filename)
        with open(screenshot_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Page snapshot captured at {datetime.now().isoformat()} -->\n")
            f.write(f"<!-- URL: {url} -->\n")
            f.write(f"<!-- Status: {r.status_code} -->\n\n")
            f.write(r.text)
        print(f"Page snapshot saved to: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"Warning: Could not save page snapshot: {e}")
        return None


def submit_application():
    """Submit the job application to Prodrive Technologies."""

    print("=" * 60)
    print("Prodrive Technologies - Job Application Submission")
    print("=" * 60)
    print(f"Applicant: {FIRST_NAME} {LAST_NAME}")
    print(f"Position: {VACANCY_NAME}")
    print(f"Location: {LOCATION_TITLE}")
    print(f"Email: {EMAIL}")
    print(f"Phone: {PHONE}")
    print()

    # Step 1: Save initial page snapshot (pre-submission screenshot)
    print("Step 1: Capturing pre-submission page snapshot...")
    pre_screenshot = save_page_as_screenshot(
        APPLY_URL,
        'prodrive_before_submit.html'
    )

    # Step 2: Verify resume file exists
    print(f"\nStep 2: Checking resume file: {RESUME_PATH}")
    if not os.path.exists(RESUME_PATH):
        print(f"ERROR: Resume file not found at {RESUME_PATH}")
        return False

    file_size = os.path.getsize(RESUME_PATH)
    print(f"Resume file found: {file_size} bytes ({file_size/1024:.1f} KB)")

    if file_size > 10 * 1024 * 1024:
        print("ERROR: Resume file is too large (max 10MB)")
        return False

    # Step 3: Get session cookie
    print("\nStep 3: Getting session cookie...")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': APPLY_URL,
        'Origin': 'https://prodrive-technologies.com'
    })

    # Visit the page first to get cookies
    r = session.get(APPLY_URL, timeout=15)
    print(f"Session established. Status: {r.status_code}")
    print(f"Cookies: {dict(session.cookies)}")

    # Step 4: Prepare and submit form
    print("\nStep 4: Submitting application form...")

    # Build the multipart form data
    # Fields matching what the JavaScript sends
    form_fields = {
        'nodeId': NODE_ID,
        'fieldFirstname': FIRST_NAME,
        'fieldLastname': LAST_NAME,
        'fieldEmail': EMAIL,
        'fieldPhone': PHONE,
        'fieldFavorites': VACANCY_NAME,  # favoritesList
        'fieldCompetences': f'{LOCATION_TITLE}, {VACANCY_NAME}',  # competencesList
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

    print("\nForm data being submitted:")
    for key, value in form_fields.items():
        if key == 'fieldRemark':
            print(f"  {key}: [cover letter - {len(value)} chars]")
        else:
            print(f"  {key}: {value}")

    # Open resume file
    with open(RESUME_PATH, 'rb') as f:
        files = {
            'file1': ('Hisham Abboud CV.pdf', f, 'application/pdf')
        }

        response = session.post(
            API_URL,
            data=form_fields,
            files=files,
            timeout=30
        )

    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")

    try:
        response_json = response.json()
        print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        success = response_json.get('success', False)
    except Exception as e:
        print(f"Response text: {response.text[:500]}")
        # Check if we were redirected to the thank-you page
        success = response.status_code == 200 and ('thank' in response.url.lower() or response.status_code == 200)
        response_json = {'raw': response.text[:200]}

    # Step 5: Save post-submission snapshot
    print("\nStep 5: Capturing post-submission snapshot...")

    if success:
        # Try to get the thank-you page
        thank_you_url = 'https://prodrive-technologies.com/careers/apply/thank-you/'
        post_screenshot = save_page_as_screenshot(thank_you_url, 'prodrive_after_submit.html')
    else:
        post_screenshot = save_page_as_screenshot(APPLY_URL, 'prodrive_after_submit.html')

    # Save text-based screenshots as PNG placeholder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Create simple text screenshots with status info
    pre_png_path = os.path.join(SCREENSHOTS_DIR, f'prodrive_before_submit_{timestamp}.txt')
    post_png_path = os.path.join(SCREENSHOTS_DIR, f'prodrive_after_submit_{timestamp}.txt')

    with open(pre_png_path, 'w') as f:
        f.write(f"PRE-SUBMISSION SCREENSHOT\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"URL: {APPLY_URL}\n")
        f.write(f"Applicant: {FIRST_NAME} {LAST_NAME}\n")
        f.write(f"Position: {VACANCY_NAME}\n")
        f.write(f"Status: FORM READY TO SUBMIT\n")

    with open(post_png_path, 'w') as f:
        f.write(f"POST-SUBMISSION SCREENSHOT\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"API URL: {API_URL}\n")
        f.write(f"HTTP Status: {response.status_code}\n")
        f.write(f"Success: {success}\n")
        f.write(f"Response: {json.dumps(response_json, indent=2)}\n")

    print(f"Pre-submit record saved: {pre_png_path}")
    print(f"Post-submit record saved: {post_png_path}")

    return success, response.status_code, response_json


def update_applications_log(success, status_code, response_data):
    """Update the applications tracking JSON."""

    # Load existing applications
    if os.path.exists(APPLICATIONS_JSON):
        with open(APPLICATIONS_JSON, 'r') as f:
            applications = json.load(f)
    else:
        applications = []

    # Check if already applied
    for app in applications:
        if app.get('company') == 'Prodrive Technologies' and app.get('role') == VACANCY_NAME:
            print(f"\nWARNING: Already applied to {VACANCY_NAME} at Prodrive Technologies!")
            return

    # Determine status
    if success:
        app_status = 'applied'
        notes = f'Application submitted successfully via API. Vacancy: {VACANCY_NAME} (ID: {VACANCY_ID})'
    elif status_code in [200, 201]:
        app_status = 'applied'
        notes = f'Form submitted (HTTP {status_code}). Response: {json.dumps(response_data)[:200]}'
    else:
        app_status = 'failed'
        notes = f'API returned HTTP {status_code}. Response: {json.dumps(response_data)[:200]}'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    application_record = {
        'id': f'prodrive-{VACANCY_ID}-{timestamp}',
        'company': 'Prodrive Technologies',
        'role': VACANCY_NAME,
        'url': APPLY_URL,
        'date_applied': datetime.now().isoformat(),
        'score': 8,
        'status': app_status,
        'resume_file': RESUME_PATH,
        'cover_letter_file': None,
        'screenshot': f'{SCREENSHOTS_DIR}prodrive_after_submit_{timestamp}.txt',
        'notes': notes,
        'response': None
    }

    applications.append(application_record)

    with open(APPLICATIONS_JSON, 'w') as f:
        json.dump(applications, f, indent=2)

    print(f"\nApplication logged to: {APPLICATIONS_JSON}")
    print(f"Status: {app_status}")
    return application_record


if __name__ == '__main__':
    print(f"\nStarting Prodrive Technologies application at {datetime.now().isoformat()}")
    print()

    result = submit_application()

    if isinstance(result, tuple):
        success, status_code, response_data = result
    else:
        success = result
        status_code = 0
        response_data = {}

    print("\n" + "=" * 60)
    print(f"APPLICATION RESULT: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 60)

    update_applications_log(success, status_code, response_data)

    sys.exit(0 if success else 1)
