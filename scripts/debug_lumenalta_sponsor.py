#!/usr/bin/env python3
"""Debug Lumenalta sponsorship dropdown structure."""

import asyncio
import json
import os
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
APPLY_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92/apply"
EMAIL = "hiaham123@hotmail.com"
NAME = "Hisham Abboud"
CITY = "Eindhoven"
PHONE = "31648412838"


def get_proxy():
    proxy_raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_raw:
        return None
    parsed = urllib.parse.urlparse(proxy_raw)
    return {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        "username": urllib.parse.unquote(parsed.username or ""),
        "password": urllib.parse.unquote(parsed.password or ""),
    }


REACT_FILL_JS = """
(args) => {
    const el = document.querySelector('[name="' + args.name + '"]');
    if (!el) { return 'not_found'; }
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    nativeInputValueSetter.call(el, args.value);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.dispatchEvent(new Event('blur', {bubbles: true}));
    return el.value;
}
"""


async def main():
    proxy = get_proxy()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        }
        if proxy:
            launch_kwargs["proxy"] = proxy

        browser = await p.chromium.launch(**launch_kwargs)
        ctx_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "ignore_https_errors": True,
        }
        if proxy:
            ctx_kwargs["proxy"] = proxy

        context = await browser.new_context(**ctx_kwargs)
        page = await context.new_page()

        await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Accept cookies
        try:
            btn = page.locator("button:has-text('Accept All')").first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Fill email to unlock
        email_el = page.locator("input[name='email']").first
        await email_el.click(timeout=5000)
        await email_el.fill(EMAIL)
        await email_el.press("Tab")
        await asyncio.sleep(5)

        # Fill fields
        for name_attr, value in [("name", NAME), ("city", CITY), ("phone", PHONE)]:
            await page.evaluate(REACT_FILL_JS, {"name": name_attr, "value": value})

        # Select country
        rs_inputs = await page.locator("input[id*='react-select']").all()
        if rs_inputs:
            await rs_inputs[0].click()
            await asyncio.sleep(0.5)
            await rs_inputs[0].fill("Netherlands")
            await asyncio.sleep(2)
            opt = page.locator("div[class*='option']:has-text('Netherlands')").first
            if await opt.count() > 0:
                await opt.click()
                print("Country: Netherlands selected")

        await asyncio.sleep(1)

        # Now examine the sponsorship dropdown area
        print("\n=== SPONSORSHIP DROPDOWN HTML ANALYSIS ===")

        # Get all elements around the sponsorship question
        html_info = await page.evaluate("""
            () => {
                // Find the sponsorship label/question
                const allTexts = Array.from(document.querySelectorAll('*')).filter(function(el) {
                    return el.children.length === 0 && el.textContent && el.textContent.includes('sponsorship');
                });

                const results = [];
                for (const el of allTexts.slice(0, 3)) {
                    const parent = el.closest('[class]');
                    if (parent) {
                        const siblings = Array.from(parent.parentElement ? parent.parentElement.children : []);
                        results.push({
                            labelEl: el.tagName + '.' + el.className,
                            labelText: el.textContent.substring(0, 80),
                            parentClass: parent.className.substring(0, 80),
                            parentTag: parent.tagName,
                            siblingClasses: siblings.map(function(s) { return s.tagName + '.' + s.className.substring(0, 40); })
                        });
                    }
                }
                return results;
            }
        """)
        print("Label analysis:")
        for item in html_info:
            print(f"  {json.dumps(item, indent=2)}")

        # Look for the actual dropdown element near sponsorship
        dropdown_info = await page.evaluate("""
            () => {
                // Find elements with 'select' or 'dropdown' class near sponsorship text
                const sponsor_els = Array.from(document.querySelectorAll('[class*="select"], [class*="dropdown"], [class*="Dropdown"]'));
                const visible = sponsor_els.filter(function(el) { return el.offsetParent !== null; });
                return visible.map(function(el) {
                    return {
                        tag: el.tagName,
                        cls: el.className.substring(0, 80),
                        text: el.textContent.substring(0, 80),
                        role: el.getAttribute('role') || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        dataName: el.getAttribute('data-name') || '',
                        id: el.id || '',
                        children_count: el.children.length
                    };
                });
            }
        """)
        print("\nDropdown elements:")
        for item in dropdown_info:
            print(f"  {item}")

        # Get all interactive elements in the page (visible)
        interactive_info = await page.evaluate("""
            () => {
                const els = Array.from(document.querySelectorAll('input, select, button, [role="combobox"], [role="listbox"], [role="option"]'));
                return els.filter(function(el) { return el.offsetParent !== null; }).map(function(el) {
                    return {
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        role: el.getAttribute('role') || '',
                        cls: el.className.substring(0, 60),
                        value: (el.value || '').substring(0, 40),
                        text: el.textContent.substring(0, 40)
                    };
                });
            }
        """)
        print("\nInteractive elements:")
        for item in interactive_info:
            print(f"  {item}")

        # Scroll down to see sponsorship and take screenshot
        await page.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(0.5)

        path = str(SCREENSHOTS_DIR / "lumenalta-debug-sponsor.png")
        await page.screenshot(path=path, full_page=False, timeout=20000, animations="disabled")
        print(f"\nScreenshot: {path}")

        # Try clicking the sponsorship dropdown - look for any clickable element near sponsorship text
        print("\n=== TRYING TO CLICK SPONSORSHIP ===")

        # Look for the custom select container
        custom_sel_html = await page.evaluate("""
            () => {
                const label = Array.from(document.querySelectorAll('label, p, span, div')).find(function(el) {
                    return el.textContent && el.textContent.trim().includes('Do you require sponsorship');
                });
                if (!label) return 'label not found';
                const container = label.closest('div') || label.parentElement;
                const next = container ? container.nextElementSibling : null;
                return {
                    label_html: label ? label.outerHTML.substring(0, 200) : 'none',
                    container_html: container ? container.outerHTML.substring(0, 400) : 'none',
                    next_html: next ? next.outerHTML.substring(0, 400) : 'none'
                };
            }
        """)
        print("Sponsorship label area:")
        print(json.dumps(custom_sel_html, indent=2))

        # Get the entire form's HTML structure around sponsorship
        form_html = await page.evaluate("""
            () => {
                const form = document.querySelector('form') || document.querySelector('[class*="form"]');
                return form ? form.innerHTML.substring(3000, 6000) : 'no form found';
            }
        """)
        print("\nForm HTML (3000-6000):")
        print(form_html)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
