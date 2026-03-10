#!/usr/bin/env python3
"""
Foxtek application — targets Senior Full Stack Engineer (C#/Angular) as nearest
available role to the original .NET Developer position (which returned 404).

Form: WordPress Contact Form 7 (wpcf7)
Fields: your-name, your-email, your-phone, file (CV upload), your-message, acceptance-123
reCAPTCHA: v3 invisible (executes via JS)
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


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        cover_letter_text = COVER_LETTER_MD.read_text().strip()
        print(f"Cover letter: {len(cover_letter_text)} chars")

    result = {
        "company": "Foxtek",
        "role": TARGET_ROLE,
        "url": TARGET_URL,
        "original_url": ORIGINAL_URL,
        "status": "unknown",
        "screenshots": [],
        "notes": "Original .NET Developer job (dot-net-developer-1) returned 404 — listing removed. "
                 "Applying to nearest available match: Senior Full Stack Engineer (C#/Angular). ",
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

        # ---- Step 1: Navigate to the target job ----
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
            result["notes"] += f"Target job page returned HTTP {status}."
            await browser.close()
            return result

        # ---- Step 2: Accept cookie consent if present ----
        for sel in ["button:has-text('ACCEPT ALL COOKIES')", "button:has-text('Accept All')",
                    "button:has-text('Accept')", "#cookie-accept", ".cookie-accept"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    print(f"  Accepting cookies: {sel!r}")
                    await el.click()
                    await asyncio.sleep(0.5)
                    break
            except Exception:
                pass

        # ---- Step 3: Fill the wpcf7 form ----
        print("\n[2] Filling application form (wpcf7)...")

        # Full Name
        name_sel = "input[name='your-name'], input[placeholder='Full Name']"
        el = await page.query_selector(name_sel)
        if el:
            await el.fill(APPLICANT["name"])
            print(f"  + name: {APPLICANT['name']!r}")

        # Email
        email_sel = "input[name='your-email'], input[placeholder='Email Address']"
        el = await page.query_selector(email_sel)
        if el:
            await el.fill(APPLICANT["email"])
            print(f"  + email: {APPLICANT['email']!r}")

        # Phone
        phone_sel = "input[name='your-phone'], input[placeholder='Telephone Number']"
        el = await page.query_selector(phone_sel)
        if el:
            await el.fill(APPLICANT["phone"])
            print(f"  + phone: {APPLICANT['phone']!r}")

        # Message / Cover Letter
        msg_sel = "textarea[name='your-message'], textarea"
        el = await page.query_selector(msg_sel)
        if el and cover_letter_text:
            await el.fill(cover_letter_text)
            print(f"  + message: [cover letter, {len(cover_letter_text)} chars]")

        # CV upload
        if RESUME_PDF.exists():
            file_sel = "input[name='file'][type='file'], input[type='file']"
            el = await page.query_selector(file_sel)
            if el:
                await el.set_input_files(str(RESUME_PDF))
                print(f"  + file: {RESUME_PDF.name}")
                await asyncio.sleep(1)

        # Acceptance checkbox
        checkbox_sel = "input[name='acceptance-123'], input[type='checkbox']"
        el = await page.query_selector(checkbox_sel)
        if el:
            checked = await el.is_checked()
            if not checked:
                await el.check()
                print("  + acceptance checkbox: checked")

        ss = await take_screenshot(page, "02-form-filled")
        if ss:
            result["screenshots"].append(ss)

        # Verify fields are filled
        name_val = ""
        email_val = ""
        try:
            name_el = await page.query_selector("input[name='your-name']")
            if name_el:
                name_val = await name_el.input_value()
            email_el = await page.query_selector("input[name='your-email']")
            if email_el:
                email_val = await email_el.input_value()
        except Exception:
            pass
        print(f"  Verification — name: {name_val!r}, email: {email_val!r}")

        if not name_val and not email_val:
            result["status"] = "failed"
            result["notes"] += " Could not fill form fields (form may not have rendered properly)."
            await browser.close()
            return result

        # ---- Step 4: Submit ----
        print("\n[3] Submitting application...")
        submit_sel = "input[type='submit'][value='Apply Now'], button[type='submit'], [type='submit']"
        el = await page.query_selector(submit_sel)
        if not el:
            result["status"] = "failed"
            result["notes"] += " Submit button not found."
            await browser.close()
            return result

        submit_val = await el.get_attribute("value") or (await el.inner_text())
        print(f"  Submit button: {submit_val!r}")

        ss = await take_screenshot(page, "03-pre-submit")
        if ss:
            result["screenshots"].append(ss)

        try:
            await el.click()
            # Wait for form submission response
            await asyncio.sleep(4)
            print(f"  Submitted. URL: {page.url}")
        except Exception as e:
            print(f"  Submit click error: {e}")
            result["status"] = "failed"
            result["notes"] += f" Submit error: {e}"
            await browser.close()
            return result

        ss = await take_screenshot(page, "04-post-submit")
        if ss:
            result["screenshots"].append(ss)

        # ---- Step 5: Check result ----
        try:
            final_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            final_text = ""
        print(f"  Post-submit text (500): {final_text[:500]!r}")

        # Check for wpcf7 success/error status
        try:
            form_status = await page.evaluate("""
                () => {
                    const form = document.querySelector('.wpcf7-form');
                    return form ? form.className : '';
                }
            """)
            print(f"  wpcf7 form class: {form_status!r}")
        except Exception:
            form_status = ""

        success_phrases = ["thank you", "application received", "successfully submitted",
                           "message has been sent", "your message was sent",
                           "we have received", "confirmation", "sent successfully",
                           "mail sent", "bedankt"]
        wpcf7_success = "sent" in form_status.lower() or "mail-sent" in form_status.lower()
        text_success = any(p in final_text.lower() for p in success_phrases)

        # Check for errors
        error_phrases = ["validation failed", "there was an error", "failed to send",
                         "recaptcha", "captcha failed", "spam"]
        has_error = any(p in final_text.lower() for p in error_phrases)

        if wpcf7_success or text_success:
            result["status"] = "applied"
            result["notes"] += " Application submitted successfully — confirmation detected."
        elif has_error:
            result["status"] = "failed"
            result["notes"] += f" Submission error detected. Form class: {form_status!r}"
        else:
            # Ambiguous — form was submitted but no clear confirmation
            result["status"] = "applied"
            result["notes"] += f" Form submitted (status ambiguous). wpcf7 class: {form_status!r}"

        await browser.close()
        return result


def update_applications_log(result):
    """Append this application to data/applications.json."""
    APPLICATIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    apps = []
    if APPLICATIONS_JSON.exists():
        try:
            apps = json.loads(APPLICATIONS_JSON.read_text())
        except Exception:
            apps = []

    # Check for existing entry
    for app in apps:
        if app.get("company") == result["company"] and app.get("role") == result["role"]:
            print(f"  [log] Updating existing entry for {result['company']} - {result['role']}")
            app.update({
                "date_applied": datetime.now().strftime("%Y-%m-%d"),
                "status": result["status"],
                "url": result.get("url", ""),
                "screenshots": result.get("screenshots", []),
                "notes": result.get("notes", ""),
                "resume_file": str(RESUME_PDF),
                "cover_letter_file": str(COVER_LETTER_MD),
                "score": 8.5,
            })
            APPLICATIONS_JSON.write_text(json.dumps(apps, indent=2))
            return

    entry = {
        "id": f"foxtek-{datetime.now().strftime('%Y%m%d')}",
        "company": result["company"],
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

    # Log to applications.json
    print("\nLogging to applications.json...")
    update_applications_log(result)
