import sqlite3
from pathlib import Path

from db import DB_NAME, get_connection


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def get_table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row["name"] for row in rows]


def get_column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({quote_identifier(table_name)})").fetchall()
    return [row["name"] for row in rows]


def inspect_schema() -> int:
    db_path = Path(DB_NAME)
    if not db_path.exists():
        print(f"Database not found: {db_path.resolve()}")
        print("Run the app once to create it, or call init_db() before inspecting the schema.")
        return 1

    try:
        conn = get_connection(db_path)
    except sqlite3.Error as exc:
        print(f"Could not connect to database: {exc}")
        return 1

    try:
        table_names = get_table_names(conn)
        if not table_names:
            print("No tables found.")
            return 0

        print("Tables:")
        for table_name in table_names:
            print(f"- {table_name}")

        print("\nColumns:")
        for table_name in table_names:
            column_names = get_column_names(conn, table_name)
            print(f"\n{table_name}:")
            for column_name in column_names:
                print(f"- {column_name}")
        return 0
    except sqlite3.Error as exc:
        print(f"Could not inspect database schema: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(inspect_schema())
