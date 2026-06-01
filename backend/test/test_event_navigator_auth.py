"""Auth-gate semantics for EventNavigator.wait_for_authenticated_event_home.

Regression coverage for the false-positive "Please log in manually" bug: a logged-in
canvas/sprite event page often renders neither the scraped home text nor an ``<img>``
role within the poll window, so the gate must trust the session cookies and proceed
instead of blocking every scheduled run.
"""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

event_navigator = import_module("automation.EventNavigator")


class _FakeContext:
    def __init__(self, cookies):
        self._cookies = cookies

    def cookies(self):
        return self._cookies


class _FakePage:
    def __init__(self, cookies=None):
        self.context = _FakeContext(cookies or [])
        self.url = "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html"

    def wait_for_timeout(self, _ms):
        return None

    def wait_for_load_state(self, *_args, **_kwargs):
        return None


def _auth_cookies():
    return [
        {"name": "ltoken_v2", "domain": ".hoyolab.com"},
        {"name": "ltuid_v2", "domain": ".hoyolab.com"},
    ]


def _indicators(*, login_link=False, login_button=False, login_frame=False, home=False):
    return {
        "login_link_visible": login_link,
        "login_button_visible": login_button,
        "login_frame_visible": login_frame,
        "mission_hint_visible": home,
        "launcher_image_count": 2 if home else 0,
        "home_signal_visible": home,
    }


@pytest.fixture
def stub_capture(monkeypatch):
    """Replace the failure-screenshot capture so tests never touch the database."""
    captured = []
    monkeypatch.setattr(
        event_navigator,
        "_capture_event_page_auth_screenshot",
        lambda page: captured.append(getattr(page, "url", None)) or "screenshot:test",
    )
    return captured


def _patch_indicators(monkeypatch, indicators):
    monkeypatch.setattr(
        event_navigator, "_collect_event_page_auth_indicators", lambda page: indicators
    )


def _run(page, **kwargs):
    return event_navigator.wait_for_authenticated_event_home(
        page, context="test", timeout_ms=10, poll_interval_ms=1, **kwargs
    )


def test_proceeds_when_cookies_present_and_home_not_detected(monkeypatch, stub_capture):
    # The page is logged in but the sprite UI exposes neither home text nor an <img>.
    _patch_indicators(monkeypatch, _indicators())
    result = _run(_FakePage(cookies=_auth_cookies()))
    assert result.ready is True
    assert result.auth_required is False
    assert result.reason == "auth_cookies_present"
    assert stub_capture == []  # no failure screenshot on the proceed path


def test_blocks_when_login_form_visible_even_with_cookies(monkeypatch, stub_capture):
    _patch_indicators(monkeypatch, _indicators(login_frame=True))
    result = _run(_FakePage(cookies=_auth_cookies()))
    assert result.ready is False
    assert result.auth_required is True
    assert result.reason == "login_prompt_visible"
    assert stub_capture  # screenshot captured on the blocking path


def test_blocks_when_no_cookies_and_home_not_detected(monkeypatch, stub_capture):
    _patch_indicators(monkeypatch, _indicators())
    result = _run(_FakePage(cookies=[]))
    assert result.ready is False
    assert result.auth_required is True
    assert stub_capture


def test_ready_when_home_detected(monkeypatch, stub_capture):
    _patch_indicators(monkeypatch, _indicators(home=True))
    result = _run(_FakePage(cookies=[]))
    assert result.ready is True
    assert result.auth_required is False
    assert result.reason == "event_home_ready"


def test_has_hoyolab_auth_cookies_requires_a_full_pair():
    assert event_navigator._has_hoyolab_auth_cookies(_FakePage(cookies=_auth_cookies())) is True

    only_one = _FakePage(cookies=[{"name": "ltoken_v2", "domain": ".hoyolab.com"}])
    assert event_navigator._has_hoyolab_auth_cookies(only_one) is False

    wrong_domain = _FakePage(
        cookies=[
            {"name": "ltoken_v2", "domain": ".example.com"},
            {"name": "ltuid_v2", "domain": ".example.com"},
        ]
    )
    assert event_navigator._has_hoyolab_auth_cookies(wrong_domain) is False
