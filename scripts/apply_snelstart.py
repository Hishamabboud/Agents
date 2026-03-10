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

In my current role as Software Service Engineer at Actemium (VINCI Energies), I develop and maintain full-stack applications using .NET, C#, ASP.NET, and SQL Server, while delivering custom integrations and REST APIs for demanding industrial clients. I work in Agile sprints and contribute across the full software lifecycle — from feature design to deployment and production support. Previously at Delta Electronics, I led a migration of a legacy Visual Basic codebase to C#, improving maintainability and performance, and built a web application for HR budget management.

My technical stack aligns well with what SnelStart relies on: C# and .NET for backend development, SQL Server for data management, Azure and CI/CD pipelines for cloud deployment, and modern JavaScript frameworks for frontend interfaces. During my internship at ASML, I deepened my experience with agile tooling (Jira, Azure DevOps) and automated testing practices, which I continue to apply in my current role.

Beyond technical skills, I bring a multilingual background (Dutch, English, Arabic) and genuine entrepreneurial drive demonstrated through founding CogitatAI, an AI customer support platform I am building independently.

I am available for a conversation at your convenience.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com"""


def screenshot(page, name, timeout=10000):
    path = os.path.join(SCREENSHOTS_DIR, f"snelstart-{name}.png")
    try:
        page.screenshot(path=path, full_page=False, timeout=timeout)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed ({name}): {e}")
        # Try with clip to avoid font loading issues
        try:
            page.screenshot(path=path, clip={"x": 0, "y": 0, "width": 1280, "height": 900}, timeout=timeout)
            print(f"Screenshot (clipped) saved: {path}")
            return path
        except Exception as e2:
            print(f"Clipped screenshot also failed: {e2}")
            return None


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
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--font-render-hinting=none",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        # Block font loading to speed up screenshots
        context.route("**/*.woff", lambda route: route.abort())
        context.route("**/*.woff2", lambda route: route.abort())
        context.route("**/*.ttf", lambda route: route.abort())
        context.route("**/*.otf", lambda route: route.abort())
        context.route("**/fonts.googleapis.com/**", lambda route: route.abort())
        context.route("**/fonts.gstatic.com/**", lambda route: route.abort())

        page = context.new_page()

        try:
            # Step 1: Navigate to the vacancy page
            print(f"Navigating to vacancy: {VACANCY_URL}")
            try:
                page.goto(VACANCY_URL, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"Navigation warning (continuing): {e}")
            time.sleep(2)

            s = screenshot(page, "01-vacancy-page")
            if s:
                result["screenshots"].append(s)
            print(f"Page title: {page.title()}")
            print(f"URL: {page.url()}")

            # Step 2: Navigate to the apply form
            print(f"\nNavigating to application form: {APPLY_URL}")
            try:
                page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"Navigation warning (continuing): {e}")
            time.sleep(5)  # Give HubSpot form time to load

            s = screenshot(page, "02-apply-form-initial")
            if s:
                result["screenshots"].append(s)
            print(f"Apply page title: {page.title()}")
            print(f"Apply URL: {page.url()}")

            # Step 3: Inspect the page for form elements
            # Print page text to understand structure
            body_text = page.evaluate("() => document.body.innerText.substring(0, 3000)")
            print(f"\nPage body text:\n{body_text}\n")

            # Check all frames
            frames = page.frames
            print(f"Total frames: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")

            # Look for form in main page and all frames
            form_frame = None
            all_frames = [page] + list(page.frames[1:])  # main + child frames

            for frame in all_frames:
                try:
                    inputs = frame.query_selector_all("input[type='text'], input[type='email'], input[type='tel'], textarea")
                    if inputs:
                        print(f"\nFound {len(inputs)} inputs in frame: {frame.url}")
                        form_frame = frame
                        break
                except Exception as e:
                    print(f"Frame error: {e}")

            if not form_frame:
                print("No form inputs found in any frame. Checking iframes...")
                iframes_el = page.query_selector_all("iframe")
                print(f"Iframe elements on page: {len(iframes_el)}")
                for el in iframes_el:
                    try:
                        src = el.get_attribute("src") or "no-src"
                        print(f"  iframe src: {src}")
                    except:
                        pass

                # Print full HTML for debugging
                html_snippet = page.evaluate("() => document.documentElement.innerHTML.substring(0, 5000)")
                print(f"\nHTML snippet:\n{html_snippet}")

                result["status"] = "skipped"
                result["notes"] = (
                    "HubSpot form could not be interacted with in headless browser. "
                    "The form is loaded via JavaScript (HubSpot portal 239619, form 6d1a7f79-b15c-48ce-9d86-f6fc4894d8b4). "
                    "Manual application required at: " + APPLY_URL + " "
                    "or email CV directly to werken@snelstart.nl"
                )
                s = screenshot(page, "03-no-form-found")
                if s:
                    result["screenshots"].append(s)
                return result

            print(f"\nUsing form frame: {form_frame.url}")

            # Get all form fields for inspection
            all_inputs = form_frame.query_selector_all("input, textarea, select")
            print(f"\nAll form inputs: {len(all_inputs)}")
            for inp in all_inputs:
                try:
                    itype = inp.get_attribute("type") or "text"
                    iname = inp.get_attribute("name") or ""
                    iid = inp.get_attribute("id") or ""
                    iplaceholder = inp.get_attribute("placeholder") or ""
                    ilabel = ""
                    if iid:
                        lbl = form_frame.query_selector(f"label[for='{iid}']")
                        if lbl:
                            ilabel = lbl.inner_text().strip()
                    print(f"  type={itype}, name={iname}, id={iid}, placeholder={iplaceholder}, label='{ilabel}'")
                except Exception as e:
                    print(f"  error reading input: {e}")

            # Fill out the form
            filled_count = 0

            field_fill_map = [
                # (name_patterns, placeholder_patterns, id_patterns, label_patterns, value)
                (["firstname", "first_name", "voornaam"], ["Voornaam", "First name", "Naam"], ["firstname", "first_name"], ["voornaam", "first name"], APPLICANT["first_name"]),
                (["lastname", "last_name", "achternaam"], ["Achternaam", "Last name"], ["lastname", "last_name"], ["achternaam", "last name"], APPLICANT["last_name"]),
                (["email"], ["E-mail", "Email", "email"], ["email"], ["email", "e-mail"], APPLICANT["email"]),
                (["phone", "telefoon", "mobiel", "mobilephone"], ["Telefoon", "Phone", "Mobiel"], ["phone", "telefoon"], ["telefoon", "phone", "mobiel"], APPLICANT["phone"]),
            ]

            for names, placeholders, ids, labels_kw, value in field_fill_map:
                filled = False
                # Try by name attribute
                for n in names:
                    try:
                        el = form_frame.query_selector(f"input[name='{n}'], input[name*='{n}']")
                        if el and el.is_visible():
                            el.click()
                            el.fill(value)
                            filled_count += 1
                            filled = True
                            print(f"  Filled by name '{n}': {value}")
                            break
                    except:
                        pass
                if filled:
                    continue

                # Try by placeholder
                for ph in placeholders:
                    try:
                        el = form_frame.query_selector(f"input[placeholder*='{ph}'], textarea[placeholder*='{ph}']")
                        if el and el.is_visible():
                            el.click()
                            el.fill(value)
                            filled_count += 1
                            filled = True
                            print(f"  Filled by placeholder '{ph}': {value}")
                            break
                    except:
                        pass
                if filled:
                    continue

                # Try by id
                for eid in ids:
                    try:
                        el = form_frame.query_selector(f"#{eid}, input[id*='{eid}']")
                        if el and el.is_visible():
                            el.click()
                            el.fill(value)
                            filled_count += 1
                            filled = True
                            print(f"  Filled by id '{eid}': {value}")
                            break
                    except:
                        pass
                if filled:
                    continue

                # Try by label
                all_labels = form_frame.query_selector_all("label")
                for label_el in all_labels:
                    try:
                        ltext = label_el.inner_text().lower()
                        if any(kw in ltext for kw in labels_kw):
                            for_id = label_el.get_attribute("for")
                            if for_id:
                                inp_el = form_frame.query_selector(f"#{for_id}")
                                if inp_el and inp_el.is_visible():
                                    inp_el.click()
                                    inp_el.fill(value)
                                    filled_count += 1
                                    filled = True
                                    print(f"  Filled by label '{ltext.strip()}': {value}")
                                    break
                    except:
                        pass
                if filled:
                    continue

            # Handle textarea (motivation/cover letter)
            textareas = form_frame.query_selector_all("textarea:visible")
            print(f"\nVisible textareas: {len(textareas)}")
            for ta in textareas:
                try:
                    ta_name = ta.get_attribute("name") or ""
                    ta_placeholder = ta.get_attribute("placeholder") or ""
                    print(f"  textarea name={ta_name}, placeholder={ta_placeholder}")
                    ta.click()
                    ta.fill(COVER_LETTER_TEXT)
                    filled_count += 1
                    print(f"  Filled textarea with cover letter")
                except Exception as e:
                    print(f"  textarea fill error: {e}")

            # Handle file upload
            file_inputs = form_frame.query_selector_all("input[type='file']")
            print(f"\nFile inputs: {len(file_inputs)}")
            for fi in file_inputs:
                if os.path.exists(RESUME_PDF):
                    try:
                        fi.set_input_files(RESUME_PDF)
                        print(f"  Uploaded: {RESUME_PDF}")
                        time.sleep(2)
                        filled_count += 1
                    except Exception as e:
                        print(f"  File upload error: {e}")

            print(f"\nTotal fields filled: {filled_count}")
            time.sleep(2)

            s = screenshot(page, "04-form-filled")
            if s:
                result["screenshots"].append(s)

            if filled_count == 0:
                result["status"] = "skipped"
                result["notes"] = (
                    "HubSpot form rendered but no form fields could be filled. "
                    "The form may use shadow DOM or requires full JS execution not available in headless mode. "
                    "Please apply manually at: " + APPLY_URL + " or email: werken@snelstart.nl"
                )
                return result

            # Find and click submit button
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button.hs-button",
                "button.hs-button.primary",
                "input.hs-button",
                "button:has-text('Verzenden')",
                "button:has-text('Submit')",
                "button:has-text('Solliciteer')",
                "button:has-text('Versturen')",
            ]

            submit_btn = None
            for sel in submit_selectors:
                try:
                    btn = form_frame.query_selector(sel)
                    if btn:
                        btn_text = btn.inner_text() if hasattr(btn, 'inner_text') else ""
                        btn_val = btn.get_attribute("value") or ""
                        print(f"  Found submit candidate: {sel} text='{btn_text}' val='{btn_val}'")
                        if btn.is_visible():
                            submit_btn = btn
                            break
                except Exception as e:
                    pass

            if submit_btn:
                s = screenshot(page, "05-pre-submit")
                if s:
                    result["screenshots"].append(s)
                print("\nClicking submit button...")
                submit_btn.click()
                time.sleep(4)
                s = screenshot(page, "06-post-submit")
                if s:
                    result["screenshots"].append(s)

                # Check for confirmation
                page_text = page.evaluate("() => document.body.innerText.substring(0, 2000)")
                print(f"\nPost-submit page text:\n{page_text}")

                if any(kw in page_text.lower() for kw in ["bedankt", "thank", "ontvangen", "received", "success", "verstuurd"]):
                    result["status"] = "applied"
                    result["notes"] = f"Application submitted successfully via {APPLY_URL}. Confirmation received."
                else:
                    result["status"] = "applied"
                    result["notes"] = f"Form submitted via {APPLY_URL}. Confirmation page text unclear - check screenshot."
            else:
                result["status"] = "skipped"
                result["notes"] = (
                    f"Form was found and {filled_count} fields filled, but submit button not found. "
                    "Please complete manually at: " + APPLY_URL
                )

        except Exception as e:
            print(f"\nError during automation: {e}")
            import traceback
            traceback.print_exc()
            result["notes"] = f"Error: {str(e)}"
            try:
                s = screenshot(page, "error")
                if s:
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
