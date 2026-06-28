#!/usr/bin/env python3
"""
Complete Catawiki Greenhouse application by entering the email verification code.

Usage:
  python3 submit_with_code.py <8-character-security-code>

The security code was sent to hiaham123@hotmail.com after the initial form submission.
"""

import sys
import json
import subprocess
import time
import uuid
import re

def get_presigned_url():
    """Get fresh presigned S3 URL for resume upload."""
    result = subprocess.run([
        'curl', '-s',
        'https://boards.greenhouse.io/uncacheable_attributes/presigned_fields?fields%5B%5D=resume&job_post_id=7960442'
    ], capture_output=True, text=True)
    return json.loads(result.stdout)

def upload_resume(s3_data):
    """Upload resume to S3 and return the URL."""
    s3_url = s3_data['url']
    fields = s3_data['resume']['fields']
    key_template = s3_data['resume']['key']
    key = key_template.replace('{timestamp}', str(int(time.time() * 1000))).replace('{unique_id}', uuid.uuid4().hex[:16])
    
    cmd = [
        'curl', '-s', '-X', 'POST', s3_url,
        '-F', f'key={key}',
        '-F', 'utf8=✓',
        '-F', 'authenticity_token=',
        '-F', f'x-amz-server-side-encryption={fields["x-amz-server-side-encryption"]}',
        '-F', f'success_action_status={fields["success_action_status"]}',
        '-F', f'policy={fields["policy"]}',
        '-F', f'x-amz-credential={fields["x-amz-credential"]}',
        '-F', f'x-amz-algorithm={fields["x-amz-algorithm"]}',
        '-F', f'x-amz-date={fields["x-amz-date"]}',
        '-F', f'x-amz-signature={fields["x-amz-signature"]}',
        '-F', 'Content-Type=application/pdf',
        '-F', 'file=@/home/user/Agents/profile/Hisham Abboud CV.pdf;type=application/pdf',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    m = re.search(r'<Location>(.*?)</Location>', result.stdout)
    if m:
        url = m.group(1)
        print(f"Resume uploaded to S3: {url[:80]}...")
        return url, 'Hisham Abboud CV.pdf'
    else:
        raise Exception(f"S3 upload failed: {result.stdout[:300]}")

def submit_application(security_code, resume_url, resume_filename):
    """Submit the application with the security code."""
    cover_letter = open('/home/user/Agents/output/cover-letters/catawiki-junior-se.md').read()
    cover_letter = re.sub(r'\*\*(.+?)\*\*', r'\1', cover_letter)
    cover_letter = re.sub(r'^---+$', '', cover_letter, flags=re.MULTILINE).strip()
    
    payload = {
        "job_application": {
            "first_name": "Hisham",
            "last_name": "Abboud",
            "email": "hiaham123@hotmail.com",
            "phone": "+310648412838",
            "cover_letter_text": cover_letter,
            "location": "Eindhoven, Netherlands",
            "country_short_name": "NL",
            "resume_url": resume_url,
            "resume_url_filename": resume_filename,
            "answers_attributes": {
                "67402957": {"question_id": "67402957", "priority": 0, "boolean_value": 1},
                "67402958": {"question_id": "67402958", "priority": 1, "boolean_value": 1},
                "67219247": {"question_id": "67219247", "priority": 2, "text_value": "https://linkedin.com/in/hisham-abboud"},
                "67402959": {"question_id": "67402959", "priority": 3, "text_value": "Job board / Online search"}
            },
            "demographic_answers": [],
            "data_compliance": {},
            "attachments": {},
            "from_job_board_renderer": True,
            "employments": []
        },
        "g-recaptcha-enterprise-token": "",
        "security_code": security_code,
        "fingerprint": "d28e45bd5af855f0e9672138efb9ca9d8e906256"
    }
    
    with open('/tmp/catawiki_final_payload.json', 'w') as f:
        json.dump(payload, f)
    
    result = subprocess.run([
        'curl', '-s', '-X', 'POST',
        'https://boards.greenhouse.io/catawiki/jobs/7960442',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json',
        '-H', 'Origin: https://job-boards.greenhouse.io',
        '-H', 'Referer: https://job-boards.greenhouse.io/catawiki/jobs/7960442',
        '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        '-d', json.dumps(payload),
        '-w', '\nHTTP_CODE:%{http_code}',
    ], capture_output=True, text=True)
    
    output = result.stdout
    http_code_match = re.search(r'HTTP_CODE:(\d+)', output)
    http_code = int(http_code_match.group(1)) if http_code_match else 0
    body = output.rsplit('\nHTTP_CODE:', 1)[0]
    
    return http_code, body

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    security_code = sys.argv[1].strip()
    print(f"Security code: {security_code}")
    
    print("Getting fresh S3 presigned URL...")
    s3_data = get_presigned_url()
    
    print("Uploading resume to S3...")
    resume_url, resume_filename = upload_resume(s3_data)
    
    print(f"Submitting application with security code '{security_code}'...")
    http_code, body = submit_application(security_code, resume_url, resume_filename)
    
    print(f"\nHTTP Status: {http_code}")
    print(f"Response: {body[:500]}")
    
    if http_code in (200, 201):
        print("\nSUCCESS: Application submitted!")
        # Update applications.json
        with open('/home/user/Agents/data/applications.json') as f:
            apps = json.load(f)
        for app in apps:
            if 'catawiki' in app.get('company', '').lower():
                app['status'] = 'applied'
                app['response'] = 'submitted'
                break
        with open('/home/user/Agents/data/applications.json', 'w') as f:
            json.dump(apps, f, indent=2)
        print("Updated applications.json: status=applied")
    elif http_code == 428:
        resp = json.loads(body)
        if resp.get('code') == 'invalid-security-code':
            print("\nERROR: Invalid security code. Double-check the code from email.")
        elif resp.get('code') == 'expired-security-code':
            print("\nERROR: Security code expired. Re-run the browser submission to get a new code.")
        else:
            print(f"\nCAPTCHA issue: {body}")
    else:
        print(f"\nUnexpected response (HTTP {http_code}): {body[:300]}")
