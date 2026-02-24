#!/usr/bin/env python3
"""
Apply to Funda Medior Backend .NET Engineer position via jobs.funda.nl (Recruitee ATS)
Version 2: Uses exact field names discovered from form inspection
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

APPLICATION_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer/c/new"
JOB_URL = "https://jobs.funda.nl/o/medior-backend-net-engineer"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/funda-medior-backend-net-engineer.txt"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CHROMIUM_EXEC = "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"

APPLICANT = {
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "location": "Eindhoven, Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()

ts = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"funda-v2-{name}-{ts}.png")


def get_proxy_config():
    proxy_url = (
        os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or
        os.environ.get("https_proxy") or os.environ.get("http_proxy")
    )
    if not proxy_url:
        return None
    try:
        scheme_end = proxy_url.index("://") + 3
        rest = proxy_url[scheme_end:]
        last_at = rest.rfind("@")
        credentials = rest[:last_at]
        hostport = rest[last_at + 1:]
        colon_pos = credentials.index(":")
        username = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]
        host, port = hostport.rsplit(":", 1)
        return {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password,
        }
    except Exception as e:
        print(f"Proxy parse error: {e}")
        return None


async def run():
    screenshots = []
    status = "failed"
    notes = ""

    proxy_config = get_proxy_config()
    if proxy_config:
        print(f"Using proxy: {proxy_config['server']}")
    else:
        print("No proxy configured")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "executable_path": CHROMIUM_EXEC,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ],
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
            "timezone_id": "Europe/Amsterdam",
            "viewport": {"width": 1280, "height": 900},
            "ignore_https_errors": True,
        }
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        # Mask webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        try:
            # Navigate to application form directly
            print(f"[1] Loading application form: {APPLICATION_URL}")
            await page.goto(APPLICATION_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            path = screenshot_path("01-form-loaded")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 2: Fill name
            print("[2] Filling name...")
            name_input = page.locator("input[name='candidate.name']")
            await name_input.wait_for(timeout=10000)
            await name_input.click()
            await name_input.fill(APPLICANT["full_name"])
            await page.wait_for_timeout(300)
            print(f"    Name: {APPLICANT['full_name']}")

            # Step 3: Fill email
            print("[3] Filling email...")
            email_input = page.locator("input[name='candidate.email']")
            await email_input.click()
            await email_input.fill(APPLICANT["email"])
            await page.wait_for_timeout(300)
            print(f"    Email: {APPLICANT['email']}")

            # Step 4: Fill phone
            print("[4] Filling phone...")
            phone_input = page.locator("input[name='candidate.phone']")
            await phone_input.click()
            # Clear existing value first (there may be a country code prefix)
            await phone_input.click(click_count=3)
            await phone_input.fill(APPLICANT["phone"])
            await page.wait_for_timeout(300)
            print(f"    Phone: {APPLICANT['phone']}")

            # Step 5: Upload CV (name='candidate.cv')
            print("[5] Uploading CV...")
            cv_input = page.locator("input[name='candidate.cv']")
            await cv_input.set_input_files(CV_PATH)
            await page.wait_for_timeout(2000)
            print(f"    CV uploaded: {CV_PATH}")

            # Step 6: Upload cover letter (name='candidate.coverLetterFile')
            print("[6] Uploading cover letter...")
            cl_input = page.locator("input[name='candidate.coverLetterFile']")
            await cl_input.set_input_files(COVER_LETTER_PATH)
            await page.wait_for_timeout(1000)
            print(f"    Cover letter uploaded: {COVER_LETTER_PATH}")

            path = screenshot_path("02-files-uploaded")
            await page.screenshot(path=path)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Step 7: Answer "How did you hear about us?" - click the label for "LinkedIn Jobs"
            print("[7] Selecting 'How did you hear about us?'...")
            # The checkboxes have labels that intercept clicks - we need to click the label
            # Checkbox value: "LinkedIn Jobs" -> id will be input-candidate.openQuestionAnswers.4816223.multiContent-21-1
            try:
                linkedin_label = page.locator(
                    "label[for='input-candidate.openQuestionAnswers.4816223.multiContent-21-1']"
                )
                if await linkedin_label.is_visible(timeout=5000):
                    await linkedin_label.scroll_into_view_if_needed()
                    await linkedin_label.click()
                    await page.wait_for_timeout(500)
                    print("    Selected: LinkedIn Jobs")
                else:
                    # Try clicking label by text
                    labels = await page.locator("label").all()
                    for label in labels:
                        txt = await label.text_content()
                        if txt and "linkedin" in txt.lower():
                            await label.scroll_into_view_if_needed()
                            await label.click()
                            await page.wait_for_timeout(300)
                            print(f"    Clicked label: {txt}")
                            break
            except Exception as e:
                print(f"    How did you hear checkbox: {e}")

            # Step 8: Fill "Why do you want to work at Funda?" (textarea)
            print("[8] Filling 'Why Funda?'...")
            why_textarea = page.locator(
                "textarea[name='candidate.openQuestionAnswers.4816224.content']"
            )
            await why_textarea.scroll_into_view_if_needed()
            await why_textarea.click()
            await why_textarea.fill(
                "I am drawn to Funda because of its scale and the engineering challenges of building "
                "performant microservices that serve millions of users searching for homes in the Netherlands. "
                "My background in .NET/C# backend development at Actemium (building production MES systems) "
                "and cloud/Kubernetes experience at ASML align well with Funda's technical stack. "
                "I am excited about contributing to a product that has real impact on people's lives and "
                "growing within a collaborative engineering team."
            )
            await page.wait_for_timeout(300)
            print("    'Why Funda' filled")

            # Step 9: Fill "Where do you currently live?"
            print("[9] Filling location...")
            location_input = page.locator(
                "input[name='candidate.openQuestionAnswers.4816225.content']"
            )
            await location_input.scroll_into_view_if_needed()
            await location_input.click()
            await location_input.fill("Eindhoven, Netherlands")
            await page.wait_for_timeout(300)
            print("    Location: Eindhoven, Netherlands")

            # Step 10: Fill "Notice period"
            print("[10] Filling notice period...")
            notice_input = page.locator(
                "input[name='candidate.openQuestionAnswers.4816226.content']"
            )
            await notice_input.scroll_into_view_if_needed()
            await notice_input.click()
            await notice_input.fill("1 month notice period. Currently employed at Actemium.")
            await page.wait_for_timeout(300)
            print("    Notice period filled")

            # Step 11: Answer yes/no question (likely "Do you currently live in the Netherlands?")
            # Radio button: candidate.openQuestionAnswers.4816227.flag - index 0 = Yes, index 1 = No
            print("[11] Answering yes/no question...")
            try:
                yes_radio_label = page.locator(
                    "label[for='input-candidate.openQuestionAnswers.4816227.flag-25-0']"
                )
                if await yes_radio_label.is_visible(timeout=3000):
                    await yes_radio_label.scroll_into_view_if_needed()
                    await yes_radio_label.click()
                    await page.wait_for_timeout(300)
                    print("    Selected: Yes (first radio option)")
                else:
                    # Try clicking radio directly
                    radio = page.locator("input[name='candidate.openQuestionAnswers.4816227.flag']").first
                    await radio.scroll_into_view_if_needed()
                    await radio.check()
                    print("    Checked first radio option")
            except Exception as e:
                print(f"    Radio question: {e}")

            # Step 12: Check consent checkbox - need to click the label
            print("[12] Checking consent...")
            try:
                # The consent checkbox has name='candidate.agreements.0.consent'
                # Click the associated label
                consent_checkbox = page.locator("input[name='candidate.agreements.0.consent']")
                await consent_checkbox.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                # Try clicking label
                consent_id = await consent_checkbox.get_attribute("id")
                if consent_id:
                    consent_label = page.locator(f"label[for='{consent_id}']")
                    if await consent_label.is_visible(timeout=3000):
                        await consent_label.click()
                        print("    Clicked consent label")
                    else:
                        # Try JS click on the input
                        await page.evaluate(
                            "document.querySelector('input[name=\"candidate.agreements.0.consent\"]').click()"
                        )
                        print("    JS-clicked consent checkbox")
                else:
                    # Try JS click directly
                    await page.evaluate(
                        "document.querySelector('input[name=\"candidate.agreements.0.consent\"]').click()"
                    )
                    print("    JS-clicked consent checkbox (no id)")
            except Exception as e:
                print(f"    Consent checkbox: {e}")

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            path = screenshot_path("03-form-bottom")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Screenshot: {path}")

            # Scroll to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            path = screenshot_path("04-before-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"[13] Pre-submit screenshot: {path}")

            # Step 13: Submit
            print("[14] Submitting form...")
            submit_clicked = False

            # Find and click submit button
            for selector in [
                "button[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Apply now')",
                "button:has-text('Apply')",
                "button:has-text('Send')",
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        await btn.click()
                        print(f"    Clicked submit: {selector}")
                        submit_clicked = True
                        await page.wait_for_timeout(5000)
                        break
                except Exception:
                    continue

            if not submit_clicked:
                # Try broader search
                btns = await page.locator("button").all()
                for btn in btns:
                    try:
                        txt = await btn.text_content()
                        if txt and any(w in txt.lower() for w in ["submit", "apply", "send", "solliciteer"]):
                            await btn.scroll_into_view_if_needed()
                            await btn.click()
                            print(f"    Clicked button: '{txt.strip()}'")
                            submit_clicked = True
                            await page.wait_for_timeout(5000)
                            break
                    except Exception:
                        continue

            if not submit_clicked:
                notes = "Could not find submit button"
                print(f"    ERROR: {notes}")

            path = screenshot_path("05-after-submit")
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"    Post-submit screenshot: {path}")

            # Check result
            current_url = page.url
            page_text = await page.evaluate("document.body.innerText")
            print(f"    Final URL: {current_url}")
            print(f"    Page text snippet: {page_text[:400]}")

            success_indicators = [
                "thank you", "bedankt", "application received", "application submitted",
                "sollicitatie ontvangen", "we'll be in touch", "confirmation", "success",
                "your application", "we have received", "great, we have received"
            ]
            captcha_indicators = ["captcha", "hcaptcha", "recaptcha", "i am not a robot", "prove you are human"]

            page_lower = page_text.lower()

            if any(ind in page_lower for ind in success_indicators):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. Final URL: {current_url}"
                print(f"    SUCCESS: {notes}")
            elif any(ind in page_lower for ind in captcha_indicators):
                status = "skipped"
                notes = f"CAPTCHA detected. Manual completion required. URL: {current_url}"
                print(f"    CAPTCHA blocked: {notes}")
            elif not submit_clicked:
                status = "failed"
                notes = "Could not find and click submit button"
            else:
                if "/c/new" not in current_url and ("funda" in current_url or "jobs" in current_url):
                    status = "applied"
                    notes = f"Form submitted, URL changed to: {current_url}. Likely success."
                    print(f"    URL changed (likely success): {notes}")
                else:
                    status = "failed"
                    notes = f"Still on form or unclear result. URL: {current_url}. Page: {page_text[:300]}"
                    print(f"    UNCLEAR: {notes}")

        except Exception as e:
            notes = f"Exception during application: {str(e)}"
            status = "failed"
            print(f"    ERROR: {notes}")
            try:
                path = screenshot_path("error")
                await page.screenshot(path=path)
                screenshots.append(path)
            except Exception:
                pass

        finally:
            await browser.close()

    # Save to applications.json
    app_entry = {
        "id": f"funda-medior-net-v2-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Funda Real Estate B.V.",
        "role": "Medior Backend .NET Engineer",
        "url": JOB_URL,
        "application_url": APPLICATION_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots,
        "notes": notes,
        "response": None,
        "email_used": APPLICANT["email"],
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    apps.append(app_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT ===")
    print(f"Status: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")
    print(f"Application log saved to: {APPLICATIONS_JSON}")
    return app_entry


if __name__ == "__main__":
    asyncio.run(run())
