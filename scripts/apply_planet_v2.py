#!/usr/bin/env python3
"""
Automated application for Planet - Software Engineer, Integration Platform
v2: with proxy handling and extended timeouts
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

JOB_URL = "https://boards.greenhouse.io/planetlabs/jobs/5034494"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/planet-software-engineer.md"
SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
APPLICATIONS_JSON = Path("/home/user/Agents/data/applications.json")

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def load_applications():
    if APPLICATIONS_JSON.exists():
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    return []

def save_application(app_data):
    apps = load_applications()
    # Remove any previous failed attempt for same job
    apps = [a for a in apps if a.get("id") != app_data["id"]]
    apps.append(app_data)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    log(f"Application logged to {APPLICATIONS_JSON}")

async def screenshot(page, name, timeout=60000):
    path = str(SCREENSHOTS_DIR / f"planet-{name}-{ts()}.png")
    try:
        await page.screenshot(path=path, full_page=True, timeout=timeout)
        log(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        log(f"Screenshot failed for {name}: {e}")
        return None

async def try_fill(page, selector, value, label="field"):
    try:
        el = page.locator(selector).first
        count = await el.count()
        if count == 0:
            return False
        await el.scroll_into_view_if_needed(timeout=3000)
        await el.fill(value, timeout=5000)
        log(f"Filled {label}")
        return True
    except Exception as e:
        log(f"Could not fill {label}: {e}")
        return False

async def run():
    application_data = {
        "id": "planet-software-engineer-integration-platform",
        "company": "Planet",
        "role": "Software Engineer, Integration Platform",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8,
        "status": "failed",
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshot": None,
        "notes": "",
        "response": None,
    }

    # Check proxy env
    http_proxy = os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY") or ""
    https_proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    log(f"Proxy env: http={http_proxy}, https={https_proxy}")

    browser_kwargs = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    }

    # Add proxy if detected
    proxy_config = None
    proxy_url = https_proxy or http_proxy
    if proxy_url:
        log(f"Using proxy: {proxy_url}")
        proxy_config = {"server": proxy_url}
        browser_kwargs["proxy"] = proxy_config

    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(**browser_kwargs)
        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "ignore_https_errors": True,
        }
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        # Set default timeout
        page.set_default_timeout(45000)

        try:
            log(f"Navigating to {JOB_URL}")
            try:
                resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
                status = resp.status if resp else "unknown"
                log(f"Page loaded, status: {status}")
            except Exception as e:
                log(f"Initial load error: {e}")
                # Try the redirect URL directly
                log("Trying redirect URL directly...")
                resp = await page.goto(
                    "https://job-boards.greenhouse.io/planetlabs/jobs/5034494",
                    wait_until="domcontentloaded",
                    timeout=45000
                )
                status = resp.status if resp else "unknown"
                log(f"Redirect URL loaded, status: {status}")

            await page.wait_for_timeout(3000)
            current_url = page.url
            log(f"Current URL: {current_url}")

            # Get page content
            page_text = await page.inner_text("body")
            log(f"Page text length: {len(page_text)}")
            log(f"Page snippet (first 300 chars): {page_text[:300]}")

            sc = await screenshot(page, "01-job-page")
            if sc:
                screenshots.append(sc)

            # Look for apply form directly on the page (Greenhouse embeds it)
            # First check if form fields are already visible
            email_field = page.locator("input#email, input[name*='email'], input[type='email']").first
            email_visible = False
            try:
                email_visible = await email_field.is_visible(timeout=3000)
            except Exception:
                pass

            if not email_visible:
                # Look for Apply Now button
                log("Form not immediately visible, looking for Apply button...")
                apply_btns = page.locator("a:has-text('Apply'), button:has-text('Apply'), a:has-text('Apply Now'), button:has-text('Apply Now')")
                btn_count = await apply_btns.count()
                log(f"Apply buttons: {btn_count}")
                if btn_count > 0:
                    await apply_btns.first.click()
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(2000)
                    log(f"After apply click URL: {page.url}")
                    sc = await screenshot(page, "02-after-apply-click")
                    if sc:
                        screenshots.append(sc)

            # Now fill the form
            await page.wait_for_timeout(1000)

            # Standard Greenhouse fields
            fills = [
                ("input#first_name, input[name='job_application[first_name]']", CANDIDATE["first_name"], "First Name"),
                ("input#last_name, input[name='job_application[last_name]']", CANDIDATE["last_name"], "Last Name"),
                ("input#email, input[name='job_application[email]'], input[type='email']", CANDIDATE["email"], "Email"),
                ("input#phone, input[name='job_application[phone]'], input[type='tel']", CANDIDATE["phone"], "Phone"),
            ]
            for sel, val, lbl in fills:
                await try_fill(page, sel, val, lbl)

            await page.wait_for_timeout(300)

            # Location
            await try_fill(page, "input[id*='location'], input[name*='location'], input[placeholder*='ity']", CANDIDATE["city"], "Location/City")

            # LinkedIn
            await try_fill(page, "input[id*='linkedin'], input[name*='linkedin'], input[placeholder*='inkedin']", CANDIDATE["linkedin"], "LinkedIn URL")

            # GitHub
            await try_fill(page, "input[id*='github'], input[name*='github'], input[placeholder*='ithub']", CANDIDATE["github"], "GitHub URL")

            # Website
            await try_fill(page, "input[id*='website'], input[name*='website'], input[placeholder*='ebsite'], input[id*='portfolio']", "https://github.com/Hishamabboud", "Website")

            # Cover letter
            cl_filled = False
            cl_selectors = [
                "textarea[name*='cover']",
                "textarea[id*='cover']",
                "textarea[placeholder*='cover' i]",
                "textarea[placeholder*='letter' i]",
                "#cover_letter_text",
                "textarea",
            ]
            for sel in cl_selectors:
                try:
                    el = page.locator(sel).first
                    count = await el.count()
                    if count > 0 and await el.is_visible(timeout=2000):
                        await el.fill(COVER_LETTER_TEXT, timeout=5000)
                        log(f"Filled cover letter via {sel}")
                        cl_filled = True
                        break
                except Exception:
                    pass
            if not cl_filled:
                log("Cover letter textarea not found.")

            # Resume upload
            file_inputs = page.locator("input[type='file']")
            fi_count = await file_inputs.count()
            log(f"File inputs found: {fi_count}")
            if fi_count > 0:
                log(f"Uploading resume from: {RESUME_PATH}")
                await file_inputs.first.set_input_files(RESUME_PATH)
                await page.wait_for_timeout(3000)
                log("Resume upload triggered.")
            else:
                log("No file input found.")

            # Handle dropdowns
            selects = page.locator("select")
            sel_count = await selects.count()
            log(f"Select dropdowns: {sel_count}")
            for i in range(sel_count):
                sel_el = selects.nth(i)
                sel_id = await sel_el.get_attribute("id") or ""
                sel_name = await sel_el.get_attribute("name") or ""
                log(f"Select {i}: id={sel_id}, name={sel_name}")
                if "country" in sel_id.lower() or "country" in sel_name.lower():
                    try:
                        await sel_el.select_option(label="Netherlands")
                        log("Selected Netherlands")
                    except Exception as e:
                        log(f"Could not select Netherlands: {e}")

            await page.wait_for_timeout(500)
            sc = await screenshot(page, "03-form-filled")
            if sc:
                screenshots.append(sc)

            # Check checkboxes (privacy/consent)
            checkboxes = page.locator("input[type='checkbox']")
            cb_count = await checkboxes.count()
            log(f"Checkboxes: {cb_count}")
            for i in range(cb_count):
                cb = checkboxes.nth(i)
                try:
                    cb_id = await cb.get_attribute("id") or ""
                    cb_name = await cb.get_attribute("name") or ""
                    label_text = ""
                    try:
                        label_el = page.locator(f"label[for='{cb_id}']")
                        if await label_el.count() > 0:
                            label_text = await label_el.inner_text(timeout=1000)
                    except Exception:
                        pass
                    log(f"CB {i}: id={cb_id}, label='{label_text[:50]}'")
                    consent_words = ["privacy", "consent", "agree", "terms", "gdpr", "policy", "data"]
                    if any(w in label_text.lower() or w in cb_name.lower() for w in consent_words):
                        if not await cb.is_checked():
                            await cb.check()
                            log(f"Checked consent checkbox: {label_text[:40]}")
                except Exception as e:
                    log(f"CB {i} error: {e}")

            # Screenshot before submit
            sc = await screenshot(page, "04-before-submit")
            if sc:
                screenshots.append(sc)
            application_data["screenshot"] = sc

            # Submit
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Submit Application')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                        txt = ""
                        try:
                            txt = await btn.inner_text(timeout=1000)
                        except Exception:
                            pass
                        log(f"Clicking submit: '{txt}' ({sel})")
                        await btn.click(timeout=10000)
                        await page.wait_for_load_state("domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(3000)
                        submitted = True
                        break
                except Exception as e:
                    log(f"Submit {sel} failed: {e}")

            final_url = page.url
            log(f"Final URL: {final_url}")
            body_text = await page.inner_text("body")
            log(f"Final page snippet: {body_text[:300]}")

            sc = await screenshot(page, "05-after-submit")
            if sc:
                screenshots.append(sc)
                application_data["screenshot"] = sc

            success_kw = ["thank", "application received", "submitted", "confirmation", "we'll be in touch", "success", "completed"]
            is_success = any(kw in body_text.lower() for kw in success_kw)

            if is_success:
                application_data["status"] = "applied"
                application_data["notes"] = f"Submitted successfully. URL: {final_url}. Confirmation detected."
                log("SUCCESS: Application submitted and confirmation detected.")
            elif submitted:
                application_data["status"] = "applied"
                application_data["notes"] = f"Submit clicked. URL: {final_url}. No explicit confirmation text found."
                log("Submit clicked - marked as applied (uncertain confirmation).")
            else:
                application_data["status"] = "failed"
                application_data["notes"] = f"No submit button found/clicked. URL: {final_url}."
                log("FAILED: Could not submit.")

        except Exception as e:
            log(f"Error: {e}")
            application_data["status"] = "failed"
            application_data["notes"] = f"Error: {str(e)[:300]}"
            try:
                sc = await screenshot(page, "error")
                if sc:
                    application_data["screenshot"] = sc
            except Exception:
                pass
        finally:
            await browser.close()

    application_data["screenshots"] = screenshots
    save_application(application_data)
    return application_data

if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== APPLICATION RESULT ===")
    print(json.dumps(result, indent=2))
