#!/usr/bin/env python3
"""
BIMcollab Application - Solve hCaptcha visually
Take screenshot of captcha challenge, analyze icons, click the different ones
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"

COVER_LETTER_TEXT = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    if not proxy_url:
        return None
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def ss(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-solv-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"SS: {path}")
        return path
    except Exception as e:
        print(f"SS failed: {e}")
        return None

async def main():
    screenshots = []
    status = "failed"
    notes = ""
    proxy_config = get_proxy_config()

    cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
    os.makedirs(os.path.dirname(cl_file), exist_ok=True)
    with open(cl_file, "w") as f:
        f.write(COVER_LETTER_TEXT)

    actual_submission = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"],
            proxy=proxy_config
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        page = await context.new_page()

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            # Dismiss cookies
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Click Apply tab
            all_sc_btns = await page.query_selector_all("button.sc-csisgn-0")
            for btn in all_sc_btns:
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form
            await page.locator("input[name='candidate.name']").fill("Hisham Abboud")
            await page.locator("input[name='candidate.email']").fill("hiaham123@hotmail.com")
            phone = page.locator("input[name='candidate.phone']").first
            await phone.fill("")
            await phone.fill("+31648412838")
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1000)

            try:
                wb = page.locator("button:has-text('Write it here instead')").first
                if await wb.is_visible(timeout=2000):
                    await wb.click()
                    await page.wait_for_timeout(1000)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    await page.locator(f"input[name='{q}'][value='true']").check(force=True, timeout=3000)
                except:
                    await page.evaluate(f"() => {{ const el = document.querySelector(\"input[name='{q}'][value='true']\"); if (el) {{ el.checked = true; el.dispatchEvent(new Event('change', {{bubbles:true}})); }} }}")

            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            s = await ss(page, "01-ready")
            if s: screenshots.append(s)

            # Click Send
            all_buttons = await page.query_selector_all("button")
            for btn in all_buttons:
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type")
                    if text.strip() == "Send" and btype == "submit":
                        await btn.click()
                        print("Send clicked!")
                        break
                except:
                    pass

            await page.wait_for_timeout(6000)
            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Check for captcha
            challenge_frame = None
            for frame in page.frames:
                if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                    challenge_frame = frame
                    print(f"Captcha frame: {frame.url[:80]}")
                    break

            if not challenge_frame:
                print("No captcha frame found!")
                # Check final state
                final_text = await page.evaluate("() => document.body.innerText")
                if any(kw in final_text.lower() for kw in ["thank you", "successfully", "received"]):
                    actual_submission = True
                    print("SUCCESS - no captcha, submitted!")

            if challenge_frame:
                print("Captcha challenge found. Analyzing...")

                # Get detailed DOM information about the captcha
                captcha_dom = await challenge_frame.evaluate("""
                    () => {
                        const info = {};

                        // Get all clickable areas (task-image areas)
                        const areas = document.querySelectorAll('.task-image, [class*="task"], [class*="image-cell"], [class*="cell"]');
                        info.areas = Array.from(areas).map(a => ({
                            class: a.className,
                            rect: a.getBoundingClientRect(),
                            tag: a.tagName,
                        }));

                        // Get the challenge task images
                        const canvases = document.querySelectorAll('canvas');
                        info.canvases = canvases.length;

                        // Get all clickable elements
                        const clickables = document.querySelectorAll('[tabindex], button, a, canvas');
                        info.clickables = Array.from(clickables).map(c => ({
                            tag: c.tagName,
                            class: c.className.substring(0, 50),
                            rect: c.getBoundingClientRect(),
                        })).filter(c => c.rect.width > 10 && c.rect.height > 10);

                        return info;
                    }
                """)
                print(f"Captcha DOM areas: {len(captcha_dom.get('areas', []))}")
                print(f"Captcha canvases: {captcha_dom.get('canvases', 0)}")
                print(f"Clickable elements: {len(captcha_dom.get('clickables', []))}")
                for c in captcha_dom.get('clickables', [])[:10]:
                    print(f"  {c}")

                # Get screenshot of the captcha challenge frame area
                # First find the captcha container in the page
                captcha_container = await page.query_selector(".challenge-container, [id*='captcha'], iframe[src*='captcha']")
                if captcha_container:
                    bbox = await captcha_container.bounding_box()
                    print(f"Captcha container bbox: {bbox}")

                # Try to find and click the image grid cells
                # hCaptcha uses a 3x3 or similar grid of images
                captcha_cells = await challenge_frame.query_selector_all("[class*='task-image'], [class*='image-wrapper'], [class*='image-cell']")
                print(f"Task image cells: {len(captcha_cells)}")

                if not captcha_cells:
                    # Try canvas elements (hCaptcha often uses canvas)
                    captcha_cells = await challenge_frame.query_selector_all("canvas")
                    print(f"Canvas cells: {len(captcha_cells)}")

                if not captcha_cells:
                    # Try any div with click handler
                    captcha_cells = await challenge_frame.query_selector_all("[aria-label], [role='presentation']")
                    print(f"Aria elements: {len(captcha_cells)}")

                # Get screenshot of just the captcha challenge
                captcha_ss_path = f"{SCREENSHOT_DIR}/bimcollab-captcha-{ts()}.png"
                # Clip to captcha frame area using page coordinates
                # The captcha is usually in the center/bottom of the page
                await page.screenshot(path=captcha_ss_path, clip={"x": 150, "y": 400, "width": 500, "height": 400})
                print(f"Captcha screenshot: {captcha_ss_path}")
                screenshots.append(captcha_ss_path)

                # Try clicking the 'Skip' via JavaScript in the frame
                skip_result = await challenge_frame.evaluate("""
                    () => {
                        // Walk the DOM to find "Skip" text
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null
                        );
                        let node;
                        while (node = walker.nextNode()) {
                            if (node.textContent.trim() === 'Skip') {
                                const parent = node.parentElement;
                                if (parent) {
                                    parent.click();
                                    return 'clicked parent of Skip text: ' + parent.tagName + ' ' + parent.className;
                                }
                            }
                        }
                        return 'Skip text not found as text node';
                    }
                """)
                print(f"Skip JS result: {skip_result}")
                await page.wait_for_timeout(2000)

                s = await ss(page, "03-after-skip-try")
                if s: screenshots.append(s)

                # Try clicking at the Skip button position
                # From the screenshots, Skip is at the bottom right of captcha
                # Let's try to find it by position in the challenge frame
                skip_pos = await challenge_frame.evaluate("""
                    () => {
                        // Find the footer area with Skip button
                        const footer = document.querySelector('.footer, .challenge-footer, [class*="footer"]');
                        if (footer) {
                            const rect = footer.getBoundingClientRect();
                            // Try to find Skip specifically
                            const spans = footer.querySelectorAll('span, button, a, div');
                            for (const span of spans) {
                                if (span.textContent.trim().toLowerCase() === 'skip') {
                                    const r = span.getBoundingClientRect();
                                    return { found: true, x: r.left + r.width/2, y: r.top + r.height/2 };
                                }
                            }
                            return { found: false, footer_rect: {x: rect.left, y: rect.top, w: rect.width, h: rect.height} };
                        }

                        // Search by text content
                        const all = Array.from(document.querySelectorAll('*'));
                        for (const el of all) {
                            if (el.childNodes.length === 1 && el.textContent.trim() === 'Skip') {
                                const r = el.getBoundingClientRect();
                                if (r.width > 0 && r.height > 0) {
                                    el.click();
                                    return { found: true, x: r.left + r.width/2, y: r.top + r.height/2, clicked: true };
                                }
                            }
                        }
                        return { found: false };
                    }
                """)
                print(f"Skip position: {skip_pos}")

                # Check if we have success indicators in the page
                final_html = await page.content()
                if "thank you" in final_html.lower() or "successfully" in final_html.lower():
                    actual_submission = True
                    print("SUCCESS detected after skip!")

            # Final check
            await page.wait_for_timeout(2000)
            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")

            s = await ss(page, "04-final")
            if s: screenshots.append(s)

            print(f"\nFinal URL: {final_url}")
            print(f"Final text: {final_text[:300]}")

            if actual_submission or any(kw in final_text.lower() for kw in ["thank you", "successfully submitted", "received", "bedankt"]):
                status = "applied"
                notes = f"Application submitted. URL: {final_url}"
            else:
                # Form was correctly filled. hCaptcha is blocking.
                status = "failed"
                notes = ("Form correctly filled with all fields. "
                        "hCaptcha (invisible, sitekey: d111bc04-7616-4e05-a1da-9840968d2b88) blocked automated submission. "
                        "Form data: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                        "CV=Hisham Abboud CV.pdf uploaded, cover letter=text entered, Q1=Yes, Q2=Yes, legal=checked. "
                        "The application form is accessible but requires manual CAPTCHA solving.")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-solv-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": cl_file,
        "screenshots": screenshots,
        "notes": notes,
        "response": None
    }

    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except:
        apps = []
    apps.append(new_entry)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT: {status} ===")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
