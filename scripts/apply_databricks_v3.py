#!/usr/bin/env python3
"""
Apply to Databricks Fullstack SE role via Greenhouse (v3).
Handles Select2 location field, custom dropdowns, and checkboxes properly.
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/databricks-fullstack-se.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def ss(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"databricks-v3-{name}-{TIMESTAMP}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"  [SS] {path}")
    except Exception as e:
        print(f"  [SS FAIL] {e}")
        path = None
    return path

def run():
    screenshots = []
    status = "failed"
    notes = ""

    with open(COVER_LETTER_PATH) as f:
        cover_letter_text = f.read().strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage", "--ignore-certificate-errors"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        try:
            # Load careers page to get Greenhouse iframe URL with token
            print("Loading Databricks careers page...")
            page.goto(
                "https://databricks.com/company/careers/open-positions/job?gh_jid=8029677002",
                wait_until="domcontentloaded", timeout=30000
            )
            time.sleep(3)

            iframe_el = page.locator("iframe[src*='greenhouse']").first
            if iframe_el.count() == 0:
                raise Exception("No Greenhouse iframe found on careers page")

            gh_url = iframe_el.get_attribute("src")
            print(f"Greenhouse URL: {gh_url[:80]}...")

            page.goto(gh_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            page.wait_for_selector("#first_name", timeout=10000)
            print("Form loaded")

            s = ss(page, "01-form-loaded")
            if s: screenshots.append(s)

            # ── INSPECT DOM STRUCTURE ────────────────────────────────────────
            # Understand the Location field and custom dropdowns
            dom_info = page.evaluate("""
            () => {
                // Location field
                const locInputs = document.querySelectorAll('[id*="location"], [name*="location"], [placeholder*="ity"], [placeholder*="ocation"]');
                const locInfo = Array.from(locInputs).map(el => ({
                    tag: el.tagName, id: el.id, name: el.name,
                    type: el.type, placeholder: el.placeholder,
                    className: el.className.substring(0,80),
                    value: el.value
                }));

                // Custom dropdown elements (not <select>)
                const dropdowns = document.querySelectorAll('[role="combobox"], [role="listbox"], .select2-container, .chosen-container, [class*="dropdown"], [class*="select"]');
                const dropInfo = Array.from(dropdowns).slice(0,10).map(el => ({
                    tag: el.tagName, id: el.id, role: el.getAttribute('role'),
                    className: el.className.substring(0,100),
                    ariaLabel: el.getAttribute('aria-label') || '',
                    text: el.textContent.trim().substring(0,60)
                }));

                // All inputs to understand structure
                const allInputs = document.querySelectorAll('input:not([type="hidden"]):not([type="file"])');
                const inputInfo = Array.from(allInputs).map(el => ({
                    tag: el.tagName, id: el.id, name: el.name,
                    type: el.type, placeholder: el.placeholder,
                    value: el.value, className: el.className.substring(0,60)
                }));

                // Checkboxes with labels
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                const cbInfo = Array.from(checkboxes).map(cb => {
                    // Walk up to find label text
                    let el = cb.parentElement;
                    let text = '';
                    for (let i = 0; i < 4 && el; i++) {
                        text = el.textContent.trim();
                        if (text.length > 3) break;
                        el = el.parentElement;
                    }
                    return {id: cb.id, name: cb.name, value: cb.value, text: text.substring(0,100)};
                });

                return {locInfo, dropInfo, inputInfo: inputInfo.slice(0,20), cbInfo};
            }
            """)

            print("=== DOM STRUCTURE ===")
            print("Location inputs:", json.dumps(dom_info['locInfo'], indent=2))
            print("\nDropdowns:", json.dumps(dom_info['dropInfo'], indent=2))
            print("\nAll inputs:", json.dumps(dom_info['inputInfo'], indent=2))
            print("\nCheckboxes:", json.dumps(dom_info['cbInfo'], indent=2))

            # Get the actual HTML of the form for deeper inspection
            form_html = page.evaluate("""
            () => {
                const form = document.querySelector('form, .application-form');
                return form ? form.innerHTML.substring(0, 8000) : document.body.innerHTML.substring(0, 8000);
            }
            """)
            print("\n=== FORM HTML (first 8000 chars) ===")
            print(form_html)

        except Exception as e:
            print(f"Error during inspection: {e}")
            try:
                s = ss(page, "error")
                if s: screenshots.append(s)
            except Exception:
                pass
        finally:
            browser.close()

    return screenshots


if __name__ == "__main__":
    print("=== DOM Inspection ===")
    screenshots = run()
    print(f"\nScreenshots: {screenshots}")
