#!/usr/bin/env python3
"""
Foxtek .NET Developer application — robust version with proxy and font timeout bypass.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
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

PROXY_URL = (
    os.environ.get("HTTPS_PROXY")
    or os.environ.get("HTTP_PROXY")
    or os.environ.get("https_proxy")
    or os.environ.get("http_proxy")
)


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(page, name):
    """Screenshot that bypasses font loading by injecting a CSS override."""
    path = SCREENSHOTS_DIR / f"foxtek-{name}-{ts()}.png"
    try:
        # Disable external fonts to prevent timeout waiting for fonts
        await page.evaluate("""
            () => {
                // Remove all stylesheets that load external fonts
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => {
                    if (el.href && (el.href.includes('fonts.') || el.href.includes('typekit'))) {
                        el.disabled = true;
                    }
                });
                // Override font-face
                const style = document.createElement('style');
                style.textContent = '* { font-family: Arial, sans-serif !important; }';
                document.head.appendChild(style);
            }
        """)
    except Exception:
        pass
    try:
        await page.screenshot(path=str(path), full_page=True, timeout=10000)
        print(f"  Screenshot: {path.name}")
        return str(path)
    except Exception as e:
        print(f"  Screenshot failed ({name}): {e}")
        return None


async def safe_goto(page, url, timeout=25000):
    """Navigate, tolerating timeouts — returns HTTP status or None."""
    try:
        resp = await page.goto(url, wait_until="commit", timeout=timeout)
        # Give the page a moment to settle
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        await page.wait_for_timeout(1500)
        return resp.status if resp else None
    except Exception as e:
        print(f"  goto error: {e}")
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
        ("input[placeholder*='Your name']", APPLICANT["name"]),
        ("input[placeholder*='your name']", APPLICANT["name"]),
    ]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(val)
                filled.append(sel)
                print(f"    {sel} = {val!r}")
        except Exception:
            pass

    for sel in ["input[type='email']", "input[name='email']", "input[id*='email']",
                "input[placeholder*='mail']", "input[placeholder*='Mail']"]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(APPLICANT["email"])
                filled.append(sel)
                print(f"    {sel} = email")
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
                print(f"    {sel} = phone")
                break
        except Exception:
            pass

    if cover_letter_text:
        for sel in ["textarea[name*='cover']", "textarea[name*='letter']",
                    "textarea[name*='message']", "textarea[name*='motivation']",
                    "textarea[id*='cover']", "textarea[id*='letter']",
                    "textarea[id*='message']", "textarea"]:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    if await el.is_visible():
                        await el.fill(cover_letter_text)
                        filled.append(f"{sel}:cover_letter")
                        print(f"    {sel} = cover_letter")
                        break
                if any("cover_letter" in f for f in filled):
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
                    print(f"    {sel} = {RESUME_PDF.name}")
                    await page.wait_for_timeout(1000)
                    break
            except Exception as e:
                print(f"    File upload {sel}: {e}")

    return filled


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        cover_letter_text = COVER_LETTER_MD.read_text().strip()
        print(f"Cover letter loaded ({len(cover_letter_text)} chars)")

    result = {
        "company": "Foxtek",
        "role": ".NET Developer",
        "url": JOB_URL,
        "status": "unknown",
        "screenshots": [],
        "notes": "",
    }

    proxy_config = {"server": PROXY_URL} if PROXY_URL else None
    if proxy_config:
        print(f"Proxy: {PROXY_URL[:60]}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=["--disable-web-security", "--no-sandbox",
                  "--disable-font-subpixel-positioning",
                  "--disable-remote-fonts"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        # Block font resources to prevent timeout waiting for fonts
        await context.route("**/*.woff", lambda r: r.abort())
        await context.route("**/*.woff2", lambda r: r.abort())
        await context.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        await context.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        await context.route("**/use.typekit.net/**", lambda r: r.abort())

        page = await context.new_page()
        page.set_default_timeout(20000)

        # ---- Step 1: Original job URL ----
        print(f"\n[Step 1] {JOB_URL}")
        status = await safe_goto(page, JOB_URL)
        print(f"  HTTP: {status}, URL: {page.url}")

        ss = await take_screenshot(page, "01-job-page")
        if ss:
            result["screenshots"].append(ss)

        title = await page.title()
        html = await page.content()
        print(f"  Title: {title!r}")

        is_404 = (
            status == 404
            or "404" in title
            or "not found" in title.lower()
            or "page not found" in html.lower()
            or not html.strip()
        )

        # ---- Step 2: If 404, check jobs overview ----
        if is_404:
            result["notes"] += f"Original URL returned {status} — job removed/filled. "
            print(f"\n[Step 2] Job not found ({status}). Checking jobs page...")

            status2 = await safe_goto(page, JOBS_PAGE)
            print(f"  Jobs page HTTP: {status2}, URL: {page.url}")

            ss = await take_screenshot(page, "02-jobs-overview")
            if ss:
                result["screenshots"].append(ss)

            # Scrape job listings
            links = await page.query_selector_all("a[href*='/job/']")
            found_jobs = []
            seen = set()
            for lnk in links:
                href = (await lnk.get_attribute("href") or "").strip()
                text = (await lnk.inner_text()).strip()
                if href and text and href not in seen and len(text) > 3:
                    seen.add(href)
                    found_jobs.append({"url": href, "title": text})
                    print(f"  Found: {text!r}")

            if not found_jobs:
                result["status"] = "skipped"
                result["notes"] += "No active job listings on Foxtek."
                await browser.close()
                return result

            # Find best match
            dotnet_match = None
            keywords = [".net", "dotnet", "dot net", "c#", "csharp", "full stack", "fullstack", "backend", "software"]
            for job in found_jobs:
                tl = job["title"].lower()
                if any(k in tl for k in keywords):
                    dotnet_match = job
                    break

            if not dotnet_match:
                result["status"] = "skipped"
                result["notes"] += (
                    "Original .NET Developer job removed. "
                    f"No equivalent role available. Active: {[j['title'] for j in found_jobs]}"
                )
                await browser.close()
                return result

            print(f"\n  Best match: {dotnet_match['title']!r}")
            result["notes"] += f"Using nearest match: '{dotnet_match['title']}'. "
            result["url"] = dotnet_match["url"]

            status3 = await safe_goto(page, dotnet_match["url"])
            print(f"  Match page HTTP: {status3}, URL: {page.url}")

            ss = await take_screenshot(page, "03-matched-job")
            if ss:
                result["screenshots"].append(ss)

        # ---- Step 3: Look for Apply button ----
        print("\n[Step 3] Looking for Apply button...")

        apply_selectors = [
            "a:has-text('Apply Now')",
            "a:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Apply')",
            ".apply-button",
            "[data-action='apply']",
            "a:has-text('Solliciteer')",
            "a[href*='apply']",
        ]

        for sel in apply_selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    txt = (await el.inner_text()).strip()
                    print(f"  Clicking: {sel!r} ({txt!r})")
                    await el.click()
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        # Check for external redirect
        cur_url = page.url
        for ext in ["linkedin.com", "indeed.com", "greenhouse.io", "workable.com", "lever.co", "recruitee.com"]:
            if ext in cur_url:
                result["status"] = "skipped"
                result["notes"] += f" Redirected to external platform: {cur_url}"
                ss = await take_screenshot(page, "04-external-redirect")
                if ss:
                    result["screenshots"].append(ss)
                await browser.close()
                return result

        # Check CAPTCHA
        html = await page.content()
        if any(x in html.lower() for x in ["captcha", "recaptcha", "hcaptcha"]):
            result["status"] = "failed"
            result["notes"] += " CAPTCHA encountered."
            ss = await take_screenshot(page, "04-captcha")
            if ss:
                result["screenshots"].append(ss)
            await browser.close()
            return result

        # ---- Step 4: Fill form ----
        form_el = await page.query_selector("form")
        email_el = await page.query_selector("input[type='email'], input[name*='email']")

        if not form_el and not email_el:
            # Dump page text for diagnostics
            try:
                pg_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                print(f"  Page text (500 chars): {pg_text[:500]!r}")
            except Exception:
                pass
            result["status"] = "skipped"
            result["notes"] += " No application form found on the page."
            ss = await take_screenshot(page, "04-no-form")
            if ss:
                result["screenshots"].append(ss)
            await browser.close()
            return result

        print("\n[Step 4] Filling application form...")
        filled = await fill_form(page, cover_letter_text)
        print(f"  Filled {len(filled)} field(s)")

        ss = await take_screenshot(page, "04-form-filled")
        if ss:
            result["screenshots"].append(ss)

        if not filled:
            result["status"] = "skipped"
            result["notes"] += " Form found but no fields could be filled."
            await browser.close()
            return result

        # ---- Step 5: Submit ----
        print("\n[Step 5] Submitting...")
        submitted = False
        for sel in ["button[type='submit']", "input[type='submit']",
                    "button:has-text('Submit')", "button:has-text('Send')",
                    "button:has-text('Apply')", "[type='submit']"]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    label = ""
                    try:
                        label = (await el.inner_text()).strip()
                    except Exception:
                        label = await el.get_attribute("value") or sel
                    print(f"  Submit: {sel!r} ({label!r})")
                    ss = await take_screenshot(page, "05-pre-submit")
                    if ss:
                        result["screenshots"].append(ss)
                    await el.click()
                    await page.wait_for_timeout(3000)
                    submitted = True
                    print(f"  Submitted. URL: {page.url}")
                    break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        ss = await take_screenshot(page, "06-post-submit")
        if ss:
            result["screenshots"].append(ss)

        # Check success
        try:
            final_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            final_text = ""
        print(f"  Post-submit text (300): {final_text[:300]!r}")

        success_phrases = ["thank you", "application received", "successfully submitted",
                           "we have received", "will be in touch", "confirmation",
                           "received your application", "we'll contact", "bedankt"]
        success = any(p in final_text.lower() for p in success_phrases)

        if success:
            result["status"] = "applied"
            result["notes"] += " Application submitted — success message detected."
        elif submitted:
            result["status"] = "applied"
            result["notes"] += " Form submitted (no explicit success message detected)."
        else:
            result["status"] = "failed"
            result["notes"] += " Could not submit form (no submit button found/clickable)."

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
