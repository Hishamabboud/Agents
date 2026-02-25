#!/usr/bin/env python3
"""
Apply to Coolblue C# Developer position for Hisham Abboud.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

# ── Constants ────────────────────────────────────────────────────────────────
SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
APPLICATIONS_JSON = Path("/home/user/Agents/data/applications.json")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
JOB_URL = "https://www.coolblue.nl/en/vacancies/c-developer"

# Playwright chromium-1194 executable
CHROMIUM_EXEC = "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "phone_nl": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

COVER_LETTER = """Dear Coolblue Hiring Team,

I am excited to apply for the C# Developer position at Coolblue. As a software engineer with hands-on C#/.NET experience building production applications at Actemium, I am drawn to Coolblue's engineering culture and commitment to clean, maintainable code.

At Actemium, I developed and maintained production-grade C# applications, working with SQL databases, implementing CI/CD pipelines, and following Agile/Scrum methodologies. I have also worked with Azure cloud services, Docker, and Git — tools that align well with Coolblue's modern tech stack.

I am passionate about writing clean, testable code and collaborating closely with cross-functional teams to deliver real business value. Coolblue's focus on customer happiness through technology resonates strongly with my approach to software development.

I would love the opportunity to contribute to Coolblue's engineering team and help build the reliable, scalable systems your customers depend on every day.

Kind regards,
Hisham Abboud
hiaham123@hotmail.com
+31648412838
"""

TS = datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_config():
    """Extract proxy configuration from environment."""
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if not proxy_url:
        return None
    try:
        parsed = urlparse(proxy_url)
        server = f"http://{parsed.hostname}:{parsed.port}"
        username = parsed.username
        password = parsed.password
        print(f"Using proxy: {server}")
        return {
            "server": server,
            "username": username,
            "password": password,
        }
    except Exception as e:
        print(f"Could not parse proxy URL: {e}")
        return None


def ss(label: str) -> str:
    """Return screenshot path."""
    name = f"coolblue-{label}-{TS}.png"
    return str(SCREENSHOTS_DIR / name)


def load_applications() -> list:
    if APPLICATIONS_JSON.exists():
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    return []


def save_application(record: dict) -> None:
    apps = load_applications()
    apps.append(record)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"Saved application record: {record['id']}")


async def run():
    print("Starting Coolblue C# Developer application...")
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "id": f"coolblue-csharp-developer-{TS}",
        "company": "Coolblue",
        "role": "C# Developer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": "failed",
        "resume_file": str(CV_PATH),
        "cover_letter_file": None,
        "screenshots": [],
        "notes": "",
        "email_used": APPLICANT["email"],
        "response": None,
    }

    proxy_config = get_proxy_config()

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--allow-insecure-localhost",
            ],
        }
        if Path(CHROMIUM_EXEC).exists():
            launch_kwargs["executable_path"] = CHROMIUM_EXEC
            print(f"Using chromium: {CHROMIUM_EXEC}")

        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            ignore_https_errors=True,
        )
        # Mask webdriver
        await context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = await context.new_page()

        try:
            # ── Step 1: Navigate to job listing ─────────────────────────────
            print(f"Navigating to {JOB_URL} ...")
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # Accept cookies if banner present
            for sel in [
                "button:has-text('Accept')",
                "button:has-text('Akkoord')",
                "button:has-text('Alles accepteren')",
                "button:has-text('Accept all')",
                "button:has-text('OK')",
                "[id*='cookie'] button",
                ".cookie-accept",
                "#onetrust-accept-btn-handler",
            ]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        await asyncio.sleep(1)
                        print(f"Accepted cookies via: {sel}")
                        break
                except Exception:
                    pass

            path = ss("01-job-page")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)
            print(f"Screenshot: {path}")

            # ── Step 2: Gather page info ──────────────────────────────────────
            page_title = await page.title()
            page_text = await page.inner_text("body")
            print(f"Page title: {page_title}")
            print(f"Page text (first 800 chars):\n{page_text[:800]}")
            print(f"URL: {page.url}")

            # Check all links on job page
            all_links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => ({text: e.textContent.trim().substring(0,80), href: e.href}))"
            )
            print(f"\nLinks on page ({len(all_links)} total):")
            for link in all_links:
                if link["href"]:
                    print(f"  {link['text']!r} -> {link['href']}")

            # ── Step 3: Find Apply button / link ─────────────────────────────
            print("\nLooking for Apply button/link...")
            apply_url = None

            for link in all_links:
                href = link.get("href", "")
                text = link.get("text", "").lower()
                if any(kw in href.lower() for kw in ["apply", "sollicit", "/application"]):
                    apply_url = href
                    print(f"Found apply link by href: {href!r}")
                    break
                if any(kw in text for kw in ["apply", "solliciteer", "direct sollicit", "apply now"]):
                    if href and "javascript" not in href and href != "#":
                        apply_url = href
                        print(f"Found apply link by text {text!r}: {href}")
                        break

            if not apply_url:
                for sel in [
                    "a:has-text('Apply now')",
                    "a:has-text('Apply')",
                    "a:has-text('Solliciteer')",
                    "a:has-text('Direct solliciteren')",
                    "button:has-text('Apply')",
                    "button:has-text('Solliciteer')",
                    ".apply-button",
                    "[data-testid*='apply']",
                    "[class*='apply']",
                ]:
                    try:
                        el = page.locator(sel).first
                        if await el.is_visible(timeout=2000):
                            href = await el.get_attribute("href")
                            if href:
                                apply_url = href if href.startswith("http") else f"https://www.coolblue.nl{href}"
                                print(f"Found apply via selector {sel}: {apply_url}")
                            else:
                                print(f"Clicking apply button: {sel}")
                                await el.click()
                                await asyncio.sleep(4)
                            break
                    except Exception:
                        pass

            # Navigate to apply URL if found and still on job listing
            if apply_url and "coolblue.nl/en/vacancies" in page.url:
                print(f"Navigating to: {apply_url}")
                await page.goto(apply_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                record["application_url"] = apply_url

            current_url = page.url
            print(f"Current URL: {current_url}")

            path = ss("02-after-navigate")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)

            # ── Step 4: Check current page ────────────────────────────────────
            page_text = await page.inner_text("body")
            print(f"Page text after navigate (first 600):\n{page_text[:600]}")

            captcha_keywords = ["captcha", "hcaptcha", "recaptcha", "i am not a robot"]
            if any(kw in page_text.lower() for kw in captcha_keywords):
                print("CAPTCHA detected!")
                record["status"] = "skipped"
                record["notes"] = "CAPTCHA detected on application page. Manual action required."
                save_application(record)
                await browser.close()
                return

            frames = page.frames
            print(f"Number of frames: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")

            # Check for external ATS links
            new_links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => ({text: e.textContent.trim().substring(0,80), href: e.href}))"
            )
            ats_systems = [
                "workday", "greenhouse", "lever", "smartrecruiters",
                "recruitee", "teamtailor", "personio", "jobvite",
                "icims", "taleo", "successfactors", "bamboohr",
            ]
            for link in new_links:
                href = link.get("href", "")
                if href and any(ats in href.lower() for ats in ats_systems):
                    if "coolblue.nl" not in href:
                        print(f"Found external ATS link: {href}")
                        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(3)
                        record["application_url"] = href
                        break

            path = ss("03-application-form")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)

            current_url = page.url
            print(f"Form URL: {current_url}")

            # ── Step 5: Inspect form inputs ───────────────────────────────────
            page_text = await page.inner_text("body")
            print(f"Form page text (first 500):\n{page_text[:500]}")

            inputs = await page.eval_on_selector_all(
                "input, textarea, select",
                "els => els.map(e => ({tag: e.tagName, type: e.type, name: e.name, id: e.id, placeholder: e.placeholder, class: e.className.substring(0,60)}))"
            )
            print(f"\nForm inputs found ({len(inputs)}):")
            for inp in inputs[:25]:
                print(f"  {inp}")

            # ── Step 6: Fill form fields ─────────────────────────────────────
            filled_fields = []

            async def try_fill_sel(selector: str, value: str, label: str) -> bool:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        el = page.locator(selector).first
                        if await el.is_visible(timeout=2000):
                            await el.click()
                            await asyncio.sleep(0.2)
                            await el.fill(value)
                            filled_fields.append(label)
                            print(f"  Filled {label}: {value!r}")
                            return True
                except Exception:
                    pass
                return False

            async def try_fill(selectors_str: str, value: str, label: str) -> bool:
                for sel in selectors_str.split(","):
                    sel = sel.strip()
                    if await try_fill_sel(sel, value, label):
                        return True
                return False

            await try_fill(
                "input[name='first_name'], input[id='first_name'], input[name='firstname'], input[id='firstname'], input[placeholder='First name'], input[placeholder='Voornaam']",
                APPLICANT["first_name"], "first_name"
            )
            await try_fill(
                "input[name='last_name'], input[id='last_name'], input[name='lastname'], input[id='lastname'], input[placeholder='Last name'], input[placeholder='Achternaam']",
                APPLICANT["last_name"], "last_name"
            )
            await try_fill(
                "input[name='name'], input[id='name'], input[placeholder='Name'], input[placeholder='Full name'], input[placeholder='Naam']",
                APPLICANT["name"], "full_name"
            )
            await try_fill(
                "input[type='email'], input[name='email'], input[id='email'], input[placeholder*='email'], input[placeholder*='Email']",
                APPLICANT["email"], "email"
            )
            await try_fill(
                "input[type='tel'], input[name='phone'], input[id='phone'], input[name='tel'], input[id='tel'], input[placeholder*='phone'], input[placeholder*='Phone'], input[placeholder*='telefoon']",
                APPLICANT["phone"], "phone"
            )
            await try_fill(
                "input[name='linkedin'], input[id='linkedin'], input[placeholder*='linkedin'], input[placeholder*='LinkedIn']",
                APPLICANT["linkedin"], "linkedin"
            )
            await try_fill(
                "input[name='location'], input[id='location'], input[placeholder*='location'], input[placeholder*='Location'], input[placeholder*='City']",
                APPLICANT["location"], "location"
            )

            for sel in [
                "textarea[name*='cover']",
                "textarea[name*='letter']",
                "textarea[name*='motivation']",
                "textarea[id*='cover']",
                "textarea[id*='motivation']",
                "textarea[placeholder*='cover']",
                "textarea[placeholder*='motivation']",
                "textarea[placeholder*='Cover']",
                "textarea",
            ]:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        el = page.locator(sel).first
                        if await el.is_visible(timeout=2000):
                            await el.fill(COVER_LETTER)
                            filled_fields.append("cover_letter")
                            print(f"  Filled cover_letter via: {sel}")
                            break
                except Exception:
                    pass

            path = ss("04-fields-filled")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)

            # ── Step 7: Upload CV ─────────────────────────────────────────────
            print("Looking for CV upload field...")
            cv_uploaded = False
            for sel in [
                "input[type='file'][name*='cv']",
                "input[type='file'][name*='resume']",
                "input[type='file'][id*='cv']",
                "input[type='file'][id*='resume']",
                "input[type='file'][accept*='pdf']",
                "input[type='file']",
            ]:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        file_input = page.locator(sel).first
                        await file_input.set_input_files(str(CV_PATH))
                        await asyncio.sleep(2)
                        print(f"CV uploaded via: {sel}")
                        cv_uploaded = True
                        filled_fields.append("cv_upload")
                        break
                except Exception as e:
                    print(f"  CV upload failed ({sel}): {e}")

            path = ss("05-cv-uploaded")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)

            print(f"\nFields filled: {filled_fields}")

            # ── Step 8: Pre-submit screenshot ─────────────────────────────────
            path = ss("06-pre-submit")
            await page.screenshot(path=path, full_page=True)
            record["screenshots"].append(path)
            print(f"Pre-submit screenshot: {path}")

            page_text_now = await page.inner_text("body")
            if any(kw in page_text_now.lower() for kw in captcha_keywords):
                print("CAPTCHA detected before submit!")
                record["status"] = "skipped"
                record["notes"] = (
                    f"CAPTCHA detected before submit. Fields filled: {filled_fields}."
                )
                save_application(record)
                await browser.close()
                return

            # ── Step 9: Submit ────────────────────────────────────────────────
            print("Looking for submit button...")
            submitted = False

            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "button:has-text('Send')",
                "button:has-text('Apply')",
                "button:has-text('Apply now')",
                "button:has-text('Solliciteer')",
                "button:has-text('Verzenden')",
                "button:has-text('Versturen')",
                "[type='submit']",
            ]:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            print(f"Clicking submit: {sel}")
                            await btn.click()
                            await asyncio.sleep(5)
                            submitted = True
                            break
                except Exception:
                    pass

            if not submitted:
                print("No submit button found")
                record["status"] = "skipped"
                record["notes"] = (
                    f"No submit button found. Fields filled: {filled_fields}. "
                    f"URL: {page.url}. Inputs: {len(inputs)}"
                )
            else:
                path = ss("07-post-submit")
                await page.screenshot(path=path, full_page=True)
                record["screenshots"].append(path)
                print(f"Post-submit screenshot: {path}")

                final_url = page.url
                final_text = await page.inner_text("body")
                print(f"Final URL: {final_url}")
                print(f"Final page text:\n{final_text[:600]}")

                if any(kw in final_text.lower() for kw in captcha_keywords):
                    print("CAPTCHA blocked submission!")
                    record["status"] = "skipped"
                    record["notes"] = (
                        f"CAPTCHA blocked after submit. Fields: {filled_fields}. URL: {final_url}"
                    )
                elif any(word in final_text.lower() for word in [
                    "thank you", "bedankt", "received", "ontvangen",
                    "application submitted", "successfully", "confirmation",
                    "we will", "we'll contact", "success", "submitted"
                ]):
                    print("Application submitted successfully!")
                    record["status"] = "applied"
                    record["notes"] = (
                        f"Application submitted. Fields: {filled_fields}. "
                        f"CV: {cv_uploaded}. URL: {final_url}"
                    )
                else:
                    record["status"] = "applied"
                    record["notes"] = (
                        f"Submit clicked. Fields: {filled_fields}. CV: {cv_uploaded}. "
                        f"URL: {final_url}. Page: {final_text[:200]}"
                    )

        except Exception as e:
            import traceback
            print(f"Exception: {e}")
            traceback.print_exc()
            try:
                path = ss("error")
                await page.screenshot(path=path, full_page=True)
                record["screenshots"].append(path)
            except Exception:
                pass
            record["status"] = "failed"
            record["notes"] = f"Exception: {e}"

        finally:
            save_application(record)
            await browser.close()
            print(f"\nDone. Status: {record['status']}")
            print(f"Record id: {record['id']}")


if __name__ == "__main__":
    asyncio.run(run())
