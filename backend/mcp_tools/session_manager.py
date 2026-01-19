"""Persistent browser session manager for MCP inspector tools.

Provides a singleton browser session that persists across tool calls,
eliminating the overhead of spawning a new browser for each inspection.

Usage:
    session = await BrowserSession.get_instance()
    page = await session.ensure_page(url)
    # ... use page for inspection
    # Session auto-closes on module unload or explicit close()
"""

import asyncio
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)


class BrowserSession:
    """Singleton browser session with persistent authentication.

    Maintains a single browser instance across multiple tool calls,
    using the bot's saved authentication state for logged-in access.
    """

    _instance: Optional["BrowserSession"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._current_url: Optional[str] = None
        self._storage_path: Optional[str] = None

    @classmethod
    async def get_instance(cls, storage_path: str = None) -> "BrowserSession":
        """Get or create the singleton browser session.

        Args:
            storage_path: Path to authentication state JSON.
                          Required on first call, optional afterwards.

        Returns:
            The singleton BrowserSession instance.
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            if storage_path:
                cls._instance._storage_path = storage_path
            return cls._instance

    @property
    def is_active(self) -> bool:
        """Check if browser session is currently active."""
        return self._browser is not None and self._browser.is_connected()

    @property
    def current_url(self) -> Optional[str]:
        """Get the current page URL, if any."""
        return self._current_url

    @property
    def page(self) -> Optional[Page]:
        """Get the current page, if any."""
        return self._page

    async def ensure_page(
        self,
        url: str = None,
        wait_strategy: str = "networkidle",
        wait_timeout_ms: int = 30000,
        headless: bool = True,
    ) -> Page:
        """Ensure a page is open and optionally navigate to URL.

        Args:
            url: URL to navigate to. If None, returns current page.
            wait_strategy: How to wait after navigation.
                          'networkidle' - Wait until no network requests for 500ms
                          'load' - Wait for load event
                          'domcontentloaded' - Wait for DOMContentLoaded
                          'commit' - Wait for response received
                          'none' - Don't wait after goto
            wait_timeout_ms: Timeout for wait operations in milliseconds.
            headless: Whether to run browser headless.

        Returns:
            The active Page instance.

        Raises:
            ValueError: If storage_path not set on first call.
        """
        # Start browser if not running
        if not self.is_active:
            await self._start_browser(headless)

        # Navigate if URL provided and different from current
        if url and url != self._current_url:
            await self._navigate(url, wait_strategy, wait_timeout_ms)

        return self._page

    async def _start_browser(self, headless: bool = True) -> None:
        """Start browser with authenticated context."""
        if not self._storage_path:
            raise ValueError("storage_path must be set before starting browser")

        logger.info(f"Starting browser session (headless={headless})")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.firefox.launch(headless=headless)
        self._context = await self._browser.new_context(
            storage_state=self._storage_path
        )
        self._page = await self._context.new_page()

        logger.info("Browser session started successfully")

    async def _navigate(
        self, url: str, wait_strategy: str, wait_timeout_ms: int
    ) -> None:
        """Navigate to URL with specified wait strategy."""
        logger.info(f"Navigating to {url} (wait={wait_strategy})")

        # Map wait strategies to Playwright wait states
        wait_until_map = {
            "networkidle": "networkidle",
            "load": "load",
            "domcontentloaded": "domcontentloaded",
            "commit": "commit",
            "none": None,
        }

        wait_until = wait_until_map.get(wait_strategy, "networkidle")

        if wait_until:
            await self._page.goto(url, wait_until=wait_until, timeout=wait_timeout_ms)
        else:
            await self._page.goto(url, timeout=wait_timeout_ms)

        self._current_url = url
        logger.info(f"Navigation complete: {await self._page.title()}")

    async def close(self) -> dict:
        """Close the browser session and release resources.

        Returns:
            dict with status and any error message.
        """
        async with self._lock:
            if not self.is_active:
                return {"status": "already_closed", "message": "No active session"}

            try:
                logger.info("Closing browser session")

                if self._page:
                    await self._page.close()
                if self._context:
                    await self._context.close()
                if self._browser:
                    await self._browser.close()
                if self._playwright:
                    await self._playwright.stop()

                self._page = None
                self._context = None
                self._browser = None
                self._playwright = None
                self._current_url = None

                logger.info("Browser session closed successfully")
                return {"status": "closed", "message": "Session closed successfully"}

            except Exception as e:
                logger.error(f"Error closing session: {e}")
                return {"status": "error", "message": str(e)}

    async def refresh(self) -> None:
        """Refresh the current page."""
        if self._page:
            await self._page.reload(wait_until="networkidle")
            logger.info("Page refreshed")

    async def wait_for_spa_render(self, timeout_ms: int = 5000) -> None:
        """Wait for SPA content to render after navigation.

        Useful for single-page applications that load content dynamically.

        Args:
            timeout_ms: How long to wait in milliseconds.
        """
        if self._page:
            await self._page.wait_for_timeout(timeout_ms)


# Convenience function for quick access
async def get_session(storage_path: str = None) -> BrowserSession:
    """Get the singleton browser session.

    Args:
        storage_path: Path to authentication state JSON.

    Returns:
        The BrowserSession singleton.
    """
    return await BrowserSession.get_instance(storage_path)
