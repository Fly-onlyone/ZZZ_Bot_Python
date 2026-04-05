from datetime import datetime
from pathlib import Path
import logging

from playwright.sync_api import BrowserContext

from core.GlobalVar import CONFIG, settings
from utils import NotificationHelper
from utils.DataHandler import save_redeem_data
from utils.storage_state_store import save_context_storage_state
from . import AutoLogin, RetryHelper

logger = logging.getLogger(__name__)

_MANUAL_CAPTCHA_NOTIFICATION = "Captcha detected. Please do manual login."
_MANUAL_LOGIN_NOTIFICATION = "Manual login required to continue redeem."
_CAPTCHA_CHALLENGE_TEXTS = (
    "Slide to complete the puzzle",
    "Slide to complete puzzle",
    "Complete verification",
    "Security verification",
    "Verify it's you",
)


def _mask_code(code: str) -> str:
    cleaned = code.strip()
    if len(cleaned) <= 8:
        return cleaned
    return f"{cleaned[:4]}...{cleaned[-4:]}"


def _capture_manual_captcha_required_event(item_name: str, masked_code: str) -> None:
    """Emit a dedicated Sentry warning for redeem attempts blocked by captcha."""
    import sentry_sdk

    with sentry_sdk.isolation_scope():
        sentry_sdk.set_tag("redeem.status", "manual_captcha_required")
        sentry_sdk.set_tag("redeem.manual_captcha_required", "true")
        sentry_sdk.set_context(
            "redeem",
            {
                "item_name": item_name,
                "masked_code": masked_code,
            },
        )
        sentry_sdk.capture_message(
            "Redeem requires manual captcha completion",
            level="warning",
        )


def _is_text_visible(locator) -> bool:
    try:
        return locator.is_visible()
    except Exception:
        return False


def _redeem_requires_manual_login(redeem_page) -> bool:
    try:
        account_frame = redeem_page.locator("#hyv-account-frame").content_frame
    except Exception:
        return False

    for text in _CAPTCHA_CHALLENGE_TEXTS:
        if _is_text_visible(account_frame.get_by_text(text)):
            return True

    return False


def _build_manual_captcha_required_result(item_name: str, masked_code: str) -> dict:
    logger.warning(
        "Redeem for '%s' requires manual captcha completion",
        item_name,
    )
    _capture_manual_captcha_required_event(item_name, masked_code)
    NotificationHelper.notify(
        title="ZZZ Bot",
        message=_MANUAL_CAPTCHA_NOTIFICATION,
        app_icon=CONFIG["SAD_ICON"],
    )
    return {
        "ok": False,
        "status": "manual_captcha_required",
        "detail": "Captcha blocked automatic redeem login.",
    }


def _build_manual_login_required_result(item_name: str) -> dict:
    logger.warning(
        "Redeem for '%s' still requires manual login after automatic login attempt",
        item_name,
    )
    NotificationHelper.notify(
        title="ZZZ Bot",
        message=_MANUAL_LOGIN_NOTIFICATION,
        app_icon=CONFIG["SAD_ICON"],
    )
    return {
        "ok": False,
        "status": "manual_login_required",
        "detail": "Redeem page still requires login after automatic login attempt.",
    }


def run(context: BrowserContext, code, item_name):
    import sentry_sdk

    with sentry_sdk.start_span(op="browser.navigate", name="RedeemAutofill"):
        current_day = datetime.now().strftime("%H:%M %d/%m/%Y")
        redeem_file_path = Path(CONFIG["REDEEM_FILE"])
        redeem_page = None
        redemption_record_id = None
        redeem_result = {
            "ok": False,
            "status": "redeem_not_started",
            "detail": "Redeem flow did not complete.",
        }
        masked_code = _mask_code(code)

        logger.info(
            "Starting redeem flow for '%s' with code %s",
            item_name,
            masked_code,
        )

        try:
            redemption_record_id = save_redeem_data(
                item_name,
                code,
                current_day,
                redeem_file_path,
                state=False,
                detail="Code saved before redeem attempt started.",
                status="redeem_pending",
            )
            logger.info(
                "Saved redemption code for '%s' before browser redeem attempt starts",
                item_name,
            )
        except Exception:
            logger.error(
                "Failed to pre-save redeem code for '%s'",
                item_name,
                exc_info=True,
            )

        try:
            redeem_page = context.new_page()
            redeem_page.goto("https://zenless.hoyoverse.com/redemption")
            redeem_page.wait_for_timeout(5000)
            logger.info("Opened redemption page for '%s'", item_name)

            if redeem_page.get_by_text("Please Log in to Redeem").is_visible():
                logger.info("Redeem page requires login for '%s'", item_name)
                login_screen = redeem_page.locator(
                    "#hyv-account-frame"
                ).content_frame.get_by_text("Account Log In")
                server_select_button = redeem_page.locator(
                    ".web-cdkey-form__select--toggle"
                )
                if RetryHelper.retry_until_screen_appears(
                    login_screen, server_select_button
                ):
                    logger.info("Attempting automatic redeem login for '%s'", item_name)
                    AutoLogin.run(redeem_page)
                    if _redeem_requires_manual_login(redeem_page):
                        redeem_result = _build_manual_captcha_required_result(
                            item_name, masked_code
                        )
                        return redeem_result

                    redeem_page.wait_for_timeout(5000)
                    select_server = redeem_page.get_by_text("Select a server")
                    if select_server.is_visible():
                        select_server.click()
                        redeem_page.get_by_text("Asia").click()
                        logger.info("Selected Asia server for '%s'", item_name)
                    elif any(
                        (
                            _is_text_visible(
                                redeem_page.get_by_text("Please Log in to Redeem")
                            ),
                            _is_text_visible(
                                redeem_page.locator("#hyv-account-frame")
                                .content_frame.get_by_text("Account Log In")
                            ),
                        )
                    ):
                        redeem_result = _build_manual_login_required_result(item_name)
                        return redeem_result
                else:
                    logger.warning(
                        "Redeem login UI did not stabilize for '%s'; continuing with current page state",
                        item_name,
                    )

            redeem_page.get_by_placeholder("Enter redemption code").fill(code)
            redeem_page.get_by_role("button", name="Redeem").click()
            logger.info(
                "Submitted redemption code for '%s' with code %s",
                item_name,
                masked_code,
            )
            redeem_page.wait_for_timeout(5000)

            if redeem_page.get_by_text(
                "Successfully redeemed. Please claim rewards from in-game mail."
            ).is_visible():
                redeem_result = {
                    "ok": True,
                    "status": "redeem_confirmed",
                    "detail": "Redeem confirmation popup detected.",
                }
                logger.info("Redeem confirmed for '%s'", item_name)
                NotificationHelper.notify(
                    title="ZZZ Bot",
                    message=f"Redeemed {item_name} successfully.",
                    app_icon=CONFIG["ICON_PATH"],
                )
            else:
                redeem_result = {
                    "ok": False,
                    "status": "redeem_not_confirmed",
                    "detail": "Redeem page did not show the success confirmation popup.",
                }
                logger.warning(
                    "Redeem for '%s' was not confirmed after submission",
                    item_name,
                )
                NotificationHelper.notify(
                    title="ZZZ Bot",
                    message=f"Redeem for {item_name} could not be confirmed. Code was saved for manual use.",
                    app_icon=CONFIG["SAD_ICON"],
                )
        except Exception as exc:
            redeem_result = {
                "ok": False,
                "status": "redeem_exception",
                "detail": f"{type(exc).__name__}: {exc}",
            }
            logger.exception(
                "Redeem flow crashed for '%s' with code %s",
                item_name,
                masked_code,
            )
            NotificationHelper.notify(
                title="ZZZ Bot",
                message=f"Redeem for {item_name} failed before confirmation. Code was saved for manual use.",
                app_icon=CONFIG["SAD_ICON"],
            )
        finally:
            try:
                save_context_storage_state(context, CONFIG["STORAGE_PATH"])
            except Exception:
                logger.warning(
                    "Failed to persist storage state after redeem attempt for '%s'",
                    item_name,
                    exc_info=True,
                )

            try:
                if redemption_record_id is None:
                    save_redeem_data(
                        item_name,
                        code,
                        current_day,
                        redeem_file_path,
                        state=redeem_result["ok"],
                        detail=redeem_result["detail"],
                        status=redeem_result["status"],
                    )
                else:
                    save_redeem_data(
                        item_name,
                        code,
                        current_day,
                        redeem_file_path,
                        state=redeem_result["ok"],
                        detail=redeem_result["detail"],
                        status=redeem_result["status"],
                        record_id=redemption_record_id,
                    )
            except Exception:
                logger.error(
                    "Failed to save redeem attempt for '%s'",
                    item_name,
                    exc_info=True,
                )

            if redeem_page is not None:
                try:
                    if not settings.hide_browser:
                        redeem_page.wait_for_timeout(2000)
                    redeem_page.close()
                except Exception:
                    logger.warning(
                        "Failed to close redeem page for '%s'",
                        item_name,
                        exc_info=True,
                    )

        return redeem_result
