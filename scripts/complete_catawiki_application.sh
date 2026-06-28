#!/bin/bash
# Complete Catawiki application with email verification code
# Usage: bash complete_catawiki_application.sh <8-CHARACTER-CODE>
#
# After running the Playwright submission, Greenhouse sends an 8-character
# verification code to hiaham123@hotmail.com
# Check that inbox and run this script with the code.

SECURITY_CODE="$1"

if [ -z "$SECURITY_CODE" ]; then
  echo "Usage: $0 <8-character-security-code>"
  echo "Example: $0 AB12CD34"
  exit 1
fi

echo "Submitting Catawiki application with security code: $SECURITY_CODE"

# Re-upload resume to get a fresh S3 URL (the old one may have expired)
echo "Getting fresh S3 presigned URLs..."
S3_DATA=$(curl -s "https://boards.greenhouse.io/uncacheable_attributes/presigned_fields?fields%5B%5D=resume&job_post_id=7960442")
S3_URL=$(echo "$S3_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['url'])")
RESUME_KEY=$(echo "$S3_DATA" | python3 -c "import json,sys,time,uuid; d=json.load(sys.stdin); k=d['resume']['key'].replace('{timestamp}', str(int(time.time()*1000))).replace('{unique_id}', uuid.uuid4().hex[:16]); print(k)")

echo "Uploading resume to S3..."
echo "$S3_DATA" | python3 -c "
import json, sys, subprocess

data = json.load(sys.stdin)
s3_url = data['url']
fields = data['resume']['fields']
key_template = data['resume']['key']

import time, uuid
key = key_template.replace('{timestamp}', str(int(time.time()*1000))).replace('{unique_id}', uuid.uuid4().hex[:16])

cmd = [
    'curl', '-s', '-X', 'POST', s3_url,
    '-F', f'key={key}',
    '-F', 'utf8=✓',
    '-F', 'authenticity_token=',
    '-F', f'x-amz-server-side-encryption={fields[\"x-amz-server-side-encryption\"]}',
    '-F', f'success_action_status={fields[\"success_action_status\"]}',
    '-F', f'policy={fields[\"policy\"]}',
    '-F', f'x-amz-credential={fields[\"x-amz-credential\"]}',
    '-F', f'x-amz-algorithm={fields[\"x-amz-algorithm\"]}',
    '-F', f'x-amz-date={fields[\"x-amz-date\"]}',
    '-F', f'x-amz-signature={fields[\"x-amz-signature\"]}',
    '-F', 'Content-Type=application/pdf',
    '-F', 'file=@/home/user/Agents/profile/Hisham Abboud CV.pdf;type=application/pdf',
]
result = subprocess.run(cmd, capture_output=True, text=True)
# Extract Location from XML
import re
m = re.search(r'<Location>(.*?)</Location>', result.stdout)
if m:
    print(m.group(1))
else:
    print('ERROR: ' + result.stdout[:200])
"

