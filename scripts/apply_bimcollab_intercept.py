#!/usr/bin/env python3
"""
BIMcollab Application - Intercept form submission to understand the API
Focus: find the actual submission endpoint and what data it needs
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright

CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"

def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    if not proxy_url:
        return None
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def main():
    proxy_config = get_proxy_config()

    all_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"],
            proxy=proxy_config
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 900}
        )

        async def handle_request(request):
            if request.method in ["POST", "PUT", "PATCH"]:
                url = request.url
                pd = request.post_data or ""
                headers = dict(request.headers)
                all_requests.append({
                    "method": request.method,
                    "url": url,
                    "data": pd[:500] if pd else None,
                    "content_type": headers.get("content-type", ""),
                })
                print(f"POST: {url[:100]}")
                if pd:
                    print(f"  Data: {pd[:200]}")

        page = await context.new_page()
        page.on("request", handle_request)

        await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # Dismiss all popups
        for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1000):
                    await btn.click()
                    await page.wait_for_timeout(500)
            except:
                pass

        # Find the actual Application tab button
        # From the structure: 'Job details' button and 'Apply' button
        # The 'Apply' button has class 'sc-s03za1-0 OACSe'
        print("\nLooking for Application tab button...")
        buttons = await page.query_selector_all("button")
        for btn in buttons:
            try:
                text = await btn.inner_text()
                cls = await btn.get_attribute("class") or ""
                print(f"  Button: '{text}', class='{cls[:50]}'")
            except:
                pass

        # The Application form section might appear after clicking "Apply" button
        # which is button with class containing 'sc-csisgn-0'
        try:
            # Click the second "Apply" button (the one that activates the form section)
            apply_btns = await page.query_selector_all("button.sc-s03za1-0")
            print(f"\nFound {len(apply_btns)} sc-s03za1-0 buttons")
            for i, btn in enumerate(apply_btns):
                text = await btn.inner_text()
                cls = await btn.get_attribute("class") or ""
                print(f"  {i}: '{text}' cls='{cls}'")
        except:
            pass

        # Try clicking "Apply" button that seems to toggle the application form
        # From the tab structure shown in screenshots: there are 3 tabs: Job details | Solliciteer met WhatsApp | Application
        # But from the button listing, we see: 'Job details' and two 'Apply' buttons
        # The 'Apply' with class 'sc-csisgn-0 cWtVVQ' seems to be the tab toggle

        try:
            # Click the Apply tab (the one that shows the embedded form)
            apply_tab = page.locator("button.sc-csisgn-0").first
            if await apply_tab.is_visible(timeout=2000):
                await apply_tab.click()
                print("\nClicked Apply tab (sc-csisgn-0)")
                await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Apply tab click: {e}")

        # Now check if name field is visible
        name_vis = False
        try:
            name_vis = await page.locator("input[name='candidate.name']").first.is_visible(timeout=2000)
        except:
            pass
        print(f"Name field visible: {name_vis}")

        # Get page screenshot to see current state
        await page.screenshot(path="/home/user/Agents/output/screenshots/bimcollab-intercept-01.png", full_page=True)

        # Fill the form naturally using type() (simulates real keyboard input)
        print("\nFilling form with type()...")

        # Fill name
        try:
            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click(force=True)
            await name_loc.type("Hisham Abboud", delay=50)
            print("Name typed")
        except Exception as e:
            print(f"Name type: {e}")

        # Fill email
        try:
            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click(force=True)
            await email_loc.type("hiaham123@hotmail.com", delay=50)
            print("Email typed")
        except Exception as e:
            print(f"Email type: {e}")

        # Fill phone
        try:
            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click(force=True)
            await phone_loc.type("+31 06 4841 2838", delay=50)
            print("Phone typed")
        except Exception as e:
            print(f"Phone type: {e}")

        await page.wait_for_timeout(500)

        # Upload CV
        try:
            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            print("CV uploaded")
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"CV: {e}")

        # Upload cover letter
        cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
        try:
            await page.locator("input[name='candidate.coverLetterFile']").set_input_files(cl_file, timeout=5000)
            print("Cover letter uploaded")
            await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"CL: {e}")

        # Click Yes radios
        result = await page.evaluate("""
            () => {
                const clickYes = (name) => {
                    const radios = Array.from(document.querySelectorAll(`input[name='${name}']`));
                    const yes = radios.find(r => r.value === 'true') || radios[0];
                    if (yes) {
                        yes.checked = true;
                        yes.dispatchEvent(new Event('change', {bubbles:true}));
                        yes.dispatchEvent(new MouseEvent('click', {bubbles:true}));
                        return yes.id;
                    }
                    return 'NOT FOUND';
                };
                return {
                    q1: clickYes('candidate.openQuestionAnswers.6352299.flag'),
                    q2: clickYes('candidate.openQuestionAnswers.6352300.flag')
                };
            }
        """)
        print(f"Radios: {result}")

        # Check form state
        state = await page.evaluate("""
            () => ({
                name: (document.querySelector("input[name='candidate.name']") || {value: 'missing'}).value,
                email: (document.querySelector("input[name='candidate.email']") || {value: 'missing'}).value,
                q1: ((document.querySelector("input[name='candidate.openQuestionAnswers.6352299.flag']:checked") || {value: 'none'}).value),
                q2: ((document.querySelector("input[name='candidate.openQuestionAnswers.6352300.flag']:checked") || {value: 'none'}).value),
            })
        """)
        print(f"Form state: {state}")

        await page.screenshot(path="/home/user/Agents/output/screenshots/bimcollab-intercept-02-filled.png", full_page=True)

        # Try clicking the actual Send/Submit button
        print("\nLooking for Send button...")
        all_btns = await page.query_selector_all("button")
        for btn in all_btns:
            try:
                text = await btn.inner_text()
                btype = await btn.get_attribute("type") or ""
                cls = await btn.get_attribute("class") or ""
                if text.strip():
                    print(f"  '{text}' type={btype} class={cls[:40]}")
            except:
                pass

        # Find and click the send button
        send_btn = None
        for sel in ["button[type='submit']", "button:has-text('Send')"]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1000):
                    send_btn = btn
                    break
            except:
                pass

        if send_btn:
            text = await send_btn.inner_text()
            print(f"Clicking: '{text}'")
            await send_btn.click()
        else:
            # Try by evaluate
            r = await page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    for (const btn of btns) {
                        if (btn.type === 'submit' || btn.textContent.trim().toLowerCase() === 'send') {
                            btn.click();
                            return btn.textContent + ' type=' + btn.type;
                        }
                    }
                    return 'none found';
                }
            """)
            print(f"JS send result: {r}")

        await page.wait_for_timeout(5000)
        await page.screenshot(path="/home/user/Agents/output/screenshots/bimcollab-intercept-03-after-submit.png", full_page=True)

        print(f"\nFinal URL: {page.url}")
        print(f"\nAll POST requests captured: {len([r for r in all_requests if r['method'] == 'POST'])}")
        for req in all_requests:
            if "captcha" not in req["url"] and "analytics" not in req["url"] and "sentry" not in req["url"]:
                print(f"\n{req['method']} {req['url'][:100]}")
                if req["data"]:
                    print(f"  Data: {req['data'][:300]}")

        await browser.close()

asyncio.run(main())
