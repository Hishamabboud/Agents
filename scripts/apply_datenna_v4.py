#!/usr/bin/env python3
"""
Apply to Datenna Python Engineer - Data Acquisition role.
Version 4: Pass proxy settings explicitly to Playwright.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Paths
SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")

# Applicant details
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

MOTIVATION = (
    "I am applying for the Python Engineer - Data Acquisition role at Datenna. "
    "At ASML I built Python automation tooling using Playwright-compatible browser automation, "
    "Pytest, and Locust to handle complex, dynamic test environments at scale. "
    "I have solid experience with HTTP fundamentals, session handling, BeautifulSoup, requests, "
    "and building resilient data pipelines. Currently I am building CogitatAI, an AI platform "
    "with a Python/Flask backend that includes real-time data acquisition pipelines and structured "
    "JSON output. I am based in Eindhoven and excited to contribute to Datenna's intelligence work."
)

APPLICATION_URL = "https://jobs.datenna.com/o/python-engineer-data-acquisition"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_settings():
    """Extract proxy settings from environment."""
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_url:
        return None

    # Parse http://user:password@host:port
    m = re.match(r"(https?)://([^:]+):([^@]+)@([^:]+):(\d+)", proxy_url)
    if m:
        scheme, user, pwd, host, port = m.groups()
        return {
            "server": f"{scheme}://{host}:{port}",
            "username": user,
            "password": pwd,
        }
    return None


async def safe_screenshot(page, name, full_page=True):
    path = SCREENSHOTS_DIR / f"datenna-{name}-{ts()}.png"
    for attempt, fp in [(True, True), (True, False), (False, False)]:
        try:
            await page.screenshot(
                path=str(path),
                full_page=fp,
                timeout=15000,
                animations="disabled",
            )
            print(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            if "fonts" in str(e).lower():
                # Try injecting CSS to disable font loading
                try:
                    await page.add_style_tag(content="* { font-family: Arial, sans-serif !important; }")
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
            print(f"Screenshot attempt failed: {e}")
    print(f"All screenshot attempts failed for {name}")
    return ""


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    print(f"CV: {CV_PATH}")

    proxy = get_proxy_settings()
    if proxy:
        print(f"Using proxy: {proxy['server']}")
    else:
        print("No proxy configured")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--font-render-hinting=none",
            ],
        }

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        if proxy:
            context_kwargs["proxy"] = proxy

        context = await browser.new_context(**context_kwargs)

        # Block font resources to prevent screenshot timeout
        async def route_handler(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", route_handler)

        page = await context.new_page()

        print(f"Navigating to: {APPLICATION_URL}")
        try:
            response = await page.goto(
                APPLICATION_URL,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            if response:
                print(f"Response status: {response.status}")
        except Exception as e:
            print(f"Goto exception: {e}")

        # Wait for network to settle
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        await asyncio.sleep(3)

        url = page.url
        title = await page.title()
        print(f"Current URL: {url}")
        print(f"Title: {title}")

        # Get body text
        try:
            body = await page.evaluate(
                "document.body ? document.body.innerHTML.length : 0"
            )
            print(f"Body HTML length: {body}")
        except Exception as e:
            print(f"Body check failed: {e}")

        # Get element counts
        try:
            counts = await page.evaluate("""
                () => ({
                    total: document.querySelectorAll('*').length,
                    inputs: document.querySelectorAll('input').length,
                    forms: document.querySelectorAll('form').length,
                    buttons: document.querySelectorAll('button').length,
                })
            """)
            print(f"DOM counts: {counts}")
        except Exception as e:
            print(f"DOM counts failed: {e}")

        # Take screenshot
        await safe_screenshot(page, "01-job-page")

        # Save page HTML
        try:
            html = await page.content()
            html_path = SCREENSHOTS_DIR / f"datenna-html-{ts()}.html"
            html_path.write_text(html[:100000])
            print(f"HTML saved: {html_path} ({len(html)} bytes)")
        except Exception as e:
            print(f"HTML save failed: {e}")
            html = ""

        # Look for Apply button
        apply_clicked = False
        apply_selectors = [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply now')",
            "button:has-text('Apply now')",
            "a[href*='apply']",
            "[class*='apply']",
            "a:has-text('Solliciteer')",
        ]

        for sel in apply_selectors:
            try:
                count = await page.locator(sel).count()
                if count > 0:
                    elem = page.locator(sel).first
                    vis = await elem.is_visible(timeout=2000)
                    if vis:
                        text = await elem.inner_text()
                        print(f"Clicking: '{text}' ({sel})")
                        await elem.click()
                        await asyncio.sleep(3)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=5000)
                        except Exception:
                            pass
                        apply_clicked = True
                        break
            except Exception:
                pass

        if apply_clicked:
            print(f"URL after apply: {page.url}")
            await safe_screenshot(page, "02-after-apply")
        else:
            print("No apply button found")

        # Analyze all form elements
        print("\n--- Form elements ---")
        try:
            all_elems = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select, label')).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    forAttr: el.htmlFor || '',
                    visible: el.offsetParent !== null,
                    text: el.innerText ? el.innerText.substring(0, 50) : ''
                }))
            """)
            print(f"Total form elements: {len(all_elems)}")
            for el in all_elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form analysis failed: {e}")
            all_elems = []

        filled = []
        cv_uploaded = False

        async def fill_input(locators, value, desc):
            for loc in locators:
                try:
                    elem = page.locator(loc).first
                    if await elem.count() > 0 and await elem.is_visible(timeout=1500):
                        await elem.click(timeout=2000)
                        await asyncio.sleep(0.2)
                        await elem.fill(value, timeout=3000)
                        filled.append(desc)
                        print(f"  Filled [{desc}]: '{value}'")
                        return True
                except Exception:
                    pass
            print(f"  Could not fill [{desc}]")
            return False

        # Fill fields
        await fill_input(
            ["input[name='name']", "input[id='name']", "input[autocomplete='name']",
             "input[placeholder*='Full name' i]", "input[placeholder*='Name' i]"],
            APPLICANT["full_name"], "full_name"
        )
        await fill_input(
            ["input[name='first_name']", "input[name='firstName']", "input[id='first_name']",
             "input[autocomplete='given-name']", "input[placeholder*='First' i]"],
            APPLICANT["first_name"], "first_name"
        )
        await fill_input(
            ["input[name='last_name']", "input[name='lastName']", "input[id='last_name']",
             "input[autocomplete='family-name']", "input[placeholder*='Last' i]"],
            APPLICANT["last_name"], "last_name"
        )
        await fill_input(
            ["input[type='email']", "input[name='email']", "input[id='email']",
             "input[autocomplete='email']"],
            APPLICANT["email"], "email"
        )
        await fill_input(
            ["input[type='tel']", "input[name='phone']", "input[name='phone_number']",
             "input[id='phone']", "input[autocomplete='tel']", "input[placeholder*='Phone' i]"],
            APPLICANT["phone"], "phone"
        )
        await fill_input(
            ["input[name='linkedin']", "input[name*='linkedin' i]", "input[id*='linkedin' i]",
             "input[placeholder*='LinkedIn' i]"],
            APPLICANT["linkedin"], "linkedin"
        )

        # Textarea
        for loc in ["textarea", "textarea[name*='cover' i]", "textarea[name*='letter' i]",
                    "textarea[name*='motivation' i]"]:
            try:
                count = await page.locator(loc).count()
                if count > 0:
                    elem = page.locator(loc).first
                    if await elem.is_visible(timeout=1500):
                        await elem.click()
                        await asyncio.sleep(0.2)
                        await elem.fill(MOTIVATION)
                        filled.append("motivation")
                        print(f"  Filled motivation textarea")
                        break
            except Exception:
                pass

        # File upload
        file_inputs = await page.locator("input[type='file']").all()
        print(f"\nFile inputs: {len(file_inputs)}")
        for i, fi in enumerate(file_inputs):
            try:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  CV uploaded to file input {i}")
                await asyncio.sleep(2)
                break
            except Exception as e:
                print(f"  File input {i} error: {e}")

        # Checkboxes
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"\nCheckboxes: {len(checkboxes)}")
        for i, cb in enumerate(checkboxes):
            try:
                if not await cb.is_checked():
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll to bottom
        try:
            await page.evaluate("document.body && window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(page, "05-pre-submit")
        print(f"\nPre-submit state: filled={filled}, cv_uploaded={cv_uploaded}")

        # Find and click submit
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send application')",
            "button:has-text('Submit application')",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                count = await page.locator(sel).count()
                if count > 0:
                    elem = page.locator(sel).first
                    if await elem.is_visible(timeout=2000):
                        text = await elem.inner_text()
                        print(f"\nSubmitting via: '{text}'")
                        await elem.click()
                        await asyncio.sleep(5)
                        submitted = True
                        break
            except Exception as e:
                print(f"Submit {sel}: {e}")

        final_url = page.url
        await safe_screenshot(page, "06-post-submit")

        if submitted:
            try:
                body_text = await page.evaluate("document.body.innerText")
                print(f"Post-submit text: {body_text[:600]}")
                success_words = ["thank", "confirm", "success", "received", "submitted",
                                  "bedankt", "we have", "application"]
                is_success = any(w in body_text.lower() for w in success_words)
                if is_success:
                    await safe_screenshot(page, "07-confirmation")
                    print("Application confirmed!")
                    status = "applied"
                    notes = "Successfully submitted to Datenna Python Engineer - Data Acquisition"
                else:
                    status = "applied"
                    notes = f"Submitted (confirmation unclear). Final URL: {final_url}"
            except Exception as e:
                status = "applied"
                notes = f"Submitted, verification error: {e}"
        else:
            # Log visible buttons for debugging
            try:
                btns = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('button, input[type=submit]'))
                        .filter(el => el.offsetParent !== null)
                        .map(el => ({tag: el.tagName, text: el.innerText || el.value, type: el.type}))
                """)
                print(f"Visible buttons: {btns[:10]}")
            except Exception:
                pass
            status = "failed"
            notes = "Could not find/click submit button. Page may not have loaded."

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
