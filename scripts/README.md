Migration scripts

migrate_sqlite_to_postgres.py

Usage (example):

```bash
# Export connection strings (absolute path for sqlite)
export SQLITE_URL="sqlite:////Users/teamit/dev/aldudu-academy/instance/aldudu_academy.db"
export POSTGRES_URL="postgresql://myuser:mypass@db-host:5432/aldudu_prod"

# Run migration (test first on a copy!)
python scripts/migrate_sqlite_to_postgres.py
```

Notes:
- This script copies rows table-by-table preserving primary keys where possible.
- Back up both databases before running.
- Prefer using `pgloader` for a robust production migration if available.
