"""
import.py — Bulk import all JSON sample datasets into the Flask/SQLAlchemy database.

Log messages mirror the exact formats used by the API controllers:
  - auth.py      → "User signed up"
  - collection.py→ "Created collection {id} - {name}" / "Edited collection {id} - {name}"
  - flashcard.py → "Created flashcard {id} - {front} in collection {id} - {name}"
                   "Edited flashcard {id} - {front}"

Duplicate-username handling:
  - If a username already exists, the incoming user is renamed to "{username}_2",
    "{username}_3", etc., until a unique name is found.

Usage (run from the demo1 directory):
    python import.py
    python import.py --clear       # drop all existing data first
    python import.py --dry-run     # validate only, no writes
"""

import os
import sys
import glob
import json
import argparse
from datetime import datetime

# ── ensure we can import from the demo1 package ───────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models.user import User
from models.collection import Collection
from models.flashcard import Flashcard
from models.action_log import ActionLog
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def unique_username(base: str, taken: set) -> str:
    """Return a username that is not in *taken*, renaming with a numeric suffix."""
    if base not in taken:
        return base
    counter = 2
    while True:
        candidate = f"{base}_{counter}"
        if candidate not in taken:
            return candidate
        counter += 1


def parse_timestamp(ts_str: str | None) -> datetime:
    """Parse an ISO-8601 timestamp string. Falls back to utcnow() on error."""
    if not ts_str:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


# ─────────────────────────────────────────────────────────────────────────────
# Core import routine
# ─────────────────────────────────────────────────────────────────────────────

def import_dataset(data: dict, dry_run: bool, taken_usernames: set) -> dict:
    """
    Processes a single parsed JSON dataset dict.
    Returns a stats dict: {users, collections, flashcards, logs, renamed}.
    """
    stats = {"users": 0, "collections": 0, "flashcards": 0, "logs": 0, "renamed": []}

    for user_data in data.get("users", []):
        # ── resolve username ──────────────────────────────────────────────────
        original_username = user_data.get("username", "unknown")
        username = unique_username(original_username, taken_usernames)
        if username != original_username:
            stats["renamed"].append((original_username, username))
            print(f"  ⚠  Duplicate username '{original_username}' → renamed to '{username}'")
        taken_usernames.add(username)

        # ── create User ───────────────────────────────────────────────────────
        raw_pw = user_data.get("password", "default_password")
        # If the JSON already contains a real hash (starts with 'pbkdf2:sha256:')
        # keep it; otherwise hash the raw value.
        if raw_pw.startswith("pbkdf2:sha256:") or raw_pw.startswith("scrypt:"):
            password_hash = raw_pw
        else:
            password_hash = generate_password_hash(raw_pw)

        user = User(
            username=username,
            password_hash=password_hash,
            role=user_data.get("role", "user"),
        )

        if not dry_run:
            db.session.add(user)
            db.session.flush()          # get user.id without full commit
        else:
            user.id = -1                # placeholder for dry-run log messages

        stats["users"] += 1

        # ── user-level log: "User signed up"  (mirrors auth.py → signup) ─────
        signup_ts = parse_timestamp(
            next((lg["timestamp"] for lg in user_data.get("logs", [])
                  if "created" in lg.get("action", "").lower()), None)
        )
        if not dry_run:
            db.session.add(ActionLog(
                user_id=user.id,
                action="User signed up",
                timestamp=signup_ts,
            ))
        stats["logs"] += 1

        # ── collections ───────────────────────────────────────────────────────
        for col_data in user_data.get("collections", []):
            col = Collection(
                name=col_data.get("name", "Unnamed Collection"),
                user_id=user.id,
                status=col_data.get("status", "private"),
            )

            if not dry_run:
                db.session.add(col)
                db.session.flush()
            else:
                col.id = -1

            stats["collections"] += 1

            # ── collection logs (mirrors collection.py → create/edit) ─────────
            for log_entry in col_data.get("logs", []):
                action_text = log_entry.get("action", "")
                log_ts = parse_timestamp(log_entry.get("timestamp"))

                # Map JSON action text → API-style log message
                if "created" in action_text.lower():
                    # mirrors: f"Created collection {new_col.id} - {new_col.name}"
                    mapped = f"Created collection {col.id} - {col.name}"
                elif "edited" in action_text.lower() or "updated" in action_text.lower():
                    # mirrors: f"Edited collection {col.id} - {col.name}"
                    mapped = f"Edited collection {col.id} - {col.name}"
                else:
                    mapped = f"{action_text} | collection {col.id} - {col.name}"

                if not dry_run:
                    db.session.add(ActionLog(
                        user_id=user.id,
                        action=mapped,
                        timestamp=log_ts,
                    ))
                stats["logs"] += 1

            # ── flashcards ────────────────────────────────────────────────────
            for card_data in col_data.get("flashcards", []):
                card = Flashcard(
                    collection_id=col.id,
                    front=card_data.get("front", ""),
                    back=card_data.get("back", ""),
                    status=card_data.get("status", "not learn"),
                    repetition=card_data.get("repetition", 0),
                    easiness_factor=card_data.get("easiness_factor", 2.5),
                    interval=card_data.get("interval", 0),
                    next_review_date=parse_timestamp(card_data.get("next_review_date")),
                )

                if not dry_run:
                    db.session.add(card)
                    db.session.flush()
                else:
                    card.id = -1

                stats["flashcards"] += 1

                # ── flashcard logs (mirrors flashcard.py → create/edit) ───────
                for log_entry in card_data.get("logs", []):
                    action_text = log_entry.get("action", "")
                    log_ts = parse_timestamp(log_entry.get("timestamp"))

                    if "created" in action_text.lower():
                        # mirrors: f"Created flashcard {id} - {front} in collection {id} - {name}"
                        mapped = (
                            f"Created flashcard {card.id} - {card.front} "
                            f"in collection {col.id} - {col.name}"
                        )
                    elif "edited" in action_text.lower() or "updated" in action_text.lower():
                        # mirrors: f"Edited flashcard {id} - {front}"
                        mapped = f"Edited flashcard {card.id} - {card.front}"
                    elif "deleted" in action_text.lower():
                        mapped = f"Deleted flashcard {card.id} - {card.front}"
                    else:
                        mapped = f"{action_text} | flashcard {card.id} - {card.front}"

                    if not dry_run:
                        db.session.add(ActionLog(
                            user_id=user.id,
                            action=mapped,
                            timestamp=log_ts,
                        ))
                    stats["logs"] += 1

        if not dry_run:
            db.session.commit()         # commit once per user for safety

    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Entry-point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bulk-import JSON sample datasets.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing users, collections, flashcards, and logs before import.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate data without writing to the database.",
    )
    args = parser.parse_args()

    # ── bootstrap Flask app context ───────────────────────────────────────────
    app = create_app()

    with app.app_context():
        if args.clear and not args.dry_run:
            print("🗑  --clear flag detected. Wiping existing data…")
            ActionLog.query.delete()
            Flashcard.query.delete()
            Collection.query.delete()
            User.query.delete()
            db.session.commit()
            print("   ✓ Database cleared.\n")

        # ── collect already-present usernames from DB ─────────────────────────
        taken_usernames: set = set(
            u.username for u in User.query.with_entities(User.username).all()
        )

        # ── discover JSON files in the 'sample dataset' folder ───────────────
        dataset_dir = os.path.join(BASE_DIR, "sample dataset")
        json_files = sorted(glob.glob(os.path.join(dataset_dir, "*.json")))

        if not json_files:
            print(f"❌  No JSON files found in: {dataset_dir}")
            sys.exit(1)

        print(f"📂  Found {len(json_files)} dataset file(s) in '{dataset_dir}'")
        if args.dry_run:
            print("🔍  DRY-RUN mode — no data will be written.\n")

        total = {"users": 0, "collections": 0, "flashcards": 0, "logs": 0, "renamed": []}

        for json_path in json_files:
            filename = os.path.basename(json_path)
            print(f"\n── Processing: {filename} ──────────────────────────────────")

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"  ❌  Failed to read '{filename}': {exc}")
                continue

            stats = import_dataset(data, dry_run=args.dry_run, taken_usernames=taken_usernames)

            print(f"  ✓  Users:       {stats['users']}")
            print(f"  ✓  Collections: {stats['collections']}")
            print(f"  ✓  Flashcards:  {stats['flashcards']}")
            print(f"  ✓  Log entries: {stats['logs']}")
            if stats["renamed"]:
                print(f"  ⚠  Renamed {len(stats['renamed'])} username(s):")
                for orig, new in stats["renamed"]:
                    print(f"       '{orig}' → '{new}'")

            for key in ("users", "collections", "flashcards", "logs"):
                total[key] += stats[key]
            total["renamed"].extend(stats["renamed"])

        # ── summary ───────────────────────────────────────────────────────────
        print("\n" + "=" * 55)
        mode_label = "DRY-RUN SUMMARY" if args.dry_run else "IMPORT COMPLETE"
        print(f"  {mode_label}")
        print("=" * 55)
        print(f"  Total users imported:       {total['users']}")
        print(f"  Total collections imported: {total['collections']}")
        print(f"  Total flashcards imported:  {total['flashcards']}")
        print(f"  Total log entries created:  {total['logs']}")
        print(f"  Total usernames renamed:    {len(total['renamed'])}")
        if total["renamed"]:
            print("\n  Renamed usernames:")
            for orig, new in total["renamed"]:
                print(f"    '{orig}' → '{new}'")
        print()


if __name__ == "__main__":
    main()
