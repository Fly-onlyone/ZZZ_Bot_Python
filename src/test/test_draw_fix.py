"""Quick test to verify the draw limit fix is working."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import DrawHandler

# Storage path for authentication
STORAGE_PATH = Path(__file__).parent.parent.parent / "authentication data" / "hoyo.json"


def test_draw_with_fix():
    """Test that DrawHandler correctly stops when no draws available."""
    print("=" * 70)
    print("TESTING DRAW HANDLER WITH FIX")
    print("=" * 70)
    print("\nThis will run the actual DrawHandler.run() function")
    print("to verify it stops correctly when draws are exhausted.\n")

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.firefox.launch(headless=False)
            context = browser.new_context(storage_state=str(STORAGE_PATH))
            page = context.new_page()

            print("Navigating to HoYoLab...")
            page.goto("https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...")
            page.wait_for_timeout(3000)

            print("\nRunning DrawHandler.run()...")
            print("-" * 70)

            # This should log and exit without attempting draws
            DrawHandler.run(page)

            print("-" * 70)
            print("\nCheck the output above:")
            print("- Should see 'Draw calculation:' with all values")
            print("- Should see 'No draws available' and stop")
            print("- Should NOT see 'Performing draw 1/...'")
            print("- Should NOT see 'Draw result dialog not visible'")

            print("\n" + "=" * 70)
            print("Browser will close in 5 seconds...")
            print("=" * 70)
            page.wait_for_timeout(5000)

            browser.close()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_draw_with_fix()
