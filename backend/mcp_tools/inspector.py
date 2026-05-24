"""MCP server for DOM inspection with authenticated browser context.

Provides 14 powerful tools for Claude Code to inspect and interact with
live DOM elements using the bot's authenticated Playwright browser session.

Key Features:
- Persistent browser session (no spawn per call)
- Multiple selector types (CSS, XPath, text, role)
- Full HTML output without arbitrary truncation
- Selector stability analysis
- DOM traversal capabilities
- Image comparison and download

Tools:
    Session Management:
        1. open_page - Open page, maintain session
        2. close_session - Close browser, release resources

    Element Inspection:
        3. find_elements - Find elements with pagination
        4. inspect_element - Deep inspection with full HTML
        5. get_element_tree - ARIA or HTML tree view
        6. traverse_dom - Navigate parent/children/siblings

    Selector Validation:
        7. validate_selector - Test uniqueness, stability hints
        8. compare_selectors - Compare multiple selectors for same target

    Page Interaction:
        9. execute_action - Click/hover/highlight for testing
        10. wait_for_condition - Wait for visible/hidden/enabled

    Capture:
        11. take_screenshot - Screenshot page or element
        12. inspect_iframe - Inspect iframe content

    Image Analysis:
        13. compare_image - Compare element image against reference(s)
        14. download_image - Download and save element image to disk

Usage:
    Standalone: python backend/mcp_tools/inspector.py
    MCP Inspector: npx @modelcontextprotocol/inspector python backend/mcp_tools/inspector.py
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import cv2

# Add backend folder to path for imports when run standalone
BACKEND_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(PROJECT_ROOT)

from core.GlobalVar import CONFIG, is_exe

logger = logging.getLogger(__name__)
INSPECTOR_DISABLED_MESSAGE = "ZZZ Bot Inspector is disabled in packaged builds."


class _DisabledMCP:
    """No-op MCP placeholder used to keep packaged builds import-safe."""

    def tool(self, func):
        logger.debug(
            "Skipping MCP tool registration for %s in packaged mode",
            self.__class__.__name__,
        )
        return func

    def run(self, transport: str = "stdio") -> None:
        logger.info("%s (transport=%s)", INSPECTOR_DISABLED_MESSAGE, transport)
        print(INSPECTOR_DISABLED_MESSAGE)


if is_exe:
    BrowserSession = None
    SelectorType = None
    analyze_selector_stability = None
    create_locator = None
    suggest_alternative_selectors = None
    fetch_image_from_locator_async = None
    compare_images_sync = None
    scan_folder_for_best_match = None
    mcp = _DisabledMCP()
else:
    from fastmcp import FastMCP

    from mcp_tools.image_helpers import (
        compare_images_sync,
        fetch_image_from_locator_async,
        scan_folder_for_best_match,
    )
    from mcp_tools.locator_factory import (
        SelectorType,
        analyze_selector_stability,
        create_locator,
        suggest_alternative_selectors,
    )
    from mcp_tools.session_manager import BrowserSession

    mcp = FastMCP("ZZZ Bot Inspector")

# Default event page URL
DEFAULT_URL = (
    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html"
    "?game=zzz&act_id=e202406271631371"
)


@mcp.tool
async def open_page(
    url: str = None,
    wait_strategy: str = "networkidle",
    wait_timeout_ms: int = 30000,
    headless: bool = False,
    spa_render_wait_ms: int = 3000,
) -> dict:
    """Open a page with authenticated browser session.

    Maintains a persistent browser session across tool calls.
    If session already exists, navigates to new URL without respawning.

    Args:
        url: URL to navigate to (defaults to ZZZ event page).
        wait_strategy: How to wait after navigation.
            'networkidle' - Wait until no network requests for 500ms (default)
            'load' - Wait for load event
            'domcontentloaded' - Wait for DOMContentLoaded
            'commit' - Wait for response received
            'none' - Don't wait after goto
        wait_timeout_ms: Timeout for wait operations in milliseconds.
        headless: Whether to run browser in headless mode (default: False for debugging).
        spa_render_wait_ms: Additional wait time for SPA content to render.

    Returns:
        dict with session status, page title, and URL.
    """
    target_url = url or DEFAULT_URL

    try:
        session = await BrowserSession.get_instance(CONFIG["STORAGE_PATH"])
        page = await session.ensure_page(
            url=target_url,
            wait_strategy=wait_strategy,
            wait_timeout_ms=wait_timeout_ms,
            headless=headless,
        )

        # Wait for SPA content to render
        if spa_render_wait_ms > 0:
            await session.wait_for_spa_render(spa_render_wait_ms)

        title = await page.title()

        return {
            "status": "success",
            "session_active": True,
            "title": title,
            "url": target_url,
            "headless": headless,
        }

    except Exception as e:
        logger.error(f"Failed to open page: {e}")
        return {
            "status": "error",
            "error": str(e),
            "session_active": False,
        }


@mcp.tool
async def close_session() -> dict:
    """Close the browser session and release resources.

    Call this when done inspecting to free memory and close the browser.

    Returns:
        dict with status and message.
    """
    session = await BrowserSession.get_instance()
    return await session.close()


# =============================================================================
# Element Inspection Tools
# =============================================================================


@mcp.tool
async def find_elements(
    selector: str,
    selector_type: str = "css",
    limit: int = 20,
    offset: int = 0,
    include_html: bool = False,
    max_html_length: int = 500,
) -> dict:
    """Find elements matching selector with pagination.

    Args:
        selector: Selector string (format depends on selector_type).
        selector_type: Type of selector - 'css', 'xpath', 'text', 'text_exact', 'role'.
        limit: Maximum elements to return (default: 20).
        offset: Skip first N elements (for pagination).
        include_html: Include innerHTML in results (default: False for performance).
        max_html_length: Truncate HTML to this length (0 = no limit).

    Returns:
        dict with total count and element list with visibility, bounding box, attributes.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))
        total_count = await locator.count()

        elements = []
        end_idx = min(offset + limit, total_count)

        for i in range(offset, end_idx):
            elem = locator.nth(i)
            try:
                elem_info = {
                    "index": i,
                    "visible": await elem.is_visible(),
                    "enabled": await elem.is_enabled(),
                    "tag_name": await elem.evaluate("el => el.tagName.toLowerCase()"),
                    "bounding_box": await elem.bounding_box(),
                }

                # Get common attributes
                for attr in ["id", "class", "data-testid", "aria-label", "role"]:
                    val = await elem.get_attribute(attr)
                    if val:
                        elem_info[attr] = val

                # Optionally include HTML
                if include_html:
                    html = await elem.inner_html()
                    if max_html_length > 0 and len(html) > max_html_length:
                        html = html[:max_html_length] + "..."
                    elem_info["inner_html"] = html

                elements.append(elem_info)

            except Exception as e:
                elements.append({"index": i, "error": str(e)})

        return {
            "selector": selector,
            "selector_type": selector_type,
            "total_count": total_count,
            "returned": len(elements),
            "offset": offset,
            "elements": elements,
        }

    except Exception as e:
        return {"error": str(e), "selector": selector}


@mcp.tool
async def inspect_element(
    selector: str,
    index: int = 0,
    selector_type: str = "css",
    include_children: bool = True,
    max_depth: int = 3,
    max_html_length: int = 0,
) -> dict:
    """Deep inspection of a specific element.

    Args:
        selector: Selector string.
        index: Which element to inspect if multiple match (default: 0).
        selector_type: Type of selector - 'css', 'xpath', 'text', 'text_exact', 'role'.
        include_children: Include child element info (default: True).
        max_depth: How deep to traverse children (default: 3).
        max_html_length: Truncate HTML to this length (0 = no limit, default).

    Returns:
        dict with complete element information including full HTML, attributes,
        computed styles, and optionally child elements.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))
        count = await locator.count()

        if count == 0:
            return {"error": f"No elements found for selector: {selector}"}

        if index >= count:
            return {"error": f"Index {index} out of range (found {count} elements)"}

        elem = locator.nth(index)

        # Get comprehensive element info via JavaScript
        elem_info = await elem.evaluate(
            """el => {
            const getElementInfo = (element, depth, maxDepth) => {
                const info = {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || null,
                    className: element.className || null,
                    textContent: element.textContent?.trim().substring(0, 200) || null,
                    attributes: {},
                    children: []
                };

                // Get all attributes
                for (const attr of element.attributes) {
                    info.attributes[attr.name] = attr.value;
                }

                // Get children if within depth limit
                if (depth < maxDepth) {
                    for (const child of element.children) {
                        info.children.push(getElementInfo(child, depth + 1, maxDepth));
                    }
                }

                return info;
            };

            return getElementInfo(el, 0, arguments[0]);
        }""",
            max_depth if include_children else 0,
        )

        # Get additional info from Playwright
        outer_html = await elem.evaluate("el => el.outerHTML")
        if max_html_length > 0 and len(outer_html) > max_html_length:
            outer_html = outer_html[:max_html_length] + "..."

        bounding_box = await elem.bounding_box()

        # Get computed styles for key properties
        computed_styles = await elem.evaluate(
            """el => {
            const style = window.getComputedStyle(el);
            return {
                display: style.display,
                visibility: style.visibility,
                opacity: style.opacity,
                position: style.position,
                zIndex: style.zIndex,
                backgroundColor: style.backgroundColor,
                color: style.color
            };
        }"""
        )

        return {
            "selector": selector,
            "index": index,
            "total_matches": count,
            "visible": await elem.is_visible(),
            "enabled": await elem.is_enabled(),
            "bounding_box": bounding_box,
            "outer_html": outer_html,
            "element_tree": elem_info,
            "computed_styles": computed_styles,
        }

    except Exception as e:
        return {"error": str(e), "selector": selector}


@mcp.tool
async def get_element_tree(
    selector: str = "body",
    selector_type: str = "css",
    format: str = "aria",
) -> dict:
    """Get element tree in ARIA snapshot or HTML outline format.

    Args:
        selector: Root element selector (default: body).
        selector_type: Type of selector.
        format: Output format - 'aria' for accessibility tree, 'html' for HTML outline.

    Returns:
        dict with tree representation.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))

        if format == "aria":
            snapshot = await locator.aria_snapshot()
            return {
                "selector": selector,
                "format": "aria",
                "tree": snapshot,
            }
        else:
            # HTML outline format
            outline = await locator.evaluate(
                """el => {
                const buildOutline = (element, indent = 0) => {
                    const tag = element.tagName.toLowerCase();
                    const id = element.id ? `#${element.id}` : '';
                    const classes = element.className ?
                        `.${element.className.split(' ').join('.')}` : '';
                    const text = element.childNodes.length === 1 &&
                        element.childNodes[0].nodeType === 3 ?
                        ` "${element.textContent.trim().substring(0, 30)}"` : '';

                    let line = '  '.repeat(indent) + `<${tag}${id}${classes}>${text}`;
                    let lines = [line];

                    for (const child of element.children) {
                        lines = lines.concat(buildOutline(child, indent + 1));
                    }

                    return lines;
                };

                return buildOutline(el).join('\\n');
            }"""
            )
            return {
                "selector": selector,
                "format": "html",
                "tree": outline,
            }

    except Exception as e:
        return {"error": str(e), "selector": selector}


@mcp.tool
async def traverse_dom(
    selector: str,
    index: int = 0,
    selector_type: str = "css",
    direction: str = "children",
    levels: int = 1,
) -> dict:
    """Navigate DOM from an element (parent, children, siblings).

    Args:
        selector: Starting element selector.
        index: Which element to start from if multiple match.
        selector_type: Type of selector.
        direction: Direction to traverse - 'parent', 'children', 'siblings',
                  'next_sibling', 'prev_sibling'.
        levels: How many levels to traverse (default: 1).

    Returns:
        dict with traversal results including element info.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))
        elem = locator.nth(index)

        if await elem.count() == 0:
            return {"error": f"Element not found: {selector}"}

        # JavaScript to traverse DOM
        traversal_script = """(el, direction, levels) => {
            const getInfo = (element) => {
                if (!element) return null;
                return {
                    tagName: element.tagName?.toLowerCase(),
                    id: element.id || null,
                    className: element.className || null,
                    textContent: element.textContent?.trim().substring(0, 100) || null,
                    childCount: element.children?.length || 0
                };
            };

            let results = [];
            let current = el;

            for (let i = 0; i < levels; i++) {
                if (direction === 'parent') {
                    current = current.parentElement;
                    if (current) results.push(getInfo(current));
                } else if (direction === 'children') {
                    if (i === 0) {
                        results = Array.from(current.children).map(getInfo);
                    }
                    break;
                } else if (direction === 'siblings') {
                    if (i === 0) {
                        const parent = current.parentElement;
                        if (parent) {
                            results = Array.from(parent.children)
                                .filter(c => c !== current)
                                .map(getInfo);
                        }
                    }
                    break;
                } else if (direction === 'next_sibling') {
                    current = current.nextElementSibling;
                    if (current) results.push(getInfo(current));
                } else if (direction === 'prev_sibling') {
                    current = current.previousElementSibling;
                    if (current) results.push(getInfo(current));
                }

                if (!current) break;
            }

            return results;
        }"""

        results = await elem.evaluate(traversal_script, direction, levels)

        return {
            "selector": selector,
            "direction": direction,
            "levels": levels,
            "results": results,
        }

    except Exception as e:
        return {"error": str(e), "selector": selector}


# =============================================================================
# Selector Validation Tools
# =============================================================================


@mcp.tool
async def validate_selector(
    selector: str,
    selector_type: str = "css",
    expected_count: int = None,
) -> dict:
    """Validate selector and analyze stability.

    Checks if selector finds elements and analyzes patterns that may
    indicate fragile selectors (hashed classes, deep nesting, etc.).

    Args:
        selector: Selector to validate.
        selector_type: Type of selector.
        expected_count: Expected number of matches (None = any count is ok).

    Returns:
        dict with match count, stability analysis, and suggestions.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))
        count = await locator.count()

        # Analyze selector stability (CSS only)
        stability = {}
        if selector_type == "css":
            stability = analyze_selector_stability(selector)

        # Check expected count
        count_ok = True
        if expected_count is not None:
            count_ok = count == expected_count

        # Get alternative suggestions if element found
        alternatives = []
        if count > 0:
            elem = locator.first
            elem_info = await elem.evaluate(
                """el => {
                return {
                    tag_name: el.tagName.toLowerCase(),
                    id: el.id || null,
                    class_list: Array.from(el.classList),
                    text_content: el.textContent?.trim().substring(0, 50) || null,
                    data_attrs: Object.fromEntries(
                        Array.from(el.attributes)
                            .filter(a => a.name.startsWith('data-'))
                            .map(a => [a.name, a.value])
                    ),
                    aria_label: el.getAttribute('aria-label'),
                    role: el.getAttribute('role')
                };
            }"""
            )
            alternatives = suggest_alternative_selectors(elem_info)

        return {
            "selector": selector,
            "selector_type": selector_type,
            "count": count,
            "expected_count": expected_count,
            "count_matches_expected": count_ok,
            "is_unique": count == 1,
            "stability_analysis": stability,
            "alternative_selectors": alternatives[:5],  # Top 5 suggestions
        }

    except Exception as e:
        return {"error": str(e), "selector": selector}


@mcp.tool
async def compare_selectors(
    selectors: list[dict],
) -> dict:
    """Compare multiple selectors to find which ones target the same element.

    Useful for finding the most stable selector among alternatives.

    Args:
        selectors: List of selector dicts, each with 'selector' and optionally
                  'selector_type' (defaults to 'css').
                  Example: [{"selector": ".class1"}, {"selector": "//div", "selector_type": "xpath"}]

    Returns:
        dict with comparison results for each selector.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    results = []

    for sel_config in selectors:
        selector = sel_config.get("selector")
        selector_type = sel_config.get("selector_type", "css")

        try:
            locator = create_locator(page, selector, SelectorType(selector_type))
            count = await locator.count()

            result = {
                "selector": selector,
                "selector_type": selector_type,
                "count": count,
                "visible_count": 0,
                "first_element": None,
            }

            if count > 0:
                # Count visible elements
                visible = 0
                for i in range(min(count, 10)):
                    if await locator.nth(i).is_visible():
                        visible += 1
                result["visible_count"] = visible

                # Get first element identifier for comparison
                first = locator.first
                result["first_element"] = await first.evaluate(
                    """el => {
                    return {
                        tagName: el.tagName.toLowerCase(),
                        id: el.id || null,
                        className: el.className || null,
                        rect: el.getBoundingClientRect().toJSON()
                    };
                }"""
                )

                # Stability analysis for CSS
                if selector_type == "css":
                    result["stability"] = analyze_selector_stability(selector)

            results.append(result)

        except Exception as e:
            results.append({"selector": selector, "error": str(e)})

    # Identify which selectors target the same element
    groups = {}
    for r in results:
        if r.get("first_element"):
            # Use position as identifier
            rect = r["first_element"].get("rect", {})
            key = f"{rect.get('x', 0):.0f},{rect.get('y', 0):.0f}"
            if key not in groups:
                groups[key] = []
            groups[key].append(r["selector"])

    return {
        "results": results,
        "same_element_groups": list(groups.values()),
        "total_selectors": len(selectors),
    }


# =============================================================================
# Page Interaction Tools
# =============================================================================


@mcp.tool
async def execute_action(
    selector: str,
    index: int = 0,
    selector_type: str = "css",
    action: str = "click",
    action_params: dict = None,
) -> dict:
    """Execute an action on an element (click, hover, highlight, etc.).

    Args:
        selector: Element selector.
        index: Which element if multiple match.
        selector_type: Type of selector.
        action: Action to perform:
            'click' - Click the element
            'hover' - Hover over element
            'highlight' - Add visual highlight (for debugging)
            'focus' - Focus the element
            'scroll_into_view' - Scroll element into view
            'fill' - Fill input with text (requires action_params.text)
            'select' - Select dropdown option (requires action_params.value)
        action_params: Additional parameters for action (e.g., {text: "value"}).

    Returns:
        dict with action result.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page
    params = action_params or {}

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))
        elem = locator.nth(index)

        if await elem.count() == 0:
            return {"error": f"Element not found: {selector}"}

        if action == "click":
            force = params.get("force", False)
            await elem.click(force=force)
            return {"action": "click", "success": True}

        elif action == "hover":
            await elem.hover()
            return {"action": "hover", "success": True}

        elif action == "highlight":
            # Add a visual highlight border
            await elem.evaluate(
                """el => {
                el.style.outline = '3px solid red';
                el.style.outlineOffset = '2px';
            }"""
            )
            return {"action": "highlight", "success": True, "note": "Red outline added"}

        elif action == "focus":
            await elem.focus()
            return {"action": "focus", "success": True}

        elif action == "scroll_into_view":
            await elem.scroll_into_view_if_needed()
            return {"action": "scroll_into_view", "success": True}

        elif action == "fill":
            text = params.get("text", "")
            await elem.fill(text)
            return {"action": "fill", "success": True, "text": text}

        elif action == "select":
            value = params.get("value", "")
            await elem.select_option(value)
            return {"action": "select", "success": True, "value": value}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        return {"error": str(e), "action": action}


@mcp.tool
async def wait_for_condition(
    selector: str,
    selector_type: str = "css",
    condition: str = "visible",
    timeout_ms: int = 30000,
) -> dict:
    """Wait for an element to meet a condition.

    Args:
        selector: Element selector.
        selector_type: Type of selector.
        condition: Condition to wait for:
            'visible' - Element is visible
            'hidden' - Element is hidden or detached
            'attached' - Element is in DOM
            'detached' - Element is removed from DOM
            'enabled' - Element is enabled (for inputs)
            'disabled' - Element is disabled
        timeout_ms: Maximum wait time in milliseconds.

    Returns:
        dict with wait result.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        locator = create_locator(page, selector, SelectorType(selector_type))

        if condition == "visible":
            await locator.first.wait_for(state="visible", timeout=timeout_ms)
        elif condition == "hidden":
            await locator.first.wait_for(state="hidden", timeout=timeout_ms)
        elif condition == "attached":
            await locator.first.wait_for(state="attached", timeout=timeout_ms)
        elif condition == "detached":
            await locator.first.wait_for(state="detached", timeout=timeout_ms)
        elif condition == "enabled":
            await locator.first.wait_for(state="visible", timeout=timeout_ms)
            # Check enabled state
            is_enabled = await locator.first.is_enabled()
            if not is_enabled:
                return {
                    "success": False,
                    "condition": condition,
                    "message": "Element visible but not enabled",
                }
        elif condition == "disabled":
            await locator.first.wait_for(state="visible", timeout=timeout_ms)
            is_disabled = not await locator.first.is_enabled()
            if not is_disabled:
                return {
                    "success": False,
                    "condition": condition,
                    "message": "Element visible but not disabled",
                }
        else:
            return {"error": f"Unknown condition: {condition}"}

        return {
            "success": True,
            "condition": condition,
            "selector": selector,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "condition": condition,
            "timeout_ms": timeout_ms,
        }


# =============================================================================
# Capture Tools
# =============================================================================


@mcp.tool
async def take_screenshot(
    filename: str = "debug.png",
    selector: Optional[str] = None,
    selector_type: str = "css",
    full_page: bool = False,
) -> dict:
    """Take screenshot of page or specific element.

    Args:
        filename: Output filename (saved to screenshot/ folder).
        selector: Optional element selector to screenshot (just that element).
        selector_type: Type of selector.
        full_page: Capture full scrollable page (default: False).

    Returns:
        dict with screenshot path.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page
    path = os.path.join(CONFIG["SCREENSHOT_FOLDER"], filename)

    try:
        if selector:
            locator = create_locator(page, selector, SelectorType(selector_type))
            await locator.first.screenshot(path=path)
        else:
            await page.screenshot(path=path, full_page=full_page)

        return {
            "success": True,
            "path": path,
            "selector": selector,
            "full_page": full_page,
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool
async def inspect_iframe(
    iframe_selector: str,
    inner_selector: str,
    iframe_selector_type: str = "css",
    inner_selector_type: str = "css",
) -> dict:
    """Inspect elements inside an iframe.

    Args:
        iframe_selector: Selector for the iframe element.
        inner_selector: Selector for element inside the iframe.
        iframe_selector_type: Type of iframe selector.
        inner_selector_type: Type of inner selector.

    Returns:
        dict with iframe content and inner element info.
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        # Get iframe
        iframe_locator = create_locator(page, iframe_selector, SelectorType(iframe_selector_type))
        iframe_elem = iframe_locator.first

        if await iframe_elem.count() == 0:
            return {"error": f"Iframe not found: {iframe_selector}"}

        # Get frame content
        frame = await iframe_elem.content_frame()
        if not frame:
            return {"error": "Could not access iframe content"}

        # Find element inside iframe
        inner_locator = create_locator(frame, inner_selector, SelectorType(inner_selector_type))
        count = await inner_locator.count()

        elements = []
        for i in range(min(count, 10)):
            elem = inner_locator.nth(i)
            try:
                elements.append(
                    {
                        "index": i,
                        "visible": await elem.is_visible(),
                        "tag_name": await elem.evaluate("el => el.tagName.toLowerCase()"),
                        "outer_html": (await elem.evaluate("el => el.outerHTML"))[:500],
                    }
                )
            except Exception as e:
                elements.append({"index": i, "error": str(e)})

        return {
            "iframe_selector": iframe_selector,
            "inner_selector": inner_selector,
            "inner_count": count,
            "elements": elements,
            "frame_url": frame.url,
        }

    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Image Comparison Tools
# =============================================================================


@mcp.tool
async def compare_image(
    selector: str,
    reference_path: str,
    selector_type: str = "css",
    index: int = 0,
    threshold: float = 5.0,
    scan_folder: bool = False,
) -> dict:
    """Compare web element image against reference image(s).

    Extracts image from a web element and compares it against reference images
    using OpenCV. Supports single image comparison or folder scanning.

    Args:
        selector: CSS/XPath selector for element containing image.
        reference_path: Path to reference image or folder.
            - Single file: "sample/ZZZ Avatar.png"
            - Folder: "reward image" (set scan_folder=True)
        selector_type: Type of selector - 'css', 'xpath', 'text', 'text_exact', 'role'.
        index: Element index if multiple match (default: 0).
        threshold: Match threshold percentage (default: 5.0, lower = stricter).
        scan_folder: If True, scan all images in folder and return best match.

    Returns:
        dict with comparison results:
            - success: bool
            - match: bool - True if difference < threshold
            - difference_percent: float
            - threshold: float
            - best_match: str (only if scan_folder=True)
            - comparisons: list (only if scan_folder=True)

    Examples:
        # Check if current avatar is ZZZ
        compare_image(selector=".avatarsItemImg-AiUG1h", reference_path="sample/ZZZ Avatar.png")

        # Detect reward type from draw
        compare_image(selector=".gainPrizeImage-FqEqMM", reference_path="reward image", scan_folder=True)
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        # Find the element
        locator = create_locator(page, selector, SelectorType(selector_type))
        count = await locator.count()

        if count == 0:
            return {
                "success": False,
                "error": "element_not_found",
                "message": f"No elements found for selector: {selector}",
            }

        if index >= count:
            return {
                "success": False,
                "error": "element_not_found",
                "message": f"Index {index} out of range (found {count} elements)",
            }

        elem = locator.nth(index)

        # Fetch image from element
        try:
            target_img = await fetch_image_from_locator_async(page, elem)
        except ValueError as e:
            return {
                "success": False,
                "error": "no_image_found",
                "message": str(e),
                "selector": selector,
            }

        # Check if reference path exists
        if not os.path.exists(reference_path):
            return {
                "success": False,
                "error": "reference_not_found",
                "message": f"Reference path not found: {reference_path}",
            }

        # Folder scanning mode
        if scan_folder:
            if not os.path.isdir(reference_path):
                return {
                    "success": False,
                    "error": "reference_not_found",
                    "message": f"scan_folder=True but path is not a directory: {reference_path}",
                }

            result = scan_folder_for_best_match(target_img, reference_path, threshold)
            result["success"] = True
            result["selector"] = selector
            result["reference_path"] = reference_path
            return result

        # Single image comparison
        if os.path.isdir(reference_path):
            return {
                "success": False,
                "error": "reference_not_found",
                "message": "reference_path is a directory. Set scan_folder=True to scan folder.",
            }

        try:
            diff = compare_images_sync(target_img, reference_path)
        except ValueError as e:
            return {
                "success": False,
                "error": "comparison_failed",
                "message": str(e),
            }

        return {
            "success": True,
            "match": diff < threshold,
            "difference_percent": round(diff, 2),
            "threshold": threshold,
            "selector": selector,
            "reference_path": reference_path,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


@mcp.tool
async def download_image(
    selector: str,
    filename: str,
    selector_type: str = "css",
    index: int = 0,
) -> dict:
    """Download and save image from web element to disk.

    Extracts image from a web element and saves it to the screenshot folder.
    Supports img elements, background-image styles, and data URIs.

    Args:
        selector: CSS/XPath selector for element containing image.
        filename: Output filename (saved to screenshot/ folder).
        selector_type: Type of selector - 'css', 'xpath', 'text', 'text_exact', 'role'.
        index: Element index if multiple match (default: 0).

    Returns:
        dict with save results:
            - success: bool
            - path: str - Full path to saved image
            - width: int - Image width in pixels
            - height: int - Image height in pixels
            - selector: str

    Examples:
        # Save unknown reward for adding to reference folder
        download_image(selector=".gainPrizeImage-FqEqMM", filename="new_reward.png")

        # Save avatar image for debugging
        download_image(selector=".avatarsItemImg-AiUG1h", filename="avatar_debug.png")
    """
    session = await BrowserSession.get_instance()
    if not session.is_active:
        return {"error": "No active session. Call open_page first."}

    page = session.page

    try:
        # Find the element
        locator = create_locator(page, selector, SelectorType(selector_type))
        count = await locator.count()

        if count == 0:
            return {
                "success": False,
                "error": "element_not_found",
                "message": f"No elements found for selector: {selector}",
            }

        if index >= count:
            return {
                "success": False,
                "error": "element_not_found",
                "message": f"Index {index} out of range (found {count} elements)",
            }

        elem = locator.nth(index)

        # Fetch image from element
        try:
            img = await fetch_image_from_locator_async(page, elem)
        except ValueError as e:
            return {
                "success": False,
                "error": "no_image_found",
                "message": str(e),
                "selector": selector,
            }

        # Ensure filename has extension
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            filename += ".png"

        # Save to screenshot folder
        output_path = os.path.join(CONFIG["SCREENSHOT_FOLDER"], filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        success = cv2.imwrite(output_path, img)
        if not success:
            return {
                "success": False,
                "error": "save_failed",
                "message": f"Failed to save image to: {output_path}",
            }

        height, width = img.shape[:2]

        return {
            "success": True,
            "path": output_path,
            "width": width,
            "height": height,
            "selector": selector,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


if __name__ == "__main__":
    mcp.run(transport="stdio")
