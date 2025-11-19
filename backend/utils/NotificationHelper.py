"""Persistent notification helper for ZZZ Bot.

Provides cross-platform notifications with Windows notification center persistence.
On Windows 10/11, notifications are saved in the Action Center.
"""

import logging
import platform
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Detect platform
IS_WINDOWS = platform.system() == "Windows"

# Import appropriate notification library
if IS_WINDOWS:
    try:
        from winotify import Notification as WinNotification, audio

        WINOTIFY_AVAILABLE = True
        logger.info("Using winotify for persistent Windows notifications")
    except ImportError:
        WINOTIFY_AVAILABLE = False
        logger.warning("winotify not available, falling back to plyer (non-persistent)")
        from plyer import notification as plyer_notification
else:
    WINOTIFY_AVAILABLE = False
    from plyer import notification as plyer_notification

    logger.info("Using plyer for notifications (non-Windows platform)")


def notify(
    title: str,
    message: str,
    app_icon: Optional[str] = None,
    app_id: str = "ZZZ Bot",
    duration: str = "long",
    timeout: int = 10,
) -> None:
    """Send a notification that persists in Windows notification center.

    Args:
        title: Notification title
        message: Notification message/body
        app_icon: Path to icon file (.ico format for Windows)
        app_id: Application ID shown in notification center (Windows only)
        duration: "short" or "long" (Windows only)
        timeout: Display duration in seconds (for plyer fallback)
    """
    try:
        if IS_WINDOWS and WINOTIFY_AVAILABLE:
            _send_windows_notification(title, message, app_icon, app_id, duration)
        else:
            _send_plyer_notification(title, message, app_icon, timeout)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        # Fallback to console if all else fails
        print(f"\n[NOTIFICATION] {title}: {message}\n")


def _send_windows_notification(
    title: str,
    message: str,
    app_icon: Optional[str],
    app_id: str,
    duration: str,
) -> None:
    """Send persistent Windows notification using winotify.

    Args:
        title: Notification title
        message: Notification message
        app_icon: Path to icon file
        app_id: Application ID
        duration: "short" or "long"
    """
    # Prepare icon path
    icon_path_str = None
    if app_icon:
        icon_path = Path(app_icon)
        if icon_path.exists():
            # winotify requires absolute path
            icon_path_str = str(icon_path.resolve())
        else:
            logger.warning(f"Icon file not found: {app_icon}")

    # Create notification with icon in constructor
    toast = WinNotification(
        app_id=app_id,
        title=title,
        msg=message,
        duration=duration,
        icon=icon_path_str if icon_path_str else "",
    )

    # Add sound (default notification sound)
    try:
        toast.set_audio(audio.Default, loop=False)
    except Exception as e:
        logger.debug(f"Could not set audio: {e}")  # Sound is optional

    # Show notification
    toast.show()
    logger.info(f"Windows notification sent: {title}")


def _send_plyer_notification(
    title: str,
    message: str,
    app_icon: Optional[str],
    timeout: int,
) -> None:
    """Send notification using plyer (fallback, non-persistent).

    Args:
        title: Notification title
        message: Notification message
        app_icon: Path to icon file
        timeout: Display duration in seconds
    """
    plyer_notification.notify(
        title=title,
        message=message,
        app_icon=app_icon,
        timeout=timeout,
    )
    logger.info(f"Plyer notification sent: {title}")


# Create a module-level object with notify method for backwards compatibility
class NotificationModule:
    """Wrapper class to provide module-like interface."""

    @staticmethod
    def notify(title: str, message: str, app_icon: Optional[str] = None, **kwargs):
        """Send notification (backwards compatible with plyer)."""
        return notify(title, message, app_icon, **kwargs)


# For backwards compatibility with: from plyer import notification
notification = NotificationModule()
