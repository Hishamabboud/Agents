#!/usr/bin/env python3
"""
Foxtek .NET Developer application — with properly parsed proxy credentials.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PDF = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
COVER_LETTER_MD = Path("/home/user/Agents/output/cover-letters/foxtek-net-developer.md")

APPLICANT = {
    "name": "Hisham Abboud",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31064841 2838",
    "location": "Eindhoven, Netherlands",
}

JOB_URL = "https://www.foxtekrs.com/job/dot-net-developer-1"
JOBS_PAGE = "https://www.foxtekrs.com/jobs/"

# Parse proxy from environment
_proxy_raw = (
    os.environ.get("HTTPS_PROXY")
    or os.environ.get("HTTP_PROXY")
    or os.environ.get("https_proxy")
    or os.environ.get("http_proxy")
    or ""
)
_parsed = urlparse(_proxy_raw)
PROXY_CONFIG = None
if _parsed.hostname:
    PROXY_CONFIG = {
        "server": f"{_parsed.scheme}://{_parsed.hostname}:{_parsed.port}",
        "username": _parsed.username or "",
        "password": _parsed.password or "",
    }
    print(f"Proxy server: {PROXY_CONFIG['server']}")
    print(f"Proxy user: {PROXY_CONFIG['username'][:40]}...")


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"foxtek-{name}-{ts()}.png"
    # Disable font loading to avoid screenshot timeout
    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => {
                    if (el.href && (
                        el.href.includes('fonts.googleapis') ||
                        el.href.includes('fonts.gstatic') ||
                        el.href.includes('typekit') ||
                        el.href.includes('use.typekit')
                    )) {
                        el.parentNode && el.parentNode.removeChild(el);
                    }
                });
                const s = document.createElement('style');
                s.textContent = '@font-face { } * { font-family: Arial, Helvetica, sans-serif !important; }';
                document.head && document.head.appendChild(s);
            }
        """)
    except Exception:
        pass
    try:
        await page.screenshot(path=str(path), full_page=True, timeout=8000)
        print(f"  [screenshot] {path.name}")
        return str(path)
    except Exception as e:
        print(f"  [screenshot failed] {name}: {e}")
        return None


async def safe_goto(page, url, timeout=20000):
    """Navigate using 'commit' wait_until for speed."""
    try:
        resp = await page.goto(url, wait_until="commit", timeout=timeout)
        # Brief wait, but don't block on load
        await asyncio.sleep(1.5)
        return resp.status if resp else None
    except Exception as e:
        print(f"  [goto error] {e}")
        return None


async def fill_form(page, cover_letter_text):
    filled = []

    for sel, val in [
        ("input[name*='first_name']", APPLICANT["first_name"]),
        ("input[name*='firstname']", APPLICANT["first_name"]),
        ("input[id*='first_name']", APPLICANT["first_name"]),
        ("input[id*='firstname']", APPLICANT["first_name"]),
        ("input[placeholder*='First']", APPLICANT["first_name"]),
        ("input[name*='last_name']", APPLICANT["last_name"]),
        ("input[name*='lastname']", APPLICANT["last_name"]),
        ("input[id*='last_name']", APPLICANT["last_name"]),
        ("input[placeholder*='Last']", APPLICANT["last_name"]),
        ("input[name='name']", APPLICANT["name"]),
        ("input[id='name']", APPLICANT["name"]),
        ("input[placeholder='Name']", APPLICANT["name"]),
        ("input[placeholder*='Full Name']", APPLICANT["name"]),
        ("input[placeholder*='your name']", APPLICANT["name"]),
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(val)
                filled.append(sel)
                print(f"    + {sel!r} = {val!r}")
        except Exception:
            pass

    for sel in ["input[type='email']", "input[name='email']", "input[id*='email']",
                "input[placeholder*='mail']"]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(APPLICANT["email"])
                filled.append(sel)
                print(f"    + {sel!r} = email")
                break
        except Exception:
            pass

    for sel in ["input[type='tel']", "input[name*='phone']", "input[name*='mobile']",
                "input[id*='phone']", "input[placeholder*='hone']"]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(APPLICANT["phone"])
                filled.append(sel)
                print(f"    + {sel!r} = phone")
                break
        except Exception:
            pass

    if cover_letter_text:
        for sel in ["textarea[name*='cover']", "textarea[name*='letter']",
                    "textarea[name*='message']", "textarea[name*='motivation']",
                    "textarea[id*='cover']", "textarea[id*='message']", "textarea"]:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    if await el.is_visible():
                        await el.fill(cover_letter_text)
                        filled.append(f"{sel}:cover_letter")
                        print(f"    + {sel!r} = [cover letter]")
                        break
                if any(":cover_letter" in f for f in filled):
                    break
            except Exception:
                pass

    if RESUME_PDF.exists():
        for sel in ["input[type='file']", "input[name*='resume']",
                    "input[name*='cv']", "input[name*='file']"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.set_input_files(str(RESUME_PDF))
                    filled.append(f"{sel}:file")
                    print(f"    + {sel!r} = {RESUME_PDF.name}")
                    await asyncio.sleep(1)
                    break
            except Exception as e:
                print(f"    ! File upload {sel!r}: {e}")

    return filled


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        cover_letter_text = COVER_LETTER_MD.read_text().strip()
        print(f"Cover letter: {len(cover_letter_text)} chars")

    result = {
        "company": "Foxtek",
        "role": ".NET Developer",
        "url": JOB_URL,
        "status": "unknown",
        "screenshots": [],
        "notes": "",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=PROXY_CONFIG,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-web-security", "--disable-features=VizDisplayCompositor"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )

        # Block font and analytics resources
        async def block_fonts(route):
            url = route.request.url
            if any(x in url for x in ["fonts.gstatic", "fonts.googleapis", "typekit", ".woff", ".woff2",
                                        "google-analytics", "googletagmanager", "doubleclick"]):
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)

        page = await context.new_page()
        page.set_default_timeout(15000)

        # Step 1: Navigate to job URL
        print(f"\n[1] {JOB_URL}")
        status = await safe_goto(page, JOB_URL)
        print(f"  HTTP {status}, URL: {page.url}")

        ss = await take_screenshot(page, "01-job-page")
        if ss:
            result["screenshots"].append(ss)

        title = await page.title()
        html = await page.content()
        print(f"  Title: {title!r}")

        # Detect 404 / not found
        is_404 = (
            status == 404
            or (status and status >= 400)
            or "404" in title
            or "not found" in title.lower()
            or "page not found" in html.lower()
        )

        # Step 2: If not available, check jobs overview
        if is_404:
            result["notes"] += f"Original job URL returned HTTP {status} — listing removed. "
            print(f"\n[2] Checking {JOBS_PAGE}")
            status2 = await safe_goto(page, JOBS_PAGE)
            print(f"  HTTP {status2}, URL: {page.url}")

            ss = await take_screenshot(page, "02-jobs-overview")
            if ss:
                result["screenshots"].append(ss)

            links = await page.query_selector_all("a[href*='/job/']")
            found_jobs = []
            seen = set()
            for lnk in links:
                href = (await lnk.get_attribute("href") or "").strip()
                text = (await lnk.inner_text()).strip()
                if href and text and href not in seen and len(text) > 3:
                    seen.add(href)
                    found_jobs.append({"url": href, "title": text})
                    print(f"  Active: {text!r}")

            if not found_jobs:
                result["status"] = "skipped"
                result["notes"] += "No active Foxtek job listings found."
                await browser.close()
                return result

            keywords = [".net", "dotnet", "c#", "csharp", "full stack", "fullstack", "backend", "software developer"]
            dotnet_match = next(
                (j for j in found_jobs if any(k in j["title"].lower() for k in keywords)),
                None
            )

            if not dotnet_match:
                titles = [j["title"] for j in found_jobs]
                result["status"] = "skipped"
                result["notes"] += f"No equivalent .NET/C# role available. Active jobs: {titles}"
                await browser.close()
                return result

            print(f"\n  Match: {dotnet_match['title']!r}")
            result["notes"] += f"Applying to: '{dotnet_match['title']}'. "
            result["url"] = dotnet_match["url"]

            status3 = await safe_goto(page, dotnet_match["url"])
            print(f"  Job page HTTP {status3}, URL: {page.url}")

            ss = await take_screenshot(page, "03-matched-job")
            if ss:
                result["screenshots"].append(ss)

        # Step 3: Apply button
        print("\n[3] Looking for Apply button...")
        for sel in ["a:has-text('Apply Now')", "a:has-text('Apply')",
                    "button:has-text('Apply Now')", "button:has-text('Apply')",
                    ".apply-button", "a[href*='apply']", "a:has-text('Solliciteer')"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    txt = (await el.inner_text()).strip()
                    print(f"  Clicking: {sel!r} ({txt!r})")
                    await el.click()
                    await asyncio.sleep(2)
                    break
            except Exception:
                pass

        # Detect external redirect
        for ext in ["linkedin.com", "indeed.com", "greenhouse.io", "workable.com", "lever.co", "recruitee.com"]:
            if ext in page.url:
                result["status"] = "skipped"
                result["notes"] += f" Redirected to external platform: {page.url}"
                ss = await take_screenshot(page, "ext-redirect")
                if ss:
                    result["screenshots"].append(ss)
                await browser.close()
                return result

        # CAPTCHA check
        html = await page.content()
        if any(x in html.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
            result["status"] = "failed"
            result["notes"] += " CAPTCHA encountered."
            ss = await take_screenshot(page, "captcha")
            if ss:
                result["screenshots"].append(ss)
            await browser.close()
            return result

        # Step 4: Fill form
        form_el = await page.query_selector("form")
        email_el = await page.query_selector("input[type='email'], input[name*='email']")

        if not form_el and not email_el:
            try:
                pg_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                print(f"  Page text (400): {pg_text[:400]!r}")
            except Exception:
                pass
            result["status"] = "skipped"
            result["notes"] += " No application form on the page."
            ss = await take_screenshot(page, "no-form")
            if ss:
                result["screenshots"].append(ss)
            await browser.close()
            return result

        print("\n[4] Filling form...")
        filled = await fill_form(page, cover_letter_text)
        print(f"  {len(filled)} field(s) filled")

        ss = await take_screenshot(page, "04-form-filled")
        if ss:
            result["screenshots"].append(ss)

        if not filled:
            result["status"] = "skipped"
            result["notes"] += " Form found but could not fill any fields."
            await browser.close()
            return result

        # Step 5: Submit
        print("\n[5] Submitting...")
        submitted = False
        for sel in ["button[type='submit']", "input[type='submit']",
                    "button:has-text('Submit')", "button:has-text('Send')",
                    "button:has-text('Apply')", "[type='submit']"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    try:
                        label = (await el.inner_text()).strip() or (await el.get_attribute("value") or sel)
                    except Exception:
                        label = sel
                    print(f"  Submit: {sel!r} ({label!r})")
                    ss = await take_screenshot(page, "05-pre-submit")
                    if ss:
                        result["screenshots"].append(ss)
                    await el.click()
                    await asyncio.sleep(3)
                    submitted = True
                    print(f"  Done. URL: {page.url}")
                    break
            except Exception as e:
                print(f"  Submit error {sel!r}: {e}")

        ss = await take_screenshot(page, "06-post-submit")
        if ss:
            result["screenshots"].append(ss)

        try:
            final_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            final_text = ""
        print(f"  Post-submit (300): {final_text[:300]!r}")

        success_phrases = ["thank you", "application received", "successfully submitted",
                           "we have received", "will be in touch", "confirmation",
                           "received your application", "bedankt"]
        success = any(p in final_text.lower() for p in success_phrases)

        if success:
            result["status"] = "applied"
            result["notes"] += " Successfully submitted — confirmation detected."
        elif submitted:
            result["status"] = "applied"
            result["notes"] += " Form submitted (no confirmation message detected)."
        else:
            result["status"] = "failed"
            result["notes"] += " Could not find/click submit button."

        result["filled_fields"] = filled
        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    for k, v in result.items():
        if k != "filled_fields":
            print(f"  {k}: {v}")
    if "filled_fields" in result:
        print(f"  filled_fields ({len(result['filled_fields'])}): {result['filled_fields']}")
    print(f"{'='*60}")
