
import pytest
from playwright.sync_api import sync_playwright

from GlobalVar import CONFIG
from RedeemAutofill import run

# Fixture to create Playwright browser context
@pytest.fixture
def browser_context():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context_options = (
            {"storage_state": "./output/account.json"}
        )
        context = browser.new_context(**context_options)
        yield context
        # ✅ Save browser state after test
        context.storage_state(path="./output/account.json")
        browser.close()

# Actual test using the fixture
def test_redeem(browser_context):
    run(browser_context, "test_code", "test_item", "test_day", CONFIG["REDEEM_FILE"])

