"""Add authentication to an existing SQLite database, with a backup first."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from sqlalchemy import URL, create_engine

from database import DATABASE_PATH
from models import LoginSession


def migrate_auth(path: Path = DATABASE_PATH):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("Database does not exist. Start the API to create a fresh database.")
    with sqlite3.connect(path) as connection:
        users = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        orders = {row[1] for row in connection.execute("PRAGMA table_info(orders)")}
        if {"role", "password_hash", "must_change_password", "active"} <= users and "created_by_user_id" in orders:
            return None
        if "admin" not in users or not {"status", "order_time", "user_id"} <= orders:
            raise ValueError("Unexpected schema. Run migrate_orders.py first for older orders tables.")
        # Normalized emails must remain unique; never silently merge customers.
        duplicates = connection.execute(
            "SELECT lower(trim(email)) FROM users WHERE email IS NOT NULL "
            "GROUP BY lower(trim(email)) HAVING count(*) > 1"
        ).fetchall()
        if duplicates:
            raise ValueError("Resolve case-insensitive duplicate emails before migration.")
        backup = path.with_name(f"{path.stem}.before-auth-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.db")
        with sqlite3.connect(backup) as destination:
            connection.backup(destination)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'customer' "
                               "CHECK (role IN ('customer', 'staff', 'admin'))")
            connection.execute("UPDATE users SET role = CASE WHEN admin = 1 THEN 'admin' ELSE 'customer' END")
            connection.execute("ALTER TABLE users DROP COLUMN admin")
            connection.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR")
            connection.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0")
            connection.execute("ALTER TABLE users ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1")
            connection.execute("UPDATE users SET email = lower(trim(email)) WHERE email IS NOT NULL")
            connection.execute("ALTER TABLE orders ADD COLUMN created_by_user_id INTEGER REFERENCES users(id)")
            # Historical creator is unknown: leave NULL instead of inventing attribution.
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Foreign key verification failed.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    engine = create_engine(URL.create("sqlite", database=str(path)))
    try:
        LoginSession.__table__.create(engine, checkfirst=True)
    finally:
        engine.dispose()
    return backup


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DATABASE_PATH)
    args = parser.parse_args()
    backup = migrate_auth(args.path)
    print(f"Authentication schema migrated. Backup: {backup}" if backup else "No migration needed.")
