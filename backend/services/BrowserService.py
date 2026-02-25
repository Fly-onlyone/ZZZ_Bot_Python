"""
Browser Automation Service

Provides browser automation capabilities using Playwright.
Implements the Dependency Inversion Principle by abstracting browser operations.
"""

import logging
import os
from contextlib import contextmanager
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext, Page

from utils.screenshot_store import save_page_screenshot

logger = logging.getLogger(__name__)


class BrowserService:
    """
    Service for managing browser automation tasks.

    Separates browser concerns from business logic, enabling:
    - Unit testing without actual browser
    - Easy browser configuration changes
    - Dependency Inversion Principle compliance
    """

    def __init__(self, headless: bool = True, browser_type: str = "firefox"):
        """
        Initialize the browser service.

        Args:
            headless: Whether to run browser in headless mode
            browser_type: Browser to use ('firefox', 'chromium', 'webkit')
        """
        self.headless = headless
        self.browser_type = browser_type

    @contextmanager
    def create_browser_session(
        self, storage_path: Optional[str] = None, url: Optional[str] = None
    ):
        """
        Context manager for browser session lifecycle.

        Handles browser creation, context setup, navigation, and cleanup.

        Args:
            storage_path: Path to saved authentication state
            url: URL to navigate to (optional)

        Yields:
            tuple: (browser, context, page)

        Example:
            with service.create_browser_session(storage_path, url) as (browser, context, page):
                # Do automation work
                page.click("button")
        """
        browser = None
        try:
            with sync_playwright() as p:
                # Launch browser
                browser_launcher = getattr(p, self.browser_type)
                browser = browser_launcher.launch(headless=self.headless)

                # Create context with optional storage state
                context_options = {}
                if storage_path and os.path.exists(storage_path):
                    context_options["storage_state"] = storage_path
                    logger.info(f"Loading authentication state from {storage_path}")
                else:
                    logger.info("No authentication state found, starting fresh session")

                context = browser.new_context(**context_options)
                page = context.new_page()

                # Navigate to URL if provided
                if url:
                    logger.info(f"Navigating to {url}")
                    page.goto(url)

                yield browser, context, page

        except Exception as e:
            logger.error(f"Browser session error: {e}")
            raise
        finally:
            if browser:
                browser.close()
                logger.info("Browser closed")

    def save_session_state(self, context: BrowserContext, storage_path: str) -> None:
        """
        Save browser session state (cookies, localStorage, etc.).

        Args:
            context: Browser context to save
            storage_path: Path to save state file
        """
        try:
            context.storage_state(path=storage_path)
            logger.info(f"Session state saved to {storage_path}")
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            raise

    def is_authenticated(self, storage_path: str) -> bool:
        """
        Check if authentication state exists.

        Args:
            storage_path: Path to check for stored authentication

        Returns:
            bool: True if authenticated state exists
        """
        return os.path.exists(storage_path)

    @staticmethod
    def click_element(
        page: Page, selector: str, force: bool = False, timeout: int = 5000
    ) -> bool:
        """
        Click an element with error handling.

        Args:
            page: Playwright page object
            selector: CSS selector for element
            force: Force click even if element is obscured
            timeout: Timeout in milliseconds

        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            element = page.locator(selector)
            if element.count() > 0:
                element.click(force=force, timeout=timeout)
                logger.info(f"Clicked element: {selector}")
                return True
            else:
                logger.warning(f"Element not found: {selector}")
                return False
        except Exception as e:
            logger.error(f"Failed to click {selector}: {e}")
            return False

    @staticmethod
    def wait_for_element(
        page: Page, selector: str, state: str = "visible", timeout: int = 5000
    ) -> bool:
        """
        Wait for an element to reach a specific state.

        Args:
            page: Playwright page object
            selector: CSS selector for element
            state: Element state ('visible', 'hidden', 'attached', 'detached')
            timeout: Timeout in milliseconds

        Returns:
            bool: True if element reached state, False otherwise
        """
        try:
            page.wait_for_selector(selector, state=state, timeout=timeout)
            logger.info(f"Element {selector} is {state}")
            return True
        except Exception as e:
            logger.warning(f"Element {selector} did not reach {state}: {e}")
            return False

    @staticmethod
    def close_overlay(
        page: Page,
        close_button_selector: str = ".panelBack--wW5qj",
        max_attempts: int = 3,
    ) -> bool:
        """
        Close an overlay/modal with retry logic.

        Args:
            page: Playwright page object
            close_button_selector: Selector for close button
            max_attempts: Maximum number of attempts

        Returns:
            bool: True if overlay closed successfully
        """
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Attempting to close overlay (attempt {attempt}/{max_attempts})"
                )

                close_button = page.locator(close_button_selector)
                if close_button.count() > 0 and close_button.is_visible(timeout=2000):
                    close_button.click(force=True)
                    page.wait_for_timeout(500)
                    logger.info("Overlay close button clicked")
                    return True

                # Try Escape key as fallback
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                logger.info("Pressed Escape key")

            except Exception as e:
                logger.warning(f"Close attempt {attempt} failed: {e}")

        logger.error("Failed to close overlay after all attempts")
        return False

    @staticmethod
    def take_screenshot(page: Page, path: str, full_page: bool = False) -> None:
        """
        Take a screenshot of the current page.

        Args:
            page: Playwright page object
            path: Path to save screenshot
            full_page: Whether to capture full scrollable page
        """
        try:
            asset_id = save_page_screenshot(page, os.path.basename(path), full_page=full_page)
            logger.info("Screenshot saved to MongoDB asset: %s", asset_id)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
