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

async def safe_screenshot(page, label):
    """Take a screenshot with a timeout, ignoring font loading issues."""
    path = screenshot_path(label)
    try:
        await page.screenshot(path=path, full_page=True, timeout=10000)
        print(f"Screenshot saved: {label}")
    except Exception as e:
        print(f"Screenshot failed ({label}): {e}")
        try:
            # Try without full_page
            await page.screenshot(path=path, timeout=10000)
            print(f"Screenshot saved (partial): {label}")
        except Exception as e2:
            print(f"Screenshot completely failed ({label}): {e2}")
    return path

async def run():
    notes = []
    status = "failed"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--font-render-hinting=none"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Set a default navigation timeout
        page.set_default_navigation_timeout(30000)
        page.set_default_timeout(15000)

        try:
            # Step 1: Navigate to ChipSoft vacatures page
            print("Navigating to ChipSoft vacatures page...")
            try:
                await page.goto("https://www.chipsoft.nl/vacatures", timeout=30000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Navigation warning (continuing): {e}")

            await asyncio.sleep(3)
            await safe_screenshot(page, "01-vacatures-page")

            title = await page.title()
            url = page.url
            print(f"Page title: {title}")
            print(f"Page URL: {url}")
            notes.append(f"Navigated to ChipSoft vacatures page. Title: {title}")

            # Get page text to analyze
            try:
                page_text = await page.evaluate("document.body.innerText")
                print(f"Page text preview (first 500 chars): {page_text[:500]}")
            except Exception as e:
                print(f"Could not get page text: {e}")
                page_text = ""

            # Step 2: Find the .NET Developer vacancy
            print("\nLooking for .NET developer vacancy...")
            clicked = False

            # Try various selectors for .NET developer links
            link_selectors = [
                "a:has-text('.NET Developer')",
                "a:has-text('NET Developer')",
                "a:has-text('.NET developer')",
                "a:has-text('Software Developer')",
                "a:has-text('Developer')",
                "a:has-text('Ontwikkelaar')",
            ]

            for selector in link_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for el in elements:
                            text = await el.inner_text()
                            href = await el.get_attribute("href") or ""
                            print(f"Found link: '{text.strip()}' -> {href}")
                        # Click the first relevant one
                        await elements[0].click()
                        await asyncio.sleep(2)
                        await safe_screenshot(page, "02-vacancy-clicked")
                        notes.append(f"Clicked vacancy link: {await elements[0].inner_text()}")
                        clicked = True
                        break
                except Exception as e:
                    print(f"Selector '{selector}' error: {e}")

            # If no link found, get all links and display them
            if not clicked:
                print("\nNo direct match found. Listing all links on page...")
                try:
                    all_links = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('a')).map(a => ({
                            text: a.innerText.trim(),
                            href: a.href,
                            classes: a.className
                        })).filter(l => l.text.length > 0)
                    """)
                    print(f"Total links found: {len(all_links)}")
                    for link in all_links[:50]:
                        print(f"  Link: '{link['text']}' -> {link['href']}")

                    # Find .NET related links
                    net_links = [l for l in all_links if any(
                        kw in l['text'].lower() or kw in l['href'].lower()
                        for kw in ['.net', 'developer', 'software', 'ontwikkel', 'programmer', 'dotnet']
                    )]
                    print(f"\n.NET/Developer related links: {len(net_links)}")
                    for link in net_links:
                        print(f"  -> '{link['text']}' : {link['href']}")

                    if net_links:
                        # Navigate directly to the first relevant link
                        target_url = net_links[0]['href']
                        print(f"\nNavigating directly to: {target_url}")
                        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                        await safe_screenshot(page, "02-vacancy-direct")
                        notes.append(f"Navigated directly to vacancy: {net_links[0]['text']}")
                        clicked = True
                except Exception as e:
                    print(f"Error listing links: {e}")

            # Step 3: If still no vacancy page, try searching
            if not clicked:
                print("\nTrying to find a search or filter mechanism...")
                try:
                    # Look for search input
                    search_inputs = await page.query_selector_all("input[type='text'], input[type='search'], input[placeholder]")
                    for inp in search_inputs:
                        placeholder = await inp.get_attribute("placeholder") or ""
                        name = await inp.get_attribute("name") or ""
                        print(f"  Input: placeholder='{placeholder}', name='{name}'")

                    # Try a direct URL approach for the vacancy
                    print("Trying direct vacancy search URL...")
                    direct_urls = [
                        "https://www.chipsoft.nl/vacatures?q=.NET",
                        "https://www.chipsoft.nl/vacatures?search=developer",
                        "https://www.chipsoft.nl/vacatures/net-developer",
                        "https://www.chipsoft.nl/vacatures/software-developer",
                    ]
                    for direct_url in direct_urls:
                        try:
                            await page.goto(direct_url, timeout=20000, wait_until="domcontentloaded")
                            await asyncio.sleep(2)
                            page_text = await page.evaluate("document.body.innerText")
                            if any(kw in page_text.lower() for kw in ['.net', 'developer', 'sollicit']):
                                await safe_screenshot(page, "02-search-url")
                                notes.append(f"Found relevant content at: {direct_url}")
                                clicked = True
                                break
                        except Exception as e:
                            print(f"URL {direct_url} failed: {e}")
                except Exception as e:
                    print(f"Search attempt failed: {e}")

            print(f"\nCurrent URL: {page.url}")
            await safe_screenshot(page, "03-current-state")

            # Step 4: Look for Apply/Solliciteer button
            print("\nLooking for Apply/Solliciteer button...")
            apply_button = None

            apply_selectors = [
                "a:has-text('Solliciteer')",
                "button:has-text('Solliciteer')",
                "a:has-text('Solliciteren')",
                "button:has-text('Solliciteren')",
                "a:has-text('Nu solliciteren')",
                "a:has-text('Apply')",
                "button:has-text('Apply')",
                "a[href*='sollicit']",
                "a[href*='apply']",
                "[class*='apply']",
                "[class*='sollicit']",
                "a:has-text('Stuur je sollicitatie')",
                "a:has-text('Reageer')",
            ]

            for selector in apply_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        try:
                            text = await element.inner_text()
                        except:
                            text = selector
                        href = await element.get_attribute("href") or ""
                        print(f"Found apply element: '{text}' -> {href}")
                        apply_button = element
                        break
                except Exception as e:
                    continue

            if apply_button:
                print("Clicking apply button...")
                try:
                    await apply_button.click()
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"Click failed, trying href navigation: {e}")
                    href = await apply_button.get_attribute("href")
                    if href:
                        await page.goto(href, timeout=20000, wait_until="domcontentloaded")
                        await asyncio.sleep(2)

                await safe_screenshot(page, "04-apply-form")
                notes.append("Clicked apply button")
                print(f"Now on: {page.url}")

                # Check for CAPTCHA
                page_content_lower = (await page.evaluate("document.body.innerText")).lower()
                if "captcha" in page_content_lower or "robot" in page_content_lower:
                    notes.append("CAPTCHA detected - cannot proceed automatically.")
                    status = "failed"
                    print("CAPTCHA detected!")
                elif "inloggen" in page_content_lower or "account aanmaken" in page_content_lower or "registreer" in page_content_lower:
                    notes.append("Application requires account login/creation - skipping.")
                    status = "skipped"
                    print("Account required!")
                else:
                    # Try to fill the form
                    print("Attempting to fill the application form...")
                    form_filled = False

                    # Get all form fields
                    try:
                        form_fields = await page.evaluate("""
                            () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                                type: el.type,
                                name: el.name,
                                id: el.id,
                                placeholder: el.placeholder,
                                className: el.className,
                                required: el.required
                            }))
                        """)
                        print(f"Found {len(form_fields)} form fields:")
                        for field in form_fields:
                            print(f"  {field}")
                    except Exception as e:
                        print(f"Could not enumerate form fields: {e}")
                        form_fields = []

                    # Fill first name
                    for sel in ["input[name*='voornaam']", "input[name*='firstname']", "input[name*='first_name']",
                                "input[id*='voornaam']", "input[id*='firstname']", "input[placeholder*='voornaam']",
                                "input[placeholder*='Voornaam']", "#firstname", "#voornaam"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(APPLICANT["first_name"])
                                print(f"Filled first name: {sel}")
                                form_filled = True
                                break
                        except Exception as e:
                            pass

                    # Fill last name
                    for sel in ["input[name*='achternaam']", "input[name*='lastname']", "input[name*='last_name']",
                                "input[id*='achternaam']", "input[id*='lastname']", "input[placeholder*='achternaam']",
                                "input[placeholder*='Achternaam']", "#lastname", "#achternaam"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(APPLICANT["last_name"])
                                print(f"Filled last name: {sel}")
                                form_filled = True
                                break
                        except Exception as e:
                            pass

                    # Fill full name if separate first/last not found
                    for sel in ["input[name*='naam']", "input[name='name']", "input[id*='naam']",
                                "input[placeholder*='naam']", "input[placeholder*='Naam']", "#name"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(APPLICANT["name"])
                                print(f"Filled full name: {sel}")
                                form_filled = True
                                break
                        except Exception as e:
                            pass

                    # Fill email
                    for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']",
                                "input[placeholder*='email']", "input[placeholder*='Email']", "#email"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(APPLICANT["email"])
                                print(f"Filled email: {sel}")
                                form_filled = True
                                break
                        except Exception as e:
                            pass

                    # Fill phone
                    for sel in ["input[type='tel']", "input[name*='phone']", "input[name*='telefoon']",
                                "input[id*='phone']", "input[id*='telefoon']", "input[placeholder*='telefoon']",
                                "input[placeholder*='Telefoon']", "#phone", "#telefoon"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                await el.fill(APPLICANT["phone"])
                                print(f"Filled phone: {sel}")
                                form_filled = True
                                break
                        except Exception as e:
                            pass

                    await safe_screenshot(page, "05-form-filled")

                    # Try to upload resume
                    file_inputs = await page.query_selector_all("input[type='file']")
                    print(f"Found {len(file_inputs)} file input(s)")
                    if file_inputs and os.path.exists(RESUME_PATH):
                        try:
                            await file_inputs[0].set_input_files(RESUME_PATH)
                            print(f"Uploaded resume from: {RESUME_PATH}")
                            notes.append("Resume uploaded successfully")
                            form_filled = True
                        except Exception as e:
                            print(f"File upload failed: {e}")

                    await safe_screenshot(page, "06-before-submit")

                    if form_filled:
                        notes.append("Application form filled with personal details")

                        # Find submit button
                        submit_button = None
                        for sel in [
                            "button[type='submit']", "input[type='submit']",
                            "button:has-text('Verzenden')", "button:has-text('Versturen')",
                            "button:has-text('Solliciteer')", "button:has-text('Submit')",
                            "button:has-text('Send')", "a:has-text('Verzenden')",
                            "[class*='submit']"
                        ]:
                            try:
                                el = await page.query_selector(sel)
                                if el:
                                    try:
                                        text = await el.inner_text()
                                    except:
                                        text = sel
                                    print(f"Found submit button: '{text}'")
                                    submit_button = el
                                    break
                            except Exception as e:
                                pass

                        if submit_button:
                            print("Submitting application...")
                            await submit_button.click()
                            await asyncio.sleep(4)
                            await safe_screenshot(page, "07-post-submit")

                            # Check for success message
                            page_text_after = (await page.evaluate("document.body.innerText")).lower()
                            success_keywords = ["bedankt", "thank you", "ontvangen", "bevestiging", "verstuurd", "succesvol"]
                            if any(kw in page_text_after for kw in success_keywords):
                                notes.append("Application submitted successfully - confirmation message found")
                                status = "applied"
                                print("APPLICATION SUBMITTED SUCCESSFULLY!")
                            else:
                                notes.append("Form submitted but no clear confirmation message")
                                status = "applied"
                                print("Form submitted (no confirmation message detected)")
                        else:
                            notes.append("Could not find submit button")
                            status = "failed"
                            print("No submit button found")
                    else:
                        notes.append("Could not fill form - no recognizable fields found")
                        status = "failed"
                        print("Could not fill any form fields")
            else:
                # No apply button found
                print("\nNo apply button found. Analyzing page...")
                try:
                    page_text_lower = (await page.evaluate("document.body.innerText")).lower()
                    all_links_info = await page.evaluate("""
                        () => Array.from(document.querySelectorAll('a')).map(a => ({
                            text: a.innerText.trim().substring(0, 100),
                            href: a.href
                        })).filter(l => l.text.length > 2)
                    """)
                    print(f"All links on current page ({len(all_links_info)}):")
                    for l in all_links_info[:30]:
                        print(f"  '{l['text']}' -> {l['href']}")

                    if "captcha" in page_text_lower:
                        notes.append("CAPTCHA on page - skipping")
                        status = "failed"
                    elif "inloggen" in page_text_lower or "aanmelden" in page_text_lower:
                        notes.append("Login required to apply - skipping")
                        status = "skipped"
                    else:
                        notes.append(f"No apply button found on page: {page.url}")
                        status = "failed"
                except Exception as e:
                    notes.append(f"Error analyzing page: {e}")
                    status = "failed"

        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            notes.append(f"Unexpected error: {str(e)}")
            status = "failed"
            await safe_screenshot(page, "error")

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
    except Exception as e:
        print(f"Could not load applications.json: {e}")
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
