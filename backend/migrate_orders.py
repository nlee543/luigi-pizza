"""Upgrade the existing SQLite orders table without losing order relationships."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from database import DATABASE_PATH


def migrate_orders(path: Path = DATABASE_PATH) -> Path | None:
    with sqlite3.connect(path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(orders)")}
        if not columns or {"status", "order_time"} <= columns:
            return None
        if columns != {"id", "user_id"}:
            raise ValueError("Unexpected orders schema; migration requires id and user_id only.")
        backup = path.with_name(
            f"{path.stem}.before-order-status-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.db"
        )
        with sqlite3.connect(backup) as destination:
            connection.backup(destination)
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN IMMEDIATE")
        try:
            objects = connection.execute(
                "SELECT sql FROM sqlite_master WHERE tbl_name = 'orders' "
                "AND type IN ('index', 'trigger') AND sql IS NOT NULL"
            ).fetchall()
            connection.execute("""
                CREATE TABLE orders_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    status VARCHAR NOT NULL DEFAULT 'order_received'
                        CONSTRAINT orders_status CHECK (status IN (
                            'order_received', 'preparing', 'out_for_delivery',
                            'ready_for_pickup', 'completed')),
                    order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute("""
                INSERT INTO orders_new (id, user_id, status, order_time)
                SELECT id, user_id, 'completed', CURRENT_TIMESTAMP FROM orders
            """)
            connection.execute("DROP TABLE orders")
            connection.execute("ALTER TABLE orders_new RENAME TO orders")
            for (sql,) in objects:
                connection.execute(sql)
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Foreign key verification failed; migration rolled back.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        return backup


if __name__ == "__main__":
    backup = migrate_orders()
    print(f"Orders migrated. Backup: {backup}" if backup else "No migration needed.")
