from playwright.sync_api import Locator


def retry_until_screen_appears(screen: Locator, button: Locator, max_retries: int = 10, delay_ms: int = 1000):
    for attempt in range(1, max_retries + 1):
        # Wait for button to become visible and click it
        button.wait_for(state='visible')
        button.click(force=True)
        print('Clicked on button.')

        # Check if the target screen becomes visible
        if screen.is_visible():
            print('Target screen appeared.')
            return True
        print(f'Attempt {attempt}: Target screen not yet visible, retrying...')

        # Wait before retrying
        button.page.wait_for_timeout(delay_ms)

    print('Max retries reached. Target screen did not appear.')
    return False


def retry_until_non_zero_count(locator: Locator, max_retries: int = 10, delay_ms: int = 1000) -> int:
    count = 0
    for attempt in range(1, max_retries + 1):
        count = locator.count()
        if count > 0:
            print(f'Non-zero count found: {count} (Attempt {attempt})')
            return count
        print(f'Attempt {attempt}: Count is 0, retrying...')

        # Wait before retrying
        locator.page.wait_for_timeout(delay_ms)

    print('Max retries reached. Count is still 0.')
    return count
