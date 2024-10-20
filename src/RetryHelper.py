from playwright.sync_api import Locator
import time

class RetryHelper:
    @staticmethod
    def retry_until_screen_appears(screen: Locator, button: Locator, max_retries: int = 10, delay_ms: int = 1000):
        for attempt in range(1, max_retries + 1):
            try:
                # Wait for button to become visible and click it
                button.wait_for(state='visible')
                button.click()
                print('Clicked on "Carry out missions to earn".')

                # Check if the target screen becomes visible
                if screen.is_visible():
                    print('Target screen appeared.')
                    return True
                print(f'Attempt {attempt}: Target screen not yet visible, retrying...')
            except Exception as e:
                print(f'Error: {e}')

            # Wait before retrying
            time.sleep(delay_ms / 1000)

        print('Max retries reached. Target screen did not appear.')
        return False

    @staticmethod
    def retry_until_non_zero_count(locator: Locator, max_retries: int = 10, delay_ms: int = 1000) -> int:
        count = 0
        for attempt in range(1, max_retries + 1):
            count = locator.count()
            if count > 0:
                print(f'Non-zero count found: {count} (Attempt {attempt})')
                return count
            print(f'Attempt {attempt}: Count is 0, retrying...')

            # Wait before retrying
            time.sleep(delay_ms / 1000)

        print('Max retries reached. Count is still 0.')
        return count
