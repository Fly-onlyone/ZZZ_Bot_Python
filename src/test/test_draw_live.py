"""Test script to diagnose draw limit detection issues.

This will open the browser, navigate to prize draw page, and show what values are extracted.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from StringUtil import extract_number, extract_price

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Selectors from DrawHandler.py
DRAW_BUTTON_INDEX = 2
SCREEN_SELECTOR = ".panelTitle-6aEu3I"
SCREEN_TEXT = "Prize Draw"
POINT_VALUE_SELECTOR = ".lotteryPointValue-qM8enE"
DRAW_COST_SELECTOR = ".lotteryCost-D-QGTv"
DRAW_LIMIT_SELECTOR = ".lotteryLimitCount-fqLQOi"
DRAW_BUTTON_SELECTOR = ".lotteryBtnCover-xI-MlR"

# Storage path for authentication
STORAGE_PATH = Path(__file__).parent.parent.parent / "authentication data" / "hoyo.json"


def test_draw_limit_detection():
    """Test draw limit extraction and calculation."""
    print("=" * 70)
    print("DRAW LIMIT DETECTION DIAGNOSTIC TEST")
    print("=" * 70)
    print("\nThis will:")
    print("1. Open Firefox browser (visible)")
    print("2. Navigate to the HoYoLab prize draw page")
    print("3. Extract and display all draw-related values")
    print("4. Show what the bot would calculate")
    print("\nBrowser will open shortly...")
    print("=" * 70)

    try:
        with sync_playwright() as p:
            # Launch browser (visible for debugging)
            print("\nLaunching browser...")
            browser = p.firefox.launch(headless=False)

            # Use saved session
            print(f"Loading session from: {STORAGE_PATH}")
            context = browser.new_context(storage_state=str(STORAGE_PATH))
            page = context.new_page()

            # Navigate to event page
            print("\nNavigating to HoYoLab event page...")
            page.goto(
                "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
            )
            page.wait_for_timeout(3000)

            # Click draw button
            print("\nStep 1: Opening prize draw screen...")
            draw_button = page.get_by_role("img").nth(DRAW_BUTTON_INDEX)
            draw_button.click()
            page.wait_for_timeout(3000)

            # Check for screen
            prize_screen = page.locator(SCREEN_SELECTOR).filter(has_text=SCREEN_TEXT)
            if not prize_screen.is_visible(timeout=5000):
                print("ERROR: Prize draw screen not visible!")
                browser.close()
                return

            print("[OK] Prize draw screen opened successfully!")
            page.wait_for_timeout(2000)

            print("\n" + "=" * 70)
            print("EXTRACTING VALUES FROM PAGE")
            print("=" * 70)

            # Get current points
            try:
                current_point_text = page.locator(POINT_VALUE_SELECTOR).inner_text()
                current_points = int(current_point_text.replace(",", ""))
                print(f"\n1. Current Points:")
                print(f"   Raw text: '{current_point_text}'")
                print(f"   Parsed value: {current_points}")
            except Exception as e:
                print(f"\n1. Current Points: ERROR - {e}")
                current_points = 0

            # Get draw cost
            try:
                draw_cost_text = page.locator(DRAW_COST_SELECTOR).inner_text()
                draw_price = extract_price(draw_cost_text)
                print(f"\n2. Draw Cost:")
                print(f"   Raw text: '{draw_cost_text}'")
                print(f"   Parsed value: ${draw_price}")
            except Exception as e:
                print(f"\n2. Draw Cost: ERROR - {e}")
                draw_price = 100

            # Calculate affordable
            max_affordable = current_points // draw_price if draw_price > 0 else 0
            print(f"\n3. Affordable Draws:")
            print(
                f"   Calculation: {current_points} // {draw_price} = {max_affordable}"
            )

            # Get draw limit
            try:
                draw_limit_text = page.locator(DRAW_LIMIT_SELECTOR).inner_text()
                print(f"\n4. Draw Limit:")
                print(f"   Raw text: '{draw_limit_text}'")
                print(f"   Length: {len(draw_limit_text)} characters")
                print(f"   Repr: {repr(draw_limit_text)}")
                print(f"   Bytes: {draw_limit_text.encode('utf-8')}")

                # Try to parse
                draws_used = extract_number(draw_limit_text, side="left")
                draws_total = extract_number(draw_limit_text, side="right")

                print(f"   Parsed left (used): {draws_used}")
                print(f"   Parsed right (total): {draws_total}")

                if draws_used is not None and draws_total is not None:
                    draws_remaining = draws_total - draws_used
                    print(
                        f"   Calculated remaining: {draws_total} - {draws_used} = {draws_remaining}"
                    )
                else:
                    draws_remaining = None
                    print(f"   ERROR: Could not parse draw limit!")

            except Exception as e:
                print(f"\n4. Draw Limit: ERROR - {e}")
                import traceback

                traceback.print_exc()
                draws_remaining = None
                draws_used = None
                draws_total = None

            # Final calculation
            print(f"\n" + "=" * 70)
            print("FINAL CALCULATION")
            print("=" * 70)

            if draws_remaining is not None:
                available_draws = min(max_affordable, draws_remaining)
                print(
                    f"Available draws = min({max_affordable} affordable, {draws_remaining} remaining)"
                )
                print(f"                = {available_draws}")

                if available_draws <= 0:
                    print(f"\n[CORRECT] Bot should NOT attempt any draws!")
                else:
                    print(f"\n[INFO] Bot will attempt {available_draws} draw(s)")
            else:
                print("[ERROR] Cannot calculate available draws due to parsing error")

            # Check button state
            print(f"\n" + "=" * 70)
            print("DRAW BUTTON STATE")
            print("=" * 70)

            try:
                draw_btn = page.locator(DRAW_BUTTON_SELECTOR)
                is_visible = draw_btn.is_visible(timeout=2000)
                is_enabled = draw_btn.is_enabled(timeout=1000)

                print(f"Button visible: {is_visible}")
                print(f"Button enabled: {is_enabled}")

                if not is_enabled:
                    print("[CORRECT] Button is disabled - should prevent draws")
                elif available_draws <= 0:
                    print("[BUG] Button is enabled but no draws available!")
                else:
                    print("[OK] Button is enabled and draws available")

            except Exception as e:
                print(f"ERROR checking button state: {e}")

            print("\n" + "=" * 70)
            print("TEST COMPLETE")
            print("Browser will close in 10 seconds...")
            print("=" * 70)
            page.wait_for_timeout(10000)

            browser.close()

    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_draw_limit_detection()
