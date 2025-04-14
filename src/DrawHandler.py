from playwright.sync_api import Page

import RedeemAutofill
import RetryHelper
from ImageProcessor import find_correct_lottery_logo, detect_reward
from StringUtil import extract_price, extract_number


def run(page: Page):
    draw_button_locator = page.get_by_role("img").nth(2)
    screen_locator = page.locator(".panelTitle-6aEu3I").filter(has_text="Prize Draw")
    if RetryHelper.retry_until_screen_appears(screen_locator, draw_button_locator):
        if find_correct_lottery_logo(page):
            current_point = page.locator(".lotteryPointValue-qM8enE").inner_text()
            draw_pirce_text = page.locator(".lotteryCost-D-QGTv").inner_text()
            draw_price = extract_price(draw_pirce_text)
            max_draw_afford = int(current_point) // draw_price
            print(f"Max draw you can afford: {max_draw_afford}")

            draw_limit_text = page.locator(".lotteryLimitCount-fqLQOi").inner_text()
            draw_limit = extract_number(draw_limit_text)
            print(f"Max draw available: {draw_limit}")

            available_draw = min(max_draw_afford, draw_limit)
            print(f"Available draw: {available_draw}")

            draw_button = page.locator(".lotteryBtnCover-xI-MlR")
            draw_dialog = page.get_by_text("Congratulations, you've")
            draw_button.click()
            page.wait_for_timeout(5000)

            if draw_dialog.is_visible():
                reward_img = page.get_by_role("img")
                reward_name = detect_reward(page, reward_img)
                code = page.locator("gainCodeCopyInput-QcgdvD")
                RedeemAutofill.run(page.context, code, reward_name)
            close_draw = page.locator(".gainClose-7Q0hz8")
            close_draw.click()
