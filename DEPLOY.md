Production migration checklist (SQLite → PostgreSQL)

Overview
--------
This document explains how to migrate from the current SQLite development DB to a production-ready PostgreSQL deployment. It assumes you have the repo checked out and a Python virtualenv set up.

1) Add/verify dependencies
--------------------------
- psycopg2-binary is required to connect to PostgreSQL. On many systems you may need PostgreSQL client headers (pg_config). On macOS use Homebrew:

  brew install postgresql

Then install Python packages in your virtualenv:

  .venv/bin/python -m pip install -r requirements.txt

(We added Flask-Migrate to the repo. If psycopg2-binary fails to build, install PostgreSQL first so pg_config is available.)

2) Configure DATABASE_URL
-------------------------
Set environment variable DATABASE_URL to your Postgres connection string:

  export DATABASE_URL='postgresql://myapp:secret@db.example.com:5432/aldudu_prod'
  export FLASK_SECRET_KEY='...'

The application `app.create_app()` prefers `DATABASE_URL` and falls back to the local SQLite file.

3) Initialize migrations & apply schema
--------------------------------------
We use Flask-Migrate (Alembic) to manage schema.

If you haven't already initialized migrations locally:

  FLASK_APP=app .venv/bin/python -m flask db init

Generate migration script from models (autogenerate):

  FLASK_APP=app .venv/bin/python -m flask db migrate -m "initial"

Apply to the target database (when DATABASE_URL points to Postgres):

  FLASK_APP=app .venv/bin/python -m flask db upgrade

4) Migrate data from SQLite to Postgres
-------------------------------------
Recommended: pgloader — it automates type conversion and copies data correctly.

Install pgloader (macOS):

  brew install pgloader

Run pgloader:

  pgloader sqlite:///absolute/path/to/aldudu_academy.db postgresql://myapp:secret@localhost:5432/aldudu_prod

pgloader (recommended for large migrations)
-------------------------------------------
For larger datasets or more complex type handling, `pgloader` is recommended. Example:

```
pgloader sqlite:///absolute/path/to/aldudu_academy.db postgresql://myapp:secret@localhost:5432/aldudu_prod
```

pgloader will convert types and copy data efficiently.

Deployment (Production) — quick recipes
-------------------------------------

Option A — Docker + Docker Compose

1. Create `.env` from `deploy/.env.example` and set values.

2. Build and start:

```bash
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

3. Apply DB migrations (inside container or with local `flask` pointing to DB):

```bash
export DATABASE_URL="postgresql://..."
.venv/bin/python -m flask db upgrade
```

Option B — Systemd + Gunicorn + Nginx

1. Create a python virtualenv on the server and install requirements.
2. Create systemd unit file from `deploy/aldudu.service` and adjust paths/credentials.
3. Place `deploy/nginx.conf` in `/etc/nginx/sites-available/` and symlink to `sites-enabled`.
4. Restart services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aldudu
sudo systemctl restart nginx
```

Option C — Managed platforms

You can also deploy the Docker image to managed containers (ECS, Azure App Service, Google Cloud Run). Ensure you set `DATABASE_URL` and `FLASK_SECRET_KEY` via managed secrets.

Security and operations notes
-----------------------------
- Use a secrets manager for DB credentials in production.
- Configure automatic backups for Postgres (pg_dump snapshots or managed snapshots).
- Use connection pooling (pgbouncer) in front of Postgres for many concurrent workers.


Alternative: export CSV and import with psql \copy, or write a Python script using SQLAlchemy to transfer rows.

5) Connection pooling & runtime
-------------------------------
For production, run behind a WSGI server with multiple workers (gunicorn) and use a DB connection pooler like pgbouncer.

Example gunicorn command:

  .venv/bin/gunicorn 'app:create_app()' -w 4 -b 0.0.0.0:8000

Example systemd unit (minimal):

  [Unit]
  Description=Aldudu Academy Gunicorn Service
  After=network.target

  [Service]
  User=www-data
  Group=www-data
  WorkingDirectory=/srv/aldudu-academy
  Environment="DATABASE_URL=postgresql://myapp:secret@localhost:5432/aldudu_prod"
  ExecStart=/srv/aldudu-academy/.venv/bin/gunicorn 'app:create_app()' -w 4 -b 0.0.0.0:8000

  [Install]
  WantedBy=multi-user.target

6) Backups & monitoring
-----------------------
- Schedule pg_dump or use managed DB's snapshot features.
- Monitor connection usage (pg_stat_activity) and tune pool_size accordingly.

7) Troubleshooting notes
------------------------
- If psycopg2-binary fails to install: install PostgreSQL dev packages first (pg_config must be present).
- If Alembic autogenerate reports "No changes detected": ensure your models are imported and the metadata is available when Flask-Migrate runs (our app factory registers models via import of models.py before db.init_app).


If you want I can:
- Try installing psycopg2-binary now (requires system-level pg_config). I can detect if pg_config is present and attempt installation.
- Create a small Python transfer script if you prefer a Python-based migration instead of pgloader.
- Prepare a CI workflow file to run migrations during deployment.
