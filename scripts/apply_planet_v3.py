#!/usr/bin/env python3
"""
Planet application v3 — correct proxy parsing for Playwright
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
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def parse_proxy(proxy_url):
    """
    Parse proxy URL in format:
      http://user:password@host:port
    Returns dict for Playwright: {"server": "http://host:port", "username": "...", "password": "..."}
    """
    if not proxy_url:
        return None
    # Match http://user:pass@host:port or https://...
    m = re.match(r'(https?://)([^:@]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        scheme = m.group(1).rstrip("://")
        username = m.group(2)
        password = m.group(3)
        host = m.group(4)
        port = m.group(5)
        server = f"http://{host}:{port}"
        log(f"Parsed proxy server={server}, user={username[:20]}...")
        return {"server": server, "username": username, "password": password}
    # Fallback: use as-is
    log(f"Using proxy as-is: {proxy_url[:60]}...")
    return {"server": proxy_url}

def load_applications():
    if APPLICATIONS_JSON.exists():
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    return []

def save_application(app_data):
    apps = load_applications()
    apps = [a for a in apps if a.get("id") != app_data["id"]]
    apps.append(app_data)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    log(f"Saved to {APPLICATIONS_JSON}")

async def screenshot(page, name):
    path = str(SCREENSHOTS_DIR / f"planet-{name}-{ts()}.png")
    try:
        await page.screenshot(path=path, full_page=True, timeout=15000)
        log(f"Screenshot: {path}")
        return path
    except Exception as e:
        log(f"Screenshot failed ({name}): {e}")
        return None

async def fill(page, selector, value, label):
    try:
        el = page.locator(selector).first
        if await el.count() == 0:
            return False
        await el.fill(value, timeout=5000)
        log(f"Filled: {label}")
        return True
    except Exception as e:
        log(f"Fill failed ({label}): {e}")
        return False

async def run():
    app = {
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

    raw_proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or \
                os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY") or ""
    proxy_cfg = parse_proxy(raw_proxy)

    launch_kwargs = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    if proxy_cfg:
        launch_kwargs["proxy"] = proxy_cfg

    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_kwargs)
        ctx_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "ignore_https_errors": True,
        }
        # Don't pass proxy at context level if already at browser level
        context = await browser.new_context(**ctx_kwargs)
        page = await context.new_page()
        page.set_default_timeout(30000)

        try:
            log(f"Loading {JOB_URL}")
            resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=40000)
            log(f"Status: {resp.status if resp else '?'}, URL: {page.url}")
            await page.wait_for_timeout(2000)

            body = await page.inner_text("body")
            log(f"Body preview: {body[:200]}")

            sc = await screenshot(page, "01-loaded")
            if sc:
                screenshots.append(sc)
                app["screenshot"] = sc

            # Check for 407 or block
            if resp and resp.status == 407:
                app["status"] = "failed"
                app["notes"] = "HTTP 407 Proxy Authentication Required — browser cannot reach greenhouse.io through this proxy."
                log("407 Proxy Auth error — cannot proceed with browser automation.")
                save_application(app)
                return app

            # Look for Apply button
            email_input = page.locator("input#email, input[type='email']").first
            has_email = await email_input.count() > 0
            if not has_email:
                # Click Apply Now
                apply_link = page.locator("a:has-text('Apply'), button:has-text('Apply'), a:has-text('Apply Now')")
                if await apply_link.count() > 0:
                    log("Clicking Apply Now...")
                    await apply_link.first.click()
                    await page.wait_for_timeout(3000)
                    sc = await screenshot(page, "02-apply-clicked")
                    if sc:
                        screenshots.append(sc)

            # Fill form
            await fill(page, "input#first_name, input[name='job_application[first_name]']", CANDIDATE["first_name"], "First Name")
            await fill(page, "input#last_name, input[name='job_application[last_name]']", CANDIDATE["last_name"], "Last Name")
            await fill(page, "input#email, input[name='job_application[email]'], input[type='email']", CANDIDATE["email"], "Email")
            await fill(page, "input#phone, input[name='job_application[phone]'], input[type='tel']", CANDIDATE["phone"], "Phone")
            await fill(page, "input[id*='location'], input[name*='location']", CANDIDATE["city"], "Location")
            await fill(page, "input[id*='linkedin'], input[name*='linkedin']", CANDIDATE["linkedin"], "LinkedIn")
            await fill(page, "input[id*='github'], input[name*='github']", CANDIDATE["github"], "GitHub")

            # Cover letter
            for sel in ["textarea[name*='cover']", "textarea[id*='cover']", "textarea"]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        await el.fill(COVER_LETTER_TEXT)
                        log("Filled cover letter.")
                        break
                except Exception:
                    pass

            # Upload resume
            fi = page.locator("input[type='file']").first
            if await fi.count() > 0:
                await fi.set_input_files(RESUME_PATH)
                await page.wait_for_timeout(2000)
                log("Resume uploaded.")

            # Checkboxes
            cbs = page.locator("input[type='checkbox']")
            for i in range(await cbs.count()):
                cb = cbs.nth(i)
                cb_id = await cb.get_attribute("id") or ""
                lbl = ""
                try:
                    lbl_el = page.locator(f"label[for='{cb_id}']")
                    if await lbl_el.count() > 0:
                        lbl = await lbl_el.inner_text(timeout=1000)
                except Exception:
                    pass
                if any(w in lbl.lower() for w in ["privacy", "consent", "agree", "terms", "gdpr"]):
                    if not await cb.is_checked():
                        await cb.check()
                        log(f"Checked: {lbl[:50]}")

            sc = await screenshot(page, "03-before-submit")
            if sc:
                screenshots.append(sc)
                app["screenshot"] = sc

            # Submit
            submitted = False
            for sel in ["input[type='submit']", "button[type='submit']",
                        "button:has-text('Submit')", "button:has-text('Apply')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                        txt = await btn.inner_text(timeout=1000)
                        log(f"Submitting via '{txt}'...")
                        await btn.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(3000)
                        submitted = True
                        break
                except Exception as e:
                    log(f"Submit attempt failed: {e}")

            final_body = await page.inner_text("body")
            sc = await screenshot(page, "04-after-submit")
            if sc:
                screenshots.append(sc)
                app["screenshot"] = sc

            success = any(k in final_body.lower() for k in ["thank", "received", "submitted", "success", "confirmation"])
            if success:
                app["status"] = "applied"
                app["notes"] = f"Submitted successfully. Confirmation detected. URL: {page.url}"
                log("SUCCESS.")
            elif submitted:
                app["status"] = "applied"
                app["notes"] = f"Submit clicked. No confirmation text. URL: {page.url}"
                log("Submitted (no confirmation text).")
            else:
                app["status"] = "failed"
                app["notes"] = f"Submit button not found. URL: {page.url}"

        except Exception as e:
            log(f"Error: {e}")
            app["status"] = "failed"
            app["notes"] = str(e)[:300]
            try:
                sc = await screenshot(page, "error")
                if sc:
                    app["screenshot"] = sc
                    screenshots.append(sc)
            except Exception:
                pass
        finally:
            await browser.close()

    app["screenshots"] = screenshots
    save_application(app)
    return app

if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
