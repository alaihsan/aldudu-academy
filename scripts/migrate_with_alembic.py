"""Upgrade target Postgres schema via Alembic (Flask-Migrate) and copy data from SQLite.

Usage:
  export SQLITE_URL="sqlite:////absolute/path/to/aldudu_academy.db"
  export POSTGRES_URL="postgresql://user:pass@host:5432/dbname"
  .venv/bin/python scripts/migrate_with_alembic.py

The script does:
 1. Export `DATABASE_URL=POSTGRES_URL` and run `flask db upgrade` (uses current Python interpreter)
 2. Copy data from SQLITE_URL -> POSTGRES_URL table-by-table (safe row copy)

Notes:
 - Run this from the repo root inside your project's virtualenv (.venv).
 - The target database will be migrated to the latest Alembic revision first.
 - Always backup both DBs before running in production.
"""

import os
import sys
import subprocess
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError


def run_flask_db_upgrade(env):
    """Run 'flask db upgrade' using the current Python interpreter and provided env."""
    cmd = [sys.executable, '-m', 'flask', 'db', 'upgrade']
    print('Running:', ' '.join(cmd))
    res = subprocess.run(cmd, env=env)
    if res.returncode != 0:
        raise SystemExit(f'flask db upgrade failed with code {res.returncode}')


def copy_table(src_engine, dst_engine, table_name):
    src_meta = MetaData()
    dst_meta = MetaData()
    src_table = Table(table_name, src_meta, autoload_with=src_engine)
    dst_table = Table(table_name, dst_meta, autoload_with=dst_engine)

    with src_engine.connect() as sconn, dst_engine.connect() as dconn:
        sel = select(src_table)
        rows = [dict(r._mapping) for r in sconn.execute(sel)]
        if not rows:
            print(f'No rows for {table_name}')
            return 0

        # Remove columns from row dicts that don't exist in dst_table (safety)
        dst_cols = set(c.name for c in dst_table.columns)
        sanitized_rows = [ {k:v for k,v in row.items() if k in dst_cols} for row in rows ]

        try:
            with dconn.begin():
                # If destination is Postgres, use ON CONFLICT DO NOTHING to be idempotent
                if dconn.dialect.name == 'postgresql':
                    stmt = pg_insert(dst_table).values(sanitized_rows)
                    stmt = stmt.on_conflict_do_nothing(index_elements=[c.name for c in dst_table.primary_key.columns])
                    dconn.execute(stmt)
                else:
                    dconn.execute(dst_table.insert(), sanitized_rows)
        except Exception as e:
            print(f'Failed to insert into {table_name}:', e)
            raise

    print(f'Copied {len(rows)} rows into {table_name}')
    return len(rows)


def main():
    sqlite_url = os.environ.get('SQLITE_URL')
    pg_url = os.environ.get('POSTGRES_URL')
    if not sqlite_url or not pg_url:
        print('Please set SQLITE_URL and POSTGRES_URL environment variables.')
        sys.exit(2)

    # Step 1: run alembic upgrades on target
    env = os.environ.copy()
    env['DATABASE_URL'] = pg_url
    env['FLASK_APP'] = 'app'
    run_flask_db_upgrade(env)

    # Step 2: copy data
    src_engine = create_engine(sqlite_url)
    dst_engine = create_engine(pg_url)

    tables_in_order = [
        'users',
        'academic_years',
        'courses',
        'enrollments',
    ]

    try:
        for t in tables_in_order:
            copy_table(src_engine, dst_engine, t)
    except SQLAlchemyError as e:
        print('Migration failed:', e)
        sys.exit(1)

    print('Migration via Alembic + data copy completed successfully.')


if __name__ == '__main__':
    main()
