"""Test script to verify shopping points extraction.

This will open the browser, navigate to shopping page, and extract current points.
"""

import logging

from playwright.sync_api import sync_playwright

import ShoppingHandler
from GlobalVar import CONFIG

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_shopping_points():
    """Test shopping points extraction."""
    print("=" * 70)
    print("SHOPPING POINTS EXTRACTION TEST")
    print("=" * 70)
    print("\nThis will:")
    print("1. Open Firefox browser (visible)")
    print("2. Navigate to the HoYoLab shopping page")
    print("3. Extract your current points")
    print("4. Show debug logs of the extraction process")
    print("\nPress Ctrl+C to cancel, or wait for browser to open...")
    print("=" * 70)

    try:
        with sync_playwright() as p:
            # Launch browser (visible for debugging)
            browser = p.firefox.launch(headless=False)

            # Use saved session
            context = browser.new_context(storage_state=CONFIG["STORAGE_PATH"])
            page = context.new_page()

            # Navigate to event page
            print("\nNavigating to HoYoLab event page...")
            page.goto(
                "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
            )
            page.wait_for_timeout(3000)

            # Run shopping handler following the correct flow
            print("\nStep 1: Opening shopping screen...")
            shopping_button = page.get_by_role("img").nth(1)
            shopping_screen = page.locator(".wrapper-O3T67n")

            # Use retry logic like the bot does
            import RetryHelper

            if not RetryHelper.retry_until_screen_appears(
                shopping_screen, shopping_button
            ):
                print("ERROR: Could not open shopping screen!")
                browser.close()
                return

            print("Shopping screen opened successfully!")
            page.wait_for_timeout(2000)  # Extra wait for content to load

            print("Step 2: Finding and clicking ZZZ avatar...")
            from ImageProcessor import find_correct_avatar

            zzz_avatar = find_correct_avatar(page)
            if not zzz_avatar:
                print("ERROR: Could not find ZZZ avatar!")
                browser.close()
                return

            zzz_avatar.click()
            print("Step 3: Waiting for points to load...")
            page.wait_for_timeout(1000)

            print("Step 4: Extracting points...")
            print("-" * 70)

            try:
                points = ShoppingHandler._extract_current_points(page)
                print("-" * 70)
                print(f"\n[SUCCESS] Extracted points: {points}")
                print(f"[SUCCESS] Your current points: {points}")

            except Exception as e:
                print("-" * 70)
                print(f"\n[ERROR] {e}")
                print("\nPlease check the debug logs above to see what went wrong.")

            print("\n" + "=" * 70)
            print("Test complete. Browser will close in 5 seconds...")
            print("=" * 70)
            page.wait_for_timeout(5000)

            browser.close()

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_shopping_points()
