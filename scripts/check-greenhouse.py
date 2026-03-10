import requests
import re
import json

r = requests.get(
    "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004",
    timeout=20,
    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)
print("Status:", r.status_code)
print("Content length:", len(r.text))

# Look for form fields
fields = re.findall(r'name="(job_application[^"]+)"', r.text)
print("Form fields found:", fields[:30])

# Look for authenticity token
token_match = re.search(r'authenticity_token[^>]+value="([^"]+)"', r.text)
if token_match:
    print("CSRF token found:", token_match.group(1)[:20] + "...")
else:
    print("No CSRF token found")

# Check if it's a SPA or server-rendered
if "application/json" in r.headers.get("content-type", ""):
    print("JSON response")
elif "<form" in r.text.lower():
    print("HTML form present")
else:
    print("No HTML form - may be React SPA")

# Save snippet
with open("/tmp/greenhouse-response.html", "w") as f:
    f.write(r.text)
print("Full response saved to /tmp/greenhouse-response.html")
