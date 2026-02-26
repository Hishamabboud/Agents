#!/usr/bin/env python3
"""
Apply to new job targets - Round 3:
1. Zetes Goods ID - Software Engineer (Eindhoven) - LinkedIn apply
2. Watch-E - .NET Software Developer (Arnhem) - Email: karel@watch-e.nl
3. Visionplanner - Software Engineer .NET (Veenendaal) - Email: peter.westmeijer@visma.com
4. New Orange - Senior Software Engineer (Den Bosch) - Email: solliciteer@neworange.agency
5. Bryder - Software Engineer Azure/.NET (Delft) - join.com

For email-only applications, we'll try via their website contact forms or log as 'action_required'.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_FILE = "/home/user/Agents/data/applications.json"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def load_applications():
    with open(APPLICATIONS_FILE) as f:
        return json.load(f)


def save_application(new_app):
    apps = load_applications()
    apps.append(new_app)
    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(apps, f, indent=2)
    print(f"Logged application: {new_app['id']}")


async def take_screenshot(page, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOTS_DIR, f"{name}-{ts}.png")
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"Screenshot: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None


async def apply_watch_e(playwright):
    """Apply to Watch-E via their website or log as email required."""
    print("\n=== Applying to Watch-E ===")
    screenshots = []
    status = "action_required"
    notes = ""

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    try:
        await page.goto("https://www.watch-e.nl/vacature/vacature-software-developer", timeout=15000, wait_until="domcontentloaded")
        shot = await take_screenshot(page, "watch-e-01-job-page")
        if shot:
            screenshots.append(shot)

        content = await page.content()
        print(f"Watch-E page loaded. URL: {page.url}")

        # No online form - email application required
        notes = ("Watch-E application requires direct email to Karel Manschot at karel@watch-e.nl. "
                 "Position: .NET Software Developer in Arnhem. "
                 "Salary: EUR 4,500-6,250/month. "
                 "Tech stack: .NET, Docker, Kubernetes, Azure, React, NoSQL. "
                 "Please email CV and cover letter from /home/user/Agents/output/cover-letters/watch-e-net-software-developer.md "
                 "with subject: 'Application: .NET Software Developer - Hisham Abboud'. "
                 "MANUAL ACTION REQUIRED: Send email to karel@watch-e.nl")
        status = "action_required"

    except Exception as e:
        print(f"Watch-E error: {e}")
        notes = f"Error navigating to Watch-E: {e}. Manual email required to karel@watch-e.nl"
        status = "action_required"
    finally:
        await browser.close()

    return {
        "id": f"watch-e-net-developer-{datetime.now().strftime('%Y%m%d')}",
        "company": "Watch-E",
        "role": ".NET Software Developer",
        "url": "https://www.watch-e.nl/vacature/vacature-software-developer",
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": "/home/user/Agents/output/cover-letters/watch-e-net-software-developer.md",
        "screenshots": screenshots,
        "notes": notes,
        "email_used": CANDIDATE["email"],
        "response": None,
        "action_required": "Send email to karel@watch-e.nl with CV and cover letter"
    }


async def apply_visionplanner(playwright):
    """Apply to Visionplanner via their website/email."""
    print("\n=== Applying to Visionplanner ===")
    screenshots = []
    status = "action_required"

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    try:
        await page.goto("https://www.visionplanner.com/werken-bij/software-engineer-net", timeout=15000, wait_until="domcontentloaded")
        shot = await take_screenshot(page, "visionplanner-01-job-page")
        if shot:
            screenshots.append(shot)

        print(f"Visionplanner page loaded. URL: {page.url}")

        # Check for apply button
        try:
            apply_btn = page.locator("a[href*='peter'], a[href*='mailto'], button:has-text('Sollicit')").first
            href = await apply_btn.get_attribute("href") if await apply_btn.count() > 0 else None
            print(f"Apply button href: {href}")
        except:
            pass

        notes = ("Visionplanner application requires email to Peter Westmeijer at peter.westmeijer@visma.com "
                 "OR sollicitatie@visionplanner.com. "
                 "Position: Software Engineer (.NET) in Veenendaal (part of Visma). "
                 "Tech stack: C#, .NET Core, ASP.NET, Azure, React. "
                 "Salary: Market-competitive, hybrid work, 27+ vacation days. "
                 "Contact: Peter Westmeijer, phone 06 12177897. "
                 "Cover letter ready at: /home/user/Agents/output/cover-letters/visionplanner-software-engineer-net.md "
                 "MANUAL ACTION REQUIRED: Email to peter.westmeijer@visma.com")

    except Exception as e:
        print(f"Visionplanner error: {e}")
        notes = f"Error: {e}. Manual email required to peter.westmeijer@visma.com"
    finally:
        await browser.close()

    return {
        "id": f"visionplanner-software-engineer-net-{datetime.now().strftime('%Y%m%d')}",
        "company": "Visionplanner (Visma)",
        "role": "Software Engineer (.NET)",
        "url": "https://www.visionplanner.com/werken-bij/software-engineer-net",
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": "action_required",
        "resume_file": RESUME_PATH,
        "cover_letter_file": "/home/user/Agents/output/cover-letters/visionplanner-software-engineer-net.md",
        "screenshots": screenshots,
        "notes": notes,
        "email_used": CANDIDATE["email"],
        "response": None,
        "action_required": "Email peter.westmeijer@visma.com or sollicitatie@visionplanner.com with CV and cover letter"
    }


async def apply_new_orange(playwright):
    """Apply to New Orange via their email."""
    print("\n=== Applying to New Orange ===")
    screenshots = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    try:
        await page.goto("https://neworange.agency/en/careers/backend-developer-net", timeout=15000, wait_until="domcontentloaded")
        shot = await take_screenshot(page, "new-orange-01-job-page")
        if shot:
            screenshots.append(shot)

        print(f"New Orange page loaded. URL: {page.url}")

        notes = ("New Orange application requires email to Rosann Noordam at solliciteer@neworange.agency. "
                 "Include: LinkedIn profile, CV, and portfolio. "
                 "Position: Backend Developer (.NET) in 's-Hertogenbosch. "
                 "Tech stack: .NET Core, Azure Functions, Azure SQL, Azure DevOps, API Management. "
                 "Benefits: Company equity from day one, 27+ vacation days. "
                 "Note: Company is looking for Dutch speakers based in Netherlands. "
                 "Cover letter ready at: /home/user/Agents/output/cover-letters/new-orange-senior-software-engineer.md "
                 "MANUAL ACTION REQUIRED: Email solliciteer@neworange.agency")

    except Exception as e:
        print(f"New Orange error: {e}")
        notes = f"Error: {e}. Manual email required to solliciteer@neworange.agency"
    finally:
        await browser.close()

    return {
        "id": f"new-orange-backend-net-{datetime.now().strftime('%Y%m%d')}",
        "company": "New Orange",
        "role": "Backend Developer (.NET)",
        "url": "https://neworange.agency/en/careers/backend-developer-net",
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": "action_required",
        "resume_file": RESUME_PATH,
        "cover_letter_file": "/home/user/Agents/output/cover-letters/new-orange-senior-software-engineer.md",
        "screenshots": screenshots,
        "notes": notes,
        "email_used": CANDIDATE["email"],
        "response": None,
        "action_required": "Email solliciteer@neworange.agency with LinkedIn profile, CV, and cover letter"
    }


async def apply_zetes(playwright):
    """Apply to Zetes Goods ID Software Engineer via LinkedIn or Workday."""
    print("\n=== Applying to Zetes Goods ID ===")
    screenshots = []
    status = "skipped"
    notes = ""

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    try:
        # Try Zetes LinkedIn jobs
        await page.goto("https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087", timeout=15000, wait_until="domcontentloaded")
        shot = await take_screenshot(page, "zetes-01-linkedin-job")
        if shot:
            screenshots.append(shot)

        print(f"Zetes LinkedIn page. URL: {page.url}")

        # LinkedIn requires login to apply
        # Try to find the "Apply" external URL
        content = await page.content()
        import re
        external_urls = re.findall(r'externalApply.*?url.*?["\']([^"\']+)["\']', content)
        print(f"External apply URLs found: {external_urls[:3]}")

        notes = ("Zetes Goods ID - Software Engineer in Eindhoven. "
                 "LinkedIn job ID: 4375182087. "
                 "Recruiter contact: Rianne Grevers (HR Adviseur). "
                 "Application requires LinkedIn login - cannot automate. "
                 "Company uses LinkedIn for jobs: https://www.linkedin.com/company/zetes/jobs/ "
                 "Tech stack: C#, .NET, Azure, Angular, TypeScript, MS SQL Server. "
                 "3+ years experience, Dutch and English required. "
                 "24-40 hours/week. "
                 "MANUAL ACTION REQUIRED: Apply via LinkedIn at https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087")
        status = "skipped"

    except Exception as e:
        print(f"Zetes error: {e}")
        notes = f"Error: {e}. Requires LinkedIn login to apply."
        status = "skipped"
    finally:
        await browser.close()

    return {
        "id": f"zetes-software-engineer-eindhoven-{datetime.now().strftime('%Y%m%d')}",
        "company": "Zetes Goods ID",
        "role": "Software Engineer",
        "url": "https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087",
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": RESUME_PATH,
        "cover_letter_file": "/home/user/Agents/output/cover-letters/zetes-goods-id-software-engineer.md",
        "screenshots": screenshots,
        "notes": notes,
        "email_used": CANDIDATE["email"],
        "response": None,
        "action_required": "Apply via LinkedIn (login required): https://nl.linkedin.com/jobs/view/software-engineer-at-zetes-goods-id-4375182087"
    }


async def apply_bryder(playwright):
    """Apply to Bryder via join.com (note: magic link auth issue)."""
    print("\n=== Applying to Bryder ===")
    screenshots = []

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    try:
        await page.goto("https://join.com/companies/bryder/15736329-software-engineer-azure-net", timeout=15000, wait_until="domcontentloaded")
        shot = await take_screenshot(page, "bryder-01-job-page")
        if shot:
            screenshots.append(shot)

        print(f"Bryder join.com page. URL: {page.url}")

        # Try to find and click Apply button
        try:
            apply_btn = page.locator("button:has-text('Apply'), a:has-text('Solliciteer'), button:has-text('Solliciteer')").first
            if await apply_btn.count() > 0:
                await apply_btn.click()
                await page.wait_for_timeout(2000)
                shot = await take_screenshot(page, "bryder-02-after-apply-click")
                if shot:
                    screenshots.append(shot)
                print(f"After apply click URL: {page.url}")

                # Try to fill email
                email_input = page.locator("input[type='email'], input[name='email']").first
                if await email_input.count() > 0:
                    await email_input.fill(CANDIDATE["email"])
                    await page.wait_for_timeout(500)

                    continue_btn = page.locator("button:has-text('Continue'), button:has-text('Doorgaan'), button[type='submit']").first
                    if await continue_btn.count() > 0:
                        await continue_btn.click()
                        await page.wait_for_timeout(3000)
                        shot = await take_screenshot(page, "bryder-03-after-email")
                        if shot:
                            screenshots.append(shot)
                        print(f"After email submit URL: {page.url}")
        except Exception as e:
            print(f"Bryder apply click failed: {e}")

        notes = ("Bryder BV - Software Engineer Azure/.NET in Delft. "
                 "join.com ID: 15736329. "
                 "Salary: EUR 3,000-5,000/month. "
                 "Tech stack: C#/.NET, Azure, Azure DevOps, PowerShell, CI/CD, JavaScript/TypeScript. "
                 "3+ years experience. "
                 "join.com uses magic-link authentication (same issue as Sendent). "
                 "Check hiaham123@hotmail.com inbox for magic link email from join.com to complete application. "
                 "Cover letter at: /home/user/Agents/output/cover-letters/bryder-software-engineer-azure-net.md "
                 "ACTION REQUIRED: Check email for join.com magic link and complete application.")

    except Exception as e:
        print(f"Bryder error: {e}")
        notes = f"Error: {e}. Manual application required at join.com/companies/bryder/15736329-software-engineer-azure-net"
    finally:
        await browser.close()

    return {
        "id": f"bryder-software-engineer-azure-net-{datetime.now().strftime('%Y%m%d')}",
        "company": "Bryder BV",
        "role": "Software Engineer Azure / .NET",
        "url": "https://join.com/companies/bryder/15736329-software-engineer-azure-net",
        "date_applied": datetime.now().isoformat(),
        "score": 8.0,
        "status": "action_required",
        "resume_file": RESUME_PATH,
        "cover_letter_file": "/home/user/Agents/output/cover-letters/bryder-software-engineer-azure-net.md",
        "screenshots": screenshots,
        "notes": notes,
        "email_used": CANDIDATE["email"],
        "response": None,
        "action_required": "Check hiaham123@hotmail.com for join.com magic link and complete application"
    }


async def main():
    print("Starting Round 3 applications...")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    async with async_playwright() as playwright:
        # Apply to each company
        try:
            r = await apply_watch_e(playwright)
            results.append(r)
            save_application(r)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Watch-E application failed: {e}")

        try:
            r = await apply_visionplanner(playwright)
            results.append(r)
            save_application(r)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Visionplanner application failed: {e}")

        try:
            r = await apply_new_orange(playwright)
            results.append(r)
            save_application(r)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"New Orange application failed: {e}")

        try:
            r = await apply_zetes(playwright)
            results.append(r)
            save_application(r)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Zetes application failed: {e}")

        try:
            r = await apply_bryder(playwright)
            results.append(r)
            save_application(r)
        except Exception as e:
            print(f"Bryder application failed: {e}")

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['company']} | {r['role']} | Status: {r['status']}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
