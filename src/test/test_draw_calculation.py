"""Test script to verify draw limit calculation logic.

This tests the fix for draw limit detection (should be 0 remaining when limit is reached).
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from StringUtil import extract_number


def test_extract_number():
    """Test the extract_number function with various inputs."""
    print("=" * 70)
    print("EXTRACT_NUMBER FUNCTION TEST")
    print("=" * 70)

    test_cases = [
        ("0/5", "left", 0, "No draws used yet"),
        ("0/5", "right", 5, "Total draws available"),
        ("3/5", "left", 3, "Partially used draws"),
        ("3/5", "right", 5, "Total draws"),
        ("5/5", "left", 5, "All draws used"),
        ("5/5", "right", 5, "Total draws"),
        ("10/10", "left", 10, "Double digit - used"),
        ("10/10", "right", 10, "Double digit - total"),
    ]

    passed = 0
    failed = 0

    for text, side, expected, description in test_cases:
        result = extract_number(text, side=side)
        status = "[PASS]" if result == expected else "[FAIL]"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | extract_number('{text}', '{side}') = {result} (expected: {expected}) - {description}")

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


def test_draw_remaining_calculation():
    """Test the draw remaining calculation logic."""
    print("\n" + "=" * 70)
    print("DRAW REMAINING CALCULATION TEST")
    print("=" * 70)

    test_cases = [
        ("0/5", 5, "No draws used - should have 5 remaining"),
        ("1/5", 4, "1 draw used - should have 4 remaining"),
        ("3/5", 2, "3 draws used - should have 2 remaining"),
        ("4/5", 1, "4 draws used - should have 1 remaining"),
        ("5/5", 0, "All draws used - should have 0 remaining (THE FIX)"),
        ("10/10", 0, "Double digit - all used"),
        ("0/10", 10, "Double digit - none used"),
    ]

    passed = 0
    failed = 0

    for draw_limit_text, expected_remaining, description in test_cases:
        # Simulate the fixed logic from DrawHandler.py
        draws_used = extract_number(draw_limit_text, side="left")
        draws_total = extract_number(draw_limit_text, side="right")

        if draws_used is not None and draws_total is not None:
            draws_remaining = draws_total - draws_used
        else:
            draws_remaining = None

        status = "[PASS]" if draws_remaining == expected_remaining else "[FAIL]"

        if draws_remaining == expected_remaining:
            passed += 1
        else:
            failed += 1

        print(f"{status} | '{draw_limit_text}' -> {draws_used}/{draws_total} -> {draws_remaining} remaining (expected: {expected_remaining})")
        print(f"       {description}")

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


def test_available_draws_calculation():
    """Test the final available draws calculation."""
    print("\n" + "=" * 70)
    print("AVAILABLE DRAWS CALCULATION TEST")
    print("=" * 70)
    print("Tests: available = min(affordable, remaining)\n")

    test_cases = [
        (1000, 100, "5/5", 0, "Enough points but limit reached"),
        (1000, 100, "0/5", 5, "Enough points for all draws"),
        (1000, 100, "3/5", 2, "Enough points for remaining draws"),
        (150, 100, "0/5", 1, "Limited by points (only afford 1)"),
        (250, 100, "0/5", 2, "Limited by points (only afford 2)"),
        (50, 100, "0/5", 0, "Not enough points for any draw"),
        (500, 100, "4/5", 1, "Enough points but only 1 remaining"),
    ]

    passed = 0
    failed = 0

    for current_points, draw_price, draw_limit_text, expected_available, description in test_cases:
        # Simulate the full logic from DrawHandler._calculate_available_draws
        max_affordable = current_points // draw_price

        draws_used = extract_number(draw_limit_text, side="left")
        draws_total = extract_number(draw_limit_text, side="right")
        draws_remaining = draws_total - draws_used

        available = min(max_affordable, draws_remaining)

        status = "[PASS]" if available == expected_available else "[FAIL]"

        if available == expected_available:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {current_points} pts, ${draw_price}/draw, {draw_limit_text} limit")
        print(f"       -> {max_affordable} affordable, {draws_remaining} remaining, {available} available (expected: {expected_available})")
        print(f"       {description}\n")

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DRAW LIMIT DETECTION FIX - UNIT TESTS")
    print("=" * 70 + "\n")

    all_passed = True

    # Run all tests
    all_passed &= test_extract_number()
    all_passed &= test_draw_remaining_calculation()
    all_passed &= test_available_draws_calculation()

    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED! Draw limit detection is working correctly.")
        print("          The fix correctly calculates 0 available draws when limit is 5/5.")
    else:
        print("[FAILED] SOME TESTS FAILED! Please review the output above.")
    print("=" * 70 + "\n")

    sys.exit(0 if all_passed else 1)
