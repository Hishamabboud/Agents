#!/usr/bin/env python3
"""
Foxtek application — targets Senior Full Stack Engineer (C#/Angular) as nearest
available role to the original .NET Developer position (which returned 404).

Form: WordPress Contact Form 7 (wpcf7), form ID 447
Fields: your-name, your-email, your-phone, file (CV upload), acceptance-123
reCAPTCHA: v3 invisible
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
    # Disable external fonts to avoid screenshot timeout
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('link[rel="stylesheet"]').forEach(function(el) {
                    if (el.href && (el.href.indexOf('fonts.') > -1 || el.href.indexOf('typekit') > -1))
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
            "Application form has: name, email, phone, CV file upload (no cover letter field). "
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

        # Block font resources
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

        # ---- Step 1: Navigate ----
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
                    print(f"  Accepting cookies...")
                    await el.click()
                    await asyncio.sleep(0.8)
                    break
            except Exception:
                pass

        # Scroll to form area
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        await asyncio.sleep(0.5)

        # ---- Step 3: Fill using locator with force ----
        print("\n[2] Filling application form...")

        # Use locator().fill() with force=True to bypass visibility
        try:
            await page.locator("input[name='your-name']").first.fill(
                APPLICANT["name"], force=True, timeout=5000
            )
            print(f"  + your-name: {APPLICANT['name']!r}")
        except Exception as e:
            print(f"  ! your-name error: {e}")

        try:
            await page.locator("input[name='your-email']").first.fill(
                APPLICANT["email"], force=True, timeout=5000
            )
            print(f"  + your-email: {APPLICANT['email']!r}")
        except Exception as e:
            print(f"  ! your-email error: {e}")

        try:
            await page.locator("input[name='your-phone']").first.fill(
                APPLICANT["phone"], force=True, timeout=5000
            )
            print(f"  + your-phone: {APPLICANT['phone']!r}")
        except Exception as e:
            print(f"  ! your-phone error: {e}")

        # Acceptance checkbox
        try:
            cb = page.locator("input[name='acceptance-123']").first
            await cb.check(force=True, timeout=5000)
            print("  + acceptance-123: checked")
        except Exception as e:
            print(f"  ! acceptance-123: {e}")

        # CV file upload
        if RESUME_PDF.exists():
            try:
                file_input = page.locator("input[type='file']").first
                await file_input.set_input_files(str(RESUME_PDF), timeout=8000)
                print(f"  + file: {RESUME_PDF.name}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"  ! file upload: {e}")
        else:
            print(f"  ! Resume not found: {RESUME_PDF}")

        ss = await take_screenshot(page, "02-form-filled")
        if ss:
            result["screenshots"].append(ss)

        # Verify form values
        try:
            v = await page.evaluate("""
                function() {
                    var form = document.querySelector('form.wpcf7-form');
                    if (!form) return {error: 'no form'};
                    var nameEl = form.querySelector('input[name="your-name"]');
                    var emailEl = form.querySelector('input[name="your-email"]');
                    var phoneEl = form.querySelector('input[name="your-phone"]');
                    var cbEl = form.querySelector('input[type="checkbox"]');
                    return {
                        name: nameEl ? nameEl.value : '',
                        email: emailEl ? emailEl.value : '',
                        phone: phoneEl ? phoneEl.value : '',
                        checkbox: cbEl ? cbEl.checked : false
                    };
                }
            """)
            print(f"\n  Verification: {v}")

            if not v.get("name") and not v.get("email"):
                result["status"] = "failed"
                result["notes"] += " Form fields could not be populated."
                await browser.close()
                return result
        except Exception as e:
            print(f"  Verification error: {e}")

        # ---- Step 4: Submit ----
        print("\n[3] Submitting...")

        # Take pre-submit screenshot
        ss = await take_screenshot(page, "03-pre-submit")
        if ss:
            result["screenshots"].append(ss)

        submitted = False
        for sel in ["input[type='submit'][value='Apply Now']",
                    "input[type='submit']",
                    "button[type='submit']",
                    ".wpcf7-submit"]:
            try:
                loc = page.locator(sel).first
                count = await loc.count()
                if count > 0:
                    label = await loc.get_attribute("value") or await loc.inner_text()
                    print(f"  Submit via: {sel!r} ({label!r})")
                    await loc.click(force=True, timeout=8000)
                    await asyncio.sleep(4)
                    submitted = True
                    print(f"  Submitted. URL: {page.url}")
                    break
            except Exception as e:
                print(f"  Submit {sel!r}: {e}")

        ss = await take_screenshot(page, "04-post-submit")
        if ss:
            result["screenshots"].append(ss)

        # ---- Step 5: Check result ----
        try:
            final_text = await page.evaluate(
                "function() { return document.body ? document.body.innerText : ''; }"
            )
        except Exception:
            final_text = ""
        print(f"\n  Post-submit text (500): {final_text[:500]!r}")

        # wpcf7 form status
        try:
            form_status = await page.evaluate("""
                function() {
                    var form = document.querySelector('.wpcf7-form');
                    if (!form) return '';
                    return form.getAttribute('data-status') || form.className;
                }
            """)
            print(f"  wpcf7 data-status: {form_status!r}")
        except Exception:
            form_status = ""

        wpcf7_success = "sent" in form_status.lower() or "mail-sent" in form_status.lower()
        text_success = any(p in final_text.lower() for p in [
            "thank you", "application received", "successfully", "message has been sent",
            "your message was sent", "mail sent", "bedankt", "sent successfully"
        ])
        has_error = any(p in final_text.lower() for p in [
            "validation failed", "there was an error", "failed to send",
            "recaptcha failed", "spam", "invalid"
        ])

        if wpcf7_success or text_success:
            result["status"] = "applied"
            result["notes"] += " Application submitted — success confirmed."
        elif has_error:
            result["status"] = "failed"
            result["notes"] += f" Submission error detected. wpcf7 status: {form_status!r}"
        elif submitted:
            result["status"] = "applied"
            result["notes"] += f" Form submitted. wpcf7 status: {form_status!r}"
        else:
            result["status"] = "failed"
            result["notes"] += " Could not click submit button."

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

    # Remove existing Foxtek entry to avoid duplicates
    apps = [a for a in apps if not (a.get("company") == "Foxtek" and
                                     a.get("role") == result["role"])]

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
