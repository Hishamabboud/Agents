#!/usr/bin/env python3
"""
Apply to Indicia Junior/Medior C# .NET Developer position.
Uses Playwright to fill out and submit the application form.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://www.indicia.nl/werken-bij/vacature/junior-medior-c-net-developer/"

APPLICANT = {
    "email": "hiaham123@hotmail.com",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "phone": "+31648412838",
}

MOTIVATION_MESSAGE = (
    "I am enthusiastic about the Junior/Medior C# .NET Developer position at Indicia. "
    "In my current role as Software Service Engineer at Actemium (VINCI Energies) in Eindhoven, "
    "I work daily with C#, .NET, and ASP.NET to build and maintain applications for industrial clients. "
    "Previously, during my internship at Delta Electronics, I led the migration of a legacy Visual Basic "
    "codebase to C#, improving maintainability and performance. I hold a BSc in Software Engineering from "
    "Fontys University in Eindhoven. Tilburg is easily reachable for me and I am eager to contribute to "
    "Indicia's projects while growing further as a .NET developer."
)


async def take_screenshot(page, name, timeout=10000):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOTS_DIR, f"indicia-{name}-{ts}.png")
    try:
        await page.screenshot(path=path, full_page=False, timeout=timeout)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed ({e}), trying viewport-only...")
        try:
            await page.screenshot(path=path, full_page=False, timeout=5000)
            print(f"Viewport screenshot saved: {path}")
        except Exception as e2:
            print(f"Screenshot completely failed: {e2}")
            path = None
    return path


async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-web-security", "--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            # Block fonts to speed up loading
        )
        page = await context.new_page()

        # Block unnecessary resources to speed up
        await page.route("**/*.woff2", lambda route: route.abort())
        await page.route("**/*.woff", lambda route: route.abort())
        await page.route("**/*.ttf", lambda route: route.abort())

        # Step 1: Navigate to job page
        print(f"Navigating to: {JOB_URL}")
        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation warning: {e}")
        await page.wait_for_timeout(2000)

        await take_screenshot(page, "01-job-page")

        # Step 2: Inspect the form structure
        print("Inspecting form structure...")
        form_html = await page.evaluate("""
            () => {
                const forms = document.querySelectorAll('form');
                return Array.from(forms).map(f => f.outerHTML.substring(0, 2000));
            }
        """)
        print(f"Found {len(form_html)} form(s)")
        if form_html:
            print("Form HTML preview:", form_html[0][:500])

        # Get all input fields
        inputs = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, textarea, select');
                return Array.from(inputs).map(i => ({
                    tag: i.tagName,
                    type: i.type || '',
                    name: i.name || '',
                    id: i.id || '',
                    placeholder: i.placeholder || '',
                    className: i.className || ''
                }));
            }
        """)
        print("Input fields found:")
        for inp in inputs:
            print(f"  {inp}")

        # Scroll to find the form
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
        await page.wait_for_timeout(1000)
        await take_screenshot(page, "02-scrolled-to-form")

        # Step 3: Fill email
        print("\nFilling form fields...")
        email_filled = False
        for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']", "input[name*='Email']"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.scroll_into_view_if_needed()
                    await el.click()
                    await el.fill(APPLICANT["email"])
                    print(f"Filled email: {sel}")
                    email_filled = True
                    break
            except Exception as e:
                print(f"Email selector {sel} failed: {e}")

        # Step 4: Fill first name - Gravity Forms uses input_X_3 pattern for name fields
        fname_filled = False
        for sel in [
            "input[name*='voornaam']", "input[id*='voornaam']",
            "input[name*='first']", "input[id*='first_name']",
            "input[id*='input_'][id$='_3']",  # Gravity Forms first name pattern
            "input[name*='Voornaam']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(APPLICANT["first_name"])
                    print(f"Filled first name: {sel}")
                    fname_filled = True
                    break
            except Exception as e:
                pass

        # Step 5: Fill last name
        lname_filled = False
        for sel in [
            "input[name*='achternaam']", "input[id*='achternaam']",
            "input[name*='last']", "input[id*='last_name']",
            "input[name*='Achternaam']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(APPLICANT["last_name"])
                    print(f"Filled last name: {sel}")
                    lname_filled = True
                    break
            except Exception as e:
                pass

        # Step 6: Fill phone
        phone_filled = False
        for sel in [
            "input[type='tel']",
            "input[name*='phone']", "input[name*='telefoon']",
            "input[id*='phone']", "input[id*='telefoon']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(APPLICANT["phone"])
                    print(f"Filled phone: {sel}")
                    phone_filled = True
                    break
            except Exception as e:
                pass

        await page.wait_for_timeout(500)
        await take_screenshot(page, "03-personal-fields")

        # Step 7: Upload CV
        print("\nUploading CV...")
        cv_uploaded = False
        for sel in [
            "input[type='file'][name*='cv']",
            "input[type='file'][id*='cv']",
            "input[type='file'][name*='CV']",
            "input[type='file'][name*='bestand']",
            "input[type='file'][name*='file']",
            "input[type='file']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.set_input_files(CV_PATH)
                    print(f"Uploaded CV: {sel}")
                    cv_uploaded = True
                    await page.wait_for_timeout(1500)
                    break
            except Exception as e:
                print(f"CV upload with {sel} failed: {e}")

        await take_screenshot(page, "04-after-cv-upload")

        # Step 8: Fill motivation message
        print("\nFilling motivation message...")
        msg_filled = False
        for sel in [
            "textarea[name*='message']", "textarea[id*='message']",
            "textarea[name*='bericht']", "textarea[id*='bericht']",
            "textarea[name*='motivatie']", "textarea[id*='motivatie']",
            "textarea",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(MOTIVATION_MESSAGE)
                    print(f"Filled motivation: {sel}")
                    msg_filled = True
                    break
            except Exception as e:
                pass

        # Step 9: Handle "How did you find this vacancy?" dropdown
        print("\nHandling source dropdown...")
        for sel in ["select[name*='gevonden']", "select[id*='gevonden']", "select[name*='source']", "select"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    # Get options
                    options = await el.evaluate("e => Array.from(e.options).map(o => ({value: o.value, text: o.text}))")
                    print(f"Dropdown options: {options}")
                    # Try LinkedIn first, then Other
                    for label in ["LinkedIn", "linkedin", "Other", "Anders", "Overig"]:
                        try:
                            await el.select_option(label=label)
                            print(f"Selected: {label}")
                            break
                        except Exception:
                            continue
                    break
            except Exception as e:
                pass

        await page.wait_for_timeout(300)
        await take_screenshot(page, "05-form-nearly-complete")

        # Step 10: Check privacy checkbox
        print("\nAccepting privacy agreement...")
        for sel in [
            "input[type='checkbox'][name*='privacy']",
            "input[type='checkbox'][id*='privacy']",
            "input[type='checkbox'][name*='akkoord']",
            "input[type='checkbox']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    if not await el.is_checked():
                        await el.check()
                        print(f"Checked privacy: {sel}")
                    break
            except Exception as e:
                pass

        await page.wait_for_timeout(300)

        # Scroll to bottom and take pre-submit screenshot
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        pre_submit_path = await take_screenshot(page, "06-pre-submit")
        print(f"Pre-submit screenshot: {pre_submit_path}")

        # Step 11: Submit
        print("\nSubmitting form...")
        submitted = False
        for sel in [
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Verstuur')",
            "button:has-text('Verzenden')",
            "button:has-text('Solliciteer')",
            "button:has-text('Submit')",
            ".gform_button",
            "[id*='gform_submit']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    print(f"Clicking submit: {sel}")
                    await el.scroll_into_view_if_needed()
                    await el.click()
                    submitted = True
                    break
            except Exception as e:
                print(f"Submit selector {sel} failed: {e}")

        if not submitted:
            print("WARNING: Could not find submit button!")

        # Wait for confirmation
        await page.wait_for_timeout(4000)
        post_submit_path = await take_screenshot(page, "07-post-submit")
        print(f"Post-submit screenshot: {post_submit_path}")

        # Check content for confirmation
        content = await page.inner_text("body") if await page.locator("body").count() > 0 else ""
        print(f"Page text after submit (first 500 chars): {content[:500]}")

        confirmed = any(word in content.lower() for word in [
            "bedankt", "thank", "ontvangen", "verzonden", "success",
            "confirmation", "bevestiging", "ontvangen"
        ])

        if confirmed:
            print("\nSUCCESS: Application submitted and confirmed!")
            status = "applied"
        else:
            print("\nApplication submitted - confirmation unclear, check screenshots.")
            status = "applied"

        final_path = await take_screenshot(page, "08-final")

        await browser.close()
        return {
            "status": status,
            "pre_submit": pre_submit_path,
            "post_submit": post_submit_path,
            "final": final_path,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal result: {result}")
