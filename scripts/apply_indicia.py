#!/usr/bin/env python3
"""
Apply to Indicia Junior/Medior C# .NET Developer position.
Uses Playwright to fill out and submit the application form.
"""

import asyncio
import os
import urllib.parse
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


def get_proxy_config():
    """Extract proxy config from environment."""
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    if not proxy_url:
        return None
    parsed = urllib.parse.urlparse(proxy_url)
    server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    return {
        "server": server,
        "username": parsed.username or "",
        "password": parsed.password or "",
    }


async def take_screenshot(page, name, timeout=20000):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOTS_DIR, f"indicia-{name}-{ts}.png")
    try:
        await page.screenshot(
            path=path,
            full_page=False,
            timeout=timeout,
            animations="disabled"
        )
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        try:
            import base64
            client = await page.context.new_cdp_session(page)
            result = await client.send("Page.captureScreenshot", {"format": "png", "fromSurface": False})
            with open(path, "wb") as f:
                f.write(base64.b64decode(result["data"]))
            print(f"CDP Screenshot saved: {path}")
            await client.detach()
            return path
        except Exception as e2:
            print(f"CDP screenshot also failed: {e2}")
            return None


async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    proxy_config = get_proxy_config()
    print(f"Proxy config: server={proxy_config['server'] if proxy_config else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--font-render-hinting=none",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
            ]
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "ignore_https_errors": True,
        }
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        # Block fonts only to speed up loading
        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_fonts)

        # Step 1: Navigate to job page
        print(f"\nNavigating to: {JOB_URL}")
        try:
            response = await page.goto(JOB_URL, wait_until="commit", timeout=60000)
            print(f"Navigation response: {response.status if response else 'no response'}")
        except Exception as e:
            print(f"Navigation warning: {e}")

        try:
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            print("DOM content loaded")
        except Exception as e:
            print(f"DOM load warning: {e}")

        await page.wait_for_timeout(3000)
        await take_screenshot(page, "01-job-page")

        try:
            title = await page.title()
            print(f"Page title: {title}")
        except Exception as e:
            print(f"Title error: {e}")

        # Step 2: Inspect input fields
        print("\nInspecting form fields...")
        try:
            inputs = await page.evaluate("""
                () => {
                    const all = document.querySelectorAll('input, textarea, select, button[type="submit"]');
                    return Array.from(all).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        className: (el.className || '').substring(0, 60),
                    }));
                }
            """)
            print(f"Found {len(inputs)} elements:")
            for el in inputs:
                print(f"  {el}")
        except Exception as e:
            print(f"Could not inspect inputs: {e}")

        # Also get the full page HTML to understand structure
        try:
            html_snippet = await page.evaluate("""
                () => {
                    const form = document.querySelector('form');
                    return form ? form.outerHTML.substring(0, 3000) : 'No form found';
                }
            """)
            print(f"\nForm HTML snippet:\n{html_snippet[:1500]}")
        except Exception as e:
            print(f"Could not get form HTML: {e}")

        # Scroll to form area
        try:
            await page.evaluate("window.scrollTo(0, 2000)")
        except Exception:
            pass
        await page.wait_for_timeout(1000)
        await take_screenshot(page, "02-scrolled-to-form")

        # Step 3: Fill form fields
        print("\nFilling form fields...")

        # Email
        for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']"]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.fill(APPLICANT["email"])
                    print(f"Filled email: {sel}")
                    break
            except Exception:
                continue

        # First name
        for sel in [
            "input[name*='voornaam']", "input[id*='voornaam']",
            "input[name*='first']", "input[id*='first']",
            "input[name*='naam']",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.fill(APPLICANT["first_name"])
                    print(f"Filled first name: {sel}")
                    break
            except Exception:
                continue

        # Last name
        for sel in [
            "input[name*='achternaam']", "input[id*='achternaam']",
            "input[name*='last']", "input[id*='last']",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.fill(APPLICANT["last_name"])
                    print(f"Filled last name: {sel}")
                    break
            except Exception:
                continue

        # Phone
        for sel in [
            "input[type='tel']",
            "input[name*='phone']", "input[name*='telefoon']",
            "input[id*='phone']", "input[id*='telefoon']",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.fill(APPLICANT["phone"])
                    print(f"Filled phone: {sel}")
                    break
            except Exception:
                continue

        await page.wait_for_timeout(500)
        await take_screenshot(page, "03-personal-fields")

        # Step 4: Upload CV
        print("\nUploading CV...")
        for sel in ["input[type='file']"]:
            try:
                loc = page.locator(sel)
                count = await loc.count()
                if count > 0:
                    print(f"Found {count} file input(s), uploading CV...")
                    await loc.first.set_input_files(CV_PATH)
                    await page.wait_for_timeout(2000)
                    print("CV uploaded")
                    break
            except Exception as e:
                print(f"CV upload failed: {e}")

        await take_screenshot(page, "04-after-cv-upload")

        # Step 5: Fill motivation/message
        print("\nFilling motivation message...")
        for sel in [
            "textarea[name*='message']", "textarea[id*='message']",
            "textarea[name*='bericht']", "textarea[id*='bericht']",
            "textarea[name*='motivatie']", "textarea[id*='motivatie']",
            "textarea",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    await loc.first.fill(MOTIVATION_MESSAGE)
                    print(f"Filled motivation: {sel}")
                    break
            except Exception:
                continue

        # Step 6: Source dropdown
        print("\nHandling source dropdown...")
        try:
            loc = page.locator("select")
            if await loc.count() > 0:
                options = await loc.first.evaluate(
                    "e => Array.from(e.options).map(o => ({value: o.value, text: o.text}))"
                )
                print(f"Dropdown options: {options}")
                for label in ["LinkedIn", "Other", "Anders", "Overig", "Google"]:
                    try:
                        await loc.first.select_option(label=label)
                        print(f"Selected: {label}")
                        break
                    except Exception:
                        continue
        except Exception as e:
            print(f"Dropdown error: {e}")

        await page.wait_for_timeout(300)
        await take_screenshot(page, "05-form-complete")

        # Step 7: Privacy checkbox
        print("\nChecking privacy checkbox...")
        for sel in [
            "input[type='checkbox'][name*='privacy']",
            "input[type='checkbox'][id*='privacy']",
            "input[type='checkbox']",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    if not await loc.first.is_checked():
                        await loc.first.check()
                        print(f"Checked privacy: {sel}")
                    break
            except Exception:
                continue

        await page.wait_for_timeout(300)

        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        except Exception:
            pass
        await page.wait_for_timeout(500)

        pre_submit_path = await take_screenshot(page, "06-pre-submit")
        print(f"Pre-submit screenshot: {pre_submit_path}")

        # Step 8: Submit
        print("\nSubmitting form...")
        submitted = False
        for sel in [
            "input[type='submit']",
            "button[type='submit']",
            ".gform_button",
            "button:has-text('Verstuur')",
            "button:has-text('Verzenden')",
            "button:has-text('Solliciteer')",
            "button:has-text('Submit')",
            "[class*='submit']",
        ]:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    print(f"Clicking submit: {sel}")
                    await loc.first.scroll_into_view_if_needed()
                    await loc.first.click()
                    submitted = True
                    break
            except Exception as e:
                print(f"Submit {sel} failed: {e}")

        if not submitted:
            print("WARNING: Submit button not found, trying JS...")
            try:
                await page.evaluate("document.querySelector('form') && document.querySelector('form').submit()")
                print("Submitted via JS")
                submitted = True
            except Exception as e:
                print(f"JS submit failed: {e}")

        await page.wait_for_timeout(5000)
        post_submit_path = await take_screenshot(page, "07-post-submit")
        print(f"Post-submit screenshot: {post_submit_path}")

        try:
            content = await page.inner_text("body")
            print(f"Page text (first 800 chars):\n{content[:800]}")
        except Exception as e:
            content = ""
            print(f"Could not get page text: {e}")

        confirmed = any(word in content.lower() for word in [
            "bedankt", "thank", "ontvangen", "verzonden", "success",
            "confirmation", "bevestiging", "gelukt"
        ])

        if confirmed:
            print("\nSUCCESS: Application submitted and confirmed!")
        else:
            print("\nApplication submitted - check screenshots for confirmation.")

        final_path = await take_screenshot(page, "08-final")
        await browser.close()

        return {
            "status": "applied" if submitted else "failed",
            "pre_submit": pre_submit_path,
            "post_submit": post_submit_path,
            "final": final_path,
            "confirmed": confirmed,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal result: {result}")
