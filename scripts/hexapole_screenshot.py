#!/usr/bin/env python3
"""Take screenshots of Hexapole job page for application record."""
import os
import re
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = '/home/user/Agents/output/screenshots'
CHROMIUM = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
JOB_URL = 'https://hexapole.com/en/vacancies/net-developer-net-core-industrial-automation/'

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Parse proxy from environment
proxy_env = os.environ.get('https_proxy', '')
match = re.match(r'http://([^:]+):(jwt_[^@]+)@([^:]+):(\d+)', proxy_env)
proxy_cfg = None
if match:
    user, pwd, host, port = match.groups()
    proxy_cfg = {'server': f'http://{host}:{port}', 'username': user, 'password': pwd}
    print(f'Using proxy: http://{host}:{port}')

with sync_playwright() as p:
    launch_kwargs = {
        'executable_path': CHROMIUM,
        'headless': True,
        'args': ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'],
    }
    if proxy_cfg:
        launch_kwargs['proxy'] = proxy_cfg

    browser = p.chromium.launch(**launch_kwargs)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 900},
        ignore_https_errors=True
    )
    page = context.new_page()

    print('Navigating to Hexapole job page...')
    try:
        page.goto(JOB_URL, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f'Load error (continuing): {e}')

    path1 = f'{SCREENSHOT_DIR}/hexapole-01-job-page.png'
    page.screenshot(path=path1, full_page=True)
    print(f'Screenshot saved: {path1}')

    page_title = page.title()
    page_url = page.url
    print(f'Title: {page_title}')
    print(f'URL: {page_url}')

    # Scroll to bottom to show application instructions
    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    page.wait_for_timeout(1000)
    path2 = f'{SCREENSHOT_DIR}/hexapole-02-job-page-bottom.png'
    page.screenshot(path=path2, full_page=True)
    print(f'Screenshot saved: {path2}')

    # Get page text
    try:
        body_el = page.query_selector('body')
        if body_el:
            text = body_el.inner_text()
            print(f'Page text length: {len(text)}')
            if text.strip():
                print('--- Page content (first 1500 chars) ---')
                print(text[:1500])
                print('--- End ---')
            else:
                print('Page appears empty or failed to load content.')
        else:
            print('No body element found.')
    except Exception as e:
        print(f'Error getting page text: {e}')

    browser.close()

print('\nDone taking screenshots.')
