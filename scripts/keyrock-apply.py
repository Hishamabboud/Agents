#!/usr/bin/env python3
"""
Keyrock Senior Full Stack Web Engineer - Application Script
Uses Playwright with route blocking to handle DNS resolution issues
"""

import os
import sys
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots'
CV_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf'
APPLICATION_URL = 'https://jobs.ashbyhq.com/keyrock/13432bba-3821-4ca9-a994-9a13ba307fd2'

APPLICANT = {
    'first_name': 'Hisham',
    'last_name': 'Abboud',
    'full_name': 'Hisham Abboud',
    'email': 'hiaham123@hotmail.com',
    'phone': '+31648412838',
    'city': 'Eindhoven',
    'country': 'Netherlands',
    'linkedin': 'linkedin.com/in/hisham-abboud',
    'github': 'github.com/Hishamabboud',
}

# Answers to screening questions
ANSWERS = {
    'name': 'Hisham Abboud',
    'email': 'hiaham123@hotmail.com',
    'gender': 'Male ',
    'how_learned': 'LinkedIn',
    'why_keyrock': (
        "I want to join Keyrock because it sits at the intersection of cutting-edge technology "
        "and financial markets - exactly where I aspire to work. Keyrock's mission of bringing "
        "liquidity and efficiency to digital asset markets resonates deeply with my passion for "
        "building systems that have real-world impact at scale.\n\n"
        "Regarding Keyrock's values: Teamwork - I have consistently delivered in collaborative "
        "environments, from cross-functional work at Actemium (VINCI Energies) with industrial "
        "clients, to agile sprints at ASML. Ownership - I founded CogitatAI as a solo founder, "
        "taking full responsibility from architecture to deployment. Passion - I am genuinely "
        "excited by the complexity of trading infrastructure and I invest personal time building "
        "AI systems and exploring financial technology."
    ),
    'digital_assets_experience': (
        "While my professional experience has focused on industrial and enterprise software, "
        "I have a strong personal interest in digital assets and blockchain technology. I have "
        "studied algorithmic trading concepts, order book mechanics, and DeFi protocols through "
        "self-directed learning. I am familiar with cryptocurrency market microstructure, "
        "liquidity provision concepts, and the role of market makers like Keyrock. My background "
        "in building high-performance Python systems (including Locust-based load testing at ASML) "
        "gives me a solid foundation to work with trading systems, and I am highly motivated to "
        "deepen this expertise at Keyrock."
    ),
    'expected_compensation': (
        "EUR 70,000 - 85,000 per year, depending on the full benefits package and growth "
        "opportunities. Open to discussing further based on role scope and Keyrock's compensation structure."
    ),
    'country': 'Netherlands',
    'fullstack_years': '4',
    'rust_cpp_years': (
        "0 years of professional Rust experience, but 3+ years with C# (.NET) at Actemium and "
        "Delta Electronics, and 2+ years with Python. Actively learning Rust and understand its "
        "ownership model - confident I can ramp up quickly."
    ),
    'privacy_consent': 'Yes',
    'cicd_gitlab': (
        "Yes - experience with CI/CD pipelines via Azure DevOps at ASML and Git-based workflows "
        "at Actemium. Hands-on experience with Docker, Kubernetes, and infrastructure-as-code principles."
    ),
    'financial_datasets_years': (
        "1 year - built analytics dashboards and worked with structured data pipelines in "
        "industrial contexts (MES data, performance metrics). Skills directly transferable to financial data."
    ),
    'fintech_years': (
        "I do not have direct fintech/crypto industry experience, but I have strong engineering "
        "foundations and deep interest in financial technology. Transitioning into fintech and "
        "Keyrock represents an excellent opportunity to apply my skills in this domain."
    ),
}


def screenshot(page, name):
    filepath = os.path.join(SCREENSHOTS_DIR, name)
    try:
        page.screenshot(path=filepath, full_page=True, timeout=60000)
        print(f'Screenshot saved: {name}')
    except Exception as e:
        print(f'Screenshot full_page failed ({e}), trying viewport...')
        try:
            page.screenshot(path=filepath, full_page=False, timeout=30000)
            print(f'Screenshot (viewport) saved: {name}')
        except Exception as e2:
            print(f'Viewport screenshot also failed: {e2}')
    return filepath


def handle_route(route, request):
    """Intercept requests - block external slow resources, allow main site."""
    url = request.url
    blocked_patterns = [
        'fullstory.com',
        'datadoghq.com',
        'sentry.io',
        'www.recaptcha.net',
        'www.google.com/recaptcha',
        'gstatic.com',
        'seondnsresolve.com',
        'seondfresolver.com',
        'deviceinfresolver.com',
        'seonintelligence.com',
        'cdn.ashbyprd.com',  # CDN assets (fonts, etc.)
    ]
    # Only block non-essential external resources
    if any(pattern in url for pattern in blocked_patterns):
        route.abort()
        return
    route.continue_()


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-font-subpixel-positioning',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
        )
        page = context.new_page()

        # Block slow/external resources BEFORE navigation
        page.route('**/*', handle_route)

        try:
            print('Step 1: Navigating to Keyrock job page (blocking external resources)...')
            # Use 'commit' to get past the initial load even if external resources fail
            page.goto(APPLICATION_URL, wait_until='commit', timeout=15000)
            print(f'Initial response received. URL: {page.url}')

            # Wait for main app content to render
            time.sleep(8)

            title = page.title()
            print(f'Page title: {title}')

            screenshot(page, 'keyrock-01-job-page.png')

            body_text = page.evaluate('() => document.body.innerText')
            print('Page text (first 1500 chars):')
            print(body_text[:1500])

        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
            try:
                screenshot(page, 'keyrock-error.png')
            except Exception:
                pass

        browser.close()
        print('\nDone.')


if __name__ == '__main__':
    main()
