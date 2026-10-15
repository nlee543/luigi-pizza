"""Create a fresh Luigi's Pizza database using only Python's standard library."""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def connect(path):
    connection = sqlite3.connect(path, timeout=10)
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def initialize(path):
    path = Path(path)
    # Exclusive creation protects an existing database from accidental replacement.
    with path.open('xb'):
        pass
    try:
        with connect(path) as connection:
            connection.execute('PRAGMA journal_mode = WAL')
            for filename in ('schema.sql', 'seed.sql'):
                connection.executescript((ROOT / filename).read_text(encoding='utf-8'))
            assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert not connection.execute('PRAGMA foreign_key_check').fetchall()
    finally:
        if 'connection' in locals():
            connection.close()
    return path.resolve()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=str(ROOT / 'luigi_pizza.db'))
    args = parser.parse_args()
    print(f'Created {initialize(args.path)}')
