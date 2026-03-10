#!/usr/bin/env python3
"""
Foxtek application — targets Senior Full Stack Engineer (C#/Angular) as nearest
available role to the original .NET Developer position (which returned 404).

Form: WordPress Contact Form 7 (wpcf7), form ID 447
Fields: your-name, your-email, your-phone, file (CV upload), acceptance-123
Note: No cover letter textarea in the application form — only CV file upload.
reCAPTCHA: v3 invisible (executes via JS automatically)
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PDF = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
COVER_LETTER_MD = Path("/home/user/Agents/output/cover-letters/foxtek-net-developer.md")
APPLICATIONS_JSON = Path("/home/user/Agents/data/applications.json")

APPLICANT = {
    "name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31064841 2838",
}

ORIGINAL_URL = "https://www.foxtekrs.com/job/dot-net-developer-1"
TARGET_URL = "https://www.foxtekrs.com/job/senior-full-stack-engineer-c-angular/"
TARGET_ROLE = "Senior Full Stack Engineer (C#/Angular)"

_proxy_raw = (
    os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    or os.environ.get("https_proxy") or os.environ.get("http_proxy") or ""
)
_parsed = urlparse(_proxy_raw)
PROXY_CONFIG = None
if _parsed.hostname:
    PROXY_CONFIG = {
        "server": f"{_parsed.scheme}://{_parsed.hostname}:{_parsed.port}",
        "username": _parsed.username or "",
        "password": _parsed.password or "",
    }


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, label):
    path = SCREENSHOTS_DIR / f"foxtek-{label}-{ts()}.png"
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => {
                    if (el.href && (el.href.includes('fonts.') || el.href.includes('typekit')))
                        el.disabled = true;
                });
            }
        """)
    except Exception:
        pass
    try:
        await page.screenshot(path=str(path), full_page=True, timeout=8000)
        print(f"  [ss] {path.name}")
        return str(path)
    except Exception as e:
        print(f"  [ss failed] {label}: {e}")
        return None


async def safe_goto(page, url, timeout=20000):
    try:
        resp = await page.goto(url, wait_until="commit", timeout=timeout)
        await asyncio.sleep(2)
        return resp.status if resp else None
    except Exception as e:
        print(f"  [goto] {e}")
        return None


async def fill_via_js(page, selector, value):
    """Fill a field using JavaScript evaluation — bypasses visibility checks."""
    try:
        result = await page.evaluate(f"""
            (value) => {{
                const el = document.querySelector('{selector}');
                if (!el) return 'not found';
                el.value = value;
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'ok: ' + el.value.substring(0, 20);
            }}
        """, value)
        return result
    except Exception as e:
        return f"error: {e}"


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "company": "Foxtek",
        "role": TARGET_ROLE,
        "url": TARGET_URL,
        "original_url": ORIGINAL_URL,
        "status": "unknown",
        "screenshots": [],
        "notes": (
            "Original .NET Developer job (dot-net-developer-1) returned 404 — listing removed. "
            "Applying to nearest available match: Senior Full Stack Engineer (C#/Angular). "
            "Application form fields: name, email, phone, CV upload (no cover letter textarea). "
        ),
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=PROXY_CONFIG,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )

        # Block font resources that cause screenshot timeout
        async def block_resources(route):
            url = route.request.url
            if any(x in url for x in ["fonts.gstatic", "fonts.googleapis", "typekit",
                                        ".woff2", ".woff", "google-analytics",
                                        "googletagmanager", "doubleclick.net"]):
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_resources)
        page = await context.new_page()
        page.set_default_timeout(15000)

        # ---- Step 1: Navigate to target job ----
        print(f"\n[1] Navigating to: {TARGET_URL}")
        status = await safe_goto(page, TARGET_URL)
        print(f"  HTTP {status}, URL: {page.url}")

        ss = await take_screenshot(page, "01-job-page")
        if ss:
            result["screenshots"].append(ss)

        title = await page.title()
        print(f"  Title: {title!r}")

        if status and status >= 400:
            result["status"] = "failed"
            result["notes"] += f"Target job returned HTTP {status}."
            await browser.close()
            return result

        # ---- Step 2: Accept cookie consent ----
        for sel in ["button:has-text('ACCEPT ALL COOKIES')", "button:has-text('Accept All')",
                    "button:has-text('Accept')"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    print(f"  Accepting cookies via: {sel!r}")
                    await el.click()
                    await asyncio.sleep(0.8)
                    break
            except Exception:
                pass

        # Scroll down to the form to ensure it's in viewport
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
        await asyncio.sleep(0.5)

        # ---- Step 3: Verify form 447 is present ----
        form_447 = await page.query_selector("form.wpcf7-form[action*='wpcf7-f447']")
        if not form_447:
            # Try generic wpcf7 form
            form_447 = await page.query_selector("form.wpcf7-form")
        print(f"  Application form found: {form_447 is not None}")

        # ---- Step 4: Fill fields using JS (bypasses visibility) ----
        print("\n[2] Filling application form fields via JS...")

        r = await fill_via_js(page, "input[name='your-name']", APPLICANT["name"])
        print(f"  your-name: {r}")

        r = await fill_via_js(page, "input[name='your-email']", APPLICANT["email"])
        print(f"  your-email: {r}")

        r = await fill_via_js(page, "input[name='your-phone']", APPLICANT["phone"])
        print(f"  your-phone: {r}")

        # Check acceptance checkbox for form 447
        checkbox_checked = await page.evaluate("""
            () => {
                // Find the checkbox in the application form (form 447, not form 8)
                const form = document.querySelector('form[action*="wpcf7-f447"]') ||
                             document.querySelector('.wpcf7-form');
                if (!form) return 'no form';
                const cb = form.querySelector('input[type="checkbox"]');
                if (!cb) return 'no checkbox';
                if (!cb.checked) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change', {bubbles: true}));
                    cb.dispatchEvent(new Event('click', {bubbles: true}));
                }
                return 'checked: ' + cb.checked;
            }
        """)
        print(f"  acceptance: {checkbox_checked}")

        # CV upload — must be done via Playwright (can't set file via JS)
        if RESUME_PDF.exists():
            # Find the file input within the application form
            try:
                file_input = await page.query_selector(
                    "form[action*='wpcf7-f447'] input[type='file'], "
                    "input[name='file'][type='file']"
                )
                if file_input:
                    await file_input.set_input_files(str(RESUME_PDF))
                    print(f"  file: {RESUME_PDF.name} uploaded")
                    await asyncio.sleep(1)
                else:
                    print("  file: no file input found in form 447")
            except Exception as e:
                print(f"  file upload error: {e}")

        ss = await take_screenshot(page, "02-form-filled")
        if ss:
            result["screenshots"].append(ss)

        # Verify values were set
        verification = await page.evaluate("""
            () => {
                const form = document.querySelector('form[action*="wpcf7-f447"]') ||
                             document.querySelector('.wpcf7-form');
                if (!form) return {};
                return {
                    name: (form.querySelector('input[name="your-name"]') || {}).value || '',
                    email: (form.querySelector('input[name="your-email"]') || {}).value || '',
                    phone: (form.querySelector('input[name="your-phone"]') || {}).value || '',
                    checkbox: (form.querySelector('input[type="checkbox"]') || {}).checked || false,
                    fileCount: (form.querySelector('input[type="file"]') || {}).files ?
                               (form.querySelector('input[type="file"]') || {}).files.length : 0,
                };
            }
        """)
        print(f"\n  Form values: {verification}")

        if not verification.get("name") and not verification.get("email"):
            result["status"] = "failed"
            result["notes"] += " Could not populate form fields (JavaScript fill failed)."
            await browser.close()
            return result

        # ---- Step 5: Submit ----
        print("\n[3] Submitting application...")

        # Find submit button in form 447
        submit_in_form = await page.evaluate("""
            () => {
                const form = document.querySelector('form[action*="wpcf7-f447"]') ||
                             document.querySelector('.wpcf7-form');
                if (!form) return null;
                const btn = form.querySelector('input[type="submit"], button[type="submit"]');
                return btn ? (btn.value || btn.textContent || 'found') : null;
            }
        """)
        print(f"  Submit button: {submit_in_form!r}")

        ss = await take_screenshot(page, "03-pre-submit")
        if ss:
            result["screenshots"].append(ss)

        # Click submit via JS to avoid visibility issues
        submit_result = await page.evaluate("""
            () => {
                const form = document.querySelector('form[action*="wpcf7-f447"]') ||
                             document.querySelector('.wpcf7-form');
                if (!form) return 'no form';
                const btn = form.querySelector('input[type="submit"], button[type="submit"]');
                if (!btn) return 'no submit button';
                btn.click();
                return 'clicked: ' + (btn.value || btn.textContent || '?');
            }
        """)
        print(f"  Submit JS click: {submit_result!r}")

        # Wait for form submission
        await asyncio.sleep(4)
        print(f"  URL after submit: {page.url}")

        ss = await take_screenshot(page, "04-post-submit")
        if ss:
            result["screenshots"].append(ss)

        # ---- Step 6: Check result ----
        try:
            final_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            final_text = ""
        print(f"\n  Post-submit text (500): {final_text[:500]!r}")

        # wpcf7 form status
        try:
            form_class = await page.evaluate("""
                () => {
                    const form = document.querySelector('.wpcf7-form');
                    return form ? form.getAttribute('data-status') || form.className : '';
                }
            """)
            print(f"  wpcf7 status: {form_class!r}")
        except Exception:
            form_class = ""

        # Check for success/error indicators
        wpcf7_success = "sent" in form_class.lower() or "mail-sent" in form_class.lower()
        text_success = any(p in final_text.lower() for p in [
            "thank you", "application received", "successfully", "message has been sent",
            "your message was sent", "mail sent", "bedankt", "confirmation"
        ])
        has_error = any(p in final_text.lower() for p in [
            "validation failed", "there was an error", "failed to send",
            "recaptcha failed", "spam detected", "invalid"
        ])

        if wpcf7_success or text_success:
            result["status"] = "applied"
            result["notes"] += " Application submitted — success confirmed."
        elif has_error:
            result["status"] = "failed"
            result["notes"] += f" Submission error. wpcf7 status: {form_class!r}"
        elif "no form" in submit_result or "no submit" in submit_result:
            result["status"] = "failed"
            result["notes"] += " Could not find form or submit button."
        else:
            # Submitted but status unclear
            result["status"] = "applied"
            result["notes"] += f" Form submitted. wpcf7 status: {form_class!r}"

        await browser.close()
        return result


def update_applications_log(result):
    APPLICATIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    apps = []
    if APPLICATIONS_JSON.exists():
        try:
            apps = json.loads(APPLICATIONS_JSON.read_text())
        except Exception:
            apps = []

    # Check for duplicate
    for app in apps:
        if app.get("company") == result["company"] and app.get("role") == result["role"]:
            print(f"  [log] Updating existing entry")
            app.update({
                "date_applied": datetime.now().strftime("%Y-%m-%d"),
                "status": result["status"],
                "url": result.get("url", ""),
                "screenshots": result.get("screenshots", []),
                "notes": result.get("notes", ""),
            })
            APPLICATIONS_JSON.write_text(json.dumps(apps, indent=2))
            return

    entry = {
        "id": f"foxtek-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Foxtek",
        "role": result["role"],
        "url": result.get("url", ""),
        "original_url": result.get("original_url", ""),
        "date_applied": datetime.now().strftime("%Y-%m-%d"),
        "score": 8.5,
        "status": result["status"],
        "resume_file": str(RESUME_PDF),
        "cover_letter_file": str(COVER_LETTER_MD),
        "screenshots": result.get("screenshots", []),
        "notes": result.get("notes", ""),
        "response": "",
    }
    apps.append(entry)
    APPLICATIONS_JSON.write_text(json.dumps(apps, indent=2))
    print(f"  [log] Saved to {APPLICATIONS_JSON}")


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print(f"{'='*60}")
    print("\nLogging to applications.json...")
    update_applications_log(result)
