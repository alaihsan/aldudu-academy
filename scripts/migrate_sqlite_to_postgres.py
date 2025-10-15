"""Simple migration script: copy data from SQLite to Postgres using SQLAlchemy.

Usage:
  SQLITE_URL=sqlite:////absolute/path/to/aldudu_academy.db POSTGRES_URL=postgresql://user:pass@host:5432/dbname \
    python scripts/migrate_sqlite_to_postgres.py

This script:
- connects to source (SQLite) and target (Postgres)
- reflects existing tables
- copies rows table-by-table while preserving PKs and relationships where possible

Notes:
- Run on a machine where both DBs are reachable and psycopg2 installed.
- Test on a copy of production DB before running on live data.
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.exc import SQLAlchemyError


def copy_table(src_engine, dst_engine, table_name, pk_cols):
    src_meta = MetaData()
    dst_meta = MetaData()

    # Reflect table definitions from each engine
    src_table = Table(table_name, src_meta, autoload_with=src_engine)
    dst_table = Table(table_name, dst_meta, autoload_with=dst_engine)

    inserted = 0
    with src_engine.connect() as sconn, dst_engine.connect() as dconn:
        sel = select(src_table)
        result = sconn.execute(sel)
        rows = [dict(r._mapping) for r in result]
        if not rows:
            print(f"No rows for {table_name}")
            return 0

        # Bulk insert using transaction on destination
        try:
            with dconn.begin():
                dconn.execute(dst_table.insert(), rows)
                inserted = len(rows)
        except Exception as e:
            print(f"Failed to insert into {table_name}: {e}")
            raise

    print(f"Copied {inserted} rows into {table_name}")
    return inserted


def main():
    sqlite_url = os.environ.get('SQLITE_URL')
    pg_url = os.environ.get('POSTGRES_URL')
    if not sqlite_url or not pg_url:
        print("Please set SQLITE_URL and POSTGRES_URL environment variables.")
        sys.exit(2)

    print(f"Connecting to source: {sqlite_url}")
    src_engine = create_engine(sqlite_url)
    print(f"Connecting to target: {pg_url}")
    dst_engine = create_engine(pg_url)

    # Reflect tables in dependency order. Adjust if your schema differs.
    tables_in_order = [
        'users',
        'academic_years',
        'courses',
        'enrollments',
    ]

    try:
        for t in tables_in_order:
            copy_table(src_engine, dst_engine, t, pk_cols=None)
    except SQLAlchemyError as e:
        print('Migration failed:', e)
        sys.exit(1)

    print('Migration completed successfully.')


if __name__ == '__main__':
    main()
