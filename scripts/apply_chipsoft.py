#!/usr/bin/env python3
"""
Automated job application script for ChipSoft .NET Developer position.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

APPLICANT = {
    "name": "Hisham Abboud",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
    "current_role": "Software Service Engineer at Actemium (VINCI Energies)"
}

def screenshot_path(label):
    return os.path.join(SCREENSHOTS_DIR, f"chipsoft-{label}-{TIMESTAMP}.png")

async def run():
    log = []
    status = "failed"
    notes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Step 1: Navigate to ChipSoft vacatures page
            print("Navigating to ChipSoft vacatures page...")
            await page.goto("https://www.chipsoft.nl/vacatures", timeout=30000, wait_until="networkidle")
            await asyncio.sleep(2)
            await page.screenshot(path=screenshot_path("01-vacatures-page"), full_page=True)
            print(f"Screenshot saved: 01-vacatures-page")
            notes.append("Navigated to ChipSoft vacatures page successfully.")

            page_content = await page.content()
            page_text = await page.evaluate("document.body.innerText")
            print(f"Page title: {await page.title()}")
            print(f"Page URL: {page.url}")

            # Step 2: Look for .NET developer vacancy
            print("Looking for .NET developer vacancy...")

            # Try to find relevant links
            dot_net_links = await page.query_selector_all("a[href*='net'], a[href*='developer'], a[href*='NET']")
            print(f"Found {len(dot_net_links)} potential .NET/developer links")

            # Search for text containing .NET or developer
            net_elements = await page.query_selector_all("text=.NET")
            dev_elements = await page.query_selector_all("text=Developer")
            software_elements = await page.query_selector_all("text=Software")
            print(f"Found .NET text elements: {len(net_elements)}")
            print(f"Found Developer text elements: {len(dev_elements)}")
            print(f"Found Software text elements: {len(software_elements)}")

            # Try clicking on .NET Developer link if found
            clicked = False

            # Method 1: Look for exact text match
            for selector in [
                "text=.NET Developer",
                "text=NET Developer",
                "text=.NET developer",
                "text=Software Developer",
                "text=Developer"
            ]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"Found element with selector '{selector}': {text}")
                        await element.click()
                        await asyncio.sleep(2)
                        await page.screenshot(path=screenshot_path("02-vacancy-clicked"), full_page=True)
                        notes.append(f"Clicked vacancy link: {text}")
                        clicked = True
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")

            # Method 2: Look for links containing relevant keywords in href or text
            if not clicked:
                all_links = await page.query_selector_all("a")
                for link in all_links:
                    try:
                        href = await link.get_attribute("href") or ""
                        text = await link.inner_text()
                        if any(kw in text.lower() or kw in href.lower() for kw in [".net", "developer", "software"]):
                            print(f"Found relevant link: text='{text}', href='{href}'")
                            if any(kw in text.lower() for kw in [".net", "developer", "software"]):
                                await link.click()
                                await asyncio.sleep(2)
                                await page.screenshot(path=screenshot_path("02-vacancy-clicked"), full_page=True)
                                notes.append(f"Clicked vacancy: {text}")
                                clicked = True
                                break
                    except Exception as e:
                        continue

            if not clicked:
                print("Could not find a direct .NET developer link, trying search or filter...")
                # Try to find a search box or filter
                search_box = await page.query_selector("input[type='search'], input[placeholder*='zoek'], input[placeholder*='search']")
                if search_box:
                    await search_box.fill(".NET")
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                    await page.screenshot(path=screenshot_path("02-search-results"), full_page=True)
                    notes.append("Used search box to search for .NET")

            # Step 3: Take screenshot of vacancy listing
            current_url = page.url
            print(f"Current URL after navigation: {current_url}")
            await page.screenshot(path=screenshot_path("03-after-navigation"), full_page=True)

            # Step 4: Look for Apply button
            print("Looking for Apply/Solliciteer button...")
            apply_button = None
            for selector in [
                "text=Solliciteer",
                "text=Solliciteren",
                "text=Apply",
                "text=Apply Now",
                "text=Nu solliciteren",
                "a[href*='sollicit']",
                "a[href*='apply']",
                "button:has-text('Sollicit')",
                "button:has-text('Apply')",
                ".apply-button",
                ".solliciteer",
                "[class*='apply']",
                "[class*='sollicit']"
            ]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f"Found apply button with selector '{selector}': {text}")
                        apply_button = element
                        break
                except Exception as e:
                    continue

            if apply_button:
                await apply_button.click()
                await asyncio.sleep(3)
                await page.screenshot(path=screenshot_path("04-apply-form"), full_page=True)
                notes.append("Clicked apply button, on application form.")
                print(f"Now on: {page.url}")

                # Step 5: Fill out the form
                print("Attempting to fill out the form...")

                # Check for CAPTCHA first
                captcha_found = await page.query_selector(".g-recaptcha, [class*='captcha'], [id*='captcha'], iframe[src*='captcha']")
                if captcha_found:
                    notes.append("CAPTCHA detected - cannot proceed automatically.")
                    status = "failed"
                    await page.screenshot(path=screenshot_path("05-captcha-detected"), full_page=True)
                    print("CAPTCHA detected!")
                else:
                    # Try to fill form fields
                    form_filled = False

                    # Name fields
                    for selector, value in [
                        ("input[name*='naam'], input[placeholder*='naam'], input[name*='name'], input[placeholder*='name']", APPLICANT["name"]),
                        ("input[name*='voornaam'], input[placeholder*='voornaam'], input[name*='first']", APPLICANT["first_name"]),
                        ("input[name*='achternaam'], input[placeholder*='achternaam'], input[name*='last']", APPLICANT["last_name"]),
                        ("input[type='email'], input[name*='email'], input[placeholder*='email']", APPLICANT["email"]),
                        ("input[type='tel'], input[name*='phone'], input[name*='telefoon'], input[placeholder*='telefoon']", APPLICANT["phone"]),
                    ]:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.fill(value)
                                form_filled = True
                                print(f"Filled field: {selector[:50]} = {value}")
                        except Exception as e:
                            print(f"Could not fill {selector[:50]}: {e}")

                    await page.screenshot(path=screenshot_path("05-form-filled"), full_page=True)

                    # Try to upload resume
                    file_input = await page.query_selector("input[type='file']")
                    if file_input:
                        if os.path.exists(RESUME_PATH):
                            await file_input.set_input_files(RESUME_PATH)
                            print(f"Uploaded resume from: {RESUME_PATH}")
                            notes.append(f"Resume uploaded: {RESUME_PATH}")
                            form_filled = True
                        else:
                            print(f"Resume not found at: {RESUME_PATH}")

                    await page.screenshot(path=screenshot_path("06-before-submit"), full_page=True)

                    # Check if form was actually filled
                    if form_filled:
                        notes.append("Form fields filled successfully.")

                        # Look for submit button
                        submit_button = None
                        for selector in [
                            "button[type='submit']",
                            "input[type='submit']",
                            "text=Verzenden",
                            "text=Versturen",
                            "text=Submit",
                            "text=Send",
                            "text=Solliciteer",
                            "[class*='submit']"
                        ]:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    text = await element.inner_text() if await element.get_attribute("type") != "submit" else "submit"
                                    print(f"Found submit button: {selector}")
                                    submit_button = element
                                    break
                            except Exception as e:
                                continue

                        if submit_button:
                            print("Found submit button - taking pre-submit screenshot...")
                            await page.screenshot(path=screenshot_path("06-pre-submit"), full_page=True)

                            # Submit the application
                            await submit_button.click()
                            await asyncio.sleep(3)
                            await page.screenshot(path=screenshot_path("07-post-submit"), full_page=True)
                            notes.append("Form submitted.")
                            status = "applied"
                            print("Application submitted!")
                        else:
                            notes.append("Could not find submit button.")
                            status = "failed"
                    else:
                        notes.append("Could not fill form - form structure not recognized.")
                        status = "failed"
            else:
                print("No apply button found. Checking page structure...")
                # Check if there's an account requirement
                account_text = await page.evaluate("""
                    () => {
                        const body = document.body.innerText.toLowerCase();
                        const hasAccount = body.includes('account') || body.includes('inloggen') || body.includes('registreer');
                        const hasCaptcha = body.includes('captcha') || body.includes('robot');
                        return { hasAccount, hasCaptcha, url: window.location.href };
                    }
                """)
                print(f"Page analysis: {account_text}")

                if account_text.get("hasAccount"):
                    notes.append("Application requires account creation - skipping.")
                    status = "skipped"
                else:
                    notes.append("Could not find apply button on page.")
                    status = "failed"

        except Exception as e:
            print(f"Error during application: {e}")
            notes.append(f"Error: {str(e)}")
            status = "failed"
            try:
                await page.screenshot(path=screenshot_path("error"), full_page=True)
            except:
                pass

        finally:
            await browser.close()

    # Log the result
    result = {
        "id": f"chipsoft-net-developer-{TIMESTAMP}",
        "company": "ChipSoft",
        "role": ".NET Developer Zorg-ICT",
        "url": "https://www.chipsoft.nl/vacatures",
        "date_applied": datetime.now().isoformat(),
        "score": 7.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": None,
        "screenshot": screenshot_path("07-post-submit"),
        "notes": "; ".join(notes),
        "response": None
    }

    # Update applications.json
    apps_file = "/home/user/Agents/data/applications.json"
    try:
        if os.path.exists(apps_file):
            with open(apps_file, "r") as f:
                apps = json.load(f)
        else:
            apps = []
    except:
        apps = []

    apps.append(result)

    with open(apps_file, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== Application Result ===")
    print(f"Status: {status}")
    print(f"Notes: {'; '.join(notes)}")
    print(f"Logged to: {apps_file}")
    return result

if __name__ == "__main__":
    asyncio.run(run())
