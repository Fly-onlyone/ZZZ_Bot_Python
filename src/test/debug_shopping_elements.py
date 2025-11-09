"""Debug script to find the correct points element."""
import logging
from playwright.sync_api import sync_playwright
from GlobalVar import CONFIG

logging.basicConfig(level=logging.INFO)

def debug_elements():
    """Find all possible points elements on the page."""
    print("=" * 70)
    print("DEBUGGING SHOPPING POINTS ELEMENTS")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=CONFIG["STORAGE_PATH"])
        page = context.new_page()

        print("\nNavigating to page...")
        page.goto("https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...")
        page.wait_for_timeout(3000)

        # Click shopping button
        print("Opening shopping screen...")
        shopping_button = page.get_by_role("img").nth(1)
        shopping_button.click()
        page.wait_for_timeout(3000)

        # Find all elements with the class
        print("\n" + "=" * 70)
        print("Looking for '.bubbleCnt-hsQFy-' elements:")
        print("=" * 70)

        elements = page.locator(".bubbleCnt-hsQFy-").all()
        print(f"\nFound {len(elements)} elements with class '.bubbleCnt-hsQFy-':\n")

        for i, elem in enumerate(elements):
            try:
                text = elem.inner_text()
                is_visible = elem.is_visible()
                print(f"  Element {i + 1}:")
                print(f"    Text: '{text}'")
                print(f"    Visible: {is_visible}")
                print(f"    HTML: {elem.evaluate('el => el.outerHTML')[:200]}")
                print()
            except Exception as e:
                print(f"  Element {i + 1}: Error - {e}\n")

        # Try to find elements containing numbers
        print("=" * 70)
        print("Looking for elements that might contain your 140 points:")
        print("=" * 70)

        # Check various selectors
        selectors_to_try = [
            ".bubbleCnt-hsQFy-",
            "[class*='bubble']",
            "[class*='point']",
            "[class*='Point']",
            "[class*='cnt']"
        ]

        for selector in selectors_to_try:
            try:
                elems = page.locator(selector).all()
                for elem in elems:
                    text = elem.inner_text()
                    if "140" in text or ("1" in text and "4" in text and "0" in text):
                        print(f"\n  POTENTIAL MATCH with selector '{selector}':")
                        print(f"    Text: '{text}'")
                        print(f"    HTML: {elem.evaluate('el => el.outerHTML')[:300]}")
            except:
                pass

        print("\n" + "=" * 70)
        print("Browser will stay open for 30 seconds so you can inspect.")
        print("Look at the page and find where your 140 points are displayed.")
        print("=" * 70)
        page.wait_for_timeout(30000)

        browser.close()

if __name__ == "__main__":
    debug_elements()
