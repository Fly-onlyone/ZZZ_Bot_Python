"""Shared locator tracking helpers for automation modules."""

from __future__ import annotations

import ast
import re
from contextlib import suppress
from typing import Optional

from playwright.sync_api import Locator, Page

_LOCATOR_SELECTOR_RE = re.compile(
    r" selector=(?P<selector>'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\")>$"
)


def extract_selector(locator: Locator) -> str:
    """Extract the underlying selector from a Playwright locator when possible."""
    with suppress(AttributeError, TypeError):
        impl_obj = getattr(locator, "_impl_obj", None)
        selector = getattr(impl_obj, "_selector", None)
        if isinstance(selector, str) and selector:
            return selector

    with suppress(AttributeError, TypeError, ValueError, SyntaxError):
        text = repr(locator)
        match = _LOCATOR_SELECTOR_RE.search(text)
        if match:
            selector = ast.literal_eval(match.group("selector"))
            if isinstance(selector, str) and selector:
                return selector

    return "unknown"


def safe_track(
    page: Page,
    selector: str,
    handler: str,
    action: str,
    success: bool,
    *,
    error_message: Optional[str] = None,
    locator: Optional[Locator] = None,
) -> None:
    """Track a locator interaction without breaking the automation flow."""
    with suppress(Exception):
        from .LocatorTracker import track_locator

        track_locator(
            page,
            selector,
            handler,
            action,
            success,
            error_message=error_message,
            locator=locator,
        )


def safe_track_locator(
    locator: Locator,
    handler: str,
    action: str,
    success: bool,
    *,
    error_message: Optional[str] = None,
) -> None:
    """Track a locator interaction when only the locator object is available."""
    with suppress(Exception):
        safe_track(
            locator.page,
            extract_selector(locator),
            handler,
            action,
            success,
            error_message=error_message,
            locator=locator,
        )
