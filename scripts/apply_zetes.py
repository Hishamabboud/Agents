#!/usr/bin/env python3
"""
Apply to Zetes Goods ID - Software Engineer position via Playwright.
Job URL: https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087
Company: Zetes Goods ID
Location: Eindhoven, Netherlands
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/zetes-goods-id-software-engineer.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

# Cover letter text
COVER_LETTER = """Dear Hiring Manager at Zetes Goods ID,

I am writing to express my strong interest in the Software Engineer position at Zetes in Eindhoven. As a software engineer living and working in Eindhoven with hands-on experience in C#, .NET, ASP.NET Core, Azure, and SQL, and fluency in both Dutch and English, I am well-positioned to contribute to your team from day one.

In my current role as Software Service Engineer at Actemium (VINCI Energies), I build and maintain enterprise applications for industrial clients, developing custom API integrations, managing SQL databases, and deploying cloud-hosted solutions. This is precisely the kind of work Zetes does - bridging IT systems with operational processes to create tangible business value.

During my internship at Delta Electronics, I built a full C# web application for HR management across multiple branches, and migrated a legacy VB codebase to C# for maintainability improvements. I have consistently worked with relational databases (SQL Server, PostgreSQL) and backend API services throughout my career.

I hold a BSc in Software Engineering from Fontys University in Eindhoven, I have full Dutch work authorization, and I am available 32-40 hours per week.

Kind regards,
Hisham Abboud"""


async def take_screenshot(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOTS_DIR, f"zetes-{name}-{ts}.png")
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None


async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        try:
            # Try to find the direct Workday or application URL from Zetes
            print("Navigating to Zetes careers page...")

            # Try multiple possible Zetes career page URLs
            zetes_career_urls = [
                "https://www.zetes.com/en/careers",
                "https://www.zetes.com/nl/careers",
                "https://www.zetes.com/careers",
            ]

            for url in zetes_career_urls:
                try:
                    response = await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    if response and response.status < 400:
                        print(f"Loaded: {url}")
                        break
                except Exception as e:
                    print(f"Failed {url}: {e}")
                    continue

            shot = await take_screenshot(page, "01-careers-page")
            if shot:
                screenshots.append(shot)

            content = await page.content()
            print(f"Page title: {await page.title()}")
            print(f"Current URL: {page.url}")

            # Try Workday application
            workday_urls = [
                "https://zetes.wd3.myworkdayjobs.com/en-US/Zetes_Careers",
                "https://zetes.wd1.myworkdayjobs.com/en-US/Zetes_Careers",
            ]

            workday_loaded = False
            for wurl in workday_urls:
                try:
                    resp = await page.goto(wurl, timeout=15000, wait_until="domcontentloaded")
                    if resp and resp.status < 400:
                        print(f"Workday loaded: {wurl}")
                        workday_loaded = True
                        break
                except Exception as e:
                    print(f"Workday URL failed: {e}")

            if workday_loaded:
                shot = await take_screenshot(page, "02-workday")
                if shot:
                    screenshots.append(shot)

                # Search for Software Engineer in Eindhoven
                try:
                    await page.wait_for_selector("input[placeholder*='Search']", timeout=5000)
                    search_input = page.locator("input[placeholder*='Search']").first
                    await search_input.fill("Software Engineer")
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(2000)

                    shot = await take_screenshot(page, "03-search-results")
                    if shot:
                        screenshots.append(shot)
                except Exception as e:
                    print(f"Search failed: {e}")

        except Exception as e:
            print(f"Error: {e}")
            shot = await take_screenshot(page, "error")
            if shot:
                screenshots.append(shot)
        finally:
            await browser.close()

    # Log the result
    result = {
        "id": f"zetes-software-engineer-eindhoven-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Zetes Goods ID",
        "role": "Software Engineer",
        "url": "https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087",
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": "failed",
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots,
        "notes": "Could not find direct Workday application portal. LinkedIn requires login.",
        "email_used": CANDIDATE["email"],
        "response": None
    }

    print("\n=== Application Result ===")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    asyncio.run(main())
