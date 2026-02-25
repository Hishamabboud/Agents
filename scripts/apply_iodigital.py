#!/usr/bin/env python3
"""
Apply to iO Digital .NET Developer position.
"""

import time
import json
import os
from datetime import date
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"

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

MOTIVATION = """Als .NET developer met professionele ervaring bij Actemium (VINCI Energies) - waar ik dagelijks .NET/C# applicaties bouw voor Manufacturing Execution Systems - zie ik een uitstekende match met deze rol bij iO Digital.

Mijn achtergrond omvat: REST API ontwikkeling met ASP.NET, VB-naar-C# migratie bij Delta Electronics, Azure cloud-omgevingen via ASML-stage, en een BSc Software Engineering van Fontys Eindhoven.

Ik werk graag in een agile team aan uitdagende digitale oplossingen voor diverse klanten, en combineer technische diepgang met klantgerichte communicatie. Den Bosch is uitstekend bereikbaar vanuit Eindhoven."""

MOTIVATION_EN = """As a .NET developer with professional experience at Actemium (VINCI Energies) — where I build .NET/C# applications daily for Manufacturing Execution Systems — I see an excellent match with this role at iO Digital.

My background includes: REST API development with ASP.NET, VB-to-C# migration at Delta Electronics, Azure cloud environments via ASML internship, and a BSc Software Engineering from Fontys Eindhoven.

I enjoy working in an agile team on challenging digital solutions for diverse clients, combining technical depth with client-focused communication. Den Bosch is easily reachable from Eindhoven."""

JOB_URLS_TO_TRY = [
    "https://www.iodigital.com/nl/carriere/vacatures/net-developer-5",
    "https://www.iodigital.com/nl/carriere/vacatures/net-developer-6",
    "https://www.iodigital.com/nl/carriere/vacatures/net-developer-4",
    "https://www.iodigital.com/nl/carriere/vacatures/net-engineer",
    "https://www.iodigital.com/nl/carriere/vacatures/software-engineer",
    "https://www.iodigital.com/en/careers/jobs/net-developer",
    "https://www.iodigital.com/en/careers/jobs/net-developer-5",
]

def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/iodigital-{name}.png"
    page.screenshot(path=path, full_page=False)
    print(f"Screenshot: {path}")
    return path

def run():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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

        # Step 1: Find the working job URL
        working_url = None
        for url in JOB_URLS_TO_TRY:
            print(f"Trying URL: {url}")
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(3)
                title = page.title()
                current_url = page.url()
                print(f"  Status: {response.status() if response else 'N/A'}, Title: {title}")

                # Check if it's actually a job page (not 404)
                content = page.content()
                if "page not found" not in title.lower() and "404" not in title and "not found" not in content.lower()[:500]:
                    working_url = current_url
                    print(f"  Found working URL: {working_url}")
                    break
                else:
                    print(f"  Page is 404/not found")
            except Exception as e:
                print(f"  Error: {e}")

        if not working_url:
            # Try the main vacancies page and search
            print("No direct URL worked. Trying careers page...")
            page.goto("https://www.iodigital.com/nl/carriere/vacatures", wait_until="domcontentloaded", timeout=20000)
            time.sleep(5)
            screenshot(page, "02-careers-page")

            # Look for .NET developer
            content = page.content()
            print(f"Careers page title: {page.title()}")
            print(f"Content length: {len(content)}")

            # Try to find and click on .NET Developer vacancy
            net_selectors = [
                "text=.NET Developer",
                "text=NET Developer",
                "a[href*='net-developer']",
                "a[href*='net-engineer']",
                "a[href*='software-engineer']",
            ]

            for sel in net_selectors:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        print(f"Found element: {sel}")
                        element.click()
                        time.sleep(3)
                        working_url = page.url()
                        print(f"Navigated to: {working_url}")
                        break
                except Exception as e:
                    print(f"Selector {sel} failed: {e}")

        # Take screenshot of current state
        screenshot(page, "01-job-page")
        print(f"Current URL: {page.url()}")
        print(f"Page title: {page.title()}")

        # Step 2: Look for Apply/Solliciteer button
        apply_clicked = False
        apply_selectors = [
            "text=Solliciteer",
            "text=Solliciteer nu",
            "text=Apply",
            "text=Apply now",
            "a[href*='apply']",
            "a[href*='solliciteer']",
            "button:has-text('Solliciteer')",
            "button:has-text('Apply')",
            "[data-testid*='apply']",
            "a.apply",
            ".apply-button",
            ".cta-apply",
        ]

        for sel in apply_selectors:
            try:
                elements = page.locator(sel)
                count = elements.count()
                if count > 0:
                    print(f"Found apply button with: {sel} ({count} elements)")
                    elements.first.click()
                    time.sleep(3)
                    apply_clicked = True
                    break
            except Exception as e:
                print(f"Selector {sel}: {e}")

        screenshot(page, "03-after-apply-click")
        print(f"After apply click - URL: {page.url()}")

        # Step 3: Check if we're on a form page or redirected somewhere
        current_url = page.url()
        page_content = page.content()

        # Check if there's an iframe (Workable, Greenhouse, etc.)
        iframes = page.frames
        print(f"Number of frames: {len(iframes)}")
        for i, frame in enumerate(iframes):
            print(f"Frame {i}: {frame.url}")

        # Try to fill form fields
        form_found = False

        # Common form field selectors
        form_fields = {
            "first_name": ["input[name*='first']", "input[id*='first']", "input[placeholder*='Voornaam']", "input[placeholder*='First']", "#firstname", "#first_name"],
            "last_name": ["input[name*='last']", "input[id*='last']", "input[placeholder*='Achternaam']", "input[placeholder*='Last']", "#lastname", "#last_name"],
            "email": ["input[type='email']", "input[name*='email']", "input[id*='email']", "input[placeholder*='mail']"],
            "phone": ["input[type='tel']", "input[name*='phone']", "input[name*='tel']", "input[id*='phone']", "input[placeholder*='Telefoon']"],
        }

        # Try filling in main page
        for field_name, selectors in form_fields.items():
            value = APPLICANT.get(field_name, "")
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.fill(value)
                        print(f"Filled {field_name} with: {value}")
                        form_found = True
                        break
                except Exception as e:
                    pass

        if form_found:
            screenshot(page, "04-form-filling")

        # Try uploading CV
        try:
            file_inputs = page.locator("input[type='file']")
            count = file_inputs.count()
            print(f"File inputs found: {count}")
            if count > 0:
                file_inputs.first.set_input_files(CV_PATH)
                print(f"CV uploaded: {CV_PATH}")
                time.sleep(2)
                screenshot(page, "05-cv-uploaded")
        except Exception as e:
            print(f"CV upload error: {e}")

        # Try filling motivation/cover letter
        try:
            text_areas = page.locator("textarea")
            count = text_areas.count()
            print(f"Textareas found: {count}")
            if count > 0:
                text_areas.first.fill(MOTIVATION)
                print("Motivation filled")
                screenshot(page, "06-motivation-filled")
        except Exception as e:
            print(f"Motivation error: {e}")

        # Pre-submit screenshot
        screenshot(page, "07-pre-submit")

        # Get page source for analysis
        with open(f"{SCREENSHOT_DIR}/iodigital-page-state.html", "w") as f:
            f.write(page.content())
        print(f"Page HTML saved")

        browser.close()

        return {
            "url": working_url or JOB_URLS_TO_TRY[0],
            "form_found": form_found,
            "apply_clicked": apply_clicked,
        }

if __name__ == "__main__":
    result = run()
    print(f"\nResult: {result}")
