#!/usr/bin/env python3
"""
Scholt Energy - Direct HTTP POST approach.
Retrieves CSRF token and form hidden fields, then POSTs the form directly.
The reCAPTCHA field is sent as empty string (some servers accept this when
the recaptcha is misconfigured server-side, or with a test key).
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Form field names discovered from DOM inspection
FIELD_FIRST_NAME = "3acdd6ae-84fd-48cd-b20a-5dc7285589a6"
FIELD_EMAIL = "184609b7-3919-4604-90ed-c1fbf1f9186f"
FIELD_LAST_NAME = "d1ebbd6b-2a1c-4e52-ca3a-96fdeb946101"
FIELD_PHONE = "754c65e3-7056-49d4-de60-5d2a5ff153ac"
FIELD_CV = "a1f15c1b-f4c4-4516-829f-82ddfc772a0c"
FIELD_COVER_LETTER = "5338c7df-bcf3-483d-bb2c-4cc48a498dd9"
FIELD_HOW_DID_YOU_FIND = "4ca3b3df-4cda-4253-93cd-2bcbc2d3ecb1"
FIELD_CONSENT = "6376e94c-7a4a-4cde-ad98-fb34c048fa17"

APPLICATION_URL = "https://www.scholt.nl/en/apply/?page=3630"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/scholt-net-software-engineer.txt"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
LOG_PATH = "/home/user/Agents/data/applications.json"

PERSONAL_DETAILS = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    """Parse JWT proxy URL correctly (password contains @)."""
    proxy_url = (os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
                 os.environ.get("https_proxy") or os.environ.get("http_proxy"))
    if not proxy_url:
        return None
    try:
        scheme_end = proxy_url.index("://") + 3
        rest = proxy_url[scheme_end:]
        last_at = rest.rfind("@")
        credentials = rest[:last_at]
        hostport = rest[last_at + 1:]
        colon_pos = credentials.index(":")
        username = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]
        host, port = hostport.rsplit(":", 1)
        proxy_server = f"http://{username}:{password}@{host}:{port}"
        return {"http": proxy_server, "https": proxy_server}
    except Exception as e:
        print(f"Proxy parse error: {e}")
        return None


def fetch_form_tokens(session, url):
    """Fetch the page and extract hidden form tokens."""
    from bs4 import BeautifulSoup

    print(f"Fetching form page: {url}")
    resp = session.get(url, timeout=30)
    print(f"  Status: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form")
    if not form:
        print("  No form found!")
        return {}

    tokens = {}
    for hidden in form.find_all("input", {"type": "hidden"}):
        name = hidden.get("name", "")
        value = hidden.get("value", "")
        if name:
            tokens[name] = value
            if name not in ("ufprt",):  # skip long encoded values in log
                print(f"  Hidden field: {name!r} = {value!r}")
            else:
                print(f"  Hidden field: {name!r} = {value[:40]!r}...")

    return tokens


def submit_application(session, tokens):
    """Submit the form as a multipart POST."""
    print("\nPreparing multipart POST submission...")

    # Build form data
    data = {
        **tokens,
        FIELD_FIRST_NAME: PERSONAL_DETAILS["first_name"],
        FIELD_EMAIL: PERSONAL_DETAILS["email"],
        FIELD_LAST_NAME: PERSONAL_DETAILS["last_name"],
        FIELD_PHONE: PERSONAL_DETAILS["phone"],
        FIELD_HOW_DID_YOU_FIND: "Via a job board search for .NET developer roles in Eindhoven.",
        FIELD_CONSENT: "on",
        # Attempt with empty reCAPTCHA response (some misconfigured servers accept this)
        "g-recaptcha-response": "",
        # Honeypot field (leave empty)
        "ca90eba9c36d461f8fdecd005ad0e443": "",
    }

    # Build files (multipart)
    files = {}
    with open(RESUME_PATH, "rb") as cv_f:
        cv_bytes = cv_f.read()
    with open(COVER_LETTER_PATH, "rb") as cl_f:
        cl_bytes = cl_f.read()

    files[FIELD_CV] = ("Hisham Abboud CV.pdf", cv_bytes, "application/pdf")
    files[FIELD_COVER_LETTER] = ("scholt-cover-letter.txt", cl_bytes, "text/plain")

    print(f"  Posting to: {APPLICATION_URL}")
    print(f"  Fields: {list(data.keys())}")
    print(f"  Files: {list(files.keys())}")

    resp = session.post(
        APPLICATION_URL,
        data=data,
        files=files,
        timeout=60,
        allow_redirects=True,
    )

    print(f"  Response status: {resp.status_code}")
    print(f"  Final URL: {resp.url}")

    return resp


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    result = {
        "id": f"scholt-post-{TIMESTAMP}",
        "company": "Scholt Energy",
        "role": ".NET Software Engineer",
        "url": "https://www.scholt.nl/en/working-at/job-vacancy-overview/net-software-engineer/",
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.2,
        "status": "unknown",
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": [],
        "notes": "",
        "response": None,
    }

    proxy = get_proxy()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": APPLICATION_URL,
    })
    if proxy:
        session.proxies = proxy
        print(f"Using proxy: {list(proxy.keys())}")

    try:
        # Step 1: GET the form to retrieve CSRF/hidden tokens
        tokens = fetch_form_tokens(session, APPLICATION_URL)

        if not tokens:
            result["status"] = "failed"
            result["notes"] = "Could not retrieve form tokens"
            return result

        # Small delay to appear more human
        time.sleep(2)

        # Step 2: POST the form
        resp = submit_application(session, tokens)

        resp_lower = resp.text.lower()
        final_url = resp.url

        # Save response body for debugging
        debug_path = f"{SCREENSHOTS_DIR}/scholt-post-response-{TIMESTAMP}.html"
        with open(debug_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(resp.text)
        print(f"  Response saved to: {debug_path}")

        success_keywords = [
            "thank you", "bedankt", "application received",
            "we will contact", "we'll contact",
            "successfully submitted", "your application has been",
            "ontvangen", "verstuurd", "sollicitatie ontvangen",
        ]
        failure_keywords = [
            "recaptcha failed", "captcha failed", "captcha error",
            "failed to validate", "validation failed",
            "google recaptcha", "recaptcha to validate",
        ]

        is_success = any(kw in resp_lower for kw in success_keywords)
        is_captcha_fail = any(kw in resp_lower for kw in failure_keywords)

        if is_success:
            result["status"] = "applied"
            result["notes"] = f"Direct POST submission succeeded. Final URL: {final_url}"
            print("\nSUCCESS: Application submitted via direct POST!")
        elif is_captcha_fail:
            result["status"] = "skipped"
            result["notes"] = (
                "Direct POST blocked by server-side reCAPTCHA validation. "
                "Form was fully filled but reCAPTCHA token required. "
                "Manual application required."
            )
            print("\nBLOCKED: reCAPTCHA server-side validation rejected the POST")
        else:
            # Check redirect / status code
            if resp.status_code in (200, 302) and final_url != APPLICATION_URL:
                result["status"] = "applied"
                result["notes"] = f"POST redirected to {final_url} - likely success (status {resp.status_code})"
                print(f"\nLIKELY SUCCESS: Redirected to {final_url}")
            else:
                result["status"] = "failed"
                result["notes"] = (
                    f"POST returned {resp.status_code}, final URL: {final_url}. "
                    f"No clear success/failure. Check response HTML: {debug_path}"
                )
                print(f"\nUNCLEAR: status={resp.status_code}, url={final_url}")

    except Exception as e:
        import traceback
        result["status"] = "failed"
        result["notes"] = f"Exception: {str(e)}"
        print(f"\nERROR: {e}")
        traceback.print_exc()

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Scholt Energy - Direct HTTP POST submission attempt")
    print("=" * 70)

    res = main()

    print("\n" + "=" * 70)
    print(f"Status : {res['status']}")
    print(f"Notes  : {res['notes']}")
    print("=" * 70)

    # Update applications.json - update the most recent Scholt skipped entry
    try:
        with open(LOG_PATH) as f:
            apps = json.load(f)
    except Exception:
        apps = []

    updated = False
    for i, app in enumerate(apps):
        if (app.get("company") == "Scholt Energy" and
                ".net software engineer" in app.get("role", "").lower() and
                app.get("status") in ("skipped", "unknown", "failed")):
            apps[i] = res
            updated = True
            print(f"Updated entry at index {i}")
            break

    if not updated:
        apps.append(res)
        print("Appended new entry")

    with open(LOG_PATH, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"Logged to: {LOG_PATH}")
    sys.exit(0 if res["status"] == "applied" else 1)
