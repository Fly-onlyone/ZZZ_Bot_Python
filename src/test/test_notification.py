"""Test script for persistent Windows notifications.

Run this to verify that notifications appear in Windows notification center.
"""

import time

import NotificationHelper
from GlobalVar import CONFIG


def test_notifications():
    """Test notification persistence in Windows notification center."""
    print("Testing persistent Windows notifications...")
    print("=" * 60)

    # Test 1: Success notification
    print("\n1. Sending SUCCESS notification...")
    NotificationHelper.notify(
        title="ZZZ Bot - Test 1",
        message="This is a test notification. Check your Windows notification center!",
        app_icon=CONFIG.get("ICON_PATH", ""),
        duration="long",
    )
    print("   [OK] Success notification sent")
    time.sleep(2)

    # Test 2: Warning notification
    print("\n2. Sending WARNING notification...")
    NotificationHelper.notify(
        title="ZZZ Bot - Test 2",
        message="This notification should persist in your notification center",
        app_icon=CONFIG.get("SAD_ICON", ""),
        duration="long",
    )
    print("   [OK] Warning notification sent")
    time.sleep(2)

    # Test 3: Multiple notifications
    print("\n3. Sending multiple notifications...")
    for i in range(3):
        NotificationHelper.notify(
            title=f"ZZZ Bot - Batch {i+1}/3",
            message=f"Testing notification #{i+1}",
            app_icon=CONFIG.get("ICON_PATH", ""),
        )
        print(f"   [OK] Notification {i+1}/3 sent")
        time.sleep(1)

    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nPlease check your Windows notification center to verify:")
    print("  1. Notifications appeared as toast popups")
    print("  2. Notifications are saved in the Action Center")
    print("  3. You can click on them to see full details")
    print("\nTo open notification center:")
    print("  - Press Windows + N")
    print("  - Or click the notification icon in taskbar")
    print("=" * 60)


if __name__ == "__main__":
    test_notifications()
