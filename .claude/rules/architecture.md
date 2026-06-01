# Architecture Patterns

## Project Structure

ZZZ Bot follows a hybrid desktop application architecture with clear separation between backend automation and frontend UI.

### Browser Automation Pipeline

```
Bot.py (scheduler) → playwright_task()
  ├─→ MissionHandler.run()        # Daily missions
  ├─→ ShoppingHandler.run()       # Shopping automation
  ├─→ DrawHandler.run()           # Prize draws
  └─→ HuntModeHandler.run_hunt()  # Hunt mode (timed item purchases)
       ↓
  Save session state → Send email notification
```

### Image Recognition System

Uses OpenCV to detect UI states by comparing screenshots with reference images in `sample/` and `reward image/`:

- Game avatar identification (ZZZ vs other games)
- Button state detection (Finished/Unfinished/Reward)
- Reward recognition from prize draws
- Threshold: <5% difference for matches

Key module: `ImageProcessor.py` with `RetryHelper.py` for element polling.

## Key Design Decisions

- **Image Recognition vs. Selectors:** Web UI selectors break frequently due to dynamic content and updates. Use OpenCV template matching with reference images (`cv2.matchTemplate`, <5% difference threshold).
- **Session Management:** Persistent Playwright storage state, saved to SQLite (`storage_state:hoyo.json`) with a local-file fallback. First-time setup via manual login UI. Avoids repeated authentication.
- **Auth-gate (login validation):** Before automation, `EventNavigator.wait_for_authenticated_event_home()` decides if the event page is usable. The Mimo page is a canvas/sprite UI whose home content is unreliable to scrape, so the gate trusts the **session cookie pair** (`ltoken_v2`/`ltuid_v2` or `cookie_token_v2`/`account_id_v2`) as the authoritative "logged in" signal. It blocks + notifies ("Please log in manually") **only** when a login form is positively visible, or when no cookies are present; on an ambiguous render it proceeds and lets the image-recognition handlers run. This avoids false-positive manual-login spam on every scheduled run.
- **Hunt Mode Three-Phase Execution:** See Pattern 5 in code-guide.md. Reduces session time, ensures cleanup even on partial failure.

## Module Dependencies

```
Bot.py (core/)
  ├─→ GlobalVar (core/, config, FastAPI app)
  ├─→ ManualLogin (core/)
  ├─→ Notification (core/, Jinja2 templates in backend/message/)
  ├─→ MissionHandler (handlers/)
  │    ├─→ ImageProcessor (automation/)
  │    ├─→ RetryHelper (automation/)
  │    └─→ DataHandler (utils/)
  ├─→ ShoppingHandler (handlers/)
  │    ├─→ RedeemAutofill (automation/)
  │    │    └─→ AutoLogin (automation/)
  │    ├─→ ImageProcessor (automation/)
  │    └─→ DataHandler (utils/)
  ├─→ DrawHandler (handlers/)
  │    ├─→ RedeemAutofill (automation/)
  │    ├─→ ImageProcessor (automation/)
  │    └─→ DataHandler (utils/)
  └─→ HuntModeHandler (handlers/)
       ├─→ ShoppingHandler (handlers/)
       ├─→ RedeemAutofill (automation/)
       ├─→ ImageProcessor (automation/)
       ├─→ RetryHelper (automation/)
       ├─→ DataHandler (utils/)
       ├─→ NotificationHelper (utils/)
       └─→ StringUtil (utils/)
```
