#!/usr/bin/env python3
"""Navigate to ALTEN Nederland job listing and find application URL."""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
        ])
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='nl-NL',
            timezone_id='Europe/Amsterdam',
            viewport={'width': 1280, 'height': 800},
        )
        page = await context.new_page()

        # Track all redirects
        urls_visited = []
        page.on('response', lambda r: urls_visited.append((r.status, r.url)) if r.status in [200, 301, 302, 303, 307, 308] else None)

        print("Navigating to initial URL...")
        try:
            await page.goto(
                'https://englishjobsearch.nl/clickout/bc0a1044202977b3',
                wait_until='networkidle',
                timeout=30000
            )
        except Exception as e:
            print(f"Navigation error (may be OK if redirected): {e}")

        final_url = page.url
        print(f"Final URL after navigation: {final_url}")

        # Screenshot
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        await page.screenshot(path=f'/home/user/Agents/output/screenshots/alten-01-initial-{ts}.png', full_page=True)

        # Get page content
        content = await page.content()
        print(f"Page title: {await page.title()}")
        print(f"Content length: {len(content)}")

        # Look for apply links
        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.textContent.trim()}))')
        print("\nLinks found on page:")
        for link in links[:30]:
            if link['href']:
                print(f"  {link['text'][:50]}: {link['href']}")

        # Print visited URLs
        print("\nURLs visited/redirected:")
        for status, url in urls_visited[:20]:
            print(f"  {status}: {url}")

        await browser.close()
        return final_url

if __name__ == '__main__':
    asyncio.run(main())
