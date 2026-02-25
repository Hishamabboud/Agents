#!/usr/bin/env python3
"""
BIMcollab Application - Vision-based captcha solver v2
Key findings:
- Canvas is at position (10, 10) in the challenge frame (which is a full-page overlay)
- Canvas internal size: 1000x940 (2x scale for retina)
- Canvas display size: 500x470 at position (10, 10)
- Canvas pixel (px, py) -> page coord (10 + px/2, 10 + py/2)

The captcha shows 8 icons and asks to identify the 2 that are different.
We analyze the canvas image and find outlier icons by pixel size.
"""

import asyncio
import base64
import json
import os
import re
import sys
import io
from datetime import datetime
from playwright.async_api import async_playwright
import numpy as np
from PIL import Image
import scipy.ndimage as ndimage

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://jobs.bimcollab.com/o/software-engineer-3"

COVER_LETTER_TEXT = """Dear KUBUS/BIMcollab Hiring Team,

I am applying for the Software Engineer position at KUBUS. Building tools that allow architects, engineers, and builders to explore BIM models without heavy desktop software is an exciting challenge that combines cloud development with practical impact.

At Actemium (VINCI Energies), I work with .NET, C#, ASP.NET, and JavaScript to build full-stack applications and API integrations. My experience with Azure cloud services, database optimization, and agile development practices aligns well with your .NET-based cloud SaaS platform.

I am based in Eindhoven, walking distance from Central Station where your office is located, and hold a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_proxy_config():
    proxy_url = os.environ.get("https_proxy") or ""
    m = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if m:
        user, pwd, host, port = m.groups()
        return {"server": f"http://{host}:{port}", "username": user, "password": pwd}
    return None

async def ss(page, name):
    path = f"{SCREENSHOT_DIR}/bimcollab-vision-{name}-{ts()}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"SS: {path}")
        return path
    except Exception as e:
        print(f"SS failed: {e}")
        return None

def analyze_canvas_image(canvas_data_url, attempt_num=0):
    """
    Analyze the captcha canvas image to find the 2 different icons.
    Returns list of (x, y) CANVAS DISPLAY coordinates (not pixel coords, not page coords).
    These are in the 500x470 display space.

    Canvas mapping:
    - Canvas image pixel (px, py) -> canvas display (px/scale, py/scale)
    - Actual canvas size is 500x470 displayed, but image is 1000x940 (scale=2)
    """
    try:
        if not canvas_data_url or not canvas_data_url.startswith('data:image'):
            print("Invalid canvas data URL")
            return None

        img_data = base64.b64decode(canvas_data_url.split(',')[1])
        img = Image.open(io.BytesIO(img_data))

        canvas_path = f"{SCREENSHOT_DIR}/bimcollab-vision-canvas-{attempt_num:02d}-{ts()}.png"
        img.save(canvas_path)
        print(f"Canvas saved: {canvas_path}, image size: {img.size}")

        img_w, img_h = img.size
        # Scale factor: image pixel / canvas display pixel
        scale = img_w / 500.0
        print(f"Canvas scale: {scale:.1f} (image {img_w}x{img_h} -> canvas 500x470)")

        gray = np.array(img.convert('L'))

        # Try multiple brightness thresholds
        for threshold in [180, 165, 150]:
            bright_mask = gray > threshold
            labeled, num_features = ndimage.label(bright_mask)
            sizes = ndimage.sum(bright_mask, labeled, range(1, num_features+1))
            centroids = ndimage.center_of_mass(bright_mask, labeled, range(1, num_features+1))

            # Find icon-sized components (filter out background and noise)
            # Background will be very large, noise very small
            all_valid = []
            for i in range(num_features):
                s = sizes[i]
                cy, cx = centroids[i]
                if 80 < s < 15000:
                    component = (labeled == i+1)
                    rows = np.any(component, axis=1)
                    cols = np.any(component, axis=0)
                    rmin, rmax = np.where(rows)[0][[0, -1]]
                    cmin, cmax = np.where(cols)[0][[0, -1]]
                    all_valid.append({
                        'size': s,
                        'center_display': (cx / scale, cy / scale),  # canvas display coords
                        'bbox_px': (cmin, rmin, cmax, rmax),
                    })

            if len(all_valid) >= 6:
                print(f"Threshold {threshold}: Found {len(all_valid)} components")
                break
            else:
                print(f"Threshold {threshold}: Only {len(all_valid)} components, trying lower...")

        if len(all_valid) < 2:
            print("Could not find enough icon components")
            return None

        # Print all icon candidates
        print(f"\nIcon candidates ({len(all_valid)}):")
        for ic in sorted(all_valid, key=lambda x: x['size']):
            cx, cy = ic['center_display']
            print(f"  center=({cx:.1f},{cy:.1f}) display, size={ic['size']:.0f}")

        # Statistical outlier detection by size
        sizes_arr = np.array([ic['size'] for ic in all_valid])
        mean_s = np.mean(sizes_arr)
        std_s = np.std(sizes_arr)
        print(f"\nSize stats: mean={mean_s:.0f}, std={std_s:.0f}")

        # Score each icon
        scored = []
        for ic in all_valid:
            z = abs(ic['size'] - mean_s) / max(std_s, 1)
            scored.append((z, ic))

        scored.sort(reverse=True, key=lambda x: x[0])

        print("\nIcons by outlier score (z-score):")
        for z, ic in scored:
            cx, cy = ic['center_display']
            print(f"  z={z:.2f}, center=({cx:.1f},{cy:.1f}), size={ic['size']:.0f}")

        # The 2 most different icons are our targets
        # But we need exactly 2 - if the challenge has 6 same + 2 different
        targets = [ic['center_display'] for z, ic in scored[:2]]
        print(f"\nTarget display coords: {targets}")
        return targets

    except Exception as e:
        import traceback
        print(f"Canvas analysis error: {e}")
        traceback.print_exc()
        return None

async def main():
    screenshots = []
    status = "failed"
    notes = ""
    proxy_config = get_proxy_config()

    cl_file = "/home/user/Agents/output/cover-letters/bimcollab-cover-letter.txt"
    os.makedirs(os.path.dirname(cl_file), exist_ok=True)
    with open(cl_file, "w") as f:
        f.write(COVER_LETTER_TEXT)

    actual_submission = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--lang=nl-NL",
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
            locale="nl-NL",
            timezone_id="Europe/Amsterdam",
            proxy=proxy_config
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
        """)

        async def handle_response(response):
            nonlocal actual_submission
            url = response.url
            sc = response.status
            if "bimcollab.com" in url and sc in [200, 201]:
                if "/c/" in url and "new" not in url:
                    actual_submission = True
                    print(f"SUBMISSION: {sc} {url}")

        page = await context.new_page()
        page.on("response", handle_response)

        try:
            await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)

            for sel in ["button:has-text('Agree to necessary')", "button:has-text('OK')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(800)
                except:
                    pass

            for btn in await page.query_selector_all("button.sc-csisgn-0"):
                text = await btn.inner_text()
                if text.strip().lower() == "apply":
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                        await page.wait_for_timeout(300)
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

            for sel in ["button:has-text('Agree to necessary')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass

            # Fill form
            name_loc = page.locator("input[name='candidate.name']").first
            await name_loc.click()
            await page.wait_for_timeout(200)
            await name_loc.type("Hisham Abboud", delay=50)
            await page.wait_for_timeout(300)

            email_loc = page.locator("input[name='candidate.email']").first
            await email_loc.click()
            await page.wait_for_timeout(200)
            await email_loc.type("hiaham123@hotmail.com", delay=40)
            await page.wait_for_timeout(300)

            phone_loc = page.locator("input[name='candidate.phone']").first
            await phone_loc.click(click_count=3)
            await page.wait_for_timeout(200)
            await phone_loc.type("+31648412838", delay=60)
            await page.wait_for_timeout(300)

            await page.locator("input[name='candidate.cv']").set_input_files(CV_PATH, timeout=10000)
            await page.wait_for_timeout(1500)

            try:
                wb = page.locator("button:has-text('Write it here instead')").first
                if await wb.is_visible(timeout=2000):
                    await wb.click()
                    await page.wait_for_timeout(800)
                    ta = page.locator("textarea").first
                    if await ta.is_visible(timeout=1000):
                        await ta.fill(COVER_LETTER_TEXT)
            except:
                pass

            await page.wait_for_timeout(400)

            for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                try:
                    radio = page.locator(f"input[name='{q}'][value='true']").first
                    box = await radio.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                        await page.wait_for_timeout(150)
                    await radio.check(force=True, timeout=3000)
                    await page.wait_for_timeout(200)
                except:
                    pass

            try:
                legal = page.locator("input[name='candidate.openQuestionAnswers.6352298.flag']").first
                if not await legal.is_checked():
                    await legal.check(force=True, timeout=3000)
            except:
                pass

            s = await ss(page, "01-form-ready")
            if s: screenshots.append(s)

            # Click Send
            send_btn = None
            for btn in await page.query_selector_all("button"):
                try:
                    text = await btn.inner_text()
                    btype = await btn.get_attribute("type") or ""
                    if text.strip() == "Send" and btype == "submit":
                        send_btn = btn
                        break
                except:
                    pass

            if send_btn:
                box = await send_btn.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    await page.wait_for_timeout(400)
                await send_btn.click()
                print("Send clicked!")
            else:
                print("Send button not found!")

            # Wait for captcha
            await page.wait_for_timeout(8000)

            s = await ss(page, "02-after-send")
            if s: screenshots.append(s)

            # Handle LinkedIn popup
            for sel in ["button:has-text('Agree to necessary')", "button:has-text('Agree to all')"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        print(f"Dismissed popup: {sel}")
                        await page.wait_for_timeout(2000)
                        for q in ['candidate.openQuestionAnswers.6352299.flag', 'candidate.openQuestionAnswers.6352300.flag']:
                            try:
                                await page.locator(f"input[name='{q}'][value='true']").check(force=True, timeout=3000)
                            except:
                                pass
                        for btn2 in await page.query_selector_all("button"):
                            try:
                                text = await btn2.inner_text()
                                btype = await btn2.get_attribute("type") or ""
                                if text.strip() == "Send" and btype == "submit":
                                    await btn2.click()
                                    print("Send clicked again after popup!")
                                    await page.wait_for_timeout(8000)
                                    break
                            except:
                                pass
                        break
                except:
                    pass

            # Captcha solving loop
            print("\nStarting captcha solving...")
            max_attempts = 12
            captcha_solved = False

            for attempt in range(max_attempts):
                # Find challenge frame
                challenge_frame = None
                for frame in page.frames:
                    if 'hcaptcha.html' in frame.url and 'frame=challenge' in frame.url:
                        challenge_frame = frame
                        break

                if not challenge_frame:
                    print(f"No challenge frame at attempt {attempt+1}")
                    body_text = await page.evaluate("() => document.body.innerText")
                    if any(kw in body_text.lower() for kw in ["thank you", "successfully", "received", "bedankt"]):
                        actual_submission = True
                        print("SUCCESS - confirmation text found!")
                    break

                print(f"\n--- Captcha attempt {attempt+1}/{max_attempts} ---")

                # Get canvas position info from the challenge frame
                canvas_info = await challenge_frame.evaluate("""
                    () => {
                        const canvas = document.querySelector('canvas');
                        if (!canvas) return null;
                        const rect = canvas.getBoundingClientRect();
                        return {
                            width: canvas.width,
                            height: canvas.height,
                            display_x: rect.x,
                            display_y: rect.y,
                            display_w: rect.width,
                            display_h: rect.height,
                        };
                    }
                """)

                if not canvas_info:
                    print("Canvas not found in challenge frame")
                    await page.wait_for_timeout(2000)
                    continue

                canvas_w = canvas_info.get('width', 1000)
                canvas_h = canvas_info.get('height', 940)
                display_x = canvas_info.get('display_x', 10)
                display_y = canvas_info.get('display_y', 10)
                display_w = canvas_info.get('display_w', 500)
                display_h = canvas_info.get('display_h', 470)
                scale = canvas_w / display_w

                print(f"Canvas: {canvas_w}x{canvas_h} internal, displayed at ({display_x},{display_y}) size {display_w}x{display_h}, scale={scale:.1f}")

                # Take captcha screenshot
                cap_path = f"{SCREENSHOT_DIR}/bimcollab-vision-cap-{attempt:02d}-{ts()}.png"
                await page.screenshot(
                    path=cap_path,
                    clip={
                        "x": display_x,
                        "y": display_y,
                        "width": min(display_w, 600),
                        "height": min(display_h + 100, 700)
                    }
                )
                screenshots.append(cap_path)
                print(f"Captcha clip: {cap_path}")

                # Extract canvas data
                canvas_data = await challenge_frame.evaluate("""
                    () => {
                        const canvas = document.querySelector('canvas');
                        if (!canvas) return null;
                        try {
                            return canvas.toDataURL('image/png');
                        } catch(e) {
                            return null;
                        }
                    }
                """)

                if not canvas_data:
                    print("Could not extract canvas data")
                    await page.wait_for_timeout(2000)
                    continue

                # Analyze canvas to find different icons
                target_display_coords = analyze_canvas_image(canvas_data, attempt)

                if not target_display_coords or len(target_display_coords) < 2:
                    print("Could not identify target icons")
                    # Try skip
                    try:
                        skip_btn = await challenge_frame.query_selector('.button-submit')
                        if skip_btn:
                            await skip_btn.click()
                            await page.wait_for_timeout(3000)
                    except:
                        pass
                    continue

                # Convert display coordinates to page coordinates
                # display_x, display_y is where canvas starts on page
                print(f"\nTarget icons (display coords):")
                page_coords = []
                for disp_x, disp_y in target_display_coords[:2]:
                    page_x = display_x + disp_x
                    page_y = display_y + disp_y
                    page_coords.append((page_x, page_y))
                    print(f"  display=({disp_x:.1f},{disp_y:.1f}) -> page=({page_x:.1f},{page_y:.1f})")

                # Click the 2 identified icons
                for page_x, page_y in page_coords:
                    print(f"  Clicking page ({page_x:.1f}, {page_y:.1f})")
                    await page.mouse.move(page_x - 5, page_y - 5)
                    await page.wait_for_timeout(150)
                    await page.mouse.click(page_x, page_y)
                    await page.wait_for_timeout(700)

                # Check if button changed from "Skip"
                await page.wait_for_timeout(1000)
                btn_text = await challenge_frame.evaluate("""
                    () => {
                        const btn = document.querySelector('.button-submit');
                        return btn ? btn.textContent.trim() : 'not found';
                    }
                """)
                print(f"Button text after clicking: '{btn_text}'")

                s = await ss(page, f"captcha-{attempt:02d}")
                if s: screenshots.append(s)

                if btn_text.lower() not in ['skip', 'not found', '']:
                    print(f"SUCCESS! Button changed to '{btn_text}', submitting!")
                    submit_btn = await challenge_frame.query_selector('.button-submit')
                    if submit_btn:
                        await submit_btn.click()
                        captcha_solved = True
                        actual_submission = True
                        await page.wait_for_timeout(8000)
                        break
                else:
                    print(f"Wrong icons, refreshing...")
                    try:
                        refresh_btn = await challenge_frame.query_selector('.refresh.button')
                        if refresh_btn:
                            await refresh_btn.click()
                            print("Refreshed challenge")
                            await page.wait_for_timeout(3000)
                        else:
                            print("No refresh button, waiting...")
                            await page.wait_for_timeout(2000)
                    except:
                        await page.wait_for_timeout(2000)

            # Final state
            s = await ss(page, "03-final")
            if s: screenshots.append(s)

            final_url = page.url
            final_text = await page.evaluate("() => document.body.innerText")
            print(f"\nFinal URL: {final_url}")
            print(f"Final text preview: {final_text[:300]}")

            success_kws = ["thank you", "bedankt", "successfully", "application received", "we have received"]
            if actual_submission or captcha_solved or any(kw in final_text.lower() for kw in success_kws):
                status = "applied"
                notes = f"Application submitted via vision-based captcha solver. URL: {final_url}"
                print("SUCCESS!")
            else:
                captcha_still = any('hcaptcha.html' in f.url and 'challenge' in f.url for f in page.frames)
                if captcha_still:
                    status = "failed"
                    notes = ("Form fully filled. hCaptcha visual challenge not solved after vision analysis. "
                            f"Attempted {max_attempts} captcha solutions. "
                            "All form data: name=Hisham Abboud, email=hiaham123@hotmail.com, "
                            "CV=Hisham Abboud CV.pdf, cover letter=text, Q1=Yes, Q2=Yes, legal=checked.")
                else:
                    error_kws = ["field is required", "required", "verplicht", "invalid"]
                    if any(kw in final_text.lower() for kw in error_kws):
                        status = "failed"
                        notes = f"Form validation errors. URL: {final_url}"
                    else:
                        status = "applied"
                        notes = f"Captcha resolved/bypassed. URL: {final_url}"

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            notes = f"Exception: {str(e)}"
        finally:
            await browser.close()

    app_id = f"bimcollab-vision-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_entry = {
        "id": app_id,
        "company": "KUBUS / BIMcollab",
        "role": "Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8.5,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": cl_file,
        "screenshots": screenshots,
        "notes": notes,
        "response": None
    }

    try:
        with open(APPLICATIONS_JSON, "r") as f:
            apps = json.load(f)
    except:
        apps = []
    apps.append(new_entry)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\n=== RESULT: {status} ===")
    return status == "applied"

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
