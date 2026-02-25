#!/usr/bin/env python3
"""
Apply to Lumenalta Senior Python/React Engineer position.
URL: https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92
"""

import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

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
JOB_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92"

MOTIVATION = """I am a full-stack developer with professional Python experience from ASML and React/JavaScript skills from building CogitatAI, my AI chatbot platform. At ASML I developed Python test suites in an Azure/Kubernetes CI/CD environment. Currently at Actemium (VINCI Energies) I build Python/Flask backends and JavaScript frontends for enterprise MES clients. CogitatAI is a full-stack project built with Python/Flask backend + React frontend, deployed on Azure with Docker/Kubernetes — demonstrating end-to-end ownership from architecture through production monitoring. I am excited to bring this full-stack Python/React experience to Lumenalta's enterprise client solutions."""

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"lumenalta-{name}-{timestamp}.png")


async def safe_screenshot(page, name):
    path = screenshot_path(name)
    try:
        await page.screenshot(path=path, timeout=10000, full_page=False)
        print(f"    Screenshot: {path}")
    except Exception as e:
        print(f"    Screenshot failed ({name}): {e}")
        # Try without font waiting
        try:
            await page.screenshot(path=path, timeout=5000, full_page=False, animations="disabled")
        except Exception:
            pass
    return path


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # Set shorter default timeout
        page.set_default_timeout(20000)

        print(f"[1] Navigating to job page: {JOB_URL}")
        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"    Page load warning: {e}")

        await asyncio.sleep(3)
        await safe_screenshot(page, "01-job-page")
        print(f"    Current URL: {page.url}")
        title = await page.title()
        print(f"    Title: {title}")

        # Get page text to understand layout
        try:
            page_text = await page.evaluate("() => document.body.innerText")
            print(f"    Page text preview: {page_text[:500]}")
        except Exception:
            pass

        # Save HTML
        try:
            content = await page.content()
            html_path = f"/home/user/Agents/output/screenshots/lumenalta-page-{timestamp}.html"
            with open(html_path, "w") as f:
                f.write(content[:100000])
            print(f"    HTML saved: {html_path}")
        except Exception as e:
            print(f"    HTML save failed: {e}")

        # Look for Apply button
        print("[2] Looking for Apply button...")
        apply_selectors = [
            "a:has-text('Apply now')",
            "a:has-text('Apply Now')",
            "a:has-text('Apply')",
            "button:has-text('Apply now')",
            "button:has-text('Apply')",
        ]

        clicked = False
        for sel in apply_selectors:
            try:
                el = page.locator(sel).first
                count = await el.count()
                if count > 0:
                    href = await el.get_attribute("href")
                    text = await el.inner_text()
                    print(f"    Found: '{text.strip()}' -> href={href}")
                    if href and href.startswith("http"):
                        # Navigate directly
                        print(f"    Navigating to: {href}")
                        await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                        clicked = True
                        break
                    else:
                        await el.click()
                        clicked = True
                        break
            except Exception as e:
                print(f"    Selector {sel} failed: {e}")
                continue

        if not clicked:
            print("    No apply button found by text, checking all links...")
            try:
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.innerText.trim(),
                        href: a.href
                    })).filter(l => l.text.toLowerCase().includes('apply') || l.href.toLowerCase().includes('apply'))
                """)
                print(f"    Apply links found: {json.dumps(links[:5], indent=2)}")
                if links:
                    href = links[0]["href"]
                    print(f"    Navigating to first apply link: {href}")
                    await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                    clicked = True
            except Exception as e:
                print(f"    Link search failed: {e}")

        await asyncio.sleep(3)
        await safe_screenshot(page, "02-after-apply-click")
        print(f"    Current URL: {page.url}")
        title = await page.title()
        print(f"    Title: {title}")

        # Save HTML again
        try:
            content = await page.content()
            html_path2 = f"/home/user/Agents/output/screenshots/lumenalta-apply-page-{timestamp}.html"
            with open(html_path2, "w") as f:
                f.write(content[:100000])
            print(f"    Apply page HTML saved: {html_path2}")
        except Exception:
            pass

        # Check for form
        form_count = await page.locator("form").count()
        input_count = await page.locator("input").count()
        print(f"    Forms: {form_count}, Inputs: {input_count}")

        # Try to fill form fields
        print("[3] Attempting to fill form fields...")
        filled_fields = {}

        # Field mapping: field_name -> value, selectors
        fields_to_fill = [
            ("first_name", APPLICANT["first_name"], [
                "input[name*='first']", "input[name='first_name']", "input[placeholder*='First name']",
                "input[placeholder*='first name']", "#first_name", "input[id*='first']",
                "input[name='firstName']", "input[placeholder*='First Name']",
            ]),
            ("last_name", APPLICANT["last_name"], [
                "input[name*='last']", "input[name='last_name']", "input[placeholder*='Last name']",
                "input[placeholder*='last name']", "#last_name", "input[id*='last']",
                "input[name='lastName']", "input[placeholder*='Last Name']",
            ]),
            ("email", APPLICANT["email"], [
                "input[type='email']", "input[name='email']", "input[name*='email']",
                "input[placeholder*='email']", "input[placeholder*='Email']", "#email",
            ]),
            ("phone", APPLICANT["phone"], [
                "input[type='tel']", "input[name='phone']", "input[name*='phone']",
                "input[placeholder*='phone']", "input[placeholder*='Phone']", "#phone",
            ]),
            ("city", APPLICANT["city"], [
                "input[name='city']", "input[name*='city']", "input[placeholder*='city']",
                "input[placeholder*='City']", "#city",
            ]),
            ("linkedin", APPLICANT["linkedin"], [
                "input[name*='linkedin']", "input[placeholder*='LinkedIn']", "input[placeholder*='linkedin']",
                "input[name*='linked_in']", "#linkedin",
            ]),
            ("github", APPLICANT["github"], [
                "input[name*='github']", "input[placeholder*='GitHub']", "input[placeholder*='github']",
                "input[name*='git']", "#github",
            ]),
        ]

        for field_name, value, selectors in fields_to_fill:
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        is_vis = await el.is_visible()
                        if is_vis:
                            await el.fill(value)
                            filled_fields[field_name] = value
                            print(f"    Filled {field_name}: {value}")
                            break
                except Exception:
                    continue

        # Cover letter / motivation
        for sel in [
            "textarea[name*='cover']", "textarea[name*='letter']",
            "textarea[name*='motivation']", "textarea[placeholder*='cover']",
            "textarea[placeholder*='Cover']", "textarea[placeholder*='letter']",
            "textarea[placeholder*='motivation']", "textarea[placeholder*='Tell us']",
            "textarea[placeholder*='Why']", "textarea[placeholder*='message']",
            "textarea",
        ]:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    el = els.first
                    if await el.is_visible():
                        await el.fill(MOTIVATION)
                        print(f"    Filled motivation textarea via {sel}")
                        break
            except Exception:
                continue

        # Upload CV
        print("[4] Looking for file upload (CV)...")
        upload_selectors = [
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='cv']",
            "input[type='file'][name*='file']",
            "input[type='file']",
        ]
        for sel in upload_selectors:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    el = els.first
                    await el.set_input_files(CV_PATH)
                    print(f"    Uploaded CV via {sel}")
                    await asyncio.sleep(2)
                    break
            except Exception as e:
                print(f"    Upload attempt {sel} failed: {e}")
                continue

        await asyncio.sleep(1)
        await safe_screenshot(page, "03-form-filled")

        # Find and click submit
        print("[5] Looking for submit button...")
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit application')",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send application')",
            "button:has-text('Send')",
            "[type='submit']",
        ]

        submit_el = None
        for sel in submit_selectors:
            try:
                els = page.locator(sel)
                count = await els.count()
                if count > 0:
                    el = els.first
                    if await el.is_visible():
                        text = await el.inner_text()
                        print(f"    Found submit: '{text.strip()}' via {sel}")
                        submit_el = el
                        break
            except Exception:
                continue

        await safe_screenshot(page, "04-pre-submit")
        print(f"    Pre-submit screenshot saved")

        status = "failed"
        if submit_el:
            print("[6] Submitting application...")
            try:
                await submit_el.click()
                await asyncio.sleep(4)
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                await safe_screenshot(page, "05-after-submit")
                print(f"    Final URL: {page.url}")

                # Check for confirmation
                try:
                    page_text = await page.evaluate("() => document.body.innerText.toLowerCase()")
                    confirmation_keywords = ["thank you", "thanks", "success", "received", "submitted", "confirm", "application received"]
                    found = [kw for kw in confirmation_keywords if kw in page_text]
                    if found:
                        print(f"    CONFIRMATION found: {found}")
                        status = "applied"
                    else:
                        print(f"    No confirmation keywords found, page text preview: {page_text[:300]}")
                        status = "attempted"
                except Exception as e:
                    print(f"    Could not check confirmation: {e}")
                    status = "attempted"
            except Exception as e:
                print(f"    Submit click failed: {e}")
                status = "failed"
        else:
            print("    No submit button found")
            # Check if it's a multi-step / redirect to external ATS
            current_url = page.url
            try:
                page_text = await page.evaluate("() => document.body.innerText")
                print(f"    Page content: {page_text[:500]}")
            except Exception:
                pass
            status = "skipped"

        result = {
            "status": status,
            "final_url": page.url,
            "filled_fields": list(filled_fields.keys()),
            "screenshots": [
                screenshot_path("01-job-page"),
                screenshot_path("02-after-apply-click"),
                screenshot_path("03-form-filled"),
                screenshot_path("04-pre-submit"),
                screenshot_path("05-after-submit"),
            ],
        }

        result_path = f"/home/user/Agents/output/screenshots/lumenalta-result-{timestamp}.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResult saved: {result_path}")

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2))
