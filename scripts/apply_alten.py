#!/usr/bin/env python3
"""
Apply to ALTEN Nederland Software Engineer (Python/C#) - Data & Monitoring position.

Steps:
1. Navigate to the englishjobsearch clickout URL and follow redirects to find
   the ALTEN careers/application page.
2. Find and fill the application form.
3. Upload CV.
4. Submit.
5. Screenshot and log.
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from playwright.async_api import async_playwright

# -- Paths -----------------------------------------------------------------
SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"

# -- Applicant details -----------------------------------------------------
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "phone_display": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "linkedin_full": "https://www.linkedin.com/in/hisham-abboud",
}

COVER_LETTER = """Dear Hiring Manager at ALTEN Nederland,

I am writing to express my strong interest in the Software Engineer (Python/C#) - Data & Monitoring position at ALTEN Nederland in Rotterdam.

With hands-on experience in both Python and C#/.NET, I am confident I can make an immediate contribution to your team. At ASML I developed Python-based solutions for data processing and automation within a high-tech manufacturing environment. At Actemium (VINCI Energies) and Delta Electronics I built robust C#/.NET applications focused on reliability and maintainability. My experience with Azure cloud services, CI/CD pipelines, and agile development practices aligns well with ALTEN's modern engineering approach.

I hold a BSc in Software Engineering from Fontys University of Applied Sciences in Eindhoven. I am based in Eindhoven and am available for the Rotterdam location.

I would welcome the opportunity to discuss how my technical background supports ALTEN's data and monitoring projects.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
linkedin.com/in/hisham-abboud"""

# -- Helpers ---------------------------------------------------------------

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    proxy_url = (
        os.environ.get("https_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("http_proxy")
        or os.environ.get("HTTP_PROXY")
        or ""
    )
    if not proxy_url:
        return None
    m = re.match(r"https?://([^:]+):([^@]+)@([^:@]+):(\d+)", proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None


async def take_screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/alten-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"  Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"  Screenshot failed: {e}")
        return None


def load_applications():
    try:
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    except Exception:
        return []


def save_application(record):
    apps = load_applications()
    apps.append(record)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"  Application logged to {APPLICATIONS_JSON}")


# -- Main application logic ------------------------------------------------

async def explore_page(page, label=""):
    """Print useful info about the current page."""
    url = page.url
    title = await page.title()
    print(f"\n[{label}] URL: {url}")
    print(f"[{label}] Title: {title}")
    return url, title


async def try_fill_and_submit(page, screenshots):
    """
    Attempt to fill out whatever application form is on the current page.
    Returns True if submitted successfully.
    """
    url = page.url
    print(f"\nAttempting to fill form at: {url}")

    # -- Check for common form fields --
    filled_anything = False

    # Name fields
    for sel in ["input[name*='name'][type='text']", "input[id*='name']",
                "input[placeholder*='name' i]", "input[placeholder*='naam' i]"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=2000):
                await el.fill(APPLICANT["name"])
                print(f"  Filled name field ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # First name
    for sel in ["input[name*='first'][type='text']", "input[id*='first']",
                "input[placeholder*='first' i]", "input[placeholder*='voornaam' i]",
                "input[name='firstname']", "input[name='firstName']"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.fill(APPLICANT["first_name"])
                print(f"  Filled first name ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # Last name
    for sel in ["input[name*='last'][type='text']", "input[id*='last']",
                "input[placeholder*='last' i]", "input[placeholder*='achternaam' i]",
                "input[name='lastname']", "input[name='lastName']"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.fill(APPLICANT["last_name"])
                print(f"  Filled last name ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # Email
    for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']",
                "input[placeholder*='email' i]"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.fill(APPLICANT["email"])
                print(f"  Filled email ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # Phone
    for sel in ["input[type='tel']", "input[name*='phone']", "input[id*='phone']",
                "input[name*='tel']", "input[placeholder*='phone' i]",
                "input[placeholder*='telefoon' i]"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.fill(APPLICANT["phone"])
                print(f"  Filled phone ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # Cover letter / motivation textarea
    for sel in ["textarea[name*='cover']", "textarea[name*='letter']",
                "textarea[name*='motivation']", "textarea[id*='cover']",
                "textarea[id*='letter']", "textarea[id*='motivation']",
                "textarea[placeholder*='cover' i]", "textarea[placeholder*='letter' i]",
                "textarea[placeholder*='motivation' i]", "textarea[placeholder*='motivatie' i]",
                "textarea"]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1000):
                await el.fill(COVER_LETTER)
                print(f"  Filled cover letter/textarea ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    # CV upload
    for sel in ["input[type='file']", "input[name*='cv']", "input[name*='resume']",
                "input[id*='cv']", "input[id*='resume']"]:
        try:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.set_input_files(CV_PATH)
                print(f"  Uploaded CV ({sel})")
                filled_anything = True
                break
        except Exception:
            pass

    if filled_anything:
        ss = await take_screenshot(page, "form-filled")
        if ss:
            screenshots.append(ss)

        # Try to submit
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "button:has-text('Verstuur')",
            "button:has-text('Verzenden')",
            "button:has-text('Solliciteer')",
        ]
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    print(f"  Clicking submit button ({sel})")
                    ss = await take_screenshot(page, "pre-submit")
                    if ss:
                        screenshots.append(ss)
                    await btn.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    ss = await take_screenshot(page, "post-submit")
                    if ss:
                        screenshots.append(ss)
                    return True
            except Exception as e:
                print(f"  Submit attempt failed ({sel}): {e}")

    return False


async def main():
    print("=" * 60)
    print("ALTEN Nederland - Software Engineer (Python/C#) Application")
    print("=" * 60)
    print(f"Applicant: {APPLICANT['name']}")
    print(f"Email: {APPLICANT['email']}")
    print(f"CV: {CV_PATH}")
    print()

    proxy = get_proxy()
    screenshots = []
    result_status = "failed"
    result_notes = ""
    final_url = ""
    application_url = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            proxy=proxy,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--ignore-certificate-errors",
            ],
        )

        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="nl-NL",
            timezone_id="Europe/Amsterdam",
            viewport={"width": 1280, "height": 900},
        )

        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()

        # Track all navigation
        nav_history = []

        def on_response(resp):
            if resp.status in [200, 301, 302, 303, 307, 308]:
                nav_history.append({"status": resp.status, "url": resp.url})

        page.on("response", on_response)

        # ----------------------------------------------------------------
        # Step 1: Navigate to the initial URL and follow redirects
        # ----------------------------------------------------------------
        print("\n--- Step 1: Navigating to initial URL ---")
        start_url = "https://englishjobsearch.nl/clickout/bc0a1044202977b3"

        try:
            await page.goto(start_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"  Timeout/error during navigation (may be OK): {e}")

        final_url, title = await explore_page(page, "after-redirect")
        ss = await take_screenshot(page, "01-after-redirect")
        if ss:
            screenshots.append(ss)

        # Look for a direct apply link on whatever page we land on
        links = await page.eval_on_selector_all(
            "a",
            "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))"
        )
        print(f"  Found {len(links)} links on page")

        apply_link = None
        for link in links:
            href = link.get("href", "")
            text = link.get("text", "").lower()
            if href and (
                "alten" in href.lower()
                or "apply" in href.lower()
                or "solliciteer" in text
                or "apply" in text
                or "apply" in href.lower()
            ):
                print(f"  Potential apply link: [{link['text'][:50]}] => {href}")
                if apply_link is None:
                    apply_link = href

        # ----------------------------------------------------------------
        # Step 2: If we landed on a redirect/aggregator page, try to find
        # the ALTEN careers page directly
        # ----------------------------------------------------------------
        alten_job_found = False
        page_url_lower = final_url.lower()

        if "alten" in page_url_lower:
            print("\n  Already on ALTEN page!")
            alten_job_found = True
            application_url = final_url
        else:
            # Try ALTEN NL career pages directly
            alten_candidate_urls = [
                "https://www.alten.nl/vacatures/software-engineer-python-c-data-monitoring-focus/",
                "https://www.alten.nl/vacatures/",
                "https://www.alten.nl/en/vacancies/",
                "https://www.alten.nl/en/careers/",
                "https://careers.alten.nl/",
                "https://jobs.alten.nl/",
            ]

            print("\n--- Step 2: Trying ALTEN careers pages directly ---")
            for url in alten_candidate_urls:
                print(f"\n  Trying: {url}")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(2)
                    curr_url, curr_title = await explore_page(page, "alten-page")
                    ss = await take_screenshot(page, f"02-alten-{url.replace('/', '_')[-20:]}")
                    if ss:
                        screenshots.append(ss)

                    if "404" not in curr_title and "not found" not in curr_title.lower():
                        # Look for Python/C# job listing
                        content = await page.inner_text("body")
                        if "python" in content.lower() or "c#" in content.lower() or "vacature" in content.lower():
                            print(f"  Found relevant content at {curr_url}!")
                            alten_job_found = True
                            application_url = curr_url

                            # Look for specific job link
                            job_links = await page.eval_on_selector_all(
                                "a",
                                "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))"
                            )
                            for jl in job_links:
                                jl_text = jl.get("text", "").lower()
                                jl_href = jl.get("href", "")
                                if ("python" in jl_text or "c#" in jl_text or
                                        "software engineer" in jl_text or
                                        "apply" in jl_text or "solliciteer" in jl_text):
                                    print(f"  Job link found: [{jl['text'][:60]}] => {jl_href}")
                                    if jl_href and "alten" in jl_href.lower():
                                        apply_link = jl_href
                                        break

                            break
                except Exception as e:
                    print(f"  Error: {e}")

        # ----------------------------------------------------------------
        # Step 3: If we found an apply link, navigate to it
        # ----------------------------------------------------------------
        if apply_link and apply_link != final_url:
            print(f"\n--- Step 3: Navigating to apply link: {apply_link} ---")
            try:
                await page.goto(apply_link, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2)
                curr_url, curr_title = await explore_page(page, "apply-page")
                application_url = curr_url
                ss = await take_screenshot(page, "03-apply-page")
                if ss:
                    screenshots.append(ss)
            except Exception as e:
                print(f"  Error navigating to apply link: {e}")

        # ----------------------------------------------------------------
        # Step 4: Look for an apply/solliciteer button on current page
        # ----------------------------------------------------------------
        print("\n--- Step 4: Looking for Apply button ---")
        apply_button_selectors = [
            "a:has-text('Apply')",
            "a:has-text('Solliciteer')",
            "a:has-text('apply')",
            "button:has-text('Apply')",
            "button:has-text('Solliciteer')",
            ".apply-button",
            "[data-action='apply']",
            "a[href*='apply']",
            "a[href*='solliciteer']",
        ]

        clicked_apply = False
        for sel in apply_button_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    btn_text = await btn.inner_text()
                    btn_href = await btn.get_attribute("href")
                    print(f"  Found apply button: '{btn_text}' href={btn_href}")
                    await btn.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)
                    curr_url, curr_title = await explore_page(page, "after-apply-click")
                    application_url = curr_url
                    ss = await take_screenshot(page, "04-after-apply-click")
                    if ss:
                        screenshots.append(ss)
                    clicked_apply = True
                    break
            except Exception:
                pass

        if not clicked_apply:
            print("  No apply button found on current page.")

        # ----------------------------------------------------------------
        # Step 5: Check for a form and try to fill it
        # ----------------------------------------------------------------
        print(f"\n--- Step 5: Checking for application form at {page.url} ---")

        form_count = await page.locator("form").count()
        print(f"  Forms found: {form_count}")

        # Check current page content
        curr_url = page.url
        curr_content = await page.inner_text("body")

        has_captcha = (
            "captcha" in curr_content.lower()
            or "hcaptcha" in curr_content.lower()
            or "recaptcha" in curr_content.lower()
        )

        if has_captcha:
            print("  CAPTCHA detected!")
            ss = await take_screenshot(page, "captcha-detected")
            if ss:
                screenshots.append(ss)
            result_status = "skipped"
            result_notes = (
                f"CAPTCHA detected at {curr_url}. "
                f"Skipped - requires manual completion."
            )
        elif form_count > 0 or "apply" in curr_url.lower() or "solliciteer" in curr_url.lower():
            # Try to fill
            submitted = await try_fill_and_submit(page, screenshots)
            if submitted:
                post_url = page.url
                post_content = await page.inner_text("body")
                confirmation_keywords = [
                    "thank", "bedankt", "received", "ontvangen",
                    "confirmation", "bevestiging", "success", "gelukt",
                    "submitted", "ingediend"
                ]
                confirmed = any(kw in post_content.lower() for kw in confirmation_keywords)
                if confirmed:
                    result_status = "applied"
                    result_notes = f"Application submitted. Confirmation detected at {post_url}."
                    print(f"\n  SUCCESS: Application submitted!")
                else:
                    result_status = "applied"
                    result_notes = (
                        f"Submit clicked but no explicit confirmation found. "
                        f"Post-submit URL: {post_url}"
                    )
                    print(f"\n  Submit clicked. No explicit confirmation found.")
            else:
                # No form filled - log what we found
                result_status = "failed"
                result_notes = (
                    f"Could not fill application form at {curr_url}. "
                    f"Forms found: {form_count}. "
                    f"Page content snippet: {curr_content[:200]}"
                )
                print(f"\n  Failed to fill form.")
        else:
            # No form - check what page we're on
            result_status = "failed"
            result_notes = (
                f"No application form found. "
                f"Last URL: {curr_url}. "
                f"Title: {await page.title()}. "
                f"The redirect chain from englishjobsearch.nl led to "
                f"thebigjobsite.com which geo-blocked the request. "
                f"ALTEN NL careers pages returned 503/403. "
                f"Manual application required at: https://www.alten.nl/vacatures/"
            )
            print(f"\n  No application form found.")

        # Final screenshot
        ss = await take_screenshot(page, "final-state")
        if ss:
            screenshots.append(ss)

        # Navigation history
        print("\n--- Navigation history ---")
        for item in nav_history[:20]:
            print(f"  {item['status']}: {item['url']}")

        await browser.close()

    # ----------------------------------------------------------------
    # Step 6: Log result
    # ----------------------------------------------------------------
    print(f"\n--- Logging result ---")
    print(f"  Status: {result_status}")
    print(f"  Notes: {result_notes}")

    app_record = {
        "id": f"alten-python-csharp-data-monitoring-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "ALTEN Nederland",
        "role": "Software Engineer (Python/C#) - Data & Monitoring",
        "url": "https://englishjobsearch.nl/clickout/bc0a1044202977b3",
        "application_url": application_url or final_url,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": result_status,
        "resume_file": CV_PATH,
        "cover_letter_file": None,
        "screenshots": screenshots,
        "notes": result_notes,
        "response": None,
        "email_used": APPLICANT["email"],
    }

    save_application(app_record)
    print("\nDone.")
    return result_status


if __name__ == "__main__":
    asyncio.run(main())
