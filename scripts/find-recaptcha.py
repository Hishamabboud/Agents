import requests
import re

r = requests.get("https://boards.greenhouse.io/clickhouse/jobs/5803692004", timeout=20)
print("Status:", r.status_code)

# Find recaptcha site key
site_keys = re.findall(r'data-sitekey=["\']([^"\']+)["\']', r.text)
print("reCAPTCHA data-sitekey:", site_keys)

# Find in window.ENV
env_match = re.search(r'window\.ENV\s*=\s*({[^;]+})', r.text)
if env_match:
    env_str = env_match.group(1)
    recaptcha_refs = re.findall(r'"([^"]*[Rr]ecaptcha[^"]*)"[^:]*:\s*"([^"]*)"', env_str)
    print("Env recaptcha keys:", recaptcha_refs)
    # Just print the env
    print("ENV:", env_str[:800])

# Security code endpoint
security = re.findall(r'security.code[^"\'<>]{0,100}', r.text, re.IGNORECASE)
print("Security code refs:", security[:5])

# API endpoint for verifying code
verify_endpoints = re.findall(r'"/[^"]*verif[^"]*"', r.text, re.IGNORECASE)
print("Verify endpoints:", verify_endpoints[:5])
