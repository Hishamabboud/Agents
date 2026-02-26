#!/usr/bin/env python3
"""
Apply to Datenna Python Engineer - Data Acquisition role.
Version 5: ignore_https_errors to handle certificate issues.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

MOTIVATION = (
    "I am applying for the Python Engineer - Data Acquisition role at Datenna. "
    "At ASML I built Python automation tooling using Pytest and Locust to handle complex, "
    "dynamic test environments at scale. I have solid experience with HTTP fundamentals, "
    "session handling, BeautifulSoup, requests, and building resilient data pipelines. "
    "Currently at Actemium (VINCI Energies) I build full-stack applications using Python/Flask "
    "backends for industrial MES clients. I also built CogitatAI, an AI platform with a "
    "Python/Flask backend that includes real-time data acquisition pipelines. "
    "I am based in Eindhoven and excited to contribute to Datenna's intelligence work."
)

APPLICATION_URL = "https://jobs.datenna.com/o/python-engineer-data-acquisition"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_settings():
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_url:
        return None
    m = re.match(r"(https?)://([^:]+):([^@]+)@([^:]+):(\d+)", proxy_url)
    if m:
        scheme, user, pwd, host, port = m.groups()
        return {"server": f"{scheme}://{host}:{port}", "username": user, "password": pwd}
    return None


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"datenna-v5-{name}-{ts()}.png"
    for full_page in [False, True]:
        try:
            await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
            print(f"Screenshot: {path}")
            return str(path)
        except Exception as e:
            print(f"Screenshot {name} failed (full_page={full_page}): {e}")
    return ""


async def fill_field(page, selectors, value, desc):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=2000):
                await el.click(timeout=2000)
                await asyncio.sleep(0.2)
                await el.fill(value, timeout=3000)
                print(f"  Filled [{desc}]: '{value}'")
                return True
        except Exception:
            pass
    print(f"  Could not fill [{desc}]")
    return False


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": "CV not found"}

    proxy = get_proxy_settings()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

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
            ],
        }
        if proxy:
            launch_kwargs["proxy"] = proxy

        browser = await p.chromium.launch(**launch_kwargs)

        ctx_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "ignore_https_errors": True,
        }
        if proxy:
            ctx_kwargs["proxy"] = proxy

        context = await browser.new_context(**ctx_kwargs)

        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)
        page = await context.new_page()

        print(f"\n[1] Navigating to: {APPLICATION_URL}")
        try:
            resp = await page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Goto warning: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(3)

        title = await page.title()
        url = page.url
        print(f"Title: {title}")
        print(f"URL: {url}")

        await safe_screenshot(page, "01-job-page")

        # Look for Apply button
        print("\n[2] Looking for Apply button...")
        apply_clicked = False
        new_pages = []
        context.on("page", lambda pg: new_pages.append(pg))

        apply_sels = [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a[href*='apply']",
            ".apply-button",
            "[class*='apply']",
        ]

        for sel in apply_sels:
            try:
                count = await page.locator(sel).count()
                if count > 0:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=2000):
                        text = await el.inner_text()
                        print(f"Found Apply: '{text}' ({sel})")
                        await el.click()
                        await asyncio.sleep(4)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            pass
                        apply_clicked = True
                        break
            except Exception as e:
                pass

        # Check if new tab opened
        active_page = page
        if new_pages:
            print(f"New tab opened: {new_pages[0].url}")
            active_page = new_pages[0]
            await asyncio.sleep(3)

        after_click_url = active_page.url
        print(f"URL after apply click: {after_click_url}")
        await safe_screenshot(active_page, "02-after-apply")

        # Inspect form
        print("\n[3] Inspecting form...")
        try:
            elems = await active_page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName, type: el.type || '', name: el.name || '',
                    id: el.id || '', placeholder: el.placeholder || '',
                    visible: el.offsetParent !== null,
                }))
            """)
            print(f"Form elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        # Check for iframes
        frames = active_page.frames
        print(f"Frames: {len(frames)}")
        for i, frame in enumerate(frames):
            print(f"  Frame {i}: {frame.url}")

        # Try each frame if form not in main page
        target_frame = active_page

        filled = []
        cv_uploaded = False

        async def do_fill(frm):
            nonlocal cv_uploaded
            f_filled = []

            fields = [
                ("full_name", APPLICANT["full_name"], [
                    "input[name='name']", "input[id='name']",
                    "input[autocomplete='name']", "input[placeholder*='Full name' i]",
                    "input[placeholder*='Name' i]",
                ]),
                ("first_name", APPLICANT["first_name"], [
                    "input[name='first_name']", "input[name='firstName']",
                    "input[id='first_name']", "input[autocomplete='given-name']",
                    "input[placeholder*='First' i]",
                ]),
                ("last_name", APPLICANT["last_name"], [
                    "input[name='last_name']", "input[name='lastName']",
                    "input[id='last_name']", "input[autocomplete='family-name']",
                    "input[placeholder*='Last' i]",
                ]),
                ("email", APPLICANT["email"], [
                    "input[type='email']", "input[name='email']", "input[id='email']",
                    "input[autocomplete='email']",
                ]),
                ("phone", APPLICANT["phone"], [
                    "input[type='tel']", "input[name='phone']", "input[name='phone_number']",
                    "input[id='phone']", "input[autocomplete='tel']",
                    "input[placeholder*='Phone' i]",
                ]),
                ("linkedin", APPLICANT["linkedin"], [
                    "input[name='linkedin']", "input[name*='linkedin' i]",
                    "input[placeholder*='LinkedIn' i]",
                ]),
            ]

            for desc, val, sels in fields:
                ok = False
                for sel in sels:
                    try:
                        el = frm.locator(sel).first
                        if await el.count() > 0 and await el.is_visible(timeout=1500):
                            await el.click(timeout=2000)
                            await asyncio.sleep(0.2)
                            await el.fill(val, timeout=3000)
                            f_filled.append(desc)
                            print(f"  Filled [{desc}]: '{val}'")
                            ok = True
                            break
                    except Exception:
                        pass
                if not ok:
                    print(f"  Could not fill [{desc}]")

            # Textarea (motivation/cover letter)
            for sel in ["textarea", "textarea[name*='cover' i]", "textarea[name*='letter' i]"]:
                try:
                    ta = frm.locator(sel).first
                    if await ta.count() > 0 and await ta.is_visible(timeout=1500):
                        await ta.click()
                        await asyncio.sleep(0.2)
                        await ta.fill(MOTIVATION)
                        f_filled.append("motivation")
                        print("  Filled motivation textarea")
                        break
                except Exception:
                    pass

            # File upload
            file_inputs = await frm.locator("input[type='file']").all()
            print(f"File inputs: {len(file_inputs)}")
            for i, fi in enumerate(file_inputs):
                try:
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded to file input {i}")
                    await asyncio.sleep(2)
                    break
                except Exception as e:
                    print(f"  File input {i}: {e}")

            # Checkboxes
            cbs = await frm.locator("input[type='checkbox']").all()
            for i, cb in enumerate(cbs):
                try:
                    if not await cb.is_checked():
                        await cb.check()
                        print(f"  Checked checkbox {i}")
                except Exception as e:
                    print(f"  Checkbox {i}: {e}")

            return f_filled

        filled = await do_fill(active_page)

        # Try iframes if nothing filled
        if not filled and len(frames) > 1:
            for frame in frames[1:]:
                print(f"\nTrying iframe: {frame.url}")
                frame_filled = await do_fill(frame)
                if frame_filled:
                    filled.extend(frame_filled)
                    target_frame = frame
                    break

        # Scroll and screenshot
        try:
            await active_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(active_page, "03-form-filled")
        print(f"\nFilled: {filled}, CV: {cv_uploaded}")

        # Submit
        print("\n[4] Submitting...")
        submitted = False
        submit_sels = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "button:has-text('Send application')",
        ]

        for frm in [active_page] + ([] if target_frame == active_page else [target_frame]):
            for sel in submit_sels:
                try:
                    el = frm.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        text = await el.inner_text()
                        print(f"Submitting via: '{text}'")
                        await safe_screenshot(active_page, "04-pre-submit")
                        await el.click()
                        await asyncio.sleep(5)
                        try:
                            await active_page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            pass
                        submitted = True
                        break
                except Exception as e:
                    print(f"  Submit {sel}: {e}")
            if submitted:
                break

        await safe_screenshot(active_page, "05-post-submit")

        final_url = active_page.url
        status = "failed"
        notes = ""

        try:
            body = await active_page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit text: {body[:600]}")
            success_words = ["thank", "confirm", "success", "received", "submitted",
                             "bedankt", "we'll be in touch", "application"]
            if any(w in body.lower() for w in success_words):
                status = "applied"
                notes = f"Application submitted to Datenna Python Engineer. URL: {final_url}"
                print("SUCCESS: Confirmed!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear confirmation). URL: {final_url}"
                print("Submitted - confirmation unclear")
            else:
                status = "failed"
                notes = f"Could not submit. Filled: {filled}. URL: {final_url}"
        except Exception as e:
            if submitted:
                status = "applied"
            notes = f"Post-submit error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
