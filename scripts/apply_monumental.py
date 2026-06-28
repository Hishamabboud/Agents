"""
Apply to Monumental - Software Engineer, Full-Stack
Application URL: https://jobs.ashbyhq.com/monumental/06d447db-9dd6-412e-881e-1b4914bfb0a3/application
"""
import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

APPLY_URL = "https://jobs.ashbyhq.com/monumental/06d447db-9dd6-412e-881e-1b4914bfb0a3/application"
JOB_URL = "https://jobs.ashbyhq.com/monumental/06d447db-9dd6-412e-881e-1b4914bfb0a3"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/monumental-fullstack-engineer.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

with open(COVER_LETTER_PATH, "r") as f:
    COVER_LETTER_TEXT = f.read()


async def take_screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"monumental-{name}-{TIMESTAMP}.png")
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path


async def main():
    screenshots = []
    status = "failed"
    notes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            ignore_https_errors=True,
        )
        page = await context.new_page()

        try:
            print(f"Navigating to: {APPLY_URL}")
            await page.goto(APPLY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            s = await take_screenshot(page, "01-initial-load")
            screenshots.append(s)

            # Log page title
            title = await page.title()
            print(f"Page title: {title}")

            # Check what's on the page
            content = await page.content()
            print(f"Page content length: {len(content)}")

            # Look for form fields - Ashby uses specific data-testid or label patterns
            # Try to find input fields
            inputs = await page.query_selector_all("input, textarea, select")
            print(f"Found {len(inputs)} input/textarea/select elements")

            for inp in inputs:
                try:
                    tag = await inp.evaluate("el => el.tagName")
                    name = await inp.get_attribute("name") or ""
                    placeholder = await inp.get_attribute("placeholder") or ""
                    input_type = await inp.get_attribute("type") or ""
                    label = await inp.get_attribute("aria-label") or ""
                    print(f"  {tag} name={name} type={input_type} placeholder={placeholder} label={label}")
                except Exception:
                    pass

            # Try filling name fields
            # Ashby typically has: First Name, Last Name, Email, Phone, LinkedIn, Resume upload
            # and possibly a cover letter textarea or file upload

            # Fill First Name
            first_name_selectors = [
                "input[name='firstName']",
                "input[placeholder*='First']",
                "input[placeholder*='first']",
                "[data-testid='firstName'] input",
                "input[id*='firstName']",
                "input[id*='first']",
            ]
            filled_first = False
            for sel in first_name_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["first_name"])
                        print(f"Filled first name via: {sel}")
                        filled_first = True
                        break
                except Exception:
                    pass

            # Fill Last Name
            last_name_selectors = [
                "input[name='lastName']",
                "input[placeholder*='Last']",
                "input[placeholder*='last']",
                "[data-testid='lastName'] input",
                "input[id*='lastName']",
                "input[id*='last']",
            ]
            filled_last = False
            for sel in last_name_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["last_name"])
                        print(f"Filled last name via: {sel}")
                        filled_last = True
                        break
                except Exception:
                    pass

            # Fill Email
            email_selectors = [
                "input[name='email']",
                "input[type='email']",
                "input[placeholder*='Email']",
                "input[placeholder*='email']",
                "[data-testid='email'] input",
            ]
            filled_email = False
            for sel in email_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["email"])
                        print(f"Filled email via: {sel}")
                        filled_email = True
                        break
                except Exception:
                    pass

            # Fill Phone
            phone_selectors = [
                "input[name='phone']",
                "input[type='tel']",
                "input[placeholder*='Phone']",
                "input[placeholder*='phone']",
                "[data-testid='phone'] input",
            ]
            for sel in phone_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["phone"])
                        print(f"Filled phone via: {sel}")
                        break
                except Exception:
                    pass

            # LinkedIn URL
            linkedin_selectors = [
                "input[name='linkedin']",
                "input[placeholder*='LinkedIn']",
                "input[placeholder*='linkedin']",
                "input[name*='linkedin']",
                "input[id*='linkedin']",
            ]
            for sel in linkedin_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["linkedin"])
                        print(f"Filled LinkedIn via: {sel}")
                        break
                except Exception:
                    pass

            # GitHub URL
            github_selectors = [
                "input[name='github']",
                "input[placeholder*='GitHub']",
                "input[placeholder*='github']",
                "input[name*='github']",
                "input[id*='github']",
            ]
            for sel in github_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(CANDIDATE["github"])
                        print(f"Filled GitHub via: {sel}")
                        break
                except Exception:
                    pass

            # Cover letter textarea
            cover_letter_selectors = [
                "textarea[name='coverLetter']",
                "textarea[name*='cover']",
                "textarea[placeholder*='cover']",
                "textarea[placeholder*='Cover']",
                "[data-testid*='cover'] textarea",
            ]
            for sel in cover_letter_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        await el.fill(COVER_LETTER_TEXT[:3000])
                        print(f"Filled cover letter via: {sel}")
                        break
                except Exception:
                    pass

            # Upload resume
            resume_selectors = [
                "input[type='file'][name='resume']",
                "input[type='file'][name*='resume']",
                "input[type='file'][name*='cv']",
                "input[type='file']",
            ]
            for sel in resume_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.set_input_files(RESUME_PATH)
                        print(f"Uploaded resume via: {sel}")
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    print(f"Resume upload error with {sel}: {e}")

            await asyncio.sleep(2)
            s = await take_screenshot(page, "02-form-filled")
            screenshots.append(s)

            # Look at the actual visible text on page to understand the form better
            visible_text = await page.evaluate("() => document.body.innerText")
            print("\n--- PAGE TEXT (first 2000 chars) ---")
            print(visible_text[:2000])
            print("---\n")

            notes.append(f"Page title: {title}")
            notes.append(f"Form fields found: {len(inputs)}")
            notes.append(f"Filled first name: {filled_first}")
            notes.append(f"Filled last name: {filled_last}")
            notes.append(f"Filled email: {filled_email}")

            # Try to find and click submit button
            submit_selectors = [
                "button[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Send')",
                "[data-testid='submit']",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2000)
                    if el:
                        is_visible = await el.is_visible()
                        is_enabled = await el.is_enabled()
                        btn_text = await el.inner_text()
                        print(f"Found submit button: '{btn_text}' visible={is_visible} enabled={is_enabled}")
                        if is_visible and is_enabled:
                            s = await take_screenshot(page, "03-pre-submit")
                            screenshots.append(s)
                            await el.click()
                            await asyncio.sleep(3)
                            s = await take_screenshot(page, "04-post-submit")
                            screenshots.append(s)
                            post_text = await page.evaluate("() => document.body.innerText")
                            print("\n--- POST SUBMIT TEXT ---")
                            print(post_text[:1000])
                            print("---")
                            if any(word in post_text.lower() for word in ["thank", "received", "submitted", "success", "confirmation"]):
                                status = "applied"
                                notes.append("Submit clicked - confirmation detected")
                            else:
                                notes.append(f"Submit clicked - post-submit text: {post_text[:200]}")
                            submitted = True
                            break
                except Exception as e:
                    print(f"Submit error with {sel}: {e}")

            if not submitted:
                notes.append("Could not find or click submit button")

        except Exception as e:
            notes.append(f"Exception: {str(e)}")
            print(f"Error: {e}")
            try:
                s = await take_screenshot(page, "error")
                screenshots.append(s)
            except Exception:
                pass

        finally:
            await browser.close()

    return {
        "status": status,
        "screenshots": screenshots,
        "notes": " | ".join(notes),
    }


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
