"""Clear all dev data so the app starts fresh for testing.

Drops the zzz_bot_dev MongoDB database and removes local data directories
(output/, authentication data/, screenshot/, backend/logs/).
"""

import shutil
import sys
from pathlib import Path

from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DIRS_TO_CLEAR = [
    PROJECT_ROOT / "output",
    PROJECT_ROOT / "authentication data",
    PROJECT_ROOT / "screenshot",
    PROJECT_ROOT / "backend" / "logs",
]

DATABASE_NAME = "zzz_bot_dev"
MONGODB_URI = "mongodb://localhost:27017"


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


def clear_database() -> None:
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
    except Exception as exc:
        print(f"  MongoDB not reachable, skipping: {exc}")
        return

    client.drop_database(DATABASE_NAME)
    print(f"  Dropped database: {DATABASE_NAME}")
    client.close()


def main() -> None:
    print(f"\n{'=' * 50}")
    print("  Clear Dev Data")
    print(f"{'=' * 50}\n")

    print("[1/2] Clearing local directories...")
    clear_directories()

    print("\n[2/2] Clearing MongoDB database...")
    clear_database()

    print(f"\n{'=' * 50}")
    print("  Done! App is ready for fresh testing.")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
