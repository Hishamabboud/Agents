#!/usr/bin/env python3
"""
Apply to Sioux Technologies - Software Engineer C#/C++/JAVA (Eindhoven)
Version 2: Uses exact field IDs discovered from form analysis.

Field mapping (from inspection):
  QEID_1194720 = First name
  QEID_1194721 = Insertion (tussenvoegsel)
  QEID_1194722 = Last name
  QEID_1194723 = E-Mail
  QEID_1194724 = Phone number
  QEID_1231274 = Citizenship (select)
  QEID_1231275 = Second citizenship (optional)
  QEID_1194725 (file) = CV upload
  QEID_1194769_NEW (file) = Motivation upload (second file input)
  QEID_1196142 (textarea) = Remarks
  QEID_-666 (checkbox) = Privacy/consent checkbox
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
COVER_LETTER_PATH = Path("/home/user/Agents/output/cover-letters/sioux-technologies-net-engineer.md")

JOB_URL = "https://vacancy.sioux.eu/vacancies/vacancy_software_engineer_c_c_java_343474_31.html"
APPLY_URL = "https://vacancy.sioux.eu/index.php/page/applicants/command/applyforjob/vid/343474/bb/1"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    # Citizenship - Syrian (Syria) with Dutch citizenship
    "citizenship": "Netherlands",
}

COVER_LETTER = """Dear Hiring Team,

I am excited to apply for the .NET Engineer position at Sioux Technologies. As a company headquartered in Eindhoven that pushes the boundaries of high-tech innovation, Sioux represents exactly the kind of environment where I want to grow my career — solving challenging technical problems alongside talented engineers.

As a Software Service Engineer at Actemium (VINCI Energies), I build and maintain industrial MES solutions using C#, .NET, and ASP.NET. This experience has given me a strong command of the .NET ecosystem and a deep appreciation for writing clean, maintainable code in demanding environments. My work with React on frontend components also aligns with Sioux's technology stack, and I am comfortable working across the full application layer.

My internship at ASML — another pillar of the Eindhoven high-tech ecosystem — was formative. There I developed automated testing frameworks using Python, Pytest, and Locust, and gained hands-on experience with Azure DevOps and Kubernetes. Working at ASML taught me the rigor and quality standards expected in high-tech, and I carry those standards into every project. At Delta Electronics, I migrated legacy VB applications to modern C# web solutions, demonstrating my ability to modernize codebases while preserving business logic.

I am also the founder of CogitatAI, an AI-powered chatbot platform built with Python and Flask, which reflects my entrepreneurial mindset and ability to deliver products end-to-end. I thrive when given ownership and the freedom to innovate — qualities I believe are valued at Sioux.

Being based in Eindhoven, fluent in English, Dutch, and Arabic, and holding a BSc in Software Engineering from Fontys, I am well-positioned to integrate into your team quickly. I am genuinely enthusiastic about contributing to Sioux's high-tech projects and would welcome the chance to discuss how my skills and drive can add value.

I am available to meet at your convenience and look forward to the conversation.

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


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"sioux-{name}-{ts()}.png"
    for full_page in [False, True]:
        try:
            await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
            print(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            print(f"Screenshot {name} failed (full_page={full_page}): {e}")
    return ""


async def fill_by_id(page, element_id, value, desc):
    """Fill a field by its ID."""
    sel = f"#{element_id}"
    try:
        el = page.locator(sel).first
        if await el.count() > 0:
            try:
                await el.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass
            await el.click(timeout=3000)
            await asyncio.sleep(0.2)
            await el.fill(value, timeout=3000)
            print(f"  Filled [{desc}] (#{element_id}): '{value}'")
            return True
        else:
            print(f"  Element #{element_id} not found")
    except Exception as e:
        print(f"  Fill #{element_id} error: {e}")
    return False


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
                "--font-render-hinting=none",
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

        # Step 1: Navigate to the job listing page
        print(f"\n[1] Navigating to job listing: {JOB_URL}")
        try:
            resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Navigation warning: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(3)
        title = await page.title()
        print(f"Title: {title}")
        print(f"URL: {page.url}")

        await safe_screenshot(page, "01-job-listing")

        # Step 2: Click the "Apply now" button
        print("\n[2] Looking for Apply Now button...")
        apply_clicked = False

        apply_selectors = [
            "[class*='apply']",
            "a:has-text('Apply now')",
            "a:has-text('Solliciteer')",
            "button:has-text('Apply now')",
            "button:has-text('Solliciteer')",
            "a[href*='applyforjob']",
            ".apply-btn",
            "#applyBtn",
        ]

        for sel in apply_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Found apply button: '{text}' ({sel})")
                    await el.click()
                    await asyncio.sleep(5)
                    apply_clicked = True
                    print(f"URL after click: {page.url}")
                    break
                elif await el.count() > 0:
                    print(f"  Found {sel} but not visible, trying JS click...")
                    await page.evaluate(f"document.querySelector('{sel}').click()")
                    await asyncio.sleep(5)
                    apply_clicked = True
                    break
            except Exception as e:
                print(f"  Selector {sel}: {e}")

        if not apply_clicked:
            print(f"\n  Trying direct navigation to apply URL: {APPLY_URL}")
            try:
                resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
                print(f"Status: {resp.status if resp else 'N/A'}")
                await asyncio.sleep(5)
                apply_clicked = True
            except Exception as e:
                print(f"Direct apply URL failed: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        current_url = page.url
        title = await page.title()
        print(f"After apply - Title: {title}")
        print(f"After apply - URL: {current_url}")

        await safe_screenshot(page, "02-apply-form-loaded")

        # Step 3: Handle cookie banner if present
        print("\n[3] Handling cookie banner...")
        cookie_sels = [
            "button:has-text('Allow all')",
            "button:has-text('Allow all cookies')",
            "button:has-text('Accept')",
            "button:has-text('Accepteer')",
            "#acceptCookies",
        ]
        for sel in cookie_sels:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    print(f"  Dismissed cookie banner ({sel})")
                    await asyncio.sleep(2)
                    break
            except Exception:
                pass

        # Step 4: Fill form fields using exact IDs
        print("\n[4] Filling personal information...")
        filled = []

        # First name: QEID_1194720
        if await fill_by_id(page, "QEID_1194720", APPLICANT["first_name"], "first_name"):
            filled.append("first_name")

        # Insertion (tussenvoegsel): QEID_1194721 - leave blank
        print(f"  Leaving insertion blank")

        # Last name: QEID_1194722
        if await fill_by_id(page, "QEID_1194722", APPLICANT["last_name"], "last_name"):
            filled.append("last_name")

        # Email: QEID_1194723
        if await fill_by_id(page, "QEID_1194723", APPLICANT["email"], "email"):
            filled.append("email")

        # Phone: QEID_1194724
        if await fill_by_id(page, "QEID_1194724", APPLICANT["phone"], "phone"):
            filled.append("phone")

        # Citizenship select: QEID_1231274
        print("\n[5] Setting citizenship dropdown...")
        try:
            # First scroll to make it visible/accessible
            try:
                await page.evaluate("document.getElementById('QEID_1231274').scrollIntoView()")
                await asyncio.sleep(0.5)
            except Exception:
                pass

            # Get available options
            options = await page.evaluate("""
                () => {
                    const sel = document.getElementById('QEID_1231274');
                    if (!sel) return [];
                    return Array.from(sel.options).map(o => ({value: o.value, text: o.text}));
                }
            """)
            print(f"  Citizenship options: {options}")

            # Try to select Netherlands
            dutch_option = None
            for opt in options:
                if "nether" in opt["text"].lower() or "dutch" in opt["text"].lower() or "nl" in opt["value"].lower():
                    dutch_option = opt["value"]
                    break

            if dutch_option:
                await page.select_option("#QEID_1231274", value=dutch_option)
                print(f"  Selected citizenship: {dutch_option}")
                filled.append("citizenship")
            elif options and len(options) > 1:
                # Pick the first non-empty option
                for opt in options:
                    if opt["value"] and opt["value"] != "---":
                        await page.select_option("#QEID_1231274", value=opt["value"])
                        print(f"  Selected citizenship (fallback): {opt['text']}")
                        filled.append("citizenship")
                        break
        except Exception as e:
            print(f"  Citizenship select error: {e}")

        # Step 5: Upload CV (QEID_1194725)
        print("\n[6] Uploading CV...")
        cv_uploaded = False
        try:
            fi = page.locator("#QEID_1194725")
            if await fi.count() > 0:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  CV uploaded to QEID_1194725")
                await asyncio.sleep(3)
        except Exception as e:
            print(f"  CV upload error: {e}")

        if not cv_uploaded:
            # Fallback: try all file inputs
            file_inputs = await page.locator("input[type='file']").all()
            print(f"  Fallback: trying {len(file_inputs)} file inputs")
            for i, fi in enumerate(file_inputs):
                try:
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded to file input {i}")
                    await asyncio.sleep(3)
                    break
                except Exception as e:
                    print(f"  File input {i}: {e}")

        # Step 6: Remarks/Cover letter (QEID_1196142)
        print("\n[7] Adding cover letter to remarks field...")
        cover_filled = False
        try:
            ta = page.locator("#QEID_1196142")
            if await ta.count() > 0:
                await ta.scroll_into_view_if_needed(timeout=3000)
                await ta.click()
                await asyncio.sleep(0.2)
                await ta.fill(COVER_LETTER)
                cover_filled = True
                filled.append("cover_letter_remarks")
                print(f"  Cover letter filled in QEID_1196142 (Remarks)")
        except Exception as e:
            print(f"  Remarks fill error: {e}")

        # Also try motivation upload field (second file input QEID_1194769_NEW)
        # We'll skip this as it's for a separate file upload

        # Step 7: Privacy checkbox (QEID_-666)
        print("\n[8] Handling privacy checkbox...")
        try:
            cb = page.locator("#QEID_-666")
            if await cb.count() > 0:
                if not await cb.is_checked():
                    await cb.check()
                    print("  Checked privacy checkbox QEID_-666")
                    filled.append("privacy_checkbox")
                else:
                    print("  Privacy checkbox already checked")
        except Exception as e:
            print(f"  Privacy checkbox error: {e}")

        # Also check any other unchecked checkboxes
        checkboxes = await page.locator("input[type='checkbox']:visible").all()
        for i, cb_el in enumerate(checkboxes):
            try:
                if not await cb_el.is_checked():
                    cb_id = await cb_el.get_attribute("id")
                    await cb_el.check()
                    print(f"  Checked checkbox {i} (id={cb_id})")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll to bottom
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(page, "03-form-filled")

        print(f"\nFilled fields: {filled}")
        print(f"CV uploaded: {cv_uploaded}")
        print(f"Cover letter: {cover_filled}")

        # Step 8: Submit
        print("\n[9] Submitting form...")
        submitted = False

        # Try input[type='submit'] first (we saw it in the form elements)
        submit_sels = [
            "input[type='submit'][name='Submit']",
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "button:has-text('Solliciteer')",
            "button:has-text('Verstuur')",
            "[type='submit']",
        ]

        for sel in submit_sels:
            try:
                el = page.locator(sel).first
                count = await el.count()
                if count == 0:
                    continue
                try:
                    visible = await el.is_visible(timeout=2000)
                except Exception:
                    visible = False

                if not visible:
                    # Try scrolling the submit button into view
                    try:
                        await page.evaluate("document.querySelector('[type=submit]').scrollIntoView()")
                        await asyncio.sleep(0.5)
                        visible = await el.is_visible(timeout=2000)
                    except Exception:
                        pass

                try:
                    text = await el.inner_text()
                except Exception:
                    text = (await el.get_attribute("value")) or sel
                print(f"Found submit element: '{text}' ({sel})")
                await safe_screenshot(page, "04-pre-submit")
                try:
                    await el.click(timeout=5000)
                except Exception:
                    # JS click fallback
                    await page.evaluate("document.querySelector('[type=submit]').click()")
                print("Clicked submit")
                await asyncio.sleep(6)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                submitted = True
                break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        await safe_screenshot(page, "05-post-submit")
        final_url = page.url

        # Determine outcome
        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"\nPost-submit text (first 800 chars):\n{body[:800]}")

            success_words = [
                "thank", "confirm", "success", "received", "bedankt",
                "application", "gelukt", "ontvangen", "sollicitatie",
                "we will contact", "we zullen", "successfully submitted",
                "your application has", "we have received"
            ]
            captcha_words = ["captcha", "robot", "verify human", "not a robot"]
            error_words = ["error", "required", "verplicht", "please fill", "invalid"]

            body_lower = body.lower()

            if any(w in body_lower for w in success_words):
                status = "applied"
                notes = f"Application submitted to Sioux Technologies Software Engineer C#/C++/JAVA. Final URL: {final_url}. Filled: {filled}"
                print("\nSUCCESS: Application confirmed!")
            elif any(w in body_lower for w in captcha_words):
                status = "failed"
                notes = f"CAPTCHA blocked the application at {final_url}"
                print("\nFAILED: CAPTCHA detected")
            elif any(w in body_lower for w in error_words):
                status = "failed"
                notes = f"Form validation errors. URL: {final_url}. Text: {body[:300]}"
                print(f"\nFAILED: Form errors detected")
            elif submitted:
                status = "applied"
                notes = f"Form submitted (confirmation ambiguous). URL: {final_url}. Filled: {filled}"
                print("\nSubmitted - outcome unclear")
            else:
                status = "failed"
                notes = f"Could not submit. URL: {final_url}. Filled: {filled}"
                print("\nFAILED: Could not submit")
        except Exception as e:
            status = "applied" if submitted else "failed"
            notes = f"Post-submit error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled_fields": filled,
            "cv_uploaded": cv_uploaded,
            "cover_letter_added": cover_filled,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result:\n{json.dumps(result, indent=2)}")
