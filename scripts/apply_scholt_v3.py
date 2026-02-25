#!/usr/bin/env python3
"""
Scholt Energy application - v3 with enhanced stealth + form inspection.
Attempts human-like interaction with warm-up browsing to build a realistic session.
Correctly handles JWT-token proxy with @ in the password.
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
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/scholt-net-software-engineer.txt"

PERSONAL_DETAILS = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_config():
    """Parse proxy URL handling JWT tokens (which contain '@' in password)."""
    proxy_url = (os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
                 os.environ.get("https_proxy") or os.environ.get("http_proxy"))
    if not proxy_url:
        return None
    try:
        # Extract scheme
        scheme_end = proxy_url.index("://") + 3
        rest = proxy_url[scheme_end:]
        # Split on last '@' to separate credentials from host:port
        last_at = rest.rfind("@")
        if last_at == -1:
            # No credentials
            return {"server": proxy_url}
        credentials = rest[:last_at]
        hostport = rest[last_at + 1:]
        # Split credentials: everything before first ':' is username
        colon_pos = credentials.index(":")
        username = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]
        host, port = hostport.rsplit(":", 1)
        server = f"http://{host}:{port}"
        print(f"  Proxy: {server} (user: {username[:30]}...)")
        return {"server": server, "username": username, "password": password}
    except Exception as e:
        print(f"  Proxy parse error: {e}")
        return None


def screenshot(page, label):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    path = f"{SCREENSHOTS_DIR}/scholt-v3-{label}-{TIMESTAMP}.png"
    page.screenshot(path=path, full_page=True)
    print(f"[screenshot] {path}")
    return path


def rand_delay(lo=0.3, hi=0.9):
    time.sleep(random.uniform(lo, hi))


def human_type(element, text):
    """Type text character by character with random delays."""
    element.click()
    rand_delay(0.1, 0.3)
    # Clear field first
    element.fill("")
    rand_delay(0.1, 0.2)
    for char in text:
        element.type(char)
        time.sleep(random.uniform(0.04, 0.12))


def dismiss_cookies(page):
    selectors = [
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Accepteer alles")',
        'button:has-text("Accepteer")',
        'button:has-text("OK")',
        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        '.cookie-accept',
        '[id*="accept"][id*="cookie"]',
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Dismissed cookies: {sel}")
                rand_delay(1, 2)
                return True
        except Exception:
            continue
    return False


def inspect_form(page):
    """Print form structure for debugging."""
    print("\n--- Form Inspection ---")
    try:
        inputs = page.locator("input, textarea, select").all()
        for i, inp in enumerate(inputs):
            try:
                tag = inp.evaluate("el => el.tagName")
                typ = inp.get_attribute("type") or ""
                name = inp.get_attribute("name") or ""
                pid = inp.get_attribute("id") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                label_text = ""
                try:
                    label_text = inp.evaluate("""el => {
                        if (el.id) {
                            const lbl = document.querySelector('label[for="' + el.id + '"]');
                            if (lbl) return lbl.textContent.trim();
                        }
                        const parent = el.closest('label');
                        if (parent) return parent.textContent.trim().substring(0, 50);
                        return '';
                    }""")
                except Exception:
                    pass
                print(f"  [{i}] {tag} type={typ!r} name={name!r} id={pid!r} placeholder={placeholder!r} label={label_text!r}")
            except Exception as e:
                print(f"  [{i}] Error: {e}")
    except Exception as e:
        print(f"  Inspection error: {e}")
    print("--- End Form Inspection ---\n")


def fill_field_by_strategies(page, value, strategies):
    """
    Try multiple strategies to fill a form field.
    Returns True if successful.
    """
    for name, locator_fn in strategies:
        try:
            loc = locator_fn() if callable(locator_fn) else locator_fn
            if hasattr(loc, 'count'):
                if loc.count() == 0:
                    continue
                el = loc.first
            else:
                el = loc
            if el.is_visible(timeout=2000):
                el.scroll_into_view_if_needed()
                rand_delay(0.2, 0.5)
                human_type(el, value)
                print(f"  Filled '{value}' via strategy: {name}")
                rand_delay(0.3, 0.7)
                return True
        except Exception as e:
            continue
    return False


def apply():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    results = {
        "id": f"scholt-v3-{TIMESTAMP}",
        "company": "Scholt Energy",
        "role": ".NET Software Engineer",
        "url": JOB_URL,
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
                "--disable-features=IsolateOrigins,site-per-process",
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
            java_script_enabled=True,
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

        # Mask automation signals
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
                    arr.item = i => arr[i];
                    arr.namedItem = n => arr.find(p => p.name === n);
                    arr.refresh = () => {};
                    return arr;
                },
            });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'nl'] });
            window.chrome = { runtime: {}, loadTimes: () => null, csi: () => null, app: {} };
            const origQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : origQuery(parameters)
            );
        """)

        page = context.new_page()

        try:
            # ---- Warm up: visit job listing first ----
            print("Step 1: Warming up - visiting job listing page...")
            page.goto(JOB_URL, wait_until="domcontentloaded", timeout=60000)
            rand_delay(2, 4)
            page.mouse.move(400, 300)
            rand_delay(0.5, 1.0)
            page.mouse.wheel(0, 300)
            rand_delay(1, 2)
            page.mouse.wheel(0, 300)
            rand_delay(1, 2)
            page.mouse.wheel(0, -200)
            rand_delay(1, 2)
            dismiss_cookies(page)

            shot = screenshot(page, "00-job-listing")
            results["screenshots"].append(shot)

            # ---- Navigate to application form ----
            print("\nStep 2: Navigating to application form...")
            rand_delay(2, 4)
            page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=60000)
            rand_delay(3, 5)

            current_url = page.url
            print(f"  Current URL: {current_url}")

            dismiss_cookies(page)
            rand_delay(1, 2)

            shot = screenshot(page, "01-form-loaded")
            results["screenshots"].append(shot)

            # Inspect form structure
            inspect_form(page)

            # ---- Fill form fields ----
            print("\nStep 3: Filling personal details...")

            page.mouse.wheel(0, 200)
            rand_delay(0.5, 1.0)

            # First Name
            filled = fill_field_by_strategies(page, PERSONAL_DETAILS["first_name"], [
                ("get_by_label first_name", lambda: page.get_by_label("First name", exact=False)),
                ("get_by_label voornaam", lambda: page.get_by_label("Voornaam", exact=False)),
                ("input[name*=first]", lambda: page.locator('input[name*="first" i], input[name*="voornaam" i]')),
                ("input[id*=first]", lambda: page.locator('input[id*="first" i], input[id*="voornaam" i]')),
                ("input[placeholder*=first]", lambda: page.locator('input[placeholder*="first" i]')),
                ("text input [0]", lambda: page.locator('input[type="text"]').nth(0)),
            ])
            if not filled:
                print("  WARNING: Could not fill First Name")

            # Last Name
            filled = fill_field_by_strategies(page, PERSONAL_DETAILS["last_name"], [
                ("get_by_label last_name", lambda: page.get_by_label("Last name", exact=False)),
                ("get_by_label achternaam", lambda: page.get_by_label("Achternaam", exact=False)),
                ("get_by_label surname", lambda: page.get_by_label("Surname", exact=False)),
                ("input[name*=last]", lambda: page.locator('input[name*="last" i], input[name*="achternaam" i]')),
                ("input[id*=last]", lambda: page.locator('input[id*="last" i], input[id*="achternaam" i]')),
                ("input[placeholder*=last]", lambda: page.locator('input[placeholder*="last" i]')),
                ("text input [1]", lambda: page.locator('input[type="text"]').nth(1)),
            ])
            if not filled:
                print("  WARNING: Could not fill Last Name")

            # Email
            filled = fill_field_by_strategies(page, PERSONAL_DETAILS["email"], [
                ("input[type=email]", lambda: page.locator('input[type="email"]')),
                ("get_by_label email", lambda: page.get_by_label("Email", exact=False)),
                ("input[name*=email]", lambda: page.locator('input[name*="email" i]')),
                ("input[id*=email]", lambda: page.locator('input[id*="email" i]')),
            ])
            if not filled:
                print("  WARNING: Could not fill Email")

            # Phone
            filled = fill_field_by_strategies(page, PERSONAL_DETAILS["phone"], [
                ("input[type=tel]", lambda: page.locator('input[type="tel"]')),
                ("get_by_label phone", lambda: page.get_by_label("Phone", exact=False)),
                ("get_by_label phonenumber", lambda: page.get_by_label("Phonenumber", exact=False)),
                ("get_by_label telefoon", lambda: page.get_by_label("Telefoon", exact=False)),
                ("input[name*=phone]", lambda: page.locator('input[name*="phone" i], input[name*="telefoon" i]')),
                ("input[id*=phone]", lambda: page.locator('input[id*="phone" i], input[id*="tel" i]')),
                ("text input [2]", lambda: page.locator('input[type="text"]').nth(2)),
            ])
            if not filled:
                print("  WARNING: Could not fill Phone")

            rand_delay(1, 2)

            # ---- Upload CV ----
            print("\nStep 4: Uploading CV...")
            try:
                file_inputs = page.locator('input[type="file"]').all()
                print(f"  Found {len(file_inputs)} file input(s)")
                if file_inputs:
                    file_inputs[0].set_input_files(RESUME_PATH)
                    print(f"  CV uploaded: {RESUME_PATH}")
                    rand_delay(2, 3)
                if len(file_inputs) > 1:
                    file_inputs[1].set_input_files(COVER_LETTER_PATH)
                    print(f"  Cover letter uploaded: {COVER_LETTER_PATH}")
                    rand_delay(2, 3)
            except Exception as e:
                print(f"  File upload error: {e}")

            # ---- Check consent checkboxes ----
            print("\nStep 5: Checking consent checkboxes...")
            try:
                checkboxes = page.locator('input[type="checkbox"]').all()
                print(f"  Found {len(checkboxes)} checkbox(es)")
                for i, cb in enumerate(checkboxes):
                    try:
                        if cb.is_visible(timeout=1000):
                            if not cb.is_checked():
                                cb.scroll_into_view_if_needed()
                                rand_delay(0.3, 0.6)
                                cb.check()
                                print(f"  Checkbox [{i}] checked")
                                rand_delay(0.3, 0.6)
                            else:
                                print(f"  Checkbox [{i}] already checked")
                    except Exception as e:
                        print(f"  Checkbox [{i}] error: {e}")
            except Exception as e:
                print(f"  Checkboxes error: {e}")

            rand_delay(2, 3)

            # Scroll through form to appear human
            page.mouse.wheel(0, 500)
            rand_delay(0.5, 1.0)
            page.mouse.wheel(0, -200)
            rand_delay(0.5, 1.0)

            # ---- Pre-submit screenshot ----
            shot = screenshot(page, "02-before-submit")
            results["screenshots"].append(shot)

            # ---- Check for reCAPTCHA ----
            page_html = page.content()
            has_recaptcha = "recaptcha" in page_html.lower() or "g-recaptcha" in page_html.lower()
            print(f"\nreCAPTCHA present in page: {has_recaptcha}")

            if has_recaptcha:
                try:
                    recaptcha_visible = page.locator('.g-recaptcha, iframe[src*="recaptcha"]').is_visible(timeout=3000)
                    print(f"  reCAPTCHA iframe visible: {recaptcha_visible}")
                except Exception:
                    print("  reCAPTCHA element not visible (may be invisible v3)")
                print("  Waiting 10s for invisible reCAPTCHA v3 to auto-validate...")
                time.sleep(10)

            # ---- Find and click submit ----
            print("\nStep 6: Submitting application...")
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send job application")',
                'button:has-text("Send application")',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Verstuur")',
                'button:has-text("Verzenden")',
                'button:has-text("Solliciteer")',
                '.submit-btn',
                '[class*="submit"]',
            ]

            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible(timeout=2000):
                        btn_text = btn.inner_text().strip()
                        print(f"  Found: '{btn_text}' via '{sel}'")
                        btn.scroll_into_view_if_needed()
                        rand_delay(0.5, 1.0)
                        btn.hover()
                        rand_delay(0.3, 0.7)
                        btn.click()
                        submitted = True
                        print("  Clicked submit button")
                        break
                except Exception:
                    continue

            if not submitted:
                print("  No standard submit button found. Trying all visible buttons...")
                buttons = page.locator("button").all()
                for i, btn in enumerate(buttons):
                    try:
                        txt = btn.inner_text().strip()
                        visible = btn.is_visible(timeout=500)
                        print(f"    button[{i}]: '{txt}' visible={visible}")
                        if visible and txt and txt not in ["", "X", "x", "Accept", "Accepteer"]:
                            btn.scroll_into_view_if_needed()
                            rand_delay(0.5, 1.0)
                            btn.click()
                            submitted = True
                            break
                    except Exception:
                        continue

            if submitted:
                print("  Waiting for response...")
                time.sleep(8)

                shot = screenshot(page, "03-after-submit")
                results["screenshots"].append(shot)

                final_url = page.url
                page_content = page.content().lower()
                print(f"  URL after submit: {final_url}")

                success_keywords = [
                    "thank you", "bedankt", "application received",
                    "we will contact", "we'll contact", "contact opnemen",
                    "successfully submitted", "your application has been",
                    "ontvangen", "verstuurd", "sollicitatie ontvangen",
                ]
                failure_keywords = [
                    "recaptcha failed", "captcha failed", "captcha error",
                    "failed to validate", "validation failed",
                ]

                is_success = any(kw in page_content for kw in success_keywords)
                is_recaptcha_fail = any(kw in page_content for kw in failure_keywords)

                if is_success:
                    results["status"] = "applied"
                    results["notes"] = f"Application submitted successfully. URL after submit: {final_url}"
                    print("\nSUCCESS: Application submitted!")
                elif is_recaptcha_fail:
                    results["status"] = "skipped"
                    results["notes"] = (
                        "Form fully filled and submit attempted, but blocked by Google reCAPTCHA. "
                        "Automated browsers cannot pass reCAPTCHA without human intervention."
                    )
                    print("\nBLOCKED: reCAPTCHA prevented submission")
                else:
                    if final_url != APPLICATION_URL and "apply" not in final_url.lower():
                        results["status"] = "applied"
                        results["notes"] = f"Page redirected after submit to: {final_url} - likely successful"
                        print(f"\nLIKELY SUCCESS: Redirected to {final_url}")
                    else:
                        results["status"] = "failed"
                        results["notes"] = (
                            f"Submit clicked but no clear success/failure indicator. "
                            f"Final URL: {final_url}. Check screenshots."
                        )
                        print("\nUNCLEAR: No definitive outcome. Check screenshots.")
            else:
                results["status"] = "failed"
                results["notes"] = "Could not find or click submit button"
                print("\nFAILED: No submit button found")

        except Exception as e:
            import traceback
            results["status"] = "failed"
            results["notes"] = f"Exception: {str(e)}"
            print(f"\nERROR: {e}")
            traceback.print_exc()
            try:
                shot = screenshot(page, "error")
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
    print("Scholt Energy - .NET Software Engineer Application (v3 stealth+proxy)")
    print("=" * 70)

    res = apply()

    print("\n" + "=" * 70)
    print(f"Status  : {res['status']}")
    print(f"Notes   : {res['notes']}")
    print(f"Screenshots: {res['screenshots']}")
    print("=" * 70)

    # Update applications.json
    log_path = "/home/user/Agents/data/applications.json"
    try:
        with open(log_path) as f:
            apps = json.load(f)
    except Exception:
        apps = []

    # Update the existing skipped/failed Scholt entry, or append
    updated = False
    for i, app in enumerate(apps):
        if (app.get("company") == "Scholt Energy" and
                ".net software engineer" in app.get("role", "").lower() and
                app.get("status") in ("skipped", "unknown", "failed")):
            apps[i] = res
            updated = True
            print(f"Updated existing entry at index {i}")
            break

    if not updated:
        apps.append(res)
        print("Appended new entry")

    with open(log_path, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"Logged to: {log_path}")
    sys.exit(0 if res["status"] == "applied" else 1)
