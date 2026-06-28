import re

with open("/tmp/greenhouse-response.html") as f:
    html = f.read()

# Find form action
form_actions = re.findall(r'action=["\']([^"\']+)["\']', html)
print("Form actions:", form_actions[:5])

# Find any API endpoints
api_refs = re.findall(r'"(/[^"]{5,80})"', html)
api_refs = [r for r in api_refs if "api" in r.lower() or "submit" in r.lower() or "application" in r.lower()]
print("API refs:", api_refs[:10])

# Find file upload endpoint
gon_match = re.search(r'gon\s*=\s*({[^;]+});', html)
if gon_match:
    print("GON data found:", gon_match.group(1)[:500])

# Find board token or job_id
board_token = re.findall(r'board_token["\'\s:=]+([^,"\'}\s]+)', html)
print("board_token:", board_token[:3])

job_ids = re.findall(r'"id"\s*:\s*([0-9]+)', html)
print("IDs found:", job_ids[:5])

# React props / initial state
state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.{0,500}})', html)
if state_match:
    print("Initial state:", state_match.group(1)[:300])

# Find any fetch or axios calls in scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, script in enumerate(scripts):
    if any(kw in script for kw in ["submit", "POST", "application", "upload"]):
        print(f"\nScript {i} (relevant):", script[:800])

# Find the Greenhouse job post ID
job_post = re.findall(r'job_post_id["\'\s:=]+([0-9]+)', html)
print("job_post_id:", job_post[:3])

# Look for the apply API URL
apply_url = re.findall(r'"(https?://[^"]*apply[^"]{0,100})"', html)
print("Apply URLs:", apply_url[:5])
