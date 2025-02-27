import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(storage_state="./authentication data/hoyo.json")
    page = context.new_page()
    page.goto("https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...")
    page.get_by_role("img").nth(2).click()
    page.locator(".lotteryBtnCover-xI-MlR").click()
    switch_draw_game = page.locator(".lotterySwitch-LdUVnT")
    draw_button = page.locator(".lotteryBtnCover-xI-MlR")
    draw_dialog = page.get_by_text("Congratulations, you've")
    reward_img = page.get_by_role("img")
    page.get_by_text("Copy", exact=True)
    code = page.locator("gainCodeCopyInput-QcgdvD")
    close_draw = page.locator(".gainClose-7Q0hz8")
    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
