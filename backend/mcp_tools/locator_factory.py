"""Multi-syntax selector support for MCP inspector tools.

Provides a unified interface for creating Playwright locators from
various selector syntaxes: CSS, XPath, text, and ARIA roles.

Usage:
    from locator_factory import SelectorType, create_locator

    # CSS selector (default)
    locator = create_locator(page, ".my-class", SelectorType.CSS)

    # XPath
    locator = create_locator(page, "//div[@class='test']", SelectorType.XPATH)

    # Text content (partial match)
    locator = create_locator(page, "Submit", SelectorType.TEXT)

    # ARIA role with name
    locator = create_locator(page, "button:Submit", SelectorType.ROLE)
"""

import re
from enum import Enum

from playwright.async_api import Locator, Page


class SelectorType(str, Enum):
    """Supported selector types for element location."""

    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    TEXT_EXACT = "text_exact"
    ROLE = "role"


def create_locator(
    page: Page,
    selector: str,
    selector_type: SelectorType = SelectorType.CSS,
) -> Locator:
    """Create a Playwright locator from selector with specified type.

    Args:
        page: Playwright Page instance.
        selector: The selector string. Format depends on selector_type:
            - css: Standard CSS selector (e.g., ".class", "#id")
            - xpath: XPath expression (e.g., "//div[@id='test']")
            - text: Partial text match (e.g., "Submit")
            - text_exact: Exact text match (e.g., "Submit Order")
            - role: ARIA role with optional name, format "role:name"
                   (e.g., "button:Submit", "heading", "link:Learn more")
        selector_type: Type of selector (default: CSS).

    Returns:
        Playwright Locator instance.

    Raises:
        ValueError: If selector_type is invalid or selector format is wrong.
    """
    selector_type = SelectorType(selector_type)

    if selector_type == SelectorType.CSS:
        return page.locator(selector)

    elif selector_type == SelectorType.XPATH:
        return page.locator(f"xpath={selector}")

    elif selector_type == SelectorType.TEXT:
        return page.get_by_text(selector, exact=False)

    elif selector_type == SelectorType.TEXT_EXACT:
        return page.get_by_text(selector, exact=True)

    elif selector_type == SelectorType.ROLE:
        return _create_role_locator(page, selector)

    else:
        raise ValueError(f"Unsupported selector type: {selector_type}")


def _create_role_locator(page: Page, selector: str) -> Locator:
    """Create a role-based locator from 'role:name' format.

    Args:
        page: Playwright Page instance.
        selector: Role selector in format "role" or "role:name".
                 Examples: "button", "button:Submit", "heading:Welcome"

    Returns:
        Playwright Locator instance.
    """
    if ":" in selector:
        role, name = selector.split(":", 1)
        return page.get_by_role(role.strip(), name=name.strip())
    else:
        return page.get_by_role(selector.strip())


def analyze_selector_stability(selector: str) -> dict:
    """Analyze a CSS selector for stability indicators.

    Detects patterns that suggest dynamic/hashed class names which
    may break when the website is updated.

    Args:
        selector: CSS selector string to analyze.

    Returns:
        dict with stability analysis:
            - is_stable: bool, overall stability assessment
            - warnings: list of potential issues
            - suggestions: list of more stable alternatives
    """
    warnings = []
    suggestions = []

    # Pattern 1: Hashed class names (e.g., .gainPrizeImage-FqEqMM)
    hashed_pattern = r"\.[a-zA-Z]+-[A-Za-z0-9]{5,8}"
    hashed_matches = re.findall(hashed_pattern, selector)
    if hashed_matches:
        warnings.append(f"Contains hashed class names that may change: {hashed_matches}")
        suggestions.append("Consider using [class*='gainPrizeImage'] for partial match")

    # Pattern 2: Very specific nth-child selectors
    nth_pattern = r":nth-child\(\d+\)"
    if re.search(nth_pattern, selector):
        warnings.append("Uses nth-child which breaks if element order changes")
        suggestions.append("Consider using data attributes or unique classes")

    # Pattern 3: Deep nesting (more than 4 levels)
    nesting_level = selector.count(" > ") + selector.count(" ")
    if nesting_level > 4:
        warnings.append(f"Deep nesting ({nesting_level} levels) is fragile")
        suggestions.append("Target elements closer to the desired element")

    # Pattern 4: ID selectors (usually stable)
    if "#" in selector:
        # IDs are generally stable, reduce warning level
        pass

    # Pattern 5: Data attributes (usually stable)
    data_attr_pattern = r"\[data-[a-z-]+"
    if re.search(data_attr_pattern, selector):
        suggestions.append("Data attributes are typically stable - good choice!")

    # Pattern 6: Attribute contains selector with partial match
    contains_pattern = r"\[class\*='[^']+'\]"
    if re.search(contains_pattern, selector):
        suggestions.append("Partial class match is more resilient to hash changes")

    is_stable = len(warnings) == 0

    return {
        "is_stable": is_stable,
        "warnings": warnings,
        "suggestions": suggestions,
        "selector": selector,
    }


def suggest_alternative_selectors(element_info: dict) -> list[dict]:
    """Suggest alternative selectors based on element information.

    Args:
        element_info: dict containing element attributes:
            - tag_name: HTML tag name
            - id: Element ID (if any)
            - class_list: List of class names
            - text_content: Text content
            - data_attrs: Dict of data-* attributes
            - aria_label: ARIA label (if any)
            - role: ARIA role (if any)

    Returns:
        List of suggested selectors with stability ratings.
    """
    suggestions = []

    tag = element_info.get("tag_name", "div")
    elem_id = element_info.get("id")
    classes = element_info.get("class_list", [])
    text = element_info.get("text_content", "")
    data_attrs = element_info.get("data_attrs", {})
    aria_label = element_info.get("aria_label")
    role = element_info.get("role")

    # ID selector (most stable)
    if elem_id:
        suggestions.append(
            {
                "selector": f"#{elem_id}",
                "type": "css",
                "stability": "high",
                "reason": "ID selectors are unique and stable",
            }
        )

    # Data attribute selectors
    for attr, value in data_attrs.items():
        suggestions.append(
            {
                "selector": f"[{attr}='{value}']",
                "type": "css",
                "stability": "high",
                "reason": "Data attributes are typically intentional and stable",
            }
        )

    # ARIA role + name
    if role and aria_label:
        suggestions.append(
            {
                "selector": f"{role}:{aria_label}",
                "type": "role",
                "stability": "high",
                "reason": "ARIA roles and labels are semantic and stable",
            }
        )
    elif role:
        suggestions.append(
            {
                "selector": role,
                "type": "role",
                "stability": "medium",
                "reason": "ARIA role without name may match multiple elements",
            }
        )

    # Text content
    if text and len(text) < 50:
        suggestions.append(
            {
                "selector": text.strip(),
                "type": "text_exact",
                "stability": "medium",
                "reason": "Text content may change with localization",
            }
        )

    # Class partial match (for hashed classes)
    for cls in classes:
        # Extract base name before hash
        match = re.match(r"^([a-zA-Z]+)-[A-Za-z0-9]{5,8}$", cls)
        if match:
            base_name = match.group(1)
            suggestions.append(
                {
                    "selector": f"[class*='{base_name}']",
                    "type": "css",
                    "stability": "medium",
                    "reason": f"Partial match for hashed class '{cls}'",
                }
            )

    # Tag + stable class combination
    stable_classes = [c for c in classes if not re.match(r".*-[A-Za-z0-9]{5,8}$", c)]
    if stable_classes:
        suggestions.append(
            {
                "selector": f"{tag}.{stable_classes[0]}",
                "type": "css",
                "stability": "medium",
                "reason": "Class without hash suffix is likely stable",
            }
        )

    return suggestions


def get_selector_type_description(selector_type: SelectorType) -> str:
    """Get a human-readable description of a selector type.

    Args:
        selector_type: The SelectorType enum value.

    Returns:
        Description string.
    """
    descriptions = {
        SelectorType.CSS: "CSS selector (e.g., '.class', '#id', 'div > span')",
        SelectorType.XPATH: "XPath expression (e.g., '//div[@id=\"test\"]')",
        SelectorType.TEXT: "Partial text match (e.g., 'Submit' matches 'Submit Order')",
        SelectorType.TEXT_EXACT: "Exact text match (e.g., 'Submit' only)",
        SelectorType.ROLE: "ARIA role with optional name (e.g., 'button:Submit')",
    }
    return descriptions.get(selector_type, "Unknown selector type")
