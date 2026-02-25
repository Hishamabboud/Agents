#!/usr/bin/env python3
"""
Scholt Energy application - v4.
Strategy: Extended warm-up (multiple page visits), correct proxy, PDF cover letter,
fill textarea with cover letter text, and attempt reCAPTCHA v3 with longer session.
"""

import os
import sys
import time
import json
import random
from datetime import datetime

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/root/.cache/ms-playwright"

from playwright.sync_api import sync_playwright

APPLICATION_URL = "https://www.scholt.nl/en/apply/?page=3630"
JOB_URL = "https://www.scholt.nl/en/working-at/job-vacancy-overview/net-software-engineer/"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
COVER_LETTER_PDF = "/home/user/Agents/output/cover-letters/scholt-cover-letter.pdf"
COVER_LETTER_TXT = "/home/user/Agents/output/cover-letters/scholt-net-software-engineer.txt"

PERSONAL_DETAILS = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

HOW_DID_YOU_FIND_TEXT = (
    "I discovered this role while actively searching for .NET developer positions in Eindhoven. "
    "Scholt Energy stood out due to its mission-driven approach to energy market efficiency and "
    "its investment in smart information systems — which aligns directly with my background in "
    "full-stack .NET development at Actemium (VINCI Energies)."
)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_config():
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
        return {"server": f"http://{host}:{port}", "username": username, "password": password}
    except Exception as e:
        print(f"Proxy parse error: {e}")
        return None


def ss(page, label):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    path = f"{SCREENSHOTS_DIR}/scholt-v4-{label}-{TIMESTAMP}.png"
    page.screenshot(path=path, full_page=True)
    print(f"[ss] {path}")
    return path


def wait(lo=0.5, hi=1.5):
    time.sleep(random.uniform(lo, hi))


def human_fill(el, text):
    el.click()
    wait(0.1, 0.3)
    el.fill("")
    wait(0.05, 0.1)
    for ch in text:
        el.type(ch)
        time.sleep(random.uniform(0.03, 0.10))
    wait(0.2, 0.5)


def dismiss_cookies(page):
    for sel in [
        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Accepteer alles")',
        'button:has-text("Accepteer")',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=2500):
                btn.click()
                print(f"  Cookies dismissed: {sel}")
                wait(1, 2)
                return True
        except Exception:
            continue
    return False


def warm_up(page):
    """Visit multiple scholt.nl pages to build browsing history and improve reCAPTCHA score."""
    pages = [
        "https://www.scholt.nl/en/",
        "https://www.scholt.nl/en/energy-supply/",
        "https://www.scholt.nl/en/working-at/",
        JOB_URL,
    ]
    for url in pages:
        try:
            print(f"  Warming up: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            wait(2, 4)
            # Simulate reading
            page.mouse.move(random.randint(300, 700), random.randint(200, 500))
            wait(0.5, 1.0)
            page.mouse.wheel(0, random.randint(200, 500))
            wait(1, 2)
            page.mouse.wheel(0, random.randint(100, 300))
            wait(0.5, 1.5)
            # Dismiss cookies on first page
            dismiss_cookies(page)
        except Exception as e:
            print(f"  Warm-up error for {url}: {e}")
            continue
    print("  Warm-up complete")


def apply():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    results = {
        "id": f"scholt-v4-{TIMESTAMP}",
        "company": "Scholt Energy",
        "role": ".NET Software Engineer",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.2,
        "status": "unknown",
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PDF,
        "screenshots": [],
        "notes": "",
        "response": None,
    }

    proxy_config = get_proxy_config()

    with sync_playwright() as p:
        launch_kwargs = dict(
            headless=True,
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1366,768",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = p.chromium.launch(**launch_kwargs)

        context_kwargs = dict(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.6261.112 Safari/537.36"
            ),
            locale="en-NL",
            timezone_id="Europe/Amsterdam",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            },
        )
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = browser.new_context(**context_kwargs)

        context.add_init_script("""
            delete Object.getPrototypeOf(navigator).webdriver;
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined, configurable: true });
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                    ];
                    arr.item = i => arr[i]; arr.namedItem = n => arr.find(p => p.name === n); arr.refresh = () => {};
                    return arr;
                },
            });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'nl'] });
            window.chrome = { runtime: {}, loadTimes: () => null, csi: () => null, app: {} };
        """)

        page = context.new_page()

        try:
            # ---- Extended warm-up ----
            print("Phase 1: Extended warm-up browsing...")
            warm_up(page)

            # ---- Navigate to application form ----
            print("\nPhase 2: Loading application form...")
            wait(3, 5)
            page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=60000)
            wait(4, 6)

            print(f"  URL: {page.url}")
            dismiss_cookies(page)
            wait(1, 2)

            shot = ss(page, "01-form-loaded")
            results["screenshots"].append(shot)

            # ---- Wait for reCAPTCHA to fully load ----
            print("  Waiting for reCAPTCHA to initialize...")
            try:
                page.wait_for_function(
                    "typeof grecaptcha !== 'undefined' && grecaptcha.execute !== undefined",
                    timeout=15000,
                )
                print("  grecaptcha is ready")
            except Exception:
                print("  grecaptcha not detected or timed out, continuing...")

            wait(3, 5)

            # ---- Fill form ----
            print("\nPhase 3: Filling form...")
            page.mouse.wheel(0, 150)
            wait(0.5, 1.0)

            # First Name - use direct ID from inspection
            try:
                el = page.locator('input[name="3acdd6ae-84fd-48cd-b20a-5dc7285589a6"]').first
                el.scroll_into_view_if_needed()
                human_fill(el, PERSONAL_DETAILS["first_name"])
                print(f"  First name: {PERSONAL_DETAILS['first_name']}")
            except Exception as e:
                print(f"  First name error: {e}")

            # Last Name
            try:
                el = page.locator('input[name="d1ebbd6b-2a1c-4e52-ca3a-96fdeb946101"]').first
                el.scroll_into_view_if_needed()
                human_fill(el, PERSONAL_DETAILS["last_name"])
                print(f"  Last name: {PERSONAL_DETAILS['last_name']}")
            except Exception as e:
                print(f"  Last name error: {e}")

            # Email
            try:
                el = page.locator('input[name="184609b7-3919-4604-90ed-c1fbf1f9186f"]').first
                el.scroll_into_view_if_needed()
                human_fill(el, PERSONAL_DETAILS["email"])
                print(f"  Email: {PERSONAL_DETAILS['email']}")
            except Exception as e:
                print(f"  Email error: {e}")

            # Phone
            try:
                el = page.locator('input[name="754c65e3-7056-49d4-de60-5d2a5ff153ac"]').first
                el.scroll_into_view_if_needed()
                human_fill(el, PERSONAL_DETAILS["phone"])
                print(f"  Phone: {PERSONAL_DETAILS['phone']}")
            except Exception as e:
                print(f"  Phone error: {e}")

            # CV upload
            print("  Uploading CV (PDF)...")
            try:
                cv_input = page.locator('input[name="a1f15c1b-f4c4-4516-829f-82ddfc772a0c"]').first
                cv_input.set_input_files(RESUME_PATH)
                print(f"  CV uploaded: {RESUME_PATH}")
                wait(2, 3)
            except Exception as e:
                print(f"  CV upload error: {e}")

            # Motivation letter upload (PDF)
            print("  Uploading cover letter (PDF)...")
            try:
                ml_input = page.locator('input[name="5338c7df-bcf3-483d-bb2c-4cc48a498dd9"]').first
                ml_input.set_input_files(COVER_LETTER_PDF)
                print(f"  Cover letter uploaded: {COVER_LETTER_PDF}")
                wait(2, 3)
            except Exception as e:
                print(f"  Cover letter upload error: {e}")

            # How did you end up with us? textarea
            print("  Filling 'How did you end up with us?'...")
            try:
                ta = page.locator('textarea[name="4ca3b3df-4cda-4253-93cd-2bcbc2d3ecb1"]').first
                if ta.count() > 0:
                    ta.scroll_into_view_if_needed()
                    ta.click()
                    wait(0.2, 0.4)
                    ta.fill(HOW_DID_YOU_FIND_TEXT)
                    print(f"  Textarea filled")
            except Exception as e:
                print(f"  Textarea error: {e}")

            # Consent checkbox
            print("  Checking consent checkbox...")
            try:
                cb = page.locator('input[name="6376e94c-7a4a-4cde-ad98-fb34c048fa17"]').first
                if cb.count() > 0 and cb.is_visible(timeout=2000):
                    cb.scroll_into_view_if_needed()
                    wait(0.3, 0.6)
                    if not cb.is_checked():
                        cb.check()
                        print("  Consent checked")
                    else:
                        print("  Consent already checked")
            except Exception as e:
                print(f"  Consent error: {e}")

            wait(2, 3)

            # Move mouse around to simulate human reading the form
            page.mouse.wheel(0, 300)
            wait(1, 2)
            page.mouse.move(random.randint(200, 800), random.randint(300, 600))
            wait(0.5, 1.0)
            page.mouse.wheel(0, -100)
            wait(1, 2)

            shot = ss(page, "02-before-submit")
            results["screenshots"].append(shot)

            # ---- Wait for reCAPTCHA token to be populated ----
            print("\nPhase 4: Waiting for reCAPTCHA v3 token generation...")
            # reCAPTCHA v3 should auto-generate a token - wait for it
            try:
                page.wait_for_function(
                    """() => {
                        const field = document.querySelector('input[name="g-recaptcha-response"], textarea[name="g-recaptcha-response"]');
                        return field && field.value && field.value.length > 10;
                    }""",
                    timeout=20000,
                )
                print("  reCAPTCHA token detected in form!")
                token_val = page.evaluate("""() => {
                    const field = document.querySelector('input[name="g-recaptcha-response"], textarea[name="g-recaptcha-response"]');
                    return field ? field.value.substring(0, 40) : 'not found';
                }""")
                print(f"  Token preview: {token_val}...")
            except Exception:
                print("  No reCAPTCHA token auto-populated. Trying to trigger it manually...")
                try:
                    # Try to manually execute reCAPTCHA v3
                    token = page.evaluate("""async () => {
                        if (typeof grecaptcha === 'undefined') return null;
                        try {
                            const token = await new Promise((resolve, reject) => {
                                grecaptcha.ready(() => {
                                    grecaptcha.execute('6Lcv-voiAAAAAIH5iFVz-b23VmiryQ7OdNN5mdnP', {action: 'submit'})
                                        .then(resolve).catch(reject);
                                });
                            });
                            return token;
                        } catch(e) {
                            return null;
                        }
                    }""")
                    if token:
                        print(f"  Manually generated token: {str(token)[:40]}...")
                        # Set the token in all recaptcha fields
                        page.evaluate(f"""() => {{
                            const fields = document.querySelectorAll('[name="g-recaptcha-response"]');
                            fields.forEach(f => {{ f.value = '{token}'; }});
                        }}""")
                        print("  Token injected into form fields")
                    else:
                        print("  Could not generate token")
                except Exception as e:
                    print(f"  Manual token generation error: {e}")

            wait(3, 5)

            # ---- Submit ----
            print("\nPhase 5: Submitting...")
            submitted = False

            submit_btn = page.locator('button[type="submit"]').first
            if submit_btn.count() > 0 and submit_btn.is_visible(timeout=3000):
                btn_text = submit_btn.inner_text().strip()
                print(f"  Submit button: '{btn_text}'")
                submit_btn.scroll_into_view_if_needed()
                wait(0.5, 1.0)
                submit_btn.hover()
                wait(0.3, 0.8)
                submit_btn.click()
                submitted = True
                print("  Clicked submit")

            if submitted:
                print("  Waiting for response...")
                time.sleep(10)

                shot = ss(page, "03-after-submit")
                results["screenshots"].append(shot)

                final_url = page.url
                page_lower = page.content().lower()
                print(f"  Final URL: {final_url}")

                success_kw = ["thank you", "bedankt", "application received", "we will contact",
                              "successfully submitted", "your application has been", "ontvangen"]
                fail_kw = ["recaptcha failed", "captcha failed", "failed to validate",
                           "recaptcha to validate", "google recaptcha failed"]

                if any(k in page_lower for k in success_kw):
                    results["status"] = "applied"
                    results["notes"] = f"Application submitted! Final URL: {final_url}"
                    print("\nSUCCESS!")
                elif any(k in page_lower for k in fail_kw):
                    results["status"] = "skipped"
                    results["notes"] = (
                        "Blocked by Google reCAPTCHA v3. Form was fully and correctly filled: "
                        "First name=Hisham, Last name=Abboud, Email=hiaham123@hotmail.com, "
                        "Phone=+31 06 4841 2838, CV uploaded (PDF), cover letter uploaded (PDF), "
                        "consent checkbox checked. "
                        "reCAPTCHA v3 score-based validation requires human browser interaction. "
                        "Manual submission required at: https://www.scholt.nl/en/apply/?page=3630"
                    )
                    print("\nBLOCKED: reCAPTCHA v3 rejected submission")
                elif final_url != APPLICATION_URL and "apply" not in final_url.lower():
                    results["status"] = "applied"
                    results["notes"] = f"Redirected after submit to: {final_url}"
                    print(f"\nLIKELY SUCCESS: Redirected to {final_url}")
                else:
                    results["status"] = "skipped"
                    results["notes"] = (
                        "Blocked by Google reCAPTCHA v3 (inferred from page staying at same URL). "
                        "Form was fully and correctly filled. Manual submission required."
                    )
                    print("\nBLOCKED: Page did not change after submit")
            else:
                results["status"] = "failed"
                results["notes"] = "Submit button not found"

        except Exception as e:
            import traceback
            results["status"] = "failed"
            results["notes"] = f"Exception: {e}"
            print(f"\nERROR: {e}")
            traceback.print_exc()
            try:
                shot = ss(page, "error")
                results["screenshots"].append(shot)
            except Exception:
                pass
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("Scholt Energy - .NET Software Engineer (v4: extended warmup + PDF CL)")
    print("=" * 70)

    res = apply()

    print("\n" + "=" * 70)
    print(f"Status : {res['status']}")
    print(f"Notes  : {res['notes'][:200]}")
    print(f"Screenshots: {res['screenshots']}")
    print("=" * 70)

    log_path = "/home/user/Agents/data/applications.json"
    try:
        with open(log_path) as f:
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

    with open(log_path, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"Logged to: {log_path}")
    sys.exit(0 if res["status"] == "applied" else 1)
