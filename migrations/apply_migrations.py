#!/usr/bin/env python3
"""
Apply all SQL migrations to the registry database.
Usage: python3 apply_migrations.py [path_to_database]
Default database path: ../registry.db
"""
import sqlite3
import sys
import os
import glob

def apply_migrations(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    # Backup reminder
    print(f"Applying migrations to: {db_path}")
    print("Make sure you have a backup before proceeding!\n")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Create migrations tracking table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Get already-applied migrations
    cur.execute("SELECT filename FROM _migrations")
    applied = {row[0] for row in cur.fetchall()}

    # Find and sort migration SQL files
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))

    applied_count = 0
    for sql_path in sql_files:
        filename = os.path.basename(sql_path)
        if filename in applied:
            print(f"  SKIP (already applied): {filename}")
            continue

        print(f"  APPLYING: {filename} ... ", end="")
        with open(sql_path, "r") as f:
            sql = f.read()

        try:
            cur.executescript(sql)
            cur.execute("INSERT INTO _migrations (filename) VALUES (?)", (filename,))
            conn.commit()
            print("OK")
            applied_count += 1
        except Exception as e:
            conn.rollback()
            print(f"FAILED: {e}")
            sys.exit(1)

    if applied_count == 0:
        print("\nAll migrations already applied.")
    else:
        print(f"\nSuccessfully applied {applied_count} migration(s).")

    # Print data quality summary
    try:
        cur.execute("SELECT * FROM v_data_quality_summary")
        row = cur.fetchone()
        if row:
            cols = [desc[0] for desc in cur.description]
            print("\n--- Data Quality Summary ---")
            for col, val in zip(cols, row):
                print(f"  {col}: {val}")
    except Exception:
        pass  # View may not exist yet

    conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "registry.db"
    )
    apply_migrations(db_path)
