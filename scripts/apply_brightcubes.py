#!/usr/bin/env python3
"""
Apply to Bright Cubes - AI/ML Engineer position.
Uses Playwright to navigate and fill the HubSpot application form.
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Applicant details
APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
JOB_URL = "https://brightcubes.nl/vacatures/machine-learning-engineer/"

MOTIVATION = """I am excited to apply for the AI/ML Engineer position at Bright Cubes. I am currently building CogitatAI, an AI chatbot platform featuring sentiment analysis and NLP capabilities, which demonstrates my hands-on experience with machine learning in production. At ASML, I developed Python-based software solutions for high-tech systems, and I have extensive experience with Azure cloud infrastructure including CI/CD pipelines and cloud-native deployments. My BSc from Fontys University of Applied Sciences (ICT - Software Engineering) and my passion for AI/ML make me a strong fit for this role. I am eager to join Bright Cubes and help clients derive real value from their data."""

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

def save_screenshot(page, name):
    path = f"{SCREENSHOTS_DIR}/brightcubes-{name}-{timestamp}.png"
    try:
        page.screenshot(path=path, full_page=False, timeout=10000)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed ({name}): {e}")
        # Try with clip instead
        try:
            page.screenshot(path=path, clip={"x": 0, "y": 0, "width": 1280, "height": 900}, timeout=10000)
            print(f"Screenshot (clipped) saved: {path}")
        except Exception as e2:
            print(f"Clipped screenshot also failed: {e2}")
    return path

def run():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--font-render-hinting=none",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = context.new_page()

        # Remove webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print(f"Navigating to {JOB_URL}")
        try:
            page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation warning: {e}")

        time.sleep(3)

        # Take initial screenshot
        s = save_screenshot(page, "01-job-page")
        screenshots.append(s)
        print("Page title:", page.title())
        print("Page URL:", page.url)

        # Check for cookie consent
        try:
            for btn_text in ["Accept all", "Accept", "Accepteer", "OK", "Alle cookies accepteren"]:
                btns = page.locator(f"button:has-text('{btn_text}')")
                if btns.count() > 0 and btns.first.is_visible(timeout=2000):
                    btns.first.click()
                    print(f"Clicked cookie consent: {btn_text}")
                    time.sleep(1)
                    break
        except:
            print("No cookie consent found")

        # Scroll down to find the form
        print("Scrolling to find form...")
        for scroll_pos in [500, 1000, 1500, 2000]:
            page.evaluate(f"window.scrollTo(0, {scroll_pos})")
            time.sleep(0.5)

        s = save_screenshot(page, "02-scrolled")
        screenshots.append(s)

        # Inspect page for HubSpot and iframes
        print("\nInspecting page structure...")

        # Get all frames
        frames = page.frames
        print(f"Total frames: {len(frames)}")
        for i, f in enumerate(frames):
            print(f"  frame[{i}]: {f.url[:100]}")

        # Get all iframes
        iframes_locator = page.locator("iframe")
        iframe_count = iframes_locator.count()
        print(f"\nIframes on page: {iframe_count}")
        for i in range(min(iframe_count, 10)):
            try:
                src = iframes_locator.nth(i).get_attribute("src") or ""
                iframe_id = iframes_locator.nth(i).get_attribute("id") or ""
                iframe_class = iframes_locator.nth(i).get_attribute("class") or ""
                print(f"  iframe[{i}]: src={src[:80]}, id={iframe_id}, class={iframe_class[:40]}")
            except:
                pass

        # Check for direct form elements
        print("\nLooking for form elements...")
        form_elements = page.locator("input, textarea, select")
        elem_count = form_elements.count()
        print(f"Form elements found: {elem_count}")
        for i in range(min(elem_count, 20)):
            try:
                el = form_elements.nth(i)
                name = el.get_attribute("name") or ""
                el_type = el.get_attribute("type") or ""
                placeholder = el.get_attribute("placeholder") or ""
                el_id = el.get_attribute("id") or ""
                print(f"  element[{i}]: name={name}, type={el_type}, id={el_id}, placeholder={placeholder[:30]}")
            except:
                pass

        # Look for HubSpot-specific elements
        hs_elements = page.locator("[class*='hs-form'], [class*='hubspot'], .hbspt-form, [data-form-id]")
        hs_count = hs_elements.count()
        print(f"\nHubSpot elements found: {hs_count}")

        # Wait for HubSpot form to load (it's dynamically injected)
        print("Waiting for dynamic form to load...")
        time.sleep(5)

        # Re-check after wait
        frames_after = page.frames
        print(f"\nFrames after wait: {len(frames_after)}")
        for i, f in enumerate(frames_after):
            if i > 0:  # Skip main frame
                print(f"  frame[{i}]: {f.url[:100]}")

        # Look for HubSpot frame specifically
        hubspot_frame = None
        for frame in page.frames:
            url = frame.url.lower()
            if any(x in url for x in ["hubspot", "hsforms", "hs-form"]):
                hubspot_frame = frame
                print(f"\nFound HubSpot frame: {frame.url}")
                break

        s = save_screenshot(page, "03-after-dynamic-wait")
        screenshots.append(s)

        if hubspot_frame:
            print("Using HubSpot frame approach")
            status = fill_hubspot_frame(page, hubspot_frame, screenshots)
        else:
            print("No HubSpot frame found - trying main page approach")
            # Check if there's a direct apply button
            apply_btns = page.locator("a:has-text('Solliciteer'), a:has-text('Apply'), button:has-text('Solliciteer'), button:has-text('Apply')")
            btn_count = apply_btns.count()
            print(f"Apply buttons found: {btn_count}")
            if btn_count > 0:
                print("Clicking apply button...")
                apply_btns.first.click()
                time.sleep(3)
                s = save_screenshot(page, "04-after-apply-click")
                screenshots.append(s)

                # Check again for forms after click
                new_url = page.url
                print(f"URL after click: {new_url}")

                # Check for external application URL
                if new_url != JOB_URL:
                    print(f"Redirected to: {new_url}")
                    status = handle_external_form(page, new_url, screenshots)
                else:
                    status = fill_visible_form(page, screenshots)
            else:
                print("No apply button found, trying to fill whatever form exists")
                status = fill_visible_form(page, screenshots)

        browser.close()
        return status, screenshots

def fill_hubspot_frame(page, frame, screenshots):
    """Fill HubSpot form in an iframe."""
    print("\nFilling HubSpot form in iframe...")

    try:
        time.sleep(2)

        # Get all inputs in the frame
        inputs = frame.locator("input, textarea, select")
        inp_count = inputs.count()
        print(f"Inputs in HubSpot frame: {inp_count}")

        for i in range(min(inp_count, 20)):
            try:
                el = inputs.nth(i)
                name = el.get_attribute("name") or ""
                el_type = el.get_attribute("type") or ""
                label = el.get_attribute("placeholder") or ""
                print(f"  input[{i}]: name={name}, type={el_type}, placeholder={label}")
            except:
                pass

        # Common HubSpot field name mappings
        field_mappings = [
            # (field names to try, value)
            (["firstname", "first_name", "fname", "voornaam"], APPLICANT["first_name"]),
            (["lastname", "last_name", "lname", "achternaam"], APPLICANT["last_name"]),
            (["email", "e-mail", "emailaddress"], APPLICANT["email"]),
            (["phone", "mobilephone", "telefoon", "tel"], APPLICANT["phone"]),
            (["city", "stad"], APPLICANT["city"]),
            (["message", "motivation", "motivatie", "comment", "sollicitatie"], MOTIVATION),
        ]

        filled_count = 0
        for field_names, value in field_mappings:
            for fname in field_names:
                try:
                    sel = f"input[name='{fname}'], textarea[name='{fname}']"
                    el = frame.locator(sel).first
                    if el.count() > 0 and el.is_visible(timeout=2000):
                        el.fill(value)
                        print(f"Filled field: {fname}")
                        filled_count += 1
                        time.sleep(0.3)
                        break
                except:
                    pass

        print(f"Filled {filled_count} fields")

        # Try file upload
        try:
            file_inputs = frame.locator("input[type='file']")
            if file_inputs.count() > 0:
                file_inputs.first.set_input_files(CV_PATH)
                print("CV uploaded")
                time.sleep(2)
        except Exception as e:
            print(f"File upload failed: {e}")

        s = save_screenshot(page, "05-form-filled")
        screenshots.append(s)

        # Find and click submit
        submit_btns = frame.locator("input[type='submit'], button[type='submit'], button:has-text('Verstuur'), button:has-text('Verzenden'), button:has-text('Submit'), button:has-text('Solliciteer')")
        if submit_btns.count() > 0:
            s = save_screenshot(page, "06-pre-submit")
            screenshots.append(s)
            print("Clicking submit button...")
            submit_btns.first.click()
            time.sleep(4)
            s = save_screenshot(page, "07-post-submit")
            screenshots.append(s)
            print("Form submitted!")
            return "applied"
        else:
            print("No submit button found in HubSpot frame")
            s = save_screenshot(page, "06-no-submit-button")
            screenshots.append(s)
            return "failed"

    except Exception as e:
        print(f"Error filling HubSpot form: {e}")
        s = save_screenshot(page, "error-hubspot")
        screenshots.append(s)
        return "failed"

def fill_visible_form(page, screenshots):
    """Fill whatever form elements are visible on the page."""
    print("\nAttempting to fill visible form elements...")

    # Scroll through page looking for inputs
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    all_filled = 0

    # Field value pairs based on common attribute patterns
    fill_attempts = [
        # (selector, value)
        ("input[name*='first'], input[placeholder*='Voornaam'], input[placeholder*='First name'], input[id*='first']", APPLICANT["first_name"]),
        ("input[name*='last'], input[placeholder*='Achternaam'], input[placeholder*='Last name'], input[id*='last']", APPLICANT["last_name"]),
        ("input[type='email'], input[name*='email'], input[placeholder*='mail']", APPLICANT["email"]),
        ("input[type='tel'], input[name*='phone'], input[placeholder*='tel'], input[placeholder*='Phone']", APPLICANT["phone"]),
        ("textarea[name*='message'], textarea[name*='motivation'], textarea[placeholder*='motivatie']", MOTIVATION),
    ]

    for selector, value in fill_attempts:
        try:
            el = page.locator(selector).first
            if el.count() > 0 and el.is_visible(timeout=2000):
                el.fill(value)
                print(f"Filled: {selector[:50]}")
                all_filled += 1
                time.sleep(0.3)
        except:
            pass

    print(f"Filled {all_filled} fields")
    s = save_screenshot(page, "05-form-fill-attempt")
    screenshots.append(s)
    return "failed" if all_filled == 0 else "applied"

def handle_external_form(page, url, screenshots):
    """Handle form on external application URL."""
    print(f"Handling external form at: {url}")
    time.sleep(2)
    s = save_screenshot(page, "04-external-form")
    screenshots.append(s)
    return fill_visible_form(page, screenshots)


if __name__ == "__main__":
    print("Starting Bright Cubes application...")
    print(f"CV: {CV_PATH}")
    print(f"URL: {JOB_URL}")

    result, screenshots = run()
    print(f"\nResult: {result}")
    print("Screenshots taken:")
    for s in screenshots:
        print(f"  {s}")
