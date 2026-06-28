#!/usr/bin/env python3
"""
Inspect the Spotler form structure in detail to understand what's visible/hidden.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

async def ss(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOTS_DIR}/spotler-inspect-{name}-{ts}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  [SS] {path}")
    return path

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        ctx = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        await page.goto("https://spotler.com/careers/jobs/open-application/apply-1136104",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # Accept cookies
        try:
            await page.click("#CybotCookiebotDialogBodyButtonAccept", timeout=3000)
            await page.wait_for_timeout(1000)
        except: pass

        await ss(page, "00-initial")

        # Check form structure
        print("[INSPECT] Form structure:")
        form_info = await page.evaluate("""
            () => {
                const form = document.querySelector('form');
                if (!form) return 'No form found';

                const pages = form.querySelectorAll('.gf_page_steps, .gf_step, [class*="page"]');

                // Get ALL inputs with visibility info
                const inputs = form.querySelectorAll('input, textarea, select');
                const inputInfo = Array.from(inputs).map(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return {
                        tag: el.tagName,
                        id: el.id,
                        name: el.name,
                        type: el.type,
                        value: el.value ? el.value.substring(0, 50) : '',
                        visible: rect.width > 0 && rect.height > 0,
                        display: style.display,
                        visibility: style.visibility,
                        disabled: el.disabled,
                        required: el.required,
                        rect: { w: Math.round(rect.width), h: Math.round(rect.height), x: Math.round(rect.x), y: Math.round(rect.y) }
                    };
                });

                // Get form pages/steps
                const stepContainers = form.querySelectorAll('[class*="gf_page"], [class*="gform_page"], [class*="page_steps"]');

                return {
                    formId: form.id,
                    formAction: form.action,
                    formMethod: form.method,
                    inputs: inputInfo,
                    stepCount: stepContainers.length,
                    steps: Array.from(stepContainers).map(s => ({ class: s.className, id: s.id })),
                    html_snippet: form.outerHTML.substring(0, 3000)
                };
            }
        """)

        print(json.dumps(form_info, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
