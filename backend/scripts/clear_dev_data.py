"""Clear all dev data so the app starts fresh for testing.

Removes local data directories: data/ (the SQLite database), output/,
authentication data/, screenshot/, and backend/logs/.
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DIRS_TO_CLEAR = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "output",
    PROJECT_ROOT / "authentication data",
    PROJECT_ROOT / "screenshot",
    PROJECT_ROOT / "backend" / "logs",
]


def clear_directories() -> None:
    for dir_path in DIRS_TO_CLEAR:
        if not dir_path.exists():
            print(f"  Skipped (not found): {dir_path.relative_to(PROJECT_ROOT)}")
            continue
        try:
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path.relative_to(PROJECT_ROOT)}")
        except PermissionError:
            # Windows may lock directories — delete contents instead
            deleted = 0
            for item in dir_path.rglob("*"):
                if item.is_file():
                    try:
                        item.unlink()
                        deleted += 1
                    except PermissionError:
                        print(f"  Locked, skipped: {item.relative_to(PROJECT_ROOT)}")
            print(
                f"  Cleared {deleted} file(s) in: {dir_path.relative_to(PROJECT_ROOT)} (dir locked)"
            )


def main() -> None:
    print(f"\n{'=' * 50}")
    print("  Clear Dev Data")
    print(f"{'=' * 50}\n")

    print("Clearing local directories...")
    clear_directories()

    print(f"\n{'=' * 50}")
    print("  Done! App is ready for fresh testing.")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
