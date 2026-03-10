#!/usr/bin/env python3
"""
Browser automation script to apply to SnelStart Full-Stack Developer role.
Uses Python Playwright with the pre-installed Chromium.
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PDF = "/home/user/Agents/profile/resume.pdf"
VACANCY_URL = "https://www.werkenbijsnelstart.nl/vacatures/full-stack-developer-amersfoort-snelstart"
APPLY_URL = "https://www.werkenbijsnelstart.nl/solliciteren-nu?vacature_id=376d6c64-66ae-f011-bbd3-7ced8d73068c&functie=Full-Stack%20Developer"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
}

COVER_LETTER_TEXT = """Dear SnelStart Recruitment Team,

I am writing to express my enthusiasm for the Full-Stack Developer position at SnelStart Software B.V. SnelStart's reputation as a leading Dutch accounting and administration SaaS platform, trusted by thousands of entrepreneurs, makes it a company where I would be proud to contribute my skills in building reliable, user-centric software.

In my current role as Software Service Engineer at Actemium (VINCI Energies), I develop and maintain full-stack applications using .NET, C#, ASP.NET, and SQL Server, while delivering custom integrations and REST APIs for demanding industrial clients. I work in Agile sprints and contribute across the full software lifecycle — from feature design to deployment and production support. Previously at Delta Electronics, I led a migration of a legacy Visual Basic codebase to C#, improving maintainability and performance, and built a web application for HR budget management — experience directly applicable to SnelStart's product development work.

My technical stack aligns well with what SnelStart relies on: C# and .NET for backend development, SQL Server for data management, Azure and CI/CD pipelines for cloud deployment, and modern JavaScript frameworks for frontend interfaces. During my internship at ASML, I deepened my experience with agile tooling (Jira, Azure DevOps) and automated testing practices, which I continue to apply in my current role.

Beyond technical skills, I bring a multilingual background (Dutch, English, Arabic) and genuine entrepreneurial drive demonstrated through founding CogitatAI, an AI customer support platform I am building independently. I am excited about the prospect of joining a product company where I can make a tangible impact on software used by real businesses every day.

I am available for a conversation at your convenience and would welcome the opportunity to discuss how I can contribute to SnelStart's engineering team.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com"""


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"snelstart-{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"Screenshot saved: {path}")
    return path


def run_application():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    result = {
        "status": "failed",
        "screenshots": [],
        "notes": "",
        "url_used": VACANCY_URL,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to the vacancy page
            print(f"Navigating to vacancy: {VACANCY_URL}")
            page.goto(VACANCY_URL, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            s = screenshot(page, "01-vacancy-page")
            result["screenshots"].append(s)
            print(f"Page title: {page.title()}")
            print(f"URL: {page.url()}")

            # Step 2: Navigate to the apply form
            print(f"\nNavigating to application form: {APPLY_URL}")
            page.goto(APPLY_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            s = screenshot(page, "02-apply-form-initial")
            result["screenshots"].append(s)
            print(f"Apply page title: {page.title()}")
            print(f"Apply URL: {page.url()}")

            # Step 3: Wait for HubSpot form to load
            print("\nWaiting for HubSpot form to load...")
            try:
                page.wait_for_selector("form, .hs-form, iframe", timeout=15000)
                time.sleep(3)
            except Exception as e:
                print(f"Form selector wait failed: {e}")

            s = screenshot(page, "03-form-loaded")
            result["screenshots"].append(s)

            # Check for iframes (HubSpot often loads in iframe)
            frames = page.frames
            print(f"Total frames: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")

            # Try to find form in main page first
            form_frame = page

            # Check if form is in an iframe
            iframes = page.query_selector_all("iframe")
            print(f"Iframes found: {len(iframes)}")

            if iframes:
                for iframe in iframes:
                    src = iframe.get_attribute("src") or ""
                    print(f"  iframe src: {src}")
                    if "hubspot" in src or "hs-form" in src or src == "":
                        frame_content = iframe.content_frame()
                        if frame_content:
                            inner_html = frame_content.content()
                            if "email" in inner_html.lower() or "input" in inner_html.lower():
                                print("  Found form content in iframe!")
                                form_frame = frame_content
                                break

            # Get all input fields
            inputs = form_frame.query_selector_all("input, textarea, select")
            print(f"\nForm inputs found: {len(inputs)}")
            for inp in inputs:
                try:
                    input_type = inp.get_attribute("type") or "text"
                    input_name = inp.get_attribute("name") or ""
                    input_placeholder = inp.get_attribute("placeholder") or ""
                    input_id = inp.get_attribute("id") or ""
                    label_text = ""
                    # Try to find associated label
                    if input_id:
                        label = form_frame.query_selector(f"label[for='{input_id}']")
                        if label:
                            label_text = label.inner_text()
                    print(f"  Input: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}, label={label_text}")
                except Exception as e:
                    print(f"  Error reading input: {e}")

            # Fill form fields
            filled_count = 0

            # Try common HubSpot field patterns
            field_mappings = [
                # (selector_patterns, value)
                (["input[name*='firstname']", "input[name*='first_name']", "input[id*='firstname']", "input[placeholder*='Voornaam']", "input[placeholder*='First']"], APPLICANT["first_name"]),
                (["input[name*='lastname']", "input[name*='last_name']", "input[id*='lastname']", "input[placeholder*='Achternaam']", "input[placeholder*='Last']"], APPLICANT["last_name"]),
                (["input[name*='email']", "input[type='email']", "input[id*='email']", "input[placeholder*='E-mail']", "input[placeholder*='Email']"], APPLICANT["email"]),
                (["input[name*='phone']", "input[type='tel']", "input[id*='phone']", "input[placeholder*='Telefoon']", "input[placeholder*='Phone']"], APPLICANT["phone"]),
                (["textarea[name*='message']", "textarea[name*='motivatie']", "textarea[id*='message']", "textarea[placeholder*='Motivatie']", "textarea[placeholder*='Bericht']"], COVER_LETTER_TEXT[:500]),
            ]

            for selectors, value in field_mappings:
                for sel in selectors:
                    try:
                        el = form_frame.query_selector(sel)
                        if el and el.is_visible():
                            el.click()
                            el.fill(value)
                            filled_count += 1
                            print(f"  Filled: {sel} = {value[:50]}...")
                            break
                    except Exception as e:
                        pass

            # Also try generic approach: fill by label text
            labels = form_frame.query_selector_all("label")
            for label in labels:
                try:
                    label_text = label.inner_text().lower()
                    for_attr = label.get_attribute("for")
                    if for_attr:
                        input_el = form_frame.query_selector(f"#{for_attr}")
                        if input_el and input_el.is_visible():
                            if "voornaam" in label_text or "first" in label_text:
                                input_el.fill(APPLICANT["first_name"])
                                filled_count += 1
                                print(f"  Filled by label 'voornaam': {APPLICANT['first_name']}")
                            elif "achternaam" in label_text or "last" in label_text:
                                input_el.fill(APPLICANT["last_name"])
                                filled_count += 1
                                print(f"  Filled by label 'achternaam': {APPLICANT['last_name']}")
                            elif "e-mail" in label_text or "email" in label_text:
                                input_el.fill(APPLICANT["email"])
                                filled_count += 1
                                print(f"  Filled by label 'email': {APPLICANT['email']}")
                            elif "telefoon" in label_text or "phone" in label_text or "mobiel" in label_text:
                                input_el.fill(APPLICANT["phone"])
                                filled_count += 1
                                print(f"  Filled by label 'telefoon': {APPLICANT['phone']}")
                except Exception as e:
                    pass

            print(f"\nTotal fields filled: {filled_count}")
            time.sleep(1)

            # Handle file upload for CV
            file_inputs = form_frame.query_selector_all("input[type='file']")
            print(f"File upload inputs: {len(file_inputs)}")
            for file_input in file_inputs:
                if os.path.exists(RESUME_PDF):
                    try:
                        file_input.set_input_files(RESUME_PDF)
                        print(f"  Uploaded resume: {RESUME_PDF}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"  File upload failed: {e}")

            time.sleep(2)
            s = screenshot(page, "04-form-filled")
            result["screenshots"].append(s)

            # Print page source snippet to understand what we're working with
            body_text = page.evaluate("() => document.body.innerText.substring(0, 2000)")
            print(f"\nPage body text preview:\n{body_text}")

            # Look for any visible form or content
            all_inputs_on_page = page.query_selector_all("input:visible, textarea:visible")
            print(f"\nVisible inputs on page: {len(all_inputs_on_page)}")

            if filled_count == 0:
                result["status"] = "skipped"
                result["notes"] = "HubSpot form loaded dynamically via JavaScript - could not interact with form fields. Form may require JavaScript execution that is blocked in headless mode. Contact at werken@snelstart.nl or apply directly at: " + APPLY_URL
                print("\nForm could not be filled - HubSpot JS form not accessible")
            else:
                # Look for submit button
                submit_btn = None
                for sel in ["input[type='submit']", "button[type='submit']", "button.hs-button", "button:has-text('Verzenden')", "button:has-text('Solliciteer')", "button:has-text('Submit')"]:
                    try:
                        btn = form_frame.query_selector(sel)
                        if btn and btn.is_visible():
                            submit_btn = btn
                            print(f"\nFound submit button: {sel}")
                            break
                    except:
                        pass

                if submit_btn:
                    s = screenshot(page, "05-pre-submit")
                    result["screenshots"].append(s)
                    print("\nSubmitting form...")
                    submit_btn.click()
                    time.sleep(3)
                    s = screenshot(page, "06-post-submit")
                    result["screenshots"].append(s)
                    result["status"] = "applied"
                    result["notes"] = f"Applied via {APPLY_URL}. Form filled and submitted."
                else:
                    result["status"] = "skipped"
                    result["notes"] = "Form fields were found but submit button not located. Please complete manually at: " + APPLY_URL

        except Exception as e:
            print(f"\nError during automation: {e}")
            result["notes"] = f"Error: {str(e)}"
            try:
                s = screenshot(page, "error")
                result["screenshots"].append(s)
            except:
                pass

        finally:
            browser.close()

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("SnelStart Full-Stack Developer Application")
    print("=" * 60)
    result = run_application()
    print("\n" + "=" * 60)
    print("RESULT:", json.dumps(result, indent=2))
    print("=" * 60)

    # Save result
    with open("/home/user/Agents/data/snelstart_apply_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Result saved to /home/user/Agents/data/snelstart_apply_result.json")
