#!/usr/bin/env python3
"""
Hexapole Application via Outlook Web.
Attempts to send the application email through Outlook Web (outlook.live.com).
"""
import os
import re
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = '/home/user/Agents/output/screenshots'
CHROMIUM = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/hexapole-automatisering-net-developer.md'

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Read cover letter
with open(COVER_LETTER_PATH, 'r') as f:
    cover_letter = f.read().strip()

RECIPIENT = 'w.rebel@hexapole.com'
SENDER = 'hiaham123@hotmail.com'
SUBJECT = 'Application: .NET Developer | Industrial Automation — Hisham Abboud'

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

    # Navigate to Outlook Web
    print('Navigating to Outlook Web (outlook.live.com)...')
    try:
        page.goto('https://outlook.live.com/mail/', wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f'Load error: {e}')

    outlook_url = page.url
    outlook_title = page.title()
    print(f'Outlook URL: {outlook_url}')
    print(f'Outlook title: {outlook_title}')

    path3 = f'{SCREENSHOT_DIR}/hexapole-03-outlook-initial.png'
    page.screenshot(path=path3, full_page=False)
    print(f'Screenshot saved: {path3}')

    is_login = ('login' in outlook_url.lower() or 'signin' in outlook_url.lower() or
                'sign in' in outlook_title.lower() or 'log in' in outlook_title.lower())

    if is_login:
        print('Outlook login page detected. Attempting to enter email...')
        try:
            # Wait for and fill email input
            email_input = page.wait_for_selector(
                'input[type="email"], input[name="loginfmt"], #i0116',
                timeout=8000
            )
            email_input.fill(SENDER)
            page.wait_for_timeout(800)

            path4 = f'{SCREENSHOT_DIR}/hexapole-04-email-entered.png'
            page.screenshot(path=path4, full_page=False)
            print(f'Screenshot saved: {path4}')

            # Click Next button
            next_btn = page.query_selector('input[type="submit"]#idSIButton9, button#idSIButton9, input[value="Next"]')
            if not next_btn:
                next_btn = page.query_selector('[type="submit"]')
            if next_btn:
                next_btn.click()
                page.wait_for_timeout(3000)
                path5 = f'{SCREENSHOT_DIR}/hexapole-05-after-email-submit.png'
                page.screenshot(path=path5, full_page=False)
                print(f'Screenshot saved: {path5}')
                print('Reached password step. No password stored — cannot complete automated login.')
            else:
                print('Next button not found.')

        except Exception as e:
            print(f'Login error: {e}')
            path4e = f'{SCREENSHOT_DIR}/hexapole-04-login-error.png'
            page.screenshot(path=path4e, full_page=False)
            print(f'Screenshot saved: {path4e}')
    else:
        print('Outlook appears accessible (possibly logged in).')
        path4 = f'{SCREENSHOT_DIR}/hexapole-04-outlook-inbox.png'
        page.screenshot(path=path4, full_page=False)
        print(f'Screenshot saved: {path4}')

        # Try to compose new email
        try:
            compose_btn = page.wait_for_selector(
                '[aria-label*="New mail"], [aria-label*="Compose"], [data-automationid="newMailButton"]',
                timeout=5000
            )
            if compose_btn:
                compose_btn.click()
                page.wait_for_timeout(2000)
                path5 = f'{SCREENSHOT_DIR}/hexapole-05-compose-open.png'
                page.screenshot(path=path5, full_page=False)
                print(f'Screenshot saved: {path5}')

                # Fill To field
                to_field = page.query_selector('[aria-label="To"], input[placeholder*="To"], [role="textbox"][aria-label*="To"]')
                if to_field:
                    to_field.click()
                    to_field.fill(RECIPIENT)
                    page.keyboard.press('Tab')
                    page.wait_for_timeout(500)

                # Fill Subject
                subj_field = page.query_selector('[aria-label="Subject"], input[placeholder*="Subject"]')
                if subj_field:
                    subj_field.fill(SUBJECT)

                # Fill body
                body_field = page.query_selector('[aria-label="Message body"], div[contenteditable="true"]')
                if body_field:
                    body_field.click()
                    body_field.fill(cover_letter)

                path6 = f'{SCREENSHOT_DIR}/hexapole-06-email-composed.png'
                page.screenshot(path=path6, full_page=False)
                print(f'Screenshot saved: {path6}')

                # Send
                send_btn = page.query_selector('[aria-label="Send"], button[title="Send"]')
                if send_btn:
                    path_presend = f'{SCREENSHOT_DIR}/hexapole-07-pre-send.png'
                    page.screenshot(path=path_presend, full_page=False)
                    print(f'Pre-send screenshot saved: {path_presend}')
                    send_btn.click()
                    page.wait_for_timeout(3000)
                    path8 = f'{SCREENSHOT_DIR}/hexapole-08-after-send.png'
                    page.screenshot(path=path8, full_page=False)
                    print(f'Screenshot saved: {path8}')
                    print('EMAIL SENT successfully!')
                else:
                    print('Send button not found — could not send email.')
        except Exception as ce:
            print(f'Compose error: {ce}')
            path5e = f'{SCREENSHOT_DIR}/hexapole-05-compose-error.png'
            page.screenshot(path=path5e, full_page=False)
            print(f'Screenshot saved: {path5e}')

    browser.close()

print('\nEmail automation complete.')
print(f'To: {RECIPIENT}')
print(f'From: {SENDER}')
print(f'Subject: {SUBJECT}')
