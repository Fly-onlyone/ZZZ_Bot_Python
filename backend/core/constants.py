"""Application-wide constants for ZZZ Bot.

Centralizes magic numbers and configuration values for better maintainability.
"""

# ============================================================================
# IMAGE COMPARISON CONSTANTS
# ============================================================================

# Percentage threshold for image matching (0-100)
IMAGE_MATCH_THRESHOLD = 5.0

# Threshold for binary image difference detection
IMAGE_BINARY_THRESHOLD = 30

# Connection pool configuration for image fetching
HTTP_POOL_CONNECTIONS = 10
HTTP_POOL_MAX_SIZE = 20
HTTP_MAX_RETRIES = 3


# ============================================================================
# TIMEOUT CONSTANTS (milliseconds)
# ============================================================================

# Dialog and popup timeouts
DIALOG_WAIT_TIMEOUT = 5000
MISSION_CLICK_WAIT = 2000
RETRY_WAIT = 1000
SHORT_WAIT = 500
NETWORK_IDLE_TIMEOUT = 10000

# Element visibility timeouts
ELEMENT_VISIBILITY_TIMEOUT = 1000
ELEMENT_VISIBILITY_TIMEOUT_LONG = 2000
ELEMENT_VISIBILITY_TIMEOUT_EXTENDED = 5000

# HTTP request timeout (seconds)
HTTP_REQUEST_TIMEOUT = 10


# ============================================================================
# DATA RETENTION CONSTANTS
# ============================================================================

# Maximum number of days to keep mission data
MISSION_DATA_RETENTION_DAYS = 5

# Maximum number of days to keep redemption codes
REDEEM_CODE_RETENTION_DAYS = 30


# ============================================================================
# HUNT MODE CONSTANTS
# ============================================================================

# Buffer time (seconds) to schedule hunt before item availability
# Default: 2 minutes (120 seconds)
HUNT_WAIT_BUFFER_SECONDS = 120


# ============================================================================
# RETRY CONSTANTS
# ============================================================================

# Maximum number of retry attempts for mission clicks
MAX_MISSION_RETRY_ATTEMPTS = 5

# Maximum attempts to close shopping screen
MAX_SHOPPING_CLOSE_ATTEMPTS = 3


# ============================================================================
# URL CONSTANTS
# ============================================================================

# Check-in URLs
CHECK_IN_URL = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
CHECK_IN_URL_WITH_AUTH = (
    "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
    "?act_id=e202406031448091&hyl_auth_required=true"
)

# Default event URL (for browser automation entry point)
DEFAULT_EVENT_URL = (
    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
)


# ============================================================================
# SELECTOR CONSTANTS
# ============================================================================

# Mission selectors
DIALOG_CLOSE_SELECTOR = ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
DIALOG_BODY_SELECTOR = "div.components-pc-assets-__dialog_---dialog-body---1SieDs"
MISSION_WRAPPER_SELECTOR = ".wrapper-O3T67n"
AVATAR_SELECTOR = "div.avatarsItemImg-AiUG1h"
TASK_ITEM_SELECTOR = ".taskItemPcLeft-Aetp6m"

# Shopping selectors
SHOPPING_SCREEN_SELECTOR = ".wrapper-O3T67n"
CURRENT_POINT_SELECTOR = ".bubbleCnt-hsQFy-"
ITEM_SELECTOR = ".item-6Owrjq"
ITEM_NAME_SELECTOR = ".itemName-NypcHW"
ITEM_PRICE_SELECTOR = ".itemPriceNum-cd1EE-"
ITEM_BUTTON_SELECTOR = ".itemBtn-gTL1Rd"
ITEM_COUNT_SELECTOR = ".itemCnt-7wIR4D"
DURATION_SELECTOR = ".bubbleExpire-L4jUSs"
CONFIRM_DIALOG_SELECTOR = ".confirm-5fGU8Q"
CONFIRM_OK_SELECTOR = ".confirmOk-vBKGy6"
REDEEM_CODE_SELECTOR = "div.gainCodeCopyInput-QcgdvD"
COPY_BUTTON_SELECTOR = "div.gainCodeCopyBtn-Lwk9eR"
CLOSE_BUTTON_SELECTOR = ".gainClose-7Q0hz8"

# Common selectors
PANEL_BACK_SELECTOR = ".panelBack--wW5qj"


# ============================================================================
# TEXT MATCH CONSTANTS
# ============================================================================

MISSION_BUTTON_TEXT = "Carry out missions to earn"
CLAIMED_POPUP_TEXT = "Claimed!"
EXCHANGE_BUTTON_TEXT = "Exchange"


# ============================================================================
# STATUS MESSAGE CONSTANTS
# ============================================================================

# Mission status messages
STATUS_SUCCESS = "Login Success"
STATUS_FAILED = "Login Failed"
STATUS_LINK_NOT_OPENED = "Link isn't opened"

# Button states
BUTTON_STATE_FINISHED = "Finished"
BUTTON_STATE_UNFINISHED = "Unfinished"
BUTTON_STATE_REWARD = "Reward"
BUTTON_STATE_UNKNOWN = "unknown"

# Item availability states
ITEM_AVAILABLE = "Exchange"
ITEM_LIMIT_REACHED = "Limit Reached"


# ============================================================================
# LOGGING CONSTANTS
# ============================================================================

# Log rotation settings
LOG_ROTATION_WHEN = "D"  # Daily rotation
LOG_ROTATION_INTERVAL = 1  # 1-day interval
LOG_BACKUP_COUNT = 7  # Keep 7 days of logs


# ============================================================================
# SCREENSHOT CONSTANTS
# ============================================================================

SCREENSHOT_LOGIN_REWARD = "login_reward.png"
SCREENSHOT_SHOPPING_WONT_CLOSE_PREFIX = "shopping_wont_close_"
