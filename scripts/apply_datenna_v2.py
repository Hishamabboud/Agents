#!/usr/bin/env python3
"""
Apply to Datenna Python Engineer - Data Acquisition role.
Uses Playwright to navigate and fill the application form.
Version 2: handles font loading timeout, uses clip screenshot.
"""

import asyncio
import json
import os
import re
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


async def screenshot(page, name, full_page=True):
    path = SCREENSHOTS_DIR / f"datenna-{name}-{ts()}.png"
    try:
        await page.screenshot(
            path=str(path),
            full_page=full_page,
            timeout=10000,
        )
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed for {name}: {e}")
        # Try without full_page
        try:
            await page.screenshot(
                path=str(path),
                full_page=False,
                timeout=10000,
            )
            print(f"Screenshot (viewport) saved: {path}")
        except Exception as e2:
            print(f"Screenshot completely failed: {e2}")
    return str(path)


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    print(f"CV found at: {CV_PATH}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--font-render-hinting=none",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Block fonts to avoid loading issues
        await page.route("**/*.woff", lambda route: route.abort())
        await page.route("**/*.woff2", lambda route: route.abort())
        await page.route("**/*.ttf", lambda route: route.abort())

        print(f"Navigating to {APPLICATION_URL}")
        try:
            await page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation warning: {e}")

        await asyncio.sleep(3)

        print(f"Current URL: {page.url}")
        title = await page.title()
        print(f"Page title: {title}")

        await screenshot(page, "01-job-page")

        # Get page content to understand structure
        content = await page.content()
        # Look for form or apply button indicators
        has_form = "<form" in content.lower()
        has_apply_btn = "apply" in content.lower()
        print(f"Has form: {has_form}, Has apply text: {has_apply_btn}")

        # Try to find and click Apply button
        apply_clicked = False
        apply_selectors = [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply now')",
            "button:has-text('Apply now')",
            "[data-qa*='apply']",
            "[class*='apply']",
            "a[href*='apply']",
        ]

        for sel in apply_selectors:
            try:
                elems = await page.locator(sel).all()
                for elem in elems:
                    if await elem.is_visible(timeout=2000):
                        text = await elem.inner_text()
                        print(f"Found apply element: '{text}' with selector: {sel}")
                        await elem.click()
                        await asyncio.sleep(2)
                        apply_clicked = True
                        break
                if apply_clicked:
                    break
            except Exception as e:
                pass

        if apply_clicked:
            print(f"Clicked apply, URL: {page.url}")
            await screenshot(page, "02-after-apply-click")
        else:
            print("No apply button found or already on form page")
            await screenshot(page, "02-no-apply-button")

        await asyncio.sleep(2)

        # Get all form elements
        print("\n--- Analyzing form elements ---")
        all_inputs = await page.locator("input, textarea, select").all()
        print(f"Total form elements: {len(all_inputs)}")

        form_map = {}
        for inp in all_inputs:
            try:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                itype = await inp.get_attribute("type") or "text"
                name = await inp.get_attribute("name") or ""
                placeholder = await inp.get_attribute("placeholder") or ""
                inp_id = await inp.get_attribute("id") or ""
                autocomplete = await inp.get_attribute("autocomplete") or ""
                aria_label = await inp.get_attribute("aria-label") or ""
                is_visible = await inp.is_visible()
                print(f"  [{tag}][{itype}] name='{name}' id='{inp_id}' placeholder='{placeholder}' autocomplete='{autocomplete}' aria='{aria_label}' visible={is_visible}")
                if is_visible:
                    form_map[name or inp_id or placeholder] = {
                        "tag": tag,
                        "type": itype,
                        "name": name,
                        "id": inp_id,
                        "placeholder": placeholder,
                    }
            except Exception as e:
                pass

        print(f"\nVisible form fields: {list(form_map.keys())}")
        print("--- End form analysis ---\n")

        # Now fill the form intelligently
        filled = []

        async def fill_by_selectors(selectors, value, desc):
            for sel in selectors:
                try:
                    elem = page.locator(sel).first
                    visible = await elem.is_visible(timeout=1500)
                    if visible:
                        await elem.click()
                        await asyncio.sleep(0.3)
                        await elem.fill(value)
                        filled.append(desc)
                        print(f"  Filled [{desc}]: '{value}'")
                        return True
                except Exception:
                    pass
            print(f"  Could not fill [{desc}]")
            return False

        # Full name
        await fill_by_selectors(
            [
                "input[name='name']",
                "input[name='full_name']",
                "input[name='fullName']",
                "input[id='name']",
                "input[placeholder*='name' i]",
                "input[placeholder*='naam' i]",
                "input[autocomplete='name']",
            ],
            APPLICANT["full_name"],
            "full_name",
        )

        # First name
        await fill_by_selectors(
            [
                "input[name='first_name']",
                "input[name='firstName']",
                "input[name='firstname']",
                "input[id='first_name']",
                "input[id='firstName']",
                "input[placeholder*='First name' i]",
                "input[placeholder*='Voornaam' i]",
                "input[autocomplete='given-name']",
            ],
            APPLICANT["first_name"],
            "first_name",
        )

        # Last name
        await fill_by_selectors(
            [
                "input[name='last_name']",
                "input[name='lastName']",
                "input[name='lastname']",
                "input[id='last_name']",
                "input[id='lastName']",
                "input[placeholder*='Last name' i]",
                "input[placeholder*='Achternaam' i]",
                "input[autocomplete='family-name']",
            ],
            APPLICANT["last_name"],
            "last_name",
        )

        # Email
        await fill_by_selectors(
            [
                "input[type='email']",
                "input[name*='email' i]",
                "input[id*='email' i]",
                "input[placeholder*='email' i]",
                "input[autocomplete='email']",
            ],
            APPLICANT["email"],
            "email",
        )

        # Phone
        await fill_by_selectors(
            [
                "input[type='tel']",
                "input[name*='phone' i]",
                "input[name*='Phone' i]",
                "input[id*='phone' i]",
                "input[placeholder*='phone' i]",
                "input[placeholder*='Phone' i]",
                "input[placeholder*='telefoon' i]",
                "input[autocomplete='tel']",
            ],
            APPLICANT["phone"],
            "phone",
        )

        # LinkedIn
        await fill_by_selectors(
            [
                "input[name*='linkedin' i]",
                "input[id*='linkedin' i]",
                "input[placeholder*='linkedin' i]",
                "input[placeholder*='LinkedIn' i]",
            ],
            APPLICANT["linkedin"],
            "linkedin",
        )

        # City/Location
        await fill_by_selectors(
            [
                "input[name*='city' i]",
                "input[name*='location' i]",
                "input[id*='city' i]",
                "input[placeholder*='city' i]",
                "input[placeholder*='City' i]",
                "input[placeholder*='stad' i]",
            ],
            APPLICANT["city"],
            "city",
        )

        # Cover letter / motivation textarea
        textareas = await page.locator("textarea").all()
        for ta in textareas:
            try:
                if await ta.is_visible(timeout=1500):
                    await ta.click()
                    await asyncio.sleep(0.3)
                    await ta.fill(MOTIVATION)
                    filled.append("motivation")
                    print(f"  Filled motivation textarea")
                    break
            except Exception:
                pass

        await asyncio.sleep(1)
        await screenshot(page, "03-fields-filled")

        # Upload CV
        cv_uploaded = False
        file_inputs = await page.locator("input[type='file']").all()
        print(f"\nFound {len(file_inputs)} file inputs")
        for i, fi in enumerate(file_inputs):
            try:
                name = await fi.get_attribute("name") or ""
                accept = await fi.get_attribute("accept") or ""
                print(f"  File input {i}: name={name} accept={accept}")
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  Uploaded CV to file input {i}")
                await asyncio.sleep(2)
                break
            except Exception as e:
                print(f"  Error uploading to file input {i}: {e}")

        if not cv_uploaded:
            # Try looking for upload buttons/labels
            print("  Trying alternative upload methods...")
            upload_labels = await page.locator("label[for], [class*='upload'], [class*='file']").all()
            for lbl in upload_labels:
                try:
                    text = await lbl.inner_text()
                    if any(word in text.lower() for word in ["cv", "resume", "upload", "file"]):
                        print(f"  Found upload label: '{text}'")
                        # Click it to open file dialog — won't work headless, skip
                except Exception:
                    pass

        await asyncio.sleep(1)
        await screenshot(page, "04-cv-uploaded")

        # Handle checkboxes
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"\nFound {len(checkboxes)} checkboxes")
        for i, cb in enumerate(checkboxes):
            try:
                is_checked = await cb.is_checked()
                cb_id = await cb.get_attribute("id") or ""
                cb_name = await cb.get_attribute("name") or ""
                print(f"  Checkbox {i}: id={cb_id} name={cb_name} checked={is_checked}")
                if not is_checked:
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Checkbox {i} error: {e}")

        # Handle country select if present
        selects = await page.locator("select").all()
        for sel_elem in selects:
            try:
                name = await sel_elem.get_attribute("name") or ""
                sel_id = await sel_elem.get_attribute("id") or ""
                if "country" in name.lower() or "country" in sel_id.lower():
                    await sel_elem.select_option(label="Netherlands")
                    print("  Selected country: Netherlands")
            except Exception:
                pass

        await asyncio.sleep(1)
        await screenshot(page, "05-pre-submit")
        print("\nPre-submit screenshot saved.")

        # Scroll to bottom to see full form
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await screenshot(page, "05b-pre-submit-bottom")

        # Find submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Verstuur')",
            "button:has-text('Verzenden')",
            "button:has-text('Send application')",
            "[class*='submit']",
            "[data-qa*='submit']",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    btn_text = await elem.inner_text()
                    print(f"\nFound submit button: '{btn_text}' ({sel})")
                    await elem.click()
                    await asyncio.sleep(4)
                    submitted = True
                    print(f"After submit URL: {page.url}")
                    break
            except Exception as e:
                pass

        if not submitted:
            # Try scrolling to find submit button
            print("Submit button not found, scrolling to find it...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            for sel in submit_selectors:
                try:
                    elem = page.locator(sel).first
                    if await elem.is_visible(timeout=2000):
                        btn_text = await elem.inner_text()
                        print(f"Found submit button after scroll: '{btn_text}'")
                        await elem.click()
                        await asyncio.sleep(4)
                        submitted = True
                        break
                except Exception:
                    pass

        final_url = page.url
        await screenshot(page, "06-after-submit")

        if submitted:
            body_text = await page.evaluate("document.body.innerText")
            print(f"\nPage text after submit: {body_text[:800]}")

            success_indicators = [
                "thank", "confirm", "success", "received", "application submitted",
                "bedankt", "ontvangen", "verstuurd", "we have received",
            ]
            lower_text = body_text.lower()
            is_success = any(ind in lower_text for ind in success_indicators)

            if is_success:
                await screenshot(page, "07-confirmation")
                print("\nApplication submitted successfully!")
                status = "applied"
                notes = "Successfully submitted application to Datenna Python Engineer - Data Acquisition"
            else:
                print("\nSubmitted but could not confirm success. Check screenshot.")
                status = "applied"
                notes = f"Form submitted; confirmation state unclear. URL: {final_url}"
        else:
            print("\nERROR: Could not find or click submit button")
            # Print buttons on page for debug
            buttons = await page.locator("button, input[type='submit']").all()
            print(f"Buttons on page: {len(buttons)}")
            for btn in buttons:
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type") or ""
                    vis = await btn.is_visible()
                    print(f"  button text='{text}' type={btype} visible={vis}")
                except Exception:
                    pass
            status = "failed"
            notes = "Could not find submit button on application form"

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
    print(f"\nResult: {json.dumps(result, indent=2)}")
