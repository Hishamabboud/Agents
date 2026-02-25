#!/usr/bin/env python3
"""
Apply to Datenna Python Engineer - Data Acquisition role.
Version 3: Better handling of JS-heavy sites, force load state.
"""

import asyncio
import json
import base64
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"datenna-{name}-{ts()}.png"
    try:
        # Use CDP to take screenshot instead of Playwright's screenshot
        cdp = await page.context.new_cdp_session(page)
        result = await cdp.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        img_data = base64.b64decode(result["data"])
        path.write_bytes(img_data)
        await cdp.detach()
        print(f"Screenshot saved: {path}")
        return str(path)
    except Exception as e:
        print(f"CDP screenshot failed: {e}")
        try:
            await page.screenshot(path=str(path), full_page=False, timeout=15000, animations="disabled")
            print(f"Screenshot saved (viewport): {path}")
            return str(path)
        except Exception as e2:
            print(f"All screenshot methods failed: {e2}")
            return ""


async def wait_for_page_ready(page, timeout=20000):
    """Wait for the page to be reasonably ready."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        print("DOM content loaded")
    except Exception as e:
        print(f"DOM load timeout: {e}")

    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
        print("Network idle")
    except Exception:
        pass

    # Wait for body to exist
    for _ in range(10):
        try:
            body = await page.evaluate("typeof document.body !== 'undefined' && document.body !== null")
            if body:
                break
        except Exception:
            pass
        await asyncio.sleep(1)


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    print(f"CV found: {CV_PATH}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--font-render-hinting=none",
                "--disable-font-subpixel-positioning",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        # Block font loading to prevent timeouts
        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)

        page = await context.new_page()

        print(f"Navigating to: {APPLICATION_URL}")
        try:
            response = await page.goto(APPLICATION_URL, wait_until="commit", timeout=30000)
            print(f"Response status: {response.status if response else 'unknown'}")
        except Exception as e:
            print(f"Goto error: {e}")

        await wait_for_page_ready(page)
        await asyncio.sleep(5)  # Extra wait for JS to render

        url = page.url
        title = await page.title()
        print(f"URL: {url}")
        print(f"Title: {title}")

        # Get page text
        try:
            body_text = await page.evaluate("document.body ? document.body.innerText : 'NO BODY'")
            print(f"Body text preview: {body_text[:500]}")
        except Exception as e:
            print(f"Could not get body text: {e}")
            body_text = ""

        # Get all elements count
        try:
            elem_count = await page.evaluate("document.querySelectorAll('*').length")
            print(f"Total DOM elements: {elem_count}")
        except Exception:
            pass

        await safe_screenshot(page, "01-job-page")

        # Get page HTML for analysis
        try:
            html = await page.content()
            html_len = len(html)
            print(f"HTML length: {html_len}")
            # Save HTML for debugging
            debug_html = SCREENSHOTS_DIR / f"datenna-page-{ts()}.html"
            debug_html.write_text(html[:50000])
            print(f"HTML saved to: {debug_html}")
        except Exception as e:
            print(f"Could not get HTML: {e}")
            html = ""

        # Check if we need to click an Apply button
        apply_clicked = False
        if "apply" in html.lower() or "vacature" in html.lower():
            apply_selectors = [
                "a:has-text('Apply')",
                "button:has-text('Apply')",
                "a:has-text('Apply now')",
                "button:has-text('Apply now')",
                "a:has-text('Solliciteer')",
                "[data-qa*='apply']",
            ]
            for sel in apply_selectors:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        elem = page.locator(sel).first
                        if await elem.is_visible(timeout=2000):
                            text = await elem.inner_text()
                            print(f"Clicking apply: '{text}'")
                            await elem.click()
                            await asyncio.sleep(3)
                            apply_clicked = True
                            break
                except Exception:
                    pass

        if apply_clicked:
            await wait_for_page_ready(page)
            await safe_screenshot(page, "02-after-apply")
            print(f"URL after apply click: {page.url}")

        # Analyze form fields
        print("\n--- Form field analysis ---")
        inputs_info = await page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                return inputs.map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    autocomplete: el.autocomplete || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect ? {
                        x: el.getBoundingClientRect().x,
                        y: el.getBoundingClientRect().y,
                        w: el.getBoundingClientRect().width,
                        h: el.getBoundingClientRect().height
                    } : {}
                }));
            }
        """)

        visible_inputs = [i for i in inputs_info if i.get("visible") and i.get("rect", {}).get("w", 0) > 0]
        print(f"All inputs: {len(inputs_info)}, Visible: {len(visible_inputs)}")
        for inp in inputs_info:
            print(f"  {inp}")

        if len(inputs_info) == 0:
            print("NO FORM ELEMENTS FOUND - page may not have loaded properly")
            # Try waiting more
            print("Waiting additional 10 seconds...")
            await asyncio.sleep(10)
            inputs_info = await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                    return inputs.map(el => ({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        visible: el.offsetParent !== null
                    }));
                }
            """)
            print(f"After extra wait - inputs found: {len(inputs_info)}")
            for inp in inputs_info:
                print(f"  {inp}")

        await safe_screenshot(page, "03-form-analyzed")

        filled = []
        cv_uploaded = False

        async def js_fill(selector, value, desc):
            """Fill a field using JavaScript."""
            try:
                result = await page.evaluate(f"""
                    (value) => {{
                        const el = document.querySelector('{selector}');
                        if (!el) return 'NOT FOUND';
                        el.focus();
                        el.value = value;
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'OK: ' + el.value;
                    }}
                """, value)
                if result and result.startswith("OK"):
                    filled.append(desc)
                    print(f"  JS filled [{desc}]: {result}")
                    return True
                else:
                    print(f"  JS fill [{desc}]: {result}")
                    return False
            except Exception as e:
                print(f"  JS fill error [{desc}]: {e}")
                return False

        async def playwright_fill(locator, value, desc):
            try:
                elem = page.locator(locator).first
                if await elem.count() > 0 and await elem.is_visible(timeout=2000):
                    await elem.click(timeout=2000)
                    await asyncio.sleep(0.2)
                    await elem.fill(value, timeout=3000)
                    filled.append(desc)
                    print(f"  PW filled [{desc}]: {value}")
                    return True
            except Exception as e:
                pass
            return False

        # Try to fill each field
        # Name fields
        name_filled = False
        for loc in ["input[name='name']", "input[id='name']", "input[name='full_name']", "input[name='fullName']"]:
            if await playwright_fill(loc, APPLICANT["full_name"], "full_name"):
                name_filled = True
                break

        if not name_filled:
            # Try first + last separately
            for loc in ["input[name='first_name']", "input[name='firstName']", "input[id='first_name']"]:
                if await playwright_fill(loc, APPLICANT["first_name"], "first_name"):
                    break
            for loc in ["input[name='last_name']", "input[name='lastName']", "input[id='last_name']"]:
                if await playwright_fill(loc, APPLICANT["last_name"], "last_name"):
                    break

        # Email
        for loc in ["input[type='email']", "input[name='email']", "input[id='email']"]:
            if await playwright_fill(loc, APPLICANT["email"], "email"):
                break

        # Phone
        for loc in ["input[type='tel']", "input[name='phone']", "input[name='phone_number']", "input[id='phone']"]:
            if await playwright_fill(loc, APPLICANT["phone"], "phone"):
                break

        # LinkedIn
        for loc in ["input[name='linkedin']", "input[name='linkedin_url']", "input[id='linkedin']",
                    "input[placeholder*='LinkedIn' i]"]:
            if await playwright_fill(loc, APPLICANT["linkedin"], "linkedin"):
                break

        # Motivation textarea
        for loc in ["textarea", "textarea[name*='cover' i]", "textarea[name*='motivation' i]",
                    "textarea[name*='letter' i]"]:
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
        print(f"\nFile inputs found: {len(file_inputs)}")
        for i, fi in enumerate(file_inputs):
            try:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  Uploaded CV to file input {i}")
                await asyncio.sleep(2)
                break
            except Exception as e:
                print(f"  File input {i} error: {e}")

        # Checkboxes
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"\nCheckboxes: {len(checkboxes)}")
        for i, cb in enumerate(checkboxes):
            try:
                is_checked = await cb.is_checked()
                if not is_checked:
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Checkbox {i} error: {e}")

        await asyncio.sleep(1)

        # Scroll to bottom
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(page, "05-pre-submit")
        print("Pre-submit screenshot saved.")
        print(f"Fields filled: {filled}")
        print(f"CV uploaded: {cv_uploaded}")

        # Find submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send application')",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                count = await page.locator(sel).count()
                if count > 0:
                    elem = page.locator(sel).first
                    if await elem.is_visible(timeout=2000):
                        text = await elem.inner_text()
                        print(f"\nFound submit button: '{text}'")
                        await elem.click()
                        await asyncio.sleep(5)
                        submitted = True
                        print(f"Submitted! URL: {page.url}")
                        break
            except Exception as e:
                print(f"Submit selector {sel}: {e}")

        final_url = page.url
        await safe_screenshot(page, "06-post-submit")

        if submitted:
            try:
                body_text = await page.evaluate("document.body.innerText")
                print(f"Post-submit text: {body_text[:600]}")

                success_words = ["thank", "confirm", "success", "received", "submitted", "bedankt"]
                is_success = any(w in body_text.lower() for w in success_words)
                if is_success:
                    await safe_screenshot(page, "07-confirmation")
                    print("Application confirmed successful!")
                    status = "applied"
                    notes = "Successfully submitted to Datenna Python Engineer - Data Acquisition"
                else:
                    status = "applied"
                    notes = f"Submitted (confirmation unclear). URL: {final_url}"
            except Exception as e:
                status = "applied"
                notes = f"Submitted, could not verify: {e}"
        else:
            print("\nERROR: No submit button found/clicked")
            # List all buttons
            btns = await page.evaluate("""
                () => Array.from(document.querySelectorAll('button, input[type=submit], a'))
                    .filter(el => el.offsetParent !== null)
                    .map(el => ({tag: el.tagName, text: el.innerText || el.value, type: el.type}))
            """)
            print(f"Visible buttons/links: {btns[:20]}")
            status = "failed"
            notes = "Could not find submit button. Page may not have loaded properly."

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled_fields": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
