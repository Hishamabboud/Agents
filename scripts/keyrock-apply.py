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
    'gender': 'Male ',  # optional
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
        "I am looking for a competitive compensation package in the range of EUR 70,000 - 85,000 "
        "per year, depending on the full benefits package and growth opportunities. I am open to "
        "discussing this further based on the role scope and Keyrock's compensation structure."
    ),
    'country': 'Netherlands',
    'fullstack_years': '4',
    'rust_cpp_years': (
        "I have 0 years of professional Rust experience, but I have hands-on experience with "
        "strongly-typed backend languages: 3+ years with C# (.NET) at Actemium and Delta "
        "Electronics, and 2+ years with Python. I am actively learning Rust and understand "
        "its ownership model, making me confident I can ramp up quickly."
    ),
    'privacy_consent': 'Yes',
    'cicd_gitlab': (
        "Yes - I have experience with CI/CD pipelines. At ASML I worked with Azure DevOps "
        "pipelines and Kubernetes for containerized deployments. At Actemium I work with "
        "Git-based workflows and automated testing pipelines. I have hands-on experience "
        "with Docker, Kubernetes, and infrastructure-as-code principles."
    ),
    'financial_datasets_years': (
        "1 year - I have built analytics dashboards and worked with structured data pipelines "
        "in industrial contexts (MES data, performance metrics). While not exclusively financial "
        "data, the skills of data modeling, query optimization, and dashboard development are "
        "directly transferable."
    ),
    'fintech_years': (
        "I do not have direct fintech/crypto industry experience, but I have strong engineering "
        "foundations and deep interest in financial technology. I am transitioning into the fintech "
        "space and Keyrock represents an excellent opportunity to apply my skills in this domain."
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


def fill_input(page, selector, value, description=''):
    """Fill an input field by selector."""
    try:
        el = page.wait_for_selector(selector, timeout=5000, state='visible')
        if el:
            el.click()
            el.fill(value)
            print(f'Filled {description or selector}: {value[:60]}')
            return True
    except Exception as e:
        print(f'Failed to fill {description or selector}: {e}')
    return False


def block_external_resources(route, request):
    """Block external resources that cause DNS failures."""
    blocked_domains = [
        'fullstory.com',
        'datadoghq.com',
        'sentry.io',
        'recaptcha',
        'gstatic.com',
        'fonts.googleapis.com',
        'fonts.gstatic.com',
        'seondnsresolve.com',
        'seondfresolver.com',
        'deviceinfresolver.com',
        'seonintelligence.com',
    ]
    url = request.url
    if any(domain in url for domain in blocked_domains):
        route.abort()
    else:
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
                '--font-render-hinting=none',
                '--disable-font-subpixel-positioning',
                '--disable-remote-fonts',
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
            # Block external fonts/tracking to avoid DNS issues
        )

        page = context.new_page()

        # Block external resources that fail DNS resolution
        page.route('**/*', block_external_resources)

        try:
            print('Step 1: Navigating to Keyrock job page...')
            page.goto(APPLICATION_URL, wait_until='domcontentloaded', timeout=30000)
            print('Page loaded (domcontentloaded)')
            time.sleep(3)

            title = page.title()
            print(f'Page title: {title}')
            print(f'Current URL: {page.url}')

            screenshot(page, 'keyrock-01-job-page.png')

            # Check page text
            body_text = page.evaluate('() => document.body.innerText')
            print('Page text (first 1000 chars):')
            print(body_text[:1000])

            # Step 2: Find and click the Apply button
            print('\nStep 2: Looking for Apply button...')

            # Wait for the Apply button
            apply_selectors = [
                'button:has-text("Apply")',
                'a:has-text("Apply")',
                '[data-testid*="apply"]',
                'button:has-text("Apply for this job")',
            ]

            apply_clicked = False
            for sel in apply_selectors:
                try:
                    btn = page.wait_for_selector(sel, timeout=3000, state='visible')
                    if btn:
                        print(f'Found apply button: {sel}')
                        btn.click()
                        apply_clicked = True
                        time.sleep(3)
                        break
                except Exception:
                    pass

            if not apply_clicked:
                # Maybe we're already on the form, or navigate directly to /application
                print('No apply button found, navigating to application URL...')
                page.goto(APPLICATION_URL + '/application', wait_until='domcontentloaded', timeout=30000)
                time.sleep(3)

            screenshot(page, 'keyrock-02-after-apply-click.png')
            print('After apply navigation - screenshot saved')

            # Check what's visible now
            body_text2 = page.evaluate('() => document.body.innerText')
            print('Page text after navigation (first 2000):')
            print(body_text2[:2000])

            # Find all inputs
            inputs = page.evaluate('''() => {
                const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                return inputs.map(el => ({
                    type: el.type || el.tagName.toLowerCase(),
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: (el.placeholder || '').substring(0, 50),
                    required: el.required,
                    visible: el.offsetParent !== null,
                    ariaLabel: el.getAttribute('aria-label') || '',
                    dataField: el.getAttribute('data-field-path') || el.getAttribute('data-testid') || ''
                }));
            }''')
            print(f'\nForm inputs ({len(inputs)} total):')
            for inp in inputs:
                if inp['visible']:
                    print(f"  [{inp['type']}] name={inp['name']} id={inp['id'][:40]} placeholder={inp['placeholder']} dataField={inp['dataField']} required={inp['required']}")

            # Get all buttons
            buttons = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('button, [role="button"]')).map(el => ({
                    text: (el.textContent || '').trim().substring(0, 60),
                    type: el.type || '',
                    id: el.id || '',
                    class: (el.className || '').substring(0, 60)
                }));
            }''')
            print('\nButtons found:')
            for btn in buttons:
                print(f"  [button] '{btn['text']}' type={btn['type']} id={btn['id']}")

        except Exception as e:
            print(f'Error in inspection: {e}')
            import traceback
            traceback.print_exc()
            try:
                screenshot(page, 'keyrock-inspect-error.png')
            except Exception:
                pass

        browser.close()
        print('\nInspection phase complete.')


if __name__ == '__main__':
    main()
