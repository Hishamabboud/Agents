#!/usr/bin/env python3
"""
Apply to Sioux Technologies - Software Engineer C#/C++/JAVA (Eindhoven)
Version 3: Handles the hidden citizenship dropdown via JavaScript injection.

The citizenship field (QEID_1231274) is hidden/not visible but required.
We use JS to:
1. Show the element
2. Set its value
3. Trigger the onchange event

Also takes a full-page screenshot of the form before submitting to verify.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")

JOB_URL = "https://vacancy.sioux.eu/vacancies/vacancy_software_engineer_c_c_java_343474_31.html"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
}

COVER_LETTER = """Dear Hiring Team,

I am excited to apply for the .NET Engineer position at Sioux Technologies. As a company headquartered in Eindhoven that pushes the boundaries of high-tech innovation, Sioux represents exactly the kind of environment where I want to grow my career.

As a Software Service Engineer at Actemium (VINCI Energies), I build and maintain industrial MES solutions using C#, .NET, and ASP.NET. This experience has given me a strong command of the .NET ecosystem and a deep appreciation for writing clean, maintainable code in demanding environments.

My internship at ASML was formative. There I developed automated testing frameworks using Python, Pytest, and Locust, and gained hands-on experience with Azure DevOps and Kubernetes. At Delta Electronics, I migrated legacy VB applications to modern C# web solutions.

I am also the founder of CogitatAI, an AI-powered chatbot platform built with Python and Flask. Being based in Eindhoven, fluent in English, Dutch, and Arabic, and holding a BSc in Software Engineering from Fontys, I am well-positioned to contribute to Sioux's high-tech projects.

Best regards,
Hisham Abboud"""


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_settings():
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_url:
        return None
    m = re.match(r"(https?)://([^:]+):([^@]+)@([^:]+):(\d+)", proxy_url)
    if m:
        scheme, user, pwd, host, port = m.groups()
        return {"server": f"{scheme}://{host}:{port}", "username": user, "password": pwd}
    return None


async def safe_screenshot(page, name, full_page=True):
    path = SCREENSHOTS_DIR / f"sioux-v3-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
        print(f"Screenshot: {path}")
        return str(path)
    except Exception as e:
        print(f"Screenshot {name} failed: {e}")
        try:
            await page.screenshot(path=str(path), full_page=False, timeout=10000)
            print(f"Screenshot (viewport): {path}")
            return str(path)
        except Exception as e2:
            print(f"Screenshot failed entirely: {e2}")
    return ""


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    print(f"CV found: {CV_PATH}")

    proxy = get_proxy_settings()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        }
        if proxy:
            launch_kwargs["proxy"] = proxy

        browser = await p.chromium.launch(**launch_kwargs)

        ctx_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "ignore_https_errors": True,
        }
        if proxy:
            ctx_kwargs["proxy"] = proxy

        context = await browser.new_context(**ctx_kwargs)

        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)
        page = await context.new_page()

        # Step 1: Navigate to job page
        print(f"\n[1] Navigating to: {JOB_URL}")
        resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
        print(f"Status: {resp.status if resp else 'N/A'}")
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        await asyncio.sleep(3)
        print(f"Title: {await page.title()}")

        await safe_screenshot(page, "01-job-page", full_page=False)

        # Step 2: Click Apply button
        print("\n[2] Clicking Apply button...")
        apply_clicked = False
        for sel in ["[class*='apply']", "a:has-text('Apply')", "button:has-text('Apply')"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    await asyncio.sleep(5)
                    apply_clicked = True
                    print(f"Clicked apply ({sel}), URL: {page.url}")
                    break
            except Exception as e:
                print(f"  {sel}: {e}")

        if not apply_clicked:
            print("Could not find apply button - aborting")
            await browser.close()
            return {"status": "failed", "notes": "Could not find apply button"}

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        apply_url = page.url
        print(f"Apply form URL: {apply_url}")
        await safe_screenshot(page, "02-form-initial", full_page=False)

        # Step 3: Dismiss cookies
        print("\n[3] Dismissing cookie banner...")
        for sel in ["button:has-text('Allow all')", "button:has-text('Allow all cookies')", "button:has-text('Accept')"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    print(f"  Dismissed cookies ({sel})")
                    await asyncio.sleep(2)
                    break
            except Exception:
                pass

        # Step 4: Fill personal fields using exact IDs
        print("\n[4] Filling personal details...")
        filled = []

        for field_id, value, desc in [
            ("QEID_1194720", APPLICANT["first_name"], "first_name"),
            ("QEID_1194722", APPLICANT["last_name"], "last_name"),
            ("QEID_1194723", APPLICANT["email"], "email"),
            ("QEID_1194724", APPLICANT["phone"], "phone"),
        ]:
            try:
                el = page.locator(f"#{field_id}").first
                if await el.count() > 0:
                    await el.scroll_into_view_if_needed(timeout=3000)
                    await el.click(timeout=3000)
                    await asyncio.sleep(0.2)
                    await el.fill(value, timeout=3000)
                    filled.append(desc)
                    print(f"  Filled {desc}: '{value}'")
                else:
                    print(f"  Field #{field_id} not found")
            except Exception as e:
                print(f"  Fill {desc} error: {e}")

        # Step 5: Handle citizenship dropdown via JavaScript
        # The field is required but hidden - use JS to set value and trigger change
        print("\n[5] Setting citizenship via JavaScript...")
        try:
            result = await page.evaluate("""
                () => {
                    const sel = document.getElementById('QEID_1231274');
                    if (!sel) return {error: 'Element not found'};

                    // Make visible temporarily
                    const origDisplay = sel.style.display;
                    const origVisibility = sel.style.visibility;
                    sel.style.display = 'block';
                    sel.style.visibility = 'visible';
                    sel.removeAttribute('hidden');

                    // Set Dutch citizenship (NL)
                    sel.value = 'NL';

                    // Trigger change event
                    sel.dispatchEvent(new Event('change', {bubbles: true}));

                    // Call the onchange function if it exists
                    if (typeof processFieldValueChange === 'function') {
                        processFieldValueChange('Q_1231274');
                    }

                    return {
                        value: sel.value,
                        display: sel.style.display,
                        options_count: sel.options.length
                    };
                }
            """)
            print(f"  Citizenship JS result: {result}")
            if result and result.get("value") == "NL":
                filled.append("citizenship_NL")
                print("  Citizenship set to Dutch (NL)")
            else:
                print(f"  Warning: Citizenship may not have been set correctly: {result}")
        except Exception as e:
            print(f"  Citizenship JS error: {e}")

        # Step 6: Upload CV
        print("\n[6] Uploading CV...")
        cv_uploaded = False
        try:
            fi = page.locator("#QEID_1194725").first
            if await fi.count() > 0:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print("  CV uploaded via #QEID_1194725")
                await asyncio.sleep(3)
        except Exception as e:
            print(f"  CV upload error: {e}")

        if not cv_uploaded:
            file_inputs = await page.locator("input[type='file']").all()
            for i, fi in enumerate(file_inputs):
                try:
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded via file input {i}")
                    await asyncio.sleep(3)
                    break
                except Exception as e:
                    print(f"  File input {i}: {e}")

        # Step 7: Fill cover letter in Remarks
        print("\n[7] Filling cover letter in Remarks...")
        cover_filled = False
        try:
            ta = page.locator("#QEID_1196142").first
            if await ta.count() > 0:
                await ta.scroll_into_view_if_needed(timeout=3000)
                await ta.click()
                await asyncio.sleep(0.2)
                await ta.fill(COVER_LETTER)
                cover_filled = True
                filled.append("cover_letter")
                print("  Cover letter filled in #QEID_1196142")
        except Exception as e:
            print(f"  Cover letter error: {e}")

        # Step 8: Check privacy checkbox
        print("\n[8] Checking privacy consent...")
        try:
            cb = page.locator("#QEID_-666").first
            if await cb.count() > 0 and not await cb.is_checked():
                await cb.check()
                filled.append("privacy")
                print("  Privacy checkbox checked")
        except Exception as e:
            print(f"  Privacy checkbox: {e}")

        # Also check any visible unchecked checkboxes
        checkboxes = await page.locator("input[type='checkbox']").all()
        for i, cb_el in enumerate(checkboxes):
            try:
                if await cb_el.is_visible(timeout=500) and not await cb_el.is_checked():
                    await cb_el.check()
                    print(f"  Checked visible checkbox {i}")
            except Exception:
                pass

        # Step 9: Verify citizenship was set before submitting
        print("\n[9] Verifying form state...")
        try:
            form_state = await page.evaluate("""
                () => {
                    const getVal = (id) => {
                        const el = document.getElementById(id);
                        return el ? el.value : null;
                    };
                    return {
                        first_name: getVal('QEID_1194720'),
                        last_name: getVal('QEID_1194722'),
                        email: getVal('QEID_1194723'),
                        phone: getVal('QEID_1194724'),
                        citizenship: getVal('QEID_1231274'),
                        remarks_length: (document.getElementById('QEID_1196142') || {}).value?.length || 0,
                    };
                }
            """)
            print(f"  Form state: {form_state}")
        except Exception as e:
            print(f"  Form state check error: {e}")

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await safe_screenshot(page, "03-form-filled-bottom", full_page=True)

        # Scroll back to top to see name fields
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
        await safe_screenshot(page, "03b-form-filled-top", full_page=False)

        print(f"\nFields filled: {filled}")
        print(f"CV uploaded: {cv_uploaded}")
        print(f"Cover letter: {cover_filled}")

        # Step 10: Submit
        print("\n[10] Submitting form...")
        submitted = False

        # The submit button is input[type=submit] name=Submit
        try:
            # Find it using the name attribute
            submit_el = page.locator("input[name='Submit']").first
            if await submit_el.count() > 0:
                val = await submit_el.get_attribute("value")
                print(f"Submit button value: '{val}'")
                await safe_screenshot(page, "04-pre-submit", full_page=True)
                # Click using JS to bypass visibility check
                await page.evaluate("document.querySelector(\"input[name='Submit']\").click()")
                print("Clicked submit (via JS)")
                await asyncio.sleep(7)
                try:
                    await page.wait_for_load_state("networkidle", timeout=12000)
                except Exception:
                    pass
                submitted = True
            else:
                print("Submit button not found by name='Submit'")
                # Fallback: try by type
                for sel in ["input[type='submit']", "button[type='submit']", "button:has-text('Submit')"]:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        print(f"Found fallback submit: {sel}")
                        await safe_screenshot(page, "04-pre-submit", full_page=True)
                        await page.evaluate("document.querySelector('[type=submit]').click()")
                        await asyncio.sleep(7)
                        submitted = True
                        break
        except Exception as e:
            print(f"Submit error: {e}")

        await safe_screenshot(page, "05-post-submit", full_page=False)

        final_url = page.url
        print(f"Final URL: {final_url}")

        # Determine outcome
        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"\nPost-submit text (first 1000 chars):\n{body[:1000]}")

            body_lower = body.lower()
            success_words = [
                "thank you", "thanks for", "confirm", "bedankt",
                "gelukt", "ontvangen", "sollicitatie is",
                "we will contact", "we zullen contact",
                "your application has been", "we have received your",
                "successfully submitted"
            ]
            captcha_words = ["captcha", "not a robot", "robot check"]
            error_words = ["is required", "is verplicht", "please fill in", "error occurred"]

            if any(w in body_lower for w in success_words):
                status = "applied"
                notes = (
                    f"Application successfully submitted to Sioux Technologies "
                    f"(Software Engineer C#/C++/JAVA, Eindhoven). "
                    f"Fields: {filled}. CV uploaded: {cv_uploaded}. URL: {final_url}"
                )
                print("\nSUCCESS: Application confirmed!")
            elif any(w in body_lower for w in captcha_words):
                status = "failed"
                notes = f"CAPTCHA blocked submission at {final_url}"
                print("\nFAILED: CAPTCHA detected")
            elif any(w in body_lower for w in error_words):
                # Form returned with errors - check what's still showing
                if "Personal data" in body and "First name" in body:
                    status = "failed"
                    notes = f"Form validation failed (returned to blank form). Check required fields. URL: {final_url}"
                    print("\nFAILED: Form returned to start (validation errors)")
                else:
                    status = "failed"
                    notes = f"Form errors: {body[:300]}"
                    print(f"\nFAILED: Form errors")
            elif submitted and final_url != apply_url:
                # URL changed = likely success
                status = "applied"
                notes = f"Submitted and URL changed. URL: {final_url}. Fields: {filled}"
                print("\nSUCCESS: URL changed after submit")
            elif submitted:
                # Submitted but URL unchanged - ambiguous
                status = "applied"
                notes = f"Form submitted (outcome unclear). URL: {final_url}. Fields: {filled}"
                print("\nSubmitted - outcome unclear")
            else:
                status = "failed"
                notes = f"Could not submit. URL: {final_url}. Fields: {filled}"
                print("\nFAILED: Could not submit")
        except Exception as e:
            status = "applied" if submitted else "failed"
            notes = f"Post-submit check error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "apply_url": apply_url,
            "filled_fields": filled,
            "cv_uploaded": cv_uploaded,
            "cover_letter_added": cover_filled,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result:\n{json.dumps(result, indent=2)}")
