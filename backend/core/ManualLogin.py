import logging
import os
import threading
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from utils import NotificationHelper
from utils.storage_state_store import build_context_options, save_context_storage_state

from .GlobalVar import CONFIG

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Enum for manual login session states."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    CLOSING = "closing"
    ERROR = "error"


class ManualLoginManager:
    """Singleton manager for manual browser login sessions.

    Provides thread-safe management of manual login sessions with proper
    state tracking, error handling, and resource cleanup.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._state = SessionState.IDLE
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._current_url: Optional[str] = None
        self._initialized = True
        logger.info("ManualLoginManager initialized")

    @property
    def state(self) -> SessionState:
        """Get current session state (thread-safe)."""
        with self._state_lock:
            return self._state

    @state.setter
    def state(self, value: SessionState):
        """Set session state (thread-safe)."""
        with self._state_lock:
            old_state = self._state
            self._state = value
            if old_state != value:
                logger.info(f"Session state changed: {old_state.value} -> {value.value}")

    @property
    def is_running(self) -> bool:
        """Check if a session is currently running."""
        return self.state in (SessionState.STARTING, SessionState.RUNNING)

    def _validate_url(self, url: str) -> bool:
        """Validate URL format and allowed domains.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid and allowed
        """
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                logger.error(f"Invalid URL format: {url}")
                return False

            # Check if URL is from allowed domains
            allowed_domains = [
                "hoyolab.com",
                "hoyoverse.com",
                "mihoyo.com",
            ]

            if not any(domain in result.netloc for domain in allowed_domains):
                logger.warning(f"URL from non-standard domain: {url}")
                # Still allow, just warn

            return True
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    def _cleanup_browser(self):
        """Clean up browser resources safely."""
        try:
            if self._browser:
                logger.info("Closing browser...")
                self._browser.close()
                self._browser = None
                self._context = None
                self._page = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")

    def start_session(self, url: str) -> bool:
        """Start a manual login session.

        Args:
            url: URL to navigate to

        Returns:
            True if session started successfully
        """
        if self.is_running:
            logger.warning("Session already running, ignoring start request")
            return False

        if not self._validate_url(url):
            logger.error(f"Invalid URL, cannot start session: {url}")
            return False

        self._current_url = url
        self._stop_event.clear()
        self.state = SessionState.STARTING

        logger.info(f"Starting manual login session for URL: {url}")
        return True

    def stop_session(self) -> bool:
        """Stop the current manual login session.

        Returns:
            True if stop signal sent successfully
        """
        if not self.is_running:
            logger.warning("No active session to stop")
            return False

        logger.info("Stopping manual login session...")
        self.state = SessionState.CLOSING
        self._stop_event.set()
        return True

    def run(self, url: str):
        """Run the manual login browser session (blocking).

        This method is intended to be run in a background thread.

        Args:
            url: URL to navigate to
        """
        import sentry_sdk

        with sentry_sdk.start_transaction(op="manual.login", name="manual-login-session"):
            self._run_session(url)

    def _run_session(self, url: str):
        """Internal session runner wrapped by run() with Sentry transaction."""
        try:
            self.state = SessionState.RUNNING
            logger.info(f"Launching browser for URL: {url}")

            # Manual login always requires visible browser for user interaction
            headless = False
            logger.info("Launching browser in visible mode for manual login")

            with sync_playwright() as p:
                # Launch browser (using Firefox for better session handling)
                self._browser = p.firefox.launch(headless=headless)
                context_options = build_context_options(CONFIG["STORAGE_PATH"])
                self._context = self._browser.new_context(**context_options)
                self._page = self._context.new_page()

                logger.info(f"Navigating to: {url}")
                self._page.goto(url, wait_until="domcontentloaded", timeout=30000)

                NotificationHelper.notify(
                    title="ZZZ Bot",
                    message="Manual login session started",
                    app_icon=CONFIG["SAD_ICON"],
                )

                logger.info("Browser ready, waiting for user interaction...")

                # Track if browser was closed manually
                browser_closed_manually = False
                check_count = 0

                # Poll for browser closure (sync API doesn't have reliable events)
                while not self._stop_event.is_set():
                    try:
                        check_count += 1

                        # Log every 10 checks (every 5 seconds) to show it's working
                        if check_count % 10 == 0:
                            logger.info(f"Browser still active (check #{check_count})")

                        # Check if page is closed
                        if self._page.is_closed():
                            logger.info("✓ Detection method: page.is_closed() returned True")
                            browser_closed_manually = True
                            break

                        # Double-check by trying to access page properties
                        try:
                            title = self._page.title()
                            if check_count % 10 == 0:
                                logger.debug(f"Page title accessible: {title[:50]}...")
                        except Exception as e:
                            logger.info(
                                f"✓ Detection method: page.title() failed - {type(e).__name__}: {e}"
                            )
                            browser_closed_manually = True
                            break

                    except Exception as e:
                        logger.info(
                            f"✓ Detection method: Exception in check loop - {type(e).__name__}: {e}"
                        )
                        browser_closed_manually = True
                        break

                    # Wait briefly before next check
                    self._stop_event.wait(timeout=0.5)

                logger.info(f"Exited monitoring loop after {check_count} checks")

                # Always try to save session (even if browser was closed manually)
                # Playwright may still have the session data in memory
                if browser_closed_manually:
                    logger.info("Browser closed manually, attempting to save session...")
                else:
                    logger.info("Stop button clicked, saving session...")

                try:
                    # Manual login should refresh MongoDB auth state directly.
                    save_context_storage_state(
                        self._context,
                        CONFIG["STORAGE_PATH"],
                        write_local_backup=False,
                    )
                    if os.path.exists(CONFIG["STORAGE_PATH"]):
                        os.remove(CONFIG["STORAGE_PATH"])
                        logger.info(
                            "Removed stale local storage-state fallback: %s",
                            CONFIG["STORAGE_PATH"],
                        )
                    logger.info("✓ Session saved successfully to MongoDB storage state")

                    NotificationHelper.notify(
                        title="ZZZ Bot",
                        message="Login session saved successfully",
                        app_icon=CONFIG["ICON_PATH"],
                    )
                except Exception as e:
                    logger.error(f"✗ Failed to save session: {e}")
                    NotificationHelper.notify(
                        title="ZZZ Bot",
                        message=f"Session save failed: {type(e).__name__}",
                        app_icon=CONFIG["SAD_ICON"],
                    )

                self._cleanup_browser()
                self.state = SessionState.IDLE
                logger.info("Manual login session completed")

        except Exception as e:
            logger.error(f"Error in manual login session: {e}", exc_info=True)
            self.state = SessionState.ERROR

            NotificationHelper.notify(
                title="ZZZ Bot Error",
                message=f"Manual login error: {str(e)}",
                app_icon=CONFIG["SAD_ICON"],
            )

            self._cleanup_browser()
            self.state = SessionState.IDLE

        finally:
            self._stop_event.clear()
            self._current_url = None


# Global singleton instance
_manager = ManualLoginManager()


def get_manager() -> ManualLoginManager:
    """Get the global ManualLoginManager instance."""
    return _manager


def run(url: str):
    """Legacy run function for backward compatibility."""
    _manager.run(url)
