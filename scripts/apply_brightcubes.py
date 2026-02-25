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
    page.screenshot(path=path, full_page=False)
    print(f"Screenshot saved: {path}")
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
        page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Take initial screenshot
        s = save_screenshot(page, "01-job-page")
        screenshots.append(s)
        print("Page title:", page.title())

        # Check for cookie consent
        try:
            cookie_btn = page.locator("button:has-text('Accept'), button:has-text('Accepteer'), button:has-text('OK'), [data-consent='accept']").first
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
                print("Clicked cookie consent")
                time.sleep(1)
        except:
            print("No cookie consent found")

        # Scroll down to find the form
        print("Scrolling to find form...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(1)

        s = save_screenshot(page, "02-scrolled-mid")
        screenshots.append(s)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        s = save_screenshot(page, "03-bottom-page")
        screenshots.append(s)

        # Look for HubSpot form iframe
        print("Looking for HubSpot form...")

        # Get all iframes
        frames = page.frames
        print(f"Found {len(frames)} frames on page")
        for f in frames:
            print(f"  Frame URL: {f.url}")

        # Check for HubSpot form iframe
        hs_iframe = None
        try:
            hs_iframe = page.frame_locator("iframe[data-hs-forms-root]").first
            print("Found HubSpot iframe via data-hs-forms-root")
        except:
            pass

        if not hs_iframe:
            try:
                hs_iframe = page.frame_locator("iframe.hs-form-iframe").first
                print("Found HubSpot iframe via class")
            except:
                pass

        # Try to find iframes more broadly
        iframes_locator = page.locator("iframe")
        iframe_count = iframes_locator.count()
        print(f"Found {iframe_count} iframes on page")

        for i in range(iframe_count):
            iframe_src = iframes_locator.nth(i).get_attribute("src") or ""
            iframe_id = iframes_locator.nth(i).get_attribute("id") or ""
            print(f"  iframe[{i}]: src={iframe_src[:80]}, id={iframe_id}")

        # Get page source to understand form structure
        page_content = page.content()

        # Check for HubSpot form in page source
        if "hubspot" in page_content.lower() or "hs-form" in page_content.lower():
            print("HubSpot form detected in page source")

        # Check for forms directly
        forms = page.locator("form")
        form_count = forms.count()
        print(f"Found {form_count} forms on page")

        for i in range(form_count):
            form_id = forms.nth(i).get_attribute("id") or ""
            form_class = forms.nth(i).get_attribute("class") or ""
            print(f"  form[{i}]: id={form_id}, class={form_class[:60]}")

        # Wait for HubSpot to load - it might be dynamically injected
        print("Waiting for HubSpot form to load...")
        try:
            page.wait_for_selector(".hs-form, .hs-form-iframe, iframe[src*='hubspot'], form[data-form-id]", timeout=10000)
            print("HubSpot form selector found")
        except:
            print("HubSpot form selector not found, trying other approaches")

        time.sleep(3)

        # Re-check frames after waiting
        frames = page.frames
        print(f"\nAfter wait - Found {len(frames)} frames on page")
        for f in frames:
            print(f"  Frame URL: {f.url[:100]}")

        s = save_screenshot(page, "04-after-wait")
        screenshots.append(s)

        # Try working directly with HubSpot form in iframe
        hubspot_frame = None
        for frame in page.frames:
            if "hubspot" in frame.url.lower() or "hsforms" in frame.url.lower():
                hubspot_frame = frame
                print(f"Found HubSpot frame: {frame.url}")
                break

        if hubspot_frame:
            print("Working with HubSpot frame directly")
            result = fill_hubspot_form(page, hubspot_frame, screenshots)
        else:
            print("No HubSpot frame found, trying direct form fill on main page")
            result = fill_form_main_page(page, screenshots)

        browser.close()
        return result, screenshots

def fill_hubspot_form(page, frame, screenshots):
    """Fill HubSpot form in an iframe."""
    print("Filling HubSpot form in iframe...")

    try:
        # Common HubSpot field names
        fields = [
            ("firstname", APPLICANT["first_name"]),
            ("lastname", APPLICANT["last_name"]),
            ("email", APPLICANT["email"]),
            ("phone", APPLICANT["phone"]),
            ("city", APPLICANT["city"]),
            ("message", MOTIVATION),
        ]

        for field_name, value in fields:
            try:
                selector = f"input[name='{field_name}'], textarea[name='{field_name}']"
                el = frame.locator(selector).first
                if el.is_visible(timeout=3000):
                    el.fill(value)
                    print(f"Filled {field_name}")
                    time.sleep(0.3)
            except Exception as e:
                print(f"Could not fill {field_name}: {e}")

        # Try file upload
        try:
            file_input = frame.locator("input[type='file']").first
            if file_input.is_visible(timeout=3000):
                file_input.set_input_files(CV_PATH)
                print("Uploaded CV")
                time.sleep(1)
        except Exception as e:
            print(f"Could not upload file: {e}")

        s = save_screenshot(page, "05-form-filled")
        screenshots.append(s)

        # Submit
        submit_btn = frame.locator("input[type='submit'], button[type='submit']").first
        if submit_btn.is_visible(timeout=3000):
            s = save_screenshot(page, "06-pre-submit")
            screenshots.append(s)
            submit_btn.click()
            time.sleep(3)
            s = save_screenshot(page, "07-post-submit")
            screenshots.append(s)
            print("Form submitted")
            return "applied"
    except Exception as e:
        print(f"Error filling HubSpot form: {e}")
        s = save_screenshot(page, "error")
        screenshots.append(s)
        return "failed"

def fill_form_main_page(page, screenshots):
    """Try to fill form directly on main page."""
    print("Attempting to fill form on main page...")

    try:
        # Look for any input fields
        inputs = page.locator("input:visible, textarea:visible")
        input_count = inputs.count()
        print(f"Found {input_count} visible inputs")

        for i in range(input_count):
            inp = inputs.nth(i)
            name = inp.get_attribute("name") or ""
            input_type = inp.get_attribute("type") or "text"
            placeholder = inp.get_attribute("placeholder") or ""
            print(f"  input[{i}]: name={name}, type={input_type}, placeholder={placeholder}")

        s = save_screenshot(page, "05-form-analysis")
        screenshots.append(s)

        # Try to scroll to find form and interact
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        # Scroll slowly looking for form
        for scroll_pos in [300, 600, 900, 1200, 1500, 1800, 2100]:
            page.evaluate(f"window.scrollTo(0, {scroll_pos})")
            time.sleep(0.5)

            # Check for visible form fields
            visible_inputs = page.locator("input[type='text']:visible, input[type='email']:visible, textarea:visible").count()
            if visible_inputs > 0:
                print(f"Found {visible_inputs} visible inputs at scroll {scroll_pos}")
                break

        s = save_screenshot(page, "06-form-found")
        screenshots.append(s)

        return "failed"  # Will be updated if form found

    except Exception as e:
        print(f"Error: {e}")
        return "failed"


if __name__ == "__main__":
    print("Starting Bright Cubes application...")
    print(f"CV: {CV_PATH}")
    print(f"URL: {JOB_URL}")

    result, screenshots = run()
    print(f"\nResult: {result}")
    print(f"Screenshots: {screenshots}")
